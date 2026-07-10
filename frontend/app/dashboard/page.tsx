"use client";

import Link from "next/link";
import { DEMO_REPORTS } from "@/lib/demo-data";
import Stamp from "@/components/Stamp";

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

      <div className="case-list">
        {DEMO_REPORTS.map((r) => (
          <article key={r.id} className="case-row">
            <Stamp variant={r.status === "Ready" ? "ready" : "failed"} text={r.status} size="sm" />
            <div className="case-main">
              <h2>{r.address}</h2>
              <p className="case-when">
                {new Date(r.created_at).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </p>
            </div>
            {r.verdict && <span className="case-verdict">{r.verdict}</span>}
            <div className="case-action">
              {r.status === "Ready" ? (
                <Link href={`/report/${r.id}`}>Open report →</Link>
              ) : (
                <span className="muted-sm">Generation failed — credits were not charged.</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
