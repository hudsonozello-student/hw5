import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API_BASE, api } from "./api";
import { ApprovalDesk } from "./components/ApprovalDesk";
import { CashBank } from "./components/CashBank";
import { DraftBoard } from "./components/DraftBoard";
import { LiveFeed } from "./components/LiveFeed";
import { Masthead } from "./components/Masthead";
import { Modal, Toasts, Yfetti, type ModalSpec, type Toast } from "./components/Overlays";
import { TeamRoster } from "./components/TeamRoster";
import { TeamSummary } from "./components/TeamSummary";
import { TicketBoard } from "./components/TicketBoard";
import { approvalTitle, money } from "./format";
import { useStoredString } from "./hooks";
import { buildRunView, sinceLastReset } from "./runModel";
import type { Approval, Cash, DeskEvent, Draft, RunInfo, Ticket } from "./types";

const errText = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** Deep links such as #ticket=103&tab=summary&run=2 open the board on one ticket (and one of its runs). */
function readHash(): { ticket: number | null; tab: "live" | "summary"; run: number | null } {
  const params = new URLSearchParams(window.location.hash.slice(1));
  const ticket = Number(params.get("ticket"));
  const run = Number(params.get("run"));
  return {
    ticket: Number.isInteger(ticket) && ticket > 0 ? ticket : null,
    tab: params.get("tab") === "summary" ? "summary" : "live",
    run: Number.isInteger(run) && run > 0 ? run : null,
  };
}

function mergeEvents(prev: DeskEvent[], incoming: DeskEvent[]): DeskEvent[] {
  const bySeq = new Map(prev.map((e) => [e.seq, e]));
  for (const e of incoming) bySeq.set(e.seq, e);
  return [...bySeq.values()].sort((a, b) => a.seq - b.seq);
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [shopToday, setShopToday] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<RunInfo | null>(null);
  const [cash, setCash] = useState<Cash | null>(null);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [events, setEvents] = useState<DeskEvent[]>([]);
  const [online, setOnline] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(() => readHash().ticket);
  const [tab, setTab] = useState<"live" | "summary">(() => readHash().tab);
  const [runPick, setRunPick] = useState<number | null>(() => readHash().run); // 1-based; null = latest run
  const [approver, setApprover] = useStoredString("campus-customs-approver");
  const [modal, setModal] = useState<ModalSpec | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [burst, setBurst] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const cursor = useRef<number | null>(null);
  const toastId = useRef(0);
  const selectedRef = useRef<number | null>(null);
  selectedRef.current = selectedId;

  useEffect(() => {
    if (selectedId !== null)
      window.history.replaceState(null, "", `#ticket=${selectedId}&tab=${tab}${runPick ? `&run=${runPick}` : ""}`);
  }, [selectedId, tab, runPick]);
  useEffect(() => {
    const onHash = () => {
      const h = readHash();
      if (h.ticket !== null) setSelectedId(h.ticket);
      setTab(h.tab);
      setRunPick(h.run);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const toast = useCallback((t: Omit<Toast, "id">) => {
    const id = ++toastId.current;
    setToasts((all) => [...all, { ...t, id }].slice(-4));
    window.setTimeout(() => setToasts((all) => all.filter((x) => x.id !== id)), 8000);
  }, []);
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  // Desk state: tickets, cash, approvals, drafts. Refreshed every few seconds and after every action.
  useEffect(() => {
    let stop = false;
    let timer = 0;
    const tick = async () => {
      try {
        const [t, c, a, d] = await Promise.all([api.tickets(), api.cash(), api.approvals(), api.drafts()]);
        if (stop) return;
        setTickets(t.tickets);
        setShopToday(t.shop_today);
        setActiveRun(t.active_run);
        setCash(c);
        setApprovals(a.approvals);
        setDrafts(d.drafts);
        setOnline(true);
        setSelectedId((id) => id ?? (t.tickets.find((x) => x.state === "open") ?? t.tickets[0])?.id ?? null);
      } catch {
        if (!stop) setOnline(false);
      }
      if (!stop) timer = window.setTimeout(tick, 2500);
    };
    tick();
    return () => {
      stop = true;
      window.clearTimeout(timer);
    };
  }, [refreshKey]);

  // Agent events: polled fast while a run is live so you can watch each step land.
  const runningId = activeRun?.run_id ?? null;
  useEffect(() => {
    let stop = false;
    let timer = 0;
    const tick = async () => {
      try {
        const res = await api.events(cursor.current);
        if (!stop) {
          if (cursor.current !== null && res.next_after < cursor.current) {
            cursor.current = null; // the trail was replaced; start over
            setEvents([]);
          } else {
            const fresh = cursor.current === null;
            cursor.current = res.next_after;
            if (fresh || res.events.length) setEvents((prev) => mergeEvents(fresh ? [] : prev, res.events));
          }
        }
      } catch {
        // the desk poll above reports the API as offline
      }
      if (!stop) timer = window.setTimeout(tick, runningId ? 900 : 3000);
    };
    tick();
    return () => {
      stop = true;
      window.clearTimeout(timer);
    };
  }, [runningId]);

  // When a run stops being active, find out how it ended and tell the human.
  const announce = useCallback(
    (run: RunInfo) => {
      refresh();
      const where = `ticket #${run.ticket_id}`;
      if (run.status === "completed" && run.decision) {
        const status = run.decision.status;
        if (status === "resolved" || status === "declined") {
          setBurst(Date.now());
          toast({ tone: "success", title: `Boola boola! ${where} is ${status}.`, body: run.decision.decision });
        } else if (status === "waiting_approval") {
          toast({ tone: "info", actor: "human", title: `${where} needs your signature`, body: "The team prepared a payment. Sign it on the signature desk to finish the ticket." });
        } else {
          toast({ tone: "info", title: `The team finished its run on ${where}`, body: run.decision.decision });
        }
        if (run.ticket_id === selectedRef.current) setTab("summary");
      } else if (run.status === "stopped_by_budget") {
        toast({ tone: "error", title: `The run on ${where} hit its token budget`, body: run.error ?? undefined });
      } else if (run.status === "error") {
        toast({ tone: "error", title: `The run on ${where} failed`, body: run.error ?? undefined });
      }
    },
    [refresh, toast],
  );

  const lastRun = useRef<RunInfo | null>(null);
  useEffect(() => {
    const prev = lastRun.current;
    lastRun.current = activeRun;
    if (!prev || activeRun?.run_id === prev.run_id) return;
    api.run(prev.run_id).then(announce).catch(() => {
      refresh();
      toast({ tone: "info", title: `The run on ticket #${prev.ticket_id} ended` });
    });
  }, [activeRun?.run_id]); // only when the active run changes, not on every poll

  const startRun = async (ticketId: number) => {
    try {
      const run = await api.runTicket(ticketId);
      lastRun.current = run;
      setActiveRun(run);
      setRunPick(null);
      setTab("live");
      toast({ tone: "info", title: `Handsome Dan is on ticket #${ticketId}`, body: "Watch the team work in the live desk feed." });
      refresh();
    } catch (e) {
      toast({ tone: "error", title: "Couldn't start the team", body: errText(e) });
    }
  };

  const askApprove = (a: Approval) =>
    setModal({
      title: `Sign for ${money(a.amount)}?`,
      tone: "sign",
      confirm: `Sign & pay ${money(a.amount)}`,
      body: (
        <>
          <p>
            <strong>{approvalTitle(a)}</strong>
            {a.ticket_id !== null && ` · ticket #${a.ticket_id}`}
          </p>
          <p className="muted">“{a.reason}”</p>
          <p>
            The agents only prepared this. Your signature as <strong>{approver.trim()}</strong> moves real money out of checking
            {cash && (
              <>
                : <strong>{money(cash.balance)}</strong> → <strong>{money(cash.balance - a.amount)}</strong>
              </>
            )}
            .
          </p>
        </>
      ),
      onConfirm: async () => {
        try {
          const r = await api.approve(a.id, approver.trim());
          toast({ tone: "success", actor: "human", title: `Signed. Paid ${money(r.paid)}.`, body: `${r.change}. Checking is now ${money(r.new_balance)}.` });
          if (r.ticket_resolved) {
            setBurst(Date.now());
            toast({ tone: "success", title: `Boola boola! Ticket #${a.ticket_id} is resolved.`, body: "Nothing is left to sign on it." });
          }
        } catch (e) {
          toast({ tone: "error", title: "The payment was refused", body: errText(e) });
        }
        refresh();
      },
    });

  const askReject = (a: Approval) =>
    setModal({
      title: `Send back ${approvalTitle(a).toLowerCase()}?`,
      tone: "danger",
      confirm: "Send it back",
      askReason: true,
      body: <p>No money moves. The ticket goes back to the team so they can re-plan.</p>,
      onConfirm: async (reason) => {
        try {
          await api.reject(a.id, approver.trim(), reason);
          toast({ tone: "info", actor: "human", title: `Sent back request #${a.id}`, body: reason });
        } catch (e) {
          toast({ tone: "error", title: "Couldn't send it back", body: errText(e) });
        }
        refresh();
      },
    });

  const askReset = () =>
    setModal({
      title: "Fresh start?",
      tone: "danger",
      confirm: "Reset the shop",
      body: (
        <>
          <p>This puts the shop database back to the original data: the starting cash and all three tickets open. Approvals, drafts, and payments made since go away.</p>
          <p className="muted">The audit trail keeps every past step; the board just starts a new chapter.</p>
        </>
      ),
      onConfirm: async () => {
        try {
          const r = await api.reset();
          toast({ tone: "info", title: "Fresh start", body: `Checking is back to ${money(r.balance)} and every ticket is open.` });
        } catch (e) {
          toast({ tone: "error", title: "Couldn't reset", body: errText(e) });
        }
        refresh();
      },
    });

  const visible = useMemo(() => sinceLastReset(events), [events]);
  const view = useMemo(() => {
    const latest = buildRunView(visible, selectedId, runningId);
    const picked = runPick ? latest.runs[runPick - 1]?.runId ?? null : null;
    return picked && picked !== latest.runId ? buildRunView(visible, selectedId, runningId, picked) : latest;
  }, [visible, selectedId, runningId, runPick]);
  const selectTicket = (id: number) => {
    setSelectedId(id);
    setRunPick(null);
  };
  const ranBefore = useMemo(
    () => new Set(visible.filter((e) => e.event === "run_start" && e.ticket_id !== null).map((e) => e.ticket_id as number)),
    [visible],
  );
  const selected = tickets.find((t) => t.id === selectedId) ?? null;

  return (
    <div className="app">
      <Masthead shopToday={shopToday} online={online} approver={approver} onApprover={setApprover} onReset={askReset} busy={activeRun !== null} />

      {!online && (
        <div className="offline" role="alert">
          Can't reach the desk API at <code>{API_BASE}</code>. Start it from <code>backend/</code> with{" "}
          <code>uvicorn main:app --reload --port 8000</code>.
        </div>
      )}

      <main className="desk">
        <TicketBoard tickets={tickets} selectedId={selectedId} activeRun={activeRun} ranBefore={ranBefore} onSelect={selectTicket} onRun={startRun} />

        <section className="panel stage" aria-label="The agent team">
          <div className="panel-head stage-head">
            <div>
              <h2>{selected ? `#${selected.id} · ${selected.subject}` : "The team"}</h2>
              {view.runs.length > 1 && (
                <div className="run-picker" role="group" aria-label="Runs on this ticket">
                  <span className="muted small">Runs</span>
                  {view.runs.map((r) => (
                    <button
                      key={r.runId}
                      className={`run-chip${r.runId === view.runId ? " on" : ""} ${r.outcome === "completed" ? "ok" : r.outcome ? "bad" : "live"}`}
                      onClick={() => setRunPick(r.n === view.runs.length ? null : r.n)}
                      title={`Run ${r.n}: ${r.outcome ?? "running"}${r.status ? ` · boss recorded ${r.status.replace("_", " ")}` : ""}`}
                    >
                      {r.n} {r.outcome === "completed" ? "✓" : r.outcome ? "✗" : "…"}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="tabs" role="tablist">
              <button role="tab" aria-selected={tab === "live"} onClick={() => setTab("live")}>
                Live desk {view.running && <span className="live-dot" aria-label="live" />}
              </button>
              <button role="tab" aria-selected={tab === "summary"} onClick={() => setTab("summary")}>
                Who did what
              </button>
            </div>
          </div>
          <TeamRoster view={view} />
          {tab === "live" ? <LiveFeed view={view} /> : <TeamSummary view={view} />}
        </section>

        <aside className="side">
          <CashBank cash={cash} />
          <ApprovalDesk approvals={approvals} cash={cash} approver={approver} onApprove={askApprove} onReject={askReject} onOpenTicket={selectTicket} />
          <DraftBoard drafts={drafts} ticketId={selectedId} />
        </aside>
      </main>

      <footer className="footer">
        Agents prepare, people sign. Drafts are never sent. Emblems are original drawings inspired by Yale, not official Yale marks.
      </footer>

      {modal && <Modal spec={modal} onClose={() => setModal(null)} />}
      <Toasts toasts={toasts} onDismiss={(id) => setToasts((all) => all.filter((t) => t.id !== id))} />
      <Yfetti burst={burst} />
    </div>
  );
}
