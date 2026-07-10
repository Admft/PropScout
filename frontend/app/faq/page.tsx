"use client";

import { useState } from "react";

const FAQS = [
  {
    q: "Where does the data come from?",
    a: "Property facts, AVMs, and comps come from RentCast (and optionally ATTOM). Neighborhood context uses Census ACS. Mortgage rates come from FRED. Flood zones come from FEMA NFHL. Every claim in a report cites its source id.",
  },
  {
    q: "Is this an appraisal?",
    a: "No. HouseFax is a decision-support tool. AVM estimates are models, not appraisals, and are not a substitute for a licensed appraiser, inspector, attorney, or financial advisor.",
  },
  {
    q: "Does the AI invent numbers?",
    a: "No. Mortgage payments, NOI, cap rate, and cash flow are computed by deterministic tools. The LLM narrates and cites — it does not invent figures. An eval harness checks math, citations, comps, fair-housing language, and overconfidence before a report ships.",
  },
  {
    q: "What if I don't like a report?",
    a: "Contact support within 7 days of purchase. Refunds are reviewed case-by-case for failed generations or clear product defects — not for disagreeing with a Cautious Buy / Pass verdict.",
  },
  {
    q: "Do you store my card number?",
    a: "No. Payments are handled by Stripe Checkout and the Stripe Customer Portal. HouseFax never stores card data.",
  },
];

export default function FaqPage() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className="page-card">
      <h1>FAQ</h1>
      <p className="sub">Objection handling — data sourcing, AI vs appraiser, refunds.</p>
      <div className="accordion">
        {FAQS.map((item, i) => (
          <div key={item.q} className="acc-item">
            <button
              type="button"
              className="acc-q"
              aria-expanded={open === i}
              onClick={() => setOpen(open === i ? null : i)}
            >
              {item.q}
            </button>
            {open === i && <p className="acc-a">{item.a}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
