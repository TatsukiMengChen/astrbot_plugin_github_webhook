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

        # Agent 配置读取（兼容字符串和布尔值）
        enable_agent_config = config.get("enable_agent", "false")
        # 正确判断：只有明确的启用值才设为 True
        if isinstance(enable_agent_config, bool):
            self.enable_agent = enable_agent_config
        elif isinstance(enable_agent_config, str):
            self.enable_agent = enable_agent_config.lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
        else:
            self.enable_agent = False

        self.llm_provider_id = config.get("llm_provider_id", "")
        self.agent_timeout = int(config.get("agent_timeout", "30") or 30)
        self.agent_system_prompt = config.get("agent_system_prompt", "")

        # Initialize rate limiter (0 means no limit)
        if self.rate_limit > 0:
            self.rate_limiter = RateLimiter(max_requests=self.rate_limit)
        else:
            self.rate_limiter = None

        # 配置验证和完整日志
        logger.info("=" * 60)
        logger.info("GitHub Webhook: Configuration loaded")
        logger.info(f"  target_umo: {self.target_umo}")
        logger.info(f"  enable_agent: {self.enable_agent}")
        logger.info(f"  llm_provider_id: {self.llm_provider_id or '(default)'}")
        logger.info(f"  agent_timeout: {self.agent_timeout}s")
        logger.info(
            f"  agent_system_prompt: {len(self.agent_system_prompt) if self.agent_system_prompt else 0} chars"
        )
        logger.info(f"  rate_limit: {self.rate_limit} req/min")
        logger.info("=" * 60)

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

        # LLM 配置日志
        if self.enable_agent:
            logger.info("GitHub Webhook: LLM mode enabled")
            if self.llm_provider_id:
                logger.info(
                    f"GitHub Webhook: Using LLM provider ID: {self.llm_provider_id}"
                )
            else:
                logger.info("GitHub Webhook: Using default LLM provider")
            if self.agent_system_prompt:
                logger.info("GitHub Webhook: Custom system prompt configured")
        else:
            logger.info("GitHub Webhook: LLM mode disabled, using default templates")

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
        """使用 LLM 生成个性化消息并发送"""
        try:
            # 构建 LLM 任务的 prompt
            event_name = {
                "push": "代码推送",
                "issues": "问题",
                "pull_request": "拉取请求",
            }.get(event_type, event_type)

            # 构建 LLM 输入信息 - 优化结构，确保 GitHub 事件内容优先级最高
            llm_input = f"""GitHub 事件信息：

{message}

任务：生成一条简洁、有趣的 QQ 群消息通知。
要求：
1. 消息要简洁明了
2. 可以使用 emoji 增加趣味性
3. 保留关键信息（作者、仓库、标题、URL等）
4. 如果有链接（commit URL、issue URL、PR URL），必须保留
5. 使用友好、生动的语气

请直接输出最终的消息内容，不要有多余的解释。
"""

            # 诊断日志
            logger.info("=" * 60)
            logger.info(f"GitHub Webhook: LLM Processing for {event_type} event")
            logger.info(f"  Provider: {self.llm_provider_id or '(default)'}")
            logger.info(f"  Input length: {len(llm_input)} chars")
            logger.info(f"  Input preview (first 300 chars): {llm_input[:300]}...")
            if self.agent_system_prompt:
                logger.info(
                    f"  System prompt length: {len(self.agent_system_prompt)} chars"
                )
            logger.info("=" * 60)

            # 获取 LLM provider ID
            if self.llm_provider_id:
                provider_id = self.llm_provider_id
            else:
                # 使用默认 provider
                try:
                    provider_id = await self.context.get_current_chat_provider_id(
                        self.target_umo
                    )
                    logger.info(
                        f"GitHub Webhook: Using default provider: {provider_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"GitHub Webhook: Failed to get default provider: {e}, falling back to template"
                    )
                    await self.send_message(message)
                    return

            # 调用 LLM
            try:
                llm_response = await asyncio.wait_for(
                    self.context.llm_generate(
                        chat_provider_id=provider_id,
                        prompt=llm_input,
                        system_prompt=self.agent_system_prompt
                        if self.agent_system_prompt
                        else None,
                    ),
                    timeout=self.agent_timeout,
                )
                logger.info(
                    f"GitHub Webhook: LLM response received, length: {len(llm_response.completion_text) if llm_response else 0}"
                )

                # 诊断日志：输出长度和内容
                output_text = llm_response.completion_text if llm_response else ""
                logger.info(f"  Output length: {len(output_text)} chars")
                if output_text:
                    logger.info(
                        f"  Output preview (first 300 chars): {output_text[:300]}..."
                    )

                # 检测输出是否可能被截断
                if output_text and len(output_text) < 100:
                    logger.warning(
                        f"GitHub Webhook: LLM output suspiciously short (input: {len(llm_input)} chars, output: {len(output_text)} chars)"
                    )

                # 从 LLM 响应中提取纯文本内容
                if llm_response and llm_response.completion_text:
                    # 直接使用 LLM 返回的文本
                    text_content = llm_response.completion_text.strip()

                    # 清理空行
                    text_content = "\n".join(
                        line.strip()
                        for line in text_content.split("\n")
                        if line.strip()
                    )

                    if text_content:
                        generated_message = text_content
                        logger.info(
                            f"GitHub Webhook: Generated message: {generated_message[:100]}..."
                        )
                        await self.send_message(generated_message)
                    else:
                        logger.warning(
                            "GitHub Webhook: LLM returned empty content, falling back to template"
                        )
                        await self.send_message(message)
                else:
                    logger.warning(
                        "GitHub Webhook: LLM returned None or empty completion, falling back to template"
                    )
                    await self.send_message(message)

            except asyncio.TimeoutError:
                logger.error(
                    f"GitHub Webhook: LLM timeout after {self.agent_timeout} seconds, falling back to template"
                )
                await self.send_message(message)

        except Exception as e:
            # LLM 调用失败，使用模板作为降级方案
            logger.error(f"GitHub Webhook: LLM invocation failed: {e}")
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
