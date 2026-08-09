from src.engine.operators import OPERATORS




def rule_applies(rule, instrument):
    """True if the rule should be evaluated for this instrument"""
    for field, expected in rule['applies_to'].items():
        if instrument.get(field) != expected:
            return False
    return True



def evaluate_rule(rule, instrument, holding, account_total):
    """evaluate one rule against one holding. Returns a finding dict."""
    operator = OPERATORS[rule["operator"]]
    field = rule["field"]

    if field in holding:
        acutal = holding.get(field)
    else:
        acutal = instrument.get(field)

    if rule["scope"] == "portfolio":
        result, reason = operator(acutal, rule["threshold"], account_total)
    else:
        result, reason = operator(acutal, rule["threshold"])

    if result is None:
        status = "UNKNOWN"
    elif result:
        status = "COMPLIANT"
    else:
        status = "BREACH"

    return {
        "account_id": holding["account_id"],
        "isin": holding["isin"],
        "rule_id": rule["rule_id"],
        "status": status,
        "field": field,
        "threshold": rule["threshold"],
        "actual": acutal,
        "severity": rule["severity"],
        "reason": reason
    }



def evaluate_holding(holding, instrument, rules, account_total):
    """Evaluate every applicable rula against one holding"""
    findings = []
    for rule in rules:
        if not rule_applies(rule, instrument):
            continue
        findings.append(evaluate_rule(rule, instrument, holding, account_total))
    return findings



def evaluate_all(holdings, instruments, rules, account_totals):
    """Evaluate every applicable rule against every holding"""
    findings = []
    for holding in holdings:
        instrument = instruments.get(holding["isin"], {})
        account_total = account_totals.get(holding["account_id"])
        findings.extend(evaluate_holding(holding, instrument, rules, account_total))
    return findings