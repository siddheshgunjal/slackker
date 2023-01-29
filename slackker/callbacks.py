import numpy as np
from keras.callbacks import Callback
from slack_sdk import WebClient
from datetime import datetime
import argparse
import slackker.utils.checkker as checkker
import slackker.utils.funckker as funckker
from slackker.utils.ccolors import colors

class SLKerasUpdate(Callback):
    """Custom Keras callback that posts to Slack while training a neural network"""
    def __init__(self, token, channel, modelName, export="png", sendPlot=True, verbose=0):

        if token is None:
            colors.prRed('[slackker] Please enter Valid Slack API Token.')
            return

        server= checkker.check_internet(verbose=verbose)
        api = checkker.slack_connect(token=token, verbose=verbose)

        if server and api:
            self.client = WebClient(token=token)
            self.channel = channel
            self.modelName = modelName
            self.export = export
            self.sendPlot = sendPlot
            self.verbose = verbose

            if export is not None:
                pass
            else:
                raise argparse.ArgumentTypeError("[slackker] 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

    # Called when training starts
    def on_train_begin(self, logs={}):
        funckker.report_stats(
            client=self.client,
            channel=self.channel,
            text=f'Training on {self.modelName} started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            verbose=self.verbose)

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

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
        server, attempt = checkker.check_internet_epoch_end()

        # If internet working send message else skip sending message and continue training.
        if server == True:
            funckker.report_stats(
                client=self.client,
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

        message1 = f'Trained for {self.n_epochs} epochs. Best epoch was {best_epoch + 1}.'
        message2 = f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"

        funckker.report_stats(client=self.client, channel=self.channel, text=message1, verbose=self.verbose)

        funckker.report_stats(client=self.client, channel=self.channel, text=message2, verbose=self.verbose)

        funckker.keras_plot_history(modelName=self.modelName,
            export=self.export,
            client=self.client,
            channel=self.channel,
            sendPlot = self.sendPlot,
            train_loss=self.train_loss,
            val_loss=self.valid_loss,
            train_acc=self.train_acc,
            val_acc=self.valid_acc,
            verbose=self.verbose)
