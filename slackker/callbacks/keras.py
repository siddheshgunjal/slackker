from datetime import datetime
import argparse
import requests
import numpy as np
from keras.callbacks import Callback
from slack_sdk import WebClient
from slackker.utils import checkker
from slackker.utils import functions
from slackker.utils.ccolors import colors

class SlackUpdate(Callback):
    """Custom Keras callback that posts to Slack while training a neural network"""
    def __init__(self, token, channel, ModelName, export="png", SendPlot=False, verbose=0):

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

            if export is not None:
                pass
            else:
                raise argparse.ArgumentTypeError("[slackker] ERROR: 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

    # Called when training starts
    def on_train_begin(self, logs={}):
        functions.Slack.report_stats(
            client=self.client,
            channel=self.channel,
            text=f'Training on "{self.ModelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            verbose=self.verbose)

    # Called when epoch ends
    def on_epoch_end(self, batch, logs={}):

        custom_logs = []

        for i in logs:
            custom_logs.append(logs[i])

        self.train_loss.append(custom_logs[0])
        self.train_acc.append(custom_logs[1])
        self.valid_loss.append(custom_logs[2])
        self.valid_acc.append(custom_logs[3])

        message = f'Epoch: {self.n_epochs}, Training Loss: {self.train_loss[-1]:.4f}, Validation Loss: {self.valid_loss[-1]:.4f}'

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
    def on_train_end(self, logs={}):

        best_epoch = np.argmin(self.valid_loss)
        val_loss = self.valid_loss[best_epoch]
        train_loss = self.train_loss[best_epoch]
        train_acc = self.train_acc[best_epoch]
        val_acc = self.valid_acc[best_epoch]

        training_logs = {'train_loss': self.train_loss, 'train_acc': self.train_acc, 'val_loss': self.valid_loss, 'val_acc': self.valid_acc}

        message1 = f'Trained for {self.n_epochs} epochs. Best epoch was {best_epoch}.'
        message2 = f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"

        functions.Slack.report_stats(client=self.client, channel=self.channel, text=message1, verbose=self.verbose)

        functions.Slack.report_stats(client=self.client, channel=self.channel, text=message2, verbose=self.verbose)

        functions.Slack.keras_plot_history(ModelName=self.ModelName,
            export=self.export,
            client=self.client,
            channel=self.channel,
            SendPlot=self.SendPlot,
            training_logs=training_logs,
            verbose=self.verbose)

class TelegramUpdate(Callback):
    """Custom Keras callback that posts to Telegram while training a neural network"""
    def __init__(self, token, ModelName, export="png", SendPlot=False, verbose=0):

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

            if export is not None:
                pass
            else:
                raise argparse.ArgumentTypeError("[slackker] ERROR: 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

    # Called when training starts
    def on_train_begin(self, logs={}):
        functions.Telegram.report_stats(
            token=self.token,
            channel=self.channel,
            text=f'Training on "{self.ModelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            verbose=self.verbose)

    # Called when epoch ends
    def on_epoch_end(self, batch, logs={}):

        custom_logs = []

        for i in logs:
            custom_logs.append(logs[i])

        self.train_loss.append(custom_logs[0])
        self.train_acc.append(custom_logs[1])
        self.valid_loss.append(custom_logs[2])
        self.valid_acc.append(custom_logs[3])
        self.n_epochs += 1

        message = f'Epoch: {self.n_epochs}, Training Loss: {self.train_loss[-1]:.4f}, Validation Loss: {self.valid_loss[-1]:.4f}'

        # Check internet before sending update on slacj
        server = checkker.check_internet_epoch_end(url="www.telegram.org")

        # If internet working send message else skip sending message and continue training.
        if server:
            functions.Telegram.report_stats(
                token=self.token,
                channel=self.channel,
                text=message,
                verbose=self.verbose)
        else:
            pass

    # Prepare and send report with graphs at the end of training.
    def on_train_end(self, logs={}):

        best_epoch = np.argmin(self.valid_loss)
        val_loss = self.valid_loss[best_epoch]
        train_loss = self.train_loss[best_epoch]
        train_acc = self.train_acc[best_epoch]
        val_acc = self.valid_acc[best_epoch]

        training_logs = {'train_loss': self.train_loss, 'train_acc': self.train_acc, 'val_loss': self.valid_loss, 'val_acc': self.valid_acc}

        message1 = f'Trained for {self.n_epochs} epochs. Best epoch was {best_epoch}.'
        message2 = f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"

        functions.Telegram.report_stats(token=self.token, channel=self.channel, text=message1, verbose=self.verbose)

        functions.Telegram.report_stats(token=self.token, channel=self.channel, text=message2, verbose=self.verbose)

        functions.Telegram.keras_plot_history(ModelName=self.ModelName,
            export=self.export,
            token=self.token,
            channel=self.channel,
            SendPlot=self.SendPlot,
            training_logs=training_logs,
            verbose=self.verbose)