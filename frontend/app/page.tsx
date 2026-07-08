"use client";

import { useState } from "react";
import { analyze } from "@/lib/api";
import type { Report } from "@/lib/types";
import ReportView from "@/components/ReportView";
import QAPanel from "@/components/QAPanel";

export default function Home() {
  const [address, setAddress] = useState("");
  const [price, setPrice] = useState("");
  const [downPct, setDownPct] = useState("20");
  const [intent, setIntent] = useState<"buyer" | "investor">("buyer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyze({
        address: address.trim(),
        purchase_price: price ? Number(price) : undefined,
        down_payment_pct: downPct ? Number(downPct) / 100 : undefined,
        intent,
      });
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="search-card no-print">
        <h1>Know the house before you buy it.</h1>
        <p className="sub">
          A source-cited due-diligence report for any residential address: payment math,
          rental underwriting, comps, and risk flags — every number computed by
          deterministic tools, every claim cited.
        </p>
        <form onSubmit={onSubmit}>
          <div className="form-grid">
            <div className="full">
              <label htmlFor="address">Property address</label>
              <input
                id="address"
                placeholder="123 Main St, Austin, TX 78704"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="price">Purchase price (optional — defaults to AVM estimate)</label>
              <input
                id="price"
                type="number"
                min="0"
                placeholder="450000"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="down">Down payment %</label>
              <input
                id="down"
                type="number"
                min="0"
                max="100"
                value={downPct}
                onChange={(e) => setDownPct(e.target.value)}
              />
            </div>
            <div className="full">
              <label htmlFor="intent">I am a…</label>
              <select
                id="intent"
                value={intent}
                onChange={(e) => setIntent(e.target.value as "buyer" | "investor")}
              >
                <option value="buyer">Home buyer</option>
                <option value="investor">Investor</option>
              </select>
            </div>
          </div>
          <button className="primary" type="submit" disabled={loading}>
            {loading ? "Analyzing… (30–60s)" : "Generate report"}
          </button>
        </form>
        {error && <div className="error-box">{error}</div>}
      </section>

      {report && (
        <>
          <ReportView report={report} />
          <QAPanel reportId={report.report_id} />
        </>
      )}
    </>
  );
}
