from slackker import callbacks
from slackker.callbacks.simple import SimpleCallback
from slackker.core import (
    BaseClient,
    DiscordClient,
    IncomingMessage,
    SlackClient,
    TeamsClient,
    TelegramClient,
)
from slackker.listener import CommandHandler, MessagePoller
from slackker.mcp.handler import MCPHandler

__author__ = "Siddhesh Gunjal"
__email__ = "siddhu19@live.com"
__version__ = "2.0.0"

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

API Reference:
    from slackker.core import SlackClient, TelegramClient, TeamsClient, DiscordClient
    from slackker.callbacks.simple import SimpleCallback
    from slackker.callbacks.keras import KerasCallback
    from slackker.callbacks.lightning import LightningCallback



References
----------
https://github.com/siddheshgunjal/slackker
"""

__all__ = [
    "SlackClient",
    "TelegramClient",
    "TeamsClient",
    "DiscordClient",
    "BaseClient",
    "IncomingMessage",
    "SimpleCallback",
    "MCPHandler",
    "MessagePoller",
    "CommandHandler",
    "callbacks",
]
