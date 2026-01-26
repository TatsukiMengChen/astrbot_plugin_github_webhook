# 部署指南

本文档介绍如何在不同环境中部署插件。

## 防火墙配置

确保服务器防火墙允许访问配置的端口（默认 8080）：

### UFW (Ubuntu/Debian)

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

### firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### 云服务商安全组

在阿里云/腾讯云/AWS 等云服务商控制台添加入站规则开放 8080 端口。

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

## 内网穿透

如果你的服务器在内网，无法直接被 GitHub 访问，可以使用内网穿透工具。

### 使用 ngrok

```bash
# 安装 ngrok
brew install ngrok  # macOS
# 或从 https://ngrok.com 下载

# 启动隧道
ngrok http 8080

# 获取公网 URL，类似：https://abc123.ngrok.io
```

在 GitHub Webhook 中配置：
```
Payload URL: https://abc123.ngrok.io/webhook
```

### 使用 frp

参考 frp 官方文档配置反向代理。

## HTTPS 配置（可选）

如果你的服务器有 SSL 证书，可以使用 HTTPS 接收 Webhook 请求。

### 使用 Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /webhook {
        proxy_pass http://localhost:8080/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

在 GitHub Webhook 中配置：
```
Payload URL: https://your-domain.com/webhook
```

## 相关文档

- [安装指南](01-installation.md) - 基础安装步骤
- [配置说明](02-configuration.md) - 端口和安全配置
