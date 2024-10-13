import time
from datetime import datetime, timezone
from slack_sdk import WebClient
from slackker.utils import checkker
from slackker.utils import functions
from slackker.utils.ccolors import colors


class TelegramUpdate():
    """Custom Keras callback that posts to Slack while training a neural network"""
    def __init__(self, token, verbose=0):

        if token is None:
            colors.prRed('[slackker] ERROR: Please enter Valid Slack API Token.')
            return

        server = checkker.check_internet(url="www.telegram.org", verbose=verbose)
        channel = checkker.get_telegram_chat_id(token=token, verbose=verbose)

        if server and channel:
            self.token = token
            self.channel = channel
            self.verbose = verbose
        
    def logger(self, function):
        def wrapper(*args, **kwargs):
            if self.verbose > 0:
                # Log the function call
                colors.prCyan(f"[slackker] INFO: Calling {function.__name__} with args: {args}, kwargs: {kwargs}")
            
            # Call the original function
            start_time = time.time()
            result = function(*args, **kwargs)
            end_time = time.time()

            # execution time
            execution_time = end_time - start_time

            if result is not None:
                message = f"Function '{function.__name__}' from Script: '{__import__(function.__module__).__file__}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: {result}"
            else:
                message = f"Function '{function.__name__}' from Script: '{__import__(function.__module__).__file__}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: None"

            # Log the return value
            functions.Telegram.report_stats(
                token=self.token,
                channel=self.channel,
                text=message,
                verbose=self.verbose
            )

            return result
        return wrapper
    
    def notify(self, script):
        
        text = f"Your script: '{script}' has been executed successfully at {datetime.now(timezone.utc).strftime('%d-%m-%Y %H:%M:%S')}"

        functions.Telegram.report_stats(
            token=self.token,
            channel=self.channel,
            text=text,
            verbose=self.verbose
        )

        return