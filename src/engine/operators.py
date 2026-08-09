RATING_SCALE = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", 
                "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC","C", "D"]


def rating_index(rating):
    """lower index means better rating"""
    if rating is None:
        return None, 'rating missing'
    if rating not in RATING_SCALE:
        return None, f'unrecognized rating: {rating}'
    return RATING_SCALE.index(rating), None

def min_rating(actual, threshold):
    """True if rating is at or above threshold"""
    actual_index, reason = rating_index(actual)
    if actual_index is None:
        return None, reason

    threshold_index, _ = rating_index(threshold)
    return actual_index <= threshold_index, None

def in_list(actual, threshold):
    """True uf actual is one of the allowed values"""
    if actual is None:
        return None, 'value missing'
    return actual in threshold, None

def equals(actual, threshold):
    """True if actual equals threshold"""
    if actual is None:
        return None, 'value missing'
    return actual == threshold, None

def max_percentage_of_account(actual, threshold, account_total):
    """True if actual is at or below threshold percent of the account total"""
    if actual is None:
        return None, 'value missing'
    if not account_total:
        return None, 'account total missing or zero'
    return (actual / account_total) * 100 <= threshold, None

OPERATORS = {
    'min_rating': min_rating,
    'in_list': in_list,
    'equals': equals,
    'max_percentage_of_account': max_percentage_of_account
}