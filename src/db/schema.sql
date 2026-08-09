CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT PRIMARY KEY,
    holder_type  TEXT
);

CREATE TABLE IF NOT EXISTS instruments (
    isin            TEXT PRIMARY KEY,
    name            TEXT,
    asset_class     TEXT,
    issuer          TEXT,
    rating          TEXT,
    listing_status  TEXT,
    domicile        TEXT
);

CREATE TABLE IF NOT EXISTS holdings (
    date          TEXT NOT NULL,
    account_id    TEXT NOT NULL,
    isin          TEXT NOT NULL,
    quantity      REAL,
    market_value  REAL,
    PRIMARY KEY (date, account_id, isin)
);

CREATE TABLE IF NOT EXISTS corporate_events (
    date        TEXT NOT NULL,
    isin        TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    PRIMARY KEY (date, isin, event_type)
);

CREATE TABLE IF NOT EXISTS findings (
    run_date    TEXT NOT NULL,
    account_id  TEXT NOT NULL,
    isin        TEXT NOT NULL,
    rule_id     TEXT NOT NULL,
    status      TEXT NOT NULL,
    field       TEXT,
    threshold   TEXT,
    actual      TEXT,
    severity    TEXT,
    reason      TEXT,
    is_new      INTEGER DEFAULT 0,
    is_affected INTEGER DEFAULT 0,
    PRIMARY KEY (run_date, account_id, isin, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(run_date, status);
CREATE INDEX IF NOT EXISTS idx_holdings_isin ON holdings(isin);