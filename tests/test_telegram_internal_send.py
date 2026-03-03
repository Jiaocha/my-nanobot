"""
Telegram Channel _internal_send 方法测试套件
===========================================

测试目标：覆盖 TelegramChannel._internal_send 方法的所有边界情况

调用链分析：
-------------
AgentLoop._process_message() 
    ↓ (通过 MessageTool.send_callback)
MessageBus.publish_outbound() 
    ↓ (事件订阅)
TelegramChannel.send() 
    ↓ (内部调用)
TelegramChannel._internal_send()

关键测试点：
1. 普通消息发送 (is_progress=False)
2. 进度消息发送与更新 (is_progress=True)
3. 消息编辑失败时的回退处理
4. 特殊字符和 Markdown 转义
5. 并发进度任务管理
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============== Fixtures ==============

@pytest.fixture
def mock_telegram_app():
    """模拟 Telegram Application 对象"""
    app = MagicMock()
    app.bot = AsyncMock()
    app.bot.send_message = AsyncMock()
    app.bot.edit_message_text = AsyncMock()
    return app


@pytest.fixture
def mock_bus():
    """模拟 MessageBus"""
    bus = MagicMock()
    bus.publish_outbound = AsyncMock()
    return bus


@pytest.fixture
def telegram_channel(mock_bus):
    """创建 TelegramChannel 实例用于测试"""
    from nanobot.channels.telegram import TelegramChannel
    from nanobot.config.schema import TelegramConfig

    config = TelegramConfig(token="test_token")
    channel = TelegramChannel(config=config, bus=mock_bus)
    return channel


# ============== 基础功能测试 ==============

@pytest.mark.asyncio
async def test_internal_send_normal_message(telegram_channel, mock_telegram_app):
    """
    测试场景：发送普通消息 (is_progress=False)
    预期结果：调用 send_message，不调用 edit_message_text
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    content = "你好，这是一条测试消息"
    metadata = {}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=False)

    # 验证结果
    mock_telegram_app.bot.send_message.assert_called_once()
    mock_telegram_app.bot.edit_message_text.assert_not_called()

    # 验证发送参数
    call_args = mock_telegram_app.bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == int(chat_id)
    assert "你好" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_internal_send_progress_message_first_time(telegram_channel, mock_telegram_app):
    """
    测试场景：首次发送进度消息 (is_progress=True, 无历史消息)
    预期结果：调用 send_message 创建新消息，保存 message_id
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    content = "正在处理中..."
    metadata = {"task_start_time": time.time()}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=True)

    # 验证结果
    mock_telegram_app.bot.send_message.assert_called_once()
    mock_telegram_app.bot.edit_message_text.assert_not_called()

    # 验证 message_id 被保存
    assert chat_id in telegram_channel._progress_messages


@pytest.mark.asyncio
async def test_internal_send_progress_message_update(telegram_channel, mock_telegram_app):
    """
    测试场景：更新现有进度消息 (is_progress=True, 有历史消息)
    预期结果：调用 edit_message_text 编辑消息，不调用 send_message
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    prev_msg_id = 987654
    telegram_channel._progress_messages[chat_id] = prev_msg_id

    content = "进度更新：50%"
    metadata = {"task_start_time": time.time()}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=True)

    # 验证结果
    mock_telegram_app.bot.edit_message_text.assert_called_once()
    mock_telegram_app.bot.send_message.assert_not_called()

    # 验证编辑参数
    call_args = mock_telegram_app.bot.edit_message_text.call_args
    assert call_args.kwargs["chat_id"] == int(chat_id)
    assert call_args.kwargs["message_id"] == prev_msg_id


# ============== 边界情况测试 ==============

@pytest.mark.asyncio
async def test_internal_send_edit_failure_fallback(telegram_channel, mock_telegram_app):
    """
    测试场景：编辑进度消息失败（例如消息已被删除）
    预期结果：回退到发送新消息，不抛出异常
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    prev_msg_id = 987654
    telegram_channel._progress_messages[chat_id] = prev_msg_id

    # 模拟编辑失败
    mock_telegram_app.bot.edit_message_text.side_effect = Exception("Message not found")

    content = "进度更新"
    metadata = {}

    # 执行测试（不应抛出异常）
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=True)

    # 验证回退行为：先尝试编辑，失败后发送新消息
    mock_telegram_app.bot.edit_message_text.assert_called_once()
    mock_telegram_app.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_internal_send_with_task_timer(telegram_channel, mock_telegram_app):
    """
    测试场景：进度消息包含任务计时器
    预期结果：消息文本包含耗时信息 [X.Xs]
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    start_time = time.time() - 5.5  # 5.5 秒前
    metadata = {"task_start_time": start_time}
    content = "处理中"

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=True)

    # 验证结果包含计时器
    call_args = mock_telegram_app.bot.send_message.call_args
    sent_text = call_args.kwargs["text"]
    assert "[5.5s]" in sent_text or "[5.6s]" in sent_text  # 允许微小时间误差


@pytest.mark.asyncio
async def test_internal_send_empty_content(telegram_channel, mock_telegram_app):
    """
    测试场景：发送空内容消息
    预期结果：正常处理，不抛出异常
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    content = ""
    metadata = {}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=False)

    # 验证仍然调用了发送
    mock_telegram_app.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_internal_send_special_characters(telegram_channel, mock_telegram_app):
    """
    测试场景：消息包含特殊字符（HTML 标签、emoji）
    预期结果：正确转义 HTML 特殊字符
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    content = "测试 <script>alert('xss')</script> & emoji 🚀"
    metadata = {}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=False)

    # 验证 HTML 转义
    call_args = mock_telegram_app.bot.send_message.call_args
    sent_text = call_args.kwargs["text"]
    assert "&lt;script&gt;" in sent_text  # HTML 标签应被转义
    assert "&amp;" in sent_text  # & 应被转义
    assert "🚀" in sent_text  # emoji 应保留


@pytest.mark.asyncio
async def test_internal_send_markdown_formatting(telegram_channel, mock_telegram_app):
    """
    测试场景：消息包含 Markdown 格式（代码块、粗体、链接）
    预期结果：正确转换为 Telegram HTML 格式
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "123456"
    content = """
# 标题
**粗体文本**
[链接](https://example.com)
`内联代码`
```python
print("代码块")
```
"""
    metadata = {}

    # 执行测试
    await telegram_channel._internal_send(chat_id, content, metadata, is_progress=False)

    # 验证转换结果
    call_args = mock_telegram_app.bot.send_message.call_args
    sent_text = call_args.kwargs["text"]
    assert "<b>粗体文本</b>" in sent_text
    assert '<a href="https://example.com">链接</a>' in sent_text
    assert "<code>内联代码</code>" in sent_text
    assert "<pre><code>" in sent_text  # 代码块


# ============== 并发场景测试 ==============

@pytest.mark.asyncio
async def test_internal_send_concurrent_progress_tasks(telegram_channel, mock_telegram_app):
    """
    测试场景：多个聊天 ID 同时进行进度任务
    预期结果：每个聊天的进度消息独立管理，互不干扰
    """
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_ids = ["111", "222", "333"]

    # 并发发送进度消息
    tasks = [
        telegram_channel._internal_send(cid, f"任务 {cid}", {}, is_progress=True)
        for cid in chat_ids
    ]
    await asyncio.gather(*tasks)

    # 验证每个聊天都有独立的进度消息记录
    assert len(telegram_channel._progress_messages) == 3
    for cid in chat_ids:
        assert cid in telegram_channel._progress_messages


@pytest.mark.asyncio
async def test_internal_send_invalid_chat_id(telegram_channel, mock_telegram_app):
    """
    测试场景：chat_id 无法转换为整数
    预期结果：处理异常，不导致程序崩溃，记录错误日志
    """
    from unittest.mock import patch
    # 设置环境
    telegram_channel._app = mock_telegram_app
    chat_id = "invalid_id"
    content = "测试"
    metadata = {}

    # 执行测试 (内部捕获了异常并记录日志)
    with patch("nanobot.channels.telegram.logger.error") as mock_log:
        await telegram_channel._internal_send(chat_id, content, metadata, is_progress=False)
        # 验证错误被记录
        mock_log.assert_called()
        assert "invalid_id" in str(mock_log.call_args[0])


# ============== 集成测试 ==============

    # 根据代码逻辑：
    # active_count <= 2: delay = 1.0 (Silky smooth)
    # active_count <= 5: delay = 2.0 (Power saving)
    # active_count > 5:  delay = 3.5 (Survival mode)
    # 这里 active_count=1，应该使用 1.0s 延迟


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
