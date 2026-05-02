import time
import os
from inspect import stack
from datetime import datetime
from slackker.core.client import BaseClient, _run_sync
from slackker.utils.logger import log


class SimpleCallback:
    """Notification callback that works with any client backend.

    Provides a decorator (`notifier`) for automatic function reporting,
    and `notify()` / `async_notify()` for manual notifications.
    """

    def __init__(self, client: BaseClient):
        self.client = client
        if not client.is_connected:
            _run_sync(client.connect())

    def notifier(self, function):
        """Decorator to log function calls and send execution reports."""
        def wrapper(*args, **kwargs):
            if self.client.verbose > 0:
                log.info(f"Calling {function.__name__} with args: {args}, kwargs: {kwargs}")

            start_time = time.time()
            result = function(*args, **kwargs)
            execution_time = time.time() - start_time

            script_name = os.path.basename(__import__(function.__module__).__file__)
            base_msg = f"Function '{function.__name__}' from Script: '{script_name}' executed.\nExecution time: {execution_time:.3f} Seconds"

            if result is not None:
                if isinstance(result, tuple):
                    message = f"{base_msg}\nReturned {len(result)} outputs:\n"
                    for num, item in enumerate(result):
                        message += f"Output {num}:\n{item}\n\n"
                else:
                    message = f"{base_msg}\nReturned output: {result}"
            else:
                message = f"{base_msg}\nReturned output: None"

            self.client.send_message_sync(message)
            return result
        return wrapper

    async def async_notify(self, event: str | None = None, attachment: str | None = None, **kwargs):
        """Async notification method."""
        script = stack()[1].filename
        text = f"Notification: {event or os.path.basename(script)} at {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"

        for key, value in kwargs.items():
            text += f"\n{key}: {value}"

        if attachment:
            await self.client.upload_file(attachment, comment=text)
        else:
            await self.client.send_message(text)

    def notify(self, event: str | None = None, attachment: str | None = None, **kwargs):
        """Sync notification method."""
        _run_sync(self.async_notify(event, attachment, **kwargs))
