"""MCP notification and interaction handler."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import TYPE_CHECKING

from slackker.core.client import _run_sync

if TYPE_CHECKING:
    from slackker.core.client import BaseClient
    from slackker.listener import CommandHandler


class MCPHandler:
    """Handle MCP-driven notifications, approval prompts, and listener lifecycle."""

    def __init__(self, client: BaseClient, poll_interval: float = 2.0):
        self.client = client

        connect = getattr(client, "connect", None)
        if not client.is_connected and callable(connect):
            _run_sync(connect())

        self._poll_interval = poll_interval
        self._listener: CommandHandler | None = None

        # Persistent sync loop for ask()/notify()/stop() sync wrappers
        self._sync_loop: asyncio.AbstractEventLoop | None = None
        self._sync_thread: threading.Thread | None = None

    # ── Persistent background loop (sync mode only) ─────────────────────────

    def _ensure_sync_loop(self) -> None:
        if self._sync_loop is None or not self._sync_loop.is_running():
            self._sync_loop = asyncio.new_event_loop()
            self._sync_thread = threading.Thread(
                target=self._sync_loop.run_forever, daemon=True
            )
            self._sync_thread.start()

    def _sync_run(self, coro):
        self._ensure_sync_loop()
        assert self._sync_loop is not None
        return asyncio.run_coroutine_threadsafe(coro, self._sync_loop).result()

    # ── Internal listener lifecycle ──────────────────────────────────────────

    async def _ensure_listener(self) -> None:
        """Start the internal ``CommandHandler`` on first use."""
        if self._listener is None:
            from slackker.listener import CommandHandler

            self._listener = CommandHandler(
                self.client,
                command_prefix="/",
                interval=self._poll_interval,
                filter_fn=lambda m: not m.is_bot,
            )
            await self._listener.start()

    async def async_stop(self) -> None:
        """Stop the internal listener if it is running."""
        if self._listener is not None:
            await self._listener.stop()
            self._listener = None

    def stop(self) -> None:
        """Stop the internal listener and shut down the sync event loop."""
        if self._sync_loop is not None and self._sync_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.async_stop(), self._sync_loop
            ).result()
            self._sync_loop.call_soon_threadsafe(self._sync_loop.stop)
            assert self._sync_thread is not None
            self._sync_thread.join(timeout=5)
            self._sync_loop = None
            self._sync_thread = None
        else:
            _run_sync(self.async_stop())

    # ── Outbound notifications ───────────────────────────────────────────────

    async def async_notify(
        self,
        event: str | None = None,
        attachment: str | None = None,
        **kwargs,
    ) -> None:
        """Send a notification message with optional metadata and attachment."""
        text = (
            f"Notification: {event or 'update'} at "
            f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        )

        for key, value in kwargs.items():
            text += f"\n{key}: {value}"

        if attachment:
            await self.client.upload_file(attachment, comment=text)
        else:
            await self.client.send_message(text)

    def notify(
        self,
        event: str | None = None,
        attachment: str | None = None,
        **kwargs,
    ) -> None:
        """Sync wrapper for :meth:`async_notify`."""
        self._sync_run(self.async_notify(event=event, attachment=attachment, **kwargs))

    # ── Interactive approval gate ────────────────────────────────────────────

    async def async_ask(
        self,
        question: str,
        timeout: float = 300.0,
        halt_on: str = "no",
    ) -> bool:
        """Ask a question and wait for a human reply.

        Returns ``True`` to continue and ``False`` to halt.
        When no reply arrives before ``timeout``, returns ``True``.
        """
        await self._ensure_listener()

        await self.client.send_message(
            f"{question}\n"
            f"(Reply *{halt_on}* to halt, anything else or no reply to continue. "
            f"{int(timeout)} s timeout → auto-continues)"
        )

        assert self._listener is not None
        reply = await self._listener.poller.wait_for_reply(timeout=timeout)

        if reply is not None and reply.text.strip().lower() == halt_on.lower():
            await self.client.send_message(f"🛑 Halted by {reply.sender}.")
            return False

        approved_by = reply.sender if reply else "timeout"
        await self.client.send_message(f"➡️ Continuing… (approved by {approved_by})")
        return True

    def ask(
        self,
        question: str,
        timeout: float = 300.0,
        halt_on: str = "no",
    ) -> bool:
        """Sync wrapper for :meth:`async_ask`."""
        return self._sync_run(
            self.async_ask(question=question, timeout=timeout, halt_on=halt_on)
        )

    # ── Status ───────────────────────────────────────────────────────────────

    async def async_get_status(self) -> dict[str, object]:
        """Return connection and listener status."""
        return {
            "connected": self.client.is_connected,
            "platform": self.client.platform,
            "listener_active": self._listener is not None and self._listener.is_running,
        }

    def get_status(self) -> dict[str, object]:
        """Sync wrapper for :meth:`async_get_status`."""
        return self._sync_run(self.async_get_status())
