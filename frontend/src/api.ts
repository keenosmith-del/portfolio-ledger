export interface Identity {
  email: string;
  role: "admin" | "analyst" | "reviewer";
  csrf: string;
}
export interface Portfolio {
  id: string;
  name: string;
  adapter: "atlaspm" | "meridianrent";
}
export interface Entity {
  id: string;
  created_at: string;
}
export interface Job extends Entity {
  adapter: string;
  source_key: string;
  status: string;
  accepted: number;
  duplicates: number;
  quarantined: number;
  attempts: number;
  checksum: string;
  filename: string;
  error: string | null;
  completed_at: string | null;
  correlation_id: string;
}
export interface Lease extends Entity {
  external_id: string;
  source_key: string;
  status: string;
  rent: string;
  start_date: string;
  end_date: string | null;
  revision: number;
  raw_id: string;
  version_id: string;
  tenant_id: string;
  unit_id: string;
}
export interface Ledger extends Entity {
  external_id: string;
  lease_id: string;
  amount: string;
  effective_date: string;
  kind: string;
  revision: number;
  raw_id: string;
  reverses_id: string | null;
  reason: string;
  source_key: string;
}
export interface ExceptionRecord extends Entity {
  reason: string;
  severity: string;
  status: string;
  evidence: Record<string, unknown>;
  run_id: string;
  lease_id: string | null;
}
export interface Pricing extends Entity {
  version: number;
  monthly_fee: string;
  effective_from: string;
  rule: string;
}
export interface Preview extends Entity {
  month: string;
  cutoff: string;
  total: string;
  config: { version: number; monthly_fee: string; rule: string };
  unresolved_exceptions: string[];
}
export interface PreviewLine {
  id: string;
  external_id: string;
  eligible: boolean;
  reason: string;
  amount: string;
}
export interface Audit extends Entity {
  action: string;
  resource_id: string;
  actor_id: string;
  correlation_id: string;
  details: Record<string, unknown>;
}
export interface Raw extends Entity {
  external_id: string | null;
  content_hash: string;
  payload: Record<string, unknown>;
  status: string;
  reason: string | null;
  job_id: string;
  row_number: number;
}
export interface Overview {
  leases: number;
  active_leases: number;
  balance: string;
  open_exceptions: number;
  pending_jobs: number;
  failed_jobs: number;
  processed_rows: number;
  quarantined_rows: number;
  last_sync: string | null;
  source_stale: boolean;
  recent_jobs: Job[];
  latest_preview: Preview | null;
}
export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
export interface JobDetail {
  job: Job;
  rows: Raw[];
  offset: number;
  limit: number;
}
export interface PreviewDetail {
  preview: Preview;
  lines: PreviewLine[];
  total: number;
}
let csrf = "";
export function setIdentity(identity: Identity | null) {
  csrf = identity?.csrf ?? "";
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (options.method && options.method !== "GET")
    headers.set("X-CSRF-Token", csrf);
  const response = await fetch(path, {
    ...options,
    headers,
    credentials: "same-origin",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { code?: string; request_id?: string };
    } | null;
    throw new Error(
      `${body?.error?.code?.replaceAll("_", " ") ?? `Request failed (${response.status})`}${body?.error?.request_id ? ` · Reference ${body.error.request_id}` : ""}`,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
