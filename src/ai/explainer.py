import json
import os
import urllib.request

API_URL = "https://api.anthropics.com/v1/messages"
MODEL  = "claude-sonnet-4-6"



def group_findings(findings):
    groups = {}
    for f in findings:
        if f["status"] == "COMPLIANT":
            continue
        key = (f["isin"], f["rule_id"])
        if key not in groups:
            groups[key] = {
                "isin": f["isin"],
                "rule_id": f["rule_id"],
                "status": f["status"],
                "field": f["field"],
                "threshold": f["threshold"],
                "actual": f["actual"],
                "reason": f["reason"],
                "severity": f["severity"],
                "accounts": [],
            }
        groups[key]["accounts"].append(f["account_id"])
    return list(groups.values())



def explain(group, instrument_name=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback(group, instrument_name)


    prompt = (
    "You are writing one sentence for a compliance officer's morning list. "
    "State what is wrong and what it affects. Do not invent facts. "
    "Do not recommend divesting; only describe the finding.\n\n"
    f"Instrument: {instrument_name or group['isin']}\n"
    f"Rule: {group['rule_id']}\n"
    f"Status: {group['status']}\n"
    f"Field: {group['field']}\n"
    f"Policy limit: {group['threshold']}\n"
    f"Actual value: {group['actual']}\n"
    f"Reason: {group['reason']}\n"
    f"Accounts affected: {len(group['accounts'])}\n\n"
    "Reply with the sentence only."
    )

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        return data["content"][0]["text"].strip()
    except Exception:
        return fallback(group, instrument_name)


def fallback(group, instrument_name=None):
    """Deterministic template used when the API is unavailable."""
    name = instrument_name or group["isin"]
    n = len(group["accounts"])
    accounts = f"{n} account" + ("s" if n != 1 else "")

    threshold = group["threshold"]
    if isinstance(threshold, str) and threshold.startswith("["):
        threshold = threshold.strip("[]").replace("'", "")

    if group["status"] == "UNKNOWN":
        return (f"{name} could not be checked against {group['rule_id']}: "
                f"{group['reason']}. Affects {accounts}.")

    return (f"{name} breaches {group['rule_id']}. "
            f"Policy limit {threshold}, actual {group['actual']}. "
            f"Affects {accounts}.")