import type { Report, Verdict } from "@/lib/types";

const usd = (n: number | null | undefined, digits = 0) =>
  n == null
    ? "—"
    : n.toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: digits,
      });

const pct = (n: number | null | undefined) => (n == null ? "—" : `${(n * 100).toFixed(2)}%`);

const badgeClass: Record<Verdict, string> = {
  "Strong Candidate": "strong",
  "Cautious Buy": "cautious",
  Pass: "pass",
};

/** Render "[source:id]" citations as chips. */
function Narrative({ text }: { text: string }) {
  const parts = text.split(/(\[[a-z0-9:_\-]+\])/g);
  return (
    <p className="narrative">
      {parts.map((part, i) =>
        /^\[[a-z0-9:_\-]+\]$/.test(part) ? (
          <span key={i} className="cite">
            {part.slice(1, -1)}
          </span>
        ) : (
          part
        )
      )}
    </p>
  );
}

export default function ReportView({ report }: { report: Report }) {
  const v = report.executive_verdict;
  const pm = report.payment_model;
  const im = report.investment_model;
  const ca = report.comp_analysis;

  return (
    <div className="report">
      <div className="report-actions no-print">
        <button className="secondary" onClick={() => window.print()}>
          Export PDF
        </button>
      </div>

      <section className="card">
        <div className="verdict-row">
          <span className={`badge ${badgeClass[v.verdict]}`}>{v.verdict}</span>
          <span className="badge muted">confidence: {v.confidence}</span>
          {report.eval_passed === false && (
            <span className="badge pass">quality checks flagged this report</span>
          )}
        </div>
        <Narrative text={v.summary} />
        <div className="fit-grid">
          <div className="fit">
            <strong>Best fit:</strong> {v.best_fit_buyer}
          </div>
          <div className="fit">
            <strong>Worst fit:</strong> {v.worst_fit_buyer}
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Property facts — {report.property_facts.address}</h2>
        <div className="kv">
          <Item k="Type" v={report.property_facts.property_type ?? "—"} />
          <Item
            k="Beds / Baths"
            v={`${report.property_facts.bedrooms ?? "—"} / ${report.property_facts.bathrooms ?? "—"}`}
          />
          <Item
            k="Square feet"
            v={report.property_facts.square_footage?.toLocaleString() ?? "—"}
          />
          <Item k="Year built" v={report.property_facts.year_built ?? "—"} />
          <Item
            k="Last sale"
            v={
              report.property_facts.last_sale_price
                ? `${usd(report.property_facts.last_sale_price)} (${report.property_facts.last_sale_date ?? "—"})`
                : "—"
            }
          />
          <Item k="Annual taxes" v={usd(report.property_facts.annual_taxes)} />
        </div>
      </section>

      {pm && (
        <section className="card">
          <h2>Payment model</h2>
          <div className="kv">
            <Item k="Purchase price" v={usd(pm.purchase_price)} />
            <Item k={`Down (${(pm.down_payment_pct * 100).toFixed(0)}%)`} v={usd(pm.down_payment)} />
            <Item k={`Rate (${pm.term_years}yr fixed)`} v={pct(pm.annual_rate)} />
            <Item k="P&I / month" v={usd(pm.monthly_principal_interest, 2)} />
            <Item k="Taxes + insurance / mo" v={usd(pm.monthly_taxes + pm.monthly_insurance, 2)} />
            <Item k="All-in monthly" v={usd(pm.all_in_monthly, 2)} highlight />
          </div>
        </section>
      )}

      {im && (
        <section className="card">
          <h2>Investment model</h2>
          <div className="kv">
            <Item k="Rent estimate / mo" v={usd(im.monthly_rent_estimate)} />
            <Item k="NOI / year" v={usd(im.noi_annual)} />
            <Item k="Cap rate" v={pct(im.cap_rate)} />
            <Item k="Cash flow / mo" v={usd(im.monthly_cash_flow, 2)} highlight />
            <Item k="Cash invested" v={usd(im.cash_invested)} />
            <Item k="Cash-on-cash" v={pct(im.cash_on_cash_return)} />
          </div>
        </section>
      )}

      <section className="card">
        <h2>Comparable sales</h2>
        {ca.narrative && <Narrative text={ca.narrative} />}
        <table>
          <thead>
            <tr>
              <th>Address</th>
              <th className="num">Distance</th>
              <th className="num">Sold</th>
              <th className="num">Price</th>
              <th className="num">Sqft</th>
              <th className="num">$/sqft</th>
            </tr>
          </thead>
          <tbody>
            {ca.comps.map((c, i) => (
              <tr key={i}>
                <td>{c.address}</td>
                <td className="num">{c.distance_miles != null ? `${c.distance_miles} mi` : "—"}</td>
                <td className="num">{c.sale_date ?? "—"}</td>
                <td className="num">{usd(c.sale_price)}</td>
                <td className="num">{c.square_footage?.toLocaleString() ?? "—"}</td>
                <td className="num">{c.price_per_sqft != null ? usd(c.price_per_sqft, 2) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {ca.pricing_delta_pct != null && (
          <p className="narrative" style={{ marginTop: 10 }}>
            Subject at {usd(ca.subject_price_per_sqft, 2)}/sqft vs comp median{" "}
            {usd(ca.median_comp_price_per_sqft, 2)}/sqft ({ca.pricing_delta_pct > 0 ? "+" : ""}
            {ca.pricing_delta_pct}%).
          </p>
        )}
      </section>

      <section className="card">
        <h2>Neighborhood</h2>
        <div className="kv" style={{ marginBottom: 12 }}>
          <Item k="Median household income" v={usd(report.neighborhood.median_household_income)} />
          <Item k="Tract population" v={report.neighborhood.population?.toLocaleString() ?? "—"} />
        </div>
        <Narrative text={report.neighborhood.narrative} />
      </section>

      <section className="card">
        <h2>Risk flags</h2>
        {report.risk_flags.map((r, i) => (
          <div className="risk" key={i}>
            <span className={`sev ${r.severity}`}>{r.severity}</span>
            <span>
              <strong style={{ textTransform: "capitalize" }}>{r.category}:</strong> {r.detail}
            </span>
          </div>
        ))}
      </section>

      <section className="card">
        <h2>Questions to ask your agent</h2>
        <ul className="questions">
          {report.questions_to_ask.map((q, i) => (
            <li key={i}>{q}</li>
          ))}
        </ul>
      </section>

      <section className="card sources">
        <h2>Sources</h2>
        {report.sources.map((s) => (
          <div key={s.id}>
            <span className="cite">{s.id}</span> {s.label}
          </div>
        ))}
        <p style={{ marginBottom: 0 }}>{report.disclaimer}</p>
      </section>
    </div>
  );
}

function Item({
  k,
  v,
  highlight,
}: {
  k: string;
  v: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="item" style={highlight ? { outline: "2px solid var(--accent)" } : undefined}>
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  );
}
