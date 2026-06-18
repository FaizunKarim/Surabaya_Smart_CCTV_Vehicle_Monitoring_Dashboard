import type {
  CCTVAnalytics,
  CCTVRecord,
  DashboardSocketPayload,
  DashboardSummary,
} from "@/lib/types";

const fallbackApiBase = "http://localhost:8000";

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  return normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL || fallbackApiBase);
}

export function getWsBaseUrl(): string {
  return getApiBaseUrl().replace(/^http/, "ws");
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchCctvs(): Promise<CCTVRecord[]> {
  return fetchJson<CCTVRecord[]>("/api/cctvs");
}

export async function fetchSummary(): Promise<DashboardSummary> {
  return fetchJson<DashboardSummary>("/api/dashboard/summary");
}

export async function fetchAnalytics(cctvId: string): Promise<CCTVAnalytics> {
  return fetchJson<CCTVAnalytics>(`/api/cctvs/${cctvId}/analytics`);
}

export function buildDashboardSocketUrl(selectedCctvId?: string): string {
  const params = new URLSearchParams();
  if (selectedCctvId) {
    params.set("cctv", selectedCctvId);
  }

  const query = params.toString();
  return `${getWsBaseUrl()}/ws/dashboard${query ? `?${query}` : ""}`;
}

export function isDashboardSocketPayload(
  payload: unknown,
): payload is DashboardSocketPayload {
  if (!payload || typeof payload !== "object") {
    return false;
  }
  return (payload as { type?: string }).type === "dashboard_snapshot";
}
