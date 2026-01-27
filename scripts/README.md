# GitHub Webhook 测试工具

这个目录包含用于测试 GitHub Webhook 插件的脚本。

## test-webhook.sh

一个集成的测试脚本，支持通过命令行参数选择不同的事件类型。

### 功能

- 支持 4 种 GitHub 事件类型：push、issues、pull_request、ping
- 可自定义服务器地址和端口
- 支持 webhook 密钥签名
- 详细的输出模式

### 使用方法

#### 基本用法

```bash
# 发送 push 事件到默认服务器 (localhost:8080)
./test-webhook.sh push

# 发送 Pull Request 事件
./test-webhook.sh pr

# 发送 Issue 事件
./test-webhook.sh issues

# 发送 Ping 事件（健康检查）
./test-webhook.sh ping
```

#### 高级用法

```bash
# 指定端口
./test-webhook.sh -p 6100 push

# 使用 webhook 密钥
./test-webhook.sh -s "your-secret-here" issues

# 指定服务器地址
./test-webhook.sh -H 192.168.1.100 pr

# 详细输出模式（显示完整的 payload）
./test-webhook.sh -v push

# 组合参数
./test-webhook.sh -H localhost -p 6100 -s "secret" -v push
```

#### 参数说明

| 参数 | 长参数 | 说明 | 默认值 |
|------|--------|------|--------|
| `-H` | `--host` | 服务器地址 | localhost |
| `-p` | `--port` | 服务器端口 | 8080 |
| `-s` | `--secret` | Webhook 密钥 | 无 |
| `-v` | `--verbose` | 详细输出 | false |
| `-h` | `--help` | 显示帮助信息 | - |

#### 事件类型

| 事件类型 | 说明 |
|---------|------|
| `push` | 推送事件 - 测试代码推送通知 |
| `issues` | Issue 事件 - 测试 Issue 创建/更新 |
| `pr` | Pull Request 事件 - 测试 PR 创建/更新 |
| `ping` | Ping 事件 - 测试服务器连接 |

### 测试示例

#### 1. 测试默认配置

```bash
./test-webhook.sh push
```

输出：
```
=== GitHub Webhook 测试 ===
事件类型: push
目标地址: http://localhost:8080/webhook

✓ 请求发送成功

=== 测试完成 ===
```

#### 2. 测试特定端口

如果你的插件配置的端口是 6100：

```bash
./test-webhook.sh -p 6100 issues
```

#### 3. 详细模式查看 payload

```bash
./test-webhook.sh -v pr
```

这将显示完整的 JSON payload：
```json
{
  "action": "opened",
  "number": 10,
  "pull_request": {
    "id": 98765,
    "title": "Test Pull Request",
    ...
  }
}
```

#### 4. 测试 webhook 签名验证

如果你的插件配置了 webhook_secret：

```bash
./test-webhook.sh -s "my-webhook-secret" push
```

脚本会自动计算 HMAC-SHA256 签名并添加到 `X-Hub-Signature-256` 请求头中。

### 注意事项

1. **确保插件已启动**：测试前请确保 AstrBot 和插件已正确启动
2. **端口配置**：使用 `-p` 参数指定正确的端口，需要与插件配置的端口一致
3. **密钥配置**：如果插件启用了签名验证，必须使用 `-s` 参数提供相同的密钥
4. **防火墙**：如果是远程测试，确保防火墙允许访问该端口

### 故障排查

#### 连接被拒绝

```
✗ 请求失败 (退出码: 7)
```

可能原因：
- 插件未启动
- 端口号错误
- 防火墙阻止连接

解决方法：
```bash
# 检查端口是否被监听
lsof -i :8080
```

#### 签名验证失败

如果启用了签名验证但未提供密钥，请求会被拒绝（HTTP 401）。

#### 速率限制

如果插件配置了速率限制，发送过多请求会返回 HTTP 429。

### 自定义 payload

如需使用自定义的 payload，可以修改脚本中的 `PAYLOAD` 变量，或直接使用 curl：

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/main",
    "repository": {
      "name": "my-repo"
    }
  }'
```

### 依赖

- `curl` - 用于发送 HTTP 请求
- `jq` - 用于格式化 JSON 输出（可选，详细模式使用）

安装依赖：
```bash
# macOS
brew install curl jq

# Ubuntu/Debian
sudo apt-get install curl jq

# CentOS/RHEL
sudo yum install curl jq
```
