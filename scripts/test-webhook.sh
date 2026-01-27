#!/bin/bash

# GitHub Webhook Plugin - 集成测试脚本
# 用法: ./test-webhook.sh [选项] <事件类型>

set -e

# 默认配置
DEFAULT_HOST="localhost"
DEFAULT_PORT="8080"
DEFAULT_SECRET=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    cat << EOF
GitHub Webhook 测试脚本

用法:
    $0 [选项] <事件类型>

选项:
    -H, --host HOST       服务器地址 (默认: localhost)
    -p, --port PORT       服务器端口 (默认: 8080)
    -s, --secret SECRET   Webhook 密钥 (默认: 无)
    -v, --verbose         详细输出
    -h, --help            显示帮助信息

事件类型:
    push              Push 事件
    issues            Issue 事件
    pr                Pull Request 事件
    ping              Ping 事件 (健康检查)

示例:
    # 发送 push 事件到默认服务器
    $0 push

    # 发送 PR 事件到指定端口
    $0 -p 6100 pr

    # 带密钥的测试
    $0 -s "my-secret" issues

    # 详细模式
    $0 -v push

EOF
}

# 解析参数
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
SECRET="$DEFAULT_SECRET"
VERBOSE=false
EVENT_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -s|--secret)
            SECRET="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        push|issues|pr|ping)
            EVENT_TYPE="$1"
            shift
            ;;
        *)
            echo -e "${RED}错误: 未知参数或事件类型 '$1'${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查是否指定了事件类型
if [[ -z "$EVENT_TYPE" ]]; then
    echo -e "${RED}错误: 必须指定事件类型${NC}"
    show_help
    exit 1
fi

# 构建 Webhook URL
WEBHOOK_URL="http://${HOST}:${PORT}/webhook"

echo -e "${GREEN}=== GitHub Webhook 测试 ===${NC}"
echo "事件类型: $EVENT_TYPE"
echo "目标地址: $WEBHOOK_URL"
echo ""

# 发送请求的函数
send_request() {
    local event_type="$1"
    local payload="$2"

    # 构建 curl 命令
    CURL_CMD="curl -s -X POST \"$WEBHOOK_URL\" \
        -H \"Content-Type: application/json\" \
        -H \"X-GitHub-Event: $event_type\""

    # 如果有密钥，添加签名头（简化版，实际使用 HMAC）
    if [[ -n "$SECRET" ]]; then
        CURL_CMD="$CURL_CMD \
        -H \"X-Hub-Signature-256: sha256=$(echo -n \"$payload\" | openssl dgst -sha256 -hmac \"$SECRET\" | awk '{print $2}')\""
    fi

    CURL_CMD="$CURL_CMD \
        -d '$payload'"

    if [[ "$VERBOSE" == true ]]; then
        echo -e "${YELLOW}发送请求...${NC}"
        echo "事件类型: $event_type"
        if [[ "$VERBOSE" == true ]]; then
            echo "Payload:"
            echo "$payload" | jq '.' 2>/dev/null || echo "$payload"
        fi
        echo ""
    fi

    # 执行请求
    RESPONSE=$(eval $CURL_CMD)
    EXIT_CODE=$?

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo -e "${GREEN}✓ 请求发送成功${NC}"
        if [[ "$VERBOSE" == true ]]; then
            echo "响应: $RESPONSE"
        fi
    else
        echo -e "${RED}✗ 请求失败 (退出码: $EXIT_CODE)${NC}"
        if [[ "$VERBOSE" == true ]]; then
            echo "响应: $RESPONSE"
        fi
    fi

    return $EXIT_CODE
}

# 生成测试 payload
case "$EVENT_TYPE" in
    push)
        PAYLOAD='{
  "ref": "refs/heads/main",
  "before": "a1b2c3d4e5f6g7h8i9j0",
  "after": "0j9i8h7g6f5e4d3c2b1a",
  "repository": {
    "id": 123456789,
    "name": "test-repo",
    "full_name": "testuser/test-repo",
    "private": false,
    "owner": {
      "login": "testuser",
      "type": "User"
    }
  },
  "pusher": {
    "name": "Test User",
    "email": "test@example.com"
  },
  "sender": {
    "login": "testuser",
    "type": "User"
  },
  "commits": [
    {
      "id": "1234567890abcdef",
      "message": "Test commit message",
      "timestamp": "2024-01-27T10:00:00Z",
      "author": {
        "name": "Test User",
        "email": "test@example.com"
      }
    }
  ]
}'
        send_request "push" "$PAYLOAD"
        ;;

    issues)
        PAYLOAD='{
  "action": "opened",
  "issue": {
    "id": 12345,
    "number": 1,
    "title": "Test Issue",
    "body": "This is a test issue",
    "state": "open",
    "user": {
      "login": "testuser",
      "type": "User"
    },
    "html_url": "https://github.com/testuser/test-repo/issues/1",
    "labels": []
  },
  "repository": {
    "id": 123456789,
    "name": "test-repo",
    "full_name": "testuser/test-repo",
    "private": false
  },
  "sender": {
    "login": "testuser",
    "type": "User"
  }
}'
        send_request "issues" "$PAYLOAD"
        ;;

    pr)
        PAYLOAD='{
  "action": "opened",
  "number": 10,
  "pull_request": {
    "id": 98765,
    "title": "Test Pull Request",
    "body": "This is a test PR",
    "state": "open",
    "user": {
      "login": "testuser",
      "type": "User"
    },
    "html_url": "https://github.com/testuser/test-repo/pull/10",
    "merged": false,
    "draft": false,
    "head": {
      "ref": "feature-branch",
      "sha": "a1b2c3d4"
    },
    "base": {
      "ref": "main",
      "sha": "e5f6g7h8"
    }
  },
  "repository": {
    "id": 123456789,
    "name": "test-repo",
    "full_name": "testuser/test-repo",
    "private": false
  },
  "sender": {
    "login": "testuser",
    "type": "User"
  }
}'
        send_request "pull_request" "$PAYLOAD"
        ;;

    ping)
        PAYLOAD='{
  "zen": "Keep it simple.",
  "hook_id": 12345
}'
        send_request "ping" "$PAYLOAD"
        ;;
esac

echo ""
echo -e "${GREEN}=== 测试完成 ===${NC}"
