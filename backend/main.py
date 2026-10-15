"""FastAPI backend for the Campus Customs desk dashboard.

Start it from this folder (backend/):

    uvicorn main:app --reload --port 8000

It then serves http://localhost:8000 (interactive docs at /docs). Shop data is
read and changed only through the campus-customs MCP server, over one desk
connection the app keeps open. Agent events come from output/audit_trail.json.
"""

import asyncio
import json
import sqlite3
import sys
import uuid
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# `uvicorn main:app` run from backend/ needs the Homework 5 folder on the path for `backend.*` imports.
HW5_DIR = Path(__file__).resolve().parent.parent
if str(HW5_DIR) not in sys.path:
    sys.path.insert(0, str(HW5_DIR))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from backend.audit import AuditTrail  # noqa: E402
from backend.config import AUDIT_TRAIL, MODEL_NAME, ORIGINAL_DB, WORKING_DB  # noqa: E402
from backend.mcp_tools import DESK, human_desk_call  # noqa: E402

CLOSED_STATUSES = {"resolved", "declined"}
RUNS: dict[str, dict[str, Any]] = {}  # run_id -> status of team runs started by this server
_active: dict[str, Any] = {"run_id": None, "task": None}


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with DESK:  # one MCP server process for every dashboard read and approval
        yield
    task = _active["task"]
    if task and not task.done():
        task.cancel()


app = FastAPI(title="Campus Customs desk API", lifespan=lifespan)
app.add_middleware(  # the React dashboard (Vite) runs on its own port and calls this API from the browser
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",  # Vite picks another port if 5173 is busy
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _busy() -> str | None:
    task = _active["task"]
    return _active["run_id"] if task is not None and not task.done() else None


async def _approval(approval_id: int) -> dict:
    listing = await human_desk_call("list_approvals", {"status": "all"})
    request = next((a for a in listing["approvals"] if a["id"] == approval_id), None)
    if request is None:
        raise HTTPException(404, f"No payment request #{approval_id}.")
    if request["status"] != "pending":
        raise HTTPException(409, f"Request #{approval_id} is already {request['status']}.")
    return request


# ---------------------------------------------------------------- 1. tickets

@app.get("/tickets")
async def list_tickets() -> dict:
    """Every desk ticket, with state "open" or "resolved" (resolved = status resolved or declined)."""
    listing = await human_desk_call("list_tickets", {"status": "all"})
    tickets = []
    for t in listing["tickets"]:
        detail = await human_desk_call("get_ticket", {"ticket_id": t["id"]})
        history = detail["history"]
        tickets.append({
            **t,
            "state": "resolved" if t["status"] in CLOSED_STATUSES else "open",
            "last_note": history[-1]["note"] if history else None,
            "pending_approvals": [a for a in detail["approvals"] if a["status"] == "pending"],
            "draft_count": len(detail["drafts"]),
            "running": _busy() is not None and RUNS[_busy()]["ticket_id"] == t["id"],
        })
    return {"shop_today": listing["shop_today"], "active_run": RUNS[_busy()] if _busy() else None,
            "tickets": tickets}


# ---------------------------------------------------------------- 2. run the agent team

class RunInfo(BaseModel):
    run_id: str
    ticket_id: int
    status: str = Field(description="running | completed | stopped_by_budget | error | cancelled")
    started_at: str
    finished_at: str | None = None
    decision: dict | None = None
    error: str | None = None


async def _run_team(run_id: str, ticket_id: int) -> None:
    from backend.team import run_ticket  # loads the agents and the Portkey key on first use
    from pydantic_ai import UsageLimitExceeded

    run = RUNS[run_id]
    try:
        decision = await run_ticket(ticket_id, run_id=run_id)
        run.update(status="completed", decision=decision.model_dump())
    except UsageLimitExceeded as exc:
        run.update(status="stopped_by_budget", error=str(exc))
    except asyncio.CancelledError:
        run.update(status="cancelled")
        raise
    except Exception as exc:
        run.update(status="error", error=repr(exc))
    finally:
        run["finished_at"] = _now()


@app.post("/tickets/{ticket_id}/run", status_code=202, response_model=RunInfo)
async def start_run(ticket_id: int, wait: bool = False):
    """Start the agent team on one ticket (boss first). Returns at once with a run_id; poll /events or
    /runs/{run_id}. Pass ?wait=true to block until the run finishes. One team run at a time."""
    if running := _busy():
        raise HTTPException(409, f"Run {running} on ticket {RUNS[running]['ticket_id']} is still going.")
    if not (await human_desk_call("get_ticket", {"ticket_id": ticket_id}))["found"]:
        raise HTTPException(404, f"No ticket {ticket_id}.")
    run_id = uuid.uuid4().hex[:12]
    RUNS[run_id] = RunInfo(run_id=run_id, ticket_id=ticket_id, status="running", started_at=_now()).model_dump()
    _active.update(run_id=run_id, task=asyncio.create_task(_run_team(run_id, ticket_id)))
    if wait:
        await _active["task"]
        return JSONResponse(RUNS[run_id], status_code=200)
    return RUNS[run_id]


@app.get("/runs/{run_id}", response_model=RunInfo)
async def get_run(run_id: str):
    """Status and final decision of a team run started by this server."""
    if run_id not in RUNS:
        raise HTTPException(404, f"No run {run_id} on this server.")
    return RUNS[run_id]


# ---------------------------------------------------------------- 3. agent events

def _summarize(seq: int, e: dict) -> dict:
    """One audit event as the board shows it: who, what they said, which tools."""
    d, kind = e["data"], e["event"]
    said, tools = None, []
    if kind == "model_response":
        said = " ".join(d.get("text") or []) or None
        tools = [c["tool"] for c in d.get("tool_calls", [])]
    elif kind == "model_request":
        tools = [p["tool"] for p in d.get("parts", []) if p.get("tool")]
        said = "Tool results came back." if tools else "Received its task."
    elif kind in ("run_start", "agent_start"):
        said = d.get("task")
        tools = d.get("tools", [])
    elif kind == "delegation_start":
        said, tools = f"Hands off to {d['to']}: {d['task']}", ["delegate"]
    elif kind == "delegation_end":
        said = f"{d['to']} reported back: {d['report'].get('summary') or d['report'].get('decision')}"
    elif kind == "delegation_refused":
        said = f"Hand-off to {d['to']} blocked: {d['reason']}"
    elif kind == "agent_end":
        out = d.get("output", {})
        said = out.get("decision") or out.get("summary")
    elif kind == "run_end":
        u = d.get("usage", {})
        said = (f"Run {d.get('outcome')}: {u.get('requests')} model calls, {u.get('tool_calls')} tool calls, "
                f"{u.get('input_tokens', 0) + u.get('output_tokens', 0):,} tokens, {d.get('hand_offs')} hand-offs.")
    elif kind == "human_decision":
        r = d.get("result", {})
        said = (f"Approved #{r.get('approval_id')}: paid ${r.get('paid', 0):,.2f}; {r.get('change')}." if r.get("paid")
                else f"Request #{d.get('request', {}).get('id')}: {r.get('status') or r.get('error')}")
    elif kind == "db_reset":
        said = "Reset the working database to the original."
    elif kind in ("limit_exceeded", "error"):
        said = d.get("error")
    return {"seq": seq, "ts": e["ts"], "run_id": e["run_id"], "ticket_id": e["ticket_id"], "agent": e["agent"],
            "chain": e["chain"], "event": kind, "step": e["step"], "said": said, "tools": tools}


@app.get("/events")
async def recent_events(after: int | None = None, limit: int = 100, ticket_id: int | None = None,
                        run_id: str | None = None, include_requests: bool = False, detail: bool = False) -> dict:
    """Recent agent events from the audit trail: what each agent said and which tools it used.
    Pass ?after=<next_after from the last call> to get only new events when the board refreshes."""
    events = json.loads(AUDIT_TRAIL.read_text(encoding="utf-8")) if AUDIT_TRAIL.exists() else []
    rows = []
    for seq, e in enumerate(events):
        if after is not None and seq <= after:
            continue
        if (ticket_id is not None and e["ticket_id"] != ticket_id) or (run_id and e["run_id"] != run_id):
            continue
        if e["event"] == "model_request" and not include_requests:
            continue
        row = _summarize(seq, e)
        if detail:
            row["data"] = e["data"]
        rows.append(row)
    next_after = len(events) - 1
    if after is None:
        rows = rows[-limit:]
    elif len(rows) > limit:  # more new events than one page: resume after the last one returned
        rows = rows[:limit]
        next_after = rows[-1]["seq"]
    return {"next_after": next_after, "count": len(rows), "events": rows}


# ---------------------------------------------------------------- 4. human approvals (the only route that moves cash)

class ApproveBody(BaseModel):
    approved_by: str = Field(description="The person clicking Approve. Agent names are refused.")


class RejectBody(BaseModel):
    rejected_by: str
    reason: str


@app.get("/approvals")
async def list_approvals(status: str = "pending") -> dict:
    """Payment and purchase requests the agents prepared, waiting for a human (or status=all)."""
    return await human_desk_call("list_approvals", {"status": status})


@app.post("/approvals/{approval_id}/approve")
async def approve(approval_id: int, body: ApproveBody) -> dict:
    """A human approves a prepared payment or PO. This is what actually pays: cash goes down, and the
    invoice is marked paid / the rent due date moves forward / the PO is ordered. Refused if cash would go negative."""
    request = await _approval(approval_id)
    result = await human_desk_call("approve_request", {"approval_id": approval_id, "approved_by": body.approved_by})
    AuditTrail(AUDIT_TRAIL).log_human(body.approved_by.strip() or "unknown", "human_decision",
                                      {"request": request, "result": result}, ticket_id=request["ticket_id"])
    if not result.get("ok"):
        raise HTTPException(409, result)
    result["ticket_resolved"] = await _settle_ticket(request["ticket_id"], body.approved_by.strip())
    return result


async def _settle_ticket(ticket_id: int | None, approver: str) -> bool:
    """When the boss parked a ticket on the human's signature and nothing is left to sign, close it."""
    if ticket_id is None:
        return False
    ticket = await human_desk_call("get_ticket", {"ticket_id": ticket_id})
    if ticket["ticket"]["status"] != "waiting_approval" or any(a["status"] == "pending" for a in ticket["approvals"]):
        return False
    update = await human_desk_call("update_ticket", {
        "ticket_id": ticket_id, "status": "resolved", "actor": f"human:{approver}",
        "note": f"All payment requests for this ticket were approved by {approver}; resolved.",
    })
    return bool(update.get("ok"))


@app.post("/approvals/{approval_id}/reject")
async def reject(approval_id: int, body: RejectBody) -> dict:
    """A human rejects a prepared payment or PO. No money moves."""
    request = await _approval(approval_id)
    result = await human_desk_call("reject_request", {"approval_id": approval_id, "rejected_by": body.rejected_by,
                                                       "reason": body.reason})
    AuditTrail(AUDIT_TRAIL).log_human(body.rejected_by.strip() or "unknown", "human_decision",
                                      {"request": request, "result": result}, ticket_id=request["ticket_id"])
    if not result.get("ok"):
        raise HTTPException(409, result)
    if request["ticket_id"] is not None:  # the plan was turned down, so the ticket goes back to the team
        await human_desk_call("update_ticket", {
            "ticket_id": request["ticket_id"], "status": "in_progress", "actor": f"human:{body.rejected_by.strip()}",
            "note": f"Request #{approval_id} rejected: {body.reason}. Run the team again to re-plan.",
        })
    return result


# ---------------------------------------------------------------- 5. cash

@app.get("/cash")
async def cash() -> dict:
    """The checking balance from cash_accounts, plus what pending requests would use."""
    return await human_desk_call("get_cash_balance", {})


# ---------------------------------------------------------------- drafts on the board

@app.get("/drafts")
async def drafts(ticket_id: int | None = None) -> dict:
    """Message drafts the agents saved. They are never sent; a person reads them on the board."""
    return await human_desk_call("list_drafts", {} if ticket_id is None else {"ticket_id": ticket_id})


# ---------------------------------------------------------------- 6. reset

@app.post("/reset")
async def reset() -> dict:
    """Put the working database back to the original data/campus_customs.db (the original is only read).
    The audit trail is kept and gets a db_reset event."""
    if running := _busy():
        raise HTTPException(409, f"Run {running} is still going; reset after it finishes.")
    if WORKING_DB.resolve() == ORIGINAL_DB.resolve():
        raise HTTPException(500, "Working database path points at the original; refusing to reset.")
    with closing(sqlite3.connect(f"{ORIGINAL_DB.resolve().as_uri()}?mode=ro", uri=True)) as src, \
            closing(sqlite3.connect(WORKING_DB)) as dst:
        src.backup(dst)  # page-for-page copy: the working copy matches the original exactly
    AuditTrail(AUDIT_TRAIL).log_human("desk", "db_reset", {"from": "data/campus_customs.db",
                                                           "to": WORKING_DB.name})
    cash_now = await human_desk_call("get_cash_balance", {})
    tickets = (await human_desk_call("list_tickets", {"status": "all"}))["tickets"]
    return {"ok": True, "balance": cash_now["balance"],
            "tickets": {t["id"]: t["status"] for t in tickets}}


@app.get("/")
async def index() -> dict:
    """What this server offers."""
    return {"service": "Campus Customs desk API", "model": MODEL_NAME, "docs": "/docs",
            "routes": sorted({f"{', '.join(sorted(r.methods - {'HEAD'}))} {r.path}" for r in app.routes
                              if getattr(r, "include_in_schema", False)})}
