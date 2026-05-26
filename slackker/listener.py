"""Background polling and command dispatch for bidirectional messaging.

Classes
-------
MessagePoller
    Polls a :class:`~slackker.core.client.BaseClient` for new messages and
    dispatches them to registered handlers.  Supports both event-driven
    (``on_message`` / ``on_command``) and request-response
    (``wait_for_reply``) patterns.

CommandHandler
    Convenience wrapper around :class:`MessagePoller` that adds a
    decorator-based command registration API (``@handler.command("name")``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from slackker.utils.logger import log

if TYPE_CHECKING:
    from slackker.core.client import BaseClient
    from slackker.core.models import IncomingMessage


class MessagePoller:
    """Background polling loop that delivers incoming messages from any slackker client.

    The poller runs as an :class:`asyncio.Task` and polls
    :meth:`~slackker.core.client.BaseClient.fetch_messages` at a configurable
    interval.  Each new message is dispatched to:

    * All handlers registered with :meth:`on_message`.
    * Any command handler registered with :meth:`on_command` whose prefix
      matches the message text.
    * Any pending :meth:`wait_for_reply` callers that match the message.

    Cursor tracking ensures messages are never re-delivered across poll
    iterations.

    Example::

        poller = MessagePoller(client, interval=3.0)

        @poller.on_message
        async def handle(msg):
            print(f"[{msg.sender}]: {msg.text}")

        await poller.start()
        # ... do work ...
        await poller.stop()

    For request-response flows::

        await client.send_message("Proceed with training? (yes/no)")
        reply = await poller.wait_for_reply(timeout=120)
        if reply and reply.text.lower() == "yes":
            ...
    """

    def __init__(
        self,
        client: BaseClient,
        interval: float = 2.0,
        thread_id: str | None = None,
        filter_fn: Callable[[IncomingMessage], bool] | None = None,
    ):
        """
        Parameters
        ----------
        client : BaseClient
            The messaging platform client to poll.
        interval : float
            Seconds between consecutive polls.  Defaults to ``2.0``.
        thread_id : str | None
            If set, every poll is scoped to this thread/reply chain (passed
            through to :meth:`~slackker.core.client.BaseClient.fetch_messages`).
        filter_fn : callable | None
            Optional callable ``(IncomingMessage) -> bool``.  Messages that
            return ``False`` are silently discarded before any handler is
            invoked.
        """
        self._client = client
        self._interval = interval
        self._thread_id = thread_id
        self._filter_fn = filter_fn

        self._task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._last_cursor: str | None = None

        self._message_handlers: list[Callable[[IncomingMessage], Awaitable[None]]] = []
        self._command_handlers: dict[str, Callable] = {}

        # Each entry is (filter_fn | None, Future) for pending wait_for_reply calls.
        self._waiters: list[tuple[Callable | None, asyncio.Future]] = []

    # ── Handler registration ──────────────────────────────────────────────────

    def on_message(
        self,
        handler: Callable[[IncomingMessage], Awaitable[None]],
    ) -> Callable:
        """Register a coroutine called for every new incoming message.

        Can be used as a decorator::

            @poller.on_message
            async def handle(msg):
                print(msg.text)
        """
        self._message_handlers.append(handler)
        return handler

    def on_command(
        self,
        prefix: str,
        handler: Callable[[IncomingMessage, str], Awaitable[None]],
    ) -> None:
        """Register a handler for messages whose text starts with *prefix*.

        The handler is called with ``(message, args_string)`` where
        *args_string* is the remainder of the text after the prefix (stripped).

        Example::

            poller.on_command("/stop", stop_training)
        """
        self._command_handlers[prefix] = handler

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background polling loop as an :class:`asyncio.Task`.

        Calling ``start()`` while the poller is already running is a no-op.
        """
        if self._task is not None and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(
            self._poll_loop(), name=f"slackker-poller-{self._client.platform}"
        )

    async def stop(self) -> None:
        """Stop the polling loop gracefully and await its completion."""
        if self._stop_event:
            self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    @property
    def is_running(self) -> bool:
        """``True`` if the polling task is active."""
        return self._task is not None and not self._task.done()

    # ── Request-response ──────────────────────────────────────────────────────

    async def wait_for_reply(
        self,
        timeout: float = 300.0,
        thread_id: str | None = None,
    ) -> IncomingMessage | None:
        """Block until a new message arrives or *timeout* seconds elapse.

        Parameters
        ----------
        timeout : float
            Maximum seconds to wait.  Returns ``None`` on timeout.
        thread_id : str | None
            If provided, only a message whose ``thread_id`` field matches is
            accepted.  This lets you wait for a reply within a specific
            thread (Slack ``thread_ts``, Telegram reply chain, etc.).

        Returns
        -------
        IncomingMessage | None
            The first matching message, or ``None`` if the timeout expired.

        Note
        ----
        The poller **must** be running (call :meth:`start` first) for
        ``wait_for_reply`` to receive dispatched messages.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()

        thread_filter: Callable | None = None
        if thread_id is not None:
            thread_filter = lambda msg: msg.thread_id == thread_id  # noqa: E731

        self._waiters.append((thread_filter, future))
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._waiters = [
                (f, fut) for f, fut in self._waiters if fut is not future
            ]

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        """Main polling coroutine.  Runs until :meth:`stop` is called."""
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                messages = await self._client.fetch_messages(
                    limit=50,
                    since=self._last_cursor,
                    thread_id=self._thread_id,
                )
                for msg in messages:
                    if self._filter_fn and not self._filter_fn(msg):
                        continue
                    await self._dispatch(msg)

                if messages:
                    self._last_cursor = self._client.cursor_from_message(messages[-1])
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(
                    f"MessagePoller: error during poll ({self._client.platform}): {e}"
                )
            await asyncio.sleep(self._interval)

    async def _dispatch(self, msg: IncomingMessage) -> None:
        """Resolve pending waiters and invoke registered handlers."""
        # Resolve wait_for_reply futures
        remaining: list[tuple[Callable | None, asyncio.Future]] = []
        for filter_fn, future in self._waiters:
            if future.done():
                continue
            if filter_fn is None or filter_fn(msg):
                future.set_result(msg)
            else:
                remaining.append((filter_fn, future))
        self._waiters = remaining

        # Generic message handlers
        for handler in self._message_handlers:
            try:
                await handler(msg)
            except Exception as e:
                log.error(f"MessagePoller: on_message handler raised: {e}")

        # Command handlers
        text = msg.text.strip()
        for prefix, handler in self._command_handlers.items():
            if text.startswith(prefix):
                args = text[len(prefix):].strip()
                try:
                    await handler(msg, args)
                except Exception as e:
                    log.error(
                        f"MessagePoller: command handler '{prefix}' raised: {e}"
                    )


class CommandHandler:
    """Decorator-based command dispatcher built on top of :class:`MessagePoller`.

    Example::

        handler = CommandHandler(client, command_prefix="/")

        @handler.command("status")
        async def on_status(msg, args):
            await client.send_message(f"Training at epoch {current_epoch}")

        @handler.command("stop")
        async def on_stop(msg, args):
            trainer.should_stop = True
            await client.send_message("Stopping after this epoch…")

        await handler.start()
        # run training loop ...
        await handler.stop()

    The underlying :class:`MessagePoller` is accessible via :attr:`poller`
    for advanced use (e.g. calling :meth:`~MessagePoller.wait_for_reply`).
    """

    def __init__(
        self,
        client: BaseClient,
        command_prefix: str = "/",
        interval: float = 2.0,
        filter_fn: Callable[[IncomingMessage], bool] | None = None,
    ):
        """
        Parameters
        ----------
        client : BaseClient
            The messaging platform client to listen on.
        command_prefix : str
            Prefix that marks a message as a command.  Defaults to ``"/"``.
        interval : float
            Polling interval in seconds passed to :class:`MessagePoller`.
        filter_fn : callable | None
            Optional ``(IncomingMessage) -> bool`` predicate passed through to
            the underlying :class:`MessagePoller`.  Messages that return
            ``False`` are silently discarded before any handler or
            ``wait_for_reply`` waiter is invoked.  A common value is
            ``lambda m: not m.is_bot`` to ignore the bot's own outbound
            messages (important on platforms like Discord where the REST API
            returns all channel messages, including those sent by the bot).
        """
        self._client = client
        self._prefix = command_prefix
        self.poller = MessagePoller(client, interval=interval, filter_fn=filter_fn)

    def command(self, name: str) -> Callable:
        """Decorator that registers a command handler for ``<prefix><name>``.

        The decorated coroutine receives ``(msg: IncomingMessage, args: str)``
        where *args* is the text that follows the full command token (stripped).

        Example::

            @handler.command("stop")
            async def on_stop(msg, args):
                await client.send_message("Stopping!")
        """
        def decorator(fn: Callable) -> Callable:
            self.poller.on_command(f"{self._prefix}{name}", fn)
            return fn
        return decorator

    async def start(self) -> None:
        """Start the underlying :class:`MessagePoller`."""
        await self.poller.start()

    async def stop(self) -> None:
        """Stop the underlying :class:`MessagePoller`."""
        await self.poller.stop()

    @property
    def is_running(self) -> bool:
        """``True`` if the underlying poller is active."""
        return self.poller.is_running
