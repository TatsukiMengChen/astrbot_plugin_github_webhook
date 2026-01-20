"""AstrBot GitHub Webhook Plugin - Receives GitHub events and forwards to chat platforms."""

import asyncio
import json
from aiohttp import web
from astrbot.api.star import Context, Star, register
from astrbot.api import all as api, AstrBotConfig
from astrbot.api import logger
from astrbot.api.message_components import Plain


@register(
    "github_webhook",
    "AstrBot Team",
    "GitHub Webhook 接收插件 - 将 GitHub 事件转发到聊天平台",
    "0.1.0",
    "https://github.com/AstrBotDevs/astrbot_plugin_github_webhook",
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

        if event_type == "push":
            await self.handle_push_event(data)

        return web.Response(status=200, text="OK")

    async def handle_push_event(self, data: dict):
        try:
            pusher = data.get("pusher", {})
            author_name = pusher.get("name", "Unknown")
            author_login = pusher.get("email", "")

            repository = data.get("repository", {})
            repo_name = repository.get("full_name", "Unknown")

            ref = data.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref else "Unknown"

            commits = data.get("commits", [])
            if not commits:
                logger.warning("GitHub Webhook: Push event has no commits")
                return

            commit = commits[0]
            commit_message = commit.get("message", "No message")
            commit_url = commit.get("url", "")
            commit_id = commit.get("id", "")[:7]

            message = self.format_push_message(
                author_name=author_name,
                repo_name=repo_name,
                branch=branch,
                commit_message=commit_message,
                commit_url=commit_url,
                commit_id=commit_id,
            )

            await self.send_message(message)

        except Exception as e:
            logger.error(f"GitHub Webhook: Error handling push event: {e}")

    def format_push_message(
        self,
        author_name: str,
        repo_name: str,
        branch: str,
        commit_message: str,
        commit_url: str,
        commit_id: str,
    ) -> str:
        return (
            f"📦 GitHub Push Event\n"
            f"👤 {author_name} pushed to {repo_name}\n"
            f"🌿 Branch: {branch}\n"
            f"💬 {commit_message}\n"
            f"🔗 Commit: {commit_id}\n"
            f"📎 {commit_url}"
        )

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
