from src.db.connection import get_connection


def insert_instruments(rows):
    conn = get_connection()
    conn.executemany(
        """INSERT OR REPLACE INTO instruments
           (isin, name, asset_class, issuer, rating, listing_status, domicile)
           VALUES (:isin, :name, :asset_class, :issuer, :rating, :listing_status, :domicile)""",
        rows,
    )
    conn.commit()


def insert_accounts(rows):
    conn = get_connection()
    conn.executemany(
        "INSERT OR REPLACE INTO accounts (account_id, holder_type) VALUES (:account_id, :holder_type)",
        rows,
    )
    conn.commit()


def insert_holdings(rows):
    conn = get_connection()
    conn.executemany(
        """INSERT OR REPLACE INTO holdings
           (date, account_id, isin, quantity, market_value)
           VALUES (:date, :account_id, :isin, :quantity, :market_value)""",
        rows,
    )
    conn.commit()


def insert_events(rows):
    conn = get_connection()
    conn.executemany(
        """INSERT OR REPLACE INTO corporate_events
           (date, isin, event_type, old_value, new_value)
           VALUES (:date, :isin, :event_type, :old_value, :new_value)""",
        rows,
    )
    conn.commit()


def get_instruments():
    """All instruments as a dict keyed by ISIN."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM instruments").fetchall()
    return {r["isin"]: dict(r) for r in rows}


def get_holdings(date):
    """All holdings for a given date."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM holdings WHERE date = ?", (date,)).fetchall()
    return [dict(r) for r in rows]


def get_events(date):
    """All corporate events for a given date."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM corporate_events WHERE date = ?", (date,)).fetchall()
    return [dict(r) for r in rows]


def get_seen_isins(before_date):
    """Every ISIN held on any account before this date."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT isin FROM holdings WHERE date < ?", (before_date,)
    ).fetchall()
    return {r["isin"] for r in rows}


def get_account_totals(date):
    """Total market value per account for a given date."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT account_id, SUM(market_value) AS total FROM holdings WHERE date = ? GROUP BY account_id",
        (date,),
    ).fetchall()
    return {r["account_id"]: r["total"] for r in rows}

def insert_findings(run_date, findings):
    conn = get_connection()
    rows = [dict(f, run_date=run_date) for f in findings]
    conn.executemany(
        """INSERT OR REPLACE INTO findings
           (run_date, account_id, isin, rule_id, status, field, threshold, actual,
            severity, reason, is_new, is_affected)
           VALUES (:run_date, :account_id, :isin, :rule_id, :status, :field, :threshold,
                   :actual, :severity, :reason, :is_new, :is_affected)""",
        rows,
    )
    conn.commit()


def count_findings(run_date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM findings WHERE run_date = ?", (run_date,)
    ).fetchone()
    return row["n"]