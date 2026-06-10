"""End-to-end test against the synthetic Aurora sample files (the demo path)."""

import json
from pathlib import Path

import pytest

from pillar_two_copilot.column_mapper import suggest_mappings
from pillar_two_copilot.completeness import (
    assemble_datasets,
    find_gaps,
    gap_summary_by_jurisdiction,
    readiness_score,
)
from pillar_two_copilot.export import build_audit_package, gaps_to_csv_bytes, package_to_json_bytes
from pillar_two_copilot.ingestion import load_tabular, profile_columns
from pillar_two_copilot.memo import build_fallback_narrative, memo_to_markdown
from pillar_two_copilot.safe_harbour import safe_harbour_triage

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_inputs"

pytestmark = pytest.mark.skipif(not SAMPLE_DIR.exists(), reason="sample data not generated")


@pytest.fixture(scope="module")
def pipeline():
    frames, profiles = {}, []
    for path in sorted(SAMPLE_DIR.iterdir()):
        if path.suffix.lower() not in (".csv", ".xlsx"):
            continue
        for sheet, df in load_tabular(path).items():
            frames[(path.name, sheet)] = df
            profiles.extend(profile_columns(df, path.name, sheet))
    mappings = suggest_mappings(profiles)
    for m in mappings:  # reviewer approves all suggestions
        if m["suggested_field"]:
            m["approved"] = True
    master = frames[("entity_master.csv", "data")]
    entity_df, jurisdiction_df, matches = assemble_datasets(
        frames, mappings, master["LegalEntityName"].tolist()
    )
    gaps = find_gaps(entity_df, jurisdiction_df)
    return frames, mappings, entity_df, jurisdiction_df, matches, gaps


def test_all_six_entities_reconciled(pipeline):
    _, _, entity_df, _, matches, _ = pipeline
    assert len(entity_df) == 6
    fuzzy = [m for m in matches if m["status"] == "fuzzy"]
    assert any(m["candidate"] == "Aurora UK Service Ltd" for m in fuzzy)
    assert not [m for m in matches if m["status"] == "unmatched"]


def test_known_planted_gaps_are_found(pipeline):
    *_, gaps = pipeline
    found = {(g["entity"], g["field"]) for g in gaps}
    assert ("Aurora IE Holdings Limited", "deferred_tax_expense") in found
    assert ("Aurora SG IP Pte Ltd", "payroll_costs") in found
    assert ("Aurora NL B.V.", "tangible_asset_carrying_value") in found
    assert ("Aurora UK Services Ltd", "jurisdiction") in found


def test_safe_harbour_story(pipeline):
    _, _, entity_df, jurisdiction_df, _, _ = pipeline
    results = {r["jurisdiction"]: r for r in safe_harbour_triage(entity_df, jurisdiction_df, 2026)}
    assert "Simplified ETR" not in results["Ireland"]["indicative_passes"]  # 12% < 17%
    assert "De minimis" in results["Netherlands"]["indicative_passes"]
    assert results["Singapore"]["can_evaluate"] == "Partial"  # tax accrued + payroll missing


def test_memo_and_exports_render(pipeline):
    _, mappings, entity_df, jurisdiction_df, matches, gaps = pipeline
    score = readiness_score(gaps, entity_df, jurisdiction_df)
    assert 0.8 < score < 1.0
    summary = gap_summary_by_jurisdiction(gaps)
    sh = safe_harbour_triage(entity_df, jurisdiction_df, 2026)
    narrative = build_fallback_narrative(score, gaps, sh)
    memo = memo_to_markdown(narrative, score, gaps, summary, sh, mappings,
                            "Aurora Global Group", 2026, "Deterministic draft")
    assert "Pillar Two Data Readiness Memo" in memo
    assert "Appendix B" in memo

    csv_bytes = gaps_to_csv_bytes(gaps)
    assert b"deferred_tax_expense" in csv_bytes

    package = build_audit_package({"f.csv": "abc"}, mappings, matches, gaps, summary,
                                  score, sh, narrative, "Deterministic draft",
                                  "Aurora Global Group", 2026)
    parsed = json.loads(package_to_json_bytes(package))
    assert parsed["readiness_score"] == score
    assert parsed["package_type"] == "pillar_two_data_readiness"
