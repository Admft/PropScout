# 🚀 PropScout Pro — Full Stack Architecture 

## 🧠 Product Overview
PropScout Pro is a **serverless, AI-enhanced real estate underwriting platform** that transforms Zillow listings into **instant investment-grade deal analysis**.

It combines:
- **Deterministic financial modeling (source of truth)**
- **Multi-source data ingestion**
- **LLM-powered narrative enhancement**
- **Cloud-native, event-driven architecture**

---

# 🏗️ Core Architecture

## 🌐 Frontend Layer
- **Static Web UI** (HTML + Tailwind CSS via CDN)
- **Chrome Extension (Planned Primary Interface)**
- Runs in **browser runtime (client-side)**
- Lightweight, no framework dependency (zero build step)

### Responsibilities
- Capture Zillow URL
- Trigger backend API request
- Render:
  - Deal verdict (PASS / REJECT / MANUAL_REVIEW)
  - Financial metrics (NOI, Cap Rate, DSCR)
  - Risk signals + valuation insights
  - Source observability diagnostics

---

## ⚙️ Backend Layer (Serverless Compute)

### Platform
- **Microsoft Azure**
- **Azure Functions (Python HTTP Trigger)**
- **Stateless, event-driven compute**

### Endpoint
```
POST /api/AnalyzeProperty
```

### Core Characteristics
- Serverless execution model
- Horizontal auto-scaling
- Consumption-based billing
- Low operational overhead

### Responsibilities
- Request validation + security enforcement
- External API orchestration
- Financial + valuation computation
- Deterministic underwriting decision engine
- Optional LLM enrichment
- Structured JSON response generation

---

## 🔗 Data Integration Layer (External APIs)

### 🏠 RentCast API
- Automated Valuation Model (AVM)
- Rental estimates
- Comparable sales data

### 🕸️ Apify (Zillow Scraper Actor)
- Property metadata extraction
- Listing descriptions
- Rent clues / historical signals

### 🤖 OpenAI API (GPT-4o)
- Natural language synthesis
- Executive summaries
- Risk interpretation

> ⚠️ Guardrail: LLM is **non-authoritative** — cannot override deterministic underwriting.

---

## 🧮 Core Intelligence Layer

### 📊 Valuation Engine
- Multi-signal weighted model:
  - Listing price
  - Zestimate
  - RentCast AVM
  - Comparable sales
  - Price-per-square-foot
  - Income approach (optional)
- Outlier detection + down-weighting
- Confidence scoring + valuation range output

---

### 💰 Financial Modeling Engine
- NOI (Net Operating Income)
- Cap Rate
- DSCR (Debt Service Coverage Ratio)
- Cash Flow
- Debt Service
- Break-even occupancy

> Missing inputs → `null` (never synthetic defaults)

---

### ⚖️ Deterministic Underwriting Engine (Core Decision Layer)

Outputs:
- `PASS`
- `REJECT`
- `MANUAL_REVIEW`

Features:
- Rule-based decision system
- Data-quality-aware branching
- No AI hallucination risk
- Fully explainable logic

---

### 🧠 Rent Selection Engine (Priority-Based Resolution)
1. RentCast estimate (primary)
2. Zillow Rent Zestimate
3. Scraped rent signals (Apify)
4. Fallback → **MANUAL_REVIEW**

---

### ✨ AI Enhancement Layer (Optional)
- GPT-generated summaries
- Risk narrative generation
- Explanation augmentation

> Strict constraint: **Cannot override deterministic decision**

---

## 💾 Persistence Layer

### Database
- **Azure Cosmos DB (NoSQL, Serverless Mode)**

### Characteristics
- Globally distributed
- Low-latency reads/writes
- JSON-native storage
- Partitioned container architecture

### Usage
- Store full analysis reports
- Enable auditability + retrieval
- Optional in **fast mode** for latency optimization

---

## 📡 Observability & Monitoring

### Platform
- **Azure Application Insights**

### Telemetry
- Request latency
- Failure rates
- Dependency tracking (RentCast, Apify, OpenAI)
- Custom business metrics:
  - Deal outcomes (PASS / REJECT / MANUAL_REVIEW)
  - Rent source selection
  - Data quality flags

---

## 🔐 Security Layer
- API key enforcement (`X-API-Key`)
- Environment-based secret management
- Planned:
  - Rate limiting
  - Usage quotas
  - Abuse detection

---

# 🔁 End-to-End Data Flow

```
[ Browser / Chrome Extension ]
              ↓
   Azure Function (HTTP Trigger)
              ↓
   ┌───────────────┬───────────────┬───────────────┐
   │ RentCast API  │ Apify Scraper │ OpenAI GPT    │
   └───────────────┴───────────────┴───────────────┘
              ↓
   Deterministic Financial Engine
              ↓
   Underwriting Decision Engine
              ↓
   Optional GPT Enhancement
              ↓
   JSON Response Payload
              ↓
   Cosmos DB (optional persistence)
```

---

# ⚡ Execution Modes

## 🚀 Fast Mode
- Deterministic analysis only
- No GPT
- Optional no persistence
- Low latency (~sub-second to few seconds)

## 🧠 Full Mode
- Includes GPT narrative
- Full report persistence
- Rich explanation layer

---

# 📦 API Response Schema (Simplified)

```json
{
  "computed_financials": {},
  "valuation_model": {},
  "algorithmic_underwrite": {},
  "ai_underwriter": {},
  "source_status": {}
}
```

### Semantics
- `null` → unavailable / not computable
- `0` → valid computed value

---

# 🧩 Key Architectural Patterns

- **Serverless Architecture**
- **Stateless Compute**
- **Event-Driven Execution**
- **Micro-Integration Pattern (API orchestration)**
- **Deterministic + AI Hybrid Model**
- **Graceful Degradation Design**
- **Observability-First System Design**

---

# 🧭 Deployment Stack

- Azure Function App (Python runtime)
- Azure Cosmos DB (Serverless NoSQL)
- Azure Application Insights (monitoring)
- Environment-based configuration (App Settings)

---

# 🧾 One-Line Definition

> PropScout Pro is a **serverless, cloud-native underwriting engine and Chrome extension** that converts Zillow listings into **instant, explainable real estate investment decisions** using **deterministic financial modeling and constrained AI augmentation**.