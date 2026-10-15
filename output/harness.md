# Campus Customs Multi-Agent Harness

Reference for the Campus Customs agent team (boss, inventory, accounting, facilities, customer service): the data, the MCP tools, the five agents, the API, the dashboard, and the safety rules. Built up over Problems 2–9.

- **Original database (read-only, reset source):** `data/campus_customs.db`
- **Working copy (the MCP server and backend read and write this one):** `data/campus_customs_new.db`
- **To reset:** press **Fresh start** on the board (`POST /reset`), or copy `data/campus_customs.db` over `data/campus_customs_new.db`.
- **Model:** `gpt-6-luna` through Portkey for every agent, and no other model anywhere.

**Contents:** [Database](#database-at-a-glance) · [Tables](#tables) · [Joins](#how-the-tables-join) · [The 3 tickets](#the-3-open-tickets) · [Desk tables](#desk-tables-added-by-the-mcp-server) · [MCP tools (P3)](#mcp-tools) · [Agent team](#agent-team-problem-5) · [MCP tools: full list](#mcp-tools-full-list-problem-5) · [SAFETY](#safety) · [Shop rules](#shop-rules-and-where-each-is-enforced) · [Backend routes](#backend-routes-problem-7) · [Dashboard](#dashboard-problem-8) · [Problem 9 results](#problem-9-run-resolving-the-tickets)

**Quick start** (from `Homework 5`, with the project `.venv`):

```powershell
cd backend; ..\.venv\Scripts\uvicorn main:app --reload --port 8000   # API at http://localhost:8000 (docs at /docs)
cd frontend; npm run dev                                            # board at http://localhost:5173
```

---

## Database at a glance

| Table | Rows | Key |
|---|---|---|
| `desk` | 1 | none (single row) |
| `tickets` | 3 | `id` |
| `inventory` | 10 | `(sku, size)` |
| `pricing` | 4 | `sku` |
| `vendors` | 3 | `id` |
| `invoices` | 1 | `id` → `vendors.id` |
| `leases` | 1 | `id` |
| `cash_accounts` | 1 | `name` |
| `payments` | 0 | `id` |
| `approvals` *(added by MCP)* | 0 | `id` |
| `purchase_orders` *(added by MCP)* | 0 | `id` → `vendors.id` |
| `drafts` *(added by MCP)* | 0 | `id` → `tickets.id` |
| `ticket_updates` *(added by MCP)* | 0 | `id` → `tickets.id` |

Starting state: shop "today" is **2026-08-31**, and `checking` holds **$3,400.00**. The last four tables don't exist in the original; the MCP server creates them empty the first time a tool runs ([details](#desk-tables-added-by-the-mcp-server)).

---

## Tables

### `desk`
Fields: `date_today` (TEXT, not null), `notes` (TEXT)

**Why it matters:** `date_today` is the shop's "today", so every overdue and due-soon check uses this date, never the real calendar.

### `tickets`
Fields: `id` (INTEGER, PK), `type` (TEXT), `requester` (TEXT), `subject` (TEXT), `sku` (TEXT), `size` (TEXT), `qty` (INTEGER), `lease_id` (INTEGER → `leases.id`), `invoice_id` (INTEGER → `invoices.id`), `status` (TEXT), `notes` (TEXT), `created_at` (TEXT, ISO timestamp)

**Why it matters:** This is the work queue. The boss reads each ticket and routes it, and its `sku`/`size`, `lease_id`, and `invoice_id` point to the other tables.

### `inventory`
Fields: `sku` (TEXT), `name` (TEXT), `size` (TEXT), `qty` (INTEGER), `location` (TEXT); PK is `(sku, size)`

**Why it matters:** The inventory agent checks stock here by SKU and size to find shortfalls (stock is tracked per size, so 8 M hoodies do not cover an order for L).

### `pricing`
Fields: `sku` (TEXT, PK), `unit_cost` (REAL), `list_price` (REAL)

**Why it matters:** Accounting computes margins here (list price minus unit cost) to judge discounts, and multiplies unit cost by quantity to price a restock PO.

### `vendors`
Fields: `id` (INTEGER, PK), `name` (TEXT), `specialty` (TEXT), `lead_days` (INTEGER)

**Why it matters:** Inventory decides who can restock an item from `specialty`, and gets restock timing from `lead_days` (lead times must come from this table).

### `invoices`
Fields: `id` (INTEGER, PK), `vendor_id` (INTEGER → `vendors.id`), `amount` (REAL), `due_date` (TEXT), `status` (TEXT), `description` (TEXT)

**Why it matters:** An `open` invoice blocks that vendor from shipping new product, and comparing `due_date` to `desk.date_today` shows what is overdue.

### `leases`
Fields: `id` (INTEGER, PK), `space_name` (TEXT), `landlord` (TEXT), `monthly_rent` (REAL), `next_due` (TEXT), `notes` (TEXT)

**Why it matters:** Facilities uses this for the shop space: how much rent is owed, to whom, and when (`next_due` should move forward a month once rent is paid).

### `cash_accounts`
Fields: `name` (TEXT, PK), `balance` (REAL), `date` (TEXT)

**Why it matters:** This is the only source of money. No revenue comes in, every payment draws it down, and the payment tool must refuse anything that would push `balance` below zero.

### `payments`
Fields: `id` (INTEGER, PK), `kind` (TEXT), `ref_id` (INTEGER), `amount` (REAL), `account` (TEXT), `paid_at` (TEXT), `approved_by` (TEXT, not null)

**Why it matters:** This is the record of money that went out. Every approved payment adds a row here, and `approved_by` (required) records which human approved it.

---

## How the tables join

| From | To | How |
|---|---|---|
| `tickets.invoice_id` | `invoices.id` | declared foreign key |
| `tickets.lease_id` | `leases.id` | declared foreign key |
| `invoices.vendor_id` | `vendors.id` | declared foreign key |
| `tickets.sku` + `tickets.size` | `inventory.sku` + `inventory.size` | matching values (no FK) |
| `tickets.sku` / `inventory.sku` | `pricing.sku` | matching values (no FK) |
| `payments.account` | `cash_accounts.name` | matching values (no FK) |
| `payments.ref_id` | `invoices.id` or `leases.id` | depends on `payments.kind` |
| SKU → vendor | `vendors.specialty` | inferred from text only: no table links SKUs to vendors |

---

## The 3 open tickets

All three were created on 2026-08-31, which is also the shop's `date_today`.

### Ticket 101: customer order (Tauhid Zaman, Bulldog tee)
- **Asks for:** 1 × `CC-TEE-WHITE`, size S.
- **inventory:** `CC-TEE-WHITE / S` has qty **0**, so the order is short 1 unit.
- **invoices:** linked to invoice **501**: Bulldog Print Co, **$840.00**, due 2026-08-28, status `open`, "Rush reprint CC-TEE-WHITE S". It is **3 days overdue**.
- **vendors:** Bulldog Print Co (id 1, apparel reprint, **5 lead days**) is the only apparel vendor, and it **cannot ship while invoice 501 is open**.
- **pricing:** tee unit cost $8.00, list price $28.00.
- **Agents involved:** inventory (shortfall), accounting (pay invoice 501, needs human approval), customer service (draft an update for Tauhid).

### Ticket 102: rent notice (Elm City Properties)
- **Asks for:** shop rent, due "in 2 days".
- **leases:** lease **1**: Chapel Street shop, landlord Elm City Properties, **$2,400.00**, `next_due` **2026-09-02**. Due in 2 days, not yet overdue.
- **Agents involved:** facilities (lease details), accounting (rent payment, needs human approval). After payment, `leases.next_due` should move to 2026-10-02.

### Ticket 103: price override (Yale AI Club, bulk hoodie discount)
- **Asks for:** 20 × `CC-HOOD-NAVY`, size M, at a bulk discount.
- **inventory:** `CC-HOOD-NAVY / M` has qty **8**, so the order is short **12** (other sizes on hand: S 4, L 14, XL 6).
- **pricing:** unit cost $22.00, list price $58.00, so the margin at list is $36.00/unit (62%). A 12-unit restock PO would cost **$264.00** at unit cost.
- **vendors:** a restock would also come from Bulldog Print Co (5 lead days), so it is **also blocked by open invoice 501**.
- **Agents involved:** accounting (margin check on the discount), inventory (shortfall and restock), boss (final call on the discount), customer service (draft a reply to the club).

### What the tickets share
- **Vendor bottleneck:** both stock shortfalls (tee S and hoodie M) need Bulldog Print Co, and both stay blocked until invoice 501 ($840) is paid.
- **Cash pressure:** $3,400 covers invoice 501 plus rent ($840 + $2,400 = $3,240, leaving $160). Adding the 12-hoodie PO ($264) brings the total to $3,504, which is **$104 more than the shop has**. The agents cannot do everything at once and must set priorities.

---

## Desk tables added by the MCP server

The original database had no place for an approval queue, purchase orders, message drafts, or ticket history. Since Problem 5, the MCP server adds these four tables to the **working copy** (never the original). A reset removes them, and they come back empty on the next tool call. The agent activity log is not a table: it is `output/audit_trail.json`.

### `approvals`
Fields: `id` (PK), `kind` (invoice / rent / purchase_order), `ref_id`, `amount`, `ticket_id` (→ `tickets.id`), `reason`, `requested_by` (agent), `status` (pending / approved / rejected), `decided_by` (human), `decision_note`, `payment_id` (→ `payments.id`), `shop_date`, `created_at`, `decided_at`

**Why it matters:** This is the human-approval queue. Agents can only add *pending* rows; a human's decision turns one into a `payments` row. Pending amounts count against cash before anything is paid.

### `purchase_orders`
Fields: `id` (PK), `vendor_id` (→ `vendors.id`), `sku`, `size`, `qty`, `unit_cost`, `total`, `ticket_id`, `status` (pending_approval / ordered / rejected), `expected_arrival`, `created_by`, `created_at`

**Why it matters:** A restock waits here until a human approves it. Cost comes from `pricing.unit_cost` and arrival from `vendors.lead_days`.

### `drafts`
Fields: `id` (PK), `ticket_id`, `audience` (customer / vendor / landlord), `recipient`, `subject`, `body`, `status` (always `draft`), `created_by`, `created_at`

**Why it matters:** Customer messages live here and on the board, and nothing is ever sent.

### `ticket_updates`
Fields: `id` (PK), `ticket_id` (→ `tickets.id`), `author` (agent or `human:<name>`), `old_status`, `new_status`, `note`, `created_at`

**Why it matters:** Each ticket's history, so the original request text in `tickets.notes` is never overwritten and a later run can see what was already done.

---

## MCP tools

Server: `mcp_server/server.py` (FastMCP), pointed at `data/campus_customs_new.db`. Every agent uses these tools. All three are read-only and return only database values; anything not on file comes back as `found: false` instead of a guess. The numbers below are real outputs from test calls against the working copy.

### 1. `check_stock(sku, size, qty_needed)`
- **Reads:** `inventory`
- **Unlocks:** Ticket 101 (also used for Ticket 103)
- **Why it is the right tool:** Ticket 101 is Tauhid Zaman's order for 1 `CC-TEE-WHITE` in size S, and `check_stock("CC-TEE-WHITE", "S", 1)` returns qty 0 in Aisle B with a shortfall of 1 (`can_fill_now: false`), which shows the tee cannot come off the shelf and points the team to the restock path through invoice 501 and Bulldog Print Co rather than promising Tauhid a shirt the shop does not have.
- **Also for 103:** `check_stock("CC-HOOD-NAVY", "M", 20)` returns 8 on hand, a shortfall of 12, and the other sizes on hand (S 4, L 14, XL 6).

### 2. `get_lease(lease_id)`
- **Reads:** `leases` (plus `desk.date_today` to count days)
- **Unlocks:** Ticket 102
- **Why it is the right tool:** Ticket 102 is Elm City Properties' "shop rent due in 2 days" email carrying `lease_id` 1, and `get_lease(1)` checks that claim against the lease on file ($2,400.00 for the Chapel Street shop, `next_due` 2026-09-02, `days_until_due` 2 from shop date 2026-08-31, `is_overdue: false`), so facilities can confirm the notice is real and accounting has the exact amount and deadline for the rent payment it will prepare for human approval.

### 3. `check_margin(sku, qty, discount_pct)`
- **Reads:** `pricing`
- **Unlocks:** Ticket 103
- **Why it is the right tool:** Ticket 103 is the Yale AI Club asking for a bulk discount on 20 `CC-HOOD-NAVY` hoodies, and `check_margin("CC-HOOD-NAVY", 20, discount_pct)` turns the pricing row ($22.00 unit cost, $58.00 list) into the numbers the boss needs to decide: $36.00/unit (62.1%) at list, $27.30/unit (55.4%) at a sample 15% off, and a 62.1% break-even discount, so any offer is judged on real margin instead of a guess.

### Still needed (later problems)
The tickets also need tools these three do not cover: vendor and open-invoice status (Bulldog Print Co is blocked by invoice 501), the cash balance, and payments that require human approval and refuse to overdraw `checking`. *(Added in Problem 5; see the full tool list below.)*

---

## Agent team (Problem 5)

Built with PydanticAI in `backend/`. **Every agent runs `gpt-6-luna` through Portkey**, using a single shared model object in `backend/agents/base.py`; no other model name appears in the code. Each agent has its own prompt file, its own MCP tool allowlist, and the shared `delegate` tool.

| Agent | Job | Prompt | Code | MCP tools it may call | Returns |
|---|---|---|---|---|---|
| **boss** | Reads each ticket, picks who goes first, delegates, makes the final call, records it | `backend/prompts/boss.md` | `backend/agents/boss.py` | `list_tickets`, `get_ticket`, `update_ticket`, `get_cash_balance`, `list_approvals` | `TicketDecision` |
| **inventory** | Stock by SKU and size, shortfalls, which vendor can restock, lead times, vendor holds | `backend/prompts/inventory.md` | `backend/agents/inventory.py` | `get_ticket`, `check_stock`, `check_vendor_status` | `SpecialistReport` |
| **accounting** | Cash, invoices, margins, and filing payment requests and POs for human approval | `backend/prompts/accounting.md` | `backend/agents/accounting.py` | `get_ticket`, `get_cash_balance`, `get_invoice`, `list_open_invoices`, `check_margin`, `check_vendor_status`, `request_payment`, `create_purchase_order`, `list_approvals` | `SpecialistReport` |
| **facilities** | The shop space: checks rent notices against the lease, routes rent to accounting | `backend/prompts/facilities.md` | `backend/agents/facilities.py` | `get_ticket`, `get_lease` | `SpecialistReport` |
| **customer_service** | Drafts customer messages (saved on the board, never sent) | `backend/prompts/customer_service.md` | `backend/agents/customer_service.py` | `get_ticket`, `save_draft` | `SpecialistReport` |

**Full connectivity:** every agent has `delegate(to, task)`, which can target any other agent. The hand-off runs the target's own agent loop and returns its structured report. Guardrails: an agent can't delegate to itself or to anyone already waiting on it in the chain (which prevents loops), depth is capped at 2, and each ticket gets at most 6 hand-offs.

**Agent loop and audit trail:** `backend/team.py` runs each agent with `Agent.iter()` one step at a time. Every step is appended to `output/audit_trail.json` (a JSON array that only grows) as it happens:

| Event | What it records |
|---|---|
| `run_start` / `run_end` | Ticket, task, limits, outcome, total tokens, requests, tool calls, hand-offs, seconds |
| `agent_start` / `agent_end` | Agent, its task brief, prompt file + SHA-256, allowed tools, structured output |
| `model_request` | One loop step: what went into the model (prompt, tool results, retry messages) |
| `model_response` | One loop step: the model's text, tool calls with arguments, token usage, finish reason |
| `delegation_start` / `_end` / `_refused` | Who handed what to whom, the report that came back, or why a hand-off was blocked |
| `limit_exceeded`, `error`, `human_decision` | Budget stops, failures, and human approvals or rejections |

Every event also carries `ts`, `run_id`, `ticket_id`, `agent`, `chain` (e.g. `boss → inventory → accounting`), `depth`, `step`, and `model`.

**Model settings** (`backend/agents/base.py`): one shared `OpenAIChatModel("gpt-6-luna")` with an OpenAI client pointed at `https://api.portkey.ai/v1` using `PORTKEY_API_KEY`. It sends `max_completion_tokens` (Luna rejects `max_tokens`), no temperature (Luna's default is 1), and `reasoning_effort: "none"`, because Luna on `/v1/chat/completions` refuses function tools while reasoning is on. That last setting came from the first live run (see Problem 9).

**Run it:** from the board's **Send in the team** button, `POST /tickets/{id}/run`, or the CLI from `Homework 5`: `.venv\Scripts\python.exe -m backend.cli run 101`. The CLI also has a human approval desk: `... -m backend.cli approvals`, `... approve <id> --by "Name"` (asks you to type APPROVE), and `... reject <id> --by "Name" --reason "..."`.

---

## MCP tools: full list (Problem 5)

`mcp_server/server.py` now has 17 tools (16 from Problem 5, plus `list_drafts` for the dashboard in Problem 7). All shop facts reach the agents through these tools; the backend has no other path to the database. The first time a tool runs, the server adds four tables to the working copy: `approvals`, `purchase_orders`, `drafts`, and `ticket_updates`. A reset removes them, and they come back empty on the next call.

| Tool | Tables it uses | Who can call it | What it does |
|---|---|---|---|
| `list_tickets` | `tickets`, `desk` | boss | The open (or all) ticket queue |
| `get_ticket` | `tickets`, `ticket_updates`, `approvals`, `purchase_orders`, `drafts`, `desk` | all agents | One ticket in full, plus everything already filed for it (including draft text) |
| `check_stock` | `inventory` | inventory | On hand per SKU and size, shortfall, can it be filled now |
| `check_vendor_status` | `vendors`, `invoices`, `desk` | inventory, accounting | Specialty, lead_days, unpaid invoices, `can_ship`, arrival if ordered today |
| `get_invoice` | `invoices`, `vendors`, `approvals`, `desk` | accounting | One invoice, days overdue, any pending payment request |
| `list_open_invoices` | `invoices`, `vendors`, `desk` | accounting | Every unpaid invoice and the total |
| `get_cash_balance` | `cash_accounts`, `approvals`, `payments`, `desk` | boss, accounting | Balance, pending requests, `available_after_pending`, recent payments |
| `get_lease` | `leases`, `desk` | facilities | Rent, landlord, next due, days until due |
| `check_margin` | `pricing` | accounting | Unit and order margin at a discount, break-even discount |
| `list_approvals` | `approvals`, `cash_accounts` | boss, accounting | Payment requests by status |
| `list_drafts` | `drafts` | dashboard only (no agent) | Message drafts on the board, with full text |
| `request_payment` | writes `approvals`; reads `invoices`, `vendors`, `leases`, `cash_accounts` | accounting | Files an invoice or rent payment **for human approval** (amount comes from the database) |
| `create_purchase_order` | writes `purchase_orders`, `approvals`; reads `vendors`, `inventory`, `pricing`, `invoices`, `cash_accounts` | accounting | Files a restock PO **for human approval**; refused while the vendor has an unpaid invoice |
| `save_draft` | writes `drafts` | customer_service | Saves a message on the board; never sent |
| `update_ticket` | writes `tickets.status`, `ticket_updates`; reads `approvals` | boss | Sets the status and adds a history note; won't mark `resolved` while approvals are pending |
| `approve_request` | writes `payments`, `cash_accounts`, `approvals`, `ticket_updates`, and `invoices` / `leases` / `purchase_orders` | **humans only** | Pays one approved request: records the payment, lowers cash, marks the invoice paid / moves rent's next due date forward a month / orders the PO |
| `reject_request` | writes `approvals`, `purchase_orders`, `ticket_updates` | **humans only** | Rejects a request; nothing is paid |

---

## SAFETY

**Money (real cash)**
- **A human approves every payment.** Agents can only *file* requests. `approve_request` and `reject_request` are tagged `human_only` and appear in no agent's allowlist (the backend refuses to start if one ever does). They are tested: an agent that calls one gets "Unknown tool". The only routes that call them are the board's approve/reject routes. On the board, signing needs a typed name and a confirmation showing the balance before → after; on the CLI, the person has to type `APPROVE`. The signer's name is saved in `payments.approved_by`.
- **No overdrafts.** A request is refused if cash left after all pending requests can't cover it, and `approve_request` re-checks the live balance before paying.
- **Rules live in code, not just prompts.** The vendor hold, duplicate-request block, database-sourced amounts, and all-or-nothing transactions are enforced by the MCP server whatever the model says.
- **Tickets close only after the human acts.** A ticket the boss parks on `waiting_approval` is marked resolved only after a human signs its last pending request. A rejection sends the ticket back to `in_progress` for the team to re-plan.
- **One team run at a time.** A reset is refused while a run is active.

**Customers and data**
- **Nothing can be sent.** No email, phone, or vendor tool exists; customer messages are drafts on the board for a person to send.
- **No invented facts.** Tools return `found: false` instead of guessing, and the prompts require citing the tool behind each fact.
- **Least privilege.** Each role sees only its tools. The backend stamps `actor` on every write, so an agent can't sign as someone else. The MCP server gets no API key, and it refuses to open the original database. The API only accepts browser calls from localhost pages (CORS).
- **A person reads every draft before it goes out.** This matters in practice: in Problem 9, draft #1 mentioned an internal invoice approval to the customer, which the customer service prompt forbids, so a human should edit it before sending.
- **Full audit.** Every loop step, hand-off, human decision, and reset is appended to `audit_trail.json` and never rewritten. Each agent run records the SHA-256 of the prompt it used, so prompt changes are traceable.

**Token limits** (`backend/config.py`; usage is shared by every agent on a ticket)
- 3,000 output tokens per response, and per ticket at most 30 model calls, 40 tool calls, and 150,000 tokens. Hitting a cap stops the run and logs `limit_exceeded`.
- At most 6 hand-offs per ticket, depth 2, no self-delegation or cycles. Delegates start fresh with only their brief, never the caller's whole conversation.
- Small per-role tool lists keep the tool definitions sent with each request short. Tool outputs are compact, and the audit trail clips long text at 4,000 characters.

**What a real shop would add before going live:** approver sign-in instead of a typed name, dual approval above a dollar threshold, alerts when a run hits a budget cap, a kill switch, and a retention policy for customer data in drafts and logs.

### Shop rules and where each is enforced

| Shop rule | Enforced in code (MCP server / API) | Also in prompts and on the board |
|---|---|---|
| `desk.date_today` is "today" | Every date check (overdue, days until due, arrival) is computed from `desk.date_today` and returned as `shop_today` | All five prompts; the board's masthead shows the shop day |
| Vendor lead times come from `vendors` | `check_vendor_status` and `create_purchase_order` use `vendors.lead_days` | Inventory prompt: arrival is "earliest", never a promise |
| A vendor with an open unpaid invoice can't ship | `create_purchase_order` refuses; `approve_request` re-checks before ordering | Inventory and accounting prompts route the invoice to accounting first |
| Human approval for every payment, and the tables update when paid | Agents only add `approvals` rows. `approve_request` (human-only) writes `payments`, lowers `cash_accounts`, and marks the invoice paid / moves `leases.next_due` / orders the PO, all in one transaction | Board: name + confirm modal. CLI: type APPROVE |
| Cash can never go negative | Requests are refused beyond `available_after_pending`; `approve_request` refuses if amount > balance | Accounting prompt; board shows "checking after signing" |
| No revenue; cash only goes out | No tool adds cash; `check_margin` states that a sale adds no cash | Accounting and boss prompts ("margin is not cash") |
| Never email customers or call vendors | No send/email/call tool exists; `save_draft` only stores | Customer service prompt; board stamps drafts "DRAFT · NOT SENT" |
| Never invent data | Tools return `found: false` / `ok: false`; amounts always come from the database | Every prompt: cite the tool behind each fact |

---

## Backend routes (Problem 7)

`backend/main.py` (FastAPI). Start it from `backend/` with `uvicorn main:app --reload --port 8000`; it serves http://localhost:8000, with interactive docs at http://localhost:8000/docs. Every shop read and every approval goes through the MCP server.

- `GET /tickets`: the 3 tickets with their status and `state` (open or resolved), last note, pending approvals, draft count, whether a run is active, and the `active_run`.
- `POST /tickets/{ticket_id}/run`: starts the agent team on one ticket (boss first) in the background and returns a `run_id`; `?wait=true` waits for the decision instead. Only one run at a time.
- `GET /runs/{run_id}`: the status (running / completed / stopped_by_budget / error) and final decision of a run.
- `GET /events`: recent agent events from `audit_trail.json`: who acted, what they said, and which tools they used. Pass `?after=<next_after>` to get only new events when the board refreshes (filters: `ticket_id`, `run_id`).
- `GET /approvals`: payment and purchase requests the agents prepared that are waiting for a human (`?status=all` for history).
- `POST /approvals/{approval_id}/approve`: a human approves (body `{"approved_by": "Name"}`). **This is the only route that changes cash.** It pays, updates the invoice / lease / PO, and refuses if cash would go negative or the name is an agent's. If that was the last pending request on a ticket the boss parked on `waiting_approval`, the ticket is marked resolved.
- `POST /approvals/{approval_id}/reject`: a human rejects a request (body `{"rejected_by", "reason"}`). No money moves, and the ticket goes back to `in_progress` for the team to re-plan.
- `GET /cash`: the current checking balance from `cash_accounts`, plus pending requests and recent payments.
- `GET /drafts`: message drafts on the board (never sent); `?ticket_id=` for one ticket.
- `POST /reset`: copies the original `campus_customs.db` back over the working copy for a fresh run. The audit trail is kept and logs a `db_reset` event. Refused while a run is active.
- `GET /`: service info and the route list.

---

## Dashboard (Problem 8)

`frontend/` is React 19 + Vite + TypeScript. Start it with `npm run dev` (it opens http://localhost:5173). It calls only the routes above at http://localhost:8000, which allows the Vite origin. Design choices and reasons are in `output/design.md`.

| What you see | Route(s) it calls | What it shows |
|---|---|---|
| **Today's tickets** (left) | `GET /tickets`, `POST /tickets/{id}/run` | All 3 tickets with state badges (Open / Team at work / Needs your signature / Resolved stamp). Pick one and press **Send in the team**. |
| **The team** (center): roster + **Live desk** feed | `GET /events?after=…` (polled every ~1 s during a run) | Each agent's live status, every hand-off (indented by depth), tool calls with arguments, the hand-off chain, and the boss's call |
| **Who did what** tab | `GET /events` (with detail) | Per-agent report cards (tools, hand-offs, what was filed, recommendations, blockers), the boss's call, any human signatures after the run, and run cost. A run picker (✓/✗) switches between runs on the same ticket. |
| **Bulldog Bank** (right) | `GET /cash` | The checking balance from `cash_accounts`, pending vs. free cash, and recent payments with who signed. The number counts down after a signature. |
| **Signature desk** | `GET /approvals`, `POST /approvals/{id}/approve` / `reject` | Prepared payments and POs as permission slips; signing needs a name and a confirmation |
| **Drafts on the board** | `GET /drafts` | Customer drafts for the selected ticket, stamped "never sent" |
| **Fresh start** | `POST /reset` | Puts the shop back to the original data (asks first) |

Agents appear as Yale-inspired personas (original drawings, not official marks): **Handsome Dan** the bulldog (boss), **Sterling** (inventory), **Lux et Ledger** (accounting), **Harkness** (facilities), **Boola** (customer service), and gold for the human signer. Deep links such as `#ticket=103&tab=summary&run=1` open the board on one ticket and one run.

---

## Problem 9 run: resolving the tickets

The working DB was reset on the board (Fresh start), and then each ticket was run from the board with `gpt-6-luna`. Hudson signed both payments on the board. Every step is in `output/audit_trail.json`.

| Ticket | Asked first | Hand-offs (final run) | Human approval | Cash | Final status |
|---|---|---|---|---|---|
| 101 tee S | Inventory | Boss → Inventory → Accounting; Boss → Customer Service | #1 invoice 501, $840.00 (Hudson) | −$840.00 | resolved |
| 102 rent | Facilities | Boss → Facilities; Boss → Accounting | #2 rent, lease 1, $2,400.00 (Hudson) | −$2,400.00 | resolved |
| 103 hoodies | Accounting | Run 1: Boss → Accounting; Boss → Inventory → Accounting; Boss → Customer Service. Run 3: Boss → Accounting | none (no payment or PO) | $0.00 | resolved |

**Cash:** $3,400.00 at the start → −$840.00 (invoice 501) → −$2,400.00 (rent) → $0.00 (ticket 103) = **$160.00**, matching `cash_accounts` in the working DB. Itemized in the Cash tab of `output/desk_tickets.html`.

**Outputs:** `output/desk_tickets.html` (Actual sections + Cash tab), `output/resolved_tickets.json` (per ticket: status, outcome, each agent's contribution, human approvals, runs), and `output/resolved_board.html` (board screenshots for each ticket; PNGs in `output/board_screenshots/`).

**What the live run taught us (all recorded in the audit trail):**
- **Tools with reasoning on are rejected.** The first attempt on 101 failed: Azure won't accept function tools from `gpt-6-luna` on chat completions while reasoning is on. Fixed by sending `reasoning_effort: "none"`.
- **Server reloads cancel runs.** A second attempt was cancelled by an API reload, so backend files must not be edited while a run is in progress.
- **The resolve rule was too vague.** Ticket 103 stayed `in_progress` after two runs, because the boss treated an unsent draft and a future "if more cash comes in" as open work. The boss prompt now says a partial yes is a final call, and `get_ticket` now returns draft text. The third run resolved it.
- **Guardrails held.** On 103, accounting saw invoice 501's request was already pending and did not file a duplicate. With $160 left, no one tried to fund the $264 restock.
