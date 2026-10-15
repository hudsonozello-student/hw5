"""Boss: reads each ticket, decides who works on it, and makes the final call."""

from backend.agents.base import make_agent
from backend.models import TicketDecision

MCP_TOOLS = frozenset({"list_tickets", "get_ticket", "update_ticket", "get_cash_balance", "list_approvals"})

agent = make_agent("boss", TicketDecision, MCP_TOOLS)
