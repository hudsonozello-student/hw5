import { persona } from "../agents";
import { Emblem } from "../emblems";
import { approvalTitle, money } from "../format";
import type { Approval, Cash } from "../types";

interface Props {
  approvals: Approval[];
  cash: Cash | null;
  approver: string;
  onApprove: (a: Approval) => void;
  onReject: (a: Approval) => void;
  onOpenTicket: (id: number) => void;
}

export function ApprovalDesk({ approvals, cash, approver, onApprove, onReject, onOpenTicket }: Props) {
  const hasName = approver.trim().length > 0;
  return (
    <section className={`panel signdesk${approvals.length ? " has-pending" : ""}`} aria-label="Signature desk">
      <div className="panel-head">
        <h2>Signature desk</h2>
        {approvals.length > 0 && <span className="count-badge">{approvals.length}</span>}
      </div>

      {approvals.length === 0 ? (
        <div className="empty-slip">
          <Emblem actor="human" size={40} />
          <p className="muted small">Nothing to sign. When an agent prepares a payment or a purchase order, the permission slip lands here.</p>
        </div>
      ) : (
        <ul className="slips">
          {approvals.map((a) => {
            const requester = persona(a.requested_by);
            const after = cash ? cash.balance - a.amount : null;
            return (
              <li key={a.id} className="slip">
                <div className="slip-top">
                  <span className="slip-kind">{approvalTitle(a)}</span>
                  {a.ticket_id !== null && (
                    <button className="link small" onClick={() => onOpenTicket(a.ticket_id!)}>
                      ticket #{a.ticket_id}
                    </button>
                  )}
                </div>
                <div className="slip-amount">{money(a.amount)}</div>
                <p className="slip-reason">“{a.reason}”</p>
                <p className="slip-by small">
                  Prepared by <Emblem actor={a.requested_by} size={18} /> {requester.nickname} ({requester.role})
                  {after !== null && <> · checking after signing: <strong>{money(after)}</strong></>}
                </p>
                <div className="slip-actions">
                  <button className="btn btn-sign" disabled={!hasName} onClick={() => onApprove(a)}>
                    Sign &amp; pay {money(a.amount)}
                  </button>
                  <button className="btn btn-quiet" disabled={!hasName} onClick={() => onReject(a)}>
                    Send back
                  </button>
                </div>
                {!hasName && <p className="hint small">Type your name next to “Signing as” at the top to sign.</p>}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
