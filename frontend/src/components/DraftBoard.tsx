import { useState } from "react";
import { persona } from "../agents";
import { Emblem } from "../emblems";
import type { Draft } from "../types";

export function DraftBoard({ drafts, ticketId }: { drafts: Draft[]; ticketId: number | null }) {
  const [openId, setOpenId] = useState<number | null>(null);
  const mine = drafts.filter((d) => d.ticket_id === ticketId);
  return (
    <section className="panel drafts" aria-label="Message drafts">
      <div className="panel-head">
        <h2>Drafts on the board</h2>
        <span className="muted small">never sent</span>
      </div>
      {mine.length === 0 ? (
        <p className="muted small">No drafts for {ticketId ? `#${ticketId}` : "this ticket"} yet. Boola writes them; a person decides whether to send.</p>
      ) : (
        <ul className="draft-list">
          {mine.map((d) => (
            <li key={d.id} className="draft">
              <div className="draft-stamp">Draft · not sent</div>
              <p className="small"><span className="muted">To</span> {d.recipient} <span className="muted">({d.audience})</span></p>
              <p className="draft-subject">{d.subject}</p>
              <p className={`draft-body${openId === d.id ? " open" : ""}`}>{d.body}</p>
              <div className="draft-foot">
                <span className="small">
                  <Emblem actor={d.created_by} size={16} /> {persona(d.created_by).nickname}
                </span>
                <button className="link small" onClick={() => setOpenId(openId === d.id ? null : d.id)}>
                  {openId === d.id ? "Collapse" : "Read it all"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
