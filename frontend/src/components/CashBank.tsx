import { useEffect, useRef, useState } from "react";
import { money } from "../format";
import { useAnimatedNumber } from "../hooks";
import type { Cash } from "../types";

const KIND: Record<string, string> = { invoice: "Vendor invoice", rent: "Rent, lease", purchase_order: "Purchase order" };

export function CashBank({ cash }: { cash: Cash | null }) {
  const balance = cash?.balance ?? 0;
  const shown = useAnimatedNumber(cash ? cash.balance : null);
  const previous = useRef<number | null>(null);
  const [delta, setDelta] = useState<{ amount: number; key: number } | null>(null);

  useEffect(() => {
    if (!cash) return;
    if (previous.current !== null && previous.current !== cash.balance) {
      setDelta({ amount: cash.balance - previous.current, key: Date.now() });
    }
    previous.current = cash.balance;
  }, [cash]);

  const pending = cash?.pending_total ?? 0;
  const pendingPct = balance > 0 ? Math.min((pending / balance) * 100, 100) : 0;

  return (
    <section className="panel bank" aria-label="Checking balance">
      <div className="scoreboard">
        <div className="scoreboard-label">
          <span>Bulldog Bank</span>
          <span className="muted">checking · as of {cash?.as_of ?? "…"}</span>
        </div>
        <div className="scoreboard-number" aria-live="polite">
          {cash && shown !== null ? money(shown) : "…"}
          {delta && (
            <span key={delta.key} className={`delta ${delta.amount < 0 ? "down" : "up"}`}>
              {delta.amount < 0 ? "−" : "+"}
              {money(Math.abs(delta.amount))}
            </span>
          )}
        </div>
        <div className="cash-bar" role="img" aria-label={`${money(pending)} of ${money(balance)} is waiting for signatures`}>
          <span className="cash-free" style={{ width: `${100 - pendingPct}%` }} />
          <span className="cash-pending" style={{ width: `${pendingPct}%` }} />
        </div>
        <div className="cash-legend">
          <span><i className="key key-free" /> Free {money(cash?.available_after_pending ?? 0)}</span>
          <span><i className="key key-pending" /> Waiting to sign {money(pending)}</span>
        </div>
      </div>

      {cash && cash.recent_payments.length > 0 ? (
        <ul className="payments">
          {cash.recent_payments.slice(0, 4).map((p) => (
            <li key={p.id}>
              <span>
                <strong>{money(p.amount)}</strong> · {KIND[p.kind] ?? p.kind} {p.ref_id}
              </span>
              <span className="muted small">signed by {p.approved_by}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted small bank-note">No payments yet. Money only moves when a human signs. No revenue is modeled, so cash only goes down.</p>
      )}
    </section>
  );
}
