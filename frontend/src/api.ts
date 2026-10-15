// Every call the desk makes goes to the FastAPI backend from Problem 7.
import type {
  ApprovalsResponse,
  ApproveResult,
  Cash,
  DraftsResponse,
  EventsResponse,
  ResetResult,
  RunInfo,
  TicketsResponse,
} from "./types";

export const API_BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function describe(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object" && "error" in detail) return String((detail as { error: unknown }).error);
    return JSON.stringify(detail);
  }
  return "Unexpected response from the desk API.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, describe(body));
  return body as T;
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  tickets: () => request<TicketsResponse>("/tickets"),
  runTicket: (ticketId: number) => post<RunInfo>(`/tickets/${ticketId}/run`),
  run: (runId: string) => request<RunInfo>(`/runs/${runId}`),
  events: (after: number | null) =>
    request<EventsResponse>(`/events?detail=true&limit=500${after === null ? "" : `&after=${after}`}`),
  approvals: () => request<ApprovalsResponse>("/approvals"),
  approve: (id: number, approvedBy: string) => post<ApproveResult>(`/approvals/${id}/approve`, { approved_by: approvedBy }),
  reject: (id: number, rejectedBy: string, reason: string) =>
    post<{ ok: boolean }>(`/approvals/${id}/reject`, { rejected_by: rejectedBy, reason }),
  cash: () => request<Cash>("/cash"),
  drafts: () => request<DraftsResponse>("/drafts"),
  reset: () => post<ResetResult>("/reset"),
};
