import type { AnalyzeRequest, Report } from "./types";

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

export function analyze(req: AnalyzeRequest): Promise<Report> {
  return post<Report>("/analyze", req);
}

export function askQuestion(
  reportId: string,
  question: string
): Promise<{ answer: string; source_ids: string[] }> {
  return post("/qa", { report_id: reportId, question });
}
