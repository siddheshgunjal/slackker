import os

import httpx

from slackker.core.client import BaseClient
from slackker.core.models import IncomingMessage
from slackker.utils import network
from slackker.utils.logger import log


class DiscordClient(BaseClient):
    """Discord client backend using the official Discord API v10."""

    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, token: str, channel_id: str, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not token:
            raise ValueError("Discord Bot token is required.")
        if not channel_id:
            raise ValueError("Discord channel_id is required.")
        self._token = token
        self._channel_id = channel_id
        self._connected = False

    @property
    def platform(self) -> str:
        return "discord"

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def connectivity_url(self) -> str:
        return "discord.com"

    async def connect(self) -> bool:
        """Verify server connectivity and Bot token. Returns True on success."""
        server = await network.check_connection(
            url="discord.com", verbose=self._verbose
        )
        api = await network.verify_discord_token(
            token=self._token, verbose=self._verbose
        )
        self._connected = server and api
        return self._connected

    async def send_message(self, text: str) -> None:
        """Send a text message to the configured channel."""
        url = f"{self.BASE_URL}/channels/{self._channel_id}/messages"
        headers = {"Authorization": f"Bot {self._token}"}
        payload = {"content": text}
        try:
            async with network._make_async_client() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10)
                resp.raise_for_status()
            if self._verbose >= 1:
                log.info(f"Posted update to Discord channel {self._channel_id}")
        except httpx.HTTPStatusError as e:
            log.error(f"Discord API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error posting update to Discord: {e}")

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        """Upload a file to the configured channel."""
        if not os.path.isfile(filepath):
            log.error(f"Invalid file path: {filepath}")
            return

        url = f"{self.BASE_URL}/channels/{self._channel_id}/messages"
        headers = {"Authorization": f"Bot {self._token}"}

        # Discord uses multipart/form-data for files.
        # The message content goes into 'payload_json'.
        import json

        caption = comment or "Attachment 📎"
        payload_json = json.dumps({"content": caption})

        try:
            async with network._make_async_client() as client:
                with open(filepath, "rb") as f:
                    files = {"file": (os.path.basename(filepath), f)}
                    data = {"payload_json": payload_json}
                    resp = await client.post(
                        url, headers=headers, data=data, files=files, timeout=60
                    )
                    resp.raise_for_status()
            if self._verbose >= 1:
                log.debug(f"Uploaded attachment to Discord channel {self._channel_id}")
        except httpx.HTTPStatusError as e:
            log.error(f"Discord API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error uploading file to Discord: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        # Discord handles images as general attachments
        await self.upload_file(filepath, comment)

    async def fetch_messages(
        self,
        limit: int = 10,
        since: str | None = None,
        thread_id: str | None = None,
    ) -> list[IncomingMessage]:
        """Fetch messages from the Discord channel.

        *since* is a Snowflake message ID — only messages with a higher
        (newer) ID are returned (maps to the ``after`` query parameter).

        When *thread_id* is provided, only messages whose
        ``message_reference.message_id`` matches are returned (client-side
        filter).  Messages are returned in chronological order (oldest first).
        """
        url = f"{self.BASE_URL}/channels/{self._channel_id}/messages"
        headers = {"Authorization": f"Bot {self._token}"}
        params: dict = {"limit": min(limit, 100)}
        if since:
            params["after"] = since

        try:
            async with network._make_async_client() as client:
                resp = await client.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                raw_messages = resp.json()

            result: list[IncomingMessage] = []
            for msg in reversed(raw_messages):  # Discord returns newest-first; reverse
                author = msg.get("author") or {}
                is_bot = author.get("bot", False)

                ref = msg.get("message_reference") or {}
                msg_thread_id = ref.get("message_id")

                if thread_id is not None and msg_thread_id != thread_id:
                    continue

                result.append(
                    IncomingMessage(
                        text=msg.get("content", ""),
                        sender=author.get("username", "unknown"),
                        sender_id=author.get("id", ""),
                        timestamp=msg.get("id", ""),  # Snowflake — monotonically increasing
                        platform="discord",
                        is_bot=is_bot,
                        thread_id=msg_thread_id,
                        raw=msg,
                    )
                )
            return result
        except httpx.HTTPStatusError as e:
            log.error(f"Discord fetch_messages error {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            log.error(f"Discord fetch_messages error: {e}")
            return []

    async def close(self) -> None:
        pass
