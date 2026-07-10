-- HouseFax schema: one Postgres for relational data, geospatial queries
-- (PostGIS), and the RAG index (pgvector). Applied automatically by the
-- postgres container's docker-entrypoint-initdb.d on first boot.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS properties (
    id            BIGSERIAL PRIMARY KEY,
    address       TEXT UNIQUE NOT NULL,
    location      GEOGRAPHY(POINT, 4326),
    property_type TEXT,
    bedrooms      NUMERIC,
    bathrooms     NUMERIC,
    square_footage INTEGER,
    lot_size      INTEGER,
    year_built    INTEGER,
    last_sale_date DATE,
    last_sale_price NUMERIC,
    annual_taxes  NUMERIC,
    raw           JSONB,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS properties_location_idx ON properties USING GIST (location);

CREATE TABLE IF NOT EXISTS comps (
    id            BIGSERIAL PRIMARY KEY,
    property_id   BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    address       TEXT NOT NULL,
    location      GEOGRAPHY(POINT, 4326),
    sale_price    NUMERIC,
    sale_date     DATE,
    bedrooms      NUMERIC,
    bathrooms     NUMERIC,
    square_footage INTEGER,
    raw           JSONB
);

CREATE INDEX IF NOT EXISTS comps_location_idx ON comps USING GIST (location);

CREATE TABLE IF NOT EXISTS reports (
    id            TEXT PRIMARY KEY,
    address       TEXT NOT NULL,
    intent        TEXT,
    report        JSONB NOT NULL,
    eval_passed   BOOLEAN,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RAG index: market narratives, uploaded document chunks, comp descriptions.
-- 1536 dims matches text-embedding-3-small; swap if you change embedders.
CREATE TABLE IF NOT EXISTS doc_chunks (
    id            BIGSERIAL PRIMARY KEY,
    property_id   BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    doc_type      TEXT NOT NULL,  -- market_report | inspection | disclosure | hoa | comp_note
    source_label  TEXT,
    page          INTEGER,
    content       TEXT NOT NULL,
    embedding     VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx
    ON doc_chunks USING hnsw (embedding vector_cosine_ops);

-- Auth / billing (NextAuth + Stripe). Wired by the app as those stacks go live.
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,           -- NextAuth user / provider subject
    email           TEXT UNIQUE NOT NULL,
    name            TEXT,
    role            TEXT CHECK (role IN ('investor', 'agent', 'homebuyer')),
    email_opt_in    BOOLEAN NOT NULL DEFAULT true,
    default_down_payment_pct NUMERIC DEFAULT 0.20,
    default_rate_assumption  NUMERIC,
    stripe_customer_id TEXT UNIQUE,
    credits         INTEGER NOT NULL DEFAULT 0,
    subscription_status TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS reports_user_id_idx ON reports (user_id);

CREATE TABLE IF NOT EXISTS property_documents (
    id            BIGSERIAL PRIMARY KEY,
    report_id     TEXT REFERENCES reports(id) ON DELETE CASCADE,
    property_id   BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    user_id       TEXT REFERENCES users(id) ON DELETE CASCADE,
    file_name     TEXT NOT NULL,
    doc_type      TEXT NOT NULL,  -- inspection | disclosure | hoa | other
    status        TEXT NOT NULL DEFAULT 'queued',  -- queued | processing | ready | failed
    storage_url   TEXT,
    findings      JSONB DEFAULT '[]'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credit_ledger (
    id            BIGSERIAL PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta         INTEGER NOT NULL,
    reason        TEXT NOT NULL,  -- purchase | report_spend | refund | grant
    stripe_event_id TEXT UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
