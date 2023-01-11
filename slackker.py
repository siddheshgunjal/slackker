from keras.callbacks import Callback, History
import logging
import numpy as np
import matplotlib.pyplot as plt
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import argparse


def report_stats(client, channel, text):
    """Report training stats"""
    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=channel, 
            text=text
        )
        print(f"Posted message on {channel} channel")

    except SlackApiError as e:
        print(f"Error posting message: {e}")
        pass

def upload_plot(name, client, channel, filepath):
    """Report training stats"""
    try:
        # Call the chat.postMessage method using the WebClient
        response = client.files_upload_v2(channel=channel,
        file = filepath,
        initial_comment=f"{name} graph ::bar_chart::"
        )
        print(f"Uploaded graphs on {channel} channel")

    except SlackApiError as e:
        print(f"Error uploading graphs: {e}")
        pass

def keras_plot_history(modelName, export, client, channel, sendPlot, train_loss, val_loss, train_acc, val_acc):
    """Create Plot for train history"""
    try:
        # Make sure training has began
        if len(train_loss) == 0:
            print('Loss is missing in history')
            return 
        
        # As loss always exists
        epochs = range(1, len(train_loss)+1)
        
        # Loss
        plt.figure(1, figsize=(15,8))
        plt.plot(epochs, train_loss,'b-', lw=2.5, label=f'Training Loss: {train_loss[-1]:.4f}')
        plt.plot(epochs, val_loss,'g-',lw=2.5, label=f'Validation Loss: {val_loss[-1]:.4f}')
        plt.title(f'{modelName} Loss Graph', fontsize=20)
        plt.xlabel('Epochs', fontsize=15)
        plt.ylabel('Loss', fontsize=15)
        plt.legend(fontsize=12)
        plt.grid(True)
        plt.savefig(f'{modelName}_Loss.{export}')
        plt.close()

        if sendPlot == True:
            try:
                upload_plot(name = f'{modelName}_Loss', client=client, channel=channel, filepath=f'{modelName}_Loss.{export}')
            except Exception as e:
                print(f"Invalid Argument: {e}")
        else:
            pass
        
        # Accuracy
        plt.figure(2, figsize=(15,8))
        plt.plot(epochs, train_acc,'b-',lw=2.5, label=f'Training Accuracy: {train_acc[-1]:.4f}')
        plt.plot(epochs, val_acc,'g-',lw=2.5, label=f'Validation Accuracy: {val_acc[-1]:.4f}')
        plt.title(f'{modelName} Accuracy Graph', fontsize=20)
        plt.xlabel('Epochs', fontsize=15)
        plt.ylabel('Accuracy', fontsize=15)
        plt.legend(fontsize=12)
        plt.grid(True)
        plt.savefig(f'{modelName}_Accuracy.{export}')
        plt.close()

        if sendPlot == True:
            try:
                upload_plot(name = f'{modelName}_Loss', client=client, channel=channel, filepath=f'{modelName}_Loss.{export}')
            except Exception as e:
                print(f"Invalid Argument: {e}")
        else:
            pass

    except Exception as e:
        print(f'Plotting Generation Failed: {e}')
        pass

class SLKerasUpdate(Callback):
    """Custom Keras callback that posts to Slack while training a neural network"""

    def __init__(self, token, channel, modelName, export=None, sendPlot=True):
        self.client = WebClient(token=token)
        self.channel = channel
        self.modelName = modelName
        self.export = export
        self.sendPlot = sendPlot

        if export is not None:
            pass
        else:
            raise argparse.ArgumentTypeError("'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

    def on_train_begin(self, logs={}):
        report_stats(
            client=self.client,
            channel=self.channel,
            text=f'Training on {self.modelName} started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

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

        report_stats(
            client=self.client,
            channel=self.channel,
            text=message)

    def on_train_end(self, logs={}):

        best_epoch = np.argmin(self.valid_loss)
        val_loss = self.valid_loss[best_epoch]
        train_loss = self.train_loss[best_epoch]
        train_acc = self.train_acc[best_epoch]
        val_acc = self.valid_acc[best_epoch]

        message = f'Trained for {self.n_epochs} epochs. Best epoch was {best_epoch + 1}.'
        report_stats(
            client=self.client,
            channel=self.channel,
            text=message)
        message = f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"
        report_stats(
            client=self.client,
            channel=self.channel,
            text=message)
        keras_plot_history(modelName=self.modelName,
            export=self.export,
            client=self.client,
            channel=self.channel,
            sendPlot = self.sendPlot,
            train_loss=self.train_loss,
            val_loss=self.valid_loss,
            train_acc=self.train_acc,
            val_acc=self.valid_acc)
