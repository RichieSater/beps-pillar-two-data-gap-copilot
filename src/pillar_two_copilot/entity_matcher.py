"""Cross-file entity name reconciliation.

Entity names rarely match exactly across ERP, provision, and legal-entity
sources ("Atlas IE Holdings Ltd" vs "... Limited"). We normalize away
legal-form suffixes and punctuation, then fuzzy-match the remainder.
"""

import difflib
import re

LEGAL_SUFFIXES = [
    "limited", "ltd", "gmbh", "bv", "b v", "pte ltd", "pte", "inc",
    "incorporated", "llc", "plc", "sarl", "s a r l", "sa", "s a",
    "co", "corp", "corporation", "holdings", "holding",
]

MATCH_REVIEW_THRESHOLD = 0.999  # anything below an exact normalized match is flagged


def normalize_entity_name(name):
    norm = re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()
    # Strip legal-form suffixes from the end, repeatedly ("Pte Ltd" -> "").
    changed = True
    while changed:
        changed = False
        for suffix in LEGAL_SUFFIXES:
            if norm.endswith(" " + suffix):
                norm = norm[: -len(suffix) - 1].strip()
                changed = True
    return norm


def match_entities(reference_names, candidate_names):
    """Match candidate names to a reference list.

    Returns a list of {candidate, matched_to, score, status} where status is
    'exact', 'fuzzy' (needs review), or 'unmatched'.
    """
    ref_by_norm = {normalize_entity_name(r): r for r in reference_names}
    results = []
    for cand in candidate_names:
        cand_norm = normalize_entity_name(cand)
        if cand_norm in ref_by_norm:
            results.append(
                {"candidate": cand, "matched_to": ref_by_norm[cand_norm], "score": 1.0, "status": "exact"}
            )
            continue
        best_ref, best_score = None, 0.0
        for ref_norm, ref in ref_by_norm.items():
            score = difflib.SequenceMatcher(None, cand_norm, ref_norm).ratio()
            if score > best_score:
                best_ref, best_score = ref, score
        if best_score >= 0.75:
            results.append(
                {"candidate": cand, "matched_to": best_ref, "score": round(best_score, 2), "status": "fuzzy"}
            )
        else:
            results.append({"candidate": cand, "matched_to": None, "score": round(best_score, 2), "status": "unmatched"})
    return results
