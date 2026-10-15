"""The five Campus Customs agents, one module per role."""

from backend.agents import accounting, boss, customer_service, facilities, inventory

AGENTS = {
    "boss": boss.agent,
    "inventory": inventory.agent,
    "accounting": accounting.agent,
    "facilities": facilities.agent,
    "customer_service": customer_service.agent,
}

MCP_TOOLS_BY_AGENT = {
    "boss": boss.MCP_TOOLS,
    "inventory": inventory.MCP_TOOLS,
    "accounting": accounting.MCP_TOOLS,
    "facilities": facilities.MCP_TOOLS,
    "customer_service": customer_service.MCP_TOOLS,
}
