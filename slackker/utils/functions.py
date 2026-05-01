import requests
import itertools
import os
import matplotlib.pyplot as plt
from slack_sdk.errors import SlackApiError
from slackker.utils.ccolors import colors

class Plotter:
    @staticmethod
    def slack_file_upload(name, client, channel, filepath, initial_comment=None, verbose=1):
        """Upload generated attachments"""
        try:
            comment = initial_comment if initial_comment is not None else f"{name} :paperclip:"
            # Call the chat.postMessage method using the WebClient
            response = client.files_upload_v2(channel=channel,
            file = filepath,
            initial_comment=comment)
            if verbose>=1:
                colors.prCyan(f"[slackker] DEBUG: Uploaded attachment on {channel} channel")

        except SlackApiError as e:
            colors.prRed(f"[slackker] ERROR: Error uploading attachment: {e}")
    
    @staticmethod
    def telegram_img_upload(name, token, channel, image, verbose=1):
        # apiURL for send image
        apiURL = f'https://api.telegram.org/bot{token}/sendPhoto'

        try:
            # Call the requests.post method using API request
            response = requests.post(apiURL, params={'chat_id': channel, 'caption': f"{name} \U0001F4CE"}, files={'photo': image})
            if verbose>=1:
                colors.prCyan("[slackker] DEBUG: Uploaded attachment on Telegram")

        except Exception as e:
            colors.prRed(f"[slackker] ERROR: Error uploading attachment: {e}")
    
    @staticmethod
    def telegram_file_upload(name, token, channel, file, caption=None, verbose=1):
        # apiURL for send file
        apiURL = f'https://api.telegram.org/bot{token}/sendDocument'

        try:
            tg_caption = caption if caption is not None else f"{name} \U0001F4CE"
            # Call the requests.post method using API request
            response = requests.post(apiURL, params={'chat_id': channel, 'caption': tg_caption}, files={'document': file})
            if verbose>=1:
                colors.prCyan("[slackker] DEBUG: Uploaded attachment on Telegram")

        except Exception as e:
            colors.prRed(f"[slackker] ERROR: Error uploading attachment: {e}")

    @staticmethod
    def plot_and_upload(platform, ModelName, export, client, channel, SendPlot, logs, metric, verbose=1):
        try:
            # Make sure training has began
            if len(logs) == 0:
                colors.prRed('[slackker] ERROR: Loss is missing from training history')
                return

            # As loss always exists
            k = str(list(logs.keys())[0])
            epochs = range(0, len(logs[k]))

            # color choices list
            clrs = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia']

            # seperate color iterator for loss and acc graphs
            ls, acc = itertools.tee(clrs, 2) # create as many as needed

            path = f'{ModelName}_{metric}.{export}'

            # Plotting
            plt.figure(1, figsize=(15,8))

            for key, value in logs.items():
                if metric in key.lower():
                    plt.plot(epochs, logs[key], next(ls) if metric == "loss" else next(acc), lw=2.5, label=f'{key}: {logs[key][-1]:.4f}')
                else:
                    pass
            plt.title(f'{ModelName}_{metric}_Graph', fontsize=20)
            plt.xlabel('Epochs', fontsize=15)
            plt.ylabel(f'{metric}', fontsize=15)
            plt.legend(fontsize=12)
            plt.grid(True)
            plt.savefig(path)
            plt.close()

            if SendPlot:
                try:
                    if platform == 'slack':
                        Plotter.slack_file_upload(name = f'{ModelName}_{metric}', client=client, channel=channel, filepath=path, verbose=verbose)
                    else:
                        Plotter.telegram_img_upload(name = f'{ModelName}_{metric}', token=client, channel=channel, image=open(path, 'rb'), verbose=verbose)
                except Exception as e:
                    colors.prRed(f"[slackker] ERROR: Invalid Argument: {e}")
            else:
                colors.prYellow("[slackker] WARNING: Skipping graph upload as SendPlot == False ")
        except Exception as e:
            colors.prRed(f'[slackker] ERROR: Plotting Generation Failed: {e}')

class Slack:
    @staticmethod
    def report_stats(client, channel, text, attachment=None, verbose=1):
        """Report training stats"""
        try:
            if attachment:
                if not os.path.isfile(attachment):
                    colors.prRed(f"[slackker] ERROR: Invalid attachment path: {attachment}")
                    return
                Plotter.slack_file_upload(
                    name="Attachment",
                    client=client,
                    channel=channel,
                    filepath=attachment,
                    initial_comment=text,
                    verbose=verbose
                )
            else:
                # Call the chat.postMessage method using the WebClient
                client.chat_postMessage(
                    channel=channel,
                    text=text
                )
                if verbose>=1:
                    colors.prCyan(f"[slackker] Posted update on {channel} channel")

        except SlackApiError as e:
            colors.prRed(f"[slackker] ERROR: Error posting update: {e}")

    @staticmethod
    def keras_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose=1):
        #plot loss
        Plotter.plot_and_upload(platform='slack', ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)

        #plot accuracy
        Plotter.plot_and_upload(platform='slack', ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)

    @staticmethod
    def lightning_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose=1):
        #plot loss
        Plotter.plot_and_upload(platform='slack', ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)

        #plot accuracy
        Plotter.plot_and_upload(platform='slack', ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)

class Telegram:
    @staticmethod
    def report_stats(token, channel, text, attachment=None, verbose=1):
        # apiURL for send message
        apiURL = f'https://api.telegram.org/bot{token}/sendMessage'

        try:
            if attachment:
                if not os.path.isfile(attachment):
                    colors.prRed(f"[slackker] ERROR: Invalid attachment path: {attachment}")
                    return
                with open(attachment, 'rb') as uploaded_file:
                    Plotter.telegram_file_upload(
                        name="Attachment",
                        token=token,
                        channel=channel,
                        file=uploaded_file,
                        caption=text,
                        verbose=verbose
                    )
            else:
                # Call the requests.post method using API request
                requests.post(apiURL, params={'chat_id': channel, 'text': text})
                if verbose>=1:
                    colors.prCyan("[slackker] DEBUG: Posted update on Telegram")

        except Exception as e:
            colors.prRed(f"[slackker] ERROR: Error posting update: {e}")

    @staticmethod
    def keras_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose=1):
        #plot loss
        Plotter.plot_and_upload(platform='telegram', ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)

        #plot accuracy
        Plotter.plot_and_upload(platform='telegram', ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)

    @staticmethod
    def lightning_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose=1):
        #plot loss
        Plotter.plot_and_upload(platform='telegram', ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)

        #plot accuracy
        Plotter.plot_and_upload(platform='telegram', ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)