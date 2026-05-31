"""Load MCP configuration and build platform clients."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from slackker.core import (
    BaseClient,
    DiscordClient,
    SlackClient,
    TeamsClient,
    TelegramClient,
)
from slackker.core.client import _run_sync
from slackker.utils.logger import log

_SUPPORTED_PLATFORMS = {"slack", "telegram", "discord", "teams"}


def _load_dotenv_values(dotenv_path: str | Path | None = None) -> dict[str, str]:
    """Read ``SLACKKER_*`` values from a local ``.env`` file."""
    path = Path(dotenv_path) if dotenv_path else Path(".env")
    if not path.is_file():
        return {}

    loaded: dict[str, str] = {}
    for key, value in dotenv_values(path).items():
        if not key or not key.startswith("SLACKKER_"):
            continue
        if value is None:
            continue
        loaded[key] = value

    return loaded


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _to_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a float, got {value!r}") from exc


def _to_int(value: Any, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an int, got {value!r}") from exc


@dataclass
class MCPConfig:
    """Store resolved configuration for ``slackker-mcp``."""

    platform: str
    token: str | None = None

    # Platform-specific channel identifiers
    channel_id: str | None = None  # Slack / Discord
    chat_id: str | None = None  # Telegram / Teams

    # Teams-specific auth config
    app_id: str | None = None
    tenant_id: str = "common"
    teams_token_cache_path: str | None = None

    # Runtime behavior
    poll_interval: float = 2.0
    verbose: int = 0

    def validate(self) -> None:
        self.platform = (self.platform or "").strip().lower()
        if self.platform not in _SUPPORTED_PLATFORMS:
            allowed = ", ".join(sorted(_SUPPORTED_PLATFORMS))
            raise ValueError(
                f"SLACKKER_PLATFORM must be one of: {allowed}. Got {self.platform!r}."
            )

        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be > 0.")

        if self.verbose not in (0, 1, 2):
            raise ValueError("verbose must be one of: 0, 1, 2.")

        if self.platform in {"slack", "telegram", "discord"} and not self.token:
            raise ValueError(
                "SLACKKER_TOKEN is required for slack, telegram, and discord platforms."
            )

        if self.platform == "slack" and not self.channel_id:
            raise ValueError("SLACKKER_CHANNEL_ID is required for Slack.")

        if self.platform == "discord" and not self.channel_id:
            raise ValueError("SLACKKER_CHANNEL_ID is required for Discord.")

        if self.platform == "teams":
            if not self.app_id:
                raise ValueError("SLACKKER_APP_ID is required for Teams platform.")
            if not self.chat_id:
                raise ValueError("SLACKKER_CHAT_ID is required for Teams platform.")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "MCPConfig":
        """Build and validate configuration from a mapping."""
        config = cls(
            platform=(data.get("platform") or data.get("SLACKKER_PLATFORM") or ""),
            token=_clean(data.get("token") or data.get("SLACKKER_TOKEN")),
            channel_id=_clean(
                data.get("channel_id") or data.get("SLACKKER_CHANNEL_ID")
            ),
            chat_id=_clean(data.get("chat_id") or data.get("SLACKKER_CHAT_ID")),
            app_id=_clean(data.get("app_id") or data.get("SLACKKER_APP_ID")),
            tenant_id=(
                _clean(data.get("tenant_id") or data.get("SLACKKER_TENANT_ID"))
                or "common"
            ),
            teams_token_cache_path=_clean(
                data.get("teams_token_cache_path")
                or data.get("SLACKKER_TEAMS_TOKEN_CACHE_PATH")
            ),
            poll_interval=_to_float(
                data.get("poll_interval")
                if data.get("poll_interval") is not None
                else data.get("SLACKKER_POLL_INTERVAL", 2.0),
                field_name="poll_interval",
            ),
            verbose=_to_int(
                data.get("verbose")
                if data.get("verbose") is not None
                else data.get("SLACKKER_VERBOSE", 0),
                field_name="verbose",
            ),
        )
        config.validate()
        return config

    def to_dict(self) -> dict[str, Any]:
        """Return configuration as a plain serializable dictionary."""
        return asdict(self)


def load_env_config(dotenv_path: str | Path | None = None) -> dict[str, Any]:
    """Read supported ``SLACKKER_*`` values from env with ``.env`` fallback.

    Resolution order inside this function:
    1) ``.env`` values (if file exists)
    2) process environment variables (override ``.env``)
    """
    dotenv_values = _load_dotenv_values(dotenv_path=dotenv_path)

    env: dict[str, str] = {}
    env.update(dotenv_values)
    env.update(
        {key: value for key, value in os.environ.items() if key.startswith("SLACKKER_")}
    )

    result: dict[str, Any] = {
        "platform": _clean(env.get("SLACKKER_PLATFORM")),
        "token": _clean(env.get("SLACKKER_TOKEN")),
        "channel_id": _clean(env.get("SLACKKER_CHANNEL_ID")),
        "chat_id": _clean(env.get("SLACKKER_CHAT_ID")),
        "app_id": _clean(env.get("SLACKKER_APP_ID")),
        "tenant_id": _clean(env.get("SLACKKER_TENANT_ID")),
        "teams_token_cache_path": _clean(env.get("SLACKKER_TEAMS_TOKEN_CACHE_PATH")),
        "poll_interval": _clean(env.get("SLACKKER_POLL_INTERVAL")),
        "verbose": _clean(env.get("SLACKKER_VERBOSE")),
    }
    return {k: v for k, v in result.items() if v is not None}


def load_config_file(path: str | Path) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object.")

    return data


def load_config(
    *,
    config_path: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> MCPConfig:
    """Load configuration from environment, file, and CLI overrides.

    Precedence (lowest to highest):
    1) environment variables
    2) config file
    3) CLI overrides
    """
    merged: dict[str, Any] = {}
    merged.update(load_env_config())

    if config_path:
        merged.update(load_config_file(config_path))

    if cli_overrides:
        merged.update({k: v for k, v in cli_overrides.items() if v is not None})

    return MCPConfig.from_mapping(merged)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for ``slackker-mcp``."""
    parser = argparse.ArgumentParser(
        prog="slackker-mcp",
        description="Run the slackker MCP server over stdio.",
    )

    parser.add_argument("--config", help="Path to JSON config file.")

    parser.add_argument("--platform", choices=sorted(_SUPPORTED_PLATFORMS))
    parser.add_argument("--token")
    parser.add_argument("--channel-id", help="Slack/Discord channel ID.")
    parser.add_argument("--chat-id", help="Telegram/Teams chat ID.")

    parser.add_argument("--app-id", help="Teams app_id (Azure client ID).")
    parser.add_argument("--tenant-id", default=None, help="Teams tenant ID.")
    parser.add_argument("--teams-token-cache-path")

    parser.add_argument("--poll-interval", type=float, default=None)
    parser.add_argument("--verbose", type=int, choices=[0, 1, 2], default=None)
    return parser


def load_config_from_args(args: argparse.Namespace) -> MCPConfig:
    """Resolve configuration from parsed CLI arguments."""
    overrides = vars(args).copy()
    config_path = overrides.pop("config", None)
    return load_config(config_path=config_path, cli_overrides=overrides)


def build_client(config: MCPConfig) -> BaseClient:
    """Build a platform client for the provided configuration."""
    if config.platform == "slack":
        return SlackClient(
            token=config.token or "",
            channel_id=config.channel_id or "",
            verbose=config.verbose,
        )

    if config.platform == "telegram":
        return TelegramClient(
            token=config.token or "",
            chat_id=config.chat_id,
            verbose=config.verbose,
        )

    if config.platform == "discord":
        return DiscordClient(
            token=config.token or "",
            channel_id=config.channel_id or "",
            verbose=config.verbose,
        )

    if config.platform == "teams":
        return TeamsClient(
            app_id=config.app_id or "",
            tenant_id=config.tenant_id,
            chat_id=config.chat_id or "",
            token_cache_path=config.teams_token_cache_path,
            verbose=config.verbose,
        )

    raise ValueError(f"Unsupported platform: {config.platform!r}")


def build_connected_client(config: MCPConfig) -> BaseClient:
    """Build a platform client and attempt an initial connection."""
    client = build_client(config)

    if not client.is_connected:
        connect = getattr(client, "connect", None)
        if callable(connect):
            try:
                connected = _run_sync(connect())
                if not connected:
                    log.warning(
                        f"MCP startup: failed to connect {config.platform} client. "
                        "Server will still start; tools may fail until connectivity is restored."
                    )
            except Exception as exc:
                log.warning(
                    f"MCP startup: error while connecting {config.platform} client: {exc}"
                )

    return client
