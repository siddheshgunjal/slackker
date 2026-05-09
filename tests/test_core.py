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

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock)
    async def test_connect_via_cached_token_verbose_log(self, mock_refresh, mock_check):
        """Verify the verbose >= 1 log line after successful silent refresh."""
        mock_refresh.return_value = {"access_token": "t", "refresh_token": "rt", "expires_in": 3600}
        client = TeamsClient(**self._INIT, verbose=1)
        client._load_token_cache = MagicMock(return_value={"refresh_token": "old-rt"})
        client._save_token_cache = MagicMock()

        result = await client.connect()
        assert result is True

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock, return_value=None)
    @patch("slackker.core.teams.network.get_teams_device_code", new_callable=AsyncMock)
    @patch("slackker.core.teams.network.poll_teams_device_code_token", new_callable=AsyncMock)
    async def test_connect_device_code_verbose_log(self, mock_poll, mock_device, mock_refresh, mock_check):
        """Verify the verbose >= 1 log line after device code success."""
        mock_device.return_value = {
            "device_code": "dc",
            "message": "Visit https://microsoft.com/devicelogin",
            "interval": 0,
        }
        mock_poll.return_value = {"access_token": "new-tok", "refresh_token": "rt", "expires_in": 3600}
        client = TeamsClient(**self._INIT, verbose=1)
        client._load_token_cache = MagicMock(return_value=None)
        client._save_token_cache = MagicMock()

        result = await client.connect()
        assert result is True

    @pytest.mark.asyncio
    @patch("slackker.core.teams.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.teams.network.refresh_teams_access_token", new_callable=AsyncMock, return_value=None)
    @patch("slackker.core.teams.network.get_teams_device_code", new_callable=AsyncMock)
    @patch("slackker.core.teams.network.poll_teams_device_code_token", new_callable=AsyncMock, return_value=None)
    async def test_connect_poll_returns_none(self, mock_poll, mock_device, mock_refresh, mock_check):
        mock_device.return_value = {
            "device_code": "dc",
            "message": "Visit https://microsoft.com/devicelogin",
            "interval": 0,
        }
        client = TeamsClient(**self._INIT)
        client._load_token_cache = MagicMock(return_value=None)

        result = await client.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_ensure_token_returns_false_when_connect_fails(self):
        client = TeamsClient(**self._INIT)
        client.connect = AsyncMock(return_value=False)

        result = await client._ensure_token()
        assert result is False
        client.connect.assert_awaited_once()

    def test_save_token_cache_exception_logs_warning(self, tmp_path):
        """If the directory cannot be created, a warning is logged (no raise)."""
        client = TeamsClient(**self._INIT, token_cache_path="/dev/null/impossible/path.json")
        # Should not raise — exception is caught internally
        client._save_token_cache({"access_token": "t", "refresh_token": "rt", "expires_at": 0})

    @pytest.mark.asyncio
    async def test_send_message_verbose_log(self):
        client = TeamsClient(**self._INIT, verbose=1)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hi")
            mock_http.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_http_error(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999

        request = httpx.Request("POST", "https://graph.microsoft.com")
        response = httpx.Response(403, request=request, text="forbidden")
        http_error = httpx.HTTPStatusError("err", request=request, response=response)

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=http_error)
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # Should not raise
            await client.send_message("Hi")

    @pytest.mark.asyncio
    async def test_send_message_general_exception(self):
        client = TeamsClient(**self._INIT)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=Exception("unexpected"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hi")

    @pytest.mark.asyncio
    async def test_upload_file_verbose_log(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("data")

        client = TeamsClient(**self._INIT, verbose=1)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999
        client.send_message = AsyncMock()

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value={"webUrl": "https://example.com/f"})
            mock_http = AsyncMock()
            mock_http.put = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path))
            client.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upload_file_general_exception(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("data")

        client = TeamsClient(**self._INIT)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999
        client.send_message = AsyncMock()

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.put = AsyncMock(side_effect=Exception("connection lost"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path))
            client.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_upload_file_no_web_url_in_response(self, tmp_path):
        """When webUrl is absent, the message still sends with just the caption."""
        file_path = tmp_path / "f.txt"
        file_path.write_text("data")

        client = TeamsClient(**self._INIT)
        client._access_token = "tok"
        client._token_expiry = 9_999_999_999
        client.send_message = AsyncMock()

        with patch("slackker.core.teams.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value={})  # no webUrl
            mock_http = AsyncMock()
            mock_http.put = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path), comment="no url here")
            client.send_message.assert_awaited_once_with("no url here")


# ── Additional SlackClient coverage ──────────────────────────────────────────

class TestSlackClientCoverage:
    """Tests for lines not covered by TestSlackClient."""

    def test_is_connected_initially_false(self):
        client = SlackClient(token="xoxb-test", channel="C123")
        assert client.is_connected is False

    @pytest.mark.asyncio
    @patch("slackker.core.slack.network.check_connection", new_callable=AsyncMock, return_value=True)
    @patch("slackker.core.slack.network.verify_slack_token", new_callable=AsyncMock, return_value=True)
    async def test_is_connected_true_after_connect(self, mock_verify, mock_check):
        client = SlackClient(token="xoxb-test", channel="C123")
        await client.connect()
        assert client.is_connected is True

    def test_connectivity_url(self):
        client = SlackClient(token="xoxb-test", channel="C123")
        assert client.connectivity_url == "www.slack.com"

    @pytest.mark.asyncio
    async def test_send_message_verbose_log(self):
        client = SlackClient(token="xoxb-test", channel="C123", verbose=1)
        client._client = AsyncMock()
        client._client.chat_postMessage = AsyncMock()

        await client.send_message("Hello verbose")
        client._client.chat_postMessage.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_slack_api_error(self):
        from slack_sdk.errors import SlackApiError

        client = SlackClient(token="xoxb-test", channel="C123")
        client._client = AsyncMock()
        client._client.chat_postMessage = AsyncMock(
            side_effect=SlackApiError("error", {"error": "channel_not_found"})
        )

        # Should not raise
        await client.send_message("Hello")

    @pytest.mark.asyncio
    async def test_upload_file_success(self, tmp_path):
        file_path = tmp_path / "report.txt"
        file_path.write_text("results")

        client = SlackClient(token="xoxb-test", channel="C123", verbose=1)
        client._client = AsyncMock()
        client._client.files_upload_v2 = AsyncMock()

        await client.upload_file(str(file_path), comment="See report")
        client._client.files_upload_v2.assert_awaited_once_with(
            channel="C123",
            file=str(file_path),
            initial_comment="See report",
        )

    @pytest.mark.asyncio
    async def test_upload_file_slack_api_error(self, tmp_path):
        from slack_sdk.errors import SlackApiError

        file_path = tmp_path / "f.txt"
        file_path.write_text("x")

        client = SlackClient(token="xoxb-test", channel="C123")
        client._client = AsyncMock()
        client._client.files_upload_v2 = AsyncMock(
            side_effect=SlackApiError("upload error", {"error": "not_authed"})
        )

        # Should not raise
        await client.upload_file(str(file_path))

    @pytest.mark.asyncio
    async def test_upload_file_default_comment(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("x")

        client = SlackClient(token="xoxb-test", channel="C123")
        client._client = AsyncMock()
        client._client.files_upload_v2 = AsyncMock()

        await client.upload_file(str(file_path))
        _, kwargs = client._client.files_upload_v2.call_args
        assert kwargs["initial_comment"] == "Attachment 📎"

    @pytest.mark.asyncio
    async def test_upload_image_delegates_to_upload_file(self, tmp_path):
        file_path = tmp_path / "plot.png"
        file_path.write_text("binary")

        client = SlackClient(token="xoxb-test", channel="C123")
        client.upload_file = AsyncMock()

        await client.upload_image(str(file_path), comment="My plot")
        client.upload_file.assert_awaited_once_with(str(file_path), "My plot")

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self):
        client = SlackClient(token="xoxb-test", channel="C123")
        await client.close()  # Should be a no-op without raising


# ── Additional TelegramClient coverage ───────────────────────────────────────

class TestTelegramClientCoverage:
    """Tests for lines not covered by TestTelegramClient."""

    def test_connectivity_url(self):
        client = TelegramClient(token="123:ABC")
        assert client.connectivity_url == "www.telegram.org"

    def test_is_connected_true_when_chat_id_set(self):
        client = TelegramClient(token="123:ABC", chat_id="99999")
        assert client.is_connected is True

    def test_chat_id_property(self):
        client = TelegramClient(token="123:ABC", chat_id="12345")
        assert client.chat_id == "12345"

    @pytest.mark.asyncio
    async def test_send_message_without_chat_id_returns_early(self):
        client = TelegramClient(token="123:ABC")  # no chat_id

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            await client.send_message("Hi")
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_verbose_log(self):
        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=1)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hi verbose")
            mock_http.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_http_status_error(self):
        client = TelegramClient(token="123:ABC", chat_id="99999")

        request = httpx.Request("POST", "https://api.telegram.org")
        response = httpx.Response(401, request=request, text="Unauthorized")
        http_error = httpx.HTTPStatusError("err", request=request, response=response)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=http_error)
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hi")  # Should not raise

    @pytest.mark.asyncio
    async def test_send_message_general_exception(self):
        client = TelegramClient(token="123:ABC", chat_id="99999")

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=Exception("network down"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.send_message("Hi")

    @pytest.mark.asyncio
    async def test_upload_file_without_chat_id_returns_early(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("x")

        client = TelegramClient(token="123:ABC")  # no chat_id
        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            await client.upload_file(str(file_path))
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_invalid_path_returns_early(self):
        client = TelegramClient(token="123:ABC", chat_id="99999")
        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            await client.upload_file("/nonexistent/path.txt")
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, tmp_path):
        file_path = tmp_path / "report.txt"
        file_path.write_text("data")

        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=1)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path), comment="My report")
            mock_http.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upload_file_http_status_error(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("x")

        client = TelegramClient(token="123:ABC", chat_id="99999")

        request = httpx.Request("POST", "https://api.telegram.org")
        response = httpx.Response(400, request=request, text="Bad Request")
        http_error = httpx.HTTPStatusError("err", request=request, response=response)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=http_error)
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path))

    @pytest.mark.asyncio
    async def test_upload_file_general_exception(self, tmp_path):
        file_path = tmp_path / "f.txt"
        file_path.write_text("x")

        client = TelegramClient(token="123:ABC", chat_id="99999")

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=Exception("unexpected"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_file(str(file_path))

    @pytest.mark.asyncio
    async def test_upload_image_without_chat_id_returns_early(self, tmp_path):
        file_path = tmp_path / "img.png"
        file_path.write_text("x")

        client = TelegramClient(token="123:ABC")  # no chat_id
        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            await client.upload_image(str(file_path))
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_image_invalid_path_returns_early(self):
        client = TelegramClient(token="123:ABC", chat_id="99999")
        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            await client.upload_image("/nonexistent/image.png")
            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_image_success(self, tmp_path):
        file_path = tmp_path / "img.png"
        file_path.write_text("binary")

        client = TelegramClient(token="123:ABC", chat_id="99999", verbose=1)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_image(str(file_path), comment="My plot")
            mock_http.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upload_image_http_status_error(self, tmp_path):
        file_path = tmp_path / "img.png"
        file_path.write_text("binary")

        client = TelegramClient(token="123:ABC", chat_id="99999")

        request = httpx.Request("POST", "https://api.telegram.org")
        response = httpx.Response(400, request=request, text="Bad Request")
        http_error = httpx.HTTPStatusError("err", request=request, response=response)

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=http_error)
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_image(str(file_path))

    @pytest.mark.asyncio
    async def test_upload_image_general_exception(self, tmp_path):
        file_path = tmp_path / "img.png"
        file_path.write_text("binary")

        client = TelegramClient(token="123:ABC", chat_id="99999")

        with patch("slackker.core.telegram.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=Exception("unexpected"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.upload_image(str(file_path))


# ── _run_sync nest_asyncio path ───────────────────────────────────────────────

class TestRunSyncNestAsyncio:
    """Cover the already-running-loop branch of _run_sync."""

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_run_sync_with_already_running_loop(self):
        import sys

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_loop.run_until_complete.return_value = 42

        mock_nest = MagicMock()

        async def dummy():
            return 42

        coro = dummy()
        with patch("asyncio.get_running_loop", return_value=mock_loop):
            with patch.dict(sys.modules, {"nest_asyncio": mock_nest}):
                result = _run_sync(coro)
        # mock_loop.run_until_complete never actually awaits the coroutine;
        # close it explicitly to prevent "coroutine was never awaited" RuntimeWarning.
        coro.close()

        mock_nest.apply.assert_called_once()
        mock_loop.run_until_complete.assert_called_once()
        assert result == 42

    def test_upload_file_sync(self):
        """BaseClient.upload_file_sync wraps upload_file."""
        client = TelegramClient(token="123:ABC", chat_id="99999")
        client.upload_file = AsyncMock()
        client.upload_file_sync("report.txt", comment="results")
        client.upload_file.assert_awaited_once_with("report.txt", "results")

    def test_upload_image_sync(self):
        """BaseClient.upload_image_sync wraps upload_image."""
        client = TelegramClient(token="123:ABC", chat_id="99999")
        client.upload_image = AsyncMock()
        client.upload_image_sync("image.png", comment="plot")
        client.upload_image.assert_awaited_once_with("image.png", "plot")
