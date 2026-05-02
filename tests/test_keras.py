"""
Comprehensive tests for slackker.callbacks.keras module.
Tests cover the new unified KerasCallback class and backward-compatible shims.
"""

import pytest
import warnings
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from slackker.callbacks.keras import KerasCallback, SlackUpdate, TelegramUpdate
from slackker.core.client import BaseClient


# ── Fixtures ──────────────────────────────────────────────────

class MockClient(BaseClient):
    """Concrete test client that records calls."""

    def __init__(self, verbose=0, platform_name="mock"):
        super().__init__(verbose=verbose)
        self._platform_name = platform_name
        self.messages = []
        self.uploaded_files = []
        self.uploaded_images = []

    @property
    def platform(self):
        return self._platform_name

    @property
    def is_connected(self):
        return True

    async def send_message(self, text):
        self.messages.append(text)

    async def upload_file(self, filepath, comment=None):
        self.uploaded_files.append((filepath, comment))

    async def upload_image(self, filepath, comment=None):
        self.uploaded_images.append((filepath, comment))


def _make_callback(platform="slack", verbose=0, send_plot=False, export="png"):
    client = MockClient(verbose=verbose, platform_name=platform)
    cb = KerasCallback(
        client=client,
        model_name="TestModel",
        export=export,
        send_plot=send_plot,
    )
    return cb, client


# ── KerasCallback initialization ──────────────────────────────

class TestKerasCallbackInit:
    def test_init_stores_attributes(self):
        cb, _ = _make_callback()
        assert cb.model_name == "TestModel"
        assert cb.export == "png"
        assert cb.send_plot is False
        assert cb.n_epochs == 0
        assert cb.train_loss == []
        assert cb.train_acc == []

    def test_init_rejects_bad_format(self):
        m = MockClient()
        with pytest.raises(ValueError, match="Unsupported export format"):
            KerasCallback(client=m, model_name="M", export="bmp")


# ── on_train_begin ────────────────────────────────────────────

class TestOnTrainBegin:
    def test_posts_training_start(self):
        cb, client = _make_callback()
        cb.on_train_begin()
        assert len(client.messages) == 1
        assert "TestModel" in client.messages[0]
        assert "started at" in client.messages[0]


# ── on_epoch_end ──────────────────────────────────────────────

class TestOnEpochEnd:
    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_tracks_metrics_and_reports(self, mock_check):
        cb, client = _make_callback()
        logs = {"accuracy": 0.85, "loss": 0.45, "val_accuracy": 0.80, "val_loss": 0.50}
        cb.on_epoch_end(batch=0, logs=logs)

        assert cb.n_epochs == 1
        assert len(cb.train_loss) == 1
        assert len(cb.valid_loss) == 1
        assert len(client.messages) == 1
        assert "Epoch: 0" in client.messages[0]

    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=False)
    def test_skips_report_without_internet(self, mock_check):
        cb, client = _make_callback()
        logs = {"accuracy": 0.85, "loss": 0.45, "val_accuracy": 0.80, "val_loss": 0.50}
        cb.on_epoch_end(batch=0, logs=logs)

        assert cb.n_epochs == 1
        assert len(cb.train_loss) == 1
        assert len(client.messages) == 0

    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_multiple_epochs(self, mock_check):
        cb, client = _make_callback()
        epochs_logs = [
            {"accuracy": 0.70, "loss": 0.60, "val_accuracy": 0.65, "val_loss": 0.65},
            {"accuracy": 0.80, "loss": 0.45, "val_accuracy": 0.75, "val_loss": 0.50},
            {"accuracy": 0.85, "loss": 0.35, "val_accuracy": 0.82, "val_loss": 0.40},
        ]
        for i, logs in enumerate(epochs_logs):
            cb.on_epoch_end(batch=i, logs=logs)

        assert cb.n_epochs == 3
        assert len(cb.train_loss) == 3
        assert cb.train_loss[-1] == 0.35
        assert cb.valid_acc[-1] == 0.82


# ── on_train_end ──────────────────────────────────────────────

class TestOnTrainEnd:
    def test_reports_best_epoch(self):
        cb, client = _make_callback()
        cb.train_loss = [0.60, 0.45, 0.35, 0.40]
        cb.train_acc = [0.70, 0.80, 0.85, 0.84]
        cb.valid_loss = [0.65, 0.50, 0.38, 0.42]
        cb.valid_acc = [0.65, 0.75, 0.82, 0.80]
        cb.n_epochs = 4

        cb.on_train_end()

        found_best = any("Best epoch was 2" in m for m in client.messages)
        assert found_best

    @patch("slackker.callbacks.keras.plotting.generate_and_get_plots", return_value=["/tmp/loss.png", "/tmp/acc.png"])
    def test_uploads_plots_when_enabled(self, mock_plots):
        cb, client = _make_callback(send_plot=True)
        cb.train_loss = [0.6, 0.4]
        cb.train_acc = [0.7, 0.8]
        cb.valid_loss = [0.65, 0.45]
        cb.valid_acc = [0.65, 0.78]
        cb.n_epochs = 2

        cb.on_train_end()

        assert len(client.uploaded_images) == 2
        mock_plots.assert_called_once()

    def test_empty_valid_loss_skips_best(self):
        cb, client = _make_callback()
        cb.n_epochs = 0
        cb.on_train_end()
        # No messages about best epoch when no data
        assert not any("Best epoch" in m for m in client.messages)


# ── Log ordering ──────────────────────────────────────────────

class TestLogOrdering:
    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_logs_stored_in_order(self, mock_check):
        cb, _ = _make_callback()
        for i in range(3):
            logs = {
                "accuracy": 0.5 + i * 0.1,
                "loss": 0.9 - i * 0.1,
                "val_accuracy": 0.4 + i * 0.1,
                "val_loss": 1.0 - i * 0.1,
            }
            cb.on_epoch_end(batch=i, logs=logs)

        assert cb.train_acc == pytest.approx([0.5, 0.6, 0.7])
        assert cb.train_loss == pytest.approx([0.9, 0.8, 0.7])
        assert cb.valid_acc == pytest.approx([0.4, 0.5, 0.6])
        assert cb.valid_loss == pytest.approx([1.0, 0.9, 0.8])


# ── Complete workflow ─────────────────────────────────────────

class TestCompleteWorkflow:
    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    @patch("slackker.callbacks.keras.plotting.generate_and_get_plots", return_value=["/tmp/loss.png"])
    def test_full_training(self, mock_plots, mock_check):
        cb, client = _make_callback(send_plot=True)

        cb.on_train_begin()
        for epoch in range(5):
            logs = {
                "accuracy": 0.70 + epoch * 0.03,
                "loss": 0.60 - epoch * 0.05,
                "val_accuracy": 0.65 + epoch * 0.03,
                "val_loss": 0.65 - epoch * 0.05,
            }
            cb.on_epoch_end(batch=epoch, logs=logs)
        cb.on_train_end()

        assert cb.n_epochs == 5
        assert len(client.messages) >= 7  # 1 begin + 5 epochs + 2 end summaries


# ── Backward-compat shim tests ───────────────────────────────

class TestSlackUpdateShim:
    @patch("slackker.callbacks.keras.SlackClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client._client = MagicMock()
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cb = SlackUpdate(token="xoxb-test", channel="C123", ModelName="M")
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    @patch("slackker.callbacks.keras.SlackClient")
    def test_shim_preserves_old_attrs(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client._client = MagicMock()
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = SlackUpdate(token="xoxb-test", channel="C123", ModelName="M", SendPlot=True, verbose=2)

        assert cb.ModelName == "M"
        assert cb.SendPlot is True
        assert cb.verbose == 2

    def test_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = SlackUpdate(token=None, channel="C123", ModelName="M")
        assert not hasattr(cb, "client")


class TestTelegramUpdateShim:
    @patch("slackker.callbacks.keras.TelegramClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.chat_id = "99999"
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cb = TelegramUpdate(token="123:ABC", ModelName="M")
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = TelegramUpdate(token=None, ModelName="M")
        assert not hasattr(cb, "client")


class TestKerasCallbackMessageFormatting:
    """Test message formatting in Keras callbacks using MockClient."""

    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_epoch_message_format(self, mock_check):
        cb, client = _make_callback()
        logs = {
            "accuracy": 0.8234,
            "loss": 0.4567,
            "val_accuracy": 0.7956,
            "val_loss": 0.5123,
        }
        cb.on_epoch_end(batch=0, logs=logs)

        assert len(client.messages) == 1
        message = client.messages[0]
        assert "Epoch: 0" in message
        assert "Training Loss:" in message
        assert "Validation Loss:" in message

    @patch("slackker.callbacks.keras.plotting.generate_and_get_plots", return_value=["loss.png"])
    def test_train_end_message_format(self, mock_plots):
        cb, client = _make_callback(send_plot=True)
        cb.train_loss = [0.60, 0.45, 0.35]
        cb.train_acc = [0.70, 0.80, 0.85]
        cb.valid_loss = [0.65, 0.50, 0.40]
        cb.valid_acc = [0.65, 0.75, 0.82]
        cb.n_epochs = 3

        cb.on_train_end()

        assert len(client.messages) >= 2
        assert any("3 epochs" in m for m in client.messages)


class TestKerasCallbackAdditionalBranches:
    """Extra branch coverage for init and lifecycle error paths."""

    def test_init_export_none_raises(self):
        m = MockClient()
        with pytest.raises(ValueError, match="Unsupported export format"):
            KerasCallback(client=m, model_name="M", export=None)

    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_on_epoch_end_incomplete_logs_skips_tracking(self, mock_check):
        cb, client = _make_callback()
        cb.on_epoch_end(batch=0, logs={"accuracy": 0.8, "loss": 0.2})
        # With < 4 log values, metrics are not tracked but epoch still counts
        assert cb.n_epochs == 1
        assert cb.train_loss == []

    @patch("slackker.callbacks.keras.network.check_connection_quick", new_callable=AsyncMock, return_value=False)
    def test_on_epoch_end_no_internet_still_tracks(self, mock_check):
        cb, client = _make_callback()
        logs = {
            "accuracy": 0.85,
            "loss": 0.45,
            "val_accuracy": 0.80,
            "val_loss": 0.50,
        }
        cb.on_epoch_end(batch=0, logs=logs)

        assert cb.n_epochs == 1
        assert cb.valid_loss == [0.50]
        assert len(client.messages) == 0

    @patch("slackker.callbacks.keras.plotting.generate_and_get_plots", return_value=["loss.png"])
    def test_train_end_message_contains_accuracy_percent(self, mock_plots):
        cb, client = _make_callback(send_plot=True)
        cb.train_loss = [0.60, 0.45, 0.35]
        cb.train_acc = [0.70, 0.80, 0.85]
        cb.valid_loss = [0.65, 0.50, 0.40]
        cb.valid_acc = [0.65, 0.75, 0.82]
        cb.n_epochs = 3

        cb.on_train_end()

        assert any("Best Accuracy =" in m and "%" in m for m in client.messages)


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
    """Verify that KerasCallback calls connect() when the client is not yet connected."""

    def test_connects_when_not_connected(self):
        client = DisconnectedMockClient()
        assert not client.is_connected
        KerasCallback(client=client, model_name="M", export="png")
        assert client.connect_calls == 1
        assert client.is_connected

    def test_skips_connect_when_already_connected(self):
        client = MockClient()          # is_connected always True
        KerasCallback(client=client, model_name="M", export="png")
        assert client.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
