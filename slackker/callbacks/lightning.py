from datetime import datetime

import numpy as np
from lightning.pytorch.callbacks import Callback

from slackker.core.client import BaseClient, _run_sync
from slackker.utils import network, plotting
from slackker.utils.logger import log


class LightningCallback(Callback):
    """Unified Lightning training callback that works with any client backend."""

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

    def __init__(
        self,
        client: BaseClient,
        model_name: str,
        track_logs: list[str] | None = None,
        monitor: str | None = None,
        export: str = "png",
        send_plot: bool = False,
    ):
        super().__init__()
        if export not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported export format '{export}'. Supported: {self.SUPPORTED_FORMATS}"
            )

        if track_logs is None:
            raise ValueError("Provide at least 1 log type for sending update.")
        if not isinstance(track_logs, list):
            raise ValueError(
                "'track_logs' must be a list, e.g. ['train_loss', 'val_loss']"
            )

        if monitor is not None and monitor not in track_logs:
            raise ValueError(f"'monitor' value '{monitor}' not found in 'track_logs'")
        elif monitor is None:
            log.warning("'monitor' not provided, will skip reporting Best Epoch")

        self.client = client
        self.model_name = model_name
        self.track_logs = track_logs
        self.monitor = monitor
        self.export = export
        self.send_plot = send_plot

        if not client.is_connected:
            _run_sync(client.connect())

        self.training_logs: dict[str, list[float]] = {}
        self.n_epochs = 0

    def on_fit_start(self, trainer, pl_module):
        self.client.send_message_sync(
            f'Training on "{self.model_name}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )

    def on_train_epoch_end(self, trainer, pl_module):
        metrics = trainer.callback_metrics

        for key in self.track_logs:
            val = float(metrics[key])
            self.training_logs.setdefault(key, []).append(val)

        parts = [f"{key}: {metrics[key]:.4f}" for key in self.track_logs]
        message = f"Epoch: {self.n_epochs}, {', '.join(parts)}"

        connected = _run_sync(
            network.check_connection_quick(url=self.client.connectivity_url)
        )
        if connected:
            self.client.send_message_sync(message)

        self.n_epochs += 1

    def on_fit_end(self, trainer, pl_module):
        if self.monitor is not None:
            for key, values in self.training_logs.items():
                if self.monitor.lower() in key.lower():
                    if "loss" in self.monitor.lower():
                        best = int(np.argmin(values))
                    else:
                        best = int(np.argmax(values))
                    message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {best}"
                    break
            else:
                message = f"Trained for {self.n_epochs} epochs."
        else:
            message = f"Trained for {self.n_epochs} epochs. 'monitor' was not provided, skipped reporting Best Epoch"

        self.client.send_message_sync(message)

        if self.send_plot:
            paths = plotting.generate_and_get_plots(
                self.model_name, self.export, self.training_logs
            )
            for path in paths:
                self.client.upload_image_sync(path, comment=f"{self.model_name} 📎")
