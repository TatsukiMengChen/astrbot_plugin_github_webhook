# config.py
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, get_type_hints

from astrbot.api import AstrBotConfig, logger


class ConfigNode:
    """配置节点: dict → 强类型属性访问（极简版）"""

    _SCHEMA_CACHE: dict[type, dict[str, type]] = {}

    @classmethod
    def _schema(cls) -> dict[str, type]:
        return cls._SCHEMA_CACHE.setdefault(cls, get_type_hints(cls))

    def __init__(self, data: MutableMapping[str, Any]):
        object.__setattr__(self, "_data", data)
        for key in self._schema():
            if key in data:
                continue
            if hasattr(self.__class__, key):
                continue
            logger.warning(f"[config:{self.__class__.__name__}] 缺少字段: {key}")

    def __getattr__(self, key: str) -> Any:
        if key in self._schema():
            return self._data.get(key)
        raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._schema():
            self._data[key] = value
            return
        object.__setattr__(self, key, value)



class PluginConfig(ConfigNode):
    """插件自定义配置"""

    port: int
    target_umo: str
    webhook_secret: str
    rate_limit: int
    enable_agent: bool
    llm_provider_id: str
    agent_timeout: int
    agent_system_prompt: str

    def __init__(self, cfg: AstrBotConfig):
        super().__init__(cfg)
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

        if self.rate_limit > 0:
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
