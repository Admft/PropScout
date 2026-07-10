/** Demo data for dashboard / admin until Postgres user scoping is wired. */

export const DEMO_REPORTS = [
  {
    id: "sample-123-main-st-austin-tx-78704",
    address: "123 Main St, Austin, TX 78704",
    created_at: "2026-07-01T12:00:00Z",
    status: "Ready" as const,
    verdict: "Cautious Buy",
  },
  {
    id: "rpt-wylie-woodbridge",
    address: "1200 Woodbridge Pkwy, Wylie, TX 75098",
    created_at: "2026-06-28T16:40:00Z",
    status: "Ready" as const,
    verdict: "Strong Candidate",
  },
  {
    id: "rpt-failed-demo",
    address: "999 Nowhere Rd, Fake City, TX 00000",
    created_at: "2026-06-20T09:12:00Z",
    status: "Failed" as const,
    verdict: null,
  },
];

export const DEMO_EVAL_STATS = [
  { category: "math_correctness", pass_rate: 0.98, flagged: 1 },
  { category: "unsupported_claims", pass_rate: 0.94, flagged: 3 },
  { category: "comp_quality", pass_rate: 0.91, flagged: 4 },
  { category: "fair_housing", pass_rate: 1.0, flagged: 0 },
  { category: "overconfidence", pass_rate: 0.96, flagged: 2 },
  { category: "source_usage", pass_rate: 0.93, flagged: 3 },
  { category: "tool_discipline", pass_rate: 0.97, flagged: 1 },
  { category: "estimate_confidence", pass_rate: 0.89, flagged: 5 },
];

export const DEMO_COST_STATS = {
  rentcast_calls_30d: 412,
  rentcast_est_spend_usd: 82.4,
  attom_calls_30d: 0,
  attom_est_spend_usd: 0,
  redis_hit_rate: 0.71,
  llm_calls_30d: 188,
};
