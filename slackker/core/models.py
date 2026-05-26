from dataclasses import dataclass, field


@dataclass
class IncomingMessage:
    """Platform-agnostic representation of a message received from a messaging platform.

    Parameters
    ----------
    text : str
        Plain-text body of the message.
    sender : str
        Human-readable display name of the sender.
    sender_id : str
        Platform-specific unique user/bot identifier.
    timestamp : str
        Platform-native timestamp used as a pagination cursor for subsequent
        ``fetch_messages`` calls:

        - **Slack** – message ``ts`` (e.g. ``"1699000000.000100"``).
        - **Telegram** – ``update_id`` as a string (e.g. ``"500"``).
        - **Discord** – Snowflake message ID (e.g. ``"1234567890123456789"``).
        - **Teams** – ISO 8601 ``createdDateTime`` (e.g. ``"2024-01-01T10:00:00Z"``).
    platform : str
        Source platform name: ``"slack"``, ``"telegram"``, ``"discord"``, or ``"teams"``.
    is_bot : bool
        ``True`` if the message was sent by a bot or application.
    thread_id : str | None
        Platform-specific thread/reply anchor, if the message belongs to a thread:

        - **Slack** – ``thread_ts`` of the parent message.
        - **Telegram** – ``message_id`` (as str) of the message being replied to.
        - **Discord** – ``message_id`` of the message being replied to.
        - **Teams** – ``replyToId`` of the parent message.

        ``None`` if the message is not part of a thread.
    raw : dict
        Full platform API payload for advanced / platform-specific use.
    """

    text: str
    sender: str
    sender_id: str
    timestamp: str
    platform: str
    is_bot: bool
    thread_id: str | None = None
    raw: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        snippet = self.text[:50] + ("…" if len(self.text) > 50 else "")
        return (
            f"IncomingMessage(platform={self.platform!r}, sender={self.sender!r}, "
            f"text={snippet!r}, thread_id={self.thread_id!r})"
        )
