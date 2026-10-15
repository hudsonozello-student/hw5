import type { Approval, Ticket } from "./types";

export const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

export const clock = (ts: string) =>
  new Date(ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });

export const shopDay = (day: string) =>
  new Date(`${day}T12:00:00`).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

export const TICKET_TYPE: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Price request",
};

export function ticketDetail(t: Ticket): string {
  if (t.sku) return [t.sku, t.size && `size ${t.size}`, t.qty && `× ${t.qty}`].filter(Boolean).join(" · ");
  if (t.lease_id) return `Lease ${t.lease_id}`;
  if (t.invoice_id) return `Invoice ${t.invoice_id}`;
  return "";
}

export function approvalTitle(a: Pick<Approval, "kind" | "ref_id">): string {
  if (a.kind === "invoice") return `Pay vendor invoice #${a.ref_id}`;
  if (a.kind === "rent") return `Pay rent on lease ${a.ref_id}`;
  return `Purchase order #${a.ref_id}`;
}

/** Tool arguments as a short, readable line: check_stock(CC-TEE-WHITE, S, 1). */
export function argsText(args: unknown): string {
  if (!args || typeof args !== "object") return "";
  return Object.entries(args as Record<string, unknown>)
    .filter(([key, value]) => key !== "actor" && value !== null && value !== undefined && value !== "")
    .map(([, value]) => (typeof value === "string" && value.length > 40 ? `${value.slice(0, 37)}…` : String(value)))
    .join(", ");
}

export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
