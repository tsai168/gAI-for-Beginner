/**
 * U05 API client (WBS-B10, ADR-0022 §3).
 *
 * Field names mirror the backend Pydantic schemas (src/api/schemas.py)
 * verbatim — no renaming — per the same Data Contract discipline the
 * Python side follows (CLAUDE.md §6).
 *
 * Auth: there is no OIDC login flow in this batch (out of scope — Work-1
 * §3.9 describes U01-U04 as screens, not an identity provider integration).
 * `setToken` lets the UI hold a bearer token obtained however the
 * deployment's IdP issues one; every request attaches it as
 * `Authorization: Bearer <token>` so the real backend JWT verification
 * (src/api/auth.py) is exercised end-to-end once a token is present.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const TOKEN_STORAGE_KEY = "cpoai_token";

export class ApiClientError extends Error {
  readonly status: number;
  readonly errorCode: string;

  constructor(status: number, errorCode: string, message: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

interface ApiErrorBody {
  error_code?: string;
  message?: unknown;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let body: ApiErrorBody = {};
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      // no JSON body to parse — fall through with the defaults below
    }
    throw new ApiClientError(
      response.status,
      body.error_code ?? "API-ERR-UNKNOWN",
      typeof body.message === "string" ? body.message : response.statusText,
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      qs.set(key, String(value));
    }
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

// --- schemas (mirrors src/api/schemas.py) -----------------------------------

export interface CompanyOut {
  company_id: string;
  company_name: string;
  universe: string;
  stock_code: string | null;
  listing_market: string | null;
  is_overseas: boolean;
  cfl_status: string;
  confidence: number | null;
}

export interface CompanyDetailOut extends CompanyOut {
  evidence_ids: string[];
}

export interface EventOut {
  event_id: string;
  project_id: string;
  entity_id: string | null;
  source_id: string | null;
  occurred_at: string | null;
  published_at: string | null;
  retrieved_at: string;
  pipeline_status: string;
  version: number;
  correlation_id: string | null;
  causation_id: string | null;
  confidence: number | null;
  evidence_ids: string[];
  cfl_status: string;
  created_at: string;
}

export interface EventDetailOut extends EventOut {
  revision_chain: string[];
}

export interface CflDecisionRequest {
  table: string;
  row_id: string;
  target: string;
}

export interface CflDecisionResponse {
  table: string;
  row_id: string;
  cfl_status: string;
}

// --- endpoints ---------------------------------------------------------------

export function listCompanies(
  params: { universe?: string; q?: string; cfl_status?: string } = {},
): Promise<CompanyOut[]> {
  return request<CompanyOut[]>(`/companies${buildQuery(params)}`);
}

export function getCompany(companyId: string): Promise<CompanyDetailOut> {
  return request<CompanyDetailOut>(`/companies/${companyId}`);
}

export function listEvents(
  params: {
    pipeline_status?: string;
    min_materiality?: number;
    correlation_id?: string;
    cfl_status?: string;
    entity_id?: string;
  } = {},
): Promise<EventOut[]> {
  return request<EventOut[]>(`/events${buildQuery(params)}`);
}

export function getEvent(eventId: string): Promise<EventDetailOut> {
  return request<EventDetailOut>(`/events/${eventId}`);
}

export function decideCfl(
  cflId: string,
  body: CflDecisionRequest,
): Promise<CflDecisionResponse> {
  return request<CflDecisionResponse>(`/cfl/${cflId}/decision`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
