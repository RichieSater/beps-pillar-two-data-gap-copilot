"""Optional Claude layer: drafts the readiness memo narrative.

Claude only writes prose around numbers that deterministic code already
produced — it never computes scores, gaps, or test outcomes. The app runs
fully without an API key via memo.build_fallback_memo.
"""

import json
import os

try:
    import anthropic
except ImportError:  # deterministic demo runs without AI deps
    anthropic = None

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are a Pillar Two data-readiness drafting assistant inside a controlled
professional-services demo workflow. You do not provide tax advice. Use ONLY the supplied
deterministic results (readiness score, data gaps, entity match report, safe harbour triage).
Never alter numeric values, scores, or test statuses. Where data is missing, describe the gap
and the remediation request; do not speculate about outcomes. Write concise, audit-ready
language suitable for review by a tax professional."""

MEMO_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "key_blockers": {"type": "array", "items": {"type": "string"}},
        "priority_jurisdictions": {"type": "array", "items": {"type": "string"}},
        "data_requests": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "request": {"type": "string"},
                },
                "required": ["owner", "request"],
                "additionalProperties": False,
            },
        },
        "open_questions_for_tax_review": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "executive_summary",
        "key_blockers",
        "priority_jurisdictions",
        "data_requests",
        "open_questions_for_tax_review",
    ],
    "additionalProperties": False,
}


def claude_available():
    return anthropic is not None and bool(os.environ.get("ANTHROPIC_API_KEY"))


def draft_memo_narrative(payload):
    """Ask Claude to draft the memo narrative from deterministic results.

    payload: dict with readiness_score, gaps, gap_summary, entity_matches,
    safe_harbour, group_alias, fiscal_year. Returns a dict matching MEMO_SCHEMA.
    Raises on any failure — callers fall back to the deterministic memo.
    """
    if anthropic is None:
        raise RuntimeError("anthropic package is not installed")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic()
    prompt = (
        "Draft the Pillar Two data-readiness memo narrative from the deterministic "
        "results below. Keep every number exactly as given.\n\nRESULTS:\n"
        + json.dumps(payload, indent=2, default=str)
    )

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": MEMO_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    text = next(block.text for block in message.content if block.type == "text")
    return json.loads(text)
