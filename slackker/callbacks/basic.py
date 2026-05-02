"""
Deprecated module. Use slackker.callbacks.simple instead.

This module is kept for backward compatibility only.
"""

import warnings
from slackker.callbacks.simple import SimpleCallback
from slackker.core.client import _run_sync as _sync
from slackker.core.slack import SlackClient
from slackker.core.telegram import TelegramClient
from slackker.utils.logger import log


class Update(SimpleCallback):
    """Deprecated: Use SimpleCallback from slackker.callbacks.simple instead."""

    def __init__(self, client):
        warnings.warn(
            "Update is deprecated. Use SimpleCallback(client) from slackker.callbacks.simple instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(client)


# ──────────────────────────────────────────────
# Backward-compatible shims (deprecated)
# ──────────────────────────────────────────────

class SlackUpdate(SimpleCallback):
    """Deprecated: Use SimpleCallback(SlackClient(...)) instead."""

    def __init__(self, token, channel, verbose=0):
        warnings.warn(
            "SlackUpdate is deprecated. Use SimpleCallback(SlackClient(token, channel)) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if token is None:
            log.error("Please enter a valid Slack API Token.")
            return

        client = SlackClient(token=token, channel=channel, verbose=verbose)
        connected = _sync(client.connect())
        if connected:
            super().__init__(client)
        else:
            log.error("Failed to connect to Slack.")


class TelegramUpdate(SimpleCallback):
    """Deprecated: Use SimpleCallback(TelegramClient(...)) instead."""

    def __init__(self, token, verbose=0):
        warnings.warn(
            "TelegramUpdate is deprecated. Use SimpleCallback(TelegramClient(token)) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if token is None:
            log.error("Please enter a valid Telegram API Token.")
            return

        client = TelegramClient(token=token, verbose=verbose)
        connected = _sync(client.connect())
        if connected:
            super().__init__(client)
        else:
            log.error("Failed to connect to Telegram.")