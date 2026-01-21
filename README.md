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
- 🔜 自定义消息模板
- 🔜 Release 事件支持

## 安装

### 1. 克隆插件到 AstrBot 插件目录

```bash
cd AstrBot/data/plugins
git clone https://github.com/TatsukiMengChen/astrbot_plugin_github_webhook.git
```

### 2. 安装依赖

```bash
cd astrbot_plugin_github_webhook
pip install -r requirements.txt
```

或使用 AstrBot 推荐的包管理器（如 uv）：

```bash
uv pip install -r requirements.txt
```

### 3. 配置插件

在 AstrBot WebUI 中配置插件，或编辑配置文件：

`data/config/astrbot_plugin_github_webhook_config.json`

```json
{
  "port": 8080,
  "target_umo": "platform_id:GroupMessage:群号",
  "webhook_secret": "your_github_webhook_secret",
  "rate_limit": 10
}
```

#### 配置项说明

- **port** (int, 默认 8080): Webhook 服务器监听端口
- **target_umo** (string, 必填): 目标会话标识符（UMO）
  - 格式：`platform_id:message_type:session_id`
  - 如何获取 UMO：在目标群组中发送 `/sid` 命令
- **webhook_secret** (string, 可选): GitHub Webhook 密钥（强烈推荐配置）
  - 在 GitHub 仓库 Webhook 设置中创建后可获取
  - 用于验证请求来源，防止恶意请求
  - 留空则禁用签名验证（生产环境不推荐）
- **rate_limit** (int, 默认 10): 请求速率限制（每分钟）
  - 设置为 0 表示不限制
  - 建议设置为 10-30 防止消息轰炸

### 4. 重启 AstrBot

重启 AstrBot 以加载插件：

```bash
# 如果使用 systemd
sudo systemctl restart astrbot

# 或手动重启
Ctrl+C 停止后重新运行
```

查看日志确认插件已加载：

```
[INFO] GitHub Webhook server started on port 8080
```

## 配置 GitHub Webhook

### 1. 打开 GitHub 仓库设置

进入你的 GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**

### 2. 配置 Webhook

- **Payload URL**: `http://你的服务器IP:配置的端口/webhook`
  - 例如：`http://123.45.67.89:8080/webhook`
- **Content type**: `application/json`
- **Secret** (强烈推荐): 配置 Webhook 密钥用于签名验证
  1. 在插件配置中设置 `webhook_secret` 字段
  2. 将此处生成的密钥复制到 GitHub Webhook 设置
  3. 用于验证请求来源，防止伪造请求
- **Events**: 选择需要触发的事件
  - 建议勾选：`Pushes`, `Issues`, `Pull requests`
- **Active**: ✅ 勾选

### 3. 点击 "Add webhook"

GitHub 会发送测试 Ping 事件，检查 AstrBot 日志确认收到：

```
[INFO] GitHub Webhook: Received event type: ping
```

## 使用示例

### Push 事件消息格式

```
📦 GitHub Push Event
👤 username pushed to owner/repo
🌿 Branch: main
💬 Fix webhook message sending issue
🔗 Commit: abc1234
📎 https://github.com/owner/repo/commit/abc1234
```

### Issues 事件消息格式

#### Issue 打开
```
🆕 GitHub Issue Event
👤 username opened issue in owner/repo
📋 Issue #42: Bug report
📎 https://github.com/owner/repo/issues/42
```

#### Issue 关闭
```
✅ GitHub Issue Event
👤 username closed issue in owner/repo
📋 Issue #42: Bug report
📎 https://github.com/owner/repo/issues/42
```

### Pull Request 事件消息格式

#### PR 打开
```
🆕 GitHub Pull Request Event
👤 username opened PR in owner/repo
📋 PR #10: Add new feature
🌿 feature → main
📎 https://github.com/owner/repo/pull/10
```

#### PR 合并
```
✅ GitHub Pull Request Event
👤 username closed PR in owner/repo
📋 PR #10: Add new feature
🌿 feature → main
📎 https://github.com/owner/repo/pull/10
```

## 获取目标 UMO

1. 加入目标群组
2. 在群组中发送命令：`/sid`
3. AstrBot 会返回当前会话的 UMO，例如：
   ```
   UMO: 「default:GroupMessage:1078537517」 此值可用于设置白名单。
   ```
4. 将此 UMO 填入插件的 `target_umo` 配置项

## 防火墙配置

确保服务器防火墙允许访问配置的端口（默认 8080）：

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8080/tcp

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# 云服务商安全组
# 在阿里云/腾讯云/AWS 控制台添加入站规则开放 8080 端口
```

## 目录结构

```
astrbot_plugin_github_webhook/
├── main.py                     # 插件主文件
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
├── .gitignore                # Git 忽略文件
├── LICENSE                   # MIT 许可证
└── README.md                # 本文件
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
- [ ] Agent 集成（智能消息生成）
- [ ] 分支过滤（仅监听 main 分支）
- [ ] 多目标支持（不同事件发到不同群组）

## 故障排查

### 问题：Webhook 收不到消息

**检查清单：**
1. AstrBot 是否正常运行
2. 插件是否已加载（查看日志）
3. 端口 8080 是否开放（使用 `telnet 服务器IP 8080` 测试）
4. GitHub Webhook 配置的 URL 是否正确
5. 服务器防火墙/安全组是否开放端口

### 问题：收到 Webhook 但未转发消息

**检查清单：**
1. `target_umo` 配置是否正确
2. UMO 格式是否为 `platform_id:GroupMessage:群号`
3. AstrBot 是否能正常发送消息（手动测试）
4. 查看日志中的错误信息

### 问题：日志显示 "Platform not found"

**原因：** UMO 中的 platform_id 错误

**解决方法：**
1. 在目标群组发送 `/sid` 获取正确的 UMO
2. 使用返回的 UMO 更新配置

### 问题：日志显示 "Invalid signature"

**原因：** Webhook Secret 配置不正确或未同步

**解决方法：**
1. 检查 GitHub 仓库 Webhook 设置中的 Secret
2. 确保插件配置中的 `webhook_secret` 与 GitHub 设置一致
3. 更新配置后重启插件

### 问题：日志显示 "Rate limit exceeded"

**原因：** 请求数量超过配置的速率限制

**解决方法：**
1. 增加 `rate_limit` 配置值（默认 10 请求/分钟）
2. 设置为 0 禁用速率限制（不推荐）
3. 检查是否有恶意请求导致限流
3. 重启插件

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

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
