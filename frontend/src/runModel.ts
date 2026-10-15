// Turns the audit-trail event stream into what the board shows for one ticket's latest run.
import { isAgent, persona } from "./agents";
import type { AgentId, DeskEvent, SpecialistReport, TicketDecision } from "./types";

export type Tone = "idle" | "busy" | "waiting" | "done" | "blocked";

export interface AgentRunState {
  called: boolean;
  status: string;
  tone: Tone;
  tools: Record<string, number>;
  handoffs: { to: string; task: string }[];
  report: SpecialistReport | TicketDecision | null;
}

export interface RunSummary {
  runId: string;
  n: number;
  outcome: string | null; // completed | error | cancelled | stopped_by_budget | null while running
  status: string | null; // the boss's recorded ticket status, when the run finished cleanly
}

export interface RunView {
  runId: string | null;
  runs: RunSummary[];
  humanDecisions: DeskEvent[];
  feed: DeskEvent[];
  running: boolean;
  runEnd: DeskEvent | null;
  bossDecision: TicketDecision | null;
  agents: Record<AgentId, AgentRunState>;
  activeAgent: AgentId | null;
  chain: string[];
}

const QUIET_TOOLS = new Set(["final_result", "delegate"]);

/** Events after the most recent database reset (a reset starts the story over). */
export function sinceLastReset(events: DeskEvent[]): DeskEvent[] {
  let cut = -1;
  for (const e of events) if (e.event === "db_reset") cut = e.seq;
  return cut < 0 ? events : events.filter((e) => e.seq > cut);
}

function emptyAgents(status: string): Record<AgentId, AgentRunState> {
  const blank = (): AgentRunState => ({
    called: false,
    status,
    tone: "idle",
    tools: {},
    handoffs: [],
    report: null,
  });
  return { boss: blank(), inventory: blank(), accounting: blank(), facilities: blank(), customer_service: blank() };
}

export function buildRunView(
  events: DeskEvent[],
  ticketId: number | null,
  activeRunId: string | null,
  pickedRunId: string | null = null,
): RunView {
  const forTicket = events.filter((e) => e.ticket_id === ticketId);
  const starts = forTicket.filter((e) => e.event === "run_start");
  const runs: RunSummary[] = starts.map((s, i) => {
    const end = forTicket.find((e) => e.run_id === s.run_id && e.event === "run_end");
    return { runId: s.run_id, n: i + 1, outcome: end?.data?.outcome ?? null, status: end?.data?.output?.status ?? null };
  });
  const start =
    starts.find((e) => e.run_id === activeRunId) ?? starts.find((e) => e.run_id === pickedRunId) ?? starts[starts.length - 1];
  if (!start) {
    return { runId: null, runs, humanDecisions: [], feed: [], running: false, runEnd: null, bossDecision: null, agents: emptyAgents("Ready"), activeAgent: null, chain: [] };
  }

  const runId = start.run_id;
  const running = runId === activeRunId;
  const nextStart = starts.find((e) => e.seq > start.seq)?.seq ?? Infinity;
  // A run's story includes the human decisions made after it, up to the next run on the ticket.
  const feed = forTicket.filter(
    (e) => e.run_id === runId || (e.agent.startsWith("human:") && e.seq > start.seq && e.seq < nextStart),
  );
  const humanDecisions = feed.filter((e) => e.event === "human_decision");
  const agents = emptyAgents(running ? "Standing by" : "Not needed this time");
  let runEnd: DeskEvent | null = null;

  for (const e of feed) {
    if (e.event === "run_end") runEnd = e;
    if (!isAgent(e.agent) || e.run_id !== runId) continue;
    const a = agents[e.agent];
    const d = e.data ?? {};
    switch (e.event) {
      case "agent_start":
        Object.assign(a, { called: true, status: "Reading the brief", tone: "busy" });
        break;
      case "model_response": {
        const names: string[] = (d.tool_calls ?? []).map((c: { tool: string }) => c.tool);
        for (const n of names) if (!QUIET_TOOLS.has(n)) a.tools[n] = (a.tools[n] ?? 0) + 1;
        const working = names.filter((n) => !QUIET_TOOLS.has(n));
        if (names.includes("final_result")) Object.assign(a, { status: "Writing up the report", tone: "busy" });
        else if (working.length) Object.assign(a, { status: `Using ${working.join(", ")}`, tone: "busy" });
        else if ((d.text ?? []).length) Object.assign(a, { status: "Thinking it through", tone: "busy" });
        break;
      }
      case "delegation_start":
        a.handoffs.push({ to: d.to, task: d.task });
        Object.assign(a, { status: `Waiting on ${persona(d.to).nickname}`, tone: "waiting" });
        break;
      case "delegation_end":
        Object.assign(a, { status: "Reading the report", tone: "busy" });
        break;
      case "delegation_refused":
        Object.assign(a, { status: "Hand-off blocked by a guardrail", tone: "blocked" });
        break;
      case "agent_end":
        Object.assign(a, { status: "Done", tone: "done", report: d.output ?? null });
        break;
      case "limit_exceeded":
      case "error":
        Object.assign(a, { status: "Stopped", tone: "blocked" });
        break;
    }
  }

  const last = [...feed].reverse().find((e) => e.run_id === runId && isAgent(e.agent));
  const bossDecision = (agents.boss.report as TicketDecision | null) ?? (runEnd?.data?.output as TicketDecision | undefined) ?? null;
  return {
    runId,
    runs,
    humanDecisions,
    feed,
    running,
    runEnd,
    bossDecision,
    agents,
    activeAgent: running && last && isAgent(last.agent) ? last.agent : null,
    chain: running && last ? last.chain : [],
  };
}
