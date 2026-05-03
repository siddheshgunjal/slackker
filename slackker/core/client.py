import asyncio
from abc import ABC, abstractmethod


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

    # --- Sync convenience wrappers ---

    def send_message_sync(self, text: str) -> None:
        _run_sync(self.send_message(text))

    def upload_file_sync(self, filepath: str, comment: str | None = None) -> None:
        _run_sync(self.upload_file(filepath, comment))

    def upload_image_sync(self, filepath: str, comment: str | None = None) -> None:
        _run_sync(self.upload_image(filepath, comment))
