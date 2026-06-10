"""Export deliverables: gap register CSV, audit package JSON."""

import hashlib
import io
import json
from datetime import datetime, timezone

import pandas as pd


def file_hash(raw):
    return hashlib.sha256(raw).hexdigest()[:16]


def gaps_to_csv_bytes(gaps):
    df = pd.DataFrame(gaps)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def build_audit_package(source_hashes, mappings, entity_matches, gaps, gap_summary,
                        readiness_score, safe_harbour_results, narrative, narrative_source,
                        group_alias, fiscal_year):
    """Everything a reviewer needs to retrace the analysis, as one JSON object."""
    return {
        "package_type": "pillar_two_data_readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "group_alias": group_alias,
        "fiscal_year": fiscal_year,
        "source_files": source_hashes,  # {filename: sha256-prefix}
        "approved_mappings": mappings,
        "entity_match_report": entity_matches,
        "readiness_score": readiness_score,
        "gap_register": gaps,
        "gap_summary_by_jurisdiction": gap_summary,
        "safe_harbour_triage": safe_harbour_results,
        "memo_narrative": narrative,
        "narrative_source": narrative_source,
        "disclaimer": (
            "Prototype output for demo purposes only. Not tax advice. "
            "Deterministic rules computed all scores and statuses; AI (if used) drafted narrative only."
        ),
    }


def package_to_json_bytes(package):
    return json.dumps(package, indent=2, default=str).encode("utf-8")
