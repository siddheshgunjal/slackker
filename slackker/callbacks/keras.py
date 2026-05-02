import warnings
from datetime import datetime
import numpy as np
from keras.callbacks import Callback
from slackker.core.client import BaseClient, _run_sync
from slackker.utils.logger import log
from slackker.utils import network, plotting


class KerasCallback(Callback):
    """Unified Keras training callback that works with any client backend."""

    SUPPORTED_FORMATS = ("eps", "jpeg", "jpg", "pdf", "pgf", "png", "ps", "raw", "rgba", "svg", "svgz", "tif", "tiff")

    def __init__(self, client: BaseClient, model_name: str, export: str = "png", send_plot: bool = False):
        super().__init__()
        if export not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format '{export}'. Supported: {self.SUPPORTED_FORMATS}")

        self.client = client
        self.model_name = model_name
        self.export = export
        self.send_plot = send_plot

        if not client.is_connected:
            _run_sync(client.connect())

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

    def on_train_begin(self, logs=None):
        self.client.send_message_sync(
            f'Training on "{self.model_name}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )

    def on_epoch_end(self, batch, logs=None):
        logs = logs or {}
        log_values = list(logs.values())

        if len(log_values) >= 4:
            self.train_acc.append(log_values[0])
            self.train_loss.append(log_values[1])
            self.valid_acc.append(log_values[2])
            self.valid_loss.append(log_values[3])

        message = f"Epoch: {self.n_epochs}"
        if self.train_loss:
            message += f", Training Loss: {self.train_loss[-1]:.4f}"
        if self.valid_loss:
            message += f", Validation Loss: {self.valid_loss[-1]:.4f}"

        connected = _run_sync(
            network.check_connection_quick(url="www.slack.com" if self.client.platform == "slack" else "www.telegram.org")
        )
        if connected:
            self.client.send_message_sync(message)

        self.n_epochs += 1

    def on_train_end(self, logs=None):
        if self.valid_loss:
            best_epoch = int(np.argmin(self.valid_loss))
            val_loss = self.valid_loss[best_epoch]
            train_loss = self.train_loss[best_epoch]
            val_acc = self.valid_acc[best_epoch] if self.valid_acc else 0
            train_acc = self.train_acc[best_epoch] if self.train_acc else 0

            self.client.send_message_sync(
                f"Trained for {self.n_epochs} epochs. Best epoch was {best_epoch}."
            )
            self.client.send_message_sync(
                f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"
            )

        training_logs = {
            "train_loss": self.train_loss,
            "train_acc": self.train_acc,
            "val_loss": self.valid_loss,
            "val_acc": self.valid_acc,
        }

        if self.send_plot:
            paths = plotting.generate_and_get_plots(self.model_name, self.export, training_logs)
            for path in paths:
                self.client.upload_image_sync(path, comment=f"{self.model_name} 📎")


# ──────────────────────────────────────────────
# Backward-compatible shims (deprecated)
# ──────────────────────────────────────────────

from slackker.core.slack import SlackClient
from slackker.core.telegram import TelegramClient


class SlackUpdate(KerasCallback):
    """Deprecated: Use KerasCallback(SlackClient(...), ...) instead."""

    def __init__(self, token, channel, ModelName, export="png", SendPlot=False, verbose=0):
        warnings.warn(
            "SlackUpdate is deprecated. Use KerasCallback(SlackClient(token, channel), model_name) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if token is None:
            log.error("Please enter a valid Slack API Token.")
            return

        client = SlackClient(token=token, channel=channel, verbose=verbose)
        connected = _run_sync(client.connect())
        if not connected:
            log.error("Failed to connect to Slack.")
            return

        super().__init__(client=client, model_name=ModelName, export=export, send_plot=SendPlot)

        # Expose old attribute names for backward compat
        self.ModelName = ModelName
        self.SendPlot = SendPlot
        self.verbose = verbose
        self._sdk_client = client._client
        self.channel = channel


class TelegramUpdate(KerasCallback):
    """Deprecated: Use KerasCallback(TelegramClient(...), ...) instead."""

    def __init__(self, token, ModelName, export="png", SendPlot=False, verbose=0):
        warnings.warn(
            "TelegramUpdate is deprecated. Use KerasCallback(TelegramClient(token), model_name) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if token is None:
            log.error("Please enter a valid Telegram API Token.")
            return

        client = TelegramClient(token=token, verbose=verbose)
        connected = _run_sync(client.connect())
        if not connected:
            log.error("Failed to connect to Telegram.")
            return

        super().__init__(client=client, model_name=ModelName, export=export, send_plot=SendPlot)

        # Expose old attribute names for backward compat
        self.ModelName = ModelName
        self.SendPlot = SendPlot
        self.verbose = verbose
        self.token = token
        self.channel = client.chat_id