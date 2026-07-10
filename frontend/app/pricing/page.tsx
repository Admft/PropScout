"use client";

import { useState } from "react";

const TIERS = [
  {
    id: "single",
    name: "Pay per report",
    price: "$9",
    detail: "1 report credit. No subscription.",
    priceIdEnv: "STRIPE_PRICE_SINGLE",
  },
  {
    id: "pack5",
    name: "5-report pack",
    price: "$35",
    detail: "Best for agents running a few deals a month.",
    priceIdEnv: "STRIPE_PRICE_PACK5",
  },
  {
    id: "pro",
    name: "Pro monthly",
    price: "$49/mo",
    detail: "20 reports / month. Unused credits do not roll over.",
    priceIdEnv: "STRIPE_PRICE_PRO",
  },
];

export default function PricingPage() {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function checkout(tierId: string) {
    setBusy(tierId);
    setError(null);
    try {
      const resp = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier: tierId }),
      });
      const data = await resp.json();
      if (data.url) {
        window.location.href = data.url;
        return;
      }
      setError(
        data.detail ??
          "Stripe Checkout is not configured yet. Set STRIPE_SECRET_KEY and price IDs."
      );
    } catch {
      setError("Checkout failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="page-card">
      <h1>Pricing</h1>
      <p className="sub">
        Pay-as-you-go. Credits are checked before each analysis. No card data is stored on
        HouseFax servers — Stripe hosts checkout and billing.
      </p>
      <div className="pricing-grid">
        {TIERS.map((t) => (
          <div key={t.id} className="pricing-card">
            <h2>{t.name}</h2>
            <p className="price">{t.price}</p>
            <p className="sub">{t.detail}</p>
            <button
              className="primary"
              type="button"
              disabled={busy === t.id}
              onClick={() => checkout(t.id)}
            >
              {busy === t.id ? "Redirecting…" : "Continue to Stripe"}
            </button>
          </div>
        ))}
      </div>
      {error && <div className="error-box">{error}</div>}
    </section>
  );
}
