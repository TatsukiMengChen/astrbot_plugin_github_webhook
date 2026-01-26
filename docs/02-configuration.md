# 配置说明

本文档详细介绍插件的所有配置项。

## 基础配置

### port

**类型**: `int` | **默认值**: `8080`

Webhook 服务器监听端口。

> 注意：确保服务器防火墙允许该端口的入站连接。

### target_umo

**类型**: `string` | **默认值**: `""` (必填)

目标会话标识符（UMO），指定 GitHub 事件消息发送到哪个群组或用户。

**格式**: `platform_id:message_type:session_id`

**如何获取 UMO**：
1. 加入目标群组
2. 在群组中发送命令：`/sid`
3. AstrBot 会返回当前会话的 UMO

### webhook_secret

**类型**: `string` | **默认值**: `""` (可选)

GitHub Webhook 密钥，用于验证请求来源。

**用途**：
- 在 GitHub 仓库 Webhook 设置中创建后可获取
- 用于验证请求来源，防止恶意请求
- 留空则禁用签名验证（生产环境不推荐）

**配置方式**：
1. 在 GitHub 仓库 → Settings → Webhooks → Add webhook
2. 在 Secret 字段生成一个密钥
3. 复制该密钥到插件配置的 `webhook_secret` 字段

### rate_limit

**类型**: `int` | **默认值**: `10`

请求速率限制（每分钟最大请求数）。

- 设置为 `0` 表示不限制
- 建议设置为 `10-30` 防止消息轰炸
- 当超过限制时，插件会返回 HTTP 429 错误

## LLM 智能消息生成配置

### enable_agent

**类型**: `bool` | **默认值**: `false`

是否启用 LLM 生成个性化消息。

**功能说明**：
- 启用后，LLM 会根据 GitHub 事件内容生成简洁、有趣的消息
- 需要在 AstrBot 中已配置 LLM Provider
- 如果禁用，则使用默认模板格式
- LLM 调用失败时会自动降级到默认模板

### llm_provider_id

**类型**: `string` | **默认值**: `""` (可选)

使用的 LLM Provider ID。

**配置方式**：
- 在 AstrBot WebUI 配置的模型提供商 ID
- 可在插件配置面板中直接选择（下拉列表）
- 留空则使用会话默认 Provider

**获取方法**：
1. 打开 AstrBot WebUI
2. 进入模型提供商设置
3. 查看已配置的 Provider ID

### agent_timeout

**类型**: `int` | **默认值**: `60`

LLM 处理超时时间（秒）。

- 建议设置为 `30-120` 秒
- 超时后自动降级到默认模板
- 过短的 timeout 可能导致 LLM 来不及生成完整消息

### agent_system_prompt

**类型**: `text` | **默认值**: `""` (可选)

自定义 LLM 系统提示词。

**用途**：
- 用于定义 LLM 生成消息的风格、语气等
- 支持多行文本输入
- 留空则使用默认提示词

**示例**：
```
你是一个技术博客编辑，需要将 GitHub 事件转换为生动有趣的简报风格，适当使用 emoji
```

**提示词模板**：
查看 `prompts/` 目录获取预置的系统提示词：
- [默认 Prompt](../prompts/default.md) - 通用 GitHub 事件消息生成提示词

**注意事项**：
- 系统提示词过长（如 50+ 行）会占用大量 token 空间
- 可能导致 GitHub 事件内容被压缩或忽略
- 建议控制提示词长度，确保主要信息能传递给 LLM

## 配置类型说明

AstrBot 配置系统支持以下类型：

- `string`: 短文本，显示为单行输入框
- `text`: 长文本，显示为可调整大小的多行文本框，适合系统提示词等长文本
- `int`: 整数，配合 `slider` 可显示滑块控件
- `bool`: 布尔值，显示为开关控件

> **注意**: `"text"` 类型是合法且推荐的类型，专用于多行文本输入（显示为 textarea）。所有需要用户输入的配置字段都应使用适当的类型。

## 配置文件位置

插件配置文件位于：

```
data/config/astrbot_plugin_github_webhook_config.json
```

配置在 WebUI 修改后会自动保存到此文件。

## 相关文档

- [安装指南](01-installation.md) - 安装和基础配置
- [故障排查](05-troubleshooting.md) - 配置相关问题排查
