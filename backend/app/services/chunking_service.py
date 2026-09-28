"""
Intelligent chunking: paragraph-aware, falling back to sentence-aware
when a paragraph is too large, respecting a token budget with overlap.
Every chunk keeps its source page (if known) for traceability.
"""
from dataclasses import dataclass
from typing import List, Optional
from app.utils.text_cleaning import split_paragraphs, split_sentences, approx_token_count
from app.config import settings


@dataclass
class ChunkCandidate:
    text: str
    page: Optional[int]
    section: Optional[str] = None


def chunk_pages(pages, chunk_size=None, overlap=None) -> List[ChunkCandidate]:
    """pages: list[(page_or_none, text)]"""
    chunk_size = chunk_size or settings.CHUNK_SIZE_TOKENS
    overlap = overlap or settings.CHUNK_OVERLAP_TOKENS

    chunks: List[ChunkCandidate] = []

    for page_num, text in pages:
        paragraphs = split_paragraphs(text) or [text]
        buffer_sentences: List[str] = []
        buffer_tokens = 0

        def flush(section=None):
            nonlocal buffer_sentences, buffer_tokens
            if buffer_sentences:
                chunks.append(ChunkCandidate(text=" ".join(buffer_sentences).strip(), page=page_num))
                # keep an overlap tail for the next chunk
                if overlap > 0:
                    tail = []
                    tail_tokens = 0
                    for s in reversed(buffer_sentences):
                        t = approx_token_count(s)
                        if tail_tokens + t > overlap:
                            break
                        tail.insert(0, s)
                        tail_tokens += t
                    buffer_sentences = tail
                    buffer_tokens = tail_tokens
                else:
                    buffer_sentences = []
                    buffer_tokens = 0

        for para in paragraphs:
            para_tokens = approx_token_count(para)

            if para_tokens > chunk_size:
                # paragraph itself too large -> split into sentences
                for sent in split_sentences(para):
                    s_tokens = approx_token_count(sent)
                    if buffer_tokens + s_tokens > chunk_size:
                        flush()
                    buffer_sentences.append(sent)
                    buffer_tokens += s_tokens
                continue

            if buffer_tokens + para_tokens > chunk_size:
                flush()

            buffer_sentences.append(para)
            buffer_tokens += para_tokens

        flush()

    # Drop degenerate empty chunks
    return [c for c in chunks if c.text.strip()]
