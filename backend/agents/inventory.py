"""Inventory: checks stock by SKU and size, spots shortfalls, and finds which vendor can restock."""

from backend.agents.base import make_agent
from backend.models import SpecialistReport

MCP_TOOLS = frozenset({"get_ticket", "check_stock", "check_vendor_status"})

agent = make_agent("inventory", SpecialistReport, MCP_TOOLS)
