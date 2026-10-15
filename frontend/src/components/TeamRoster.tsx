import { TEAM, persona } from "../agents";
import { Emblem } from "../emblems";
import type { RunView } from "../runModel";

export function TeamRoster({ view }: { view: RunView }) {
  return (
    <div className="roster" aria-label="The agent team">
      <div className="roster-row">
        {TEAM.map((p) => {
          const id = p.id as keyof RunView["agents"];
          const state = view.agents[id];
          const active = view.activeAgent === id;
          return (
            <div key={p.id} className={`player tone-${state.tone}${active ? " active" : ""}`} style={{ ["--agent" as string]: p.color }}>
              <Emblem actor={p.id} size={58} ring={active} />
              <div className="player-name">{p.nickname}</div>
              <div className="player-role">{p.role}</div>
              <div className="player-status" aria-live={active ? "polite" : undefined}>
                {state.status}
              </div>
            </div>
          );
        })}
      </div>
      {view.chain.length > 1 && (
        <div className="relay" aria-label="Hand-off chain">
          <span className="muted">Hand-off chain</span>
          {view.chain.map((a, i) => (
            <span key={`${a}-${i}`} className="relay-step">
              {i > 0 && <span className="relay-arrow">→</span>}
              <Emblem actor={a} size={20} /> {persona(a).nickname}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
