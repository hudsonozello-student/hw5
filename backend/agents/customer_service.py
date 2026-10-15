"""Customer service: drafts messages for customers. Drafts stay on the board; nothing is ever sent."""

from backend.agents.base import make_agent
from backend.models import SpecialistReport

MCP_TOOLS = frozenset({"get_ticket", "save_draft"})

agent = make_agent("customer_service", SpecialistReport, MCP_TOOLS)
