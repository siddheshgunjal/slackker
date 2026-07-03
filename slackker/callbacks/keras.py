from datetime import datetime

import numpy as np
from keras.callbacks import Callback

from slackker.core.client import BaseClient, _run_sync
from slackker.utils import network, plotting


class KerasCallback(Callback):
    """Unified Keras training callback that works with any client backend.

    Parameters
    ----------
    client : BaseClient
        The messaging platform client to send notifications through.
    model_name : str
        Human-readable name for the model (used in messages and plot titles).
    export : str
        Image format for training plots. Defaults to ``"png"``.
    send_plot : bool
        If ``True``, upload training-curve plots at the end of training.
        Defaults to ``False``.
    track_logs : dict[str, str] | None
        Mapping of attribute names to Keras ``logs`` dictionary keys.
        The values are appended to lists stored on the callback instance
        (e.g. ``self.train_loss``, ``self.val_acc``).

        Defaults to the standard Keras convention::

            {
                "train_loss":  "loss",
                "train_acc":   "accuracy",
                "valid_loss":  "val_loss",
                "valid_acc":   "val_accuracy",
            }

        Pass a custom mapping when your model uses non-standard metric
        names (e.g. ``{"train_loss": "loss", "train_auc": "auc"}``).
    monitor : str
        Attribute name (from *track_logs*) used to determine the best
        epoch.  Lower is better when the name contains ``"loss"``;
        otherwise higher is better.  Defaults to ``"valid_loss"``.
    """

    SUPPORTED_FORMATS = (
        "eps",
        "jpeg",
        "jpg",
        "pdf",
        "pgf",
        "png",
        "ps",
        "raw",
        "rgba",
        "svg",
        "svgz",
        "tif",
        "tiff",
    )

    _DEFAULT_TRACK_LOGS: dict[str, str] = {
        "train_loss": "loss",
        "train_acc": "accuracy",
        "valid_loss": "val_loss",
        "valid_acc": "val_accuracy",
    }

    def __init__(
        self,
        client: BaseClient,
        model_name: str,
        export: str = "png",
        send_plot: bool = False,
        track_logs: dict[str, str] | None = None,
        monitor: str = "valid_loss",
    ):
        super().__init__()
        if export not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported export format '{export}'. Supported: {self.SUPPORTED_FORMATS}"
            )

        self.track_logs = track_logs or dict(self._DEFAULT_TRACK_LOGS)
        self.monitor = monitor

        if monitor not in self.track_logs:
            raise ValueError(
                f"'monitor' value '{monitor}' not found in 'track_logs' keys. "
                f"Available keys: {list(self.track_logs)}"
            )

        self.client = client
        self.model_name = model_name
        self.export = export
        self.send_plot = send_plot

        if not client.is_connected:
            _run_sync(client.connect())

        # Metric lists — populated from logs using self.track_logs mapping
        self.train_acc: list[float] = []
        self.valid_acc: list[float] = []
        self.train_loss: list[float] = []
        self.valid_loss: list[float] = []
        self.n_epochs = 0

    def on_train_begin(self, logs=None):
        self.client.send_message_sync(
            f'Training on "{self.model_name}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        # Extract metrics by key name (not positional index).
        for attr_name, log_key in self.track_logs.items():
            if log_key in logs:
                metric_list: list[float] = getattr(self, attr_name, None)
                if metric_list is not None:
                    metric_list.append(float(logs[log_key]))

        message = f"Epoch: {self.n_epochs}"
        if self.train_loss:
            message += f", Training Loss: {self.train_loss[-1]:.4f}"
        if self.valid_loss:
            message += f", Validation Loss: {self.valid_loss[-1]:.4f}"

        connected = _run_sync(
            network.check_connection_quick(url=self.client.connectivity_url)
        )
        if connected:
            self.client.send_message_sync(message)

        self.n_epochs += 1

    def on_train_end(self, logs=None):
        monitor_values: list[float] = getattr(self, self.monitor, None) or []

        if monitor_values:
            # Lower is better for loss-like metrics, higher otherwise.
            if "loss" in self.monitor.lower():
                best_epoch = int(np.argmin(monitor_values))
            else:
                best_epoch = int(np.argmax(monitor_values))

            self.client.send_message_sync(
                f"Trained for {self.n_epochs} epochs. Best epoch was {best_epoch}."
            )

            # Build a detailed best-epoch summary from all tracked metrics.
            parts: list[str] = []
            for attr_name in self.track_logs:
                values: list[float] = getattr(self, attr_name, None) or []
                if len(values) > best_epoch:
                    val = values[best_epoch]
                    if "acc" in attr_name.lower():
                        parts.append(f"{attr_name} = {100 * val:.4f}%")
                    else:
                        parts.append(f"{attr_name} = {val:.4f}")
            if parts:
                self.client.send_message_sync(", ".join(parts))

        training_logs = {
            "train_loss": self.train_loss,
            "train_acc": self.train_acc,
            "val_loss": self.valid_loss,
            "val_acc": self.valid_acc,
        }

        if self.send_plot:
            paths = plotting.generate_and_get_plots(
                self.model_name, self.export, training_logs
            )
            for path in paths:
                self.client.upload_image_sync(path, comment=f"{self.model_name} 📎")
