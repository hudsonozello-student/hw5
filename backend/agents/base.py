"""Shared wiring for the five Campus Customs agents: one model, MCP tools by role, and delegation."""

from typing import Any

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from backend.config import MAX_OUTPUT_TOKENS, MODEL_NAME, PORTKEY_BASE_URL, PROMPTS_DIR, portkey_api_key
from backend.mcp_tools import tools_for
from backend.models import AGENT_NAMES, AgentName, TeamDeps


def build_model() -> OpenAIChatModel:
    """gpt-6-luna through Portkey. Every agent shares this one instance, so no other model can run."""
    key = portkey_api_key()
    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
        timeout=120,
        max_retries=2,
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


MODEL = build_model()
# max_tokens is sent as max_completion_tokens (Luna rejects max_tokens); temperature stays at Luna's default of 1.
# reasoning_effort must be "none": Luna on /v1/chat/completions refuses function tools when reasoning is on.
SETTINGS = OpenAIChatModelSettings(max_tokens=MAX_OUTPUT_TOKENS, openai_reasoning_effort="none")


def load_prompt(name: AgentName) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


async def delegate(ctx: RunContext[TeamDeps], to: AgentName, task: str) -> str:
    """Hand part of this ticket to a teammate and get their report back.

    Args:
        to: The teammate: boss, inventory, accounting, facilities, or customer_service.
        task: A complete, self-contained brief. Include the ticket id, the facts you already
            have (numbers and ids), and exactly what you need back. The teammate cannot see
            your conversation.
    """
    from backend.team import run_delegation  # imported here: team.py imports the agents

    return await run_delegation(ctx, to, task)


def run_context(ctx: RunContext[TeamDeps]) -> str:
    """Per-run facts appended to every prompt: ticket, hand-off chain, and what delegation is still allowed."""
    deps = ctx.deps
    budget = deps.budget
    left = budget.max_delegations - budget.delegations_used
    waiting = [n for n in deps.chain if n != deps.agent]
    open_to = [n for n in AGENT_NAMES if n != deps.agent and n not in deps.chain]
    lines = [f"Run context: ticket {deps.ticket_id}; you are '{deps.agent}'; "
             f"hand-off chain so far: {' -> '.join(deps.chain)}."]
    if deps.depth < budget.max_depth and left > 0 and open_to:
        lines.append(f"You may delegate to: {', '.join(open_to)}. Hand-offs left for this ticket: {left}.")
    else:
        lines.append("You cannot delegate on this run (depth or hand-off budget reached). Finish with what you "
                     "have and list anything missing as a blocker.")
    if waiting:
        lines.append(f"Do not delegate to {', '.join(waiting)}: they are waiting on your answer.")
    return " ".join(lines)


def make_agent(name: AgentName, output_type: type, mcp_tools: frozenset[str]) -> Agent[TeamDeps, Any]:
    """One team member: its own prompt file, its own MCP tool allowlist, and the shared delegate tool."""
    return Agent(
        MODEL,
        name=name,
        deps_type=TeamDeps,
        output_type=output_type,
        instructions=[load_prompt(name), run_context],
        toolsets=[tools_for(mcp_tools)],
        tools=[delegate],
        model_settings=SETTINGS,
        retries=2,
    )
