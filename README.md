# HouseFax

**An AI-generated due-diligence report for any residential property. Carfax for houses.**

HouseFax is an AI property-analysis platform for residential buyers and investors. It combines
structured property data, geospatial search, deterministic underwriting calculators, RAG over
supporting documents, and LLM-based report generation to produce cited, auditable property
intelligence reports.

It is a **decision-support tool** — not financial, legal, or real-estate advice, and not a
listing marketplace.

## Core principle

> **LLM explains. Tools calculate. Database grounds. Evals police.**

- The LLM never computes a mortgage payment or cap rate itself — it calls
  `calculate_monthly_payment()`, `calculate_cap_rate()`, etc. and narrates the results.
- Every narrative claim must cite a source id (`[rentcast:avm-value]`, `[census:acs5]`, …).
- Before a report ships, an **eval harness** machine-checks it: math correctness, citation
  presence, comp quality, fair-housing language, overconfidence, and tool discipline.

## Architecture

```
┌────────────────────────┐     ┌──────────────────────────────┐
│  Next.js + TypeScript  │────▶│  FastAPI                     │
│  address search        │     │  /analyze  /qa  /evals/run   │
│  report viewer, Q&A    │     │  tool-calling orchestration  │
└────────────────────────┘     └──────┬───────────┬───────────┘
                                      │           │
                              ┌───────▼──┐   ┌────▼─────────────────────┐
                              │  Redis   │   │ Postgres                 │
                              │ provider │   │  + PostGIS (geospatial)  │
                              │ + report │   │  + pgvector (RAG index)  │
                              │  cache   │   └──────────────────────────┘
                              └──────────┘
       Data: RentCast (facts/AVM/comps) · Census ACS (tract income/population)
             FRED (mortgage rate) · FEMA NFHL (flood zones)
       AI:   hosted LLM (Anthropic or OpenAI) + deterministic calculator tools
```

## Report pipeline

1. **Address input** — address, optional purchase price / down payment / buyer-vs-investor intent.
2. **Data fetch** — RentCast property facts, AVM value + comps, rent estimate; Census tract
   profile; FRED mortgage rate; FEMA flood zone. All responses cached in Redis (they're metered).
3. **Deterministic models** — payment model, NOI, cap rate, cash flow, cash-on-cash, comp
   selection and $/sqft analysis — computed in code, never by the model.
4. **AI orchestration** — the LLM receives grounding data + calculator tools, calls tools for any
   additional figures, and submits narrative sections with inline citations.
5. **Eval harness** — the report is machine-checked before it's returned; failures are attached
   to the report (`eval_passed`, `eval_failures`).
6. **Output** — structured JSON rendered in the UI, exportable to PDF, with a follow-up Q&A panel
   grounded in the report.

## Eval harness

| Check | Catches |
|---|---|
| `math_correctness` | wrong mortgage / cap-rate / cash-flow figures (recomputed from inputs) |
| `source_usage` | narrative sections that cite nothing, or cite non-existent sources |
| `tool_discipline` | numbers with no provenance in grounding data or tool results |
| `comp_quality` | comps too far, wrong size band, or stale |
| `fair_housing` | steering or demographic-coded phrasing |
| `overconfidence` | guaranteed appreciation/returns; "high" confidence on a wide AVM range |

The same suite runs as a regression gate in CI (`evals/cases.py`) — a merge that would let a
bad report ship fails the build.

## Quickstart

```bash
cp .env.example .env      # add RENTCAST_API_KEY and an LLM key
docker compose up --build
# web: http://localhost:3000   api docs: http://localhost:8000/docs
```

### Bare-metal dev

```bash
# backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload          # http://localhost:8000

# frontend
cd frontend
npm install && npm run dev                        # http://localhost:3000

# tests + eval suite
cd backend && .venv/bin/python -m pytest
```

Redis and Postgres are optional in dev: the cache falls back to memory and report persistence
no-ops without `DATABASE_URL`.

## Repo layout

```
backend/
  app/
    clients/       RentCast, Census, FRED, FEMA (all cached)
    tools/         deterministic calculators, comp selection, risk flags, tool registry
    ai/            provider-agnostic LLM client, prompts, orchestration loop
    routers/       /analyze, /reports/{id}, /qa, /evals/run
    db/            init.sql (PostGIS + pgvector schema), persistence layer
  evals/           checks, fixture cases, runner (pre-ship gate + CI regression suite)
  tests/           unit tests
frontend/          Next.js + TypeScript app (search, report viewer, PDF export, Q&A)
infra/postgres/    Postgres 16 + PostGIS + pgvector image
legacy/            the previous PropScout prototype (kept for reference)
```

## Roadmap

- **Now**: everything above.
- **Next**: document intelligence module (LlamaIndex multi-document RAG over inspection
  reports / disclosures / HOA docs with page citations), 30–50-case eval dataset, S3 PDF storage,
  AWS deployment (RDS + ECS).
- **Later, only if usage justifies it**: Terraform, Kubernetes, service split, Kafka, fine-tuning,
  standalone vector DB.
