import type { AnalyzeRequest, Report } from "./types";
import { SAMPLE_REPORT } from "./sample-report";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed (${resp.status})`);
  }
  return resp.json();
}

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed (${resp.status})`);
  }
  return resp.json();
}

export function analyze(req: AnalyzeRequest): Promise<Report> {
  return post<Report>("/analyze", req);
}

export function askQuestion(
  reportId: string,
  question: string
): Promise<{ answer: string; source_ids: string[] }> {
  return post("/qa", { report_id: reportId, question });
}

/** Load a saved report; falls back to the static sample for demo IDs. */
export async function getReport(reportId: string): Promise<Report> {
  if (reportId === SAMPLE_REPORT.report_id || reportId === "123-main-street") {
    return SAMPLE_REPORT;
  }
  try {
    return await get<Report>(`/reports/${encodeURIComponent(reportId)}`);
  } catch {
    // Local demo: if API has no saved report, show sample so the route still works
    if (reportId.startsWith("sample-") || reportId.startsWith("rpt-")) {
      return { ...SAMPLE_REPORT, report_id: reportId };
    }
    throw new Error("Report not found or expired");
  }
}
