"""The agent loop: run any agent step by step, audit every step, and let agents hand work to each other.

Each model call and the tool results fed back to it are written to
output/audit_trail.json as they happen, so a crashed or budget-stopped run
still leaves its trail. Usage is shared by every agent on a ticket, so the
limits in config.py are a per-ticket budget.
"""

import asyncio
import hashlib
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic_ai import (
    CallToolsNode,
    ModelRequestNode,
    RetryPromptPart,
    RunContext,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UsageLimitExceeded,
    UserPromptPart,
)
from pydantic_ai.usage import RunUsage, UsageLimits
from pydantic_core import to_jsonable_python

from backend.agents import AGENTS, MCP_TOOLS_BY_AGENT
from backend.audit import AuditTrail
from backend.config import (
    AUDIT_TRAIL,
    MAX_DELEGATION_DEPTH,
    MAX_DELEGATIONS_PER_TICKET,
    MAX_OUTPUT_TOKENS,
    MODEL_NAME,
    PROMPTS_DIR,
    TICKET_REQUEST_LIMIT,
    TICKET_TOKEN_LIMIT,
    TICKET_TOOL_CALL_LIMIT,
)
from backend.mcp_tools import SHOP
from backend.models import AgentName, RunBudget, TeamDeps, TicketDecision

LIMITS = UsageLimits(
    request_limit=TICKET_REQUEST_LIMIT,
    tool_calls_limit=TICKET_TOOL_CALL_LIMIT,
    total_tokens_limit=TICKET_TOKEN_LIMIT,
)


def _usage(usage: RunUsage) -> dict[str, int]:
    return {"requests": usage.requests, "tool_calls": usage.tool_calls,
            "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}


def _request_parts(request) -> list[dict[str, Any]]:
    """What went into the model on this step (the system prompt is logged once, by hash, at agent_start)."""
    parts = []
    for part in request.parts:
        if isinstance(part, SystemPromptPart):
            continue
        if isinstance(part, UserPromptPart):
            parts.append({"type": "user_prompt", "content": to_jsonable_python(part.content)})
        elif isinstance(part, ToolReturnPart):
            parts.append({"type": "tool_result", "tool": part.tool_name, "tool_call_id": part.tool_call_id,
                          "content": to_jsonable_python(part.content)})
        elif isinstance(part, RetryPromptPart):
            parts.append({"type": "retry", "tool": part.tool_name, "content": part.model_response()})
        else:
            parts.append({"type": type(part).__name__})
    return parts


def _response_parts(response) -> dict[str, Any]:
    """What the model answered on this step: its text, the tools it chose and their arguments, and token use."""
    calls = []
    for part in response.parts:
        if isinstance(part, ToolCallPart):
            try:
                args = part.args_as_dict()
            except Exception:  # malformed JSON from the model is kept as-is for the audit
                args = part.args
            calls.append({"tool": part.tool_name, "tool_call_id": part.tool_call_id, "args": args})
    return {
        "text": [p.content for p in response.parts if isinstance(p, TextPart)],
        "tool_calls": calls,
        "reasoning_parts": sum(isinstance(p, ThinkingPart) for p in response.parts),
        "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        "finish_reason": response.finish_reason,
    }


async def run_agent(name: AgentName, task: str, deps: TeamDeps, usage: RunUsage) -> Any:
    """Run one agent's loop (model -> tools -> model ...) to its structured output, auditing each step."""
    agent = AGENTS[name]
    prompt_file = PROMPTS_DIR / f"{name}.md"
    deps.audit.log(deps, "agent_start", {
        "task": task,
        "prompt_file": f"backend/prompts/{prompt_file.name}",
        "prompt_sha256": hashlib.sha256(prompt_file.read_bytes()).hexdigest()[:16],
        "tools": sorted(MCP_TOOLS_BY_AGENT[name]) + ["delegate"],
    }, model=MODEL_NAME)

    step = 0
    async with agent.iter(task, deps=deps, usage=usage, usage_limits=LIMITS) as run:
        async for node in run:
            if isinstance(node, ModelRequestNode):
                step += 1
                deps.audit.log(deps, "model_request", {"parts": _request_parts(node.request)},
                               step=step, model=MODEL_NAME)
            elif isinstance(node, CallToolsNode):
                deps.audit.log(deps, "model_response", _response_parts(node.model_response),
                               step=step, model=node.model_response.model_name or MODEL_NAME)
        output = run.result.output

    deps.audit.log(deps, "agent_end", {"output": output.model_dump(), "ticket_usage_so_far": _usage(usage)},
                   step=step, model=MODEL_NAME)
    return output


async def run_delegation(ctx: RunContext[TeamDeps], to: AgentName, task: str) -> str:
    """The delegate tool: any agent can hand work to any other, inside the cycle, depth, and budget guardrails."""
    deps, budget = ctx.deps, ctx.deps.budget
    if to not in AGENTS:
        reason = f"'{to}' is not a teammate."
    elif to == deps.agent:
        reason = "You cannot delegate to yourself."
    elif to in deps.chain:
        reason = (f"{to} is already waiting on your answer ({' -> '.join(deps.chain)}). "
                  "Answer with what you have and name the open question in your report.")
    elif deps.depth >= budget.max_depth:
        reason = f"The hand-off depth limit ({budget.max_depth}) is reached. Finish the task yourself."
    elif budget.delegations_used >= budget.max_delegations:
        reason = f"This ticket has used all {budget.max_delegations} hand-offs. Finish with what you have."
    else:
        reason = None
    if reason:
        deps.audit.log(deps, "delegation_refused", {"to": to, "task": task, "reason": reason})
        return f"DELEGATION REFUSED: {reason}"

    budget.delegations_used += 1
    deps.audit.log(deps, "delegation_start",
                   {"to": to, "task": task, "hand_off_number": budget.delegations_used})
    report = await run_agent(to, task, deps.for_delegate(to), ctx.usage)
    deps.audit.log(deps, "delegation_end", {"to": to, "report": report.model_dump()})
    return report.model_dump_json()


async def run_ticket(ticket_id: int, *, audit_path: Path = AUDIT_TRAIL, start_agent: AgentName = "boss",
                     task: str | None = None, run_id: str | None = None) -> TicketDecision:
    """Work one desk ticket with the whole team, starting from the boss."""
    audit = AuditTrail(audit_path)
    deps = TeamDeps(
        run_id=run_id or uuid.uuid4().hex[:12], ticket_id=ticket_id, agent=start_agent, chain=(start_agent,),
        budget=RunBudget(max_delegations=MAX_DELEGATIONS_PER_TICKET, max_depth=MAX_DELEGATION_DEPTH), audit=audit,
    )
    task = task or (f"Handle desk ticket {ticket_id}. Read it with get_ticket, route the work to the right "
                    "teammates, make the final call, and record it with update_ticket.")
    audit.log(deps, "run_start", {"task": task, "limits": {
        "max_output_tokens_per_response": MAX_OUTPUT_TOKENS, "request_limit": TICKET_REQUEST_LIMIT,
        "tool_calls_limit": TICKET_TOOL_CALL_LIMIT, "total_tokens_limit": TICKET_TOKEN_LIMIT,
        "max_delegation_depth": MAX_DELEGATION_DEPTH, "max_delegations": MAX_DELEGATIONS_PER_TICKET,
    }}, model=MODEL_NAME)

    usage = RunUsage()
    started = time.perf_counter()

    def finish(outcome: str, **extra: Any) -> None:
        audit.log(deps, "run_end", {"outcome": outcome, "usage": _usage(usage),
                                    "hand_offs": deps.budget.delegations_used,
                                    "seconds": round(time.perf_counter() - started, 1), **extra}, model=MODEL_NAME)

    try:
        async with SHOP:  # one MCP server process for every agent on this ticket
            decision = await run_agent(start_agent, task, deps, usage)
    except UsageLimitExceeded as exc:
        audit.log(deps, "limit_exceeded", {"error": str(exc), "usage": _usage(usage)})
        finish("stopped_by_budget")
        raise
    except asyncio.CancelledError:  # e.g. the API server restarted mid-run
        finish("cancelled")
        raise
    except Exception as exc:
        audit.log(deps, "error", {"error": repr(exc)})
        finish("error")
        raise
    finish("completed", output=decision.model_dump())
    return decision
