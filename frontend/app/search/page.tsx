"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { analyze } from "@/lib/api";
import Link from "next/link";

const STEPS = [
  "Checking credits…",
  "Fetching county & provider records…",
  "Running financial tools…",
  "Drafting cited narrative…",
  "Running eval harness…",
];

function SearchInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [address, setAddress] = useState(params.get("address") ?? "");
  const [price, setPrice] = useState("");
  const [downPct, setDownPct] = useState("20");
  const [intent, setIntent] = useState<"buyer" | "investor">("buyer");
  const [loading, setLoading] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);

  // Demo credit flag — replace with Postgres/Stripe credit check
  const [credits] = useState(() => {
    if (typeof window === "undefined") return 1;
    const raw = localStorage.getItem("housefax_credits");
    return raw == null ? 1 : Number(raw);
  });

  useEffect(() => {
    try {
      const raw = localStorage.getItem("housefax_profile");
      if (!raw) return;
      const p = JSON.parse(raw);
      if (p.default_down_pct) setDownPct(String(p.default_down_pct));
      if (p.role === "investor") setIntent("investor");
      if (p.role === "homebuyer") setIntent("buyer");
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (!loading) return;
    const t = setInterval(() => {
      setStepIdx((i) => (i < STEPS.length - 1 ? i + 1 : i));
    }, 4000);
    return () => clearInterval(t);
  }, [loading]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (credits <= 0) {
      setShowPaywall(true);
      return;
    }

    setLoading(true);
    setStepIdx(0);
    try {
      const result = await analyze({
        address: address.trim(),
        purchase_price: price ? Number(price) : undefined,
        down_payment_pct: downPct ? Number(downPct) / 100 : undefined,
        intent,
      });
      const next = Math.max(0, credits - 1);
      localStorage.setItem("housefax_credits", String(next));
      router.push(`/report/${encodeURIComponent(result.report_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <>
      <section className="search-card">
        <h1>Analyze a property</h1>
        <p className="sub">
          Step 1: address. Step 2: purchase assumptions. Credits remaining (demo):{" "}
          <strong>{credits}</strong>
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
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="price">Purchase price (optional)</label>
              <input
                id="price"
                type="number"
                min="0"
                placeholder="450000"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                disabled={loading}
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
                disabled={loading}
              />
            </div>
            <div className="full">
              <label htmlFor="intent">I am a…</label>
              <select
                id="intent"
                value={intent}
                onChange={(e) => setIntent(e.target.value as "buyer" | "investor")}
                disabled={loading}
              >
                <option value="buyer">Home buyer</option>
                <option value="investor">Investor</option>
              </select>
            </div>
          </div>
          <button className="primary" type="submit" disabled={loading}>
            {loading ? "Generating report…" : "Generate report"}
          </button>
        </form>

        {loading && (
          <div className="progress-box">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((stepIdx + 1) / STEPS.length) * 100}%` }}
              />
            </div>
            <ol className="progress-steps">
              {STEPS.map((s, i) => (
                <li key={s} className={i <= stepIdx ? "done" : ""}>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        )}

        {error && <div className="error-box">{error}</div>}
      </section>

      {showPaywall && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>No credits remaining</h2>
            <p>
              Each report uses one credit. Purchase a pack or subscribe to continue — checkout is
              hosted by Stripe.
            </p>
            <div className="modal-actions">
              <Link href="/pricing" className="primary-link">
                Go to pricing
              </Link>
              <button className="secondary" type="button" onClick={() => setShowPaywall(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<section className="search-card">Loading…</section>}>
      <SearchInner />
    </Suspense>
  );
}
