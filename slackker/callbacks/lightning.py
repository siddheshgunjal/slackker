import sys
from datetime import datetime
import argparse
import requests
import numpy as np
from lightning.pytorch.callbacks import Callback
from slack_sdk import WebClient
from slackker.utils import checkker
from slackker.utils import functions
from slackker.utils.ccolors import colors

class SlackUpdate(Callback):
    """Custom Lightning callback that posts to Slack while training a neural network"""
    def __init__(self, token, channel, ModelName, TrackLogs=None, monitor=None, export="png", SendPlot=False, verbose=0):
        if token is None:
            colors.prRed('[slackker] ERROR: Please enter Valid Slack API Token.')
            return

        server = checkker.check_internet(url="www.slack.com", verbose=verbose)
        api = checkker.slack_connect(token=token, verbose=verbose)

        if server and api:
            self.client = WebClient(token=token)
            self.channel = channel
            self.ModelName = ModelName
            self.export = export
            self.SendPlot = SendPlot
            self.verbose = verbose
            self.TrackLogs = TrackLogs
            self.monitor = monitor

            if export is not None:
                pass
            else:
                raise argparse.ArgumentTypeError("[slackker] ERROR: 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

            if TrackLogs is None:
                colors.prRed("[slackker] ERROR: Provice at least 1 log type for sending update.")
                sys.exit()
            else:
                if type(TrackLogs) is not list and TrackLogs is not None:
                    colors.prRed("[slackker] ERROR: 'TrackLogs' is a list type of argument, add values in '[]'")
                    sys.exit()
                else:
                    pass

            if monitor is not None:
                if monitor not in TrackLogs:
                    colors.prRed("[slackker] ERROR: Couldn't find Argument 'monitor' value in 'TrackLogs' provided")
                    sys.exit()
                else:
                    pass
            else:
                colors.prYellow("[slackker] WARNING: Argument 'monitor' not provided, will skip reporting Best Epoch")

        self.training_logs = {}
        self.n_epochs = 0

    # Called when training starts
    def on_fit_start(self, trainer, pl_module):
        functions.Slack.report_stats(
            client=self.client,
            channel=self.channel,
            text=f'Training on "{self.ModelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            verbose=self.verbose)

    # Called when every training epoch ends
    def on_train_epoch_end(self, trainer, pl_module):
        metrics = trainer.callback_metrics
        logs = self.TrackLogs

        custom_logs = {}
        toPrint = []

        [custom_logs.update({i:float(metrics[i])}) for i in logs]

        [self.training_logs.setdefault(key, []).append(value) for key, value in custom_logs.items()]

        [toPrint.append(f"{i}: {metrics[i]:.4f}") for i in logs]

        message = f"Epoch: {self.n_epochs}, {', '.join(toPrint)}"

        # Check internet before sending update on slacj
        server = checkker.check_internet_epoch_end(url="www.slack.com")

        # If internet working send message else skip sending message and continue training.
        if server:
            functions.Slack.report_stats(
                client=self.client,
                channel=self.channel,
                text=message,
                verbose=self.verbose)
        else:
            pass

        self.n_epochs += 1

    # Prepare and send report with graphs at the end of training.
    def on_fit_end(self, trainer, pl_module):
        if self.monitor is not None:
            for key, value in self.training_logs.items():
                if "loss" in self.monitor.lower():
                    if self.monitor.lower() in key.lower():
                        # print(f"Lowest loss value is {min(value)}")
                        message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmin(value)}"
                elif "acc" in self.monitor.lower():
                    if self.monitor.lower() in key.lower():
                        # print(f"Highest accuracy value is{max(value)}")
                        message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmax(value)}"
        else:
            message = f"Trained for {self.n_epochs} epochs. Argument 'monitor' was not provided, skipped reporting Best Epoch"

        functions.Slack.report_stats(
            client=self.client,
            channel=self.channel,
            text=message,
            verbose=self.verbose)

        functions.Slack.lightning_plot_history(ModelName=self.ModelName,
            export=self.export,
            client=self.client,
            channel=self.channel,
            SendPlot=self.SendPlot,
            training_logs=self.training_logs,
            verbose=self.verbose)

class TelegramUpdate(Callback):
    """Custom Lightning callback that posts to Telegram while training a neural network"""
    def __init__(self, token, ModelName, TrackLogs=None, monitor=None, export="png", SendPlot=False, verbose=0):
        if token is None:
            colors.prRed('[slackker] ERROR: Please enter Valid Telegram API Token.')
            return

        server = checkker.check_internet(url="www.telegram.org", verbose=verbose)
        channel = checkker.get_telegram_chat_id(token=token, verbose=verbose)

        if server and channel:
            self.token = token
            self.channel = channel
            self.ModelName = ModelName
            self.export = export
            self.SendPlot = SendPlot
            self.verbose = verbose
            self.TrackLogs = TrackLogs
            self.monitor = monitor

            if export is not None:
                pass
            else:
                raise argparse.ArgumentTypeError("[slackker] ERROR: 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

            if TrackLogs is None:
                colors.prRed("[slackker] ERROR: Provice at least 1 log type for sending update.")
                sys.exit()
            else:
                if type(TrackLogs) is not list and TrackLogs is not None:
                    colors.prRed("[slackker] ERROR: 'TrackLogs' is a list type of argument, add values in '[]'")
                    sys.exit()
                else:
                    pass

            if monitor is not None:
                if monitor not in TrackLogs:
                    colors.prRed("[slackker] ERROR: Couldn't find Argument 'monitor' value in 'TrackLogs' provided")
                    sys.exit()
                else:
                    pass
            else:
                colors.prYellow("[slackker] WARNING: Argument 'monitor' not provided, will skip reporting Best Epoch")

        self.training_logs = {}
        self.n_epochs = 0

    # Called when training starts
    def on_fit_start(self, trainer, pl_module):
        functions.Telegram.report_stats(
            token=self.token,
            channel=self.channel,
            text=f'Training on "{self.ModelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            verbose=self.verbose)

    # Called when every training epoch ends
    def on_train_epoch_end(self, trainer, pl_module):
        metrics = trainer.callback_metrics
        logs = self.TrackLogs

        custom_logs = {}
        toPrint = []

        [custom_logs.update({i:float(metrics[i])}) for i in logs]

        [self.training_logs.setdefault(key, []).append(value) for key, value in custom_logs.items()]

        [toPrint.append(f"{i}: {metrics[i]:.4f}") for i in logs]

        message = f"Epoch: {self.n_epochs}, {', '.join(toPrint)}"

        # Check internet before sending update on slacj
        server = checkker.check_internet_epoch_end(url="www.slack.com")

        # If internet working send message else skip sending message and continue training.
        if server:
            functions.Telegram.report_stats(
                token=self.token,
                channel=self.channel,
                text=message,
                verbose=self.verbose)
        else:
            pass

        self.n_epochs += 1

    # Prepare and send report with graphs at the end of training.
    def on_fit_end(self, trainer, pl_module):
        if self.monitor is not None:
            for key, value in self.training_logs.items():
                if "loss" in self.monitor.lower():
                    if self.monitor.lower() in key.lower():
                        # print(f"Lowest loss value is {min(value)}")
                        message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmin(value)}"
                elif "acc" in self.monitor.lower():
                    if self.monitor.lower() in key.lower():
                        # print(f"Highest accuracy value is{max(value)}")
                        message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmax(value)}"
        else:
            message = f"Trained for {self.n_epochs} epochs. Argument 'monitor' was not provided, skipped reporting Best Epoch"

        functions.Telegram.report_stats(
            token=self.token,
            channel=self.channel,
            text=message,
            verbose=self.verbose)

        functions.Telegram.lightning_plot_history(ModelName=self.ModelName,
            export=self.export,
            token=self.token,
            channel=self.channel,
            SendPlot=self.SendPlot,
            training_logs=self.training_logs,
            verbose=self.verbose)