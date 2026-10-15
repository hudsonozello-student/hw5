"""Campus Customs MCP server.

Shared tool belt for every agent on the Campus Customs team (boss, inventory,
accounting, facilities, customer service) and for the human approval desk.
Every tool works on the working copy data/campus_customs_new.db. The original
data/campus_customs.db is never opened, so it stays a clean reset point.

Tool groups
- Read tools report only what is in the database. Anything not on file comes
  back as found=False with an error instead of a guess.
- Agent write tools record payment requests, purchase orders, message drafts,
  and ticket notes. None of them moves money or contacts anyone.
- Human-only tools (tag "human_only") approve or reject a request. They are the
  only tools that move money, and the backend never gives them to an agent.

The first time a tool runs, the server adds four tables to the working copy
(approvals, purchase_orders, drafts, ticket_updates). Resetting the working
copy to the original removes them, and they come back empty on the next call.

Run (stdio transport):  .venv\\Scripts\\python.exe mcp_server\\server.py
"""

import calendar
import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

HW5_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_DB = (HW5_DIR / "data" / "campus_customs.db").resolve()
# CAMPUS_CUSTOMS_DB lets tests point at a scratch copy; it may never point at the original.
DB_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_DB", HW5_DIR / "data" / "campus_customs_new.db")).resolve()
if DB_PATH == ORIGINAL_DB:
    raise SystemExit("Refusing to open data/campus_customs.db: it is the untouched reset copy.")

AGENT_NAMES = {"boss", "inventory", "accounting", "facilities", "customer_service"}
CASH_ACCOUNT = "checking"

mcp = FastMCP(
    "campus-customs",
    instructions=(
        "Tools for the Campus Customs shop at Yale SOM. All data comes from the "
        "shop database; desk.date_today is the shop's 'today'. Never fill in "
        "values the tools did not return. Agents can request payments but only "
        "a human can approve them, and nothing is ever sent to customers or vendors."
    ),
)

READ_ONLY = {"readOnlyHint": True, "openWorldHint": False}
AGENT_WRITE = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
HUMAN_ONLY = {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False}

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,              -- invoice | rent | purchase_order
    ref_id INTEGER NOT NULL,         -- invoices.id | leases.id | purchase_orders.id
    amount REAL NOT NULL,
    ticket_id INTEGER REFERENCES tickets(id),
    reason TEXT NOT NULL,
    requested_by TEXT NOT NULL,      -- agent that asked
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | rejected
    decided_by TEXT,                 -- human who decided
    decision_note TEXT,
    payment_id INTEGER REFERENCES payments(id),
    shop_date TEXT NOT NULL,         -- desk.date_today when requested
    created_at TEXT NOT NULL,        -- real UTC time, for the audit trail
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id),
    sku TEXT NOT NULL,
    size TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    total REAL NOT NULL,
    ticket_id INTEGER REFERENCES tickets(id),
    status TEXT NOT NULL DEFAULT 'pending_approval',  -- pending_approval | ordered | rejected
    expected_arrival TEXT NOT NULL,  -- shop date + vendor lead_days
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    audience TEXT NOT NULL,          -- customer | vendor | landlord
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',     -- drafts are never sent by the system
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_updates (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    author TEXT NOT NULL,            -- agent name, or human:<name>
    old_status TEXT,
    new_status TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


# ---------------------------------------------------------------- helpers

DESK_TABLES = {"approvals", "purchase_orders", "drafts", "ticket_updates"}


def _connect(write: bool = False) -> sqlite3.Connection:
    """Open the working copy (read-only unless write=True); fail loudly if it is missing."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Working database not found at {DB_PATH}. "
            "Copy data/campus_customs.db to data/campus_customs_new.db first."
        )
    _ensure_schema()
    return _open(write)


def _open(write: bool) -> sqlite3.Connection:
    if write:
        con = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
        con.execute("PRAGMA foreign_keys = ON")
    else:
        con = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    return con


@contextmanager
def _transaction():
    """One all-or-nothing write; any error rolls back so no change is half-made."""
    con = _connect(write=True)
    try:
        con.execute("BEGIN IMMEDIATE")
        yield con
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def _ensure_schema() -> None:
    """Add the desk tables if they are missing (first use, or after the working copy was reset)."""
    with closing(_open(write=False)) as con:
        have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not DESK_TABLES <= have:
        with closing(_open(write=True)) as con:
            con.executescript(SCHEMA)


def _shop_today(con: sqlite3.Connection) -> str:
    """The shop's 'today' from desk.date_today (not the real calendar date)."""
    return con.execute("SELECT date_today FROM desk").fetchone()["date_today"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rows(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def _add_days(day: str, days: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=days)).isoformat()


def _add_month(day: str) -> str:
    d = date.fromisoformat(day)
    year, month = d.year + d.month // 12, d.month % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1])).isoformat()


def _invoice_view(row: dict, today: str) -> dict:
    """An invoice plus how it stands against the shop's today."""
    days_past_due = (date.fromisoformat(today) - date.fromisoformat(row["due_date"])).days
    return {**row, "is_overdue": row["status"] != "paid" and days_past_due > 0,
            "days_overdue": max(days_past_due, 0)}


def _unpaid_invoices(con: sqlite3.Connection, today: str, vendor_id: int | None = None) -> list[dict]:
    sql = (
        "SELECT i.id, i.vendor_id, v.name AS vendor, i.amount, i.due_date, i.status, i.description "
        "FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.status != 'paid'"
    )
    params: tuple = ()
    if vendor_id is not None:
        sql += " AND i.vendor_id = ?"
        params = (vendor_id,)
    return [_invoice_view(r, today) for r in _rows(con, sql + " ORDER BY i.due_date", params)]


def _cash(con: sqlite3.Connection) -> dict:
    """Cash on hand, and what is left once every pending request is paid."""
    acct = con.execute(
        "SELECT name, balance, date FROM cash_accounts WHERE name = ?", (CASH_ACCOUNT,)
    ).fetchone()
    pending = con.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS n FROM approvals WHERE status = 'pending'"
    ).fetchone()
    return {
        "account": acct["name"],
        "balance": acct["balance"],
        "as_of": acct["date"],
        "pending_requests": pending["n"],
        "pending_total": round(pending["total"], 2),
        "available_after_pending": round(acct["balance"] - pending["total"], 2),
    }


def _hold_message(unpaid: list[dict]) -> str:
    parts = [
        f"invoice {i['id']} (${i['amount']:,.2f}, due {i['due_date']}"
        + (f", {i['days_overdue']} days overdue)" if i["is_overdue"] else ")")
        for i in unpaid
    ]
    return f"{unpaid[0]['vendor']} cannot ship new product until it is paid: " + "; ".join(parts) + "."


def _is_human_name(name: str) -> bool:
    cleaned = name.strip().lower()
    return bool(cleaned) and cleaned not in AGENT_NAMES | {"unknown", "agent", "system"}


# ---------------------------------------------------------------- read tools

@mcp.tool(annotations=READ_ONLY)
def list_tickets(status: str = "open") -> dict:
    """List desk tickets. status="open" (default) lists open tickets; status="all" lists every ticket.

    Each row has the ticket id, type, requester, subject, any SKU/size/qty, and the
    linked lease_id or invoice_id. Call get_ticket for the full ticket and its history.
    """
    with closing(_connect()) as con:
        sql = ("SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, status, created_at "
               "FROM tickets")
        rows = _rows(con, sql + " ORDER BY id") if status == "all" else \
            _rows(con, sql + " WHERE status = ? ORDER BY id", (status,))
        return {"shop_today": _shop_today(con), "count": len(rows), "tickets": rows}


@mcp.tool(annotations=READ_ONLY)
def get_ticket(ticket_id: int) -> dict:
    """Read one ticket in full: the request, its linked lease/invoice ids, and everything the team has done on it.

    Returns the tickets row, its status history (ticket_updates), and any payment
    requests (approvals), purchase orders, and message drafts already filed for it,
    so work is not repeated.
    """
    with closing(_connect()) as con:
        ticket = con.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if ticket is None:
            return {"found": False, "error": f"Ticket {ticket_id} is not in the tickets table."}
        return {
            "found": True,
            "shop_today": _shop_today(con),
            "ticket": dict(ticket),
            "history": _rows(con, "SELECT author, old_status, new_status, note FROM ticket_updates "
                                  "WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
            "approvals": _rows(con, "SELECT id, kind, ref_id, amount, status, requested_by, decided_by "
                                    "FROM approvals WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
            "purchase_orders": _rows(con, "SELECT id, vendor_id, sku, size, qty, total, status, expected_arrival "
                                          "FROM purchase_orders WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
            "drafts": _rows(con, "SELECT id, audience, recipient, subject, body, created_by "
                                 "FROM drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
        }


@mcp.tool(annotations=READ_ONLY)
def check_stock(sku: str, size: str | None = None, qty_needed: int | None = None) -> dict:
    """Check on-hand stock for a SKU in the inventory table.

    Stock is tracked per size, so pass `size` (e.g. "S", "M", "L", "XL", or "OS"
    for one-size items) to check one size; leave it out to list every size of
    the SKU. Pass `qty_needed` (e.g. a ticket's qty) to get the shortfall and
    whether the order can be filled from the shelf right now.
    """
    sku = sku.strip().upper()
    if qty_needed is not None and qty_needed < 1:
        return {"found": False, "error": "qty_needed must be 1 or more."}

    with closing(_connect()) as con:
        rows = con.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? ORDER BY rowid",
            (sku,),
        ).fetchall()

    if not rows:
        return {"found": False, "error": f"SKU {sku} is not in the inventory table."}
    sizes = [dict(r) for r in rows]

    if size is None:
        return {"found": True, "sku": sku, "name": sizes[0]["name"], "sizes": sizes}

    size = size.strip().upper()
    match = next((r for r in sizes if r["size"] == size), None)
    if match is None:
        return {
            "found": False,
            "error": f"SKU {sku} has no size {size} in the inventory table.",
            "sizes_on_file": [r["size"] for r in sizes],
        }

    result = {"found": True, **match, "other_sizes": [r for r in sizes if r["size"] != size]}
    if qty_needed is not None:
        shortfall = max(qty_needed - match["qty"], 0)
        result.update(qty_needed=qty_needed, shortfall=shortfall, can_fill_now=shortfall == 0)
    return result


@mcp.tool(annotations=READ_ONLY)
def check_vendor_status(vendor_id: int | None = None) -> dict:
    """Check which vendors can ship right now, what they make, and how long they take.

    For each vendor (or just `vendor_id`): specialty, lead_days, any unpaid
    invoices, can_ship (False while any invoice is unpaid: a vendor with an open
    unpaid invoice cannot ship new product), and the arrival date if an order
    were placed today (shop date + lead_days). Lead times come only from the
    vendors table.
    """
    with closing(_connect()) as con:
        today = _shop_today(con)
        sql = "SELECT id, name, specialty, lead_days FROM vendors"
        vendors = _rows(con, sql + " WHERE id = ?", (vendor_id,)) if vendor_id is not None else \
            _rows(con, sql + " ORDER BY id")
        if not vendors:
            return {"found": False, "error": f"Vendor {vendor_id} is not in the vendors table."}
        out = []
        for v in vendors:
            unpaid = _unpaid_invoices(con, today, v["id"])
            out.append({
                **v,
                "can_ship": not unpaid,
                "unpaid_invoices": unpaid,
                "hold_reason": _hold_message(unpaid) if unpaid else None,
                "arrival_if_ordered_today": _add_days(today, v["lead_days"]),
            })
        return {"found": True, "shop_today": today, "vendors": out}


@mcp.tool(annotations=READ_ONLY)
def get_invoice(invoice_id: int) -> dict:
    """Read one vendor invoice: vendor, amount, due date, status, and whether it is overdue.

    Overdue is measured against desk.date_today. Also shows any payment request
    already waiting for human approval on this invoice.
    """
    with closing(_connect()) as con:
        today = _shop_today(con)
        row = con.execute(
            "SELECT i.id, i.vendor_id, v.name AS vendor, v.lead_days, i.amount, i.due_date, i.status, "
            "i.description FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?",
            (invoice_id,),
        ).fetchone()
        if row is None:
            return {"found": False, "error": f"Invoice {invoice_id} is not in the invoices table."}
        pending = _rows(con, "SELECT id, amount, requested_by FROM approvals "
                             "WHERE kind = 'invoice' AND ref_id = ? AND status = 'pending'", (invoice_id,))
        return {"found": True, "shop_today": today, **_invoice_view(dict(row), today),
                "pending_payment_request": pending[0] if pending else None}


@mcp.tool(annotations=READ_ONLY)
def list_open_invoices() -> dict:
    """List every unpaid vendor invoice with its amount, due date, and days overdue (vs desk.date_today)."""
    with closing(_connect()) as con:
        today = _shop_today(con)
        unpaid = _unpaid_invoices(con, today)
        return {"shop_today": today, "count": len(unpaid),
                "total_unpaid": round(sum(i["amount"] for i in unpaid), 2), "invoices": unpaid}


@mcp.tool(annotations=READ_ONLY)
def get_cash_balance() -> dict:
    """Show cash in the checking account and how much is already promised to pending requests.

    available_after_pending = balance minus every payment request still waiting
    for a human. The shop has no revenue, so cash only goes down, and it may
    never go below zero. Also lists pending requests and the five latest payments.
    """
    with closing(_connect()) as con:
        return {
            "shop_today": _shop_today(con),
            **_cash(con),
            "pending": _rows(con, "SELECT id, kind, ref_id, amount, ticket_id, requested_by FROM approvals "
                                  "WHERE status = 'pending' ORDER BY id"),
            "recent_payments": _rows(con, "SELECT id, kind, ref_id, amount, paid_at, approved_by "
                                          "FROM payments ORDER BY id DESC LIMIT 5"),
        }


@mcp.tool(annotations=READ_ONLY)
def get_lease(lease_id: int) -> dict:
    """Look up a shop lease: space, landlord, monthly rent, and when rent is next due.

    Also returns days_until_due and is_overdue, counted from desk.date_today
    (the shop's 'today'), so a rent notice can be checked against the lease on
    file. This tool only reads; it does not pay rent.
    """
    with closing(_connect()) as con:
        row = con.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        today = _shop_today(con)

    if row is None:
        return {"found": False, "error": f"Lease {lease_id} is not in the leases table."}

    days_until_due = (date.fromisoformat(row["next_due"]) - date.fromisoformat(today)).days
    return {
        "found": True,
        **dict(row),
        "shop_today": today,
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
    }


@mcp.tool(annotations=READ_ONLY)
def check_margin(sku: str, qty: int = 1, discount_pct: float = 0.0) -> dict:
    """Work out the margin on selling `qty` units of a SKU, optionally at a discount.

    Uses unit_cost and list_price from the pricing table. `discount_pct` is percent
    off list price (15 means 15% off). Returns per-unit and total margin plus the
    break-even discount (the discount at which the price equals unit cost). This
    is for judging a price or discount request only: the shop does not model
    revenue, so no cash is added by a sale.
    """
    sku = sku.strip().upper()
    if qty < 1:
        return {"found": False, "error": "qty must be 1 or more."}
    if not 0 <= discount_pct <= 100:
        return {"found": False, "error": "discount_pct must be between 0 and 100."}

    with closing(_connect()) as con:
        row = con.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()

    if row is None:
        return {"found": False, "error": f"SKU {sku} is not in the pricing table."}

    unit_cost, list_price = row["unit_cost"], row["list_price"]
    unit_price = round(list_price * (1 - discount_pct / 100), 2)
    unit_margin = round(unit_price - unit_cost, 2)
    return {
        "found": True,
        "sku": sku,
        "qty": qty,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "discount_pct": discount_pct,
        "unit_price": unit_price,
        "unit_margin": unit_margin,
        "margin_pct": round(unit_margin / unit_price * 100, 1) if unit_price else None,
        "order_total": round(unit_price * qty, 2),
        "order_cost": round(unit_cost * qty, 2),
        "order_margin": round(unit_margin * qty, 2),
        "break_even_discount_pct": round((1 - unit_cost / list_price) * 100, 1),
        "below_cost": unit_margin < 0,
    }


@mcp.tool(annotations=READ_ONLY)
def list_approvals(status: str = "pending") -> dict:
    """List payment requests. status="pending" (default) shows those waiting for a human; "all" shows every one."""
    with closing(_connect()) as con:
        sql = ("SELECT id, kind, ref_id, amount, ticket_id, reason, requested_by, status, decided_by, "
               "decision_note, payment_id, shop_date FROM approvals")
        rows = _rows(con, sql + " ORDER BY id") if status == "all" else \
            _rows(con, sql + " WHERE status = ? ORDER BY id", (status,))
        return {"count": len(rows), "approvals": rows, **_cash(con)}


@mcp.tool(annotations=READ_ONLY)
def list_drafts(ticket_id: int | None = None) -> dict:
    """List message drafts on the board, newest first, optionally for one ticket. Drafts are never sent."""
    with closing(_connect()) as con:
        sql = "SELECT id, ticket_id, audience, recipient, subject, body, status, created_by, created_at FROM drafts"
        rows = _rows(con, sql + " ORDER BY id DESC") if ticket_id is None else \
            _rows(con, sql + " WHERE ticket_id = ? ORDER BY id DESC", (ticket_id,))
        return {"count": len(rows), "drafts": rows}


# ---------------------------------------------------------------- agent write tools (no money moves)

@mcp.tool(annotations=AGENT_WRITE)
def request_payment(kind: Literal["invoice", "rent"], ref_id: int, reason: str,
                    ticket_id: int | None = None, actor: str = "unknown") -> dict:
    """Ask a human to approve paying a vendor invoice (kind="invoice", ref_id=invoices.id) or rent (kind="rent", ref_id=leases.id).

    The amount always comes from the database (invoice amount or monthly_rent),
    never from the caller. This only files a request: NO money moves until a
    human approves it. Refused if the invoice is already paid, a request for the
    same item is already pending, or cash left after all pending requests cannot
    cover it (cash may never go negative). `actor` is filled in by the system.
    """
    with _transaction() as con:
        if kind == "invoice":
            inv = con.execute("SELECT i.*, v.name AS vendor FROM invoices i JOIN vendors v ON v.id = i.vendor_id "
                              "WHERE i.id = ?", (ref_id,)).fetchone()
            if inv is None:
                return {"ok": False, "error": f"Invoice {ref_id} is not in the invoices table."}
            if inv["status"] == "paid":
                return {"ok": False, "error": f"Invoice {ref_id} is already paid."}
            amount = inv["amount"]
            what = f"Invoice {ref_id} from {inv['vendor']}: {inv['description']} (due {inv['due_date']})"
        else:
            lease = con.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if lease is None:
                return {"ok": False, "error": f"Lease {ref_id} is not in the leases table."}
            amount = lease["monthly_rent"]
            what = f"Rent for {lease['space_name']} to {lease['landlord']} (due {lease['next_due']})"

        dup = con.execute("SELECT id FROM approvals WHERE kind = ? AND ref_id = ? AND status = 'pending'",
                          (kind, ref_id)).fetchone()
        if dup:
            return {"ok": False, "approval_id": dup["id"],
                    "error": f"Request #{dup['id']} for this {kind} is already waiting for a human."}

        cash = _cash(con)
        if amount > cash["available_after_pending"]:
            return {"ok": False, "refused": "not_enough_cash", "amount": amount, "cash": cash,
                    "error": (f"Refused: ${amount:,.2f} is more than the ${cash['available_after_pending']:,.2f} "
                              "left after pending requests. Cash cannot go negative.")}

        cur = con.execute(
            "INSERT INTO approvals (kind, ref_id, amount, ticket_id, reason, requested_by, shop_date, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, ticket_id, reason, actor, _shop_today(con), _now()),
        )
        return {"ok": True, "approval_id": cur.lastrowid, "status": "pending", "kind": kind, "ref_id": ref_id,
                "amount": amount, "description": what,
                "cash_left_if_approved": round(cash["available_after_pending"] - amount, 2),
                "note": "Waiting for a human to approve. No money has moved."}


@mcp.tool(annotations=AGENT_WRITE)
def create_purchase_order(vendor_id: int, sku: str, size: str, qty: int, reason: str,
                          ticket_id: int | None = None, actor: str = "unknown") -> dict:
    """Prepare a restock purchase order and file it for human approval.

    Cost = pricing.unit_cost x qty; arrival = shop date + the vendor's lead_days.
    Approving the PO pays the vendor, so it goes into the same human approval
    queue as other payments. Refused if the vendor has any unpaid invoice (they
    cannot ship new product), the SKU/size is unknown, the same restock is
    already pending, or cash left after pending requests cannot cover it.
    `actor` is filled in by the system.
    """
    sku, size = sku.strip().upper(), size.strip().upper()
    if qty < 1:
        return {"ok": False, "error": "qty must be 1 or more."}
    with _transaction() as con:
        today = _shop_today(con)
        vendor = con.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if vendor is None:
            return {"ok": False, "error": f"Vendor {vendor_id} is not in the vendors table."}
        if con.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
            return {"ok": False, "error": f"{sku} size {size} is not in the inventory table."}
        price = con.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
        if price is None:
            return {"ok": False, "error": f"SKU {sku} is not in the pricing table."}

        unpaid = _unpaid_invoices(con, today, vendor_id)
        if unpaid:
            return {"ok": False, "refused": "vendor_on_hold", "unpaid_invoices": unpaid,
                    "error": "Refused: " + _hold_message(unpaid)
                             + " Request payment of the invoice first (request_payment kind='invoice')."}

        dup = con.execute("SELECT id FROM purchase_orders WHERE vendor_id = ? AND sku = ? AND size = ? "
                          "AND status = 'pending_approval'", (vendor_id, sku, size)).fetchone()
        if dup:
            return {"ok": False, "purchase_order_id": dup["id"],
                    "error": f"PO #{dup['id']} for {sku} {size} is already waiting for a human."}

        total = round(price["unit_cost"] * qty, 2)
        cash = _cash(con)
        if total > cash["available_after_pending"]:
            return {"ok": False, "refused": "not_enough_cash", "amount": total, "cash": cash,
                    "error": (f"Refused: ${total:,.2f} is more than the ${cash['available_after_pending']:,.2f} "
                              "left after pending requests. Cash cannot go negative.")}

        arrival = _add_days(today, vendor["lead_days"])
        po = con.execute(
            "INSERT INTO purchase_orders (vendor_id, sku, size, qty, unit_cost, total, ticket_id, expected_arrival, "
            "created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (vendor_id, sku, size, qty, price["unit_cost"], total, ticket_id, arrival, actor, _now()),
        ).lastrowid
        approval = con.execute(
            "INSERT INTO approvals (kind, ref_id, amount, ticket_id, reason, requested_by, shop_date, created_at) "
            "VALUES ('purchase_order', ?, ?, ?, ?, ?, ?, ?)",
            (po, total, ticket_id, reason, actor, today, _now()),
        ).lastrowid
        return {"ok": True, "purchase_order_id": po, "approval_id": approval, "status": "pending_approval",
                "vendor": vendor["name"], "sku": sku, "size": size, "qty": qty, "unit_cost": price["unit_cost"],
                "total": total, "expected_arrival_if_approved_today": arrival,
                "cash_left_if_approved": round(cash["available_after_pending"] - total, 2),
                "note": "Waiting for a human to approve. Nothing has been ordered or paid."}


@mcp.tool(annotations=AGENT_WRITE)
def save_draft(audience: Literal["customer", "vendor", "landlord"], recipient: str, subject: str, body: str,
               ticket_id: int | None = None, actor: str = "unknown") -> dict:
    """Save a message draft on the board for a human to review. It is NEVER sent: the system cannot email or call anyone.

    `actor` is filled in by the system.
    """
    if not (recipient.strip() and subject.strip() and body.strip()):
        return {"ok": False, "error": "recipient, subject, and body are all required."}
    with _transaction() as con:
        draft = con.execute(
            "INSERT INTO drafts (ticket_id, audience, recipient, subject, body, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, audience, recipient.strip(), subject.strip(), body.strip(), actor, _now()),
        ).lastrowid
        return {"ok": True, "draft_id": draft, "status": "draft",
                "note": "Saved on the board as a draft. Nothing was sent."}


@mcp.tool(annotations=AGENT_WRITE)
def update_ticket(ticket_id: int, status: Literal["open", "in_progress", "waiting_approval", "resolved", "declined"],
                  note: str, actor: str = "unknown") -> dict:
    """Set a ticket's status and add a note to its history (the original request text is kept).

    Use waiting_approval while any payment request for the ticket is pending; a
    ticket cannot be marked resolved until those are decided. `actor` is filled
    in by the system.
    """
    if not note.strip():
        return {"ok": False, "error": "A note explaining the update is required."}
    with _transaction() as con:
        ticket = con.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if ticket is None:
            return {"ok": False, "error": f"Ticket {ticket_id} is not in the tickets table."}
        pending = _rows(con, "SELECT id, kind, amount FROM approvals WHERE ticket_id = ? AND status = 'pending'",
                        (ticket_id,))
        if status == "resolved" and pending:
            return {"ok": False, "pending_approvals": pending,
                    "error": "Refused: payment requests for this ticket are still waiting for a human. "
                             "Use status='waiting_approval'."}
        con.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        con.execute("INSERT INTO ticket_updates (ticket_id, author, old_status, new_status, note, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)", (ticket_id, actor, ticket["status"], status, note.strip(), _now()))
        return {"ok": True, "ticket_id": ticket_id, "old_status": ticket["status"], "new_status": status}


# ---------------------------------------------------------------- human-only tools (the only way money moves)

@mcp.tool(annotations=HUMAN_ONLY, tags={"human_only"})
def approve_request(approval_id: int, approved_by: str) -> dict:
    """HUMAN ONLY. Approve a pending request and make the payment.

    Re-checks everything at the moment of payment and refuses (changing nothing)
    if cash would go negative, the invoice is no longer open, or the vendor is on
    hold. On success, in one transaction: adds a payments row, lowers the cash
    balance, marks the invoice paid / moves the lease's next_due forward one
    month / marks the PO ordered, and records who approved it.
    """
    if not _is_human_name(approved_by):
        return {"ok": False, "error": "approved_by must be the name of the human approver, not an agent."}
    approver = approved_by.strip()
    with _transaction() as con:
        today = _shop_today(con)
        req = con.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        if req is None:
            return {"ok": False, "error": f"Request {approval_id} is not in the approvals table."}
        if req["status"] != "pending":
            return {"ok": False, "error": f"Request {approval_id} is already {req['status']}."}

        balance = con.execute("SELECT balance FROM cash_accounts WHERE name = ?", (CASH_ACCOUNT,)).fetchone()["balance"]
        if req["amount"] > balance:
            return {"ok": False, "refused": "not_enough_cash",
                    "error": f"Refused: paying ${req['amount']:,.2f} would overdraw {CASH_ACCOUNT} "
                             f"(balance ${balance:,.2f}). Nothing was paid."}

        kind, ref = req["kind"], req["ref_id"]
        if kind == "invoice":
            inv = con.execute("SELECT status FROM invoices WHERE id = ?", (ref,)).fetchone()
            if inv is None or inv["status"] == "paid":
                return {"ok": False, "error": f"Invoice {ref} is missing or already paid. Nothing was paid."}
            con.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref,))
            change = f"invoice {ref} marked paid"
        elif kind == "rent":
            lease = con.execute("SELECT next_due FROM leases WHERE id = ?", (ref,)).fetchone()
            new_due = _add_month(lease["next_due"])
            con.execute("UPDATE leases SET next_due = ? WHERE id = ?", (new_due, ref))
            change = f"lease {ref} next_due moved from {lease['next_due']} to {new_due}"
        else:
            po = con.execute("SELECT * FROM purchase_orders WHERE id = ?", (ref,)).fetchone()
            unpaid = _unpaid_invoices(con, today, po["vendor_id"])
            if unpaid:
                return {"ok": False, "refused": "vendor_on_hold",
                        "error": "Refused: " + _hold_message(unpaid) + " Nothing was paid."}
            lead = con.execute("SELECT lead_days FROM vendors WHERE id = ?", (po["vendor_id"],)).fetchone()["lead_days"]
            arrival = _add_days(today, lead)
            con.execute("UPDATE purchase_orders SET status = 'ordered', expected_arrival = ? WHERE id = ?",
                        (arrival, ref))
            change = f"PO {ref} ordered, expected {arrival}"

        payment = con.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref, req["amount"], CASH_ACCOUNT, today, approver),
        ).lastrowid
        new_balance = round(balance - req["amount"], 2)
        con.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?", (new_balance, today, CASH_ACCOUNT))
        con.execute("UPDATE approvals SET status = 'approved', decided_by = ?, decided_at = ?, payment_id = ? "
                    "WHERE id = ?", (approver, _now(), payment, approval_id))
        if req["ticket_id"] is not None:
            status = con.execute("SELECT status FROM tickets WHERE id = ?", (req["ticket_id"],)).fetchone()["status"]
            con.execute("INSERT INTO ticket_updates (ticket_id, author, old_status, new_status, note, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (req["ticket_id"], f"human:{approver}", status, status,
                         f"Approved request #{approval_id}: paid ${req['amount']:,.2f}; {change}.", _now()))
        return {"ok": True, "approval_id": approval_id, "payment_id": payment, "paid": req["amount"],
                "kind": kind, "ref_id": ref, "change": change, "new_balance": new_balance, "approved_by": approver}


@mcp.tool(annotations=HUMAN_ONLY, tags={"human_only"})
def reject_request(approval_id: int, rejected_by: str, reason: str) -> dict:
    """HUMAN ONLY. Reject a pending request. No money moves; a rejected PO is cancelled."""
    if not _is_human_name(rejected_by):
        return {"ok": False, "error": "rejected_by must be the name of the human approver, not an agent."}
    rejecter = rejected_by.strip()
    with _transaction() as con:
        req = con.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        if req is None:
            return {"ok": False, "error": f"Request {approval_id} is not in the approvals table."}
        if req["status"] != "pending":
            return {"ok": False, "error": f"Request {approval_id} is already {req['status']}."}
        con.execute("UPDATE approvals SET status = 'rejected', decided_by = ?, decision_note = ?, decided_at = ? "
                    "WHERE id = ?", (rejecter, reason, _now(), approval_id))
        if req["kind"] == "purchase_order":
            con.execute("UPDATE purchase_orders SET status = 'rejected' WHERE id = ?", (req["ref_id"],))
        if req["ticket_id"] is not None:
            status = con.execute("SELECT status FROM tickets WHERE id = ?", (req["ticket_id"],)).fetchone()["status"]
            con.execute("INSERT INTO ticket_updates (ticket_id, author, old_status, new_status, note, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (req["ticket_id"], f"human:{rejecter}", status, status,
                         f"Rejected request #{approval_id}: {reason}", _now()))
        return {"ok": True, "approval_id": approval_id, "status": "rejected", "rejected_by": rejecter}


if __name__ == "__main__":
    mcp.run(show_banner=False)
