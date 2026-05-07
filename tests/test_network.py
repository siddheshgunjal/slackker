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
