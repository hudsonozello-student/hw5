"""Command line for the desk: run a ticket through the team, and the human approval desk.

Run from the Homework 5 folder with the project venv:

    .venv\\Scripts\\python.exe -m backend.cli run 101
    .venv\\Scripts\\python.exe -m backend.cli approvals
    .venv\\Scripts\\python.exe -m backend.cli approve 1 --by "Your Name"
    .venv\\Scripts\\python.exe -m backend.cli reject 1 --by "Your Name" --reason "Not now"

Approving asks you to type APPROVE, so only a person at the keyboard can move money.
"""

import argparse
import asyncio
import json

from backend.audit import AuditTrail
from backend.config import AUDIT_TRAIL, MODEL_NAME
from backend.mcp_tools import human_desk_call


async def _find_request(approval_id: int) -> dict | None:
    listing = await human_desk_call("list_approvals", {"status": "all"})
    return next((a for a in listing["approvals"] if a["id"] == approval_id), None)


async def _decide(approval_id: int, decided_by: str, approve: bool, reason: str) -> None:
    request = await _find_request(approval_id)
    if request is None:
        print(f"No request #{approval_id}.")
        return
    print(json.dumps(request, indent=2))
    if request["status"] != "pending":
        print(f"Request #{approval_id} is already {request['status']}.")
        return
    word = "APPROVE" if approve else "REJECT"
    action = f"pay ${request['amount']:,.2f}" if approve else "reject it"
    if input(f"Type {word} to {action} as {decided_by}: ").strip() != word:
        print("Cancelled. Nothing changed.")
        return
    if approve:
        result = await human_desk_call("approve_request", {"approval_id": approval_id, "approved_by": decided_by})
    else:
        result = await human_desk_call("reject_request",
                                       {"approval_id": approval_id, "rejected_by": decided_by, "reason": reason})
    AuditTrail(AUDIT_TRAIL).log_human(decided_by, "human_decision", {"request": request, "result": result},
                                      ticket_id=request.get("ticket_id"))
    print(json.dumps(result, indent=2))


async def _run(ticket_id: int) -> None:
    from backend.team import run_ticket  # loads the agents (and the API key) only when needed

    print(f"Running ticket {ticket_id} with {MODEL_NAME}. Every step is appended to {AUDIT_TRAIL.name}.")
    decision = await run_ticket(ticket_id)
    print(decision.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="backend.cli", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="work one ticket with the agent team").add_argument("ticket_id", type=int)
    sub.add_parser("approvals", help="list payment requests waiting for a human")
    for name in ("approve", "reject"):
        p = sub.add_parser(name, help=f"{name} a payment request (human only)")
        p.add_argument("approval_id", type=int)
        p.add_argument("--by", required=True, help="your name, recorded as the approver")
        if name == "reject":
            p.add_argument("--reason", required=True)
    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(_run(args.ticket_id))
    elif args.command == "approvals":
        print(json.dumps(asyncio.run(human_desk_call("list_approvals", {"status": "pending"})), indent=2))
    else:
        asyncio.run(_decide(args.approval_id, args.by, args.command == "approve", getattr(args, "reason", "")))


if __name__ == "__main__":
    main()
