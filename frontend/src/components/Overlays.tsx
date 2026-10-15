import { useEffect, useRef, useState, type ReactNode } from "react";
import { Emblem } from "../emblems";

export interface ModalSpec {
  title: string;
  body: ReactNode;
  confirm: string;
  tone?: "sign" | "danger" | "primary";
  askReason?: boolean;
  onConfirm: (reason: string) => Promise<void> | void;
}

export function Modal({ spec, onClose }: { spec: ModalSpec; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const firstButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    firstButton.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && !working && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, working]);

  const go = async () => {
    setWorking(true);
    try {
      await spec.onConfirm(reason.trim());
      onClose();
    } finally {
      setWorking(false);
    }
  };

  return (
    <div className="scrim" onClick={() => !working && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" onClick={(e) => e.stopPropagation()}>
        <h2 id="modal-title">{spec.title}</h2>
        <div className="modal-body">{spec.body}</div>
        {spec.askReason && (
          <label className="reason">
            <span className="small muted">Why are you sending it back?</span>
            <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} placeholder="e.g. Not this week; cash is needed for rent." />
          </label>
        )}
        <div className="modal-actions">
          <button className="btn btn-quiet" onClick={onClose} disabled={working}>
            Cancel
          </button>
          <button
            ref={firstButton}
            className={`btn btn-${spec.tone ?? "primary"}`}
            onClick={go}
            disabled={working || (spec.askReason && !reason.trim())}
          >
            {working ? "Working…" : spec.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}

export interface Toast {
  id: number;
  tone: "success" | "info" | "error";
  title: string;
  body?: string;
  actor?: string;
}

export function Toasts({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="toasts" aria-live="assertive">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.tone}`} role="status">
          <Emblem actor={t.actor ?? "boss"} size={36} />
          <div>
            <strong>{t.title}</strong>
            {t.body && <p>{t.body}</p>}
          </div>
          <button className="toast-x" onClick={() => onDismiss(t.id)} aria-label="Dismiss">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

/** A burst of falling Yale "Y"s when a ticket is resolved. */
export function Yfetti({ burst }: { burst: number }) {
  if (!burst || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return null;
  return (
    <div className="yfetti" key={burst} aria-hidden="true">
      {Array.from({ length: 28 }, (_, i) => (
        <span
          key={i}
          style={{
            left: `${(i * 37) % 100}%`,
            animationDelay: `${(i % 7) * 0.12}s`,
            fontSize: `${14 + ((i * 7) % 16)}px`,
            color: i % 3 === 0 ? "#63aaff" : i % 3 === 1 ? "#00356b" : "#286dc0",
          }}
        >
          Y
        </span>
      ))}
    </div>
  );
}
