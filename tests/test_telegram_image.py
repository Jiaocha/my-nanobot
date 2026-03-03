"""Tests for Telegram channel image handling."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.channels.telegram import TelegramChannel


class TestTelegramImageHandling:
    """Test Telegram image download and processing."""

    @pytest.fixture
    def mock_config(self):
        """Create mock Telegram config."""
        config = MagicMock()
        config.token = "test_token"
        config.allow_from = ["test_user"]
        return config

    @pytest.fixture
    def mock_bus(self):
        """Create mock message bus."""
        bus = MagicMock()
        bus.publish_inbound = AsyncMock()
        return bus

    @pytest.fixture
    def channel(self, mock_config, mock_bus):
        """Create TelegramChannel instance."""
        return TelegramChannel(mock_config, mock_bus)

    @pytest.mark.asyncio
    async def test_photo_download(self, channel):
        """Test photo download from Telegram."""
        # Mock update with photo
        mock_photo = MagicMock()
        mock_photo.file_id = "test_photo_id"
        mock_photo[-1].file_id = "test_photo_id"  # Largest size

        mock_message = MagicMock()
        mock_message.photo = [mock_photo]
        mock_message.text = None
        mock_message.caption = None
        mock_message.document = None
        mock_message.effective_user.id = "123"
        mock_message.effective_user.username = "test_user"
        mock_message.chat_id = "456"
        mock_message.message_id = "789"

        mock_update = MagicMock()
        mock_update.message = mock_message

        mock_context = MagicMock()
        mock_file = AsyncMock()
        mock_file.download_to_drive = AsyncMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock _handle_message to capture arguments
        captured_args = {}

        async def mock_handle_message(**kwargs):
            captured_args.update(kwargs)

        channel._handle_message = mock_handle_message

        # Call _on_message
        await channel._on_message(mock_update, mock_context)

        # Verify photo was downloaded
        assert mock_context.bot.get_file.called
        assert mock_file.download_to_drive.called

        # Verify media paths were passed
        assert "media" in captured_args
        assert captured_args["media"] is not None
        assert len(captured_args["media"]) > 0

    @pytest.mark.asyncio
    async def test_document_download(self, channel):
        """Test document download from Telegram."""
        # Mock update with document
        mock_doc = MagicMock()
        mock_doc.file_id = "test_doc_id"
        mock_doc.file_name = "test.pdf"

        mock_message = MagicMock()
        mock_message.photo = None
        mock_message.document = mock_doc
        mock_message.text = None
        mock_message.caption = None
        mock_message.effective_user.id = "123"
        mock_message.effective_user.username = "test_user"
        mock_message.chat_id = "456"
        mock_message.message_id = "789"

        mock_update = MagicMock()
        mock_update.message = mock_message

        mock_context = MagicMock()
        mock_file = AsyncMock()
        mock_file.download_to_drive = AsyncMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock _handle_message
        captured_args = {}

        async def mock_handle_message(**kwargs):
            captured_args.update(kwargs)

        channel._handle_message = mock_handle_message

        # Call _on_message
        await channel._on_message(mock_update, mock_context)

        # Verify document was downloaded
        assert mock_context.bot.get_file.called
        assert mock_file.download_to_drive.called

        # Verify media paths were passed
        assert "media" in captured_args
        assert captured_args["media"] is not None

    @pytest.mark.asyncio
    async def test_photo_with_caption(self, channel):
        """Test photo with caption."""
        # Mock update with photo and caption
        mock_photo = MagicMock()
        mock_photo.file_id = "test_photo_id"
        mock_photo[-1].file_id = "test_photo_id"

        mock_message = MagicMock()
        mock_message.photo = [mock_photo]
        mock_message.text = None
        mock_message.caption = "请描述这张图片"
        mock_message.document = None
        mock_message.effective_user.id = "123"
        mock_message.effective_user.username = "test_user"
        mock_message.chat_id = "456"
        mock_message.message_id = "789"

        mock_update = MagicMock()
        mock_update.message = mock_message

        mock_context = MagicMock()
        mock_file = AsyncMock()
        mock_file.download_to_drive = AsyncMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock _handle_message
        captured_content = ""

        async def mock_handle_message(content, **kwargs):
            nonlocal captured_content
            captured_content = content

        channel._handle_message = mock_handle_message

        # Call _on_message
        await channel._on_message(mock_update, mock_context)

        # Verify caption was used as content
        assert captured_content == "请描述这张图片"

    @pytest.mark.asyncio
    async def test_photo_only_no_caption(self, channel):
        """Test photo without caption generates default prompt."""
        # Mock update with photo but no caption
        mock_photo = MagicMock()
        mock_photo.file_id = "test_photo_id"
        mock_photo[-1].file_id = "test_photo_id"

        mock_message = MagicMock()
        mock_message.photo = [mock_photo]
        mock_message.text = None
        mock_message.caption = None
        mock_message.document = None
        mock_message.effective_user.id = "123"
        mock_message.effective_user.username = "test_user"
        mock_message.chat_id = "456"
        mock_message.message_id = "789"

        mock_update = MagicMock()
        mock_update.message = mock_message

        mock_context = MagicMock()
        mock_file = AsyncMock()
        mock_file.download_to_drive = AsyncMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock _handle_message
        captured_content = ""

        async def mock_handle_message(content, **kwargs):
            nonlocal captured_content
            captured_content = content

        channel._handle_message = mock_handle_message

        # Call _on_message
        await channel._on_message(mock_update, mock_context)

        # Verify default prompt was generated
        assert captured_content == "请描述这张图片"

    @pytest.mark.asyncio
    async def test_download_failure_handling(self, channel):
        """Test graceful handling of download failures."""
        # Mock update with photo
        mock_photo = MagicMock()
        mock_photo.file_id = "test_photo_id"
        mock_photo[-1].file_id = "test_photo_id"

        mock_message = MagicMock()
        mock_message.photo = [mock_photo]
        mock_message.text = "测试消息"
        mock_message.caption = None
        mock_message.document = None
        mock_message.effective_user.id = "123"
        mock_message.effective_user.username = "test_user"
        mock_message.chat_id = "456"
        mock_message.message_id = "789"

        mock_update = MagicMock()
        mock_update.message = mock_message

        mock_context = MagicMock()
        # Simulate download failure
        mock_context.bot.get_file = AsyncMock(side_effect=Exception("Download failed"))

        # Mock _handle_message
        called = False

        async def mock_handle_message(**kwargs):
            nonlocal called
            called = True

        channel._handle_message = mock_handle_message

        # Call _on_message - should not raise
        await channel._on_message(mock_update, mock_context)

        # Verify message was still processed
        assert called
