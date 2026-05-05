"""Tests for slackker.core client abstraction layer."""

import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from slackker.core.client import BaseClient, _run_sync
from slackker.core.slack import SlackClient
from slackker.core.telegram import TelegramClient
from slackker.core.teams import TeamsClient


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


class TestTeamsClient:
    """Test TeamsClient (device code flow)."""

    _INIT = dict(app_id="app-id-1234", tenant_id="common", chat_id="19:abc@thread.v2")

    def test_init_requires_app_id(self):
        with pytest.raises(ValueError, match="app_id"):
            TeamsClient(app_id="", chat_id="19:abc")

    def test_init_requires_chat_id(self):
        with pytest.raises(ValueError, match="chat_id"):
            TeamsClient(app_id="app-id-1234", chat_id="")

    def test_init_stores_attributes(self):
        client = TeamsClient(**self._INIT, verbose=1)
        assert client.platform == "teams"
        assert client.chat_id == "19:abc@thread.v2"
        assert client.verbose == 1
        assert client.connectivity_url == "graph.microsoft.com"
        assert client.is_connected is False  # not yet connected

    def test_init_tenant_defaults_to_common(self):
        client = TeamsClient(app_id="app-id-1234", chat_id="19:abc")
        assert client._tenant_id == "common"

    def test_auth_headers(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "abc123"
        headers = client._auth_headers()
        assert headers["Authorization"] == "Bearer abc123"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_ensure_token_uses_existing_token(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "cached-token"
        client._token_expiry = 9_999_999_999
        client.connect = AsyncMock()

        result = await client._ensure_token()
        assert result is True
        client.connect.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_token_reconnects_when_expired(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "expired-token"
        client._token_expiry = 0
        client.connect = AsyncMock(return_value=True)

        result = await client._ensure_token()
        assert result is True
        client.connect.assert_awaited_once()

    def test_token_cache_roundtrip(self, tmp_path):
        cache_path = tmp_path / "teams_cache.json"
        client = TeamsClient(**self._INIT, token_cache_path=str(cache_path))

        client._save_token_cache({"access_token": "a", "refresh_token": "r", "expires_at": 1})
        assert os.path.isfile(cache_path)

        loaded = client._load_token_cache()
        assert loaded is not None
        assert loaded["refresh_token"] == "r"

    def test_load_token_cache_unreadable_returns_none(self, tmp_path):
        cache_path = tmp_path / "teams_cache.json"
        cache_path.write_text("{bad-json")
        client = TeamsClient(**self._INIT, token_cache_path=str(cache_path))

        loaded = client._load_token_cache()
        assert loaded is None

    def test_apply_token_sets_connection_state_and_persists_cache(self):
        client = TeamsClient(**self._INIT)
        client._save_token_cache = MagicMock()

        client._apply_token({"access_token": "tok", "refresh_token": "rt", "expires_in": 3600})

        assert client._access_token == "tok"
        assert client.is_connected is True
        client._save_token_cache.assert_called_once()

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=False)
    async def test_connect_no_internet(self, mock_check):
        client = TeamsClient(**self._INIT)
        result = await client.connect()
        assert result is False
        assert client.is_connected is False

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock)
    async def test_connect_via_cached_token(self, mock_refresh, mock_check):
        mock_refresh.return_value = {"access_token": "fresh-tok", "refresh_token": "rt", "expires_in": 3600}
        client = TeamsClient(**self._INIT)
        client._load_token_cache = MagicMock(return_value={"refresh_token": "old-rt"})
        client._save_token_cache = MagicMock()

        result = await client.connect()
        assert result is True
        assert client.is_connected is True
        mock_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock, return_value=None)
    @patch("slackker.core.teams.network.get_teams_device_code", new_callable=AsyncMock)
    @patch("slackker.core.teams.network.poll_teams_device_code_token", new_callable=AsyncMock)
    async def test_connect_via_device_code(self, mock_poll, mock_device, mock_refresh, mock_check):
        mock_device.return_value = {
            "device_code": "dev-code",
            "user_code": "ABCD1234",
            "verification_uri": "https://microsoft.com/devicelogin",
            "message": "Go to https://microsoft.com/devicelogin and enter ABCD1234",
            "interval": 5,
            "expires_in": 900,
        }
        mock_poll.return_value = {"access_token": "new-tok", "refresh_token": "rt", "expires_in": 3600}
        client = TeamsClient(**self._INIT)
        client._load_token_cache = MagicMock(return_value=None)
        client._save_token_cache = MagicMock()

        result = await client.connect()
        assert result is True
        assert client.is_connected is True
        mock_device.assert_awaited_once()
        mock_poll.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock, return_value=None)
    @patch("slackker.core.teams.network.get_teams_device_code", new_callable=AsyncMock, return_value=None)
    async def test_connect_device_code_failed(self, mock_device, mock_refresh, mock_check):
        client = TeamsClient(**self._INIT)
        client._load_token_cache = MagicMock(return_value=None)
        result = await client.connect()
        assert result is False
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_send_message(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "fake-token"
        client._token_expiry = 9_999_999_999

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hello Teams")
            mock_http.post.assert_awaited_once()
            assert "chats/19:abc@thread.v2/messages" in mock_http.post.call_args.args[0]

    @pytest.mark.asyncio
    async def test_send_message_when_not_connected(self):
        client = TeamsClient(**self._INIT)
        client._ensure_token = AsyncMock(return_value=False)

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            await client.send_message("Hello Teams")
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_invalid_path(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "fake-token"
        client._token_expiry = 9_999_999_999

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file("/nonexistent/file.txt")
            mock_http.put.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_upload_file_when_not_connected(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("hello")

        client = TeamsClient(**self._INIT)
        client._ensure_token = AsyncMock(return_value=False)

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            await client.upload_file(str(file_path))
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_success_posts_link(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("hello")

        client = TeamsClient(**self._INIT)
        client._access_token = "fake-token"
        client._token_expiry = 9_999_999_999
        client.send_message = AsyncMock()

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value={"webUrl": "https://example.com/file"})

            mock_http = AsyncMock()
            mock_http.put = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path), comment="See file")

            mock_http.put.assert_awaited_once()
            client.send_message.assert_awaited_once_with("See file\nhttps://example.com/file")

    @pytest.mark.asyncio
    async def test_upload_file_http_error(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("hello")

        client = TeamsClient(**self._INIT)
        client._access_token = "fake-token"
        client._token_expiry = 9_999_999_999
        client.send_message = AsyncMock()

        request = httpx.Request("PUT", "https://graph.microsoft.com")
        response = httpx.Response(500, request=request, text="oops")
        http_error = httpx.HTTPStatusError("failed", request=request, response=response)

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=http_error)
            mock_http = AsyncMock()
            mock_http.put = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path))
            client.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_upload_image_delegates_to_upload_file(self):
        client = TeamsClient(**self._INIT)
        client.upload_file = AsyncMock()

        await client.upload_image("image.png", comment="plot")
        client.upload_file.assert_awaited_once_with("image.png", "plot")

    def test_send_message_sync(self):
        client = TeamsClient(**self._INIT)
        client.send_message = AsyncMock()
        client.send_message_sync("Hello sync")
        client.send_message.assert_awaited_once_with("Hello sync")
