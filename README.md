# AstrBot GitHub Webhook Plugin

AstrBot 插件，用于接收 GitHub 事件（push、issues、pull requests 等）并转发到聊天平台（QQ 群组、私聊等）。

## 功能特性

- ✅ 接收 GitHub Webhook 事件
- ✅ 支持 Push 事件（代码提交）
- ✅ 支持 Issues 事件（问题追踪）
- ✅ 支持 Pull Request 事件（代码合并）
- ✅ 实时转发到指定的聊天平台群组/用户
- ✅ 自定义端口号配置
- ✅ 简洁的消息格式，包含关键信息
- ✅ Webhook Secret 签名验证（防止恶意请求）
- ✅ 请求速率限制（防止消息轰炸）
- ✅ 全面的错误处理和日志记录
- ✅ LLM 智能消息生成（支持自定义提示词）
- 🔜 自定义消息模板
- 🔜 Release 事件支持

## 快速开始

### 安装

```bash
cd AstrBot/data/plugins
git clone https://github.com/TatsukiMengChen/astrbot_plugin_github_webhook.git
cd astrbot_plugin_github_webhook
pip install -r requirements.txt
```

### 配置

在 AstrBot WebUI 中配置插件，或编辑配置文件：

`data/config/astrbot_plugin_github_webhook_config.json`

```json
{
  "port": 8080,
  "target_umo": "platform_id:GroupMessage:群号",
  "webhook_secret": "your_github_webhook_secret",
  "rate_limit": 10,
  "enable_agent": true,
  "llm_provider_id": "",
  "agent_timeout": 60,
  "agent_system_prompt": ""
}
```

### 重启

```bash
sudo systemctl restart astrbot
# 或手动重启 AstrBot
```

查看日志确认插件已加载：

```
[INFO] GitHub Webhook server started on port 8080
```

### 配置 GitHub Webhook

1. 进入 GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `http://你的服务器IP:8080/webhook`
3. **Content type**: `application/json`
4. **Secret** (可选): 配置 Webhook 密钥用于签名验证
5. **Events**: 选择需要触发的事件（建议勾选 Pushes, Issues, Pull requests）
6. **Active**: ✅ 勾选
7. 点击 "Add webhook"

## 文档

详细的配置、使用和部署文档请查看 [docs/](docs/) 目录：

- [文档索引](docs/index.md) - 文档导航中心
- [安装指南](docs/01-installation.md) - 详细安装步骤
- [配置说明](docs/02-configuration.md) - 所有配置项详解
- [使用示例](docs/03-usage.md) - 查看各种事件的消息格式
- [部署指南](docs/04-deployment.md) - 防火墙、Docker 部署
- [故障排查](docs/05-troubleshooting.md) - 常见问题解决方案
- [项目结构](docs/07-project-structure.md) - 了解代码组织
- [开发相关](docs/06-development.md) - 贡献指南和路线图

## LLM Prompt 示例

在 `prompts/` 目录中提供了预置的系统提示词：

- [默认 Prompt](prompts/default.md) - 通用 GitHub 事件消息生成提示词

## 目录结构

```
astrbot_plugin_github_webhook/
├── main.py                     # 插件主文件
├── config.py                   # 插件配置管理
├── metadata.yaml               # 插件元数据
├── requirements.txt             # Python 依赖
├── _conf_schema.json           # 配置架构（WebUI 使用）
├── handlers/                  # 事件处理器模块
├── formatters/                # 消息格式化模块
├── utils/                     # 工具模块
├── docs/                      # 文档目录
├── prompts/                   # LLM 提示词示例
├── LICENSE                   # MIT 许可证
└── README.md                 # 本文件
```

## 依赖

- [aiohttp](https://docs.aiohttp.org/) ≥ 3.11.0 - 异步 HTTP 服务器

## 开发计划

- [x] Issues 事件支持
- [x] Pull Request 事件支持
- [ ] Release 事件支持
- [x] Webhook Secret 签名验证
- [x] 请求速率限制
- [ ] 自定义消息模板（Jinja2）
- [x] Agent 集成（智能消息生成）
- [ ] 分支过滤（仅监听 main 分支）
- [ ] 多目标支持（不同事件发到不同群组）

## 贡献

欢迎提交 Issue 和 Pull Request！详见 [开发文档](docs/06-development.md)。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者

TatsukiMengChen

## 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 强大的聊天机器人框架
- [GitHub Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks) - GitHub 官方文档

## 相关链接

- [AstrBot 文档](https://docs.astrbot.net)
- [AstrBot 插件开发指南](https://docs.astrbot.net/dev/star/introduction)
- [GitHub Webhooks 文档](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
