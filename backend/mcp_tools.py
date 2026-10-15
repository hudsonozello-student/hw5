"""The team's only door to shop data: the campus-customs MCP server, started over stdio.

Every agent reaches the database through one shared MCP connection, each with
its own allowlist of tools. There is no other shop-tools layer.
"""

import os
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.client.stdio import get_default_environment
from pydantic_ai import RunContext
from pydantic_ai.mcp import CallToolFunc, MCPToolset
from pydantic_ai.toolsets import FilteredToolset

from backend.config import HW5_DIR, mcp_server_command
from backend.models import TeamDeps

# Only a person may call these (through the approval desk), so no agent allowlist may contain them.
HUMAN_ONLY_TOOLS = frozenset({"approve_request", "reject_request"})
# Write tools that record who asked. The backend fills `actor` from the run, so a model cannot sign as someone else.
ACTOR_TOOLS = frozenset({"request_payment", "create_purchase_order", "save_draft", "update_ticket"})


def _transport() -> StdioTransport:
    command, args = mcp_server_command()
    # A minimal environment: the MCP server never sees PORTKEY_API_KEY or other secrets.
    env = get_default_environment()
    if "CAMPUS_CUSTOMS_DB" in os.environ:  # test runs point at a scratch copy
        env["CAMPUS_CUSTOMS_DB"] = os.environ["CAMPUS_CUSTOMS_DB"]
    return StdioTransport(command=command, args=args, env=env, cwd=str(HW5_DIR))


async def _stamp_actor(ctx: RunContext[TeamDeps], call_tool: CallToolFunc, name: str, args: dict[str, Any]) -> Any:
    if name in HUMAN_ONLY_TOOLS:  # unreachable through the allowlists; kept as a second lock
        raise PermissionError(f"{name} is for humans only.")
    if name in ACTOR_TOOLS:
        args = {**args, "actor": ctx.deps.agent}
    return await call_tool(name, args)


# One MCP server process, shared by every agent working a ticket.
SHOP = MCPToolset(Client(_transport()), id="campus-customs", process_tool_call=_stamp_actor, max_retries=1)


def tools_for(allowed: frozenset[str]) -> FilteredToolset[TeamDeps]:
    """The slice of the MCP server one agent may use."""
    if allowed & HUMAN_ONLY_TOOLS:
        raise ValueError(f"Agents may not hold human-only tools: {sorted(allowed & HUMAN_ONLY_TOOLS)}")
    return SHOP.filtered(lambda ctx, tool_def: tool_def.name in allowed)


# The human desk's own connection (dashboard reads, approvals). The API keeps it open for its
# lifetime; the CLI opens it per command. Agents never use it.
DESK = Client(_transport())


async def human_desk_call(name: str, args: dict[str, Any]) -> dict:
    """Call an MCP tool for the human desk, outside any agent run."""
    async with DESK:  # re-entrant: reuses the open session when the API holds one
        return (await DESK.call_tool(name, args, raise_on_error=False)).data
