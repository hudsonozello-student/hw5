# Campus Customs MCP Server

## What it is for

This [FastMCP](https://gofastmcp.com) server is the shared tool belt for the whole Campus Customs agent team (boss, inventory, accounting, facilities, customer service) and for the human approval desk. Agents never touch the database directly. They call these tools, and the tools return only what is in the database. If something is not on file, a tool returns `found: false` (or `ok: false`) with an error instead of guessing.

## Database

- **Uses:** `data/campus_customs_new.db` (the working copy).
- **Never touches:** `data/campus_customs.db` (the original, kept as the reset point). The server refuses to start if pointed at it.
- **Adds on first use:** four tables in the working copy: `approvals` (payment requests waiting for a human), `purchase_orders`, `drafts` (message drafts on the board), and `ticket_updates` (ticket history).
- **Reset:** `POST /reset` on the backend (or copy `data/campus_customs.db` over `data/campus_customs_new.db`). This also removes the added tables, which come back empty on the next tool call.
- "Today" for the shop is `desk.date_today` (2026-08-31), not the real calendar date.
- Testing only: the environment variable `CAMPUS_CUSTOMS_DB` points the server at a scratch copy instead.

## Tools (17)

### Read tools (no changes to the database)

| Tool | Reads | What it returns |
|---|---|---|
| `list_tickets(status="open")` | `tickets`, `desk` | The open ticket queue, or every ticket with `status="all"` |
| `get_ticket(ticket_id)` | `tickets`, `ticket_updates`, `approvals`, `purchase_orders`, `drafts` | One ticket plus everything already filed for it |
| `check_stock(sku, size?, qty_needed?)` | `inventory` | On-hand qty and location, other sizes, shortfall, can it be filled now |
| `check_vendor_status(vendor_id?)` | `vendors`, `invoices`, `desk` | Specialty, lead_days, unpaid invoices, `can_ship`, arrival if ordered today |
| `get_invoice(invoice_id)` | `invoices`, `vendors`, `approvals` | Amount, due date, days overdue, any pending payment request |
| `list_open_invoices()` | `invoices`, `vendors` | Every unpaid invoice and the total |
| `get_cash_balance()` | `cash_accounts`, `approvals`, `payments` | Balance, pending requests, `available_after_pending`, recent payments |
| `get_lease(lease_id)` | `leases`, `desk` | Rent, landlord, `next_due`, `days_until_due`, `is_overdue` |
| `check_margin(sku, qty?, discount_pct?)` | `pricing` | Unit and order margin at a discount, break-even discount |
| `list_approvals(status="pending")` | `approvals`, `cash_accounts` | Payment requests by status |
| `list_drafts(ticket_id?)` | `drafts` | Message drafts on the board with full text (used by the dashboard, not by agents) |

### Agent write tools (record work; never move money or contact anyone)

| Tool | Writes | Guardrails |
|---|---|---|
| `request_payment(kind, ref_id, reason, ticket_id?)` | `approvals` | Amount comes from the invoice or lease; refused if already paid, already pending, or cash left after pending requests can't cover it |
| `create_purchase_order(vendor_id, sku, size, qty, reason, ticket_id?)` | `purchase_orders`, `approvals` | Cost = unit_cost × qty; refused while the vendor has any unpaid invoice, for an unknown SKU/size, if a duplicate is pending, or if cash can't cover it |
| `save_draft(audience, recipient, subject, body, ticket_id?)` | `drafts` | Saved on the board only; nothing is ever sent |
| `update_ticket(ticket_id, status, note)` | `tickets.status`, `ticket_updates` | Keeps the original request text; refuses `resolved` while payment requests are pending |

These tools also take an `actor` argument, which the backend fills with the calling agent's name so that every record shows who asked.

### Human-only tools (tag `human_only`; never given to an agent)

| Tool | Writes | What happens |
|---|---|---|
| `approve_request(approval_id, approved_by)` | `payments`, `cash_accounts`, `approvals`, `ticket_updates`, and `invoices` / `leases` / `purchase_orders` | Re-checks cash (never below zero) and vendor holds, then in one transaction: adds the payment, lowers the balance, and marks the invoice paid / moves the lease's `next_due` forward a month / marks the PO ordered |
| `reject_request(approval_id, rejected_by, reason)` | `approvals`, `purchase_orders`, `ticket_updates` | Nothing is paid; a rejected PO is cancelled |

`approved_by` / `rejected_by` must be a person's name; agent names are refused.

## Run

From the `Homework 5` folder, with the project `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe mcp_server\server.py
```

The server uses the stdio transport. The agent backend starts it automatically (see `backend/mcp_tools.py`), and the vibe coder starts it from `.mcp.json`, which runs `python mcp_server/server.py`. For that, open Claude Code in the `hw5` folder with the virtual environment active.
