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

## 常见问题

### 问题：配置更新或版本更新后不生效

**现象**：
- 在 WebUI 中修改了配置（如 `llm_provider_id`、`agent_system_prompt`）
- 但插件行为没有变化，仍在使用旧配置
- 重启 AstrBot 后配置生效

**可能原因**：
1. 配置未正确保存到持久化存储
2. 插件缓存了旧配置
3. 配置值类型错误（见下方 "配置值类型错误"）
4. 云端环境和本地环境配置同步延迟

**解决方法**：

#### 方法 1：重启 AstrBot（推荐）

在命令行中重启 AstrBot：

```bash
# 如果使用 systemd
sudo systemctl restart astrbot

# 或手动重启
# Ctrl+C 停止后重新运行
```

**验证配置已加载**：
重启后查看日志，应该看到配置快照：

```
============================================================
GitHub Webhook: Configuration loaded
  target_umo: platform_id:GroupMessage:1078537517
  enable_agent: True
  llm_provider_id: openai:gpt-4
  agent_timeout: 30s
  agent_system_prompt: 1250 chars
  rate_limit: 10 req/min
============================================================
```

如果看到上述日志，说明新配置已生效。

#### 方法 2：检查配置值类型

确保配置字段类型正确。本插件的 `_conf_schema.json` 中，所有需要用户输入的配置字段都应该是：

```json
{
  "enable_agent": {
    "type": "string",    // ✅ 正确
    ...
  },
  "llm_provider_id": {
    "type": "string",    // ✅ 正确
    ...
  },
  "agent_system_prompt": {
    "type": "string",    // ✅ 正确
    ...
  }
}
```

**注意**：
- 如果字段类型是 `"text"` 而不是 `"string"`，AstrBot 配置系统可能无法正确读取
- 配置类型错误会导致 WebUI 中的输入无法被正确解析
- 所有需要用户输入的配置字段都应该是 `"string"` 类型

#### 方法 3：查看完整的配置日志

插件初始化时会输出配置快照（60 个 `=` 号分隔），如果配置没有正确加载，可以通过日志诊断。

**配置正常**：
```
============================================================
GitHub Webhook: Configuration loaded
  target_umo: ...
  enable_agent: True/False
  llm_provider_id: ... 或 (default)
  ...
============================================================
```

**配置异常**（缺少配置快照）：
- 如果日志中没有看到上述分隔线
- 说明插件初始化时配置读取可能失败
- 检查 AstrBot 日志中是否有其他错误信息

---

### 问题：LLM 输出只有标题，缺少详细内容

**现象**：
- Commit message 是完整的（多行内容、详细描述）
- 但 LLM 生成的消息只有标题
- 丢失了关键信息

**可能原因**：

#### 原因 1：系统提示词过长（占用 token）

如果配置的系统提示词太长（例如 50+ 行），会占用大量 token 空间，导致 GitHub 事件内容被压缩或忽略。

**诊断方法**：
查看日志中的长度信息：

```
============================================================
GitHub Webhook: LLM Processing for push event
  Provider: (default)
  Input length: 523 chars
  Input preview (first 300 chars): GitHub 事件信息：
...
  System prompt length: 1250 chars
============================================================
```

如果看到系统提示词过长（如 1250+ 字符），建议缩短或简化。

#### 原因 2：Prompt 结构问题

如果 GitHub 事件信息放在 prompt 的中间或后面，LLM 可能只关注前面的系统提示词部分。

**诊断方法**：
1. 简化系统提示词，将主要指令移到 `system_prompt` 参数
2. GitHub 事件信息放在 prompt 的最前面
3. 减少 prompt 中的冗余描述

#### 原因 3：LLM 上下文限制

某些 LLM Provider 的上下文窗口有限制（如 4096 tokens），如果输入太长会被截断。

**诊断方法**：
1. 查看日志中的 "Output length"
2. 如果输出过短（< 100 字符），但输入很长，可能是截断
3. 日志会警告："LLM output suspiciously short"

**示例日志（截断警告）**：
```
GitHub Webhook: LLM response received, length: 312 chars
  Output preview (first 300 chars): [推送] TatsukiMengChen/astrbot_plugin_github_webhook
-----------------------------------------------------------------
GitHub Webhook: LLM output suspiciously short (input: 523 chars, output: 312 chars)
```

---

### 问题：配置值类型错误

**现象**：
- 在 WebUI 中填写了配置（如 `enable_agent`、`agent_system_prompt`）
- 保存后没有效果
- 查看 `_conf_schema.json`，发现字段类型是 `"text"`

**错误示例**：
```json
{
  "enable_agent": {
    "type": "text",     // ❌ 错误！
    ...
  }
}
```

**正确配置**：
```json
{
  "enable_agent": {
    "type": "string",    // ✅ 正确
    ...
  }
}
```

**解决方法**：
1. 修改 `_conf_schema.json`，将字段类型从 `"text"` 改为 `"string"`
2. 更新后重启 AstrBot
3. 验证配置是否正确加载

**注意事项**：
- 所有需要用户输入的配置字段都应该是 `"string"` 类型
- `"text"` 类型通常用于多行文本内容（如描述），不适合简单的布尔或字符串值

---

### 问题：云端环境配置与本地不一致

**现象**：
- 本地开发环境配置正常工作
- 云端生产环境相同配置不生效

**可能原因**：
1. 配置文件在不同步或未正确上传
2. 插件读取了缓存配置而不是最新配置
3. 插件初始化时机问题

**解决方法**：

#### 方法 1：使用配置快照日志诊断

在云端 AstrBot 日志中查找 "Configuration loaded" 快照，对比 WebUI 中的配置：

```bash
# 查找配置加载日志
grep "GitHub Webhook: Configuration loaded" astrbot.log
```

检查以下关键值：
- `enable_agent` 是否为预期的 True/False
- `llm_provider_id` 是否为正确的 provider ID
- `agent_system_prompt` 长度是否正确

#### 方法 2：强制重新加载插件配置

如果配置在 WebUI 中更新但插件未使用新值：

1. 在 AstrBot WebUI 中禁用插件
2. 点击"保存配置"
3. 重新启用插件
4. 查看日志确认新配置已加载

#### 方法 3：检查配置文件权限

确保插件配置文件可以被正确读取：

```bash
# 检查文件权限
ls -la data/config/astrbot_plugin_github_webhook_config.json

# 如果权限不正确，修复
chmod 644 data/config/astrbot_plugin_github_webhook_config.json
```

---

### 问题：Webhook Secret 配置不生效

**现象**：
- 在插件中配置了 `webhook_secret`
- GitHub Webhook 提示 "Invalid signature"
- 配置看起来正确

**可能原因**：
1. GitHub 仓库中的 Secret 配置与插件不一致
2. 插件配置中包含多余空格或隐藏字符
3. Secret 在复制粘贴时引入了错误字符

**解决方法**：

#### 方法 1：重新生成 GitHub Webhook Secret

1. 进入 GitHub 仓库 → Settings → Webhooks
2. 找到对应的 webhook
3. 点击 "Edit"
4. 滚动到 "Secret" 部分
5. 点击 "Update" 或 "Regenerate" 重新生成 Secret
6. 复制新的 Secret
7. 在插件配置中更新 `webhook_secret` 字段

#### 方法 2：临时禁用签名验证进行调试

如果需要调试签名验证问题，可以临时禁用：

1. 将插件配置中的 `webhook_secret` 清空
2. 更新配置
3. 测试 webhook 是否正常（会看到日志 "Signature verification disabled"）
4. 确认正常后重新配置正确的 Secret
5. 重新启用签名验证

---

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
  4. 留空则禁用签名验证（生产环境不推荐）
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

## Docker 部署

如果你的 AstrBot 使用 Docker 部署，需要特别注意端口映射配置。

### 注意事项

**重要**：如果 AstrBot 在 Docker 容器中运行，容器的内部端口（如 8080）必须映射到宿主机端口，否则外部（包括 GitHub webhook）无法访问。

### 方法 1：使用 Docker Compose（推荐）

编辑 `docker-compose.yml`：

```yaml
version: '3'

services:
  astrbot:
    image: ghcr.io/astrbotdev/astrbot:latest
    container_name: astrbot
    restart: unless-stopped
    
    # 数据卷映射
    volumes:
      - ./AstrBot:/app
      - ./data:/app/data
    
    # ← 关键配置：端口映射
    ports:
      - "8080:8080"  # 宿主机:容器端口
    
    environment:
      - TZ=Asia/Shanghai
```

**说明**：
- `"8080:8080"` 表示：宿主机 8080 端口 → 容器 8080 端口
- 插件配置的 `port` 参数应与容器端口一致（8080）

### 方法 2：使用 docker run 命令

```bash
# 停止现有容器
docker stop astrbot

# 重新启动，添加端口映射
docker run -d \
  --name astrbot \
  -v ./AstrBot:/app \
  -v ./data:/app/data \
  -p 8080:8080 \
  ghcr.io/astrbotdev/astrbot:latest
```

### 验证 Docker 端口映射

```bash
# 1. 查看容器端口映射
docker port astrbot

# 应该看到类似输出：
# 8080/tcp -> 0.0.0.0.8080

# 2. 检查容器是否运行
docker ps | grep astrbot

# 3. 查看容器日志
docker logs astrbot | tail -20

# 4. 从宿主机测试端口
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"ping": "test"}'
```

### Docker 端口配置 + 插件配置示例

如果 Docker 端口映射为 `8080:8080`：

```json
// 插件配置文件（data/config/astrbot_plugin_github_webhook_config.json）
{
  "port": 8080,  // ← 这里配置容器端口（不是宿主机端口）
  "target_umo": "default:GroupMessage:群号",
  "webhook_secret": "your_github_webhook_secret",
  "rate_limit": 10
}

// GitHub Webhook 配置
Payload URL: http://你的服务器IP:8080/webhook  // ← 使用宿主机端口
```

**关键区别**：
- Docker 端口映射：`"8080:8080"` （宿主机:容器端口）
- 插件配置 `port`: `8080` （容器内部端口）
- GitHub webhook URL: `http://IP:8080` （使用宿主机端口）

## 常见问题

### 问题：配置更新或版本更新后不生效

**现象**：
- 在 WebUI 中修改了配置（如 `llm_provider_id`、`agent_system_prompt`）
- 但插件行为没有变化，仍在使用旧配置
- 重启 AstrBot 后配置生效

**可能原因**：
1. 配置未正确保存到持久化存储
2. 插件缓存了旧配置
3. 配置值类型错误（见下方 "配置值类型错误"）
4. 云端环境和本地环境配置同步延迟

**解决方法**：

#### 方法 1：重启 AstrBot（推荐）

在命令行中重启 AstrBot：

```bash
# 如果使用 systemd
sudo systemctl restart astrbot

# 或手动重启
# Ctrl+C 停止后重新运行
```

**验证配置已加载**：
重启后查看日志，应该看到配置快照：

```
============================================================
GitHub Webhook: Configuration loaded
  target_umo: platform_id:GroupMessage:1078537517
  enable_agent: True
  llm_provider_id: openai:gpt-4
  agent_timeout: 30s
  agent_system_prompt: 1250 chars
  rate_limit: 10 req/min
============================================================
```

如果看到上述日志，说明新配置已生效。

#### 方法 2：检查配置值类型

确保配置字段类型正确。本插件的 `_conf_schema.json` 中，所有字段类型应该是：

```json
{
  "enable_agent": "string",      // ✅ 正确
  "llm_provider_id": "string",  // ✅ 正确
  "agent_system_prompt": "string", // ✅ 正确
  ...
}
```

**注意**：
- 如果字段类型是 `"text"` 而不是 `"string"`，AstrBot 配置系统可能无法正确读取
- 配置类型错误会导致 WebUI 中的输入无法被正确解析

#### 方法 3：查看完整的配置日志

插件初始化时会输出配置快照（60 个 `=` 号分隔），如果配置没有正确加载，可以通过日志诊断。

**配置正常**：
```
============================================================
GitHub Webhook: Configuration loaded
  target_umo: ...
  enable_agent: True/False
  llm_provider_id: ... 或 (default)
  ...
============================================================
```

**配置异常**（缺少配置快照）：
- 如果日志中没有看到上述分隔线
- 说明插件初始化时配置读取可能失败
- 检查 AstrBot 日志中是否有其他错误信息

---

### 问题：LLM 输出只有标题，缺少详细内容

**现象**：
- Commit message 是完整的（多行内容、详细描述）
- 但 LLM 生成的消息只有标题（title）
- 丢失了关键信息（commit 内容、问题描述等）

**可能原因**：

#### 原因 1：系统提示词过长（占用 token）

如果配置的系统提示词太长（例如 50+ 行），会占用大量 token 空间，导致 GitHub 事件内容被压缩或忽略。

**诊断方法**：
查看日志中的长度信息：

```
============================================================
GitHub Webhook: LLM Processing for push event
  Provider: (default)
  Input length: 523 chars
  Input preview (first 300 chars): GitHub 事件信息：
...
  System prompt length: 1250 chars
============================================================
```

如果看到系统提示词过长（如 1250+ 字符），建议缩短或简化。

#### 原因 2：Prompt 结构问题

如果 GitHub 事件信息放在 prompt 的中间或后面，LLM 可能只关注前面的系统提示词部分。

**诊断方法**：
1. 简化系统提示词，将主要指令移到 `system_prompt` 参数
2. GitHub 事件信息放在 prompt 的最前面
3. 减少 prompt 中的冗余描述

#### 原因 3：LLM 上下文限制

某些 LLM Provider 的上下文窗口有限制（如 4096 tokens），如果输入太长会被截断。

**诊断方法**：
1. 查看日志中的 "Output length"
2. 如果输出过短（< 100 字符），但输入很长，可能是截断
3. 日志会警告："LLM output suspiciously short"

**示例日志（截断警告）**：
```
GitHub Webhook: LLM response received, length: 312 chars
  Output preview (first 300 chars): [推送] TatsukiMengChen/astrbot_plugin_github_webhook
-----------------------------------------------------------------
GitHub Webhook: LLM output suspiciously short (input: 523 chars, output: 312 chars)
```

---

### 问题：配置值类型错误

**现象**：
- 在 WebUI 中填写了配置（如 `enable_agent`、`agent_system_prompt`）
- 保存后没有效果
- 查看 `_conf_schema.json`，发现字段类型是 `"text"` 而不是 `"string"`

**错误示例**：
```json
{
  "enable_agent": {
    "type": "text",     // ❌ 错误！
    ...
  }
}
```

**正确配置**：
```json
{
  "enable_agent": {
    "type": "string",    // ✅ 正确
    ...
  }
}
```

**解决方法**：
1. 修改 `_conf_schema.json`，将字段类型从 `"text"` 改为 `"string"`
2. 更新后重启 AstrBot
3. 验证配置是否正确加载

**注意事项**：
- 所有需要用户输入的配置字段都应该是 `"string"` 类型
- `"text"` 类型通常用于多行文本内容（如描述），不适合简单的布尔或字符串值

---

### 问题：云端环境配置与本地不一致

**现象**：
- 本地开发环境配置正常工作
- 云端生产环境相同配置不生效

**可能原因**：
1. 配置文件在不同步或未正确上传
2. 插件读取了缓存配置而不是最新配置
3. 插件初始化时机问题

**解决方法**：

#### 方法 1：使用配置快照日志诊断

在云端 AstrBot 日志中查找 "Configuration loaded" 快照，对比 WebUI 中的配置：

```bash
# 查找配置加载日志
grep "GitHub Webhook: Configuration loaded" astrbot.log
```

检查以下关键值：
- `enable_agent` 是否为预期的 True/False
- `llm_provider_id` 是否为正确的 provider ID
- `agent_system_prompt` 长度是否正确

#### 方法 2：强制重新加载插件配置

如果配置在 WebUI 中更新但插件未使用新值：

1. 在 AstrBot WebUI 中禁用插件
2. 点击"保存配置"
3. 重新启用插件
4. 查看日志确认新配置已加载

#### 方法 3：检查配置文件权限

确保插件配置文件可以被正确读取：

```bash
# 检查文件权限
ls -la data/config/astrbot_plugin_github_webhook_config.json

# 如果权限不正确，修复
chmod 644 data/config/astrbot_plugin_github_webhook_config.json
```

---

## 常见问题

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
