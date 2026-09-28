"""
Generates short/detailed summaries, key topics, and a document-type guess.
Falls back to a purely extractive heuristic (first + most claim-dense
sentences, frequency-based keyword topics) when no LLM is configured.
"""
import re
from collections import Counter
from app.services import llm_service
from app.utils.text_cleaning import split_sentences

DOC_TYPE_KEYWORDS = {
    "policy": ["policy", "shall", "must", "compliance", "employees must"],
    "manual": ["manual", "instructions", "step", "how to"],
    "report": ["report", "findings", "results", "analysis"],
    "specification": ["specification", "spec", "requirements", "architecture"],
}

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "to",
    "of", "and", "or", "in", "on", "for", "with", "that", "this", "as", "by",
    "at", "it", "from", "will", "shall", "must", "should", "may", "not",
}


def _guess_doc_type(text: str) -> str:
    low = text.lower()
    scores = {}
    for label, keywords in DOC_TYPE_KEYWORDS.items():
        scores[label] = sum(low.count(k) for k in keywords)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general document"


def _heuristic_keywords(text: str, top_n=8):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text)
    counts = Counter(w.lower() for w in words if w.lower() not in STOPWORDS)
    top = [w for w, _ in counts.most_common(top_n)]
    return [w.capitalize() for w in top]


def _heuristic_summary(full_text: str):
    sentences = split_sentences(full_text)
    short = " ".join(sentences[:3]) if sentences else full_text[:400]
    detailed = " ".join(sentences[:12]) if sentences else full_text[:1500]
    return short.strip(), detailed.strip()


SYSTEM_PROMPT = (
    "You summarize documents accurately and concisely, using ONLY "
    "information present in the provided text. Never invent facts, dates, "
    "or figures. Return ONLY JSON with keys: short_summary (2-5 sentences), "
    "detailed_summary (structured, a few short paragraphs), key_topics "
    "(array of up to 8 short strings), document_type (short string guess "
    "like 'policy', 'report', 'manual', 'specification', or 'code')."
)


def summarize_document(full_text: str) -> dict:
    truncated = full_text[:12000]  # keep prompt bounded; retrieval, not brute force
    if llm_service.is_available():
        result = llm_service.call_structured(SYSTEM_PROMPT, truncated, max_tokens=1200)
        if isinstance(result, dict) and "short_summary" in result:
            return {
                "short_summary": result.get("short_summary", ""),
                "detailed_summary": result.get("detailed_summary", ""),
                "key_topics": result.get("key_topics", []) or [],
                "document_type_guess": result.get("document_type", "general document"),
            }
    short, detailed = _heuristic_summary(full_text)
    return {
        "short_summary": short,
        "detailed_summary": detailed,
        "key_topics": _heuristic_keywords(full_text),
        "document_type_guess": _guess_doc_type(full_text),
    }
