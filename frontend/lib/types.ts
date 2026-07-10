// Mirrors backend/app/schemas/report.py — the FastAPI report contract.
// If the backend shape changes, these types (and the build) must change too.

export type Verdict = "Strong Candidate" | "Cautious Buy" | "Pass";

export interface Source {
  id: string;
  label: string;
  retrieved_at?: string | null;
}

export interface PropertyFacts {
  address: string;
  property_type?: string | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  square_footage?: number | null;
  lot_size?: number | null;
  year_built?: number | null;
  last_sale_date?: string | null;
  last_sale_price?: number | null;
  annual_taxes?: number | null;
  source_ids: string[];
}

export interface PaymentModel {
  purchase_price: number;
  down_payment: number;
  down_payment_pct: number;
  loan_amount: number;
  annual_rate: number;
  rate_source_id: string;
  term_years: number;
  monthly_principal_interest: number;
  monthly_taxes: number;
  monthly_insurance: number;
  all_in_monthly: number;
}

export interface InvestmentModel {
  monthly_rent_estimate: number;
  rent_range_low?: number | null;
  rent_range_high?: number | null;
  vacancy_rate: number;
  gross_annual_income: number;
  operating_expenses_annual: number;
  noi_annual: number;
  cap_rate: number;
  monthly_cash_flow: number;
  cash_invested: number;
  cash_on_cash_return: number;
  source_ids: string[];
}

export interface Comp {
  address: string;
  distance_miles?: number | null;
  sale_price?: number | null;
  sale_date?: string | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  square_footage?: number | null;
  price_per_sqft?: number | null;
}

export interface CompAnalysis {
  comps: Comp[];
  subject_price_per_sqft?: number | null;
  median_comp_price_per_sqft?: number | null;
  pricing_delta_pct?: number | null;
  narrative: string;
  source_ids: string[];
}

export interface RiskFlag {
  category: string;
  severity: "low" | "moderate" | "high" | "unknown";
  detail: string;
  source_ids: string[];
}

export interface NeighborhoodThesis {
  median_household_income?: number | null;
  population?: number | null;
  narrative: string;
  source_ids: string[];
}

export interface ExecutiveVerdict {
  verdict: Verdict;
  confidence: "low" | "medium" | "high";
  summary: string;
  best_fit_buyer: string;
  worst_fit_buyer: string;
}

export interface Report {
  report_id: string;
  generated_at: string;
  intent: "buyer" | "investor";
  disclaimer: string;
  executive_verdict: ExecutiveVerdict;
  property_facts: PropertyFacts;
  payment_model?: PaymentModel | null;
  investment_model?: InvestmentModel | null;
  comp_analysis: CompAnalysis;
  neighborhood: NeighborhoodThesis;
  risk_flags: RiskFlag[];
  questions_to_ask: string[];
  sources: Source[];
  eval_passed?: boolean | null;
  eval_failures: string[];
}

export interface AnalyzeRequest {
  address: string;
  purchase_price?: number;
  down_payment_pct?: number;
  intent: "buyer" | "investor";
}
