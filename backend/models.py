"""Data types shared by the Campus Customs agent team."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from backend.audit import AuditTrail

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[AgentName, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")

TicketStatus = Literal["open", "in_progress", "waiting_approval", "resolved", "declined"]

AuditEventType = Literal[
    "run_start",            # a ticket run begins
    "agent_start",          # an agent picks up a task (boss or a delegate)
    "model_request",        # one loop step: what was sent to the model (prompt, tool results, retries)
    "model_response",       # one loop step: what the model answered (text, tool calls, token usage)
    "delegation_start",     # one agent hands work to another
    "delegation_refused",   # a hand-off blocked by a guardrail (self, cycle, depth, budget)
    "delegation_end",       # the delegate's report came back
    "agent_end",            # an agent finished with its structured output
    "limit_exceeded",       # the per-ticket token/request budget ran out
    "error",                # anything else that stopped a run
    "run_end",              # the ticket run finished (with totals)
    "human_decision",       # a human approved or rejected a payment request
    "db_reset",             # a human reset the working database to the original
]


class SpecialistReport(BaseModel):
    """What inventory, accounting, facilities, and customer service hand back after a delegated task."""

    summary: str = Field(description="Two or three sentences answering the task you were given.")
    facts: list[str] = Field(
        default_factory=list,
        description="Facts you relied on, each with the tool it came from, e.g. 'check_stock: CC-TEE-WHITE S qty 0'.",
    )
    actions: list[str] = Field(
        default_factory=list,
        description="Records you created or changed, with their ids (approval #, PO #, draft #). Empty if none.",
    )
    recommendation: str = Field(description="What you recommend the caller or boss do next.")
    blockers: list[str] = Field(
        default_factory=list,
        description="Anything still blocking the ticket: pending human approvals, refusals, missing facts.",
    )


class TicketDecision(BaseModel):
    """The boss's final call on one ticket."""

    ticket_id: int
    decision: str = Field(description="The final call in plain English, with the key numbers.")
    status: TicketStatus = Field(description="The status you recorded with update_ticket.")
    delegated_to: list[AgentName] = Field(default_factory=list, description="Teammates you handed work to.")
    actions: list[str] = Field(
        default_factory=list, description="Records the team created, with ids (approval #, PO #, draft #)."
    )
    waiting_on_human: list[str] = Field(
        default_factory=list, description="Payment requests or drafts that need a person before anything moves."
    )
    next_steps: list[str] = Field(default_factory=list, description="What happens after the human decides.")


@dataclass
class RunBudget:
    """Counters shared by every agent working one ticket."""

    max_delegations: int
    max_depth: int
    delegations_used: int = 0


@dataclass
class TeamDeps:
    """Run context handed to every agent. Each delegate gets its own copy with a longer chain."""

    run_id: str
    ticket_id: int | None
    agent: AgentName
    chain: tuple[AgentName, ...]
    budget: RunBudget
    audit: AuditTrail

    @property
    def depth(self) -> int:
        return len(self.chain) - 1

    def for_delegate(self, target: AgentName) -> TeamDeps:
        return TeamDeps(self.run_id, self.ticket_id, target, (*self.chain, target), self.budget, self.audit)


class AuditEvent(BaseModel):
    """One line of output/audit_trail.json."""

    ts: str = Field(description="Real UTC time the event was written.")
    run_id: str
    ticket_id: int | None
    agent: str
    chain: list[str] = Field(description="Who handed work to whom to reach this agent, e.g. ['boss', 'inventory'].")
    depth: int
    step: int = Field(description="Agent-loop step number within this agent's run (0 = not a model step).")
    event: AuditEventType
    model: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
