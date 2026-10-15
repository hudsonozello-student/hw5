// Shapes returned by the FastAPI desk API (backend/main.py).

export type AgentId = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";
export type TicketStatus = "open" | "in_progress" | "waiting_approval" | "resolved" | "declined";
export type RunStatus = "running" | "completed" | "stopped_by_budget" | "error" | "cancelled";

export interface ApprovalRef {
  id: number;
  kind: string;
  ref_id: number;
  amount: number;
  status: string;
  requested_by: string;
  decided_by: string | null;
}

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  status: TicketStatus;
  created_at: string;
  state: "open" | "resolved";
  last_note: string | null;
  pending_approvals: ApprovalRef[];
  draft_count: number;
  running: boolean;
}

export interface TicketDecision {
  ticket_id: number;
  decision: string;
  status: TicketStatus;
  delegated_to: AgentId[];
  actions: string[];
  waiting_on_human: string[];
  next_steps: string[];
}

export interface SpecialistReport {
  summary: string;
  facts: string[];
  actions: string[];
  recommendation: string;
  blockers: string[];
}

export interface RunInfo {
  run_id: string;
  ticket_id: number;
  status: RunStatus;
  started_at: string;
  finished_at: string | null;
  decision: TicketDecision | null;
  error: string | null;
}

export interface TicketsResponse {
  shop_today: string;
  active_run: RunInfo | null;
  tickets: Ticket[];
}

export interface Payment {
  id: number;
  kind: string;
  ref_id: number;
  amount: number;
  paid_at: string;
  approved_by: string;
}

export interface Cash {
  shop_today: string;
  account: string;
  balance: number;
  as_of: string;
  pending_requests: number;
  pending_total: number;
  available_after_pending: number;
  recent_payments: Payment[];
}

export interface Approval {
  id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number;
  amount: number;
  ticket_id: number | null;
  reason: string;
  requested_by: string;
  status: "pending" | "approved" | "rejected";
  decided_by: string | null;
  decision_note: string | null;
  payment_id: number | null;
  shop_date: string;
}

export interface ApprovalsResponse {
  count: number;
  approvals: Approval[];
}

export interface Draft {
  id: number;
  ticket_id: number | null;
  audience: string;
  recipient: string;
  subject: string;
  body: string;
  status: string;
  created_by: string;
  created_at: string;
}

export interface DraftsResponse {
  count: number;
  drafts: Draft[];
}

// One audit-trail event. `data` is the raw event payload (the API is called with detail=true).
export interface DeskEvent {
  seq: number;
  ts: string;
  run_id: string;
  ticket_id: number | null;
  agent: string;
  chain: string[];
  event: string;
  step: number;
  said: string | null;
  tools: string[];
  data?: any; // payload shape depends on `event` (see backend/team.py)
}

export interface EventsResponse {
  next_after: number;
  count: number;
  events: DeskEvent[];
}

export interface ApproveResult {
  ok: boolean;
  approval_id: number;
  payment_id: number;
  paid: number;
  kind: string;
  ref_id: number;
  change: string;
  new_balance: number;
  approved_by: string;
  ticket_resolved: boolean;
}

export interface ResetResult {
  ok: boolean;
  balance: number;
  tickets: Record<string, string>;
}
