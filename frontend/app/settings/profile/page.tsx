"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Profile = {
  role: "investor" | "agent" | "homebuyer";
  name: string;
  email_opt_in: boolean;
  default_down_pct: string;
  default_rate: string;
};

const empty: Profile = {
  role: "homebuyer",
  name: "",
  email_opt_in: true,
  default_down_pct: "20",
  default_rate: "",
};

export default function ProfileSettingsPage() {
  const [profile, setProfile] = useState<Profile>(empty);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("housefax_profile");
      if (raw) setProfile({ ...empty, ...JSON.parse(raw) });
    } catch {
      /* ignore */
    }
  }, []);

  function onSave(e: React.FormEvent) {
    e.preventDefault();
    localStorage.setItem("housefax_profile", JSON.stringify(profile));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <section className="page-card">
      <div className="page-header">
        <h1>Profile</h1>
        <Link href="/settings/billing" className="nav-link">
          Billing →
        </Link>
      </div>
      <p className="sub">
        Edit the role captured at onboarding, plus defaults used to pre-fill{" "}
        <Link href="/search">/search</Link>.
      </p>

      <form className="form-stack" onSubmit={onSave}>
        <div>
          <label htmlFor="name">Display name</label>
          <input
            id="name"
            value={profile.name}
            onChange={(e) => setProfile({ ...profile, name: e.target.value })}
            placeholder="Alex Rivera"
          />
        </div>
        <div>
          <label htmlFor="role">I am a…</label>
          <select
            id="role"
            value={profile.role}
            onChange={(e) =>
              setProfile({ ...profile, role: e.target.value as Profile["role"] })
            }
          >
            <option value="investor">Investor</option>
            <option value="agent">Agent</option>
            <option value="homebuyer">Homebuyer</option>
          </select>
        </div>
        <div className="form-grid">
          <div>
            <label htmlFor="down">Default down payment %</label>
            <input
              id="down"
              type="number"
              min="0"
              max="100"
              value={profile.default_down_pct}
              onChange={(e) => setProfile({ ...profile, default_down_pct: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="rate">Default rate assumption % (optional)</label>
            <input
              id="rate"
              type="number"
              step="0.01"
              placeholder="Uses FRED live rate if blank"
              value={profile.default_rate}
              onChange={(e) => setProfile({ ...profile, default_rate: e.target.value })}
            />
          </div>
        </div>
        <label className="check-row">
          <input
            type="checkbox"
            checked={profile.email_opt_in}
            onChange={(e) => setProfile({ ...profile, email_opt_in: e.target.checked })}
          />
          Email me when a report is ready and for product updates
        </label>
        <button className="primary" type="submit">
          Save profile
        </button>
        {saved && <p className="success-note">Saved.</p>}
      </form>
    </section>
  );
}
