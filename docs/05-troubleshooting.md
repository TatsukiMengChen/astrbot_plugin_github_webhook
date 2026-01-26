# 故障排查

本文档介绍常见问题及解决方案。

## 配置更新或版本更新后不生效

### 现象

- 在 WebUI 中修改了配置（如 `llm_provider_id`、`agent_system_prompt`）
- 但插件行为没有变化，仍在使用旧配置
- 重启 AstrBot 后配置生效

### 可能原因

1. 配置未正确保存到持久化存储
2. 插件缓存了旧配置
3. 配置值类型错误
4. 云端环境和本地环境配置同步延迟

### 解决方法

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

#### 方法 2：查看完整的配置日志

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

## LLM 输出只有标题，缺少详细内容

### 现象

- Commit message 是完整的（多行内容、详细描述）
- 但 LLM 生成的消息只有标题（title）
- 丢失了关键信息（commit 内容、问题描述等）

### 可能原因

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

## Webhook Secret 配置不生效

### 现象

- 在插件中配置了 `webhook_secret`
- GitHub Webhook 提示 "Invalid signature"
- 配置看起来正确

### 可能原因

1. GitHub 仓库中的 Secret 配置与插件不一致
2. 插件配置中包含多余空格或隐藏字符
3. Secret 在复制粘贴时引入了错误字符

### 解决方法

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

## 云端环境配置与本地不一致

### 现象

- 本地开发环境配置正常工作
- 云端生产环境相同配置不生效

### 可能原因

1. 配置文件不同步或未正确上传
2. 插件读取了缓存配置而不是最新配置
3. 插件初始化时机问题

### 解决方法

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

## 获取更多帮助

如果以上方法都无法解决你的问题：

1. 查看 AstrBot 主日志，寻找错误信息
2. 检查插件日志，确认事件是否被正确接收
3. 在 GitHub 仓库提交 Issue，提供详细的错误信息和日志

## 相关文档

- [配置说明](02-configuration.md) - 了解配置项含义
- [使用示例](03-usage.md) - 查看预期消息格式
