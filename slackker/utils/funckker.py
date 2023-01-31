import numpy as np
import matplotlib.pyplot as plt
from slack_sdk.errors import SlackApiError
from slackker.utils.ccolors import colors

def report_stats(client, channel, text, verbose=1):
    """Report training stats"""
    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=channel, 
            text=text
        )
        if verbose>=1:
            colors.prCyan(f"[slackker] Posted message on {channel} channel")

    except SlackApiError as e:
        colors.prRed(f"[slackker] Error posting message: {e}")
        pass

def upload_plot(name, client, channel, filepath, verbose=1):
    """Report training stats"""
    try:
        # Call the chat.postMessage method using the WebClient
        response = client.files_upload_v2(channel=channel,
        file = filepath,
        initial_comment=f"{name} graph ::bar_chart::"
        )
        if verbose>=1:
            colors.prCyan(f"[slackker] Uploaded graphs on {channel} channel")

    except SlackApiError as e:
        colors.prRed(f"[slackker] Error uploading graphs: {e}")
        pass

def keras_plot_history(modelName, export, client, channel, sendPlot, train_loss, val_loss, train_acc, val_acc, verbose=1):
    """Create Plot for train history"""
    try:
        # Make sure training has began
        if len(train_loss) == 0:
            colors.prRed('[slackker] Loss is missing in history')
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
                upload_plot(name = f'{modelName}_Loss', client=client, channel=channel, filepath=f'{modelName}_Loss.{export}', verbose=verbose)
            except Exception as e:
                colors.prRed(f"[slackker] Invalid Argument: {e}")
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
                upload_plot(name = f'{modelName}_Accuracy', client=client, channel=channel, filepath=f'{modelName}_Accuracy.{export}', verbose=verbose)
            except Exception as e:
                colors.prRed(f"[slackker] Invalid Argument: {e}")
        else:
            pass

    except Exception as e:
        colors.prRed(f'[slackker] Plotting Generation Failed: {e}')
        pass
