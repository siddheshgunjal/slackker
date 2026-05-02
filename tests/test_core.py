"""Tests for slackker.core client abstraction layer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from slackker.core.client import BaseClient, _run_sync
from slackker.core.slack import SlackClient
from slackker.core.telegram import TelegramClient


class TestBaseClient:
    """Test the ABC contract."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseClient(verbose=0)

    def test_subclass_must_implement_abstract_methods(self):
        class Incomplete(BaseClient):
            @property
            def platform(self):
                return "test"

        with pytest.raises(TypeError):
            Incomplete(verbose=0)


class TestSlackClient:
    """Test SlackClient."""

    def test_init_requires_token(self):
        with pytest.raises(ValueError, match="Slack API token is required"):
            SlackClient(token="", channel="C123")

    def test_init_stores_attributes(self):
        client = SlackClient(token="xoxb-test", channel="C123", verbose=2)
        assert client.platform == "slack"
        assert client.channel == "C123"
        assert client.verbose == 2

    @pytest.mark.asyncio
    @patch("slackker.core.slack.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.slack.network.verify_slack_token", new_callable=AsyncMock, return_value=True)
    async def test_connect_success(self, mock_verify, mock_check):
        client = SlackClient(token="xoxb-test", channel="C123")
        result = await client.connect()
        assert result is True
        mock_check.assert_awaited_once()
        mock_verify.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("slackker.core.slack.network.check_connection", new_callable=AsyncMock, return_value=False)
    @patch("slackker.core.slack.network.verify_slack_token", new_callable=AsyncMock, return_value=True)
    async def test_connect_no_internet(self, mock_verify, mock_check):
        client = SlackClient(token="xoxb-test", channel="C123")
        result = await client.connect()
        assert result is False

    @pytest.mark.asyncio
    @patch("slackker.core.slack.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.slack.network.verify_slack_token", new_callable=AsyncMock, return_value=False)
    async def test_connect_invalid_token(self, mock_verify, mock_check):
        client = SlackClient(token="xoxb-bad", channel="C123")
        result = await client.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message(self):
        client = SlackClient(token="xoxb-test", channel="C123", verbose=0)
        client._client = AsyncMock()
        client._client.chat_postMessage = AsyncMock()

        await client.send_message("Hello")
        client._client.chat_postMessage.assert_awaited_once_with(channel="C123", text="Hello")

    @pytest.mark.asyncio
    async def test_upload_file_invalid_path(self):
        client = SlackClient(token="xoxb-test", channel="C123", verbose=0)
        client._client = AsyncMock()
        # Should not raise, just log an error
        await client.upload_file("/nonexistent/file.txt")
        client._client.files_upload_v2.assert_not_awaited()

    def test_send_message_sync(self):
        client = SlackClient(token="xoxb-test", channel="C123", verbose=0)
        client._client = MagicMock()
        # Mock the async method to return a coroutine
        client.send_message = AsyncMock()
        client.send_message_sync("Hello sync")
        client.send_message.assert_awaited_once_with("Hello sync")


class TestTelegramClient:
    """Test TelegramClient."""

    def test_init_requires_token(self):
        with pytest.raises(ValueError, match="Telegram API token is required"):
            TelegramClient(token="", verbose=0)

    def test_init_stores_attributes(self):
        client = TelegramClient(token="123:ABC", verbose=1)
        assert client.platform == "telegram"
        assert client.verbose == 1
        assert client.chat_id is None

    def test_init_with_chat_id(self):
        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=0)
        assert client.chat_id == "99999"

    @pytest.mark.asyncio
    @patch("slackker.core.telegram.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.telegram.network.get_telegram_chat_id", new_callable=AsyncMock, return_value="12345")
    async def test_connect_discovers_chat_id(self, mock_get_id, mock_check):
        client = TelegramClient(token="123:ABC", verbose=0)
        result = await client.connect()
        assert result is True
        assert client.chat_id == "12345"

    @pytest.mark.asyncio
    @patch("slackker.core.telegram.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.telegram.network.get_telegram_chat_id", new_callable=AsyncMock, return_value=None)
    async def test_connect_no_chat_id(self, mock_get_id, mock_check):
        client = TelegramClient(token="123:ABC", verbose=0)
        result = await client.connect()
        assert result is False

    @pytest.mark.asyncio
    @patch("slackker.core.telegram.network.check_connection", new_callable=AsyncMock, return_value=False)
    async def test_connect_no_internet(self, mock_check):
        client = TelegramClient(token="123:ABC", verbose=0)
        result = await client.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message(self):
        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=0)
        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Test message")
            mock_http.post.assert_awaited_once()

    def test_send_message_sync(self):
        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=0)
        client.send_message = AsyncMock()
        client.send_message_sync("Hello sync")
        client.send_message.assert_awaited_once_with("Hello sync")


class TestRunSync:
    """Test the _run_sync helper."""

    def test_run_sync_basic(self):
        async def async_add(a, b):
            return a + b

        result = _run_sync(async_add(2, 3))
        assert result == 5
