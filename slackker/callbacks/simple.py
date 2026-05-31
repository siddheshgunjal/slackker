import asyncio
import os
import threading
import time
from datetime import datetime
from inspect import stack

from slackker.core.client import BaseClient, _run_sync
from slackker.utils.logger import log


class SimpleCallback:
    """Notification callback that works with any client backend.

    Provides a decorator (`notifier`) for automatic function reporting,
    `notify()` / `async_notify()` for outbound notifications, and
    `ask()` / `ask_sync()` for interactive approval gates — all without
    requiring the user to manage a :class:`~slackker.listener.CommandHandler`
    directly.
    """

    def __init__(self, client: BaseClient):
        self.client = client
        if not client.is_connected:
            _run_sync(client.connect())
        self._listener = None       # lazily created on first ask()
        self._sync_loop = None      # persistent event loop for sync ask()/stop()
        self._sync_thread = None    # background thread running _sync_loop

    # ── Persistent background loop (sync mode only) ───────────────────────────

    def _ensure_sync_loop(self) -> None:
        """Start a persistent background event loop for sync ask() calls.

        ``asyncio.run()`` creates a *new* event loop per call and closes it
        when the coroutine finishes.  Because the polling Task is bound to the
        loop it was created in, a second ``ask()`` call would find the Task
        dead and ``wait_for_reply`` would never be resolved.

        A single persistent loop avoids this: the Task created during the
        first ``ask()`` stays alive across all subsequent calls until
        ``stop()`` is explicitly called.
        """
        if self._sync_loop is None or not self._sync_loop.is_running():
            self._sync_loop = asyncio.new_event_loop()
            self._sync_thread = threading.Thread(
                target=self._sync_loop.run_forever, daemon=True
            )
            self._sync_thread.start()

    def _sync_run(self, coro):
        """Submit *coro* to the persistent background loop and block until done."""
        self._ensure_sync_loop()
        return asyncio.run_coroutine_threadsafe(coro, self._sync_loop).result()  # type: ignore

    # ── Internal listener lifecycle ───────────────────────────────────────────

    async def _ensure_listener(self) -> None:
        """Start the internal CommandHandler the first time ask() is called."""
        if self._listener is None:
            from slackker.listener import CommandHandler  # avoid circular import
            self._listener = CommandHandler(
                self.client,
                command_prefix="/",
                filter_fn=lambda m: not m.is_bot,
            )
            await self._listener.start()

    async def async_stop(self) -> None:
        """Async: stop the internal listener if it is running."""
        if self._listener is not None:
            await self._listener.stop()
            self._listener = None

    def stop(self) -> None:
        """Sync: stop the internal listener and shut down the background loop."""
        if self._sync_loop is not None and self._sync_loop.is_running():
            # Stop the listener inside the persistent loop, then shut it down
            asyncio.run_coroutine_threadsafe(self.async_stop(), self._sync_loop).result()
            self._sync_loop.call_soon_threadsafe(self._sync_loop.stop)
            self._sync_thread.join(timeout=5)  # type: ignore
            self._sync_loop = None
            self._sync_thread = None
        else:
            _run_sync(self.async_stop())

    # ── Interactive approval gate ─────────────────────────────────────────────

    async def async_ask(
        self,
        question: str,
        timeout: float = 60.0,
        halt_on: str = "no",
    ) -> bool:
        """Async: send *question* and wait for a human reply.

        Parameters
        ----------
        question : str
            The message sent to the platform asking for approval.
        timeout : float
            Seconds to wait for a reply.  On timeout the gate **auto-approves**
            and returns ``True`` so automated runs never block indefinitely.
        halt_on : str
            The exact reply text (case-insensitive) that halts the flow.
            Defaults to ``"no"``.

        Returns
        -------
        bool
            ``True``  — reply was not *halt_on*, or timed out (continue).
            ``False`` — reply matched *halt_on* (halt).

        Example::

            if not await notifier.async_ask("Step 1 done. Continue?"):
                await notifier.async_stop()
                return
        """
        await self._ensure_listener()
        await self.client.send_message(
            f"{question}\n"
            f"(Reply *{halt_on}* to halt, anything else or no reply to continue. "
            f"{int(timeout)} s timeout → auto-continues)"
        )
        reply = await self._listener.poller.wait_for_reply(timeout=timeout)  # type: ignore
        if reply is not None and reply.text.strip().lower() == halt_on.lower():
            await self.client.send_message(f"🛑 Halted by {reply.sender}.")
            return False
        approved_by = reply.sender if reply else "timeout"
        await self.client.send_message(f"➡️ Continuing… (approved by {approved_by})")
        return True

    def ask(
        self,
        question: str,
        timeout: float = 60.0,
        halt_on: str = "no",
    ) -> bool:
        """Sync: send *question* and wait for a human reply.

        Uses a persistent background event loop so the polling Task stays
        alive across multiple consecutive ``ask()`` calls — unlike
        ``asyncio.run()`` which would close the loop (and kill the Task)
        after every call.

        Example (inside a Keras/Lightning training callback)::

            if not notifier.ask("Epoch 3 done. Continue?"):
                self.model.stop_training = True
        """
        return self._sync_run(self.async_ask(question, timeout, halt_on))

    # ── Notifier decorator ────────────────────────────────────────────────────

    def notifier(self, function):
        """Decorator to log function calls and send execution reports."""

        def wrapper(*args, **kwargs):
            if self.client.verbose > 0:
                log.info(
                    f"Calling {function.__name__} with args: {args}, kwargs: {kwargs}"
                )

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

    async def async_notify(
        self, event: str | None = None, attachment: str | None = None, **kwargs
    ):
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
