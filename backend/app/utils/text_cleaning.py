import re


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str):
    """Lightweight sentence splitter (no heavy NLP dependency)."""
    text = text.strip()
    if not text:
        return []
    # Split on sentence-ending punctuation followed by whitespace + capital/number,
    # while trying not to split on common abbreviations.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: str):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs


def approx_token_count(text: str) -> int:
    # Rough approximation: ~1.3 tokens per word for English text.
    words = len(text.split())
    return int(words * 1.3)
