"""
Aligns claims between two document versions using embedding similarity
(candidate matching only - NOT the final classification, per spec section
11: "semantic similarity does not automatically mean unchanged"), then
applies deterministic/hybrid rules to classify the change.
"""
import numpy as np
from app.config import settings
from app.services.embedding_service import embed_texts
from app.services import llm_service

STRENGTH_ORDER = {"none": 0, "optional": 1, "recommended": 2, "mandatory": 3}


def _strength_rank(s):
    return STRENGTH_ORDER.get((s or "none").lower(), 0)


def _cosine_matrix(vecs_a: np.ndarray, vecs_b: np.ndarray) -> np.ndarray:
    # vectors are already normalized by embed_texts
    return vecs_a @ vecs_b.T


def _classify_pair(claim_a: dict, claim_b: dict):
    text_a = (claim_a["normalized_statement"] or "").strip().lower()
    text_b = (claim_b["normalized_statement"] or "").strip().lower()

    if text_a == text_b:
        return "UNCHANGED", None

    rank_a = _strength_rank(claim_a.get("requirement_strength"))
    rank_b = _strength_rank(claim_b.get("requirement_strength"))

    if rank_b > rank_a:
        return "MODIFIED", "REQUIREMENT_STRENGTHENED"
    if rank_b < rank_a:
        return "MODIFIED", "REQUIREMENT_WEAKENED"

    scope_a = (claim_a.get("scope") or "").lower()
    scope_b = (claim_b.get("scope") or "").lower()
    if scope_a != scope_b:
        if "all" in scope_b and "all" not in scope_a:
            return "MODIFIED", "SCOPE_EXPANDED"
        if "all" in scope_a and "all" not in scope_b:
            return "MODIFIED", "SCOPE_REDUCED"
        return "MODIFIED", "SCOPE_EXPANDED" if len(scope_b) > len(scope_a) else "SCOPE_REDUCED"

    if any(ch.isdigit() for ch in text_a) or any(ch.isdigit() for ch in text_b):
        return "MODIFIED", "VALUE_CHANGED"

    return "MODIFIED", None


def _explain(claim_a: dict, claim_b: dict, change_type: str, semantic_change: str):
    if llm_service.is_available():
        prompt = (
            f"Previous claim: \"{claim_a['normalized_statement'] if claim_a else '(none - newly added)'}\"\n"
            f"Current claim: \"{claim_b['normalized_statement'] if claim_b else '(none - removed)'}\"\n"
            f"Detected change type: {change_type} ({semantic_change or 'n/a'})\n"
            "In one concise sentence, explain what changed and why it matters. "
            "Do not speculate about the author's motivation unless explicitly stated."
        )
        text = llm_service.call_text(
            "You explain document changes precisely and concisely based only on given claim text.",
            prompt, max_tokens=200,
        )
        if text:
            return text

    # Templated fallback
    if change_type == "ADDED":
        return f"A new requirement appeared: \"{claim_b['normalized_statement']}\"."
    if change_type == "REMOVED":
        return f"A previous requirement was removed: \"{claim_a['normalized_statement']}\"."
    if semantic_change == "REQUIREMENT_STRENGTHENED":
        return "The requirement became stricter between versions."
    if semantic_change == "REQUIREMENT_WEAKENED":
        return "The requirement became less strict between versions."
    if semantic_change == "SCOPE_EXPANDED":
        return "The requirement's scope was expanded to cover more people/systems."
    if semantic_change == "SCOPE_REDUCED":
        return "The requirement's scope was narrowed."
    if semantic_change == "VALUE_CHANGED":
        return "A specific value or number in the requirement changed."
    return "The wording of this requirement changed between versions."


def compare_claims(claims_a: list[dict], claims_b: list[dict]) -> list[dict]:
    """
    claims_a / claims_b: list of dicts with keys id, topic, normalized_statement,
    requirement_strength, scope (as produced by Claim ORM -> dict).
    Returns list of change dicts ready to persist as `Change` rows.
    """
    if not claims_a and not claims_b:
        return []

    changes = []

    if claims_a and claims_b:
        vecs_a = embed_texts([c["normalized_statement"] for c in claims_a])
        vecs_b = embed_texts([c["normalized_statement"] for c in claims_b])
        sims = _cosine_matrix(vecs_a, vecs_b)
    else:
        sims = np.zeros((len(claims_a), len(claims_b)))

    matched_a = set()
    matched_b = set()

    # Greedy best-match pairing above threshold
    pairs = []
    for i in range(len(claims_a)):
        for j in range(len(claims_b)):
            pairs.append((sims[i, j], i, j))
    pairs.sort(key=lambda x: -x[0])

    for score, i, j in pairs:
        if score < settings.CLAIM_ALIGNMENT_THRESHOLD:
            break
        if i in matched_a or j in matched_b:
            continue
        matched_a.add(i)
        matched_b.add(j)
        change_type, semantic_change = _classify_pair(claims_a[i], claims_b[j])
        explanation = _explain(claims_a[i], claims_b[j], change_type, semantic_change)
        changes.append({
            "topic": claims_b[j]["topic"] or claims_a[i]["topic"],
            "change_type": change_type,
            "semantic_change": semantic_change,
            "previous_claim_id": claims_a[i]["id"],
            "current_claim_id": claims_b[j]["id"],
            "previous_text": claims_a[i]["normalized_statement"],
            "current_text": claims_b[j]["normalized_statement"],
            "explanation": explanation,
            "confidence": round(float(score), 3),
        })

    for i, claim in enumerate(claims_a):
        if i not in matched_a:
            changes.append({
                "topic": claim["topic"],
                "change_type": "REMOVED",
                "semantic_change": None,
                "previous_claim_id": claim["id"],
                "current_claim_id": None,
                "previous_text": claim["normalized_statement"],
                "current_text": None,
                "explanation": _explain(claim, None, "REMOVED", None),
                "confidence": 0.9,
            })

    for j, claim in enumerate(claims_b):
        if j not in matched_b:
            changes.append({
                "topic": claim["topic"],
                "change_type": "ADDED",
                "semantic_change": None,
                "previous_claim_id": None,
                "current_claim_id": claim["id"],
                "previous_text": None,
                "current_text": claim["normalized_statement"],
                "explanation": _explain(None, claim, "ADDED", None),
                "confidence": 0.9,
            })

    return changes


def evolution_score(changes: list[dict]) -> dict:
    """A project-defined (NOT a standardized/scientific) 0-100 score
    reflecting how much a document changed, per spec section 23."""
    if not changes:
        return {"score": 0, "factors": {}}

    weights = {
        "ADDED": 3, "REMOVED": 3, "MODIFIED": 2, "UNCHANGED": 0,
    }
    semantic_bonus = {
        "REQUIREMENT_STRENGTHENED": 2, "REQUIREMENT_WEAKENED": 2,
        "SCOPE_EXPANDED": 1.5, "SCOPE_REDUCED": 1.5, "VALUE_CHANGED": 1,
    }
    raw = 0.0
    factor_counts = {}
    for c in changes:
        raw += weights.get(c["change_type"], 0)
        raw += semantic_bonus.get(c.get("semantic_change"), 0)
        factor_counts[c["change_type"]] = factor_counts.get(c["change_type"], 0) + 1

    max_possible = len(changes) * (3 + 2)  # rough ceiling for normalization
    score = min(100, round((raw / max_possible) * 100)) if max_possible else 0
    return {"score": score, "factors": factor_counts}
