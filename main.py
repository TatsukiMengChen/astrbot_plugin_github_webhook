"""AstrBot GitHub Webhook Plugin - Entry point."""

import sys
from pathlib import Path

from astrbot.api.star import Context, Star, register

# 将 src/ 添加到 sys.path，使 Python 能找到模块
sys.path.insert(0, str(Path(__file__).parent))

from src.core.plugin import GitHubWebhookPlugin


@register(
    "github_webhook",
    "TatsukiMengChen",
    "GitHub Webhook 集成插件 - 接收 GitHub 事件并转发到聊天平台",
    "0.4.0",
)
class PluginEntry(Star):
    """插件入口类，代理到实际的 GitHubWebhookPlugin 类"""

    def __init__(self, context: Context, config):
        """初始化插件 - 将调用传递给实际的插件类"""
        self._plugin = GitHubWebhookPlugin(context, config)

    async def initialize(self):
        """插件初始化"""
        await self._plugin.start_server()

    async def handle_webhook(self, request):
        """处理 webhook 请求"""
        return await self._plugin.handle_webhook(request)

    async def terminate(self):
        """插件销毁"""
        await self._plugin.terminate()
