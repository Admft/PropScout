import { DEMO_EVAL_STATS } from "@/lib/demo-data";
import Link from "next/link";

export default function AdminEvalsPage() {
  return (
    <section className="page-card">
      <div className="page-header">
        <div>
          <h1>Admin · Eval harness</h1>
          <p className="sub">Internal-only. Pass/fail rates by category + flagged reports.</p>
        </div>
        <Link href="/admin/costs">Costs →</Link>
      </div>

      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th className="num">Pass rate</th>
            <th className="num">Flagged</th>
          </tr>
        </thead>
        <tbody>
          {DEMO_EVAL_STATS.map((row) => (
            <tr key={row.category}>
              <td>
                <code>{row.category}</code>
              </td>
              <td className="num">{(row.pass_rate * 100).toFixed(0)}%</td>
              <td className="num">{row.flagged}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="mt">Flagged for manual review</h2>
      <ul className="questions">
        <li>
          <code>rpt-wylie-woodbridge</code> — tool_discipline warning on narrative figure
        </li>
        <li>
          <code>sample-123-main…</code> — estimate_confidence: wide AVM range, confidence=medium OK
        </li>
      </ul>
    </section>
  );
}
