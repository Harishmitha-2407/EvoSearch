"""
Extracts atomic, normalized claims from document text.

Prefers the LLM (structured JSON output, validated) when available;
otherwise falls back to a deterministic heuristic that flags sentences
containing requirement-style language (must/shall/required/recommended/
optional/may) and derives a topic + requirement strength from keywords.
Heuristic mode is intentionally conservative: it will surface fewer claims
than an LLM would, rather than fabricate structure that isn't there.
"""
import re
from app.services import llm_service
from app.utils.text_cleaning import split_sentences

MANDATORY_WORDS = ["must", "shall", "required", "mandatory", "is required to", "has to"]
RECOMMENDED_WORDS = ["should", "recommended", "advised", "encouraged"]
OPTIONAL_WORDS = ["may", "optional", "can choose to", "at their discretion"]

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "and", "or", "in", "on", "for", "with", "that", "this",
    "must", "shall", "should", "may", "will", "not", "all", "any",
}


def _requirement_strength(sentence: str):
    low = sentence.lower()
    if any(w in low for w in MANDATORY_WORDS):
        return "mandatory"
    if any(w in low for w in RECOMMENDED_WORDS):
        return "recommended"
    if any(w in low for w in OPTIONAL_WORDS):
        return "optional"
    return None


def _guess_topic(sentence: str) -> str:
    """Very lightweight topic guess: the most salient capitalized or
    frequent non-stopword noun-ish token near the start of the sentence."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", sentence)
    candidates = [w for w in words if w.lower() not in STOPWORDS]
    if not candidates:
        return "General"
    # Prefer a capitalized multi-word acronym/proper-noun-like token first
    for w in candidates:
        if w.isupper() and len(w) <= 6:
            return w
    return candidates[0].capitalize()


def _guess_scope(sentence: str) -> str | None:
    low = sentence.lower()
    if "all employees" in low:
        return "all employees"
    if "administrators" in low or "admins" in low:
        return "administrators"
    if "users" in low:
        return "users"
    if "employees" in low:
        return "employees"
    return None


def extract_claims_heuristic(text: str, page=None):
    claims = []
    for sentence in split_sentences(text):
        strength = _requirement_strength(sentence)
        if not strength:
            continue
        if len(sentence.split()) < 4:
            continue
        claims.append({
            "topic": _guess_topic(sentence),
            "statement": sentence.strip(),
            "requirement_strength": strength,
            "scope": _guess_scope(sentence),
            "importance": 0.6 if strength == "mandatory" else 0.4,
            "page": page,
        })
    return claims


SYSTEM_PROMPT = (
    "You are a precise information-extraction engine. Extract atomic, "
    "verifiable claims from the given document excerpt. Return ONLY a JSON "
    "array, no prose, no markdown fences. Each element must have exactly "
    "these keys: topic (short string), statement (normalized sentence), "
    "requirement_strength (one of: mandatory, recommended, optional, none), "
    "scope (string or null), importance (0.0-1.0 float). "
    "Only extract claims that are explicitly present in the text - never "
    "invent facts, dates, or numbers not stated in the excerpt. If there are "
    "no clear claims, return an empty array []."
)


def extract_claims(text: str, page=None):
    if llm_service.is_available():
        result = llm_service.call_structured(
            SYSTEM_PROMPT,
            f"Document excerpt (page {page if page else 'n/a'}):\n\n{text}",
        )
        if isinstance(result, list):
            valid = []
            for item in result:
                if not isinstance(item, dict):
                    continue
                if "statement" not in item or "topic" not in item:
                    continue
                item.setdefault("requirement_strength", None)
                item.setdefault("scope", None)
                item.setdefault("importance", 0.5)
                item.setdefault("page", page)
                valid.append(item)
            return valid
        # LLM failed / returned malformed output -> fall through to heuristic
    return extract_claims_heuristic(text, page=page)
