"""
Query -> embedding -> FAISS search -> metadata filter -> ranked results.
Used directly by the /search endpoint and as the retrieval step for chat.
"""
from sqlalchemy.orm import Session
from app.services.embedding_service import embed_query
from app.services import vector_service
from app import models
from app.config import settings


def semantic_search(db: Session, query: str, top_k: int = 8, filters: dict | None = None):
    filters = filters or {}
    query_vec = embed_query(query)

    # Over-fetch to leave room for post-filtering by metadata.
    raw_hits = vector_service.search("chunks", query_vec, top_k=max(top_k * 6, 40))

    results = []
    for vector_ref, score in raw_hits:
        if score < settings.SEARCH_SIMILARITY_THRESHOLD:
            continue
        chunk = db.query(models.Chunk).filter(models.Chunk.vector_ref == vector_ref).first()
        if not chunk:
            continue
        doc = db.query(models.Document).filter(models.Document.id == chunk.document_id).first()
        if not doc:
            continue

        if filters.get("document_id") and doc.id != filters["document_id"]:
            continue
        if filters.get("group") and doc.group != filters["group"]:
            continue
        if filters.get("year") and doc.year != filters["year"]:
            continue
        if filters.get("file_type") and doc.file_type != filters["file_type"]:
            continue

        results.append({
            "chunk_id": chunk.id,
            "document_id": doc.id,
            "document_filename": doc.filename,
            "text": chunk.text,
            "similarity": round(score, 4),
            "page": chunk.page,
            "section": chunk.section,
            "group": doc.group,
            "year": doc.year,
        })
        if len(results) >= top_k:
            break

    return results
