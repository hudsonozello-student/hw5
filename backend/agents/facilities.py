"""Facilities: the shop space side, checking leases and rent notices against the lease on file."""

from backend.agents.base import make_agent
from backend.models import SpecialistReport

MCP_TOOLS = frozenset({"get_ticket", "get_lease"})

agent = make_agent("facilities", SpecialistReport, MCP_TOOLS)
