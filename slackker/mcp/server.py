"""Define the slackker MCP server and register tools."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable, cast

from slackker.core import BaseClient
from slackker.mcp.config import (
    MCPConfig,
    build_arg_parser,
    build_connected_client,
    load_config_from_args,
)
from slackker.mcp.handler import MCPHandler
from slackker.utils.logger import log


@dataclass
class SlackkerMCPApp:
    """Store runtime objects for a configured MCP app."""

    mcp: Any
    client: BaseClient
    handler: MCPHandler
    tools: dict[str, Any]


def _load_fastmcp_class():
    """Import the FastMCP class lazily."""
    try:
        module = importlib.import_module("mcp.server.fastmcp")
        FastMCP = getattr(module, "FastMCP")
    except Exception as exc:  # pragma: no cover - import path depends on optional extra
        raise RuntimeError(
            "MCP SDK is not installed. Install with: pip install 'slackker[mcp]'"
        ) from exc
    return FastMCP


def register_tools(mcp: Any, handler: MCPHandler, client: BaseClient) -> dict[str, Any]:
    """Register MCP tools for notifications, approvals, and status reads."""
    tools: dict[str, Any] = {}

    @mcp.tool()
    async def notify(
        event: str | None = None,
        attachment: str = "",
        **kwargs,
    ) -> str:
        """Send a notification event with optional key-value metadata and attachment."""
        await handler.async_notify(event=event, attachment=attachment or None, **kwargs)
        return f"Notification '{event or 'update'}' sent."

    @mcp.tool()
    async def ask(
        question: str,
        timeout: float = 300.0,
        halt_on: str = "no",
    ) -> str:
        """Ask a question and return ``"continue"`` or ``"halt"``."""
        approved = await handler.async_ask(question, timeout=timeout, halt_on=halt_on)
        return "continue" if approved else "halt"

    @mcp.tool()
    async def get_messages(count: int = 10) -> list[dict[str, str]]:
        """Fetch recent channel messages."""
        messages = await client.fetch_messages(limit=count)
        return [
            {
                "sender": m.sender,
                "text": m.text,
                "time": m.timestamp,
            }
            for m in messages
        ]

    @mcp.tool()
    async def get_status() -> dict[str, object]:
        """Get connection and listener status."""
        return await handler.async_get_status()

    tools["notify"] = notify
    tools["ask"] = ask
    tools["get_messages"] = get_messages
    tools["get_status"] = get_status

    return tools


def _register_optional_resources(
    mcp: Any,
    handler: MCPHandler,
    client: BaseClient,
) -> None:
    """Register optional MCP resources when supported by the runtime."""
    resource = getattr(mcp, "resource", None)
    if not callable(resource):
        return

    resource_decorator = cast(Callable[[str], Any], resource)

    try:

        @resource_decorator("slackker://status")
        async def status_resource() -> dict[str, object]:
            return await handler.async_get_status()

        @resource_decorator("slackker://messages/recent")
        async def recent_messages_resource() -> list[dict[str, str]]:
            messages = await client.fetch_messages(limit=10)
            return [
                {
                    "sender": m.sender,
                    "text": m.text,
                    "time": m.timestamp,
                }
                for m in messages
            ]

    except Exception as exc:  # pragma: no cover - depends on optional SDK behavior
        log.debug(f"FastMCP resources not registered (unsupported API variant): {exc}")


def create_app(
    config: MCPConfig,
    *,
    client: BaseClient | None = None,
    fastmcp_cls: type | None = None,
) -> SlackkerMCPApp:
    """Create and configure a slackker MCP app."""
    resolved_client = client or build_connected_client(config)
    handler = MCPHandler(resolved_client, poll_interval=config.poll_interval)

    FastMCP = fastmcp_cls or _load_fastmcp_class()
    mcp = FastMCP("slackker")

    tools = register_tools(mcp=mcp, handler=handler, client=resolved_client)
    _register_optional_resources(mcp=mcp, handler=handler, client=resolved_client)

    return SlackkerMCPApp(
        mcp=mcp,
        client=resolved_client,
        handler=handler,
        tools=tools,
    )


def _run_mcp(mcp: Any) -> None:
    """Run the MCP server using stdio transport when supported."""
    run = getattr(mcp, "run", None)
    if not callable(run):
        raise RuntimeError("FastMCP instance does not expose a callable run() method.")

    try:
        result = run(transport="stdio")
    except TypeError:
        result = run()

    if inspect.iscoroutine(result):
        asyncio.run(result)
    elif inspect.isawaitable(result):

        async def _await_wrapper(awaitable):
            return await awaitable

        asyncio.run(_await_wrapper(result))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for ``slackker-mcp``."""
    parser = build_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the ``slackker-mcp`` command-line entry point."""
    args = parse_args(argv)
    config = load_config_from_args(args)
    app = create_app(config)

    try:
        _run_mcp(app.mcp)
    except KeyboardInterrupt:
        log.info("MCP server interrupted by user.")
    finally:
        app.handler.stop()


if __name__ == "__main__":
    main()
