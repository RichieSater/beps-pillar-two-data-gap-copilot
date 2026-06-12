"""The narration layer must faithfully describe deterministic results."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pillar_two_copilot.narration import classify_source, narrate_file


def _mapping(column, field, confidence=0.95, note="Exact match on 'x'"):
    return {
        "source_file": "f.csv", "source_sheet": "data", "source_column": column,
        "suggested_field": field,
        "field_label": field or "(unmapped)",
        "confidence": confidence, "note": note,
        "approved": bool(field) and confidence >= 0.85,
    }


def test_classify_entity_master():
    kind, _ = classify_source([_mapping("Entity_ID", "entity_id"), _mapping("Entity_Name", "entity_name")])
    assert kind == "entity_master"


def test_classify_trial_balance():
    kind, _ = classify_source([_mapping("Entity_Name", "entity_name"), _mapping("Revenue", "revenue")])
    assert kind == "trial_balance"


def test_classify_tax_provision():
    kind, _ = classify_source(
        [_mapping("Entity_Name", "entity_name"), _mapping("CurrTax", "current_tax_expense")]
    )
    assert kind == "tax_provision"


def test_classify_cbcr():
    kind, _ = classify_source([_mapping("Rev_Total", "cbcr_revenue")])
    assert kind == "cbcr_report"


def test_classify_jurisdiction_attributes():
    kind, _ = classify_source([_mapping("QDMTT", "qdmtt_status")])
    assert kind == "jurisdiction_attributes"


def test_classify_unknown():
    kind, _ = classify_source([_mapping("Mystery", None, confidence=0.1)])
    assert kind == "other"


def test_narrate_file_stages_and_facts():
    profiles = [
        {"source_file": "f.csv", "source_sheet": "data", "source_column": "Entity_Name",
         "dtype": "object", "rows": 6, "non_null": 6, "fill_rate": 1.0, "sample_values": ["A"]},
        {"source_file": "f.csv", "source_sheet": "data", "source_column": "Jurisdiction",
         "dtype": "object", "rows": 6, "non_null": 5, "fill_rate": 0.833, "sample_values": ["Ireland"]},
    ]
    file_mappings = [
        _mapping("Entity_Name", "entity_name"),
        _mapping("Jurisdiction", "jurisdiction", confidence=0.6, note="Token overlap with 'country'"),
    ]
    stages = narrate_file(
        "f.csv", [("data", 6, 2)], profiles, file_mappings,
        "entity_master", "it carries both entity identifiers and legal names",
        source_hash="abc123",
    )
    labels = [s["label"] for s in stages]
    assert len(stages) == 4  # read, profile, map, classify (no reconciliation stage)
    text = "\n".join(line for s in stages for line in s["lines"])
    assert "abc123" in text                      # hash recorded
    assert "Jurisdiction" in text and "83%" in text  # partially-filled column called out
    assert "queued for human review" in text     # low-confidence mapping flagged
    assert "reference list" in text              # entity-master classification consequence


def test_narrate_file_reconciliation_stage():
    matches = [
        {"candidate": "Atlas GmbH", "matched_to": "Atlas GmbH", "score": 1.0, "status": "exact"},
        {"candidate": "Atlas UK Service Ltd", "matched_to": "Atlas UK Services Ltd",
         "score": 0.94, "status": "fuzzy"},
        {"candidate": "Mystery Co", "matched_to": None, "score": 0.31, "status": "unmatched"},
    ]
    stages = narrate_file(
        "tb.xlsx", [("TB", 6, 5)],
        [{"source_file": "tb.xlsx", "source_sheet": "TB", "source_column": "Entity",
          "dtype": "object", "rows": 6, "non_null": 6, "fill_rate": 1.0, "sample_values": ["A"]}],
        [_mapping("Entity", "entity_name")],
        "trial_balance", "it carries entity-level financial balances",
        match_results=matches, n_reference=6,
    )
    assert len(stages) == 5
    recon = "\n".join(stages[-1]["lines"])
    assert "Atlas UK Service Ltd" in recon and "0.94" in recon
    assert "Mystery Co" in recon and "Held out" in recon
