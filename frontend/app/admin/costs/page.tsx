import { DEMO_COST_STATS } from "@/lib/demo-data";
import Link from "next/link";

export default function AdminCostsPage() {
  const c = DEMO_COST_STATS;
  return (
    <section className="page-card">
      <div className="page-header">
        <div>
          <h1>Admin · Costs</h1>
          <p className="sub">
            RentCast/ATTOM volume &amp; spend, Redis cache hit rate — main variable costs.
          </p>
        </div>
        <Link href="/admin/evals">← Evals</Link>
      </div>

      <div className="kv">
        <div className="item">
          <div className="k">RentCast calls (30d)</div>
          <div className="v">{c.rentcast_calls_30d}</div>
        </div>
        <div className="item">
          <div className="k">RentCast est. spend</div>
          <div className="v">${c.rentcast_est_spend_usd.toFixed(2)}</div>
        </div>
        <div className="item">
          <div className="k">ATTOM calls (30d)</div>
          <div className="v">{c.attom_calls_30d}</div>
        </div>
        <div className="item">
          <div className="k">ATTOM est. spend</div>
          <div className="v">${c.attom_est_spend_usd.toFixed(2)}</div>
        </div>
        <div className="item">
          <div className="k">Redis hit rate</div>
          <div className="v">{(c.redis_hit_rate * 100).toFixed(0)}%</div>
        </div>
        <div className="item">
          <div className="k">LLM calls (30d)</div>
          <div className="v">{c.llm_calls_30d}</div>
        </div>
      </div>
    </section>
  );
}
