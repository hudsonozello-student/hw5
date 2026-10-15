# Campus Customs Multi-Agent Operations (MGT 409 · HW5)

An agent team that runs the Campus Customs shop desk at Yale SOM. There are five PydanticAI agents (**boss, inventory, accounting, facilities, customer service**) that can hand work to each other. They read and change shop data only through an **MCP server**, a **FastAPI backend** runs them, and a **React board** lets a person watch the agents work and **sign every payment**. Every agent uses **`gpt-6-luna` through Portkey**, and no other model.

```
hw5/
├── README.md, AI_prompts.md, requirements.txt, .env.example, .gitignore, .mcp.json
├── data/
│   ├── campus_customs.db        original data: never modified (the reset source)
│   └── campus_customs_new.db    working copy: the MCP server reads and writes this one
├── mcp_server/                  server.py (FastMCP, 17 tools) + README.md
├── backend/                     main.py (FastAPI), models.py, team.py (agent loop), agents/, prompts/ (one per agent)
├── frontend/                    React + Vite + TypeScript board
└── output/                      harness.md, design.md, desk_tickets.html, resolved_*.{json,html}, audit_trail.json, …
```

---

## 1. One-time setup

You need Python 3.12+ (built with 3.14) and Node.js 20+ (built with 24).

**Python environment**, from the `hw5` folder:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**API key:** copy `.env.example` to `.env` in the same folder and paste your Portkey key as `PORTKEY_API_KEY`. `.env` is git-ignored; never commit it.

**Board packages:**

```bash
cd frontend
npm install
```

---

## 2. Databases: copy the original to the working copy for a clean run

- `data/campus_customs.db` is the **original** and is never changed. The MCP server refuses to open it.
- `data/campus_customs_new.db` is the **working copy** that agents, payments, and the board change. **As committed, it holds the end state of our graded run** (all three tickets resolved, $160.00 in checking), so it matches the files in `output/`.

Whenever you want a clean start, copy the original over the working copy (with the backend stopped):

```powershell
Copy-Item data\campus_customs.db data\campus_customs_new.db -Force     # Windows
```

```bash
cp data/campus_customs.db data/campus_customs_new.db                     # macOS / Linux
```

The four desk tables (`approvals`, `purchase_orders`, `drafts`, `ticket_updates`) are created automatically the first time a tool runs.

---

## 3. Start the MCP server

The backend starts the MCP server for you (over stdio) every time it needs shop data, so for normal use there is nothing extra to run. To start it on its own, for example to test tools or connect a vibe coder, run this from `hw5` with the virtual environment active:

```bash
python mcp_server/server.py
```

It waits silently for a client on stdio (stop with Ctrl+C). `.mcp.json` registers the same server for Claude Code: open Claude Code in the `hw5` folder with the virtual environment active, and the `campus-customs` tools appear. See `mcp_server/README.md` for the full tool list.

---

## 4. Start the FastAPI backend

With the virtual environment active:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API runs at http://localhost:8000, with interactive docs at http://localhost:8000/docs. It allows the Vite page (http://localhost:5173) to call it from the browser. Don't edit backend `.py` files while a ticket is running: `--reload` restarts the server and cancels the run.

---

## 5. Start the React board

In a second terminal:

```bash
cd frontend
npm run dev
```

This opens the desk at http://localhost:5173. Pick a ticket, press **Send in the team**, and watch each agent work. Payments and purchase orders wait on the **Signature desk** until a person signs them.

---

## 6. A full 3-ticket run: reset the DB first

1. **Reset.** Press **Fresh start** on the board, or copy the original DB as in step 2, or call `POST http://localhost:8000/reset`. Check that **Bulldog Bank** shows **$3,400.00** and all three tickets show **Open**.
2. Type your name next to **Signing as** (top right).
3. Run **101**, then **102**, then **103** with **Send in the team**, one at a time (the board allows one run at a time).
4. When a permission slip appears, read it and **Sign & pay**. Agents only *prepare* payments; your signature is what moves cash, and the board shows the balance before → after. A ticket waiting on your signature resolves when you sign its last slip.
5. If the boss leaves a ticket *in progress* (for example, after a vendor hold is lifted), run that ticket again.
6. Check the result: **Who did what** for each ticket, and the balance in Bulldog Bank (it matches `cash_accounts` in the working DB).

Our graded run went **$3,400.00 → −$840.00 (invoice 501, ticket 101) → −$2,400.00 (rent, ticket 102) → $0.00 (ticket 103) = $160.00**. Agent output varies from run to run, but the cash rules don't.

**Command-line alternative** (from `hw5`, venv active): `python -m backend.cli run 101`, `python -m backend.cli approvals`, `python -m backend.cli approve 1 --by "Your Name"`.

---

## Where to look

| File | What it is |
|---|---|
| `output/harness.md` | The full reference: tables, MCP tools, the 5 agents, API routes, dashboard, safety rules, and the Problem 9 results |
| `output/desk_tickets.html` | Expected vs. Actual for each ticket, the itemized Cash tab, and the reflection (double-click to open) |
| `output/resolved_tickets.json` | Per ticket: final status, outcome, each agent's contribution, human approvals, runs |
| `output/resolved_board.html` | Screenshots of the board for each resolved ticket (double-click to open) |
| `output/audit_trail.json` | Every agent-loop step, hand-off, human decision, and reset, appended and never rewritten |
| `output/design.md` | Why the board looks and works the way it does |
| `output/mcp_smoke.json` | The Problem 4 tool tests from the vibe coder |
| `AI_prompts.md` | Every prompt given to the vibe coder, verbatim, by problem |

## Safety at a glance

- Only a human can approve a payment. The approve/reject tools are human-only and never given to an agent.
- Cash can never go negative: requests are refused beyond what's left after pending requests, and payment re-checks the balance.
- A vendor with an unpaid invoice can't receive a purchase order.
- Nothing is ever sent to customers or vendors. Drafts stay on the board.
- Each agent sees only its own tools, and every step is logged in `output/audit_trail.json`.

Details are in `output/harness.md` (SAFETY and Shop rules).
