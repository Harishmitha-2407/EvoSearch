from app.services.comparison_service import _classify_pair, evolution_score


def test_classify_requirement_strengthened():
    claim_a = {"normalized_statement": "MFA is recommended.", "requirement_strength": "recommended", "scope": None}
    claim_b = {"normalized_statement": "MFA is mandatory.", "requirement_strength": "mandatory", "scope": None}
    change_type, semantic = _classify_pair(claim_a, claim_b)
    assert change_type == "MODIFIED"
    assert semantic == "REQUIREMENT_STRENGTHENED"


def test_classify_unchanged():
    claim_a = {"normalized_statement": "Passwords must be 12 characters.", "requirement_strength": "mandatory", "scope": None}
    claim_b = {"normalized_statement": "Passwords must be 12 characters.", "requirement_strength": "mandatory", "scope": None}
    change_type, semantic = _classify_pair(claim_a, claim_b)
    assert change_type == "UNCHANGED"


def test_classify_scope_expanded():
    claim_a = {"normalized_statement": "MFA required for admins.", "requirement_strength": "mandatory", "scope": "administrators"}
    claim_b = {"normalized_statement": "MFA required for all employees.", "requirement_strength": "mandatory", "scope": "all employees"}
    change_type, semantic = _classify_pair(claim_a, claim_b)
    assert change_type == "MODIFIED"
    assert semantic == "SCOPE_EXPANDED"


def test_evolution_score_bounds():
    changes = [
        {"change_type": "ADDED", "semantic_change": None},
        {"change_type": "MODIFIED", "semantic_change": "REQUIREMENT_STRENGTHENED"},
    ]
    result = evolution_score(changes)
    assert 0 <= result["score"] <= 100
    assert result["factors"]["ADDED"] == 1
