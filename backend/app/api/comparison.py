from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app import models
from app.schemas import ComparisonRequest, ChangeOut
from app.services.comparison_service import compare_claims, evolution_score

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


def _claim_to_dict(c: models.Claim) -> dict:
    return {
        "id": c.id, "topic": c.topic, "normalized_statement": c.normalized_statement,
        "requirement_strength": c.requirement_strength, "scope": c.scope,
    }


@router.post("/documents")
def compare_documents(req: ComparisonRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    import logging
    logger = logging.getLogger("evosearch.comparison")
    
    try:
        doc_a = db.query(models.Document).filter(
            models.Document.id == req.document_id_a,
            models.Document.user_id == user.id  # Add user filter
        ).first()
        doc_b = db.query(models.Document).filter(
            models.Document.id == req.document_id_b,
            models.Document.user_id == user.id  # Add user filter
        ).first()
        if not doc_a or not doc_b:
            raise HTTPException(404, "One or both documents not found")
        if doc_a.status != "ready" or doc_b.status != "ready":
            raise HTTPException(400, "Both documents must finish processing before comparison")

        claims_a = [_claim_to_dict(c) for c in db.query(models.Claim).filter(models.Claim.document_id == doc_a.id)]
        claims_b = [_claim_to_dict(c) for c in db.query(models.Claim).filter(models.Claim.document_id == doc_b.id)]

        try:
            raw_changes = compare_claims(claims_a, claims_b)
        except Exception as e:
            logger.warning(f"Claim comparison failed for {doc_a.id} vs {doc_b.id}: {e}, returning empty changes")
            raw_changes = []

        # Clear any previously stored comparison between exactly this pair to avoid duplicates
        try:
            db.query(models.Change).filter(
                models.Change.group == doc_b.group,
                models.Change.from_version_label == doc_a.version_label,
                models.Change.to_version_label == doc_b.version_label,
            ).delete()
        except Exception as e:
            logger.warning(f"Failed to delete previous changes: {e}, continuing")

        stored = []
        for ch in raw_changes:
            row = models.Change(
                group=doc_b.group, topic=ch["topic"], change_type=ch["change_type"],
                semantic_change=ch["semantic_change"],
                previous_claim_id=ch["previous_claim_id"], current_claim_id=ch["current_claim_id"],
                previous_text=ch["previous_text"], current_text=ch["current_text"],
                explanation=ch["explanation"], confidence=ch["confidence"],
                from_year=doc_a.year, to_year=doc_b.year,
                from_version_label=doc_a.version_label, to_version_label=doc_b.version_label,
            )
            db.add(row)
            stored.append(row)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Database commit failed for comparison: {e}")
            db.rollback()
            raise HTTPException(500, f"Database error: {e}")
            
        for row in stored:
            db.refresh(row)

        try:
            score = evolution_score(raw_changes)
        except Exception as e:
            logger.warning(f"Evolution score calculation failed: {e}, using default")
            score = 0.0

        return {
            "changes": [ChangeOut.model_validate(r) for r in stored],
            "evolution_score": score,
            "document_a": {"id": doc_a.id, "filename": doc_a.filename, "version_label": doc_a.version_label, "year": doc_a.year},
            "document_b": {"id": doc_b.id, "filename": doc_b.filename, "version_label": doc_b.version_label, "year": doc_b.year},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in compare_documents")
        raise HTTPException(500, "Comparison failed")


@router.get("/changes", response_model=List[ChangeOut])
def list_changes(group: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Verify user has documents in this group
    user_has_group = db.query(models.Document).filter(
        models.Document.user_id == user.id,
        models.Document.group == group
    ).first()
    
    if not user_has_group:
        raise HTTPException(403, "You don't have access to this group")
    
    return db.query(models.Change).filter(models.Change.group == group).order_by(
        models.Change.to_year.asc().nullslast()
    ).all()
