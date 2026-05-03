"""
Tests for slackker.callbacks.lightning module.
Tests cover the new unified LightningCallback class and backward-compatible shims.
"""

import pytest
import warnings
import numpy as np
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from slackker.callbacks.lightning import LightningCallback, SlackUpdate, TelegramUpdate
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


def _trainer_with_metrics(metrics):
    return SimpleNamespace(callback_metrics=metrics)


def _make_callback(
    platform="slack",
    verbose=0,
    track_logs=None,
    monitor="val_loss",
    send_plot=False,
):
    if track_logs is None:
        track_logs = ["train_loss", "train_acc", "val_loss", "val_acc"]
    client = MockClient(verbose=verbose, platform_name=platform)
    cb = LightningCallback(
        client=client,
        model_name="TestModel",
        track_logs=track_logs,
        monitor=monitor,
        export="png",
        send_plot=send_plot,
    )
    return cb, client


# ── LightningCallback initialization ─────────────────────────

class TestLightningCallbackInit:
    def test_init_stores_attributes(self):
        cb, _ = _make_callback()
        assert cb.model_name == "TestModel"
        assert cb.track_logs == ["train_loss", "train_acc", "val_loss", "val_acc"]
        assert cb.monitor == "val_loss"
        assert cb.export == "png"
        assert cb.send_plot is False
        assert cb.training_logs == {}
        assert cb.n_epochs == 0

    def test_init_requires_track_logs(self):
        m = MockClient()
        with pytest.raises(SystemExit):
            LightningCallback(client=m, model_name="M", track_logs=None, monitor="val_loss")

    def test_init_track_logs_must_be_list(self):
        m = MockClient()
        with pytest.raises(SystemExit):
            LightningCallback(client=m, model_name="M", track_logs="train_loss", monitor="train_loss")

    def test_init_monitor_must_be_in_track_logs(self):
        m = MockClient()
        with pytest.raises(SystemExit):
            LightningCallback(
                client=m, model_name="M",
                track_logs=["train_loss", "val_loss"],
                monitor="val_acc",
            )

    def test_init_monitor_none_warns(self, capsys):
        # monitor=None should warn but not crash
        cb, _ = _make_callback(monitor=None)
        assert cb.monitor is None

    def test_init_rejects_bad_format(self):
        m = MockClient()
        with pytest.raises(ValueError, match="Unsupported export format"):
            LightningCallback(
                client=m, model_name="M",
                track_logs=["train_loss"], monitor="train_loss", export="bmp",
            )


# ── on_fit_start ──────────────────────────────────────────────

class TestOnFitStart:
    def test_posts_training_start(self):
        cb, client = _make_callback()
        cb.on_fit_start(trainer=None, pl_module=None)
        assert len(client.messages) == 1
        assert "TestModel" in client.messages[0]
        assert "started at" in client.messages[0]


# ── on_train_epoch_end ────────────────────────────────────────

class TestOnTrainEpochEnd:
    @patch("slackker.callbacks.lightning.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    def test_tracks_metrics_and_reports(self, mock_check):
        cb, client = _make_callback()
        trainer = _trainer_with_metrics({
            "train_loss": 0.90, "train_acc": 0.62, "val_loss": 0.84, "val_acc": 0.67,
        })
        cb.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert cb.n_epochs == 1
        assert cb.training_logs["train_loss"] == [0.90]
        assert cb.training_logs["val_loss"] == [0.84]
        assert len(client.messages) == 1
        assert "Epoch: 0" in client.messages[0]

    @patch("slackker.callbacks.lightning.network.check_connection_quick", new_callable=AsyncMock, return_value=False)
    def test_skips_report_without_internet(self, mock_check):
        cb, client = _make_callback()
        trainer = _trainer_with_metrics({
            "train_loss": 0.90, "train_acc": 0.62, "val_loss": 0.84, "val_acc": 0.67,
        })
        cb.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert cb.n_epochs == 1
        assert cb.training_logs["val_loss"] == [0.84]
        assert len(client.messages) == 0


# ── on_fit_end ────────────────────────────────────────────────

class TestOnFitEnd:
    def test_reports_best_epoch_loss_monitor(self):
        cb, client = _make_callback(monitor="val_loss")
        cb.training_logs = {
            "train_loss": [0.9, 0.7, 0.5],
            "train_acc": [0.6, 0.7, 0.8],
            "val_loss": [0.8, 0.4, 0.6],
            "val_acc": [0.65, 0.75, 0.72],
        }
        cb.n_epochs = 3

        cb.on_fit_end(trainer=None, pl_module=None)

        found = any("Best epoch was, Epoch 1" in m for m in client.messages)
        assert found

    def test_reports_best_epoch_acc_monitor(self):
        cb, client = _make_callback(monitor="val_acc")
        cb.training_logs = {
            "val_acc": [0.50, 0.72, 0.69],
            "val_loss": [0.7, 0.5, 0.6],
        }
        cb.n_epochs = 3

        cb.on_fit_end(trainer=None, pl_module=None)

        found = any("Best epoch was, Epoch 1" in m for m in client.messages)
        assert found

    def test_no_monitor_fallback_message(self):
        cb, client = _make_callback(monitor=None)
        cb.training_logs = {"train_loss": [0.9], "val_loss": [0.8]}
        cb.n_epochs = 1

        cb.on_fit_end(trainer=None, pl_module=None)

        found = any("monitor' was not provided" in m for m in client.messages)
        assert found

    @patch("slackker.callbacks.lightning.plotting.generate_and_get_plots", return_value=["/tmp/loss.png", "/tmp/acc.png"])
    def test_uploads_plots_when_enabled(self, mock_plots):
        cb, client = _make_callback(send_plot=True)
        cb.training_logs = {"train_loss": [0.9, 0.7], "val_loss": [0.8, 0.6]}
        cb.n_epochs = 2

        cb.on_fit_end(trainer=None, pl_module=None)

        assert len(client.uploaded_images) == 2
        mock_plots.assert_called_once()


# ── Complete workflow ─────────────────────────────────────────

class TestCompleteWorkflow:
    @patch("slackker.callbacks.lightning.network.check_connection_quick", new_callable=AsyncMock, return_value=True)
    @patch("slackker.callbacks.lightning.plotting.generate_and_get_plots", return_value=["/tmp/loss.png"])
    def test_full_training(self, mock_plots, mock_check):
        cb, client = _make_callback(send_plot=True)

        cb.on_fit_start(trainer=None, pl_module=None)
        for epoch in range(6):
            trainer = _trainer_with_metrics({
                "train_loss": 0.90 - (0.05 * epoch),
                "train_acc": 0.60 + (0.04 * epoch),
                "val_loss": 0.85 - (0.04 * epoch),
                "val_acc": 0.62 + (0.03 * epoch),
            })
            cb.on_train_epoch_end(trainer=trainer, pl_module=None)
        cb.on_fit_end(trainer=None, pl_module=None)

        assert cb.n_epochs == 6
        assert len(cb.training_logs["train_loss"]) == 6
        # 1 begin + 6 epochs + 1 summary
        assert len(client.messages) == 8


# ── Backward-compat shim tests ───────────────────────────────

class TestSlackUpdateShim:
    @patch("slackker.callbacks.lightning.SlackClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client._client = MagicMock()
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cb = SlackUpdate(
                token="xoxb-test", channel="C123", ModelName="M",
                TrackLogs=["train_loss"], monitor="train_loss",
            )
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    @patch("slackker.callbacks.lightning.SlackClient")
    def test_shim_preserves_old_attrs(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client._client = MagicMock()
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = SlackUpdate(
                token="xoxb-test", channel="C123", ModelName="M",
                TrackLogs=["train_loss", "val_loss"], monitor="val_loss",
                SendPlot=True, verbose=2,
            )

        assert cb.ModelName == "M"
        assert cb.TrackLogs == ["train_loss", "val_loss"]
        assert cb.SendPlot is True
        assert cb.verbose == 2

    def test_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = SlackUpdate(
                token=None, channel="C123", ModelName="M",
                TrackLogs=["train_loss"], monitor="train_loss",
            )
        assert not hasattr(cb, "client")


class TestTelegramUpdateShim:
    @patch("slackker.callbacks.lightning.TelegramClient")
    def test_init_deprecation_warning(self, mock_cls):
        mock_client = MockClient()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.chat_id = "99999"
        mock_cls.return_value = mock_client

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cb = TelegramUpdate(
                token="123:ABC", ModelName="M",
                TrackLogs=["train_loss"], monitor="train_loss",
            )
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_no_token(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cb = TelegramUpdate(
                token=None, ModelName="M",
                TrackLogs=["train_loss"], monitor="train_loss",
            )
        assert not hasattr(cb, "client")


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
    """Verify that LightningCallback calls connect() when the client is not yet connected."""

    def test_connects_when_not_connected(self):
        client = DisconnectedMockClient()
        assert not client.is_connected
        LightningCallback(
            client=client, model_name="M",
            track_logs=["train_loss"], monitor="train_loss",
        )
        assert client.connect_calls == 1
        assert client.is_connected

    def test_skips_connect_when_already_connected(self):
        client = MockClient()          # is_connected always True
        LightningCallback(
            client=client, model_name="M",
            track_logs=["train_loss"], monitor="train_loss",
        )
        assert client.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
