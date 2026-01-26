# 开发相关

本文档介绍如何参与项目贡献和开发计划。

## 开发计划

### 已完成

- [x] Issues 事件支持
- [x] Pull Request 事件支持
- [x] Webhook Secret 签名验证
- [x] 请求速率限制
- [x] Agent 集成（智能消息生成）

### 计划中

- [ ] Release 事件支持
- [ ] 自定义消息模板（Jinja2）
- [ ] 分支过滤（仅监听 main 分支）
- [ ] 多目标支持（不同事件发到不同群组）

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交代码流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 在 GitHub 上提交 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 添加必要的注释和文档字符串
- 保持模块化和可维护性
- 更新相关文档

### 提交新功能

如果要添加新的 GitHub 事件支持：

1. 在 `handlers/` 目录创建新的 handler 文件
2. 在 `formatters/` 目录创建对应的 formatter
3. 在 `main.py` 的 `handle_webhook()` 中添加事件路由
4. 更新 `_conf_schema.json` 和相关文档
5. 添加使用示例到 `docs/03-usage.md`

### 添加新 Prompt 示例

1. 在 `prompts/` 目录创建新的 markdown 文件
2. 包含以下内容：
   - 提示词说明
   - 完整的提示词内容
   - 使用方法
   - 适用场景
   - 效果示例
3. 在文档索引中添加链接

## 测试

### 本地测试

1. 启动 AstrBot 并加载插件
2. 使用 curl 测试 Webhook 端点：
   ```bash
   curl -X POST http://localhost:8080/webhook \
     -H "Content-Type: application/json" \
     -d '{"ping": "test"}'
   ```
3. 检查 AstrBot 日志确认事件被正确接收

### GitHub Webhook 测试

1. 在 GitHub 仓库配置 Webhook
2. 选择 "Let me select individual events"
3. 勾选要测试的事件
4. 在仓库中触发相应操作（push、创建 issue 等）
5. 检查插件日志和群组消息

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件

## 作者

TatsukiMengChen

## 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 强大的聊天机器人框架
- [GitHub Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks) - GitHub 官方文档

## 相关资源

- [AstrBot 文档](https://docs.astrbot.net)
- [AstrBot 插件开发指南](https://docs.astrbot.net/dev/star/introduction)
- [GitHub Webhooks 文档](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
