"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const ROLES = [
  {
    id: "investor",
    title: "Investor",
    blurb: "Underwrite rentals — NOI, cap rate, cash-on-cash, comps.",
  },
  {
    id: "agent",
    title: "Agent",
    blurb: "Arm clients with cited due-diligence before showings and offers.",
  },
  {
    id: "homebuyer",
    title: "Homebuyer",
    blurb: "Payment model, risk flags, and questions to ask your agent.",
  },
] as const;

export default function WelcomePage() {
  const router = useRouter();
  const [role, setRole] = useState<(typeof ROLES)[number]["id"] | "">("");
  const [saving, setSaving] = useState(false);

  async function onContinue(e: React.FormEvent) {
    e.preventDefault();
    if (!role) return;
    setSaving(true);
    try {
      localStorage.setItem(
        "housefax_profile",
        JSON.stringify({ role, onboarded_at: new Date().toISOString() })
      );
      router.push("/dashboard");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <h1>Welcome — how will you use HouseFax?</h1>
        <p className="sub">
          This personalizes defaults and report framing. You can change it anytime in Settings.
        </p>
        <form onSubmit={onContinue}>
          <div className="role-grid">
            {ROLES.map((r) => (
              <button
                key={r.id}
                type="button"
                className={role === r.id ? "role-card selected" : "role-card"}
                onClick={() => setRole(r.id)}
              >
                <strong>{r.title}</strong>
                <span>{r.blurb}</span>
              </button>
            ))}
          </div>
          <button className="primary" type="submit" disabled={!role || saving}>
            {saving ? "Saving…" : "Continue to dashboard"}
          </button>
        </form>
      </section>
    </div>
  );
}
