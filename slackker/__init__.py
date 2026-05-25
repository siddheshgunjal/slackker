from slackker import callbacks
from slackker.callbacks.simple import SimpleCallback
from slackker.core import (
    BaseClient,
    IncomingMessage,
    SlackClient,
    TeamsClient,
    TelegramClient,
)
from slackker.listener import CommandHandler, MessagePoller

__author__ = "Siddhesh Gunjal"
__email__ = "siddhu19@live.com"
__version__ = "1.4.5"

# module level doc-string
__doc__ = """
slackker
=====================================================================
Description
-----------
slackker is a python package for sending notifications and monitoring
your pipeline & ML model training in real-time on Slack, Telegram,
Microsoft Teams, and Discord.

Async-first with sync convenience wrappers. Works with any client
backend via the BaseClient abstraction.

Bidirectional communication — send updates *and* receive commands:
    from slackker.listener import MessagePoller, CommandHandler

New API (recommended):
    from slackker.core import SlackClient, TelegramClient, TeamsClient, DiscordClient
    from slackker.callbacks.simple import SimpleCallback
    from slackker.callbacks.keras import KerasCallback
    from slackker.callbacks.lightning import LightningCallback

Legacy API (deprecated, still works):
    from slackker.callbacks.basic import Update, SlackUpdate, TelegramUpdate
    from slackker.callbacks.keras import SlackUpdate, TelegramUpdate
    from slackker.callbacks.lightning import SlackUpdate, TelegramUpdate

References
----------
https://github.com/siddheshgunjal/slackker
"""

__all__ = [
    "SlackClient",
    "TelegramClient",
    "TeamsClient",
    "BaseClient",
    "IncomingMessage",
    "SimpleCallback",
    "MessagePoller",
    "CommandHandler",
    "callbacks",
]
