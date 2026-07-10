"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getReport } from "@/lib/api";
import type { Report } from "@/lib/types";
import ReportView from "@/components/ReportView";
import QAPanel from "@/components/QAPanel";

export default function ReportPage() {
  const params = useParams();
  const addressId = decodeURIComponent(String(params.address_id ?? ""));
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await getReport(addressId);
        if (!cancelled) setReport(r);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Report not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [addressId]);

  if (loading) {
    return <section className="page-card">Loading report…</section>;
  }

  if (error || !report) {
    return (
      <section className="page-card">
        <h1>Report unavailable</h1>
        <p className="sub">{error ?? "Not found"}</p>
        <Link href="/search">Run a new analysis →</Link>
      </section>
    );
  }

  return (
    <>
      <div className="report-toolbar no-print">
        <Link href="/dashboard">← Dashboard</Link>
        <Link href={`/report/${encodeURIComponent(addressId)}/documents`}>
          Documents →
        </Link>
      </div>
      <ReportView report={report} />
      <QAPanel reportId={report.report_id} />
    </>
  );
}
