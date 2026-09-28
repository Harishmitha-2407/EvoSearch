# ARCHITECTURE.md

## System diagram

```
                ┌───────────────────┐
                │       USER        │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │   React Frontend  │  (Vite + TS + Tailwind + TanStack Query)
                └─────────┬─────────┘
                          │ /api/*
                          ▼
                ┌───────────────────┐
                │    FastAPI API    │  app/main.py + app/api/*.py
                └─────────┬─────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
   Document Engine   Code Analysis    AI Assistant
   (documents.py)    (code.py)        (chat.py)
          │               │                │
          ▼               ▼                ▼
      Chunking        AST/Regex        Retrieval
   (chunking_       Parser          (retrieval_
    service.py)   (code_analysis_    service.py)
          │        service.py)          │
          ▼               ▼                ▼
      Claims          Code Entities     Context
  (claim_service.py)  (models.py)    Construction
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                   Embedding Engine
               (embedding_service.py — sentence-transformers)
                          │
                          ▼
                    Vector Search
                (vector_service.py — FAISS IndexFlatIP)
                          │
                          ▼
                  Claim Alignment
              (comparison_service.py)
                          │
                          ▼
                  Change Detection
           (ADDED/REMOVED/MODIFIED/UNCHANGED
            + semantic sub-categories)
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      Timeline        Impact Analysis   Knowledge Map
   (api/timeline.py) (impact_service.py) (api/timeline.py)
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                     AI Explanation
                  (llm_service.py, optional)
                          │
                          ▼
                     React UI
```

## Backend module map

```
backend/app/
├── main.py              FastAPI app, router registration, global exception handler
├── config.py            pydantic-settings: all env-configurable values
├── database.py           SQLAlchemy engine/session/Base
├── dependencies.py       FastAPI DB-session dependency
├── models.py             ORM: Document, Chunk, Claim, Change, CodeFile,
│                         CodeEntity, CodeChange, AnalysisResult,
│                         ChatSession, ChatMessage
├── schemas.py            Pydantic request/response models
│
├── api/
│   ├── health.py         GET /api/health
│   ├── documents.py       document upload pipeline + CRUD + suggestions
│   ├── search.py          POST /api/search
│   ├── chat.py            POST /api/chat (+ session history)
│   ├── comparison.py      POST /api/comparison/documents
│   ├── code.py             code upload + parse + compare + impact
│   └── timeline.py         GET /api/timeline/{group} (+ /knowledge-map)
│
├── services/
│   ├── document_service.py     text extraction (pdf/docx/txt/md/csv/json/yaml)
│   ├── chunking_service.py     paragraph→sentence→token-aware chunking
│   ├── embedding_service.py    sentence-transformers wrapper + disk cache
│   ├── vector_service.py       FAISS index management (namespaces: chunks, claims, code_entities)
│   ├── claim_service.py        claim extraction (LLM + heuristic fallback)
│   ├── summary_service.py      document summarization (LLM + heuristic fallback)
│   ├── comparison_service.py   claim alignment + change classification + evolution score
│   ├── retrieval_service.py    query embedding → FAISS search → metadata filter
│   ├── llm_service.py          thin Anthropic API wrapper, validated JSON parsing
│   ├── code_analysis_service.py    Python AST + regex-fallback parsers
│   ├── code_comparison_service.py  entity diffing + security-pattern flags
│   ├── impact_service.py       textual cross-file reference search
│   └── recommendation_service.py   evidence-based improvement suggestions
│
├── utils/
│   ├── hashing.py         sha256 helpers (checksums, embedding-cache keys)
│   └── text_cleaning.py   whitespace normalization, sentence/paragraph split
│
└── tests/                 pytest unit tests
```

## Key design decisions

**Why FAISS `IndexFlatIP` with normalized vectors instead of cosine index
type?** Inner product on unit-normalized vectors is mathematically
identical to cosine similarity, and `IndexFlatIP` is the simplest exact
(non-approximate) FAISS index — appropriate for the document/code volumes
this build targets. Swapping in an approximate index (HNSW/IVF) for larger
corpora only requires changing `_get_index()` in `vector_service.py`.

**Why store `vector_ref` on the SQL row instead of storing embeddings in
Postgres?** Per the spec: don't store large vectors in relational tables
when an external vector store is in use. `vector_ref` is just the integer
position in the FAISS index, letting us go DB row → FAISS vector and back
in O(1) without duplicating the vector data.

**Why is claim alignment (`comparison_service.py`) *not* purely
embedding-similarity-based?** The spec is explicit that semantic similarity
identifies *candidate* matches only — it doesn't tell you whether a
requirement got stricter or looser. So alignment uses embeddings to find
the best candidate pairing (greedy, thresholded), then a separate
deterministic rule set (`_classify_pair`) inspects requirement-strength
keywords, scope keywords, and literal text equality to decide the actual
change type.

**Why does every LLM call have a non-LLM fallback?** Per spec sections 10,
16, 17, 25: "never accept malformed AI output without validation," and the
system should be evaluable/usable without assuming an LLM key is present.
`llm_service.call_structured()` validates JSON structure and returns `None`
on any failure (network error, malformed JSON, missing keys) — every
calling service treats `None` as "fall back to heuristic," never as a
crash.

**Why is Python code analysis significantly more capable than other
languages?** Python ships a full parser (`ast`) in the standard library
with zero extra dependencies. Full-fidelity multi-language parsing needs
Tree-sitter grammars (native bindings per language) — a real dependency
commitment intentionally deferred past this build pass (see README
Limitations/Future Work). The regex fallback still produces diffable,
useful structure for common patterns.
