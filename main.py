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


@register(
    "github_webhook",
    "AstrBot Team",
    "GitHub Webhook 接收插件 - 将 GitHub 事件转发到聊天平台",
    "0.2.0",
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

        if not self.target_umo:
            logger.warning(
                "GitHub Webhook: target_umo not configured, plugin may not work!"
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

        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            logger.error(f"GitHub Webhook: Failed to parse JSON: {e}")
            return web.Response(status=400, text="Invalid JSON")

        logger.info(f"GitHub Webhook: Received event type: {event_type}")

        if event_type == "ping":
            return web.Response(text="Pong")

        message = None

        if event_type == "push":
            message = await handle_push_event(data, self.context)
        elif event_type == "issues":
            message = await handle_issues_event(data, self.context)
        elif event_type == "pull_request":
            message = await handle_pull_request_event(data, self.context)

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
            message_chain = api.MessageChain(chain=[Plain(message)])
            result = await self.context.send_message(self.target_umo, message_chain)
            logger.info(
                f"GitHub Webhook: Message sent to {self.target_umo}, result: {result}"
            )
            if not result:
                logger.warning(
                    f"GitHub Webhook: Platform not found for {self.target_umo}"
                )
        except Exception as e:
            logger.error(f"GitHub Webhook: Failed to send message: {e}")

    async def terminate(self):
        if self.site:
            await self.site.stop()
            logger.info("GitHub Webhook server stopped")
        if self.runner:
            await self.runner.cleanup()
