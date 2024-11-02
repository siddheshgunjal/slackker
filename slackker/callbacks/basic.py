import time
import os
from inspect import stack
from datetime import datetime
from slack_sdk import WebClient
from slackker.utils import checkker
from slackker.utils import functions
from slackker.utils.ccolors import colors

class SlackUpdate():
    ''' SlackUpdate class to send updates to Telegram channel '''
    def __init__(self, token, channel, verbose=0):

        if token is None:
            colors.prRed('[slackker] ERROR: Please enter Valid Slack API Token.')
            return

        server = checkker.check_internet(url="www.telegram.org", verbose=verbose)
        api = checkker.slack_connect(token=token, verbose=verbose)

        if server and api:
            self.client = WebClient(token=token)
            self.channel = channel
            self.verbose = verbose
        
    def notifier(self, function):
        ''' Decorator to log function calls '''
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
                if isinstance(result, tuple):
                    message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned {len(result)} outputs:\n"
                    num = 0
                    for i in result:
                        message += f"Output {num}:\n{i}\n\n"
                        num += 1
                else:
                    message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: {result}"
            else:
                message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: None"

            # Log the return value
            functions.Slack.report_stats(
                client=self.client,
                channel=self.channel,
                text=message,
                verbose=self.verbose
            )

            return result
        return wrapper
    
    def notify(self, *args, **kwargs):
        ''' Notify the user that the script has been executed '''
        
        script = stack()[1].filename
        
        text = f"Your script: '{os.path.basename(script)}' has been executed successfully at {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        if args:
            for arg in args:
                text += f"\n\n{arg}"
        if kwargs:
            for key, value in kwargs.items():
                text += f"\n\n{key}: {value}"

        functions.Slack.report_stats(
            client=self.client,
            channel=self.channel,
            text=text,
            verbose=self.verbose
        )

class TelegramUpdate():
    ''' TelegramUpdate class to send updates to Telegram channel '''
    def __init__(self, token, verbose=0):

        if token is None:
            colors.prRed('[slackker] ERROR: Please enter Valid Telegram API Token.')
            return

        server = checkker.check_internet(url="www.telegram.org", verbose=verbose)
        channel = checkker.get_telegram_chat_id(token=token, verbose=verbose)

        if server and channel:
            self.token = token
            self.channel = channel
            self.verbose = verbose
        
    def notifier(self, function):
        ''' Decorator to log function calls '''
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
                if isinstance(result, tuple):
                    message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned {len(result)} outputs:\n"
                    num = 0
                    for i in result:
                        message += f"Output {num}:\n{i}\n\n"
                        num += 1
                else:
                    message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: {result}"
            else:
                message = f"Function '{function.__name__}' from Script: '{os.path.basename(__import__(function.__module__).__file__)}' executed.\nExecution time: {execution_time:.3f} Seconds\nReturned output: None"

            # Log the return value
            functions.Telegram.report_stats(
                token=self.token,
                channel=self.channel,
                text=message,
                verbose=self.verbose
            )

            return result
        return wrapper
    
    def notify(self, *args, **kwargs):
        ''' Notify the user that the script has been executed '''

        script = stack()[1].filename
        
        text = f"Your script: '{os.path.basename(script)}' has been executed successfully at {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        if args:
            for arg in args:
                text += f"\n\n{arg}"
        if kwargs:
            for key, value in kwargs.items():
                text += f"\n\n{key}: {value}"

        functions.Telegram.report_stats(
            token=self.token,
            channel=self.channel,
            text=text,
            verbose=self.verbose
        )