"""Deprecated: Use slackker.utils.network instead."""

import warnings
from slackker.utils.network import (
    check_connection_sync,
    check_connection_quick_sync,
    verify_slack_token_sync,
    get_telegram_chat_id_sync,
)

warnings.warn(
    "slackker.utils.checkker is deprecated. Use slackker.utils.network instead.",
    DeprecationWarning,
    stacklevel=2,
)


def check_internet(url, verbose=2):
    return check_connection_sync(url=url, retries=0, delay=60, verbose=verbose)


def check_internet_epoch_end(url):
    return check_connection_quick_sync(url=url, max_retries=3, delay=10, verbose=1)


def slack_connect(token, verbose=2):
    return verify_slack_token_sync(token=token, verbose=verbose)


def get_telegram_chat_id(token, verbose=2):
    return get_telegram_chat_id_sync(token=token, verbose=verbose)
