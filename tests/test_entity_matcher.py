from pillar_two_copilot.entity_matcher import match_entities, normalize_entity_name


def test_legal_suffixes_stripped():
    assert normalize_entity_name("Aurora IE Holdings Limited") == normalize_entity_name("Aurora IE Holdings Ltd")
    assert normalize_entity_name("Aurora NL B.V.") == normalize_entity_name("Aurora NL BV")
    assert normalize_entity_name("Aurora SG IP Pte. Ltd") == normalize_entity_name("Aurora SG IP Pte Ltd")


def test_exact_after_normalization():
    results = match_entities(["Aurora US Inc"], ["Aurora US, Inc."])
    assert results[0]["status"] == "exact"
    assert results[0]["matched_to"] == "Aurora US Inc"


def test_typo_is_fuzzy_matched_and_flagged():
    results = match_entities(["Aurora UK Services Ltd"], ["Aurora UK Service Ltd"])
    assert results[0]["status"] == "fuzzy"
    assert results[0]["matched_to"] == "Aurora UK Services Ltd"
    assert results[0]["score"] >= 0.9


def test_unrelated_name_unmatched():
    results = match_entities(["Aurora US Inc"], ["Borealis Shipping AS"])
    assert results[0]["status"] == "unmatched"
    assert results[0]["matched_to"] is None
