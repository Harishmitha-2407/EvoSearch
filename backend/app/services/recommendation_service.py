"""
Heuristic, evidence-based improvement suggestions. Every suggestion carries
its evidence and a confidence score, and is explicitly framed as a
suggestion, never a fact (per spec section 22 / 55).
"""
import re

AMBIGUOUS_TERMS = ["tbd", "etc.", "as appropriate", "if necessary", "may vary", "at some point"]


def suggest_for_document(full_text: str, claims: list[dict]) -> list[dict]:
    suggestions = []
    low = full_text.lower()

    for term in AMBIGUOUS_TERMS:
        if term in low:
            idx = low.index(term)
            suggestions.append({
                "category": "ambiguity",
                "description": f"The document uses vague/ambiguous language ('{term}') that may be hard to enforce consistently.",
                "evidence": full_text[max(0, idx - 60):idx + 60].strip(),
                "location": None,
                "confidence": 0.5,
            })

    # Contradiction heuristic: same topic with both mandatory and optional claims
    by_topic = {}
    for c in claims:
        by_topic.setdefault(c["topic"], set()).add(c.get("requirement_strength"))
    for topic, strengths in by_topic.items():
        if "mandatory" in strengths and "optional" in strengths:
            suggestions.append({
                "category": "contradiction",
                "description": f"Topic '{topic}' has claims marked both mandatory and optional in this document - may be contradictory or context-dependent.",
                "evidence": None,
                "location": f"topic: {topic}",
                "confidence": 0.4,
            })

    if len(full_text.split()) < 50:
        suggestions.append({
            "category": "missing sections",
            "description": "Document is very short; it may be missing expected sections (scope, definitions, enforcement, exceptions).",
            "evidence": f"Document length: ~{len(full_text.split())} words.",
            "location": None,
            "confidence": 0.3,
        })

    return suggestions


def suggest_for_code(entities: list[dict], raw_text: str) -> list[dict]:
    suggestions = []

    for e in entities:
        if e["entity_type"] in ("function", "method") and not e.get("docstring"):
            suggestions.append({
                "category": "documentation gaps",
                "description": f"Function/method '{e['name']}' has no docstring.",
                "evidence": e.get("signature"),
                "location": f"line {e.get('start_line')}",
                "confidence": 0.6,
            })

    if raw_text:
        for m in re.finditer(r"except\s*:\s*\n", raw_text):
            line = raw_text.count("\n", 0, m.start()) + 1
            suggestions.append({
                "category": "error handling",
                "description": "Bare 'except:' clause swallows all exceptions, including unrelated bugs and KeyboardInterrupt.",
                "evidence": None,
                "location": f"line {line}",
                "confidence": 0.7,
            })

        for m in re.finditer(r"#\s*TODO", raw_text, re.IGNORECASE):
            line = raw_text.count("\n", 0, m.start()) + 1
            suggestions.append({
                "category": "maintainability",
                "description": "Unresolved TODO comment found.",
                "evidence": None,
                "location": f"line {line}",
                "confidence": 0.9,
            })

        if re.search(r"(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{4,}", raw_text, re.IGNORECASE):
            suggestions.append({
                "category": "security",
                "description": "Possible hardcoded credential/secret literal in source - review whether this should be an environment variable.",
                "evidence": None,
                "location": None,
                "confidence": 0.5,
            })

    # Duplicate function names across the same file (excluding methods, which
    # legitimately repeat names across classes)
    names = [e["name"] for e in entities if e["entity_type"] == "function"]
    dupes = {n for n in names if names.count(n) > 1}
    for n in dupes:
        suggestions.append({
            "category": "maintainability",
            "description": f"Function name '{n}' is defined more than once at module level - possible duplication or accidental override.",
            "evidence": None, "location": None, "confidence": 0.6,
        })

    return suggestions
