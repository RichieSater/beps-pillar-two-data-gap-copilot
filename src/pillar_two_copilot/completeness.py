"""Deterministic completeness rules: assemble mapped data, find gaps, score readiness."""

import pandas as pd

from .entity_matcher import match_entities
from .field_catalog import FIELD_CATALOG, SEVERITY_WEIGHTS, blocked_purposes, fields_for_level


def _apply_mappings(df, mappings):
    """Rename a frame's columns to canonical field keys using approved mappings.

    If two columns map to the same field, the first wins (the duplicate is
    surfaced in the mapping review screen, not silently merged).
    """
    rename, seen = {}, set()
    for m in mappings:
        field = m.get("suggested_field")
        if not m.get("approved") or not field or field in seen:
            continue
        if m["source_column"] in df.columns:
            rename[m["source_column"]] = field
            seen.add(field)
    return df[list(rename.keys())].rename(columns=rename)


def assemble_datasets(frames, mappings, reference_entities=None):
    """Combine mapped source frames into one entity-level and one
    jurisdiction-level dataset.

    frames: {(source_file, sheet): DataFrame}
    mappings: approved mapping records from column_mapper
    reference_entities: canonical entity-name list (usually the entity
        master). Entity names in other files are reconciled to it.

    Returns (entity_df, jurisdiction_df, entity_match_report).
    """
    entity_frames, jurisdiction_frames = [], []
    for (source_file, sheet), df in frames.items():
        frame_mappings = [
            m for m in mappings if m["source_file"] == source_file and m["source_sheet"] == sheet
        ]
        mapped = _apply_mappings(df, frame_mappings)
        if mapped.empty or not list(mapped.columns):
            continue
        if "entity_name" in mapped.columns:
            entity_frames.append(mapped)
        elif "jurisdiction" in mapped.columns:
            jurisdiction_frames.append(mapped)

    match_report = []
    if entity_frames:
        if reference_entities is None:
            reference_entities = entity_frames[0]["entity_name"].dropna().tolist()
        canonical = []
        for frame in entity_frames:
            matches = match_entities(reference_entities, frame["entity_name"].dropna().tolist())
            match_report.extend(matches)
            lookup = {m["candidate"]: m["matched_to"] for m in matches if m["matched_to"]}
            frame = frame.copy()
            frame["entity_name"] = frame["entity_name"].map(lambda n: lookup.get(n, n))
            canonical.append(frame.groupby("entity_name", as_index=False).first())
        entity_df = canonical[0]
        for frame in canonical[1:]:
            overlap = [c for c in frame.columns if c != "entity_name" and c in entity_df.columns]
            entity_df = entity_df.merge(frame.drop(columns=overlap), on="entity_name", how="outer")
    else:
        entity_df = pd.DataFrame(columns=["entity_name"])

    if jurisdiction_frames:
        jurisdiction_df = jurisdiction_frames[0]
        for frame in jurisdiction_frames[1:]:
            overlap = [c for c in frame.columns if c != "jurisdiction" and c in jurisdiction_df.columns]
            jurisdiction_df = jurisdiction_df.merge(frame.drop(columns=overlap), on="jurisdiction", how="outer")
        jurisdiction_df = jurisdiction_df.groupby("jurisdiction", as_index=False).first()
    else:
        jurisdiction_df = pd.DataFrame(columns=["jurisdiction"])

    return entity_df, jurisdiction_df, match_report


def _gap_record(field_key, entity, jurisdiction, reason):
    spec = FIELD_CATALOG[field_key]
    if jurisdiction is None or (isinstance(jurisdiction, float) and pd.isna(jurisdiction)):
        jurisdiction = "(unassigned)"
    return {
        "jurisdiction": jurisdiction,
        "entity": entity,
        "field": field_key,
        "field_label": spec["label"],
        "severity": spec["severity"],
        "blocks": "; ".join(blocked_purposes(field_key)),
        "likely_owner": spec["likely_owner"],
        "suggested_action": spec["remediation"],
        "reason": reason,
    }


def find_gaps(entity_df, jurisdiction_df):
    """Compare assembled data against the field catalog. Returns gap records."""
    gaps = []

    entity_fields = fields_for_level("entity")
    for field_key in entity_fields:
        if field_key == "entity_name":
            continue  # entity_name is the join key; absence means no entity data at all
        if field_key not in entity_df.columns:
            for _, row in entity_df.iterrows():
                gaps.append(
                    _gap_record(
                        field_key,
                        row.get("entity_name", "(unknown)"),
                        row.get("jurisdiction", "(unknown)"),
                        "Field not present in any uploaded source",
                    )
                )
            continue
        for _, row in entity_df.iterrows():
            if pd.isna(row[field_key]):
                gaps.append(
                    _gap_record(
                        field_key,
                        row.get("entity_name", "(unknown)"),
                        row.get("jurisdiction", "(unknown)"),
                        "Value missing for this entity",
                    )
                )

    jurisdiction_fields = fields_for_level("jurisdiction")
    for field_key in jurisdiction_fields:
        if field_key not in jurisdiction_df.columns:
            for _, row in jurisdiction_df.iterrows():
                gaps.append(
                    _gap_record(field_key, "(jurisdiction-level)", row.get("jurisdiction", "(unknown)"),
                                "Field not present in any uploaded source")
                )
            continue
        for _, row in jurisdiction_df.iterrows():
            if pd.isna(row[field_key]):
                gaps.append(
                    _gap_record(field_key, "(jurisdiction-level)", row.get("jurisdiction", "(unknown)"),
                                "Value missing for this jurisdiction")
                )

    return gaps


def readiness_score(gaps, entity_df, jurisdiction_df):
    """Severity-weighted completeness in [0, 1]; 1.0 = no gaps."""
    n_entities = max(len(entity_df), 1)
    n_jurisdictions = max(len(jurisdiction_df), 1)
    total = sum(
        SEVERITY_WEIGHTS[spec["severity"]] * (n_entities if spec["level"] == "entity" else n_jurisdictions)
        for key, spec in FIELD_CATALOG.items()
        if key != "entity_name"
    )
    missing = sum(SEVERITY_WEIGHTS[g["severity"]] for g in gaps)
    if total == 0:
        return 0.0
    return round(max(0.0, 1.0 - missing / total), 3)


def gap_summary_by_jurisdiction(gaps):
    """Pivot gaps into per-jurisdiction severity counts for the dashboard."""
    summary = {}
    for g in gaps:
        row = summary.setdefault(g["jurisdiction"], {"high": 0, "medium": 0, "low": 0})
        row[g["severity"]] += 1
    return [
        {"jurisdiction": j, **counts, "total": sum(counts.values())}
        for j, counts in sorted(summary.items())
    ]
