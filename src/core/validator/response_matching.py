"""
Response Matching — lenient success-token detection for validator responses.
Small local models often add extra words, punctuation, or slight variations
around a success token (e.g. "Yes, CONSISTENT." instead of just "CONSISTENT").
This module makes validator parsing robust to that variation across ANY model.
"""
import re


def matches_success_token(response: str, token: str) -> bool:
    """
    Return True if response clearly indicates the success token, tolerating:
    - extra punctuation / whitespace
    - the token embedded in a short sentence
    - case differences
    - underscores vs spaces (NO_CONTRADICTIONS vs "no contradictions")
    """
    if not response:
        return False

    cleaned = response.strip().upper()
    token_clean = token.upper()
    token_spaced = token_clean.replace("_", " ")

    # Reject if it explicitly says NOT / WRONG / INCONSISTENT near the token
    negation_words = ("NOT ", "ISN'T", "DOESN'T", "NO MATCH", "INCONSISTENT", "FAILED")
    if any(neg in cleaned for neg in negation_words) and token_clean not in (
        "NO_CONTRADICTIONS",
    ):
        # For tokens that are themselves about absence of a problem, still allow them
        if token_clean != "NO_CONTRADICTIONS":
            return False

    if token_clean in cleaned or token_spaced in cleaned:
        # Make sure response is short enough that this isn't just incidentally mentioning it
        # while actually describing problems (heuristic: success responses are short)
        if len(cleaned) <= len(token_clean) + 40:
            return True
        # Longer response — only count it if token appears at the very start
        if cleaned.startswith(token_clean) or cleaned.startswith(token_spaced):
            return True

    return False
