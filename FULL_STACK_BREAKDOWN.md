# PropScout Pro: Full-Stack Breakdown

## What This Product Is
PropScout Pro is a real-estate deal intelligence stack built for fast property analysis from a Zillow URL. It combines deterministic underwriting math with AI narrative enhancement, while staying robust when outside services fail.

## Full Stack at a Glance

### Frontend
- **Static Web UI**: `index.html`
- **Styling**: Tailwind CSS via CDN
- **Runtime**: Browser (works for Chrome extension style workflows)
- **Responsibility**:
  - Capture Zillow URL + optional address
  - Call backend endpoint
  - Render financial metrics, risk flags, and verdict

### Backend API
- **Platform**: Azure Functions (Python HTTP trigger)
- **Endpoint**: `POST /api/AnalyzeProperty`
- **Core file**: `function_app.py`
- **Responsibility**:
  - Validate request + Zillow URL
  - Gather valuation/comps/listing data
  - Compute valuation + financial metrics
  - Run deterministic underwriting
  - Optionally enhance narrative with GPT
  - Return final JSON report

### Data + AI Integrations
- **RentCast API**
  - AVM valuation (`/v1/avm/value`)
  - Sales comps (`/v1/sales/comps`)
- **Apify Zillow scraper actor**
  - Pulls property details + description + rent clues
- **OpenAI API**
  - Enhances executive summary and risk wording
  - Guardrailed by deterministic outcome

### Persistence
- **Azure Cosmos DB**
- Stores full report payload for retrieval/audit
- Fast mode can skip persistence for low latency

## Core Analysis Pipeline
1. **Input + Security**
   - Optional `X-API-Key` enforcement
   - Strict Zillow `https` URL validation
2. **Data Collection**
   - RentCast valuation
   - RentCast comps
   - Zillow scrape (Apify)
3. **Rent Selection (priority order)**
   1. RentCast midpoint
   2. Zillow rent Zestimate
   3. Zillow history fallback extraction
   4. None (manual-review path)
4. **Valuation Modeling**
   - Multi-signal weighted blend (list, zestimate, AVM, comps, ppsf, optional income approach)
   - Outlier down-weighting
   - Confidence scoring + valuation range
5. **Financial Engine**
   - NOI, cap rate, DSCR, debt service, cash flow, breakeven occupancy
   - Missing inputs return `None` (not fake zeros)
6. **Deterministic Underwriting (source of truth)**
   - Outputs `PASS`, `REJECT`, or `MANUAL_REVIEW`
   - Missing-rent cases route to `MANUAL_REVIEW`, not fake distress
7. **GPT Enhancement (optional)**
   - Improves narrative only
   - Cannot override deterministic `REJECT` or `MANUAL_REVIEW`
8. **Report + Optional Save**
   - Returns JSON with metrics, valuation model, underwriting, and source health

## What’s Special / Technically Strong

### 1) Deterministic-First + AI-Enhanced
Most stacks let LLMs decide the deal. This one does the opposite:
- Math/rules produce the canonical verdict
- GPT improves communication, not truth
- Hard guardrails prevent AI drift

### 2) Data-Quality-Aware Underwriting
Missing rent is treated as **unknown**, not **zero performance**:
- Prevents false `0 NOI / 0 DSCR` cascades
- Triggers `MANUAL_REVIEW` with explicit warning

### 3) Transparent Source Observability
`source_status` explains:
- What succeeded, failed, or was skipped
- Which rent source won
- Whether GPT and persistence ran
This is huge for extension UX and debugging trust.

### 4) Extension-Friendly Fast Mode
`mode=fast` supports low-latency use:
- Skip GPT
- Optionally skip Cosmos write
- Return deterministic underwriting quickly

### 5) Resilient External Calls
- Shared `requests.Session`
- Retry/backoff on transient network/status failures
- Graceful degradation keeps endpoint usable

## JSON Contract Highlights
The report intentionally includes:
- `computed_financials`
- `valuation_model`
- `algorithmic_underwrite`
- `ai_underwriter`
- `source_status`

Semantics:
- `null` => unavailable / not computable
- `0` => real computed zero

## Key Config Knobs (Env + constants)
- API keys: OpenAI / RentCast / Apify / Cosmos
- Optional auth key: `PROPSCOUT_API_KEY`
- Financial assumptions (vacancy, tax, insurance, maintenance, etc.)
- Comp radius/limit
- Fast mode behavior flags

## Why This Is Good for Product Growth
- Easy to demo now (single HTTP function)
- Explainable output for users and investors
- Structured source status for better support/debugging
- Deterministic core makes later model upgrades safer
- Clean foundation for eventual async scaling when volume grows

## Future Evolution (when ready)
- Move long-running scrape/LLM work to async jobs
- Add richer telemetry dashboards + latency/error SLOs
- Introduce report schema versioning + integration test suite
