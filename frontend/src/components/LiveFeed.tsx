import { useEffect, useRef, useState, type ReactNode } from "react";
import { persona } from "../agents";
import { Emblem, PawPrint } from "../emblems";
import { argsText, clock, money } from "../format";
import type { RunView } from "../runModel";
import type { DeskEvent } from "../types";

function Clip({ text, limit = 220 }: { text: string; limit?: number }) {
  const [open, setOpen] = useState(false);
  if (text.length <= limit) return <>{text}</>;
  return (
    <>
      {open ? text : `${text.slice(0, limit)}…`}{" "}
      <button className="link" onClick={() => setOpen(!open)}>
        {open ? "less" : "more"}
      </button>
    </>
  );
}

function Bubble({ e, kind, children }: { e: DeskEvent; kind: string; children: ReactNode }) {
  const p = persona(e.agent);
  return (
    <li className={`bubble bubble-${kind}`} style={{ ["--agent" as string]: p.color, ["--soft" as string]: p.soft, marginLeft: Math.min(e.chain.length - 1, 3) * 22 }}>
      <Emblem actor={e.agent} size={34} />
      <div className="bubble-body">
        <div className="bubble-head">
          <strong>{p.nickname}</strong>
          <span className="muted">{p.role}</span>
          <time className="muted">{clock(e.ts)}</time>
        </div>
        {children}
      </div>
    </li>
  );
}

function Banner({ e, tone, children }: { e: DeskEvent; tone: string; children: ReactNode }) {
  return (
    <li className={`banner banner-${tone}`}>
      <PawPrint size={14} /> <span>{children}</span> <time className="muted">{clock(e.ts)}</time>
    </li>
  );
}

function FeedItem({ e }: { e: DeskEvent }) {
  const d = e.data ?? {};
  switch (e.event) {
    case "run_start":
      return <Banner e={e} tone="start">The team picked up ticket #{e.ticket_id}</Banner>;
    case "agent_start":
      return (
        <Bubble e={e} kind="brief">
          <p className="muted small">Picked up the brief:</p>
          <blockquote><Clip text={d.task ?? ""} limit={180} /></blockquote>
        </Bubble>
      );
    case "model_response": {
      const calls = (d.tool_calls ?? []).filter((c: { tool: string }) => c.tool !== "final_result" && c.tool !== "delegate");
      const text: string = (d.text ?? []).join(" ").trim();
      if (!calls.length && !text) return null; // hand-offs and final reports have their own bubbles
      return (
        <Bubble e={e} kind="work">
          {text && <p><Clip text={text} /></p>}
          {calls.length > 0 && (
            <div className="tool-row">
              {calls.map((c: { tool: string; tool_call_id: string; args: unknown }) => (
                <code key={c.tool_call_id} className="tool-chip">
                  {c.tool}({argsText(c.args)})
                </code>
              ))}
            </div>
          )}
        </Bubble>
      );
    }
    case "delegation_start":
      return (
        <Bubble e={e} kind="handoff">
          <p className="handoff-line">
            Hands off to <Emblem actor={d.to} size={20} /> <strong>{persona(d.to).nickname}</strong>
          </p>
          <blockquote><Clip text={d.task ?? ""} /></blockquote>
        </Bubble>
      );
    case "delegation_refused":
      return (
        <Bubble e={e} kind="refused">
          <p>Tried to hand off to {persona(d.to).nickname}, but a guardrail said no: <em>{d.reason}</em></p>
        </Bubble>
      );
    case "delegation_end":
      return (
        <Bubble e={e} kind="return">
          <p className="handoff-line">
            <Emblem actor={d.to} size={20} /> <strong>{persona(d.to).nickname}</strong> reported back
          </p>
          <blockquote><Clip text={d.report?.summary ?? d.report?.decision ?? ""} /></blockquote>
        </Bubble>
      );
    case "agent_end": {
      const out = d.output ?? {};
      return (
        <Bubble e={e} kind={e.agent === "boss" ? "decision" : "done"}>
          <p className="done-label">{e.agent === "boss" ? "The boss's call" : "Done"}</p>
          <p><Clip text={out.decision ?? out.summary ?? ""} limit={320} /></p>
        </Bubble>
      );
    }
    case "run_end": {
      const u = d.usage ?? {};
      const tone = d.outcome === "completed" ? "end" : "bad";
      return (
        <Banner e={e} tone={tone}>
          Run {d.outcome === "completed" ? "finished" : d.outcome?.replaceAll("_", " ")} · {u.requests} model calls · {u.tool_calls} tool calls ·{" "}
          {((u.input_tokens ?? 0) + (u.output_tokens ?? 0)).toLocaleString()} tokens · {d.hand_offs} hand-offs · {d.seconds}s
        </Banner>
      );
    }
    case "human_decision": {
      const r = d.result ?? {};
      return (
        <Bubble e={e} kind="human">
          <p>
            {r.ok && r.paid !== undefined
              ? `Signed and paid ${money(r.paid)}: ${r.change}.`
              : r.ok
                ? `Sent back request #${d.request?.id}.`
                : `Tried to decide request #${d.request?.id}: ${r.error}`}
          </p>
        </Bubble>
      );
    }
    case "limit_exceeded":
    case "error":
      return <Banner e={e} tone="bad">Stopped: {d.error}</Banner>;
    default:
      return null;
  }
}

export function LiveFeed({ view }: { view: RunView }) {
  const listRef = useRef<HTMLOListElement>(null);
  const pinned = useRef(true);

  useEffect(() => {
    const el = listRef.current;
    if (el && pinned.current) el.scrollTop = el.scrollHeight;
  }, [view.feed.length]);

  if (!view.runId) {
    return (
      <div className="empty-state">
        <div className="sleepy">
          <Emblem actor="boss" size={84} />
          <span className="zzz">z z z</span>
        </div>
        <p><strong>Handsome Dan is napping.</strong></p>
        <p className="muted">Pick a ticket and press <em>Send in the team</em> to watch the agents work it, step by step.</p>
      </div>
    );
  }

  return (
    <ol
      className="feed"
      ref={listRef}
      aria-live="polite"
      onScroll={(e) => {
        const el = e.currentTarget;
        pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
      }}
    >
      {view.feed.map((e) => (
        <FeedItem key={e.seq} e={e} />
      ))}
      {view.running && (
        <li className="typing" aria-hidden="true">
          <span /> <span /> <span />
        </li>
      )}
    </ol>
  );
}
