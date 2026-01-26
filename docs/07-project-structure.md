# 项目结构

本文档介绍插件的代码组织结构。

## 目录结构

```
astrbot_plugin_github_webhook/
├── main.py                     # 插件主文件
├── config.py                   # 插件配置管理（强类型访问）
├── metadata.yaml               # 插件元数据
├── requirements.txt             # Python 依赖
├── _conf_schema.json           # 配置架构（WebUI 使用）
├── handlers/                  # 事件处理器模块
│   ├── __init__.py
│   ├── push_handler.py         # Push 事件处理
│   ├── issues_handler.py       # Issues 事件处理
│   └── pull_request_handler.py # Pull Request 事件处理
├── formatters/                # 消息格式化模块
│   ├── __init__.py
│   ├── push_formatter.py       # Push 消息格式化
│   ├── issues_formatter.py     # Issues 消息格式化
│   └── pull_request_formatter.py # Pull Request 消息格式化
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── rate_limiter.py         # 请求速率限制器
│   └── verify_signature.py     # Webhook 签名验证
├── docs/                      # 文档目录
│   ├── index.md               # 文档索引
│   ├── 01-installation.md     # 安装指南
│   ├── 02-configuration.md   # 配置说明
│   ├── 03-usage.md          # 使用示例
│   ├── 04-deployment.md      # 部署指南
│   ├── 05-troubleshooting.md # 故障排查
│   ├── 06-development.md     # 开发相关
│   └── 07-project-structure.md # 项目结构（本文件）
├── prompts/                   # LLM 提示词示例
│   └── default.md            # 默认系统提示词
├── .gitignore                # Git 忽略文件
├── LICENSE                   # MIT 许可证
└── README.md                 # 项目说明
```

## 核心模块说明

### main.py

插件的入口文件，负责：
- aiohttp 服务器启动
- Webhook 路由处理
- 事件分发到对应的 Handler
- LLM 消息生成逻辑
- 消息发送到聊天平台

### config.py

强类型配置管理，提供：
- ConfigNode 基类：字典到强类型属性的转换
- PluginConfig 类：所有配置字段的类型定义
- 配置验证和日志输出

### handlers/

按事件类型拆分的处理器模块：

**push_handler.py**
- 处理 GitHub Push 事件
- 提取：推送者、仓库、分支、commit 信息
- 调用 formatter 生成消息

**issues_handler.py**
- 处理 GitHub Issues 事件
- 支持：opened, closed, reopened 等状态
- 提取：action, issue 信息, URL

**pull_request_handler.py**
- 处理 GitHub Pull Request 事件
- 支持：opened, closed, reopened, synchronize 等状态
- 提取：action, PR 信息, 分支信息

### formatters/

将 GitHub Payload 转换为可读的消息文本：
- 格式化输出包含关键信息（作者、仓库、链接等）
- 使用 emoji 增强可读性

### utils/

通用工具函数：

**rate_limiter.py**
- RateLimiter 类：基于滑动窗口的请求限流
- 防止高频 Webhook 导致的消息轰炸
- 提供 `is_allowed()` 和 `get_usage()` 方法

**verify_signature.py**
- Webhook 签名验证函数
- 使用 HMAC-SHA256 验证 GitHub 请求
- 防止恶意请求

## 依赖项

### runtime.txt

```
aiohttp>=3.11.0
```

### AstrBot API

- `astrbot.api` - AstrBot 核心 API
- `astrbot.api.star.Context` - 插件上下文
- `astrbot.api.message_components` - 消息组件

## 数据流

```
GitHub Webhook
    ↓
main.py:handle_webhook()
    ↓ (限流检查、签名验证)
handlers/*.py
    ↓
formatters/*.py
    ↓
main.py:send_with_agent() 或 send_message()
    ↓
聊天平台 (QQ/微信等)
```

## 相关文档

- [安装指南](01-installation.md) - 如何部署插件
- [开发计划](06-development.md) - 贡献和路线图
