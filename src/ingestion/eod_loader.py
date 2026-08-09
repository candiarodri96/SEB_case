import csv
from pathlib import Path


def read_csv(path):
    """Read a CSV into a list of dicts. Empty strings become None."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({k: (v if v != "" else None) for k, v in row.items()})
        return rows


def load_instruments(path="data/instruments.csv"):
    return read_csv(path)


def load_accounts(path="data/accounts.csv"):
    return read_csv(path)


def load_holdings(date, directory="data/eod"):
    path = Path(directory) / f"holdings_{date}.csv"
    rows = read_csv(path)
    for row in rows:
        row["quantity"] = float(row["quantity"]) if row["quantity"] else None
        row["market_value"] = float(row["market_value"]) if row["market_value"] else None
    return rows