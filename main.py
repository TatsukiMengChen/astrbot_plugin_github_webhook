"""AstrBot GitHub Webhook Plugin - Receives GitHub events and forwards to chat platforms."""

import asyncio
import json
import re
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

        # Agent 配置
        self.enable_agent = config.get("enable_agent", "false").lower() == "true"
        self.agent_id = config.get("agent_id", "")
        self.agent_timeout = config.get("agent_timeout", 30)
        self.agent_system_prompt = config.get("agent_system_prompt", "")

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

        # Agent 配置日志
        if self.enable_agent:
            logger.info("GitHub Webhook: Agent mode enabled")
            if self.agent_id:
                logger.info(f"GitHub Webhook: Using Agent ID: {self.agent_id}")
            else:
                logger.info("GitHub Webhook: Using default Agent")
            if self.agent_system_prompt:
                logger.info("GitHub Webhook: Custom agent system prompt configured")
        else:
            logger.info("GitHub Webhook: Agent mode disabled, using default templates")

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
            if self.enable_agent:
                await self.send_with_agent(message, data, event_type)
            else:
                await self.send_message(message)

        return web.Response(status=200, text="OK")

    async def send_with_agent(self, message: str, data: dict, event_type: str):
        """使用 Agent 生成个性化消息并发送"""
        try:
            # 构建 Agent 任务的 prompt
            event_name = {
                "push": "代码推送",
                "issues": "问题",
                "pull_request": "拉取请求",
            }.get(event_type, event_type)

            # 构建 Agent 输入信息
            agent_input = f"""你是一个 GitHub 事件助手。请根据以下 GitHub {event_name}事件，生成一条简洁、有趣的消息通知，发到QQ群组。

事件类型：{event_type}

事件详情：
{message}

要求：
1. 消息要简洁明了
2. 可以使用 emoji 增加趣味性
3. 保留关键信息（作者、仓库、标题、URL等）
4. 如果有链接（commit URL、issue URL、PR URL），必须保留
5. 使用友好、生动的语气

请直接输出最终的消息内容，不要有多余的解释。
"""

            logger.info(
                f"GitHub Webhook: Calling Agent {self.agent_id} for {event_type} event"
            )
            logger.info(f"GitHub Webhook: Agent prompt preview: {agent_input[:100]}...")

            # 调用 Agent
            try:
                agent_response = await asyncio.wait_for(
                    self.context.tool_loop_agent(
                        agent_input, agent_id=self.agent_id if self.agent_id else None
                    ),
                    timeout=self.agent_timeout,
                )
                logger.info(
                    f"GitHub Webhook: Agent response received, length: {len(str(agent_response)) if agent_response else 0}"
                )

                # 从 Agent 响应中提取纯文本内容
                if agent_response:
                    # 尝试解析 Agent 响应
                    import re

                    # 移除可能的 XML 标记或其他标记
                    text_content = str(agent_response)

                    # 清理可能的额外解释
                    text_content = re.sub(
                        r"^[\s\S]*[:：]\s*", "", text_content, flags=re.MULTILINE
                    )
                    text_content = re.sub(
                        r"^[\s\S]*[:：]\s*", "", text_content, flags=re.IGNORECASE
                    )

                    # 移除常见的解释性前缀
                    text_content = re.sub(
                        r"^(最终消息|输出|结果|message|content)[：：]\s*",
                        "",
                        text_content,
                        flags=re.IGNORECASE,
                    )

                    # 清理空行
                    text_content = "\n".join(
                        line.strip()
                        for line in text_content.split("\n")
                        if line.strip()
                    )

                    if text_content.strip():
                        generated_message = text_content.strip()
                        logger.info(
                            f"GitHub Webhook: Generated message: {generated_message[:100]}..."
                        )
                        await self.send_message(generated_message)
                    else:
                        logger.warning(
                            "GitHub Webhook: Agent returned empty content, falling back to template"
                        )
                        await self.send_message(message)
                else:
                    logger.warning(
                        "GitHub Webhook: Agent returned None, falling back to template"
                    )
                    await self.send_message(message)

            except asyncio.TimeoutError:
                logger.error(
                    f"GitHub Webhook: Agent timeout after {self.agent_timeout} seconds, falling back to template"
                )
                await self.send_message(message)

        except Exception as e:
            # Agent 调用失败，使用模板作为降级方案
            logger.error(f"GitHub Webhook: Agent invocation failed: {e}")
            logger.error(f"GitHub Webhook: Falling back to default template")
            await self.send_message(message)

    async def send_message(self, message: str):
        if not self.target_umo:
            logger.error(
                "GitHub Webhook: Cannot send message - target_umo not configured"
            )
            return

        try:
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
