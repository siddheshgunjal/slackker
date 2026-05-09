"""Tests for slackker.utils.network — exercises the actual implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from slackker.utils import network


class TestCheckConnection:
    """Test check_connection (the real async implementation)."""

    @pytest.mark.asyncio
    async def test_retries_sleep_is_called_between_attempts(self):
        """asyncio.sleep is called between failed attempts when retries are not exhausted.
        Also covers the verbose retry-warning log (line before the sleep call).
        """
        import httpx as _httpx

        mock_client = AsyncMock()
        mock_client.head = AsyncMock(side_effect=_httpx.RequestError("timeout"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await network.check_connection(
                    "www.slack.com", retries=2, delay=5, verbose=1
                )

        assert result is False
        # Sleep called once: after attempt 1 (attempt 2 exhausts retries and returns)
        mock_sleep.assert_awaited_once_with(5)

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.head = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.check_connection("www.slack.com", retries=1, verbose=0)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_after_max_retries(self):
        import httpx as _httpx

        mock_client = AsyncMock()
        mock_client.head = AsyncMock(side_effect=_httpx.RequestError("timeout"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.check_connection(
                "www.slack.com", retries=2, delay=0, verbose=0
            )

        assert result is False
        assert mock_client.head.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_until_success(self):
        import httpx as _httpx

        mock_response = MagicMock()
        mock_client = AsyncMock()
        mock_client.head = AsyncMock(
            side_effect=[_httpx.RequestError("fail"), mock_response]
        )

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.check_connection(
                "www.slack.com", retries=3, delay=0, verbose=0
            )

        assert result is True
        assert mock_client.head.call_count == 2


class TestVerifySlackToken:
    """Test verify_slack_token (the real async implementation)."""

    @pytest.mark.asyncio
    async def test_returns_true_on_valid_token(self):
        mock_web_client = AsyncMock()
        mock_web_client.api_test = AsyncMock(return_value={"ok": True})

        with patch("slackker.utils.network.AsyncWebClient", return_value=mock_web_client):
            result = await network.verify_slack_token("xoxb-valid", verbose=0)

        assert result is True
        mock_web_client.api_test.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self):
        mock_web_client = AsyncMock()
        mock_web_client.api_test = AsyncMock(side_effect=Exception("invalid_auth"))

        with patch("slackker.utils.network.AsyncWebClient", return_value=mock_web_client):
            result = await network.verify_slack_token("xoxb-bad", verbose=0)

        assert result is False

    @pytest.mark.asyncio
    async def test_does_not_call_close(self):
        """AsyncWebClient has no close() method — verify_slack_token must not call it."""
        mock_web_client = AsyncMock(spec=[])  # no attributes by default
        mock_web_client.api_test = AsyncMock(return_value={"ok": True})

        with patch("slackker.utils.network.AsyncWebClient", return_value=mock_web_client):
            # Would raise AttributeError if close() is called on a spec-less mock
            result = await network.verify_slack_token("xoxb-valid", verbose=0)

        assert result is True
        assert not hasattr(mock_web_client, "close"), (
            "verify_slack_token must not call close() — AsyncWebClient has no such method"
        )


class TestGetTelegramChatId:
    """Test get_telegram_chat_id (the real async implementation)."""

    @pytest.mark.asyncio
    async def test_returns_chat_id_on_success(self):
        mock_response = MagicMock()
        mock_response.json = MagicMock(
            return_value={"result": [{"message": {"chat": {"id": 12345}}}]}
        )
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_telegram_chat_id("123:TOKEN", verbose=0)

        assert result == "12345"

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("network error"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_telegram_chat_id("123:BAD", verbose=0)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_results(self):
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={"result": []})
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_telegram_chat_id("123:TOKEN", verbose=0)

        assert result is None


class TestSyncWrappers:
    """Verify sync wrappers call their async counterparts."""

    def test_check_connection_sync(self):
        with patch("slackker.utils.network.check_connection", new_callable=AsyncMock, return_value=True) as mock_fn:
            result = network.check_connection_sync("www.slack.com", retries=1, verbose=0)
        assert result is True
        mock_fn.assert_awaited_once()

    def test_verify_slack_token_sync(self):
        with patch("slackker.utils.network.verify_slack_token", new_callable=AsyncMock, return_value=True) as mock_fn:
            result = network.verify_slack_token_sync("xoxb-test", verbose=0)
        assert result is True
        mock_fn.assert_awaited_once()

    def test_get_telegram_chat_id_sync(self):
        with patch("slackker.utils.network.get_telegram_chat_id", new_callable=AsyncMock, return_value="999") as mock_fn:
            result = network.get_telegram_chat_id_sync("123:TOKEN", verbose=0)
        assert result == "999"
        mock_fn.assert_awaited_once()

    def test_check_connection_quick_sync(self):
        with patch("slackker.utils.network.check_connection_quick", new_callable=AsyncMock, return_value=True) as mock_fn:
            result = network.check_connection_quick_sync("www.slack.com", max_retries=1, verbose=0)
        assert result is True
        mock_fn.assert_awaited_once()

    def test_get_teams_device_code_sync(self):
        payload = {"device_code": "dc", "user_code": "XY", "message": "go here"}
        with patch("slackker.utils.network.get_teams_device_code", new_callable=AsyncMock, return_value=payload) as mock_fn:
            result = network.get_teams_device_code_sync("app-id", "common", ["Chat.ReadWrite"], verbose=0)
        assert result == payload
        mock_fn.assert_awaited_once()

    def test_poll_teams_device_code_token_sync(self):
        token_data = {"access_token": "tok", "refresh_token": "rt"}
        with patch("slackker.utils.network.poll_teams_device_code_token", new_callable=AsyncMock, return_value=token_data) as mock_fn:
            result = network.poll_teams_device_code_token_sync("app-id", "common", "dev-code", verbose=0)
        assert result == token_data
        mock_fn.assert_awaited_once()

    def test_refresh_teams_access_token_sync(self):
        token_data = {"access_token": "new-tok"}
        with patch("slackker.utils.network.refresh_teams_access_token", new_callable=AsyncMock, return_value=token_data) as mock_fn:
            result = network.refresh_teams_access_token_sync("app-id", "common", "rt", ["Chat.ReadWrite"], verbose=0)
        assert result == token_data
        mock_fn.assert_awaited_once()


# ── verbose logging paths ─────────────────────────────────────────────────────

class TestVerbosePaths:
    """Ensure verbose >= 2 debug branches are executed."""

    @pytest.mark.asyncio
    async def test_check_connection_verbose_success(self):
        mock_response = MagicMock()
        mock_client = AsyncMock()
        mock_client.head = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.check_connection("www.slack.com", retries=1, verbose=2)

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_slack_token_verbose(self):
        mock_web_client = AsyncMock()
        mock_web_client.api_test = AsyncMock(return_value={"ok": True})

        with patch("slackker.utils.network.AsyncWebClient", return_value=mock_web_client):
            result = await network.verify_slack_token("xoxb-valid", verbose=2)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_telegram_chat_id_verbose(self):
        mock_response = MagicMock()
        mock_response.json = MagicMock(
            return_value={"result": [{"message": {"chat": {"id": 99}}}]}
        )
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_telegram_chat_id("123:TOKEN", verbose=2)

        assert result == "99"

    @pytest.mark.asyncio
    async def test_check_connection_verbose_final_failure_warning(self):
        """Final-failure warning branch (verbose >= 1, all retries exhausted)."""
        import httpx as _httpx

        mock_client = AsyncMock()
        mock_client.head = AsyncMock(side_effect=_httpx.RequestError("timeout"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.check_connection(
                    "www.slack.com", retries=2, delay=0, verbose=1
                )

        assert result is False


# ── check_connection_quick ────────────────────────────────────────────────────

class TestCheckConnectionQuick:
    @pytest.mark.asyncio
    async def test_delegates_to_check_connection(self):
        mock_response = MagicMock()
        mock_client = AsyncMock()
        mock_client.head = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.check_connection_quick("www.slack.com", max_retries=1, verbose=0)

        assert result is True


# ── get_teams_device_code ─────────────────────────────────────────────────────

class TestGetTeamsDeviceCode:
    @pytest.mark.asyncio
    async def test_returns_payload_on_success(self):
        payload = {
            "device_code": "dc123",
            "user_code": "ABCD-1234",
            "verification_uri": "https://microsoft.com/devicelogin",
            "message": "Go to …",
            "interval": 5,
            "expires_in": 900,
        }
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=payload)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_teams_device_code("app-id", "common", ["Chat.ReadWrite"], verbose=2)

        assert result == payload

    @pytest.mark.asyncio
    async def test_returns_none_on_http_error(self):
        import httpx as _httpx

        request = _httpx.Request("POST", "https://login.microsoftonline.com")
        response = _httpx.Response(400, request=request, text="Bad Request")
        http_error = _httpx.HTTPStatusError("bad", request=request, response=response)

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=http_error)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_teams_device_code("app-id", "common", ["Chat.ReadWrite"], verbose=0)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_general_exception(self):
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=Exception("network error"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.get_teams_device_code("app-id", "common", ["Chat.ReadWrite"], verbose=0)

        assert result is None


# ── poll_teams_device_code_token ──────────────────────────────────────────────

class TestPollTeamsDeviceCodeToken:
    @pytest.mark.asyncio
    async def test_returns_token_on_success(self):
        token_data = {"access_token": "tok", "refresh_token": "rt", "expires_in": 3600}
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=token_data)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.poll_teams_device_code_token(
                    "app-id", "common", "dev-code", interval=0, verbose=2
                )

        assert result == token_data

    @pytest.mark.asyncio
    async def test_pending_then_success(self):
        """authorization_pending is retried until success."""
        pending = {"error": "authorization_pending"}
        token_data = {"access_token": "tok", "refresh_token": "rt", "expires_in": 3600}

        mock_response = MagicMock()
        mock_response.json = MagicMock(side_effect=[pending, pending, token_data])
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.poll_teams_device_code_token(
                    "app-id", "common", "dev-code", interval=0, verbose=0
                )

        assert result == token_data
        assert mock_http.post.call_count == 3

    @pytest.mark.asyncio
    async def test_slow_down_increases_interval(self):
        """slow_down increases the polling interval, then succeeds."""
        slow = {"error": "slow_down"}
        token_data = {"access_token": "tok", "expires_in": 3600}

        mock_response = MagicMock()
        mock_response.json = MagicMock(side_effect=[slow, token_data])
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.poll_teams_device_code_token(
                    "app-id", "common", "dev-code", interval=0, verbose=0
                )

        assert result == token_data

    @pytest.mark.asyncio
    async def test_returns_none_on_declined(self):
        """authorization_declined returns None."""
        declined = {"error": "authorization_declined", "error_description": "User declined"}
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=declined)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.poll_teams_device_code_token(
                    "app-id", "common", "dev-code", interval=0, verbose=0
                )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_request_exception(self):
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=Exception("network fail"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await network.poll_teams_device_code_token(
                    "app-id", "common", "dev-code", interval=0, verbose=0
                )

        assert result is None


# ── refresh_teams_access_token ────────────────────────────────────────────────

class TestRefreshTeamsAccessToken:
    @pytest.mark.asyncio
    async def test_returns_token_on_success(self):
        token_data = {"access_token": "new-tok", "refresh_token": "rt", "expires_in": 3600}
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=token_data)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.refresh_teams_access_token(
                "app-id", "common", "old-rt", ["Chat.ReadWrite"], verbose=2
            )

        assert result == token_data

    @pytest.mark.asyncio
    async def test_returns_none_on_http_error(self):
        import httpx as _httpx

        request = _httpx.Request("POST", "https://login.microsoftonline.com")
        response = _httpx.Response(400, request=request, text="invalid_grant")
        http_error = _httpx.HTTPStatusError("expired", request=request, response=response)

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=http_error)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.refresh_teams_access_token(
                "app-id", "common", "bad-rt", ["Chat.ReadWrite"], verbose=1
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_access_token_in_response(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"error": "something"})
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.refresh_teams_access_token(
                "app-id", "common", "rt", ["Chat.ReadWrite"], verbose=0
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_general_exception(self):
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=Exception("connection refused"))

        with patch("slackker.utils.network.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await network.refresh_teams_access_token(
                "app-id", "common", "rt", ["Chat.ReadWrite"], verbose=0
            )

        assert result is None
