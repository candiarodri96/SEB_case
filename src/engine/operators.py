RATING_SCALE = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", 
                "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC","C", "D"]


def rating_index(rating):
    """lower index means better rating"""
    if rating is None:
        return None, "rating missing"
    if rating not in RATING_SCALE:
        return None, f'unrecognized rating: {rating}'
    return RATING_SCALE.index(rating), None