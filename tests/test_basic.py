"""
Comprehensive tests for slackker.callbacks.simple and slackker.callbacks.basic modules.
Tests cover SimpleCallback and backward-compatible Update/SlackUpdate/TelegramUpdate shims.
"""

import pytest
import warnings
from unittest.mock import AsyncMock, MagicMock, patch
from slackker.callbacks.simple import SimpleCallback
from slackker.callbacks.basic import Update, SlackUpdate, TelegramUpdate
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


def _make_update(verbose=0):
    """Legacy helper using deprecated Update."""
    client = MockClient(verbose=verbose)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        return Update(client), client


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


# ── Deprecated Update alias test ─────────────────────────────

class TestUpdateDeprecation:
    """Ensure Update emits DeprecationWarning and still works."""

    def test_update_deprecation_warning(self):
        client = MockClient()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = Update(client)
            assert any(issubclass(x.category, DeprecationWarning) for x in w)
            assert any("Update is deprecated" in str(x.message) for x in w)

    def test_update_still_functions(self):
        client = MockClient()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = Update(client)

        obj.notify("test_event", x=1)
        assert any("test_event" in m for m in client.messages)


# ── Backward-compat shim tests ───────────────────────────────

class TestSlackUpdateShim:
    """Test backward-compatible SlackUpdate."""

    @patch("slackker.callbacks.basic.SlackClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = SlackUpdate(token="test", channel="C123", verbose=0)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "SlackUpdate is deprecated" in str(w[0].message)

    @patch("slackker.callbacks.basic.SlackClient")
    def test_init_success(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = SlackUpdate(token="test", channel="C123", verbose=0)

        assert hasattr(obj, "client")
        assert obj.client is mock_client

    def test_init_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = SlackUpdate(token=None, channel="C123")
        assert not hasattr(obj, "client")


class TestTelegramUpdateShim:
    """Test backward-compatible TelegramUpdate."""

    @patch("slackker.callbacks.basic.TelegramClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = TelegramUpdate(token="test", verbose=0)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

    @patch("slackker.callbacks.basic.TelegramClient")
    def test_init_success(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = TelegramUpdate(token="test", verbose=0)

        assert hasattr(obj, "client")

    def test_init_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = TelegramUpdate(token=None)
        assert not hasattr(obj, "client")


class TestShimWorkflows:
    """Integration-style tests using the shims with a mock client."""

    @patch("slackker.callbacks.basic.SlackClient")
    def test_slack_notifier_and_notify(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = SlackUpdate(token="xoxb-test", channel="C123", verbose=0)

        @obj.notifier
        def compute(x, y):
            return x + y, x * y

        s, p = compute(5, 3)
        assert s == 8
        assert p == 15

        obj.notify(f"Sum: {s}", product=f"{p}")
        assert len(mock_client.messages) == 2

    @patch("slackker.callbacks.basic.TelegramClient")
    def test_telegram_notifier_and_notify(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = TelegramUpdate(token="123:ABC", verbose=0)

        @obj.notifier
        def func():
            return "v1", "v2"

        func()
        obj.notify("arg1", detail="arg2", value="str")
        assert len(mock_client.messages) == 2


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
        client = MockClient()          # is_connected always True
        SimpleCallback(client)
        # MockClient has no connect_calls attr — just ensure no AttributeError
        assert client.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
