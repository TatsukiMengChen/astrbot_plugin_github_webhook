# 项目结构

本文档介绍插件的代码组织结构。

## 目录结构

```
astrbot_plugin_github_webhook/
├── src/                          # Python 源代码目录
│   ├── core/                 # 核心管理层
│   │   ├── __init__.py
│   │   ├── config.py        # PluginConfig 类（配置管理）
│   │   ├── plugin.py        # GitHubWebhookPlugin 类（插件实现）
│   │   └── constants.py     # 常量定义
│   ├── handlers/              # 事件处理层
│   │   ├── __init__.py
│   │   ├── issues_handler.py
│   │   ├── pull_request_handler.py
│   │   └── push_handler.py
│   ├── formatters/             # 消息格式化层
│   │   ├── __init__.py
│   │   ├── issues_formatter.py
│   │   ├── pull_request_formatter.py
│   │   └── push_formatter.py
│   ├── utils/                 # 工具层
│   │   ├── __init__.py
│   │   ├── rate_limiter.py     # 请求速率限制器
│   │   └── verify_signature.py # Webhook 签名验证
│   └── services/              # 业务服务层
│       ├── __init__.py
│       └── llm_service.py      # LLM 调用服务
├── main.py                     # 插件入口文件（AstrBot 加载点）
├── metadata.yaml               # 插件元数据
├── requirements.txt             # Python 依赖
├── _conf_schema.json           # 配置架构（WebUI 使用）
├── docs/                      # 文档目录
│   ├── index.md               # 文档索引
│   ├── 01-installation.md     # 安装指南
│   ├── 02-configuration.md   # 配置说明
│   ├── 03-usage.md          # 使用示例
│   ├── 04-deployment.md      # 部署指南
│   ├── 05-troubleshooting.md # 故障排查
│   ├── 06-development.md     # 开发相关
│   └── 07-project-structure.md # 项目结构（本文件）
├── templates/                 # Prompt 模板目录
│   └── default.md            # 默认系统提示词
├── tests/                     # 测试目录
│   ├── __init__.py
│   └── test_config.py        # 配置测试
├── LICENSE                    # MIT 许可证
└── README.md                  # 项目说明
```

## 设计理念

### 1. src/ 目录 - 代码与资源分离

将所有 Python 源代码放入 `src/` 目录，遵循 Python 项目最佳实践：

**优势**：
- 代码和资源（文档、模板、配置）清晰分离
- 符合 Python Packaging User Guide 推荐的 `src/` 布局
- 便于测试和打包
- 便于未来可能的多语言支持（src/ 下的包结构）

### 2. 分层架构

插件采用清晰的三层架构：

```
main.py (入口层)
    ↓
src/core/ (管理层)
    ↓
src/handlers/ (业务层)
    ↓
src/formatters/ + src/utils/ (工具层)
```

### 3. 模块职责

| 模块 | 职责 |
|--------|--------|
| **main.py** | 插件入口，代理到实际的 GitHubWebhookPlugin 类 |
| **src/core/config.py** | 配置管理，提供强类型属性访问 |
| **src/core/plugin.py** | 插件核心实现，Webhook 服务器和事件分发 |
| **src/core/constants.py** | 常量定义（端口、事件类型、动作等）|
| **src/handlers/\*** | 处理不同类型的 GitHub 事件 |
| **src/formatters/\*** | 将 GitHub Payload 转换为可读的消息文本 |
| **src/utils/rate_limiter.py** | 基于滑动窗口的请求限流器 |
| **src/utils/verify_signature.py** | GitHub Webhook HMAC-SHA256 签名验证 |
| **src/services/llm_service.py** | LLM 消息生成服务 |

## 数据流

```
GitHub Webhook
    ↓
main.py: PluginEntry.handle_webhook()
    ↓
src/core/plugin.py: GitHubWebhookPlugin.handle_webhook()
    ↓ (限流检查、签名验证)
src/handlers/*.py: handle_xxx_event()
    ↓
src/formatters/*.py: format_xxx_message()
    ↓
src/core/plugin.py: send_message() 或 send_with_agent()
    ↓ (如果启用 LLM: src/services/llm_service.py)
    ↓
聊天平台 (QQ/微信等)
```

## 导入规范

### 相对导入（src/ 内部）

```python
# 同级模块
from .config import PluginConfig
from .plugin import GitHubWebhookPlugin

# 跨层级导入（需要回到 src/）
from ..handlers.issues_handler import handle_issues_event
from ..formatters.push_formatter import format_push_message
from ..utils.rate_limiter import RateLimiter
from ..services.llm_service import send_with_agent
```

### 绝对导入（AstrBot API）

```python
from astrbot.api import AstrBotConfig, logger
from astrbot.api.star import Context, Star, register
from astrbot.api import all as api
```

## 依赖项

### runtime.txt

```
aiohttp>=3.11.0
```

### AstrBot API

- `astrbot.api` - AstrBot 核心 API
- `astrbot.api.star.Context` - 插件上下文
- `astrbot.api.message_components` - 消息组件

## 测试

### 运行测试

```bash
cd tests
pytest test_config.py -v
```

### 测试覆盖

- `tests/test_config.py` - 配置类测试

## 扩展指南

### 添加新的事件处理器

1. 在 `src/handlers/` 创建新文件 `new_event_handler.py`
2. 实现处理函数 `async def handle_new_event(data, context):`
3. 在 `src/core/plugin.py` 的 `handle_webhook()` 中添加路由
4. 在 `src/formatters/` 创建对应的格式化器（如需要）

### 添加新的工具类

1. 在 `src/utils/` 创建新文件 `new_util.py`
2. 在相关模块中导入使用

### 添加新的服务

1. 在 `src/services/` 创建新文件 `new_service.py`
2. 在 `src/core/plugin.py` 或其他模块中导入使用

## 相关文档

- [安装指南](01-installation.md) - 如何部署插件
- [开发计划](06-development.md) - 贡献和路线图
