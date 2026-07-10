"use client";

import Link from "next/link";
import { DEMO_REPORTS } from "@/lib/demo-data";

export default function DashboardPage() {
  return (
    <section className="page-card">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="sub">Past addresses you&apos;ve analyzed.</p>
        </div>
        <Link href="/search" className="primary-link">
          New analysis →
        </Link>
      </div>

      <div className="report-grid">
        {DEMO_REPORTS.map((r) => (
          <article key={r.id} className="report-tile">
            <div className="tile-top">
              <span className={`badge ${r.status === "Ready" ? "strong" : "pass"}`}>
                {r.status}
              </span>
              {r.verdict && <span className="badge muted">{r.verdict}</span>}
            </div>
            <h2>{r.address}</h2>
            <p className="muted-sm">
              {new Date(r.created_at).toLocaleString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </p>
            {r.status === "Ready" ? (
              <Link href={`/report/${r.id}`}>Open report →</Link>
            ) : (
              <span className="muted-sm">Generation failed — credits were not charged.</span>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
