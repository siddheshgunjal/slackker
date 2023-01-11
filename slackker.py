from keras.callbacks import Callback, History
import logging
import numpy as np
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime


client = WebClient(token="xoxb-4615231545733-4603743143687-P0ngiBAuMsp512V5DafGBajT")
channel_id = "C04JAK77KHQ"


def report_stats(text, channel):
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

def keras_plot_history(history, modelName):
    loss_list = [s for s in history.history.keys() if 'loss' in s and 'val' not in s]
    val_loss_list = [s for s in history.history.keys() if 'loss' in s and 'val' in s]
    acc_list = [s for s in history.history.keys() if 'acc' in s and 'val' not in s]
    val_acc_list = [s for s in history.history.keys() if 'acc' in s and 'val' in s]
    
    try:
        ## As loss always exists
        epochs = range(1,len(history.history[loss_list[0]]) + 1)
        
        ## Loss
        plt.figure(1, figsize=(15,8))
        for l in loss_list:
            plt.plot(epochs, history.history[l], 'b-', lw = 2.5, label='Training loss (' + str(str(format(history.history[l][-1],'.4f'))+')'))
        for l in val_loss_list:
            plt.plot(epochs, history.history[l], 'g-', lw = 2.5, label='Validation loss (' + str(str(format(history.history[l][-1],'.4f'))+')'))
        
        plt.title(f'{modelName} Loss Graph', fontsize=20)
        plt.xlabel('Epochs', fontsize=15)
        plt.ylabel('Loss', fontsize=15)
        plt.legend(fontsize=12)
        plt.grid(True)
        plt.savefig('Loss.svg')
        
        ## Accuracy
        plt.figure(2, figsize=(15,8))
        for l in acc_list:
            plt.plot(epochs, history.history[l], 'b-', lw=3.0, label='Training accuracy (' + str(format(history.history[l][-1],'.4f'))+')')
        for l in val_acc_list:    
            plt.plot(epochs, history.history[l], 'g-', lw=3.0, label='Validation accuracy (' + str(format(history.history[l][-1],'.4f'))+')')

        plt.title(f'{modelName} Accuracy Graph', fontsize=20)
        plt.xlabel('Epochs', fontsize=15)
        plt.ylabel('Accuracy', fontsize=15)
        plt.legend(fontsize=12)
        plt.grid(True)
        plt.savefig('accuracy.svg')

    except Exception as e:
        print(e)
        pass

class SLKerasUpdate(Callback):
    """Custom Keras callback that posts to Slack while training a neural network"""

    def __init__(self, modelName):
        self.channel = channel_id
        # self.history = {}
        self.modelName = modelName

    def on_train_begin(self, logs={}):
        report_stats(text=f'Training on {self.modelName} started at {datetime.now()}',
                     channel=self.channel)

        self.train_acc = []
        self.valid_acc = []
        self.train_loss = []
        self.valid_loss = []
        self.n_epochs = 0

    def on_epoch_end(self, batch, logs={}):

        self.train_acc.append(logs.get('accuracy'))
        self.valid_acc.append(logs.get('val_accuracy'))
        self.train_loss.append(logs.get('loss'))
        self.valid_loss.append(logs.get('val_loss'))
        self.n_epochs += 1

        message = f'Epoch: {self.n_epochs}, Training Loss: {self.train_loss[-1]:.4f}, Validation Loss: {self.valid_loss[-1]:.4f}'

        report_stats(message, channel=self.channel)

    def on_train_end(self, logs={}):

        best_epoch = np.argmin(self.valid_loss)
        val_loss = self.valid_loss[best_epoch]
        train_loss = self.train_loss[best_epoch]
        train_acc = self.train_acc[best_epoch]
        val_acc = self.valid_acc[best_epoch]

        message = f'Trained for {self.n_epochs} epochs. Best epoch was {best_epoch + 1}.'
        report_stats(message, channel=self.channel)
        message = f"Best validation loss = {val_loss:.4f}, Training Loss = {train_loss:.4f}, Best Accuracy = {100*val_acc:.4f}%"
        report_stats(message, channel=self.channel)

        print(len(self.valid_loss))
        # keras_plot_history(history=self.model, modelName=self.modelName)
