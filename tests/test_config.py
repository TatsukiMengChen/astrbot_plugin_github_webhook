"""Tests for GitHub Webhook plugin."""

import pytest
from astrbot.api import AstrBotConfig
from src.core.config import PluginConfig
from src.core.constants import DEFAULT_PORT


def test_config_default_values():
    """测试配置类的默认值"""
    config_data = {
        "port": DEFAULT_PORT,
        "target_umo": "",
        "webhook_secret": "",
        "rate_limit": 10,
        "enable_agent": False,
        "llm_provider_id": "",
        "agent_timeout": 60,
        "agent_system_prompt": "",
    }
    config = AstrBotConfig(config_data)
    plugin_config = PluginConfig(config)

    assert plugin_config.port == DEFAULT_PORT
    assert plugin_config.rate_limit == 10
    assert plugin_config.enable_agent == False


def test_config_with_custom_values():
    """测试配置类的自定义值"""
    config_data = {
        "port": 9000,
        "target_umo": "test:GroupMessage:123456",
        "webhook_secret": "test_secret",
        "rate_limit": 20,
        "enable_agent": True,
        "llm_provider_id": "test_provider",
        "agent_timeout": 90,
        "agent_system_prompt": "Custom prompt",
    }
    config = AstrBotConfig(config_data)
    plugin_config = PluginConfig(config)

    assert plugin_config.port == 9000
    assert plugin_config.target_umo == "test:GroupMessage:123456"
    assert plugin_config.webhook_secret == "test_secret"
    assert plugin_config.enable_agent == True
