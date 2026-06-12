from pillar_two_copilot.entity_matcher import match_entities, normalize_entity_name


def test_legal_suffixes_stripped():
    assert normalize_entity_name("Atlas IE Holdings Limited") == normalize_entity_name("Atlas IE Holdings Ltd")
    assert normalize_entity_name("Atlas NL B.V.") == normalize_entity_name("Atlas NL BV")
    assert normalize_entity_name("Atlas SG IP Pte. Ltd") == normalize_entity_name("Atlas SG IP Pte Ltd")


def test_exact_after_normalization():
    results = match_entities(["Atlas US Inc"], ["Atlas US, Inc."])
    assert results[0]["status"] == "exact"
    assert results[0]["matched_to"] == "Atlas US Inc"


def test_typo_is_fuzzy_matched_and_flagged():
    results = match_entities(["Atlas UK Services Ltd"], ["Atlas UK Service Ltd"])
    assert results[0]["status"] == "fuzzy"
    assert results[0]["matched_to"] == "Atlas UK Services Ltd"
    assert results[0]["score"] >= 0.9


def test_unrelated_name_unmatched():
    results = match_entities(["Atlas US Inc"], ["Borealis Shipping AS"])
    assert results[0]["status"] == "unmatched"
    assert results[0]["matched_to"] is None
