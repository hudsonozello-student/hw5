import { TEAM, persona } from "../agents";
import { Emblem } from "../emblems";
import { money } from "../format";
import type { RunView } from "../runModel";
import type { SpecialistReport } from "../types";

function List({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="mini-list">
      <span className="mini-title">{title}</span>
      <ul>
        {items.map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

export function TeamSummary({ view }: { view: RunView }) {
  if (!view.runId) {
    return <div className="empty-state"><p className="muted">No run yet for this ticket, so nobody has done anything. Yet.</p></div>;
  }
  const decision = view.bossDecision;
  const usage = view.runEnd?.data?.usage;

  return (
    <div className="summary">
      {decision ? (
        <div className="boss-call">
          <Emblem actor="boss" size={48} />
          <div>
            <span className="mini-title">The boss's call at the end of the run · recorded as: {decision.status.replace("_", " ")}</span>
            <p className="boss-decision">{decision.decision}</p>
            <List title="Waiting on you" items={decision.waiting_on_human} />
            <List title="Next steps" items={decision.next_steps} />
          </div>
        </div>
      ) : (
        <div className="boss-call pending">
          <Emblem actor="boss" size={48} />
          <p className="muted">{view.running ? "The team is still working. The boss's call shows up here when they finish." : "This run ended without a final call."}</p>
        </div>
      )}

      {view.humanDecisions.length > 0 && (
        <div className="human-call">
          <Emblem actor="human" size={40} />
          <div>
            <span className="mini-title">After the run · signed by a human</span>
            <ul>
              {view.humanDecisions.map((e) => {
                const r = e.data?.result ?? {};
                const req = e.data?.request ?? {};
                return (
                  <li key={e.seq}>
                    <strong>{e.agent.replace("human:", "")}</strong>{" "}
                    {r.ok && r.paid !== undefined
                      ? <>signed approval #{req.id}: paid <strong>{money(r.paid)}</strong>; {r.change}.</>
                      : r.ok ? <>sent back request #{req.id}.</> : <>tried request #{req.id}: {r.error}</>}
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}

      <div className="summary-grid">
        {TEAM.map((p) => {
          const a = view.agents[p.id as keyof RunView["agents"]];
          const report = a.report as (SpecialistReport & { decision?: string }) | null;
          const tools = Object.entries(a.tools);
          return (
            <article key={p.id} className={`summary-card${a.called ? "" : " not-called"}`} style={{ ["--agent" as string]: p.color, ["--soft" as string]: p.soft }}>
              <header>
                <Emblem actor={p.id} size={36} />
                <div>
                  <strong>{p.nickname}</strong>
                  <span className="muted"> · {p.role}</span>
                </div>
              </header>
              {!a.called ? (
                <p className="muted small">{view.running ? "Standing by." : "Not needed on this ticket. The boss didn't call everyone."}</p>
              ) : (
                <>
                  {p.id !== "boss" && report?.summary && <p>{report.summary}</p>}
                  {tools.length > 0 && (
                    <div className="tool-row">
                      {tools.map(([name, n]) => (
                        <code key={name} className="tool-chip">
                          {name}{n > 1 ? ` ×${n}` : ""}
                        </code>
                      ))}
                    </div>
                  )}
                  {a.handoffs.map((h, i) => (
                    <p key={i} className="small handoff-line">
                      → asked <Emblem actor={h.to} size={16} /> <strong>{persona(h.to).nickname}</strong> for help
                    </p>
                  ))}
                  {p.id !== "boss" && (
                    <>
                      <List title="Did" items={report?.actions} />
                      {report?.recommendation && (
                        <p className="small"><span className="mini-title">Recommends</span> {report.recommendation}</p>
                      )}
                      <List title="Blocked by" items={report?.blockers} />
                    </>
                  )}
                  {p.id === "boss" && <List title="Recorded" items={decision?.actions} />}
                  {!report && <p className="muted small">{a.status}…</p>}
                </>
              )}
            </article>
          );
        })}
      </div>

      {usage && (
        <p className="run-stats muted small">
          This run: {usage.requests} model calls · {usage.tool_calls} tool calls ·{" "}
          {((usage.input_tokens ?? 0) + (usage.output_tokens ?? 0)).toLocaleString()} tokens · {view.runEnd?.data?.hand_offs} hand-offs ·{" "}
          {view.runEnd?.data?.seconds}s
        </p>
      )}
    </div>
  );
}
