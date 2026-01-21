"""AstrBot GitHub Webhook Plugin - Receives GitHub events and forwards to chat platforms."""

import asyncio
import json
from aiohttp import web
from astrbot.api.star import Context, Star, register
from astrbot.api import all as api, AstrBotConfig
from astrbot.api import logger
from astrbot.api.message_components import Plain

from .handlers.push_handler import handle_push_event
from .handlers.issues_handler import handle_issues_event
from .handlers.pull_request_handler import handle_pull_request_event
from .utils.rate_limiter import RateLimiter
from .utils.verify_signature import verify_signature


@register(
    "github_webhook",
    "TatsukiMengChen",
    "GitHub Webhook 接收插件 - 将 GitHub 事件转发到聊天平台",
    "0.3.0",
    "https://github.com/TatsukiMengChen/astrbot_plugin_github_webhook",
)
class GitHubWebhookPlugin(Star):
    """GitHub Webhook receiver plugin."""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.app = web.Application()
        self.app.router.add_post("/webhook", self.handle_webhook)
        self.runner = None
        self.site = None

        self.port = config.get("port", 8080)
        self.target_umo = config.get("target_umo", "")
        self.webhook_secret = config.get("webhook_secret", "")
        self.rate_limit = config.get("rate_limit", 10)

        # Initialize rate limiter (0 means no limit)
        if self.rate_limit > 0:
            self.rate_limiter = RateLimiter(max_requests=self.rate_limit)
        else:
            self.rate_limiter = None

        if not self.target_umo:
            logger.warning(
                "GitHub Webhook: target_umo not configured, plugin may not work!"
            )

        if self.webhook_secret:
            logger.info("GitHub Webhook: Signature verification enabled")
        else:
            logger.warning(
                "GitHub Webhook: No webhook_secret configured, "
                "signature verification disabled (not recommended for production)"
            )

        if self.rate_limiter:
            logger.info(
                f"GitHub Webhook: Rate limiting enabled "
                f"({self.rate_limit} requests/minute)"
            )

        asyncio.create_task(self.start_server())

    async def start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        logger.info(f"GitHub Webhook server started on port {self.port}")

    async def handle_webhook(self, request: web.Request):
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        signature = request.headers.get("X-Hub-Signature-256", "")

        # Rate limiting check
        if self.rate_limiter:
            is_allowed, retry_after = await self.rate_limiter.is_allowed()
            if not is_allowed:
                current, max_req = self.rate_limiter.get_usage()
                logger.warning(
                    f"GitHub Webhook: Rate limit exceeded "
                    f"({current}/{max_req} requests/minute)"
                )
                return web.Response(
                    status=429,
                    text=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_req),
                        "X-RateLimit-Remaining": str(max_req - current),
                        "X-RateLimit-Reset": str(retry_after),
                    },
                )

        # Read payload
        try:
            payload_bytes = await request.read()
            data = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"GitHub Webhook: Failed to parse JSON: {e}")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as e:
            logger.error(f"GitHub Webhook: Failed to read request body: {e}")
            return web.Response(status=400, text="Failed to read request")

        # Signature verification
        if self.webhook_secret and signature:
            if not verify_signature(payload_bytes, signature, self.webhook_secret):
                logger.warning("GitHub Webhook: Invalid signature - request rejected")
                return web.Response(status=401, text="Invalid signature")

        logger.info(f"GitHub Webhook: Received event type: {event_type}")

        if event_type == "ping":
            return web.Response(text="Pong")

        message = None

        try:
            if event_type == "push":
                message = await handle_push_event(data, self.context)
            elif event_type == "issues":
                message = await handle_issues_event(data, self.context)
            elif event_type == "pull_request":
                message = await handle_pull_request_event(data, self.context)
            else:
                logger.info(f"GitHub Webhook: Event type '{event_type}' not handled")
        except Exception as e:
            logger.error(f"GitHub Webhook: Error processing event: {e}", exc_info=True)
            return web.Response(status=500, text="Internal server error")

        if message:
            await self.send_message(message)

        return web.Response(status=200, text="OK")

    async def send_message(self, message: str):
        if not self.target_umo:
            logger.error(
                "GitHub Webhook: Cannot send message - target_umo not configured"
            )
            return

        try:
            # 正确构建消息链：Plain 组件直接作为参数，不是 chain 参数
            message_chain = api.MessageChain([Plain(message)])
            result = await self.context.send_message(self.target_umo, message_chain)
            logger.info(
                f"GitHub Webhook: Message sent to {self.target_umo}, result: {result}"
            )
            if not result:
                logger.warning(
                    f"GitHub Webhook: Platform not found for {self.target_umo}"
                )
        except Exception as e:
            # 记录完整错误信息但不传播异常
            logger.error(f"GitHub Webhook: Failed to send message: {e}")
            logger.error(f"GitHub Webhook: Error type: {type(e).__name__}")
            logger.error(f"GitHub Webhook: Error details: {str(e)}")

    async def terminate(self):
        if self.site:
            await self.site.stop()
            logger.info("GitHub Webhook server stopped")
        if self.runner:
            await self.runner.cleanup()
