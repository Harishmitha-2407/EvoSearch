from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.dependencies import get_db, get_current_user
from app import models, schemas
from app.config import settings
from app.utils.hashing import sha256_bytes
from app.services import (
    document_service, chunking_service, embedding_service, vector_service,
    claim_service, summary_service, recommendation_service,
)

logger = logging.getLogger("evosearch.documents")
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    group: str = Form("Ungrouped"),
    version_label: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    try:
        logger.info(f"Document upload started by user {user.id}: {file.filename}")
        
        data = await file.read()
        size_mb = len(data) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_MB:
            raise HTTPException(413, f"File exceeds max upload size of {settings.MAX_UPLOAD_MB}MB")
        if len(data) == 0:
            raise HTTPException(400, "Uploaded file is empty")

        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ") or "upload"
        checksum = sha256_bytes(data)
        file_type = document_service.guess_file_type(safe_filename)
        
        logger.info(f"File: {safe_filename}, Type: {file_type}, Size: {size_mb:.2f}MB")

        doc = models.Document(
            user_id=user.id,
            filename=safe_filename,
            file_type=file_type or "unknown",
            size_bytes=len(data),
            checksum=checksum,
            storage_path="",
            group=group or "Ungrouped",
            version_label=version_label,
            year=year,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Document record created: {doc.id}")

        storage_path = f"{settings.STORAGE_PATH}/{doc.id}_{safe_filename}"
        try:
            with open(storage_path, "wb") as f:
                f.write(data)
            doc.storage_path = storage_path
            logger.info(f"File saved to: {storage_path}")
        except Exception as e:
            logger.warning(f"Could not persist raw file to disk: {e}")

        try:
            logger.info(f"Starting extraction for {doc.id}")
            _, pages = document_service.extract_text(safe_filename, data)
            logger.info(f"Extraction complete: {len(pages)} pages extracted")
            
            _process_document_pipeline(db, doc, pages)
            logger.info(f"Pipeline complete for {doc.id}")
            
            doc.status = "ready"
        except document_service.ExtractionError as e:
            doc.status = "failed"
            doc.error_message = str(e)
            logger.warning(f"Extraction failed for {doc.id}: {e}")
        except Exception as e:
            doc.status = "failed"
            doc.error_message = f"Unexpected processing error: {e}"
            logger.exception(f"Unexpected error processing document {doc.id}")

        db.commit()
        db.refresh(doc)
        logger.info(f"Document upload complete: {doc.id}, status: {doc.status}")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Top-level error in upload_document")
        raise


def _process_document_pipeline(db: Session, doc: models.Document, pages):
    try:
        full_text = "\n\n".join(t for _, t in pages if t)
        if not full_text.strip():
            raise document_service.ExtractionError("No text content extracted from document.")

        # --- chunking ---
        candidates = chunking_service.chunk_pages(pages)
        if not candidates:
            raise document_service.ExtractionError("Document produced no valid chunks.")

        try:
            vectors = embedding_service.embed_texts([c.text for c in candidates])
            vector_refs = vector_service.add_vectors("chunks", vectors)
        except Exception as e:
            logger.warning(f"Vector storage failed for {doc.id}: {e}, continuing without vector storage")
            vector_refs = [None] * len(candidates)

        chunk_rows = []
        for i, (cand, vref) in enumerate(zip(candidates, vector_refs)):
            chunk = models.Chunk(
                document_id=doc.id, chunk_index=i, text=cand.text,
                page=cand.page, section=cand.section, vector_ref=vref,
            )
            db.add(chunk)
            chunk_rows.append(chunk)
        
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Database flush failed after adding chunks for {doc.id}: {e}")
            db.rollback()
            raise document_service.ExtractionError(f"Database error: {e}")

        # --- claims (per page, so we retain page-level traceability) ---
        all_claims_dicts = []
        for page_num, text in pages:
            if not text.strip():
                continue
            try:
                raw_claims = claim_service.extract_claims(text, page=page_num)
                if not raw_claims:
                    continue
                
                try:
                    claim_vectors = embedding_service.embed_texts([c["statement"] for c in raw_claims])
                    claim_refs = vector_service.add_vectors("claims", claim_vectors)
                except Exception as e:
                    logger.warning(f"Claim vector storage failed for page {page_num} in {doc.id}: {e}")
                    claim_refs = [None] * len(raw_claims)
                
                matching_chunk = next((c for c in chunk_rows if c.page == page_num), chunk_rows[0] if chunk_rows else None)
                for c, vref in zip(raw_claims, claim_refs):
                    claim = models.Claim(
                        document_id=doc.id,
                        chunk_id=matching_chunk.id if matching_chunk else None,
                        topic=c["topic"], original_statement=c["statement"],
                        normalized_statement=c["statement"],
                        requirement_strength=c.get("requirement_strength"),
                        scope=c.get("scope"), importance=c.get("importance", 0.5),
                        page=page_num, vector_ref=vref,
                    )
                    db.add(claim)
                    all_claims_dicts.append({
                        "topic": c["topic"], "normalized_statement": c["statement"],
                        "requirement_strength": c.get("requirement_strength"),
                    })
            except Exception as e:
                logger.warning(f"Claim extraction failed for page {page_num} in {doc.id}: {e}, continuing")
                continue
        
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Database flush failed after adding claims for {doc.id}: {e}")
            db.rollback()
            raise document_service.ExtractionError(f"Database error: {e}")

        # --- summary ---
        try:
            summary = summary_service.summarize_document(full_text)
            doc.short_summary = summary.get("short_summary")
            doc.detailed_summary = summary.get("detailed_summary")
            doc.key_topics = summary.get("key_topics")
            doc.document_type_guess = summary.get("document_type_guess")
        except Exception as e:
            logger.warning(f"Summary generation failed for {doc.id}: {e}, using defaults")
            doc.short_summary = "Summary generation failed"
            doc.detailed_summary = ""
            doc.key_topics = []

        # --- improvement suggestions ---
        try:
            suggestions = recommendation_service.suggest_for_document(full_text, all_claims_dicts)
            for s in suggestions:
                db.add(models.AnalysisResult(
                    target_type="document", target_id=doc.id,
                    category=s["category"], description=s["description"],
                    evidence=s.get("evidence"), location=s.get("location"),
                    confidence=s.get("confidence", 0.5),
                ))
        except Exception as e:
            logger.warning(f"Recommendation generation failed for {doc.id}: {e}, continuing")
        
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Database flush failed after adding results for {doc.id}: {e}")
            db.rollback()
            raise document_service.ExtractionError(f"Database error: {e}")
            
    except document_service.ExtractionError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in _process_document_pipeline for {doc.id}")
        raise document_service.ExtractionError(f"Pipeline processing failed: {e}")


@router.get("", response_model=List[schemas.DocumentOut])
def list_documents(
    group: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    q = db.query(models.Document).filter(models.Document.user_id == user.id)
    if group:
        q = q.filter(models.Document.group == group)
    return q.order_by(models.Document.year.asc().nullslast(), models.Document.created_at.asc()).all()


@router.get("/groups")
def list_groups(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    rows = db.query(models.Document.group).filter(
        models.Document.user_id == user.id
    ).distinct().all()
    return sorted({r[0] for r in rows})


@router.get("/stats/summary")
def documents_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    total_documents = db.query(models.Document).filter(models.Document.user_id == user.id).count()
    total_groups = db.query(models.Document.group).filter(models.Document.user_id == user.id).distinct().count()
    total_claims = db.query(models.Claim).join(models.Document).filter(models.Document.user_id == user.id).count()
    total_changes = db.query(models.Change).filter(models.Change.group.in_(
        db.query(models.Document.group).filter(models.Document.user_id == user.id)
    )).count()
    failed = db.query(models.Document).filter(
        models.Document.user_id == user.id,
        models.Document.status == "failed"
    ).count()
    return {
        "total_documents": total_documents,
        "total_groups": total_groups,
        "total_claims": total_claims,
        "total_changes": total_changes,
        "failed_documents": failed,
    }


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{document_id}/claims", response_model=List[schemas.ClaimOut])
def get_document_claims(
    document_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return db.query(models.Claim).filter(models.Claim.document_id == document_id).all()


@router.get("/{document_id}/suggestions", response_model=List[schemas.SuggestionOut])
def get_document_suggestions(
    document_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    rows = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.target_type == "document",
        models.AnalysisResult.target_id == document_id,
    ).all()
    return [schemas.SuggestionOut(
        category=r.category, description=r.description, evidence=r.evidence,
        location=r.location, confidence=r.confidence,
    ) for r in rows]


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    db.query(models.AnalysisResult).filter(
        models.AnalysisResult.target_type == "document", models.AnalysisResult.target_id == document_id
    ).delete()
    db.delete(doc)
    db.commit()
    return {"deleted": True}
