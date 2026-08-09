import csv
import random
from pathlib import Path

random.seed(42)

INSTRUMENTS = [
    # isin, name, asset_class, issuer, rating, listing_status, domicile
    ["SE0000108656", "Volvo B",             "equity", "Volvo AB",        "",     "LISTED", ""],
    ["SE0000163594", "Ericsson B",          "equity", "Ericsson AB",     "",     "LISTED", ""],
    ["SE0000242455", "Atlas Copco A",       "equity", "Atlas Copco AB",  "",     "LISTED", ""],
    ["XS1111111111", "Nordea 2030",         "bond",   "Nordea Bank",     "A",    "",       ""],
    ["XS2222222222", "Heimstaden 2029",     "bond",   "Heimstaden AB",   "BBB",  "",       ""],
    ["XS3333333333", "Kommuninvest 2031",   "bond",   "Kommuninvest",    "AA-",  "",       ""],
    ["XS4444444444", "Castellum 2028",      "bond",   "Castellum AB",    "",     "",       ""],
    ["LU1111111111", "Global Equity Fund",  "fund",   "Amundi",          "",     "",       "LU"],
    ["IE2222222222", "Euro Bond Fund",      "fund",   "BlackRock",       "",     "",       "IE"],
    ["XX0000000001", "Unclassified Note",   "",       "Unknown Issuer",  "",     "",       ""],
    ["KY1111111111", "Offshore Growth",     "fund",   "Cayman Partners", "",     "",       "KY"],
    ["SE0000667925", "Investor B",          "equity", "Investor AB",     "",     "LISTED", ""],
]

ACCOUNTS = [
    ["ACC001", "private"],
    ["ACC002", "private"],
    ["ACC003", "corporate"],
    ["ACC004", "private"],
]

EVENTS = [
    ["2026-08-07", "XS2222222222", "RATING_DOWNGRADE", "BBB", "BB"],
    ["2026-08-07", "SE0000163594", "DELISTING", "LISTED", "DELISTED"],
    ["2026-08-07", "XS9999999999", "RATING_DOWNGRADE", "A", "BBB+"],
]

BASE = [i[0] for i in INSTRUMENTS if i[0] not in ("SE0000667925",)]


def build_holdings(date, include_new=False):
    rows = []
    for account, _ in ACCOUNTS:
        isins = list(BASE)
        if include_new and account == "ACC002":
            isins.append("SE0000667925")

        # jämnare spridning, alla nära lika stora
        values = {isin: random.randint(52000, 58000) for isin in isins}

        if account == "ACC003":
            # normalisera övriga nedåt, lyft ett innehav till ~18%
            others = [i for i in isins if i != "SE0000108656"]
            for isin in others:
                values[isin] = random.randint(48000, 52000)
            values["SE0000108656"] = int(sum(values[i] for i in others) * 0.22)

        for isin, value in values.items():
            rows.append([date, account, isin, round(value / 100, 2), float(value)])
    return rows


def write(path, header, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{path}: {len(rows)} rows")


write("data/instruments.csv",
      ["isin", "name", "asset_class", "issuer", "rating", "listing_status", "domicile"],
      INSTRUMENTS)

write("data/accounts.csv", ["account_id", "holder_type"], ACCOUNTS)

eod_header = ["date", "account_id", "isin", "quantity", "market_value"]
write("data/eod/holdings_2026-08-05.csv", eod_header, build_holdings("2026-08-05"))
write("data/eod/holdings_2026-08-06.csv", eod_header, build_holdings("2026-08-06"))
write("data/eod/holdings_2026-08-07.csv", eod_header, build_holdings("2026-08-07", include_new=True))

write("data/events/events_2026-08-07.csv",
      ["date", "isin", "event_type", "old_value", "new_value"], EVENTS)