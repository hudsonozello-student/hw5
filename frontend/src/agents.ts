import type { AgentId } from "./types";

export interface Persona {
  id: AgentId | "human" | "system";
  nickname: string;
  role: string;
  blurb: string;
  color: string; // emblem and accent color
  soft: string; // tinted background for that agent's bubbles
}

// Each agent gets a Yale-inspired persona so you can tell them apart at a glance.
export const TEAM: Persona[] = [
  {
    id: "boss",
    nickname: "Handsome Dan",
    role: "Boss",
    blurb: "Top dog. Reads every ticket, picks who works it, and makes the final call.",
    color: "#00356b",
    soft: "#e7eef7",
  },
  {
    id: "inventory",
    nickname: "Sterling",
    role: "Inventory",
    blurb: "Knows every shelf, every size, and which vendor can restock it.",
    color: "#286dc0",
    soft: "#e9f1fb",
  },
  {
    id: "accounting",
    nickname: "Lux et Ledger",
    role: "Accounting",
    blurb: "Guards the cash and preps every payment for your signature.",
    color: "#3d6b35",
    soft: "#ecf3e9",
  },
  {
    id: "facilities",
    nickname: "Harkness",
    role: "Facilities",
    blurb: "Minds the shop space: the lease, the rent, the landlord.",
    color: "#6b6259",
    soft: "#f2efec",
  },
  {
    id: "customer_service",
    nickname: "Boola",
    role: "Customer service",
    blurb: "Writes the friendly notes. Never hits send.",
    color: "#a64d24",
    soft: "#f9ede6",
  },
];

const HUMAN: Persona = {
  id: "human",
  nickname: "You",
  role: "Approver",
  blurb: "The only one who can move money.",
  color: "#9a7a1c",
  soft: "#fbf4df",
};

const SYSTEM: Persona = { id: "system", nickname: "Desk", role: "System", blurb: "", color: "#5d6677", soft: "#f1f3f6" };

const BY_ID = new Map(TEAM.map((p) => [p.id, p]));

/** Persona for an audit-trail actor: an agent id, "human:<name>", or anything else. */
export function persona(actor: string): Persona {
  const agent = BY_ID.get(actor as AgentId);
  if (agent) return agent;
  if (actor === "human") return HUMAN;
  if (actor.startsWith("human:")) {
    const name = actor.slice("human:".length);
    return name === "desk" ? { ...HUMAN, nickname: "Desk" } : { ...HUMAN, nickname: name };
  }
  return SYSTEM;
}

export const isAgent = (actor: string): actor is AgentId => BY_ID.has(actor as AgentId);
