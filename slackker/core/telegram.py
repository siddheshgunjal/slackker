import os
import httpx
from slackker.core.client import BaseClient
from slackker.utils.logger import log
from slackker.utils import network


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
    def chat_id(self) -> str | None:
        return self._chat_id

    async def connect(self) -> bool:
        """Verify server connectivity and discover chat_id if not provided."""
        server = await network.check_connection(url="www.telegram.org", verbose=self._verbose)
        if not server:
            return False

        if not self._chat_id:
            self._chat_id = await network.get_telegram_chat_id(
                token=self._token, verbose=self._verbose
            )

        return self._chat_id is not None

    async def send_message(self, text: str) -> None:
        if not self._chat_id:
            log.error("chat_id is not set. Call `await client.connect()` before sending messages.")
            return
        url = f"{self._base_url}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params={"chat_id": self._chat_id, "text": text})
                response.raise_for_status()
            if self._verbose >= 1:
                log.debug("Posted update on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error posting update: {e}")

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        if not self._chat_id:
            log.error("chat_id is not set. Call `await client.connect()` before uploading files.")
            return
        url = f"{self._base_url}/sendDocument"
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            caption = comment or "Attachment 📎"
            async with httpx.AsyncClient() as client:
                with open(filepath, "rb") as f:
                    response = await client.post(
                        url,
                        params={"chat_id": self._chat_id, "caption": caption},
                        files={"document": f},
                    )
                    response.raise_for_status()
            if self._verbose >= 1:
                log.debug("Uploaded attachment on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error uploading file: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        if not self._chat_id:
            log.error("chat_id is not set. Call `await client.connect()` before uploading images.")
            return
        url = f"{self._base_url}/sendPhoto"
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            caption = comment or "Attachment 📎"
            async with httpx.AsyncClient() as client:
                with open(filepath, "rb") as f:
                    response = await client.post(
                        url,
                        params={"chat_id": self._chat_id, "caption": caption},
                        files={"photo": f},
                    )
                    response.raise_for_status()
            if self._verbose >= 1:
                log.debug("Uploaded image on Telegram")
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            log.error(f"Error uploading image: {e}")
