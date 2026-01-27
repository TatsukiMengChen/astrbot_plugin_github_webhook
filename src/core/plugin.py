"""GitHub Webhook Plugin core implementation."""

import json
from aiohttp import web

from astrbot.api import all as api
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star
from astrbot.api import logger

from .config import PluginConfig
from .constants import DEFAULT_PORT
from ..handlers.issues_handler import handle_issues_event
from ..handlers.pull_request_handler import handle_pull_request_event
from ..handlers.push_handler import handle_push_event
from ..utils.rate_limiter import RateLimiter
from ..utils.verify_signature import verify_signature


class GitHubWebhookPlugin(Star):
    """GitHub Webhook receiver plugin."""

    def __init__(self, context: Context, config):
        super().__init__(context)
        self.app = web.Application()
        self.app.router.add_post("/webhook", self.handle_webhook)
        self.runner = None
        self.site = None
        self.cfg = PluginConfig(config)

        if self.cfg.rate_limit > 0:
            self.rate_limiter = RateLimiter(max_requests=self.cfg.rate_limit)
        else:
            self.rate_limiter = None

    async def start_server(self):
        # Clean up any existing server instance
        if self.site:
            await self.site.stop()
            logger.info("GitHub Webhook: Cleaned up existing server instance")
        if self.runner:
            await self.runner.cleanup()
            logger.info("GitHub Webhook: Cleaned up existing runner")

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.cfg.port)
        await self.site.start()
        logger.info(f"GitHub Webhook: Server started on port {self.cfg.port}")

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
        if self.cfg.webhook_secret and signature:
            if not verify_signature(payload_bytes, signature, self.cfg.webhook_secret):
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
            if self.cfg.enable_agent:
                from ..services.llm_service import send_with_agent

                await send_with_agent(self, message, data, event_type)
            else:
                await self.send_message(message)

        return web.Response(status=200, text="OK")

    async def send_message(self, message: str):
        if not self.cfg.target_umo:
            logger.error(
                "GitHub Webhook: Cannot send message - target_umo not configured"
            )
            return

        try:
            message_chain = api.MessageChain([Plain(message)])
            result = await self.context.send_message(self.cfg.target_umo, message_chain)
            logger.info(
                f"GitHub Webhook: Message sent to {self.cfg.target_umo}, result: {result}"
            )
            if not result:
                logger.warning(
                    f"GitHub Webhook: Platform not found for {self.cfg.target_umo}"
                )
        except Exception as e:
            # 记录完整错误信息但不传播异常
            logger.error(f"GitHub Webhook: Failed to send message: {e}")
            logger.error(f"GitHub Webhook: Error type: {type(e).__name__}")
            logger.error(f"GitHub Webhook: Error details: {str(e)}")

    async def terminate(self):
        logger.info("GitHub Webhook: Shutting down server...")
        if self.site:
            await self.site.stop()
            logger.info("GitHub Webhook: Server stopped")
        if self.runner:
            await self.runner.cleanup()
            logger.info("GitHub Webhook: Runner cleaned up")
