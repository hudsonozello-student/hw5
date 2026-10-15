// Original Yale-inspired emblems for each agent (drawn here; not official Yale marks).
import type { ReactElement } from "react";
import { persona } from "./agents";

const SERIF = "Georgia, 'Times New Roman', serif";

function Bulldog(): ReactElement {
  return (
    <g>
      {/* ears */}
      <path d="M13 22 C9 12 17 9 22 14 L24 22 Z" fill="#7a5a43" />
      <path d="M51 22 C55 12 47 9 42 14 L40 22 Z" fill="#7a5a43" />
      {/* head and jowls */}
      <path d="M12 32 C12 19 21 14 32 14 C43 14 52 19 52 32 C52 43 46 50 32 50 C18 50 12 43 12 32 Z" fill="#ead9c3" />
      <path d="M25 21 Q32 18 39 21" stroke="#b9987a" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M27 24.5 Q32 22.5 37 24.5" stroke="#b9987a" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* eyes */}
      <circle cx="24" cy="30" r="3.3" fill="#1e1a17" />
      <circle cx="40" cy="30" r="3.3" fill="#1e1a17" />
      <circle cx="25.1" cy="28.9" r="1.1" fill="#fff" />
      <circle cx="41.1" cy="28.9" r="1.1" fill="#fff" />
      {/* muzzle */}
      <ellipse cx="32" cy="40" rx="13" ry="8.6" fill="#f7eee3" />
      <path d="M27 34.6 Q32 31.8 37 34.6 Q36.4 38.6 32 39 Q27.6 38.6 27 34.6 Z" fill="#2a2421" />
      {/* underbite with two proud teeth */}
      <path d="M23.5 42.5 Q32 49 40.5 42.5" stroke="#5c4636" strokeWidth="1.7" fill="#c9806f" strokeLinecap="round" />
      <path d="M26.8 43.4 L28.2 39.9 L29.6 44.3 Z" fill="#fff" />
      <path d="M34.4 44.3 L35.8 39.9 L37.2 43.4 Z" fill="#fff" />
      {/* collar and Y tag */}
      <path d="M17 48.5 Q32 56.5 47 48.5 L46 53 Q32 60.5 18 53 Z" fill="#ffffff" />
      <circle cx="32" cy="57" r="4.6" fill="#ffffff" stroke="#00356b" strokeWidth="1.2" />
      <text x="32" y="59.6" fontSize="7" fontFamily={SERIF} fontWeight="700" textAnchor="middle" fill="#00356b">
        Y
      </text>
    </g>
  );
}

function SterlingStacks(): ReactElement {
  return (
    <g>
      <path d="M15 55 V28 C15 17 22 11 32 9 C42 11 49 17 49 28 V55 Z" fill="#f5efe4" />
      <path d="M32 10 V20 M23.5 19 Q32 13.5 40.5 19" stroke="#8b7b67" strokeWidth="1.3" fill="none" />
      <rect x="17.5" y="33" width="29" height="2.2" fill="#8b7b67" />
      <rect x="17.5" y="45.5" width="29" height="2.2" fill="#8b7b67" />
      <rect x="19.5" y="23.5" width="7" height="9.5" rx="1" fill="#00356b" />
      <rect x="27.5" y="26" width="6" height="7" rx="1" fill="#63aaff" />
      <rect x="34.5" y="22.5" width="9" height="10.5" rx="1" fill="#286dc0" />
      <rect x="19.5" y="37" width="9" height="8.5" rx="1" fill="#286dc0" />
      <rect x="29.5" y="38.5" width="6" height="7" rx="1" fill="#a64d24" />
      <rect x="36.5" y="36" width="7.5" height="9.5" rx="1" fill="#00356b" />
      <text x="39.3" y="30.6" fontSize="5.5" fontFamily={SERIF} fontWeight="700" textAnchor="middle" fill="#fff">
        Y
      </text>
    </g>
  );
}

function LuxEtLedger(): ReactElement {
  return (
    <g>
      <path d="M13 11 H51 V33 C51 46 43 53 32 57 C21 53 13 46 13 33 Z" fill="#ffffff" />
      <path d="M18 23 Q25 20 32 23 V40 Q25 37 18 40 Z" fill="#00356b" />
      <path d="M46 23 Q39 20 32 23 V40 Q39 37 46 40 Z" fill="#00356b" />
      <path d="M20.5 27 H29.5 M20.5 30.5 H29.5 M20.5 34 H27 M34.5 27 H43.5 M34.5 30.5 H43.5 M37 34 H43.5" stroke="#ffffff" strokeWidth="1.2" />
      <circle cx="32" cy="47" r="5.4" fill="#d6a51f" stroke="#a87c0e" strokeWidth="1" />
      <text x="32" y="49.8" fontSize="7.5" fontFamily={SERIF} fontWeight="700" textAnchor="middle" fill="#5e4506">
        $
      </text>
    </g>
  );
}

function HarknessTower(): ReactElement {
  return (
    <g fill="#ffffff">
      <path d="M25 56 V31 H39 V56 Z" />
      <path d="M27.5 31 V21 H36.5 V31 Z" />
      <path d="M29.6 21 L32 7 L34.4 21 Z" />
      <path d="M24.5 31 L26 24.5 L27.5 31 Z M36.5 31 L38 24.5 L39.5 31 Z" />
      <path d="M27.3 21 L28.3 16 L29.3 21 Z M34.7 21 L35.7 16 L36.7 21 Z" />
      <circle cx="32" cy="37" r="3.6" fill="#6b6259" />
      <path d="M32 37 V34.6 M32 37 L33.8 38.1" stroke="#ffffff" strokeWidth="1" strokeLinecap="round" />
      <path d="M29.3 50 V45.8 Q32 42.6 34.7 45.8 V50 Z" fill="#6b6259" />
      <rect x="13" y="55" width="38" height="3" rx="1.5" opacity="0.75" />
    </g>
  );
}

function BoolaPennant(): ReactElement {
  return (
    <g>
      <rect x="15" y="10" width="3.2" height="44" rx="1.6" fill="#ffffff" />
      <path d="M18 12 L52 22.5 L18 33 Z" fill="#ffffff" />
      <text x="28" y="27.4" fontSize="12" fontFamily={SERIF} fontWeight="700" fill="#00356b">
        Y
      </text>
      <path
        d="M29 39 H49 A4 4 0 0 1 53 43 V48.5 A4 4 0 0 1 49 52.5 H39 L34 57 V52.5 H29 A4 4 0 0 1 25 48.5 V43 A4 4 0 0 1 29 39 Z"
        fill="#ffffff"
      />
      <circle cx="33.5" cy="45.8" r="1.6" fill="#a64d24" />
      <circle cx="39" cy="45.8" r="1.6" fill="#a64d24" />
      <circle cx="44.5" cy="45.8" r="1.6" fill="#a64d24" />
    </g>
  );
}

function Signature(): ReactElement {
  return (
    <g>
      <path d="M12 47 C17 37 22 37 23 44 C24 50 29 41 32 43 C35 45 38 44 44 41" stroke="#ffffff" strokeWidth="2.6" fill="none" strokeLinecap="round" />
      <path d="M44 12 L52 20 L36.5 35.5 L29.5 38 L32 31 Z" fill="#ffffff" />
      <path d="M32 31 L29.5 38 L36.5 35.5" fill="#f3e2a8" />
      <path d="M12 52 H50" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="2 3" />
    </g>
  );
}

function DeskMark(): ReactElement {
  return (
    <text x="32" y="44" fontSize="30" fontFamily={SERIF} fontWeight="700" textAnchor="middle" fill="#ffffff">
      Y
    </text>
  );
}

const ART: Record<string, () => ReactElement> = {
  boss: Bulldog,
  inventory: SterlingStacks,
  accounting: LuxEtLedger,
  facilities: HarknessTower,
  customer_service: BoolaPennant,
  human: Signature,
  system: DeskMark,
};

export function Emblem({ actor, size = 40, ring = false }: { actor: string; size?: number; ring?: boolean }) {
  const p = persona(actor);
  const Art = ART[p.id] ?? DeskMark;
  return (
    <span
      className={`emblem${ring ? " emblem-active" : ""}`}
      style={{ width: size, height: size, ["--agent" as string]: p.color }}
      title={`${p.nickname} · ${p.role}`}
    >
      <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label={`${p.nickname}, ${p.role}`}>
        <circle cx="32" cy="32" r="32" fill={p.color} />
        <Art />
      </svg>
    </span>
  );
}

export function PawPrint({ size = 14 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden="true" className="paw">
      <ellipse cx="12" cy="16" rx="5.2" ry="4.4" fill="currentColor" />
      <ellipse cx="5.6" cy="10.5" rx="2.1" ry="2.7" fill="currentColor" />
      <ellipse cx="9.6" cy="6.6" rx="2.1" ry="2.7" fill="currentColor" />
      <ellipse cx="14.4" cy="6.6" rx="2.1" ry="2.7" fill="currentColor" />
      <ellipse cx="18.4" cy="10.5" rx="2.1" ry="2.7" fill="currentColor" />
    </svg>
  );
}
