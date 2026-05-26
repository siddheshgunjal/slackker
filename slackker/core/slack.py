import os

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from slackker.core.client import BaseClient
from slackker.core.models import IncomingMessage
from slackker.utils import network
from slackker.utils.logger import log


class SlackClient(BaseClient):
    """Slack client backend using the async Slack SDK."""

    def __init__(self, token: str, channel_id: str, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not token:
            raise ValueError("Slack API token is required.")
        self._token = token
        self._channel_id = channel_id
        self._client = AsyncWebClient(token=token)
        self._connected = False

    @property
    def platform(self) -> str:
        return "slack"

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def connectivity_url(self) -> str:
        return "api.slack.com"

    async def connect(self) -> bool:
        """Verify server connectivity and API token. Returns True on success."""
        server = await network.check_connection(url="api.slack.com")
        api = await network.verify_slack_token(token=self._token)
        self._connected = server and api
        return self._connected

    async def send_message(self, text: str) -> None:
        try:
            await self._client.chat_postMessage(channel=self._channel_id, text=text)
            log.info(f"Posted update on {self._channel_id} channel")
        except SlackApiError as e:
            log.error(f"Error posting update: {e}")

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        try:
            if not os.path.isfile(filepath):
                log.error(f"Invalid file path: {filepath}")
                return
            initial_comment = comment or "Attachment 📎"
            await self._client.files_upload_v2(
                channel=self._channel_id,
                file=filepath,
                initial_comment=initial_comment,
            )
            log.debug(f"Uploaded attachment on {self._channel_id} channel")
        except SlackApiError as e:
            log.error(f"Error uploading attachment: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        # Slack handles images the same way as files
        await self.upload_file(filepath, comment)

    async def fetch_messages(
        self,
        limit: int = 10,
        since: str | None = None,
        thread_id: str | None = None,
    ) -> list[IncomingMessage]:
        """Fetch messages from the Slack channel.

        When *thread_id* is provided, fetches replies via
        ``conversations.replies`` (skipping the parent message itself).
        Otherwise fetches channel history via ``conversations.history``.
        Messages are returned in chronological order (oldest first).
        """
        try:
            if thread_id:
                resp = await self._client.conversations_replies(
                    channel=self._channel_id,
                    ts=thread_id,
                    oldest=since,
                    limit=limit
                    + 1,  # +1 because the parent is always the first element
                )
                # conversations.replies is already chronological (oldest first);
                # skip index 0 which is always the parent message itself.
                raw_messages = (resp.get("messages") or [])[1:]
            else:
                resp = await self._client.conversations_history(
                    channel=self._channel_id,
                    oldest=since,
                    limit=limit,
                )
                # conversations.history returns newest-first; reverse to oldest-first.
                raw_messages = list(reversed(resp.get("messages") or []))

            result: list[IncomingMessage] = []
            for msg in raw_messages:
                is_bot = bool(msg.get("bot_id")) or msg.get("subtype") == "bot_message"
                result.append(
                    IncomingMessage(
                        text=msg.get("text", ""),
                        sender=msg.get("user") or msg.get("bot_id") or "unknown",
                        sender_id=msg.get("user") or msg.get("bot_id") or "",
                        timestamp=msg.get("ts", ""),
                        platform="slack",
                        is_bot=is_bot,
                        thread_id=msg.get("thread_ts"),
                        raw=msg,
                    )
                )
            return result
        except SlackApiError as e:
            log.error(f"Slack fetch_messages error: {e}")
            return []

    async def close(self) -> None:
        pass  # AsyncWebClient does not expose a close() method
