import json
from src.engine.evaluator import evaluate_all

with open("policy/policy_v1.json") as f:
    rules = json.load(f)["rules"]

instruments = {
    "SE0000108656": {"asset_class": "equity", "listing_status": "LISTED"},
    "XS1234567890": {"asset_class": "bond", "rating": "BB"},
    "LU9999999999": {"asset_class": "fund", "domicile": "KY"},
    "XX0000000000": {},
}

holdings = [
    {"account_id": "ACC001", "isin": "SE0000108656", "market_value": 50000},
    {"account_id": "ACC001", "isin": "XS1234567890", "market_value": 30000},
    {"account_id": "ACC001", "isin": "LU9999999999", "market_value": 15000},
    {"account_id": "ACC001", "isin": "XX0000000000", "market_value": 5000},
]

account_totals = {"ACC001": 100000}

for f in evaluate_all(holdings, instruments, rules, account_totals):
    print(f["isin"], f["rule_id"], f["status"], f["actual"], f["reason"])
