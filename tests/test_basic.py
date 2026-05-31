"""Comprehensive tests for `slackker.callbacks.simple` module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from slackker.callbacks.simple import SimpleCallback
from slackker.core.client import BaseClient

# ── Fixtures ──────────────────────────────────────────────────


class MockClient(BaseClient):
    """Concrete test client that records calls."""

    def __init__(self, verbose=0):
        super().__init__(verbose=verbose)
        self.messages = []
        self.uploaded_files = []
        self.uploaded_images = []

    @property
    def platform(self):
        return "mock"

    @property
    def connectivity_url(self):
        return "mock.example.com"

    @property
    def is_connected(self):
        return True

    async def send_message(self, text):
        self.messages.append(text)

    async def upload_file(self, filepath, comment=None):
        self.uploaded_files.append((filepath, comment))

    async def upload_image(self, filepath, comment=None):
        self.uploaded_images.append((filepath, comment))


def _make_callback(verbose=0):
    client = MockClient(verbose=verbose)
    return SimpleCallback(client), client


# ── SimpleCallback tests ──────────────────────────────────────


class TestSimpleCallbackNotifier:
    """Test SimpleCallback.notifier decorator."""

    def test_notifier_with_tuple_return(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return "a", "b"

        result = func()
        assert result == ("a", "b")
        assert len(client.messages) == 1
        assert "func" in client.messages[0]
        assert "Returned 2 outputs" in client.messages[0]
        assert "a" in client.messages[0]
        assert "b" in client.messages[0]

    def test_notifier_with_single_return(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return "single"

        result = func()
        assert result == "single"
        assert "Returned output: single" in client.messages[0]

    def test_notifier_with_none_return(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return None

        result = func()
        assert result is None
        assert "Returned output: None" in client.messages[0]

    def test_notifier_execution_time(self):
        import time

        cb, client = _make_callback()

        @cb.notifier
        def func():
            time.sleep(0.05)
            return "done"

        func()
        assert "Execution time:" in client.messages[0]

    def test_notifier_with_args(self):
        cb, client = _make_callback(verbose=1)

        @cb.notifier
        def add(a, b):
            return a + b

        result = add(10, 20)
        assert result == 30

    def test_notifier_with_exception(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            func()

    def test_notifier_with_empty_tuple(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return ()

        result = func()
        assert result == ()

    def test_notifier_with_dict_return(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return {"key": "value"}

        result = func()
        assert result == {"key": "value"}

    def test_notifier_with_list_return(self):
        cb, client = _make_callback()

        @cb.notifier
        def func():
            return [1, 2, 3]

        result = func()
        assert result == [1, 2, 3]


class TestSimpleCallbackNotify:
    """Test SimpleCallback.notify method."""

    def test_notify_with_event(self):
        cb, client = _make_callback()
        cb.notify("my_event", detail="arg2")

        assert len(client.messages) == 1
        assert "Notification: my_event" in client.messages[0]
        assert "detail: arg2" in client.messages[0]

    def test_notify_with_kwargs(self):
        cb, client = _make_callback()
        cb.notify(value="string", status="completed")

        msg = client.messages[0]
        assert "value: string" in msg
        assert "status: completed" in msg

    def test_notify_with_mixed(self):
        cb, client = _make_callback()
        cb.notify("evt", arg2="a2", value="kwval")

        msg = client.messages[0]
        assert "evt" in msg
        assert "arg2: a2" in msg
        assert "value: kwval" in msg

    def test_notify_timestamp(self):
        cb, client = _make_callback()
        cb.notify()

        assert "Notification:" in client.messages[0]

    def test_notify_with_attachment(self):
        cb, client = _make_callback()
        cb.notify("done", attachment="/tmp/model.ckpt")

        assert len(client.uploaded_files) == 1
        assert client.uploaded_files[0][0] == "/tmp/model.ckpt"
        assert "done" in client.uploaded_files[0][1]


class TestAsyncNotify:
    """Test async variant of notify."""

    @pytest.mark.asyncio
    async def test_async_notify(self):
        cb, client = _make_callback()
        await cb.async_notify("async_event", key="val")

        assert len(client.messages) == 1
        assert "async_event" in client.messages[0]
        assert "key: val" in client.messages[0]

    @pytest.mark.asyncio
    async def test_async_notify_attachment(self):
        cb, client = _make_callback()
        await cb.async_notify("done", attachment="/tmp/file.zip")

        assert len(client.uploaded_files) == 1


# ── Auto-connect tests ───────────────────────────────────────


class DisconnectedMockClient(MockClient):
    """MockClient that starts disconnected and records connect() calls."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect_calls = 0
        self._connected = False

    @property
    def is_connected(self):
        return self._connected

    async def connect(self):
        self.connect_calls += 1
        self._connected = True
        return True


class TestAutoConnect:
    """Verify that SimpleCallback calls connect() when the client is not yet connected."""

    def test_connects_when_not_connected(self):
        client = DisconnectedMockClient()
        assert not client.is_connected
        SimpleCallback(client)
        assert client.connect_calls == 1
        assert client.is_connected

    def test_skips_connect_when_already_connected(self):
        client = MockClient()  # is_connected always True
        SimpleCallback(client)
        # MockClient has no connect_calls attr — just ensure no AttributeError
        assert client.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ── SimpleCallback.ask / async_ask / stop / async_stop tests ─────────────────


class MockPoller:
    """Minimal MessagePoller stand-in that returns a preset reply."""

    def __init__(self, reply=None):
        self._reply = reply

    async def wait_for_reply(self, timeout=60.0):
        return self._reply


def _make_reply(text="yes", sender="human"):
    from slackker.core.models import IncomingMessage

    return IncomingMessage(
        text=text,
        sender=sender,
        sender_id="u1",
        timestamp="1",
        platform="mock",
        is_bot=False,
    )


def _patch_listener(cb, reply=None):
    """Inject a fake CommandHandler+poller into cb._listener."""
    poller = MockPoller(reply=reply)
    listener = MagicMock()
    listener.poller = poller
    listener.stop = AsyncMock()
    cb._listener = listener
    return poller, listener


class TestAsyncAsk:
    """Tests for SimpleCallback.async_ask()."""

    @pytest.mark.asyncio
    async def test_returns_true_on_yes_reply(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        assert await cb.async_ask("Continue?") is True

    @pytest.mark.asyncio
    async def test_returns_false_on_no_reply(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("no"))
        assert await cb.async_ask("Continue?") is False

    @pytest.mark.asyncio
    async def test_returns_true_on_timeout(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=None)
        assert await cb.async_ask("Continue?") is True

    @pytest.mark.asyncio
    async def test_sends_question_message(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        await cb.async_ask("Step 1 done?")
        assert any("Step 1 done?" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_question_includes_halt_on_hint(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        await cb.async_ask("Continue?", halt_on="abort")
        assert any("abort" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_question_includes_timeout_hint(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        await cb.async_ask("Continue?", timeout=30.0)
        assert any("30" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_sends_halted_message_on_no(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("no", sender="alice"))
        await cb.async_ask("Continue?")
        assert any("🛑" in m and "alice" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_sends_continuing_message_with_sender(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes", sender="bob"))
        await cb.async_ask("Continue?")
        assert any("bob" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_sends_timeout_auto_approved_message(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=None)
        await cb.async_ask("Continue?")
        assert any("timeout" in m for m in client.messages)

    @pytest.mark.asyncio
    async def test_custom_halt_on(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("stop"))
        assert await cb.async_ask("Continue?", halt_on="stop") is False

    @pytest.mark.asyncio
    async def test_halt_on_is_case_insensitive(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("NO"))
        assert await cb.async_ask("Continue?", halt_on="no") is False

    @pytest.mark.asyncio
    async def test_non_halt_reply_returns_true(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("sure"))
        assert await cb.async_ask("Continue?") is True

    @pytest.mark.asyncio
    async def test_lazy_listener_created_on_first_ask(self):
        cb, client = _make_callback()
        assert cb._listener is None
        mock_handler = MagicMock()
        mock_handler.poller = MockPoller(reply=_make_reply("yes"))
        mock_handler.start = AsyncMock()
        with patch("slackker.listener.CommandHandler", return_value=mock_handler):
            await cb.async_ask("Continue?")
        assert cb._listener is mock_handler

    @pytest.mark.asyncio
    async def test_listener_reused_across_asks(self):
        cb, client = _make_callback()
        _, listener = _patch_listener(cb, reply=_make_reply("yes"))
        await cb.async_ask("Step 1?")
        await cb.async_ask("Step 2?")
        listener.start.assert_not_called()


class TestAskSync:
    """Tests for SimpleCallback.ask() — sync wrapper."""

    def test_returns_true_on_yes(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        assert cb.ask("Continue?") is True

    def test_returns_false_on_no(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("no"))
        assert cb.ask("Continue?") is False

    def test_returns_true_on_timeout(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=None)
        assert cb.ask("Continue?") is True

    def test_sends_messages(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        cb.ask("Step done?")
        assert any("Step done?" in m for m in client.messages)

    def test_persistent_loop_reused_across_calls(self):
        """Regression: second ask() must reuse the same event loop so the
        polling Task (bound to loop 1) is still alive to resolve wait_for_reply."""
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        cb.ask("Step 1?")
        loop_after_first = cb._sync_loop
        cb.ask("Step 2?")
        assert cb._sync_loop is loop_after_first  # same loop, not a new one

    def test_persistent_loop_created_on_first_ask(self):
        cb, client = _make_callback()
        assert cb._sync_loop is None
        _patch_listener(cb, reply=_make_reply("yes"))
        cb.ask("Step 1?")
        assert cb._sync_loop is not None

    def test_stop_shuts_down_loop(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        cb.ask("Step 1?")
        assert cb._sync_loop is not None
        cb.stop()
        assert cb._sync_loop is None


class TestStop:
    """Tests for SimpleCallback.async_stop() and stop()."""

    @pytest.mark.asyncio
    async def test_async_stop_clears_listener(self):
        cb, client = _make_callback()
        _, listener = _patch_listener(cb)
        await cb.async_stop()
        assert cb._listener is None
        listener.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_stop_noop_when_no_listener(self):
        cb, client = _make_callback()
        await cb.async_stop()  # must not raise

    def test_stop_sync_clears_listener(self):
        cb, client = _make_callback()
        _, listener = _patch_listener(cb)
        cb.stop()
        assert cb._listener is None
        listener.stop.assert_awaited_once()

    def test_stop_sync_noop_when_no_listener(self):
        cb, client = _make_callback()
        cb.stop()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_after_ask_cleans_up(self):
        cb, client = _make_callback()
        _patch_listener(cb, reply=_make_reply("yes"))
        await cb.async_ask("Continue?")
        await cb.async_stop()
        assert cb._listener is None
