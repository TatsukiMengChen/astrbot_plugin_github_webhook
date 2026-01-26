"""LLM service for message generation."""

import asyncio
import json

from astrbot.api import logger


async def send_with_agent(plugin_instance, message: str, data: dict, event_type: str):
    """使用 LLM 生成个性化消息并发送"""
    try:
        # 构建 LLM 任务的 prompt
        event_name = {
            "push": "代码推送",
            "issues": "问题",
            "pull_request": "拉取请求",
        }.get(event_type, event_type)

        # 构建 LLM 输入信息 - 优化结构，确保 GitHub 事件内容优先级最高
        llm_input = f"""GitHub 事件信息：

{message}

任务：生成一条简洁、有趣的 QQ 群消息通知。
要求：
1. 消息要简洁明了
2. 可以使用 emoji 增加趣味性
3. 保留关键信息（作者、仓库、标题、URL等）
4. 如果有链接（commit URL、issue URL、PR URL），必须保留
5. 使用友好、生动的语气

请直接输出最终的消息内容，不要有多余的解释。
"""

        # 诊断日志
        logger.info("=" * 60)
        logger.info(f"GitHub Webhook: LLM Processing for {event_type} event")
        logger.info(f"  Provider: {plugin_instance.cfg.llm_provider_id or '(default)'}")
        logger.info(f"  Input length: {len(llm_input)} chars")
        logger.info(f"  Input preview (first 300 chars): {llm_input[:300]}...")
        if plugin_instance.cfg.agent_system_prompt:
            logger.info(
                f"  System prompt length: {len(plugin_instance.cfg.agent_system_prompt)} chars"
            )
        logger.info("=" * 60)

        # 获取 LLM provider ID
        if plugin_instance.cfg.llm_provider_id:
            provider_id = plugin_instance.cfg.llm_provider_id
        else:
            # 使用默认 provider
            try:
                provider_id = (
                    await plugin_instance.context.get_current_chat_provider_id(
                        plugin_instance.cfg.target_umo
                    )
                )
                logger.info(f"GitHub Webhook: Using default provider: {provider_id}")
            except Exception as e:
                logger.warning(
                    f"GitHub Webhook: Failed to get default provider: {e}, falling back to template"
                )
                await plugin_instance.send_message(message)
                return

        # 调用 LLM
        try:
            llm_response = await asyncio.wait_for(
                plugin_instance.context.llm_generate(
                    chat_provider_id=provider_id,
                    prompt=llm_input,
                    system_prompt=plugin_instance.cfg.agent_system_prompt or None,
                ),
                timeout=plugin_instance.cfg.agent_timeout,
            )
            logger.info(
                f"GitHub Webhook: LLM response received, length: {len(llm_response.completion_text) if llm_response else 0}"
            )

            # 诊断日志：输出长度和内容
            output_text = llm_response.completion_text if llm_response else ""
            logger.info(f"  Output length: {len(output_text)} chars")
            if output_text:
                logger.info(
                    f"  Output preview (first 300 chars): {output_text[:300]}..."
                )

            # 检测输出是否可能被截断
            if output_text and len(output_text) < 100:
                logger.warning(
                    f"GitHub Webhook: LLM output suspiciously short (input: {len(llm_input)} chars, output: {len(output_text)} chars)"
                )

            # 从 LLM 响应中提取纯文本内容
            if llm_response and llm_response.completion_text:
                # 直接使用 LLM 返回的文本
                text_content = llm_response.completion_text.strip()

                # 清理空行
                text_content = "\n".join(
                    line.strip() for line in text_content.split("\n") if line.strip()
                )

                if text_content:
                    generated_message = text_content
                    logger.info(
                        f"GitHub Webhook: Generated message: {generated_message[:100]}..."
                    )
                    await plugin_instance.send_message(generated_message)
                else:
                    logger.warning(
                        "GitHub Webhook: LLM returned empty content, falling back to template"
                    )
                    await plugin_instance.send_message(message)
            else:
                logger.warning(
                    "GitHub Webhook: LLM returned None or empty completion, falling back to template"
                )
                await plugin_instance.send_message(message)

        except asyncio.TimeoutError:
            logger.error(
                f"GitHub Webhook: LLM timeout after {plugin_instance.cfg.agent_timeout} seconds, falling back to template"
            )
            await plugin_instance.send_message(message)

    except Exception as e:
        # LLM 调用失败，使用模板作为降级方案
        logger.error(f"GitHub Webhook: LLM invocation failed: {e}")
        logger.error("GitHub Webhook: Falling back to default template")
        await plugin_instance.send_message(message)
