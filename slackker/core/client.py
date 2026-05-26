import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from slackker.utils.logger import set_verbosity

if TYPE_CHECKING:
    from slackker.core.models import IncomingMessage


def _run_sync(coro):
    """Run an async coroutine synchronously, handling already-running event loops (e.g. Jupyter)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio

        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)


class BaseClient(ABC):
    """Abstract base class for all client backends (Slack, Telegram, etc.)."""

    def __init__(self, verbose: int = 0):
        self._verbose = verbose
        set_verbosity(verbose)

    @property
    def verbose(self) -> int:
        return self._verbose

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return the platform name, e.g. 'slack' or 'telegram'."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the client has successfully connected (token verified, chat_id known, etc.)."""
        ...

    @property
    @abstractmethod
    def connectivity_url(self) -> str:
        """Return the hostname used to check platform reachability, e.g. 'www.slack.com'."""
        ...

    @abstractmethod
    async def send_message(self, text: str) -> None:
        """Send a text message to the configured channel."""
        ...

    @abstractmethod
    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        """Upload a file to the configured channel."""
        ...

    @abstractmethod
    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        """Upload an image to the configured channel."""
        ...

    async def fetch_messages(
        self,
        limit: int = 10,
        since: str | None = None,
        thread_id: str | None = None,
    ) -> "list[IncomingMessage]":
        """Fetch recent messages from the configured channel.

        Parameters
        ----------
        limit : int
            Maximum number of messages to return.
        since : str | None
            Platform-specific cursor/timestamp — only messages *after* this
            value are returned (exclusive).  Pass the ``timestamp`` of the
            last ``IncomingMessage`` you processed, or use
            :meth:`cursor_from_message` to derive the correct next-cursor.

            - **Slack** – ``ts`` of the last seen message.
            - **Telegram** – ``str(update_id + 1)`` of the last seen update.
            - **Discord** – Snowflake ID of the last seen message.
            - **Teams** – ISO 8601 datetime of the last seen message.
        thread_id : str | None
            Scope the fetch to a specific thread/reply chain:

            - **Slack** – ``thread_ts`` of the parent message; returns replies
              via ``conversations.replies``.
            - **Telegram** – ``message_id`` string of the message being replied
              to; filters updates client-side.
            - **Discord** – ``message_id`` of the message being replied to;
              filters by ``message_reference`` client-side.
            - **Teams** – message ID whose replies to fetch via
              ``/messages/{id}/replies``.

        Returns
        -------
        list[IncomingMessage]
            Messages in chronological order (oldest first).
        """
        return []

    def cursor_from_message(self, msg: "IncomingMessage") -> str:
        """Return the ``since`` cursor for the next :meth:`fetch_messages` call.

        The default implementation returns ``msg.timestamp`` unchanged.
        Platforms with offset-based pagination (Telegram) override this.
        """
        return msg.timestamp

    # --- Sync convenience wrappers ---

    def send_message_sync(self, text: str) -> None:
        _run_sync(self.send_message(text))

    def upload_file_sync(self, filepath: str, comment: str | None = None) -> None:
        _run_sync(self.upload_file(filepath, comment))

    def upload_image_sync(self, filepath: str, comment: str | None = None) -> None:
        _run_sync(self.upload_image(filepath, comment))

    def fetch_messages_sync(
        self,
        limit: int = 10,
        since: str | None = None,
        thread_id: str | None = None,
    ) -> "list[IncomingMessage]":
        return _run_sync(self.fetch_messages(limit, since, thread_id))
