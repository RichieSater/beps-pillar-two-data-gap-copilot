"""Heuristic source-column -> Pillar Two field mapping.

Deterministic and explainable: every suggestion carries a confidence and
a note saying *why* it matched. Claude may add review commentary on top
(see claude_client), but never changes the scores.
"""

import re

from .field_catalog import FIELD_CATALOG

# Suggestions below this confidence are left unmapped for human triage.
SUGGESTION_THRESHOLD = 0.45
# Suggestions at/above this confidence are pre-ticked for approval.
AUTO_APPROVE_THRESHOLD = 0.85


def normalize(text):
    """Lowercase, strip punctuation/camelCase boundaries, collapse spaces."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(text))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def _token_score(candidate_tokens, synonym_tokens):
    """Jaccard overlap between token sets, scaled into [0, 0.8]."""
    if not candidate_tokens or not synonym_tokens:
        return 0.0
    inter = candidate_tokens & synonym_tokens
    union = candidate_tokens | synonym_tokens
    return 0.8 * len(inter) / len(union)


def score_column(source_column):
    """Return (best_field, confidence, note) for one source column name."""
    norm = normalize(source_column)
    tokens = set(norm.split())
    best_field, best_score, best_note = None, 0.0, ""

    for field_key, spec in FIELD_CATALOG.items():
        candidates = [field_key.replace("_", " ")] + spec["synonyms"]
        for syn in candidates:
            syn_norm = normalize(syn)
            if norm == syn_norm:
                score, note = 0.95, f"Exact match on '{syn}'"
            elif syn_norm and (syn_norm in norm or norm in syn_norm):
                score, note = 0.85, f"Substring match on '{syn}'"
            else:
                score = _token_score(tokens, set(syn_norm.split()))
                note = f"Token overlap with '{syn}'"
            if score > best_score:
                best_field, best_score, best_note = field_key, score, note

    return best_field, round(best_score, 2), best_note


def suggest_mappings(column_profiles):
    """Suggest a Pillar Two field per profiled source column.

    Returns a list of mapping records preserving full source lineage —
    file, sheet, column — plus confidence and an approval default.
    """
    suggestions = []
    for profile in column_profiles:
        field, confidence, note = score_column(profile["source_column"])
        if confidence < SUGGESTION_THRESHOLD:
            field, note = None, "No confident match — needs manual mapping"
        suggestions.append(
            {
                "source_file": profile["source_file"],
                "source_sheet": profile["source_sheet"],
                "source_column": profile["source_column"],
                "suggested_field": field,
                "field_label": FIELD_CATALOG[field]["label"] if field else "(unmapped)",
                "confidence": confidence,
                "note": note,
                "approved": bool(field) and confidence >= AUTO_APPROVE_THRESHOLD,
            }
        )
    return suggestions
