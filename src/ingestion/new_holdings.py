def find_new_isins(holdings, seen_isins):
    """ISINs in today's holdings that have never been held before."""
    todays = {h["isin"] for h in holdings}
    return todays - seen_isins