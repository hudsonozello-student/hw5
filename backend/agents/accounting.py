"""Accounting: watches cash and invoices, checks margins, and files payments and POs for human approval."""

from backend.agents.base import make_agent
from backend.models import SpecialistReport

MCP_TOOLS = frozenset({
    "get_ticket", "get_cash_balance", "get_invoice", "list_open_invoices", "check_margin",
    "check_vendor_status", "request_payment", "create_purchase_order", "list_approvals",
})

agent = make_agent("accounting", SpecialistReport, MCP_TOOLS)
