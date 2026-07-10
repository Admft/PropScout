"use client";

import Link from "next/link";
import { useState } from "react";

export default function BillingSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function openPortal() {
    setLoading(true);
    setMessage(null);
    try {
      const resp = await fetch("/api/billing/portal", { method: "POST" });
      const data = await resp.json();
      if (data.url) {
        window.location.href = data.url;
        return;
      }
      setMessage(
        data.detail ??
          "Stripe Customer Portal is not configured yet. Set STRIPE_SECRET_KEY to enable."
      );
    } catch {
      setMessage("Could not open billing portal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-card">
      <div className="page-header">
        <h1>Billing</h1>
        <Link href="/settings/profile" className="nav-link">
          ← Profile
        </Link>
      </div>
      <p className="sub">
        Manage payment methods, invoices, and subscriptions via Stripe&apos;s hosted Customer
        Portal — HouseFax never stores card numbers.
      </p>
      <button className="primary" type="button" onClick={openPortal} disabled={loading}>
        {loading ? "Opening…" : "Open Stripe Customer Portal"}
      </button>
      {message && <div className="error-box">{message}</div>}
      <p className="hint">
        Need credits? See <Link href="/pricing">Pricing</Link>.
      </p>
    </section>
  );
}
