import os

import httpx

from slackker.core.client import BaseClient
from slackker.core.models import IncomingMessage
from slackker.utils import network
from slackker.utils.logger import log


class TelegramClient(BaseClient):
    """Telegram client backend using httpx async client."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, token: str, chat_id: str | None = None, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not token:
            raise ValueError("Telegram API token is required.")
        self._token = token
        self._chat_id = chat_id
        self._base_url = self.BASE_URL.format(token=token)

    @property
    def platform(self) -> str:
        return "telegram"

    @property
    def is_connected(self) -> bool:
        return self._chat_id is not None

    @property
    def connectivity_url(self) -> str:
        return "api.telegram.org"

    @property
    def chat_id(self) -> str | None:
        return self._chat_id

    async def connect(self) -> bool:
        """Verify server connectivity and discover chat_id if not provided."""
        server = await network.check_connection(url="api.telegram.org")
        if not server:
            return False

        if not self._chat_id:
            self._chat_id = await network.get_telegram_chat_id(token=self._token)

        return self._chat_id is not None

    async def send_message(self, text: str) -> None:
        if not self._chat_id:
            log.error(
                "chat_id is not set. Call `await client.connect()` before sending messages."
            )
            return
        url = f"{self._base_url}/sendMessage"
        try:
            async with network._make_async_client() as client:
                response = await client.post(
                    url, params={"chat_id": self._chat_id, "text": text}
                )
                response.raise_for_status()
            log.debug("Posted update on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error posting update: {e}")

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        if not self._chat_id:
            log.error(
                "chat_id is not set. Call `await client.connect()` before uploading files."
            )
            return
        url = f"{self._base_url}/sendDocument"
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            caption = comment or "Attachment 📎"
            async with network._make_async_client() as client:
                with open(filepath, "rb") as f:
                    response = await client.post(
                        url,
                        params={"chat_id": self._chat_id, "caption": caption},
                        files={"document": f},
                    )
                    response.raise_for_status()
            log.debug("Uploaded attachment on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error uploading file: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        if not self._chat_id:
            log.error(
                "chat_id is not set. Call `await client.connect()` before uploading images."
            )
            return
        url = f"{self._base_url}/sendPhoto"
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            caption = comment or "Attachment 📎"
            async with network._make_async_client() as client:
                with open(filepath, "rb") as f:
                    response = await client.post(
                        url,
                        params={"chat_id": self._chat_id, "caption": caption},
                        files={"photo": f},
                    )
                    response.raise_for_status()
            log.debug("Uploaded image on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error uploading image: {e}")

    async def fetch_messages(
        self,
        limit: int = 10,
        since: str | None = None,
        thread_id: str | None = None,
    ) -> list[IncomingMessage]:
        """Fetch new updates from the Telegram bot via ``getUpdates``.

        *since* is treated as the ``offset`` parameter (the ``update_id`` of
        the last seen update, incremented by one — see
        :meth:`cursor_from_message`).

        When *thread_id* is provided only messages whose
        ``reply_to_message.message_id`` matches are returned (client-side
        filter, since Telegram has no server-side reply filter).
        """
        url = f"{self._base_url}/getUpdates"
        params: dict = {"limit": min(limit, 100), "timeout": 0}
        if since:
            params["offset"] = int(since)

        try:
            async with network._make_async_client() as client:
                resp = await client.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()

            result: list[IncomingMessage] = []
            for update in data.get("result", []):
                msg = update.get("message") or update.get("channel_post")
                if not msg:
                    continue

                # Filter to the configured chat
                if self._chat_id and str(msg["chat"]["id"]) != str(self._chat_id):
                    continue

                # Thread context: which message is this a reply to?
                reply_to = msg.get("reply_to_message")
                msg_thread_id = str(reply_to["message_id"]) if reply_to else None

                if thread_id is not None and msg_thread_id != thread_id:
                    continue

                from_user = msg.get("from") or {}
                is_bot = from_user.get("is_bot", False)
                sender = (
                    from_user.get("username")
                    or from_user.get("first_name")
                    or "unknown"
                )

                result.append(
                    IncomingMessage(
                        text=msg.get("text", ""),
                        sender=sender,
                        sender_id=str(from_user.get("id", "")),
                        timestamp=str(update["update_id"]),
                        platform="telegram",
                        is_bot=is_bot,
                        thread_id=msg_thread_id,
                        raw=update,
                    )
                )
            return result
        except httpx.HTTPStatusError as e:
            log.error(
                f"Telegram fetch_messages error {e.response.status_code}: {e.response.text}"
            )
            return []
        except Exception as e:
            log.error(f"Telegram fetch_messages error: {e}")
            return []

    def cursor_from_message(self, msg: IncomingMessage) -> str:
        """Return ``str(update_id + 1)`` so the next poll skips already-seen updates."""
        return str(int(msg.timestamp) + 1)
