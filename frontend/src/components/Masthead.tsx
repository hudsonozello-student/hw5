import { Emblem } from "../emblems";
import { shopDay } from "../format";

interface Props {
  shopToday: string | null;
  online: boolean;
  approver: string;
  onApprover: (name: string) => void;
  onReset: () => void;
  busy: boolean;
}

export function Masthead({ shopToday, online, approver, onApprover, onReset, busy }: Props) {
  return (
    <header className="masthead">
      <div className="brand">
        <Emblem actor="boss" size={56} />
        <div>
          <h1>Campus Customs Desk</h1>
          <p>Yale SOM · the agents prep, you sign</p>
        </div>
      </div>

      <div className="mast-meta">
        <span className="chip chip-light">Shop day · {shopToday ? shopDay(shopToday) : "loading…"}</span>
        <span className={`chip ${online ? "chip-online" : "chip-offline"}`}>
          <span className="dot" /> {online ? "Desk API connected" : "Desk API offline"}
        </span>
      </div>

      <div className="mast-actions">
        <label className="signer">
          <span>Signing as</span>
          <input value={approver} onChange={(e) => onApprover(e.target.value)} placeholder="Your name" maxLength={60} />
        </label>
        <button className="btn btn-ghost" onClick={onReset} disabled={busy} title="Put the shop back to the original data">
          Fresh start
        </button>
      </div>
    </header>
  );
}
