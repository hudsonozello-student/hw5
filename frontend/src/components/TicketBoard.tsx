import { PawPrint } from "../emblems";
import { TICKET_TYPE, money, ticketDetail } from "../format";
import type { RunInfo, Ticket } from "../types";

interface Props {
  tickets: Ticket[];
  selectedId: number | null;
  activeRun: RunInfo | null;
  ranBefore: Set<number>;
  onSelect: (id: number) => void;
  onRun: (id: number) => void;
}

function badge(t: Ticket, running: boolean): { label: string; cls: string } {
  if (running) return { label: "Team at work", cls: "badge-running" };
  switch (t.status) {
    case "resolved":
      return { label: "Resolved", cls: "badge-resolved" };
    case "declined":
      return { label: "Declined", cls: "badge-declined" };
    case "waiting_approval":
      return { label: "Needs your signature", cls: "badge-sign" };
    case "in_progress":
      return { label: "In progress", cls: "badge-progress" };
    default:
      return { label: "Open", cls: "badge-open" };
  }
}

export function TicketBoard({ tickets, selectedId, activeRun, ranBefore, onSelect, onRun }: Props) {
  const open = tickets.filter((t) => t.state === "open").length;
  return (
    <section className="panel tickets" aria-label="Tickets">
      <div className="panel-head">
        <h2>Today's tickets</h2>
        <span className="muted">{open} open · {tickets.length - open} resolved</span>
      </div>

      <ol className="ticket-list">
        {tickets.map((t) => {
          const running = activeRun?.ticket_id === t.id;
          const b = badge(t, running);
          const selected = t.id === selectedId;
          const pending = t.pending_approvals.reduce((sum, a) => sum + a.amount, 0);
          return (
            <li key={t.id}>
              <div
                className={`ticket-card ${b.cls}${selected ? " selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-pressed={selected}
                onClick={() => onSelect(t.id)}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(t.id)}
              >
                <div className="ticket-top">
                  <span className="ticket-no">#{t.id}</span>
                  <span className="ticket-type">{TICKET_TYPE[t.type] ?? t.type}</span>
                  <span className={`badge ${b.cls}`}>
                    {running && <PawPrint size={12} />} {b.label}
                  </span>
                </div>
                <h3>{t.subject}</h3>
                <p className="ticket-who">{t.requester}</p>
                {ticketDetail(t) && <p className="ticket-detail">{ticketDetail(t)}</p>}

                {running && (
                  <div className="paw-trail" aria-hidden="true">
                    {Array.from({ length: 6 }, (_, i) => (
                      <span key={i} style={{ animationDelay: `${i * 0.25}s` }}>
                        <PawPrint size={13} />
                      </span>
                    ))}
                  </div>
                )}
                {t.pending_approvals.length > 0 && !running && (
                  <p className="ticket-sign">
                    ✍ {t.pending_approvals.length} to sign · {money(pending)}
                  </p>
                )}
                {t.last_note && !running && <p className="ticket-note">“{t.last_note}”</p>}

                {t.state === "resolved" && (
                  <div className="stamp-row">
                    <div className="stamp" aria-label={`Ticket ${t.id} ${t.status}`}>
                      {t.status === "declined" ? "Declined" : "Resolved"}
                      <small>Campus Customs · {t.created_at.slice(0, 10)}</small>
                    </div>
                  </div>
                )}

                {selected && (
                  <button
                    className="btn btn-primary btn-run"
                    disabled={activeRun !== null}
                    onClick={(e) => {
                      e.stopPropagation();
                      onRun(t.id);
                    }}
                    title={activeRun ? `The team is busy on #${activeRun.ticket_id}` : "Start the agent team on this ticket"}
                  >
                    {running ? "Team is on it…" : activeRun ? `Team busy on #${activeRun.ticket_id}` : ranBefore.has(t.id) ? "Run the team again" : "Send in the team"}
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
