import os
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from slackker.core.client import BaseClient
from slackker.utils.logger import log
from slackker.utils import network


class SlackClient(BaseClient):
    """Slack client backend using the async Slack SDK."""

    def __init__(self, token: str, channel: str, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not token:
            raise ValueError("Slack API token is required.")
        self._token = token
        self._channel = channel
        self._client = AsyncWebClient(token=token)
        self._connected = False

    @property
    def platform(self) -> str:
        return "slack"

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """Verify server connectivity and API token. Returns True on success."""
        server = await network.check_connection(url="www.slack.com", verbose=self._verbose)
        api = await network.verify_slack_token(token=self._token, verbose=self._verbose)
        self._connected = server and api
        return self._connected

    async def send_message(self, text: str) -> None:
        try:
            await self._client.chat_postMessage(channel=self._channel, text=text)
            if self._verbose >= 1:
                log.info(f"Posted update on {self._channel} channel")
        except SlackApiError as e:
            log.error(f"Error posting update: {e}")

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            initial_comment = comment or "Attachment 📎"
            await self._client.files_upload_v2(
                channel=self._channel,
                file=filepath,
                initial_comment=initial_comment,
            )
            if self._verbose >= 1:
                log.debug(f"Uploaded attachment on {self._channel} channel")
        except SlackApiError as e:
            log.error(f"Error uploading attachment: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        # Slack handles images the same way as files
        await self.upload_file(filepath, comment)

    async def close(self) -> None:
        await self._client.close()
