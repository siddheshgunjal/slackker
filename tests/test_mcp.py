"""Tests for slackker.mcp config, handler, and server tools."""

from __future__ import annotations

import argparse
import importlib.util
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from slackker.core.client import BaseClient
from slackker.core.models import IncomingMessage
from slackker.mcp import config as mcp_config_module
from slackker.mcp import server as mcp_server_module
from slackker.mcp.config import (
    MCPConfig,
    build_arg_parser,
    build_client,
    build_connected_client,
    load_config,
    load_config_file,
    load_config_from_args,
    load_env_config,
)
from slackker.mcp.handler import MCPHandler
from slackker.mcp.server import (
    _load_fastmcp_class,
    _register_optional_resources,
    _run_mcp,
    create_app,
    main,
    parse_args,
    register_tools,
)


class MockClient(BaseClient):
    """Concrete test client for MCP tests."""

    def __init__(self, messages: list[IncomingMessage] | None = None):
        super().__init__(verbose=0)
        self._connected = True
        self.connect_calls = 0

        self.sent_messages: list[str] = []
        self.uploaded_files: list[tuple[str, str | None]] = []

        self.fetch_messages_calls: list[dict] = []
        self._messages = messages or []

    @property
    def platform(self) -> str:
        return "mock"

    @property
    def connectivity_url(self) -> str:
        return "mock.example.com"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        self.connect_calls += 1
        self._connected = True
        return True

    async def send_message(self, text: str) -> None:
        self.sent_messages.append(text)

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        self.uploaded_files.append((filepath, comment))

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        self.uploaded_files.append((filepath, comment))

    async def fetch_messages(self, limit=10, since=None, thread_id=None):
        self.fetch_messages_calls.append(
            {"limit": limit, "since": since, "thread_id": thread_id}
        )
        return list(self._messages)[:limit]


class DisconnectedMockClient(MockClient):
    def __init__(self):
        super().__init__()
        self._connected = False


class NonConnectableDisconnectedClient(BaseClient):
    """Disconnected client with no connect() method (for guard-path testing)."""

    def __init__(self):
        super().__init__(verbose=0)
        self._connected = False

    @property
    def platform(self) -> str:
        return "mock"

    @property
    def connectivity_url(self) -> str:
        return "mock.example.com"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def send_message(self, text: str) -> None:
        return None

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        return None

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        return None


class MockPoller:
    def __init__(self, reply: IncomingMessage | None = None):
        self._reply = reply

    async def wait_for_reply(self, timeout=300.0):
        return self._reply


def _msg(text="hi", sender="alice", timestamp="1") -> IncomingMessage:
    return IncomingMessage(
        text=text,
        sender=sender,
        sender_id="U1",
        timestamp=timestamp,
        platform="mock",
        is_bot=False,
    )


def _patch_listener(handler: MCPHandler, reply: IncomingMessage | None = None):
    listener = MagicMock()
    listener.poller = MockPoller(reply=reply)
    listener.stop = AsyncMock()
    listener.is_running = True
    handler._listener = listener
    return listener


# ── MCPHandler tests ─────────────────────────────────────────────────────────


class TestMCPHandler:
    def test_init_connects_if_client_disconnected(self):
        client = DisconnectedMockClient()
        assert client.is_connected is False

        MCPHandler(client)

        assert client.connect_calls == 1
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_async_notify_sends_message(self):
        client = MockClient()
        handler = MCPHandler(client)

        await handler.async_notify("pipeline_done", rows=42)

        assert len(client.sent_messages) == 1
        assert "pipeline_done" in client.sent_messages[0]
        assert "rows: 42" in client.sent_messages[0]

    @pytest.mark.asyncio
    async def test_async_notify_uploads_attachment(self):
        client = MockClient()
        handler = MCPHandler(client)

        await handler.async_notify("done", attachment="/tmp/out.txt", score=0.9)

        assert len(client.uploaded_files) == 1
        filepath, comment = client.uploaded_files[0]
        assert filepath == "/tmp/out.txt"
        assert comment is not None
        assert "done" in comment

    @pytest.mark.asyncio
    async def test_async_ask_halt_reply(self):
        client = MockClient()
        handler = MCPHandler(client)
        _patch_listener(handler, reply=_msg(text="no", sender="bob"))

        approved = await handler.async_ask("Continue?", timeout=10.0)

        assert approved is False
        assert any("🛑" in text and "bob" in text for text in client.sent_messages)

    @pytest.mark.asyncio
    async def test_async_ask_timeout_auto_approves(self):
        client = MockClient()
        handler = MCPHandler(client)
        _patch_listener(handler, reply=None)

        approved = await handler.async_ask("Continue?", timeout=5.0)

        assert approved is True
        assert any("timeout" in text for text in client.sent_messages)

    @pytest.mark.asyncio
    async def test_ensure_listener_lazy_init(self):
        client = MockClient()
        handler = MCPHandler(client)
        assert handler._listener is None

        mock_listener = MagicMock()
        mock_listener.start = AsyncMock()

        with patch("slackker.listener.CommandHandler", return_value=mock_listener) as p:
            await handler._ensure_listener()

        assert handler._listener is mock_listener
        p.assert_called_once()
        mock_listener.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_stop_clears_listener(self):
        client = MockClient()
        handler = MCPHandler(client)
        listener = _patch_listener(handler)

        await handler.async_stop()

        assert handler._listener is None
        listener.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_get_status(self):
        client = MockClient()
        handler = MCPHandler(client)

        status = await handler.async_get_status()

        assert status["connected"] is True
        assert status["platform"] == "mock"
        assert status["listener_active"] is False

    def test_sync_ask_and_stop(self):
        client = MockClient()
        handler = MCPHandler(client)
        _patch_listener(handler, reply=_msg(text="yes", sender="alice"))

        assert handler.ask("Proceed?") is True
        assert handler._sync_loop is not None

        handler.stop()
        assert handler._sync_loop is None

    def test_notify_sync_wrapper(self):
        client = MockClient()
        handler = MCPHandler(client)

        handler.notify("checkpoint", score=0.8)

        assert any("checkpoint" in text for text in client.sent_messages)

        handler.stop()

    def test_get_status_sync_wrapper(self):
        client = MockClient()
        handler = MCPHandler(client)

        status = handler.get_status()

        assert status["connected"] is True
        assert status["platform"] == "mock"

        handler.stop()

    def test_stop_without_sync_loop_uses_async_stop(self):
        client = MockClient()
        handler = MCPHandler(client)
        listener = _patch_listener(handler)

        handler.stop()

        assert handler._listener is None
        listener.stop.assert_awaited_once()


# ── Config tests ─────────────────────────────────────────────────────────────


class TestMCPConfig:
    def test_load_from_env_slack(self, monkeypatch):
        monkeypatch.setenv("SLACKKER_PLATFORM", "slack")
        monkeypatch.setenv("SLACKKER_TOKEN", "xoxb-test")
        monkeypatch.setenv("SLACKKER_CHANNEL", "C123")
        monkeypatch.setenv("SLACKKER_POLL_INTERVAL", "3.5")

        config = load_config()

        assert config.platform == "slack"
        assert config.token == "xoxb-test"
        assert config.resolved_channel_id == "C123"
        assert config.poll_interval == 3.5

    def test_file_and_cli_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SLACKKER_PLATFORM", "slack")
        monkeypatch.setenv("SLACKKER_TOKEN", "env-token")
        monkeypatch.setenv("SLACKKER_CHANNEL", "CENV")

        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(
            '{"platform":"slack","token":"file-token","channel":"CFILE","poll_interval":9.0}'
        )

        config = load_config(
            config_path=config_file,
            cli_overrides={"token": "cli-token", "poll_interval": 2.0},
        )

        assert config.token == "cli-token"  # CLI wins
        assert config.resolved_channel_id == "CFILE"  # file wins over env
        assert config.poll_interval == 2.0  # CLI wins

    def test_missing_required_values_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_TOKEN"):
            load_config(
                cli_overrides={
                    "platform": "slack",
                    "channel": "C123",
                }
            )

    def test_build_connected_client_calls_connect_when_needed(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "slack",
                "token": "xoxb-test",
                "channel": "C123",
            }
        )

        disconnected_client = DisconnectedMockClient()

        with patch(
            "slackker.mcp.config.build_client", return_value=disconnected_client
        ):
            client = build_connected_client(config)

        assert client is disconnected_client
        assert disconnected_client.connect_calls == 1

    def test_validate_invalid_platform_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_PLATFORM"):
            MCPConfig.from_mapping({"platform": "unknown"})

    def test_validate_poll_interval_non_positive_raises(self):
        with pytest.raises(ValueError, match="poll_interval"):
            MCPConfig.from_mapping(
                {
                    "platform": "telegram",
                    "token": "123:ABC",
                    "poll_interval": 0,
                }
            )

    def test_validate_verbose_out_of_range_raises(self):
        with pytest.raises(ValueError, match="verbose"):
            MCPConfig.from_mapping(
                {
                    "platform": "telegram",
                    "token": "123:ABC",
                    "verbose": 99,
                }
            )

    def test_validate_slack_missing_channel_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_CHANNEL"):
            MCPConfig.from_mapping(
                {
                    "platform": "slack",
                    "token": "xoxb-test",
                }
            )

    def test_validate_discord_missing_channel_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_CHANNEL_ID"):
            MCPConfig.from_mapping(
                {
                    "platform": "discord",
                    "token": "Bot-token",
                }
            )

    def test_validate_teams_missing_app_id_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_APP_ID"):
            MCPConfig.from_mapping(
                {
                    "platform": "teams",
                    "chat_id": "19:abc@thread.v2",
                }
            )

    def test_validate_teams_missing_chat_id_raises(self):
        with pytest.raises(ValueError, match="SLACKKER_CHAT_ID"):
            MCPConfig.from_mapping(
                {
                    "platform": "teams",
                    "app_id": "app-id",
                }
            )

    def test_to_dict_roundtrip(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "999",
                "poll_interval": 1.5,
                "verbose": 1,
            }
        )

        data = config.to_dict()

        assert data["platform"] == "telegram"
        assert data["chat_id"] == "999"
        assert data["poll_interval"] == 1.5

    def test_load_env_config_strips_and_drops_empty(self, monkeypatch):
        monkeypatch.setenv("SLACKKER_PLATFORM", " slack ")
        monkeypatch.setenv("SLACKKER_TOKEN", "  ")
        monkeypatch.setenv("SLACKKER_CHANNEL", " C123 ")

        env = load_env_config()

        assert env["platform"] == "slack"
        assert env["channel"] == "C123"
        assert "token" not in env

    def test_load_config_file_not_found_raises(self, tmp_path):
        missing = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_config_file(missing)

    def test_load_config_file_non_object_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps([1, 2, 3]))

        with pytest.raises(ValueError, match="JSON object"):
            load_config_file(p)

    def test_load_config_invalid_poll_interval_type_raises(self):
        with pytest.raises(ValueError, match="poll_interval must be a float"):
            load_config(
                cli_overrides={
                    "platform": "telegram",
                    "token": "123:ABC",
                    "poll_interval": "abc",
                }
            )

    def test_load_config_invalid_verbose_type_raises(self):
        with pytest.raises(ValueError, match="verbose must be an int"):
            load_config(
                cli_overrides={
                    "platform": "telegram",
                    "token": "123:ABC",
                    "verbose": "loud",
                }
            )

    def test_build_arg_parser_and_parse_args(self):
        parser = build_arg_parser()
        args = parser.parse_args(
            [
                "--platform",
                "slack",
                "--token",
                "xoxb-1",
                "--channel",
                "C123",
                "--poll-interval",
                "1.25",
                "--verbose",
                "2",
            ]
        )

        assert args.platform == "slack"
        assert args.token == "xoxb-1"
        assert args.channel == "C123"
        assert args.poll_interval == 1.25
        assert args.verbose == 2

    def test_load_config_from_args_uses_config_and_overrides(self, tmp_path):
        p = tmp_path / "cfg.json"
        p.write_text(
            json.dumps(
                {
                    "platform": "slack",
                    "token": "file-token",
                    "channel": "CFILE",
                    "poll_interval": 5.0,
                }
            )
        )

        args = argparse.Namespace(
            config=str(p),
            platform=None,
            token="cli-token",
            channel=None,
            channel_id=None,
            chat_id=None,
            app_id=None,
            tenant_id=None,
            teams_token_cache_path=None,
            poll_interval=2.5,
            verbose=None,
        )

        cfg = load_config_from_args(args)
        assert cfg.token == "cli-token"
        assert cfg.resolved_channel_id == "CFILE"
        assert cfg.poll_interval == 2.5

    def test_build_client_for_each_platform(self):
        slack_cfg = MCPConfig.from_mapping(
            {"platform": "slack", "token": "x", "channel": "C1"}
        )
        telegram_cfg = MCPConfig.from_mapping(
            {"platform": "telegram", "token": "123:ABC", "chat_id": "7"}
        )
        discord_cfg = MCPConfig.from_mapping(
            {"platform": "discord", "token": "Bot-t", "channel_id": "D1"}
        )
        teams_cfg = MCPConfig.from_mapping(
            {
                "platform": "teams",
                "app_id": "app-id",
                "chat_id": "19:abc@thread.v2",
            }
        )

        with patch.object(
            mcp_config_module, "SlackClient", return_value="slack_client"
        ) as p_slack:
            assert build_client(slack_cfg) == "slack_client"
            p_slack.assert_called_once()

        with patch.object(
            mcp_config_module, "TelegramClient", return_value="tg_client"
        ) as p_tg:
            assert build_client(telegram_cfg) == "tg_client"
            p_tg.assert_called_once()

        with patch.object(
            mcp_config_module, "DiscordClient", return_value="disc_client"
        ) as p_disc:
            assert build_client(discord_cfg) == "disc_client"
            p_disc.assert_called_once()

        with patch.object(
            mcp_config_module, "TeamsClient", return_value="teams_client"
        ) as p_teams:
            assert build_client(teams_cfg) == "teams_client"
            p_teams.assert_called_once()

    def test_build_client_unknown_platform_raises(self):
        cfg = MCPConfig(platform="unknown")
        with pytest.raises(ValueError, match="Unsupported platform"):
            build_client(cfg)

    def test_build_connected_client_does_not_connect_when_already_connected(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "99",
            }
        )
        client = MockClient()

        with patch("slackker.mcp.config.build_client", return_value=client):
            returned = build_connected_client(config)

        assert returned is client
        assert client.connect_calls == 0

    def test_build_connected_client_skips_when_connect_not_callable(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "99",
            }
        )
        client = NonConnectableDisconnectedClient()

        with patch("slackker.mcp.config.build_client", return_value=client):
            returned = build_connected_client(config)

        assert returned is client

    def test_build_connected_client_warns_when_connect_returns_false(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "slack",
                "token": "x",
                "channel": "C1",
            }
        )
        client = DisconnectedMockClient()
        client.connect = AsyncMock(return_value=False)

        with patch("slackker.mcp.config.build_client", return_value=client):
            with patch.object(mcp_config_module.log, "warning") as warn:
                returned = build_connected_client(config)

        assert returned is client
        warn.assert_called_once()

    def test_build_connected_client_warns_when_connect_raises(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "slack",
                "token": "x",
                "channel": "C1",
            }
        )
        client = DisconnectedMockClient()
        client.connect = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("slackker.mcp.config.build_client", return_value=client):
            with patch.object(mcp_config_module.log, "warning") as warn:
                returned = build_connected_client(config)

        assert returned is client
        warn.assert_called_once()


# ── MCP server tool tests ────────────────────────────────────────────────────


class FakeFastMCP:
    """Minimal FastMCP stand-in for unit testing tool registration."""

    def __init__(self, name: str):
        self.name = name
        self.tools: dict[str, object] = {}
        self.resources: dict[str, object] = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator

    def resource(self, uri: str):
        def decorator(fn):
            self.resources[uri] = fn
            return fn

        return decorator

    def run(self, transport=None):
        return None


class TestMCPServerTools:
    @pytest.mark.asyncio
    async def test_register_tools_notify_ask_get_messages_get_status(self):
        client = MockClient(
            messages=[_msg(text="hello", sender="alice", timestamp="100")]
        )

        handler = MagicMock(spec=MCPHandler)
        handler.async_notify = AsyncMock()
        handler.async_ask = AsyncMock(return_value=True)
        handler.async_get_status = AsyncMock(
            return_value={
                "connected": True,
                "platform": "mock",
                "listener_active": False,
            }
        )

        mcp = FakeFastMCP("slackker")
        tools = register_tools(mcp=mcp, handler=handler, client=client)

        notify_result = await tools["notify"]("done", attachment="/tmp/a.txt", x=1)
        handler.async_notify.assert_awaited_once_with(
            event="done",
            attachment="/tmp/a.txt",
            x=1,
        )
        assert "done" in notify_result

        ask_result = await tools["ask"]("Proceed?")
        handler.async_ask.assert_awaited_once_with(
            "Proceed?",
            timeout=300.0,
            halt_on="no",
        )
        assert ask_result == "continue"

        messages = await tools["get_messages"](count=1)
        assert messages == [{"sender": "alice", "text": "hello", "time": "100"}]
        assert client.fetch_messages_calls[-1]["limit"] == 1

        status = await tools["get_status"]()
        assert status["connected"] is True
        assert status["platform"] == "mock"

    @pytest.mark.asyncio
    async def test_ask_tool_returns_halt(self):
        client = MockClient()
        handler = MagicMock(spec=MCPHandler)
        handler.async_notify = AsyncMock()
        handler.async_ask = AsyncMock(return_value=False)
        handler.async_get_status = AsyncMock(return_value={})

        tools = register_tools(FakeFastMCP("slackker"), handler=handler, client=client)

        result = await tools["ask"]("Deploy?")
        assert result == "halt"

    def test_create_app_with_fake_fastmcp(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "99",
                "poll_interval": 1.5,
            }
        )
        client = MockClient()

        app = create_app(config=config, client=client, fastmcp_cls=FakeFastMCP)

        assert app.mcp.name == "slackker"
        assert app.client is client
        assert set(app.tools.keys()) == {"notify", "ask", "get_messages", "get_status"}
        assert "slackker://status" in app.mcp.resources
        assert "slackker://messages/recent" in app.mcp.resources


class TestMCPServerRuntime:
    def test_load_fastmcp_class_success(self):
        fake_module = SimpleNamespace(FastMCP=FakeFastMCP)
        with patch("importlib.import_module", return_value=fake_module):
            fastmcp_cls = _load_fastmcp_class()

        assert fastmcp_cls is FakeFastMCP

    def test_load_fastmcp_class_error(self):
        with patch("importlib.import_module", side_effect=ImportError("nope")):
            with pytest.raises(
                RuntimeError, match=r"Install with: pip install 'slackker\[mcp\]'"
            ):
                _load_fastmcp_class()

    @pytest.mark.asyncio
    async def test_register_tools_notify_default_event_and_blank_attachment(self):
        client = MockClient()
        handler = MagicMock(spec=MCPHandler)
        handler.async_notify = AsyncMock()
        handler.async_ask = AsyncMock(return_value=True)
        handler.async_get_status = AsyncMock(return_value={})

        tools = register_tools(FakeFastMCP("slackker"), handler=handler, client=client)
        result = await tools["notify"](attachment="")

        handler.async_notify.assert_awaited_once_with(event=None, attachment=None)
        assert "update" in result

    @pytest.mark.asyncio
    async def test_optional_resources_handlers_execute(self):
        mcp = FakeFastMCP("slackker")
        client = MockClient(messages=[_msg(text="hi", sender="eve", timestamp="77")])

        handler = MagicMock(spec=MCPHandler)
        handler.async_get_status = AsyncMock(return_value={"connected": True})

        _register_optional_resources(mcp=mcp, handler=handler, client=client)

        assert "slackker://status" in mcp.resources
        assert "slackker://messages/recent" in mcp.resources

        status = await mcp.resources["slackker://status"]()
        messages = await mcp.resources["slackker://messages/recent"]()

        assert status == {"connected": True}
        assert messages == [{"sender": "eve", "text": "hi", "time": "77"}]

    def test_optional_resources_non_callable_resource_is_noop(self):
        mcp = SimpleNamespace(resource=None)
        handler = MagicMock(spec=MCPHandler)
        client = MockClient()

        _register_optional_resources(mcp=mcp, handler=handler, client=client)

    def test_optional_resources_exception_path_logs_debug(self):
        class BrokenMCP:
            def resource(self, uri: str):
                raise RuntimeError("broken resource registration")

        with patch.object(mcp_server_module.log, "debug") as debug:
            _register_optional_resources(
                mcp=BrokenMCP(),
                handler=MagicMock(spec=MCPHandler),
                client=MockClient(),
            )

        debug.assert_called_once()

    def test_create_app_uses_default_client_builder_and_fastmcp_loader(self):
        config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "42",
            }
        )
        client = MockClient()

        with patch(
            "slackker.mcp.server.build_connected_client", return_value=client
        ) as build_client_mock:
            with patch(
                "slackker.mcp.server._load_fastmcp_class", return_value=FakeFastMCP
            ) as loader:
                app = create_app(config=config)

        build_client_mock.assert_called_once_with(config)
        loader.assert_called_once()
        assert app.client is client
        assert app.mcp.name == "slackker"

    def test_run_mcp_raises_when_run_not_callable(self):
        with pytest.raises(RuntimeError, match="callable run"):
            _run_mcp(SimpleNamespace(run=None))

    def test_run_mcp_uses_transport_stdio(self):
        run = MagicMock(return_value=None)
        _run_mcp(SimpleNamespace(run=run))
        run.assert_called_once_with(transport="stdio")

    def test_run_mcp_fallback_when_transport_kw_not_supported(self):
        run = MagicMock(side_effect=[TypeError("no transport"), None])
        _run_mcp(SimpleNamespace(run=run))

        assert run.call_count == 2
        assert run.call_args_list[0].kwargs == {"transport": "stdio"}
        assert run.call_args_list[1].kwargs == {}

    def test_run_mcp_runs_coroutine_result(self):
        async def coro_result():
            return 1

        run = MagicMock(return_value=coro_result())
        _run_mcp(SimpleNamespace(run=run))

    def test_run_mcp_runs_generic_awaitable_result(self):
        class AwaitableOnly:
            def __await__(self):
                async def _inner():
                    return "ok"

                return _inner().__await__()

        run = MagicMock(return_value=AwaitableOnly())
        _run_mcp(SimpleNamespace(run=run))

    def test_parse_args_wrapper(self):
        args = parse_args(
            [
                "--platform",
                "slack",
                "--token",
                "xoxb-test",
                "--channel",
                "C123",
            ]
        )
        assert args.platform == "slack"
        assert args.token == "xoxb-test"
        assert args.channel == "C123"

    def test_main_runs_server_and_stops_handler(self):
        fake_args = argparse.Namespace()
        fake_config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "7",
            }
        )
        fake_handler = MagicMock()
        fake_app = SimpleNamespace(mcp=object(), handler=fake_handler)

        with patch("slackker.mcp.server.parse_args", return_value=fake_args):
            with patch(
                "slackker.mcp.server.load_config_from_args", return_value=fake_config
            ):
                with patch("slackker.mcp.server.create_app", return_value=fake_app):
                    with patch("slackker.mcp.server._run_mcp") as run_mcp:
                        main([])

        run_mcp.assert_called_once_with(fake_app.mcp)
        fake_handler.stop.assert_called_once()

    def test_main_handles_keyboard_interrupt_and_stops(self):
        fake_args = argparse.Namespace()
        fake_config = MCPConfig.from_mapping(
            {
                "platform": "telegram",
                "token": "123:ABC",
                "chat_id": "7",
            }
        )
        fake_handler = MagicMock()
        fake_app = SimpleNamespace(mcp=object(), handler=fake_handler)

        with patch("slackker.mcp.server.parse_args", return_value=fake_args):
            with patch(
                "slackker.mcp.server.load_config_from_args", return_value=fake_config
            ):
                with patch("slackker.mcp.server.create_app", return_value=fake_app):
                    with patch(
                        "slackker.mcp.server._run_mcp", side_effect=KeyboardInterrupt
                    ):
                        with patch.object(mcp_server_module.log, "info") as info:
                            main([])

        info.assert_called_once()
        fake_handler.stop.assert_called_once()


@pytest.mark.integration
@pytest.mark.skipif(
    importlib.util.find_spec("mcp") is None,
    reason="mcp SDK not installed",
)
def test_create_app_with_real_fastmcp_when_installed():
    """Light integration smoke test using real FastMCP when optional dep is present."""
    import importlib

    FastMCP = getattr(importlib.import_module("mcp.server.fastmcp"), "FastMCP")

    config = MCPConfig.from_mapping(
        {
            "platform": "telegram",
            "token": "123:ABC",
            "chat_id": "99",
        }
    )

    app = create_app(config=config, client=MockClient(), fastmcp_cls=FastMCP)
    assert app.mcp is not None
    assert "notify" in app.tools
