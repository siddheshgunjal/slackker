import requests
import numpy as np
import matplotlib.pyplot as plt
from slack_sdk.errors import SlackApiError
from slackker.utils.ccolors import colors

class slack():
    def report_stats(client, channel, text, verbose=1):
        """Report training stats"""
        try:
            # Call the chat.postMessage method using the WebClient
            result = client.chat_postMessage(
                channel=channel, 
                text=text
            )
            if verbose>=1:
                colors.prCyan(f"[slackker] Posted update on {channel} channel")

        except SlackApiError as e:
            colors.prRed(f"[slackker] Error posting update: {e}")

    def upload_plot(name, client, channel, filepath, verbose=1):
        """Upload generated graphs"""
        try:
            # Call the chat.postMessage method using the WebClient
            response = client.files_upload_v2(channel=channel,
            file = filepath,
            initial_comment=f"{name} :bar_chart:"
            )
            if verbose>=1:
                colors.prCyan(f"[slackker] Uploaded graph on {channel} channel")

        except SlackApiError as e:
            colors.prRed(f"[slackker] Error uploading graph: {e}")

    def keras_plot_history(ModelName, export, client, channel, SendPlot, train_loss, val_loss, train_acc, val_acc, verbose=1):
        """Create Plot for train history"""
        try:
            # Make sure training has began
            if len(train_loss) == 0:
                colors.prRed('[slackker] Loss is missing from training history')
                return 
            
            # As loss always exists
            epochs = range(0, len(train_loss))
            
            # Loss
            plt.figure(1, figsize=(15,8))
            plt.plot(epochs, train_loss,'b-', lw=2.5, label=f'Training Loss: {train_loss[-1]:.4f}')
            plt.plot(epochs, val_loss,'g-',lw=2.5, label=f'Validation Loss: {val_loss[-1]:.4f}')
            plt.title(f'{ModelName} Loss Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Loss', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Loss.{export}')
            plt.close()

            if SendPlot:
                try:
                    slack.upload_plot(name = f'{ModelName} Loss', client=client, channel=channel, filepath=f'{ModelName}_Loss.{export}', verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass
            
            # Accuracy
            plt.figure(2, figsize=(15,8))
            plt.plot(epochs, train_acc,'b-',lw=2.5, label=f'Training Accuracy: {train_acc[-1]:.4f}')
            plt.plot(epochs, val_acc,'g-',lw=2.5, label=f'Validation Accuracy: {val_acc[-1]:.4f}')
            plt.title(f'{ModelName} Accuracy Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Accuracy', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Accuracy.{export}')
            plt.close()

            if SendPlot:
                try:
                    slack.upload_plot(name = f'{ModelName} Accuracy', client=client, channel=channel, filepath=f'{ModelName}_Accuracy.{export}', verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

        except Exception as e:
            colors.prRed(f'[slackker] Plotting Generation Failed: {e}')
            pass

    def lightning_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose=1):
        try:
            # Make sure training has began
            if len(training_logs) == 0:
                colors.prRed('[slackker] Loss is missing from training history')
                return

            # As loss always exists
            k = str(list(training_logs.keys())[0])
            epochs = range(0, len(training_logs[k]))

            # colors list for loss graph
            clrs_loss = iter(['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia'])

            # Loss
            plt.figure(1, figsize=(15,8))

            for key, value in training_logs.items():
                if 'loss' in key.lower():
                    plt.plot(epochs, training_logs[key], next(clrs_loss), lw=2.5, label=f'{key}: {training_logs[key][-1]:.4f}')
                else:
                    pass
            plt.title(f'{ModelName} Loss Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Loss', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Loss.{export}')
            plt.close()

            if SendPlot == True:
                try:
                    slack.upload_plot(name = f'{ModelName} Loss', client=client, channel=channel, filepath=f'{ModelName}_Loss.{export}', verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

            # Accuracy
            plt.figure(1, figsize=(15,8))

            # colors list for accuracy graph
            clrs_acc = iter(['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia'])

            for key, value in training_logs.items():
                if 'acc' in key.lower():
                    plt.plot(epochs, training_logs[key], next(clrs_acc), lw=2.5, label=f'{key}: {training_logs[key][-1]:.4f}')
                else:
                    pass
            plt.title(f'{ModelName} Accuracy Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Accuracy', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Accuracy.{export}')
            plt.close()

            if SendPlot:
                try:
                    slack.upload_plot(name = f'{ModelName} Accuracy', client=client, channel=channel, filepath=f'{ModelName}_Accuracy.{export}', verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

        except Exception as e:
            colors.prRed(f'[slackker] Plotting Generation Failed: {e}')

class telegram():
    def report_stats(token, channel, text, verbose=1):
        # apiURL for send message
        apiURL = f'https://api.telegram.org/bot{token}/sendMessage'

        """Report training stats"""
        try:
            # Call the requests.post method using API request
            response = requests.post(apiURL, params={'chat_id': channel, 'text': text})
            if verbose>=1:
                colors.prCyan("[slackker] Posted update on Telegram")

        except Exception as e:
            colors.prRed(f"[slackker] Error posting update: {e}")

    def upload_plot(name, token, channel, image, verbose=1):
        # apiURL for send image
        apiURL = f'https://api.telegram.org/bot{token}/sendPhoto'

        """Upload generated graphs"""
        try:
            # Call the requests.post method using API request
            response = requests.post(apiURL, params={'chat_id': channel, 'caption': f"{name} \U0001F4CA"}, files={'photo': image})
            if verbose>=1:
                colors.prCyan("[slackker] Uploaded graph on Telegram")

        except Exception as e:
            colors.prRed(f"[slackker] Error uploading graph: {e}")

    def keras_plot_history(ModelName, export, token, channel, SendPlot, train_loss, val_loss, train_acc, val_acc, verbose=1):
        """Create Plot for train history"""
        try:
            # Make sure training has began
            if len(train_loss) == 0:
                colors.prRed('[slackker] Loss is missing from training history')
                return 
            
            # As loss always exists
            epochs = range(0, len(train_loss))
            
            # Loss
            plt.figure(1, figsize=(15,8))
            plt.plot(epochs, train_loss,'b-', lw=2.5, label=f'Training Loss: {train_loss[-1]:.4f}')
            plt.plot(epochs, val_loss,'g-',lw=2.5, label=f'Validation Loss: {val_loss[-1]:.4f}')
            plt.title(f'{ModelName} Loss Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Loss', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Loss.{export}')
            plt.close()

            if SendPlot:
                try:
                    telegram.upload_plot(name=f'{ModelName} Loss', token=token, channel=channel, image=open(f'{ModelName}_Loss.{export}', 'rb'), verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass
            
            # Accuracy
            plt.figure(2, figsize=(15,8))
            plt.plot(epochs, train_acc,'b-',lw=2.5, label=f'Training Accuracy: {train_acc[-1]:.4f}')
            plt.plot(epochs, val_acc,'g-',lw=2.5, label=f'Validation Accuracy: {val_acc[-1]:.4f}')
            plt.title(f'{ModelName} Accuracy Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Accuracy', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Accuracy.{export}')
            plt.close()

            if SendPlot:
                try:
                    telegram.upload_plot(name=f'{ModelName} Accuracy', token=token, channel=channel, image=open(f'{ModelName}_Accuracy.{export}', 'rb'), verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

        except Exception as e:
            colors.prRed(f'[slackker] Plotting Generation Failed: {e}')

    def lightning_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose=1):
        try:
            # Make sure training has began
            if len(training_logs) == 0:
                colors.prRed('[slackker] Loss is missing from training history')
                return

            # As loss always exists
            k = str(list(training_logs.keys())[0])
            epochs = range(0, len(training_logs[k]))

            # colors list for loss graph
            clrs_loss = iter(['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia'])

            # Loss
            plt.figure(1, figsize=(15,8))

            for key, value in training_logs.items():
                if 'loss' in key.lower():
                    plt.plot(epochs, training_logs[key], next(clrs_loss), lw=2.5, label=f'{key}: {training_logs[key][-1]:.4f}')
                else:
                    pass
            plt.title(f'{ModelName} Loss Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Loss', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Loss.{export}')
            plt.close()

            if SendPlot:
                try:
                    telegram.upload_plot(name = f'{ModelName} Loss', token=token, channel=channel, image=open(f'{ModelName}_Loss.{export}', 'rb'), verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

            # Accuracy
            plt.figure(1, figsize=(15,8))

            # colors list for accuracy graph
            clrs_acc = iter(['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia'])

            for key, value in training_logs.items():
                if 'acc' in key.lower():
                    plt.plot(epochs, training_logs[key], next(clrs_acc), lw=2.5, label=f'{key}: {training_logs[key][-1]:.4f}')
                else:
                    pass
            plt.title(f'{ModelName} Accuracy Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel('Accuracy', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(f'{ModelName}_Accuracy.{export}')
            plt.close()

            if SendPlot:
                try:
                    telegram.upload_plot(name = f'{ModelName} Accuracy', token=token, channel=channel, image=open(f'{ModelName}_Accuracy.{export}', 'rb'), verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] Invalid Argument: {e}")
            else:
                pass

        except Exception as e:
            colors.prRed(f'[slackker] Plotting Generation Failed: {e}')