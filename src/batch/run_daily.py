import json
import sys

from src.db.connection import init_db
from src.db import repository as repo
from src.ingestion.eod_loader import load_instruments, load_accounts, load_holdings
from src.ingestion.event_loader import load_events
from src.ingestion.new_holdings import find_new_isins
from src.engine.evaluator import evaluate_all


def load_policy(path="policy/policy_v1.json"):
    with open(path) as f:
        return json.load(f)["rules"]


def apply_events(events):
    """Write event outcomes into the instrument register."""
    field_for = {
        "RATING_DOWNGRADE": "rating",
        "RATING_UPGRADE": "rating",
        "DELISTING": "listing_status",
        "DOMICILE_CHANGE": "domicile",
    }

    instruments = repo.get_instruments()
    updated = []

    for event in events:
        isin = event["isin"]
        if isin not in instruments:
            print(f"  event on {isin} ignored, not in register")
            continue

        field = field_for.get(event["event_type"])
        if field is None:
            print(f"  unknown event type {event['event_type']}, skipped")
            continue

        instrument = instruments[isin]
        instrument[field] = event["new_value"]
        updated.append(instrument)
        print(f"  {isin}: {field} {event['old_value']} -> {event['new_value']}")

    if updated:
        repo.insert_instruments(updated)

    return {e["isin"] for e in events}

def run_daily(date):
    init_db()
    rules = load_policy()

    print(f"Running batch for {date}")

    existing = repo.count_findings(date)
    if existing:
        print(f"  run already exists with {existing} findings, replacing")

    repo.insert_instruments(load_instruments())
    repo.insert_accounts(load_accounts())

    seen_isins = repo.get_seen_isins(date)

    holdings = load_holdings(date)
    repo.insert_holdings(holdings)

    new_isins = find_new_isins(holdings, seen_isins)
    print(f"  {len(new_isins)} new instrument(s): {sorted(new_isins)}")

    events = load_events(date)
    repo.insert_events(events)
    print(f"  {len(events)} corporate event(s)")
    affected_isins = apply_events(events)

    instruments = repo.get_instruments()
    account_totals = repo.get_account_totals(date)
    findings = evaluate_all(holdings, instruments, rules, account_totals)

    for f in findings:
        f["is_new"] = 1 if f["isin"] in new_isins else 0
        f["is_affected"] = 1 if f["isin"] in affected_isins else 0
        f["threshold"] = str(f["threshold"])
        f["actual"] = str(f["actual"]) if f["actual"] is not None else None

    repo.insert_findings(date, findings)

    breaches = [f for f in findings if f["status"] == "BREACH"]
    unknowns = [f for f in findings if f["status"] == "UNKNOWN"]
    print(f"  {len(findings)} findings: {len(breaches)} breaches, {len(unknowns)} unknown")

    for f in breaches + unknowns:
        print(f"    {f['account_id']} {f['isin']} {f['rule_id']} {f['status']} actual={f['actual']}")


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-08-07"
    run_daily(date)