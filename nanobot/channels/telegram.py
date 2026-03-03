"""Telegram channel implementation using python-telegram-bot."""

from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path

from loguru import logger
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import TelegramConfig


def _markdown_to_telegram_html(text: str) -> str:
    """Convert markdown to Telegram-safe HTML."""
    if not text: return ""
    code_blocks: list[str] = []
    def save_code_block(m: re.Match) -> str:
        code_blocks.append(m.group(1)); return f"\x00CB{len(code_blocks) - 1}\x00"
    text = re.sub(r'```[\w]*\n?([\s\S]*?)```', save_code_block, text)
    inline_codes: list[str] = []
    def save_inline_code(m: re.Match) -> str:
        inline_codes.append(m.group(1)); return f"\x00IC{len(inline_codes) - 1}\x00"
    text = re.sub(r'`([^`]+)`', save_inline_code, text)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*(.*)$', r'\1', text, flags=re.MULTILINE)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    text = re.sub(r'(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])', r'<i>\1</i>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)
    for i, code in enumerate(inline_codes):
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00IC{i}\x00", f"<code>{escaped}</code>")
    for i, code in enumerate(code_blocks):
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00CB{i}\x00", f"<pre><code>{escaped}</code></pre>")
    return text


class TelegramChannel(BaseChannel):
    name = "telegram"
    BOT_COMMANDS = [
        BotCommand("new", "✨ 开启新会话"),
        BotCommand("prune", "🧹 记忆审计与整理"),
        BotCommand("mcp", "🛠️ 检查外部工具状态"),
        BotCommand("tools", "🔧 查看可用工具集"),
        BotCommand("config", "⚙️ 配置文件摘要"),
        BotCommand("weather", "🌤️ 实时天气"),
        BotCommand("memory", "🧠 搜索记忆"),
        BotCommand("status", "📊 系统状态"),
        BotCommand("cleanup", "🗑️ 清理缓存"),
        BotCommand("stop", "⏹️ 停止任务"),
        BotCommand("help", "❓ 使用帮助"),
    ]

    def __init__(self, config: TelegramConfig, bus: MessageBus, groq_api_key: str = ""):
        super().__init__(config, bus)
        self.config = config
        self._app: Application | None = None
        self._typing_tasks: dict[str, asyncio.Task] = {}
        self._progress_tasks: dict[str, asyncio.Task] = {}
        self._progress_messages: dict[str, int] = {} # chat_id -> last progress msg_id
        self._progress_data: dict[str, dict] = {} # chat_id -> {content, metadata}
        self._last_update_time: dict[str, float] = {}

    async def _internal_send(self, chat_id_str: str, content: str, metadata: dict, is_progress: bool) -> None:
        now = time.time()
        # Basic Throttling for progress updates from bus
        if is_progress:
            last_t = self._last_update_time.get(chat_id_str, 0)
            if now - last_t < 0.5: return
            self._last_update_time[chat_id_str] = now
            self._progress_data[chat_id_str] = {"content": content, "metadata": metadata}

            spinners = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
            spinner = spinners[int(now * 1.5) % len(spinners)]
            timer_str = ""
            if start_time := metadata.get("task_start_time"):
                timer_str = f" <code>[{now - float(start_time):.1f}s]</code>"
            display_text = f"{spinner} {content}{timer_str}"
        else:
            display_text = content

        html = _markdown_to_telegram_html(display_text)

        # Telegram limit is 4096. Use 4000 for safety.
        LIMIT = 4000

        if is_progress:
            if len(html) > LIMIT:
                html = html[:LIMIT-3] + "..."

            prev_msg_id = self._progress_messages.get(chat_id_str)
            if prev_msg_id:
                try:
                    await self._app.bot.edit_message_text(
                        chat_id=int(chat_id_str), message_id=prev_msg_id,
                        text=html, parse_mode="HTML"
                    )
                    return
                except Exception: pass

        # Split long regular messages
        if len(html) <= LIMIT:
            chunks = [html]
        else:
            chunks = []
            current = html
            while len(current) > LIMIT:
                # Try to split at last newline before LIMIT
                split_idx = current.rfind("\n", 0, LIMIT)
                if split_idx == -1: split_idx = LIMIT
                chunks.append(current[:split_idx])
                current = current[split_idx:].lstrip()
            if current: chunks.append(current)

        for chunk in chunks:
            try:
                sent = await self._app.bot.send_message(chat_id=int(chat_id_str), text=chunk, parse_mode="HTML")
                if is_progress: self._progress_messages[chat_id_str] = sent.message_id
            except Exception as e:
                logger.error("Send failed to chat_id={}: {}", chat_id_str, e)
                # Fallback: if HTML parsing failed (likely due to split in middle of tag), send as plain text
                try:
                    sent = await self._app.bot.send_message(chat_id=int(chat_id_str), text=chunk[:LIMIT])
                    if is_progress: self._progress_messages[chat_id_str] = sent.message_id
                except Exception as e2:
                    logger.error("Plain text fallback failed: {}", e2)

    async def send(self, msg: OutboundMessage) -> None:
        if not self._app: return
        chat_id_str = str(msg.chat_id)
        is_progress = msg.metadata.get("_progress", False)

        if not is_progress:
            self._stop_progress_loop(chat_id_str)
            self._progress_messages.pop(chat_id_str, None)
            self._progress_data.pop(chat_id_str, None)

        self._stop_typing(msg.chat_id)

        if is_progress:
            await self._internal_send(chat_id_str, msg.content, msg.metadata, is_progress)
            self._start_progress_loop(chat_id_str)
        else:
            await self._internal_send(chat_id_str, msg.content, msg.metadata, is_progress)

    def _start_progress_loop(self, chat_id: str) -> None:
        if chat_id not in self._progress_tasks:
            self._progress_tasks[chat_id] = asyncio.create_task(self._progress_update_loop(chat_id))

    def _stop_progress_loop(self, chat_id: str) -> None:
        if task := self._progress_tasks.pop(chat_id, None):
            task.cancel()

    async def _progress_update_loop(self, chat_id: str) -> None:
        """Keep the spinner spinning and timer counting."""
        try:
            while self._running:
                await asyncio.sleep(0.6)
                data = self._progress_data.get(chat_id)
                if not data: continue

                # Update without throttling
                now = time.time()
                self._last_update_time[chat_id] = now

                spinners = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
                spinner = spinners[int(now * 1.5) % len(spinners)]
                timer_str = ""
                metadata = data["metadata"]
                if start_time := metadata.get("task_start_time"):
                    timer_str = f" <code>[{now - float(start_time):.1f}s]</code>"

                display_text = f"{spinner} {data['content']}{timer_str}"
                html = _markdown_to_telegram_html(display_text)
                if len(html) > 4000: html = html[:3997] + "..."

                msg_id = self._progress_messages.get(chat_id)
                if msg_id:
                    try:
                        await self._app.bot.edit_message_text(
                            chat_id=int(chat_id), message_id=msg_id,
                            text=html, parse_mode="HTML"
                        )
                    except Exception: pass
        except asyncio.CancelledError: pass
        except Exception as e: logger.debug("Progress loop error for {}: {}", chat_id, e)

    async def start(self) -> None:
        if not self.config.token: return
        self._running = True
        req = HTTPXRequest(connection_pool_size=16, proxy=self.config.proxy)
        self._app = Application.builder().token(self.config.token).request(req).build()
        self._app.add_handler(CommandHandler(["start"], self._on_start))
        self._app.add_handler(CommandHandler(["new", "prune", "mcp", "tools", "config", "weather", "memory", "status", "cleanup", "stop", "help"], self._forward_command))
        self._app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL) & ~filters.COMMAND, self._on_message))
        await self._app.initialize()
        await self._app.start()
        await self._app.bot.set_my_commands(self.BOT_COMMANDS)
        await self._app.updater.start_polling(allowed_updates=["message"], drop_pending_updates=True)
        while self._running: await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False
        if self._app:
            await self._app.updater.stop(); await self._app.stop(); await self._app.shutdown()

    @staticmethod
    def _sender_id(user) -> str:
        return f"{user.id}|{user.username}" if user.username else str(user.id)

    async def _forward_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user: return
        await self._handle_message(sender_id=self._sender_id(update.effective_user), chat_id=str(update.message.chat_id), content=update.message.text)

    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message: await update.message.reply_text("👋 你好！我是 nanobot。发送消息开始对话。")

    async def _on_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message: await update.message.reply_text("使用 /help 查看详细指南。")

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages including text, photos, and documents."""
        if not update.message or not update.effective_user:
            return
        msg, user = update.message, update.effective_user
        self._start_typing(str(msg.chat_id))

        # Handle media - download to local and pass file paths
        media_paths = []
        media_dir = Path.home() / ".nanobot" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Download photos (largest size)
        if msg.photo:
            try:
                photo = msg.photo[-1]  # Largest size
                file = await context.bot.get_file(photo.file_id)
                file_path = media_dir / f"{photo.file_id}.jpg"
                await file.download_to_drive(str(file_path))
                media_paths.append(str(file_path))
                logger.debug("Downloaded photo to {}", file_path)
            except Exception as e:
                logger.warning("Failed to download photo: {}", e)

        # Download documents
        if msg.document:
            try:
                doc = msg.document
                file = await context.bot.get_file(doc.file_id)
                ext = doc.file_name.split(".")[-1] if doc.file_name else "bin"
                file_path = media_dir / f"{doc.file_id}.{ext}"
                await file.download_to_drive(str(file_path))
                media_paths.append(str(file_path))
                logger.debug("Downloaded document to {}", file_path)
            except Exception as e:
                logger.warning("Failed to download document: {}", e)

        # Build content
        content = msg.text or msg.caption or ""
        if not content and media_paths:
            content = "请描述这张图片"

        await self._handle_message(
            sender_id=self._sender_id(user),
            chat_id=str(msg.chat_id),
            content=content,
            media=media_paths if media_paths else None,
            metadata={"message_id": msg.message_id}
        )

    def _start_typing(self, chat_id: str) -> None:
        self._stop_typing(chat_id)
        self._typing_tasks[chat_id] = asyncio.create_task(self._typing_loop(chat_id))

    def _stop_typing(self, chat_id: str) -> None:
        if task := self._typing_tasks.pop(chat_id, None): task.cancel()

    async def _typing_loop(self, chat_id: str) -> None:
        try:
            while self._app:
                await self._app.bot.send_chat_action(chat_id=int(chat_id), action="typing")
                await asyncio.sleep(4)
        except asyncio.CancelledError: pass
