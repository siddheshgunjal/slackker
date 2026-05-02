"""Deprecated: Use slackker.core and slackker.utils.plotting instead."""

import warnings
import os
from slackker.utils.logger import log
from slackker.utils.plotting import generate_plot

warnings.warn(
    "slackker.utils.functions is deprecated. Use slackker.core client classes and slackker.utils.plotting instead.",
    DeprecationWarning,
    stacklevel=2,
)


class Plotter:
    """Deprecated: Use slackker.utils.plotting and client.upload_file() instead."""

    @staticmethod
    def slack_file_upload(name, client, channel, filepath, initial_comment=None, verbose=1):
        from slack_sdk.errors import SlackApiError
        try:
            comment = initial_comment if initial_comment is not None else f"{name} 📎"
            client.files_upload_v2(channel=channel, file=filepath, initial_comment=comment)
            if verbose >= 1:
                log.debug(f"Uploaded attachment on {channel} channel")
        except SlackApiError as e:
            log.error(f"Error uploading attachment: {e}")

    @staticmethod
    def telegram_img_upload(name, token, channel, image, verbose=1):
        import requests
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            requests.post(url, params={"chat_id": channel, "caption": f"{name} 📎"}, files={"photo": image})
            if verbose >= 1:
                log.debug("Uploaded attachment on Telegram")
        except Exception as e:
            log.error(f"Error uploading attachment: {e}")

    @staticmethod
    def telegram_file_upload(name, token, channel, file, caption=None, verbose=1):
        import requests
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        try:
            tg_caption = caption if caption is not None else f"{name} 📎"
            requests.post(url, params={"chat_id": channel, "caption": tg_caption}, files={"document": file})
            if verbose >= 1:
                log.debug("Uploaded attachment on Telegram")
        except Exception as e:
            log.error(f"Error uploading attachment: {e}")

    @staticmethod
    def plot_and_upload(platform, ModelName, export, client, channel, SendPlot, logs, metric, verbose=1):
        path = generate_plot(ModelName, export, logs, metric)
        if path and SendPlot:
            try:
                if platform == "slack":
                    Plotter.slack_file_upload(name=f"{ModelName}_{metric}", client=client, channel=channel, filepath=path, verbose=verbose)
                else:
                    Plotter.telegram_img_upload(name=f"{ModelName}_{metric}", token=client, channel=channel, image=open(path, "rb"), verbose=verbose)
            except Exception as e:
                log.error(f"Invalid Argument: {e}")
        elif not SendPlot:
            log.warning("Skipping graph upload as SendPlot == False")


class Slack:
    """Deprecated: Use slackker.core.SlackClient instead."""

    @staticmethod
    def report_stats(client, channel, text, attachment=None, verbose=1):
        from slack_sdk.errors import SlackApiError
        try:
            if attachment:
                if not os.path.isfile(attachment):
                    log.error(f"Invalid attachment path: {attachment}")
                    return
                Plotter.slack_file_upload(
                    name="Attachment", client=client, channel=channel, filepath=attachment, initial_comment=text, verbose=verbose
                )
            else:
                client.chat_postMessage(channel=channel, text=text)
                if verbose >= 1:
                    log.info(f"Posted update on {channel} channel")
        except SlackApiError as e:
            log.error(f"Error posting update: {e}")

    @staticmethod
    def keras_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose=1):
        Plotter.plot_and_upload(platform="slack", ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)
        Plotter.plot_and_upload(platform="slack", ModelName=ModelName, export=export, client=client, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)

    @staticmethod
    def lightning_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose=1):
        Slack.keras_plot_history(ModelName, export, client, channel, SendPlot, training_logs, verbose)


class Telegram:
    """Deprecated: Use slackker.core.TelegramClient instead."""

    @staticmethod
    def report_stats(token, channel, text, attachment=None, verbose=1):
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            if attachment:
                if not os.path.isfile(attachment):
                    log.error(f"Invalid attachment path: {attachment}")
                    return
                with open(attachment, "rb") as f:
                    Plotter.telegram_file_upload(name="Attachment", token=token, channel=channel, file=f, caption=text, verbose=verbose)
            else:
                requests.post(url, params={"chat_id": channel, "text": text})
                if verbose >= 1:
                    log.debug("Posted update on Telegram")
        except Exception as e:
            log.error(f"Error posting update: {e}")

    @staticmethod
    def keras_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose=1):
        Plotter.plot_and_upload(platform="telegram", ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="loss", verbose=verbose)
        Plotter.plot_and_upload(platform="telegram", ModelName=ModelName, export=export, client=token, channel=channel, SendPlot=SendPlot, logs=training_logs, metric="acc", verbose=verbose)

    @staticmethod
    def lightning_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose=1):
        Telegram.keras_plot_history(ModelName, export, token, channel, SendPlot, training_logs, verbose)