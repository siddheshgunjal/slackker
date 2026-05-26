"""Tests for slackker.core.models, platform fetch_messages, and slackker.listener."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from slackker.core.client import BaseClient
from slackker.core.models import IncomingMessage
from slackker.listener import CommandHandler, MessagePoller

# ── Shared helpers ────────────────────────────────────────────────────────────


def _msg(
    text="hello",
    sender="alice",
    sender_id="U001",
    timestamp="1000",
    platform="mock",
    is_bot=False,
    thread_id=None,
    raw=None,
) -> IncomingMessage:
    return IncomingMessage(
        text=text,
        sender=sender,
        sender_id=sender_id,
        timestamp=timestamp,
        platform=platform,
        is_bot=is_bot,
        thread_id=thread_id,
        raw=raw or {},
    )


class MockClient(BaseClient):
    """Minimal concrete client used across listener tests."""

    def __init__(self, messages: list[IncomingMessage] | None = None):
        super().__init__(verbose=0)
        self._messages: list[IncomingMessage] = messages or []
        self.fetch_calls: list[dict] = []

    @property
    def platform(self) -> str:
        return "mock"

    @property
    def connectivity_url(self) -> str:
        return "mock.example.com"

    @property
    def is_connected(self) -> bool:
        return True

    async def send_message(self, text: str) -> None:
        pass

    async def upload_file(self, filepath, comment=None) -> None:
        pass

    async def upload_image(self, filepath, comment=None) -> None:
        pass

    async def fetch_messages(self, limit=10, since=None, thread_id=None):
        self.fetch_calls.append(
            {"limit": limit, "since": since, "thread_id": thread_id}
        )
        return list(self._messages)


# ── IncomingMessage ───────────────────────────────────────────────────────────


class TestIncomingMessage:
    def test_basic_construction(self):
        msg = _msg()
        assert msg.text == "hello"
        assert msg.sender == "alice"
        assert msg.sender_id == "U001"
        assert msg.timestamp == "1000"
        assert msg.platform == "mock"
        assert msg.is_bot is False
        assert msg.thread_id is None
        assert msg.raw == {}

    def test_thread_id_stored(self):
        msg = _msg(thread_id="thread-123")
        assert msg.thread_id == "thread-123"

    def test_raw_field(self):
        raw = {"key": "value", "nested": {"a": 1}}
        msg = _msg(raw=raw)
        assert msg.raw == raw

    def test_repr_short(self):
        msg = _msg(text="hi")
        r = repr(msg)
        assert "IncomingMessage(" in r
        assert "mock" in r
        assert "alice" in r

    def test_repr_truncates_long_text(self):
        msg = _msg(text="x" * 100)
        r = repr(msg)
        assert "…" in r
        assert len(r) < 200

    def test_default_raw_is_empty_dict(self):
        msg = IncomingMessage(
            text="t",
            sender="s",
            sender_id="id",
            timestamp="0",
            platform="p",
            is_bot=False,
        )
        assert msg.raw == {}
        assert isinstance(msg.raw, dict)


# ── BaseClient.cursor_from_message default ────────────────────────────────────


class TestBaseCursorDefault:
    def test_default_returns_timestamp(self):
        client = MockClient()
        msg = _msg(timestamp="99999")
        assert client.cursor_from_message(msg) == "99999"


# ── Slack fetch_messages ──────────────────────────────────────────────────────


class TestSlackFetchMessages:
    @pytest.mark.asyncio
    async def test_channel_history_oldest_first(self):
        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        client._client.conversations_history = AsyncMock(
            return_value={
                "messages": [
                    {"ts": "2000", "text": "newer", "user": "U2"},
                    {"ts": "1000", "text": "older", "user": "U1"},
                ]
            }
        )

        msgs = await client.fetch_messages(limit=10)

        assert len(msgs) == 2
        assert msgs[0].text == "older"  # oldest first
        assert msgs[1].text == "newer"
        assert msgs[0].platform == "slack"
        assert msgs[0].timestamp == "1000"

    @pytest.mark.asyncio
    async def test_since_passed_as_oldest(self):
        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        client._client.conversations_history = AsyncMock(return_value={"messages": []})

        await client.fetch_messages(limit=5, since="1234567890.000100")

        client._client.conversations_history.assert_called_once_with(
            channel="C123", oldest="1234567890.000100", limit=5
        )

    @pytest.mark.asyncio
    async def test_thread_replies_skips_parent(self):
        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        # Slack always includes the parent message as the first element
        client._client.conversations_replies = AsyncMock(
            return_value={
                "messages": [
                    {"ts": "1000", "text": "parent", "user": "U1"},  # skipped
                    {"ts": "1001", "text": "reply1", "user": "U2", "thread_ts": "1000"},
                    {"ts": "1002", "text": "reply2", "user": "U3", "thread_ts": "1000"},
                ]
            }
        )

        msgs = await client.fetch_messages(limit=10, thread_id="1000")

        assert len(msgs) == 2
        assert msgs[0].text == "reply1"
        assert msgs[1].text == "reply2"
        assert msgs[0].thread_id == "1000"

    @pytest.mark.asyncio
    async def test_bot_message_flagged(self):
        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        client._client.conversations_history = AsyncMock(
            return_value={
                "messages": [{"ts": "1000", "text": "bot msg", "bot_id": "B123"}]
            }
        )

        msgs = await client.fetch_messages()
        assert msgs[0].is_bot is True
        assert msgs[0].sender == "B123"

    @pytest.mark.asyncio
    async def test_api_error_returns_empty_list(self):
        from slack_sdk.errors import SlackApiError

        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        client._client.conversations_history = AsyncMock(
            side_effect=SlackApiError("fail", {"error": "not_authed"})
        )

        assert await client.fetch_messages() == []

    def test_cursor_from_message(self):
        from slackker.core.slack import SlackClient

        client = SlackClient(token="xoxb-test", channel_id="C123")
        msg = _msg(timestamp="1699000000.000100", platform="slack")
        assert client.cursor_from_message(msg) == "1699000000.000100"


# ── Telegram fetch_messages ───────────────────────────────────────────────────


def _telegram_mock_ctx(updates_payload: dict):
    """Return a patched _make_async_client context that returns the given payload."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = updates_payload

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx, mock_http


class TestTelegramFetchMessages:
    @pytest.mark.asyncio
    async def test_fetch_basic_message(self):
        from slackker.core.telegram import TelegramClient

        client = TelegramClient(token="123:ABC", chat_id="99")
        payload = {
            "result": [
                {
                    "update_id": 500,
                    "message": {
                        "message_id": 10,
                        "chat": {"id": 99},
                        "from": {"id": 1, "first_name": "Alice", "is_bot": False},
                        "text": "hello",
                    },
                }
            ]
        }
        mock_ctx, _ = _telegram_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(limit=10)

        assert len(msgs) == 1
        assert msgs[0].text == "hello"
        assert msgs[0].sender == "Alice"
        assert msgs[0].platform == "telegram"
        assert msgs[0].timestamp == "500"
        assert msgs[0].is_bot is False

    @pytest.mark.asyncio
    async def test_since_passed_as_offset(self):
        from slackker.core.telegram import TelegramClient

        client = TelegramClient(token="123:ABC", chat_id="99")
        payload = {"result": []}
        mock_ctx, mock_http = _telegram_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            await client.fetch_messages(limit=5, since="501")

        call_kwargs = mock_http.get.call_args
        assert call_kwargs[1]["params"]["offset"] == 501

    @pytest.mark.asyncio
    async def test_filters_by_chat_id(self):
        from slackker.core.telegram import TelegramClient

        client = TelegramClient(token="123:ABC", chat_id="99")
        payload = {
            "result": [
                {
                    "update_id": 1,
                    "message": {
                        "message_id": 1,
                        "chat": {"id": 99},
                        "from": {"id": 1, "first_name": "Alice", "is_bot": False},
                        "text": "for me",
                    },
                },
                {
                    "update_id": 2,
                    "message": {
                        "message_id": 2,
                        "chat": {"id": 77},  # different chat
                        "from": {"id": 2, "first_name": "Bob", "is_bot": False},
                        "text": "not for me",
                    },
                },
            ]
        }
        mock_ctx, _ = _telegram_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages()

        assert len(msgs) == 1
        assert msgs[0].text == "for me"

    @pytest.mark.asyncio
    async def test_thread_filter_by_reply_to(self):
        from slackker.core.telegram import TelegramClient

        client = TelegramClient(token="123:ABC", chat_id="99")
        payload = {
            "result": [
                {
                    "update_id": 10,
                    "message": {
                        "message_id": 11,
                        "chat": {"id": 99},
                        "from": {"id": 2, "first_name": "Bob", "is_bot": False},
                        "text": "reply to 10",
                        "reply_to_message": {"message_id": 10},
                    },
                },
                {
                    "update_id": 11,
                    "message": {
                        "message_id": 12,
                        "chat": {"id": 99},
                        "from": {"id": 3, "first_name": "Eve", "is_bot": False},
                        "text": "unrelated",
                    },
                },
            ]
        }
        mock_ctx, _ = _telegram_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(limit=10, thread_id="10")

        assert len(msgs) == 1
        assert msgs[0].text == "reply to 10"
        assert msgs[0].thread_id == "10"

    def test_cursor_increments_update_id(self):
        from slackker.core.telegram import TelegramClient

        client = TelegramClient(token="123:ABC", chat_id="99")
        msg = _msg(timestamp="500", platform="telegram")
        assert client.cursor_from_message(msg) == "501"


# ── Discord fetch_messages ────────────────────────────────────────────────────


def _discord_mock_ctx(messages_payload):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = messages_payload

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx, mock_http


class TestDiscordFetchMessages:
    @pytest.mark.asyncio
    async def test_returns_oldest_first(self):
        from slackker.core.discord import DiscordClient

        client = DiscordClient(token="Bot-token", channel_id="CH1")
        payload = [
            {
                "id": "200",
                "content": "newer",
                "author": {"id": "U2", "username": "Bob", "bot": False},
            },
            {
                "id": "100",
                "content": "older",
                "author": {"id": "U1", "username": "Alice", "bot": False},
            },
        ]
        mock_ctx, _ = _discord_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(limit=10)

        assert len(msgs) == 2
        assert msgs[0].text == "older"
        assert msgs[1].text == "newer"
        assert msgs[0].platform == "discord"
        assert msgs[0].timestamp == "100"

    @pytest.mark.asyncio
    async def test_since_passed_as_after(self):
        from slackker.core.discord import DiscordClient

        client = DiscordClient(token="Bot-token", channel_id="CH1")
        mock_ctx, mock_http = _discord_mock_ctx([])

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            await client.fetch_messages(limit=5, since="123456789")

        call_kwargs = mock_http.get.call_args
        assert call_kwargs[1]["params"]["after"] == "123456789"

    @pytest.mark.asyncio
    async def test_thread_filter_by_message_reference(self):
        from slackker.core.discord import DiscordClient

        client = DiscordClient(token="Bot-token", channel_id="CH1")
        payload = [
            {
                "id": "200",
                "content": "reply",
                "author": {"id": "U2", "username": "Bob", "bot": False},
                "message_reference": {"message_id": "100"},
            },
            {
                "id": "300",
                "content": "unrelated",
                "author": {"id": "U3", "username": "Eve", "bot": False},
            },
        ]
        mock_ctx, _ = _discord_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(limit=10, thread_id="100")

        assert len(msgs) == 1
        assert msgs[0].text == "reply"
        assert msgs[0].thread_id == "100"

    @pytest.mark.asyncio
    async def test_bot_flag(self):
        from slackker.core.discord import DiscordClient

        client = DiscordClient(token="Bot-token", channel_id="CH1")
        payload = [
            {
                "id": "1",
                "content": "bot says hi",
                "author": {"id": "B1", "username": "mybot", "bot": True},
            },
        ]
        mock_ctx, _ = _discord_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages()

        assert msgs[0].is_bot is True

    def test_cursor_returns_timestamp_unchanged(self):
        from slackker.core.discord import DiscordClient

        client = DiscordClient(token="Bot-token", channel_id="CH1")
        msg = _msg(timestamp="987654321", platform="discord")
        assert client.cursor_from_message(msg) == "987654321"


# ── Teams fetch_messages ──────────────────────────────────────────────────────


def _teams_mock_ctx(value_payload):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"value": value_payload}

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx, mock_http


class TestTeamsFetchMessages:
    def _connected_client(self):
        from slackker.core.teams import TeamsClient

        client = TeamsClient(app_id="app-id", chat_id="19:chat@thread.v2")
        client._access_token = "fake-token"
        client._token_expiry = time.time() + 3600
        return client

    @pytest.mark.asyncio
    async def test_fetch_basic_message(self):
        client = self._connected_client()
        payload = [
            {
                "id": "msg1",
                "body": {"content": "hello teams"},
                "from": {"user": {"id": "U1", "displayName": "Alice"}},
                "createdDateTime": "2024-01-01T10:00:00Z",
            }
        ]
        mock_ctx, _ = _teams_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(limit=10)

        assert len(msgs) == 1
        assert msgs[0].text == "hello teams"
        assert msgs[0].sender == "Alice"
        assert msgs[0].platform == "teams"
        assert msgs[0].timestamp == "2024-01-01T10:00:00Z"

    @pytest.mark.asyncio
    async def test_returns_oldest_first(self):
        client = self._connected_client()
        payload = [
            {
                "id": "msg2",
                "body": {"content": "newer"},
                "from": {"user": {"id": "U1", "displayName": "Alice"}},
                "createdDateTime": "2024-01-01T10:01:00Z",
            },
            {
                "id": "msg1",
                "body": {"content": "older"},
                "from": {"user": {"id": "U1", "displayName": "Alice"}},
                "createdDateTime": "2024-01-01T10:00:00Z",
            },
        ]
        mock_ctx, _ = _teams_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages()

        assert msgs[0].text == "older"
        assert msgs[1].text == "newer"

    @pytest.mark.asyncio
    async def test_since_filters_client_side(self):
        client = self._connected_client()
        payload = [
            {
                "id": "msg2",
                "body": {"content": "after"},
                "from": {"user": {"id": "U1", "displayName": "Alice"}},
                "createdDateTime": "2024-01-01T10:01:00Z",
            },
            {
                "id": "msg1",
                "body": {"content": "before"},
                "from": {"user": {"id": "U1", "displayName": "Alice"}},
                "createdDateTime": "2024-01-01T10:00:00Z",
            },
        ]
        mock_ctx, _ = _teams_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages(since="2024-01-01T10:00:00Z")

        # Only the message with timestamp > since should be returned
        assert len(msgs) == 1
        assert msgs[0].text == "after"

    @pytest.mark.asyncio
    async def test_thread_replies_url(self):
        client = self._connected_client()
        mock_ctx, mock_http = _teams_mock_ctx([])

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            await client.fetch_messages(thread_id="msg1")

        call_args = mock_http.get.call_args
        assert "/messages/msg1/replies" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_bot_message_flagged(self):
        client = self._connected_client()
        payload = [
            {
                "id": "msg1",
                "body": {"content": "automated"},
                "from": {"application": {"id": "APP1", "displayName": "MyBot"}},
                "createdDateTime": "2024-01-01T10:00:00Z",
            }
        ]
        mock_ctx, _ = _teams_mock_ctx(payload)

        with patch("slackker.utils.network._make_async_client", return_value=mock_ctx):
            msgs = await client.fetch_messages()

        assert msgs[0].is_bot is True

    @pytest.mark.asyncio
    async def test_not_connected_returns_empty(self):
        from slackker.core.teams import TeamsClient

        client = TeamsClient(app_id="app-id", chat_id="19:chat@thread.v2")
        # _access_token is None -> not connected; connect() would do device flow -> mock it
        client.connect = AsyncMock(return_value=False)

        msgs = await client.fetch_messages()
        assert msgs == []


# ── MessagePoller ─────────────────────────────────────────────────────────────


class TestMessagePoller:
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.05)

        await poller.start()
        assert poller.is_running

        await asyncio.sleep(0.15)
        assert len(client.fetch_calls) >= 2  # multiple polls happened

        await poller.stop()
        assert not poller.is_running

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.1)

        await poller.start()
        task1 = poller._task
        await poller.start()  # second call is a no-op
        task2 = poller._task

        assert task1 is task2
        await poller.stop()

    @pytest.mark.asyncio
    async def test_on_message_handler_called(self):
        msgs = [_msg(text="hi", timestamp="1")]
        client = MockClient(messages=msgs)
        poller = MessagePoller(client, interval=0.05)

        received = []

        @poller.on_message
        async def handle(msg):
            received.append(msg.text)

        await poller.start()
        await asyncio.sleep(0.15)
        await poller.stop()

        assert "hi" in received

    @pytest.mark.asyncio
    async def test_on_message_decorator_returns_fn(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.5)

        @poller.on_message
        async def handler(msg):
            pass

        assert handler.__name__ == "handler"
        assert handler in poller._message_handlers

    @pytest.mark.asyncio
    async def test_cursor_advances_between_polls(self):
        """Poller must pass the cursor from the previous batch as since."""
        msg1 = _msg(text="first", timestamp="100")
        msg2 = _msg(text="second", timestamp="200")
        call_count = 0
        seen_cursors = []

        class SequentialClient(MockClient):
            async def fetch_messages(self, limit=10, since=None, thread_id=None):
                nonlocal call_count
                call_count += 1
                seen_cursors.append(since)
                if call_count == 1:
                    return [msg1]
                if call_count == 2:
                    return [msg2]
                return []

        client = SequentialClient()
        poller = MessagePoller(client, interval=0.05)
        delivered = []

        @poller.on_message
        async def collect(msg):
            delivered.append(msg.text)

        await poller.start()
        await asyncio.sleep(0.2)
        await poller.stop()

        assert "first" in delivered
        assert "second" in delivered
        # After first poll the cursor should be "100"; second poll receives it as since
        assert "100" in seen_cursors

    @pytest.mark.asyncio
    async def test_filter_fn_excludes_messages(self):
        msgs = [
            _msg(text="keep", timestamp="1", is_bot=False),
            _msg(text="discard", timestamp="2", is_bot=True),
        ]
        client = MockClient(messages=msgs)
        poller = MessagePoller(client, interval=0.05, filter_fn=lambda m: not m.is_bot)

        received = []

        @poller.on_message
        async def handle(msg):
            received.append(msg.text)

        await poller.start()
        await asyncio.sleep(0.15)
        await poller.stop()

        assert "keep" in received
        assert "discard" not in received

    @pytest.mark.asyncio
    async def test_on_command_dispatch(self):
        msgs = [_msg(text="/stop now", timestamp="1")]
        client = MockClient(messages=msgs)
        poller = MessagePoller(client, interval=0.05)

        fired_args = []

        async def stop_handler(msg, args):
            fired_args.append(args)

        poller.on_command("/stop", stop_handler)

        await poller.start()
        await asyncio.sleep(0.15)
        await poller.stop()

        assert "now" in fired_args

    @pytest.mark.asyncio
    async def test_on_command_no_match_for_other_messages(self):
        msgs = [_msg(text="just chatting", timestamp="1")]
        client = MockClient(messages=msgs)
        poller = MessagePoller(client, interval=0.05)

        fired = []

        async def stop_handler(msg, args):
            fired.append(args)

        poller.on_command("/stop", stop_handler)

        await poller.start()
        await asyncio.sleep(0.15)
        await poller.stop()

        assert fired == []

    @pytest.mark.asyncio
    async def test_wait_for_reply_receives_dispatched_message(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.1)
        await poller.start()

        msg = _msg(text="yes!", timestamp="99")

        async def deliver():
            await asyncio.sleep(0.05)
            await poller._dispatch(msg)

        asyncio.create_task(deliver())
        result = await poller.wait_for_reply(timeout=1.0)

        assert result is not None
        assert result.text == "yes!"
        await poller.stop()

    @pytest.mark.asyncio
    async def test_wait_for_reply_timeout_returns_none(self):
        client = MockClient()  # no messages
        poller = MessagePoller(client, interval=0.05)
        await poller.start()

        result = await poller.wait_for_reply(timeout=0.1)
        assert result is None
        await poller.stop()

    @pytest.mark.asyncio
    async def test_wait_for_reply_thread_filter(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.1)
        await poller.start()

        wrong_thread = _msg(text="wrong", timestamp="1", thread_id="other")
        right_thread = _msg(text="right", timestamp="2", thread_id="target")

        async def deliver():
            await asyncio.sleep(0.04)
            await poller._dispatch(wrong_thread)
            await asyncio.sleep(0.04)
            await poller._dispatch(right_thread)

        asyncio.create_task(deliver())
        result = await poller.wait_for_reply(timeout=1.0, thread_id="target")

        assert result is not None
        assert result.text == "right"
        await poller.stop()

    @pytest.mark.asyncio
    async def test_wait_for_reply_no_thread_accepts_any(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.1)
        await poller.start()

        msg = _msg(text="anything", timestamp="1", thread_id="some-thread")

        async def deliver():
            await asyncio.sleep(0.05)
            await poller._dispatch(msg)

        asyncio.create_task(deliver())
        result = await poller.wait_for_reply(timeout=1.0)  # no thread_id filter

        assert result is not None
        assert result.text == "anything"
        await poller.stop()

    @pytest.mark.asyncio
    async def test_multiple_waiters_each_receive_message(self):
        client = MockClient()
        poller = MessagePoller(client, interval=0.1)
        await poller.start()

        msg = _msg(text="broadcast", timestamp="1")

        async def deliver():
            await asyncio.sleep(0.05)
            await poller._dispatch(msg)

        asyncio.create_task(deliver())

        r1, r2 = await asyncio.gather(
            poller.wait_for_reply(timeout=1.0),
            poller.wait_for_reply(timeout=1.0),
        )

        assert r1 is not None and r1.text == "broadcast"
        assert r2 is not None and r2.text == "broadcast"
        await poller.stop()

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash_poller(self):
        msgs = [_msg(text="hi", timestamp="1")]
        client = MockClient(messages=msgs)
        poller = MessagePoller(client, interval=0.05)

        @poller.on_message
        async def bad_handler(msg):
            raise RuntimeError("handler exploded")

        good_received = []

        @poller.on_message
        async def good_handler(msg):
            good_received.append(msg.text)

        await poller.start()
        await asyncio.sleep(0.15)
        await poller.stop()

        # Good handler should still run despite bad_handler raising
        assert "hi" in good_received


# ── CommandHandler ────────────────────────────────────────────────────────────


class TestCommandHandler:
    def test_command_decorator_registers_with_prefix(self):
        client = MockClient()
        handler = CommandHandler(client, command_prefix="/")

        @handler.command("status")
        async def on_status(msg, args):
            pass

        assert "/status" in handler.poller._command_handlers
        assert handler.poller._command_handlers["/status"] is on_status

    def test_command_decorator_returns_original_fn(self):
        client = MockClient()
        handler = CommandHandler(client)

        @handler.command("ping")
        async def on_ping(msg, args):
            pass

        assert on_ping.__name__ == "on_ping"

    def test_custom_prefix(self):
        client = MockClient()
        handler = CommandHandler(client, command_prefix="!")

        @handler.command("help")
        async def on_help(msg, args):
            pass

        assert "!help" in handler.poller._command_handlers
        assert "/help" not in handler.poller._command_handlers

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        client = MockClient()
        handler = CommandHandler(client, interval=0.05)

        assert not handler.is_running
        await handler.start()
        assert handler.is_running
        await handler.stop()
        assert not handler.is_running

    @pytest.mark.asyncio
    async def test_command_fired_on_matching_message(self):
        msgs = [_msg(text="/ping hello world", timestamp="1")]
        client = MockClient(messages=msgs)
        handler = CommandHandler(client, command_prefix="/", interval=0.05)

        received = []

        @handler.command("ping")
        async def on_ping(msg, args):
            received.append(args)

        await handler.start()
        await asyncio.sleep(0.15)
        await handler.stop()

        assert "hello world" in received

    @pytest.mark.asyncio
    async def test_multiple_commands_registered(self):
        client = MockClient()
        handler = CommandHandler(client)

        @handler.command("start")
        async def on_start(msg, args):
            pass

        @handler.command("stop")
        async def on_stop(msg, args):
            pass

        @handler.command("status")
        async def on_status(msg, args):
            pass

        assert len(handler.poller._command_handlers) == 3

    def test_poller_attribute_accessible(self):
        client = MockClient()
        handler = CommandHandler(client)
        assert isinstance(handler.poller, MessagePoller)

    @pytest.mark.asyncio
    async def test_wait_for_reply_via_poller(self):
        client = MockClient()
        handler = CommandHandler(client, interval=0.1)
        await handler.start()

        msg = _msg(text="user reply", timestamp="5")

        async def deliver():
            await asyncio.sleep(0.05)
            await handler.poller._dispatch(msg)

        asyncio.create_task(deliver())
        result = await handler.poller.wait_for_reply(timeout=1.0)

        assert result is not None
        assert result.text == "user reply"
        await handler.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
