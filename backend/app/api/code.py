from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.dependencies import get_db, get_current_user
from app import models, schemas
from app.config import settings
from app.utils.hashing import sha256_bytes
from app.services import code_analysis_service, embedding_service, vector_service, recommendation_service
from app.services.code_comparison_service import compare_code_files
from app.services.impact_service import find_potential_impact
from app.schemas import CodeCompareRequest, ImpactOut, SuggestionOut

logger = logging.getLogger("evosearch.code")
router = APIRouter(prefix="/api/code", tags=["code"])


@router.post("/upload", response_model=schemas.CodeFileOut)
async def upload_code(
    file: UploadFile = File(...),
    group: str = Form("Ungrouped"),
    version_label: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    try:
        logger.info(f"Code upload started by user {user.id}: {file.filename}")
        
        data = await file.read()
        if len(data) == 0:
            raise HTTPException(400, "Uploaded file is empty")
        if len(data) / (1024 * 1024) > settings.MAX_UPLOAD_MB:
            raise HTTPException(413, f"File exceeds max upload size of {settings.MAX_UPLOAD_MB}MB")

        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ") or "upload"
        language = code_analysis_service.detect_language(safe_filename)
        source_text = data.decode("utf-8", errors="replace")
        logger.info(f"File: {safe_filename}, Language: {language}, Size: {len(data)} bytes")

        code_file = models.CodeFile(
            user_id=user.id,
            filename=safe_filename, language=language, group=group or "Ungrouped",
            version_label=version_label, checksum=sha256_bytes(data),
            raw_text=source_text, status="processing",
        )
        db.add(code_file)
        
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Database flush failed for code file creation: {e}")
            db.rollback()
            raise HTTPException(500, f"Database error: {e}")
            
        logger.info(f"Code file record created: {code_file.id}")

        storage_path = f"{settings.STORAGE_PATH}/{code_file.id}_{safe_filename}"
        try:
            with open(storage_path, "wb") as f:
                f.write(data)
            code_file.storage_path = storage_path
            logger.info(f"File saved to: {storage_path}")
        except Exception as e:
            logger.warning(f"Could not persist code file to disk: {e}")

        try:
            logger.info(f"Starting code analysis for {code_file.id}")
            entities = code_analysis_service.parse_code(safe_filename, source_text)
            logger.info(f"Parsing complete: {len(entities)} entities found")
            
            if entities:
                try:
                    logger.info(f"Embedding {len(entities)} entities")
                    vectors = embedding_service.embed_texts(
                        [e.source_snippet or e.signature or e.name for e in entities]
                    )
                    vector_refs = vector_service.add_vectors("code_entities", vectors)
                except Exception as e:
                    logger.warning(f"Vector storage failed for {code_file.id}: {e}, continuing without vectors")
                    vector_refs = [None] * len(entities)
            else:
                vector_refs = []

            for e, vref in zip(entities, vector_refs or [None] * len(entities)):
                db.add(models.CodeEntity(
                    code_file_id=code_file.id, entity_type=e.entity_type, name=e.name,
                    parent=e.parent, start_line=e.start_line, end_line=e.end_line,
                    signature=e.signature, docstring=e.docstring,
                    source_snippet=e.source_snippet, vector_ref=vref,
                ))

            try:
                db.flush()
            except Exception as e:
                logger.error(f"Database flush failed after adding entities for {code_file.id}: {e}")
                db.rollback()
                raise code_analysis_service.CodeParsingError(f"Database error: {e}")

            logger.info(f"Generating suggestions for {code_file.id}")
            try:
                suggestions = recommendation_service.suggest_for_code(
                    [{"entity_type": e.entity_type, "name": e.name, "signature": e.signature,
                      "docstring": e.docstring, "start_line": e.start_line} for e in entities],
                    source_text,
                )
                for s in suggestions:
                    db.add(models.AnalysisResult(
                        target_type="code", target_id=code_file.id,
                        category=s["category"], description=s["description"],
                        evidence=s.get("evidence"), location=s.get("location"),
                        confidence=s.get("confidence", 0.5),
                    ))
            except Exception as e:
                logger.warning(f"Suggestion generation failed for {code_file.id}: {e}, continuing")

            code_file.status = "ready"
            logger.info(f"Code analysis complete for {code_file.id}")
        except code_analysis_service.CodeParsingError as e:
            code_file.status = "ready"
            code_file.error_message = f"Structured parsing failed, stored as plain text: {e}"
            logger.warning(f"Code parsing error for {code_file.id}: {e}")
        except Exception as e:
            code_file.status = "failed"
            code_file.error_message = f"Unexpected processing error: {e}"
            logger.exception(f"Unexpected error processing code file {code_file.id}")

        try:
            db.commit()
        except Exception as e:
            logger.error(f"Database commit failed for code file {code_file.id}: {e}")
            db.rollback()
            raise HTTPException(500, f"Database error: {e}")
            
        db.refresh(code_file)
        logger.info(f"Code upload complete: {code_file.id}, status: {code_file.status}")
        return code_file
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Top-level error in upload_code")
        raise HTTPException(500, "Code upload failed")


@router.get("/files", response_model=List[schemas.CodeFileOut])
def list_code_files(
    group: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    q = db.query(models.CodeFile).filter(models.CodeFile.user_id == user.id)
    if group:
        q = q.filter(models.CodeFile.group == group)
    return q.order_by(models.CodeFile.created_at.asc()).all()


@router.get("/groups")
def list_code_groups(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    rows = db.query(models.CodeFile.group).filter(
        models.CodeFile.user_id == user.id
    ).distinct().all()
    return sorted({r[0] for r in rows})


@router.get("/stats/summary")
def code_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    total_files = db.query(models.CodeFile).filter(models.CodeFile.user_id == user.id).count()
    total_entities = db.query(models.CodeEntity).join(models.CodeFile).filter(
        models.CodeFile.user_id == user.id
    ).count()
    total_changes = db.query(models.CodeChange).filter(
        models.CodeChange.group.in_(
            db.query(models.CodeFile.group).filter(models.CodeFile.user_id == user.id)
        )
    ).count()
    total_groups = db.query(models.CodeFile.group).filter(
        models.CodeFile.user_id == user.id
    ).distinct().count()
    return {
        "total_files": total_files,
        "total_entities": total_entities,
        "total_changes": total_changes,
        "total_groups": total_groups,
    }


@router.get("/files/{file_id}", response_model=schemas.CodeFileOut)
def get_code_file(
    file_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    f = db.query(models.CodeFile).filter(
        models.CodeFile.id == file_id,
        models.CodeFile.user_id == user.id
    ).first()
    if not f:
        raise HTTPException(404, "Code file not found")
    return f


@router.delete("/files/{file_id}")
def delete_code_file(
    file_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    f = db.query(models.CodeFile).filter(
        models.CodeFile.id == file_id,
        models.CodeFile.user_id == user.id
    ).first()
    if not f:
        raise HTTPException(404, "Code file not found")
    
    # Delete associated entities and changes
    db.query(models.CodeEntity).filter(models.CodeEntity.code_file_id == file_id).delete()
    db.query(models.CodeChange).filter(
        (models.CodeChange.from_file_id == file_id) | (models.CodeChange.to_file_id == file_id)
    ).delete()
    db.query(models.AnalysisResult).filter(
        (models.AnalysisResult.target_type == "code") & (models.AnalysisResult.target_id == file_id)
    ).delete()
    
    # Delete the file itself
    db.delete(f)
    db.commit()
    
    return {"status": "deleted", "id": file_id}


@router.get("/files/{file_id}/suggestions", response_model=List[SuggestionOut])
def get_code_suggestions(
    file_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # Verify ownership
    f = db.query(models.CodeFile).filter(
        models.CodeFile.id == file_id,
        models.CodeFile.user_id == user.id
    ).first()
    if not f:
        raise HTTPException(404, "Code file not found")
    
    rows = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.target_type == "code",
        models.AnalysisResult.target_id == file_id,
    ).all()
    return [SuggestionOut(
        category=r.category, description=r.description, evidence=r.evidence,
        location=r.location, confidence=r.confidence,
    ) for r in rows]


def _entity_to_dict(e: models.CodeEntity) -> dict:
    return {
        "entity_type": e.entity_type, "name": e.name, "parent": e.parent,
        "source_snippet": e.source_snippet, "signature": e.signature,
    }


@router.post("/compare")
def compare_code(
    req: CodeCompareRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    import logging
    logger = logging.getLogger("evosearch.code")
    
    try:
        file_a = db.query(models.CodeFile).filter(
            models.CodeFile.id == req.from_file_id,
            models.CodeFile.user_id == user.id
        ).first()
        file_b = db.query(models.CodeFile).filter(
            models.CodeFile.id == req.to_file_id,
            models.CodeFile.user_id == user.id
        ).first()
        if not file_a or not file_b:
            raise HTTPException(404, "One or both code files not found")

        entities_a = [_entity_to_dict(e) for e in file_a.entities]
        entities_b = [_entity_to_dict(e) for e in file_b.entities]
        
        # Get source text and metadata
        source_a = file_a.raw_text or ""
        source_b = file_b.raw_text or ""

        try:
            comparison_result = compare_code_files(
                entities_a, entities_b, 
                source_a, source_b,
                file_a.filename, file_b.filename,
                file_a.language, file_b.language
            )
            raw_changes = comparison_result["changes"]
        except Exception as e:
            logger.warning(f"Code comparison failed for {file_a.id} vs {file_b.id}: {e}, returning empty changes")
            raw_changes = []
            comparison_result = {
                "changes": [],
                "version_a_summary": "Comparison failed",
                "version_a_explanation": "",
                "version_b_summary": "Comparison failed",
                "version_b_explanation": "",
                "comparison_stats": {},
                "overall_summary": "Code comparison encountered an error"
            }

        try:
            db.query(models.CodeChange).filter(
                models.CodeChange.from_file_id == file_a.id, models.CodeChange.to_file_id == file_b.id
            ).delete()
        except Exception as e:
            logger.warning(f"Failed to delete previous code changes: {e}, continuing")

        stored = []
        for ch in raw_changes:
            row = models.CodeChange(
                group=file_b.group, from_file_id=file_a.id, to_file_id=file_b.id,
                change_type=ch["change_type"], entity_name=ch["entity_name"],
                entity_type=ch["entity_type"], previous_code=ch["previous_code"],
                current_code=ch["current_code"], explanation=ch["explanation"],
                category=ch["category"], confidence=ch["confidence"],
            )
            db.add(row)
            stored.append(row)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Database commit failed for code comparison: {e}")
            db.rollback()
            raise HTTPException(500, f"Database error: {e}")
            
        for row in stored:
            db.refresh(row)

        return {
            "changes": [schemas.CodeChangeOut.model_validate(r) for r in stored],
            "from_file": {
                "id": file_a.id,
                "filename": file_a.filename,
                "version_label": file_a.version_label,
                "language": file_a.language,
                "summary": comparison_result.get("version_a_summary", {}).get("overview", "") if isinstance(comparison_result.get("version_a_summary"), dict) else str(comparison_result.get("version_a_summary", "")),
                "explanation": comparison_result.get("version_a_explanation", "") or file_a.raw_text or ""
            },
            "to_file": {
                "id": file_b.id,
                "filename": file_b.filename,
                "version_label": file_b.version_label,
                "language": file_b.language,
                "summary": comparison_result.get("version_b_summary", {}).get("overview", "") if isinstance(comparison_result.get("version_b_summary"), dict) else str(comparison_result.get("version_b_summary", "")),
                "explanation": comparison_result.get("version_b_explanation", "") or file_b.raw_text or ""
            },
            "comparison_stats": comparison_result.get("comparison_stats", {}),
            "overall_summary": comparison_result.get("overall_summary", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in compare_code")
        raise HTTPException(500, "Code comparison failed")


@router.get("/files/{file_id}/impact/{entity_name}", response_model=ImpactOut)
def get_impact(
    file_id: str,
    entity_name: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    f = db.query(models.CodeFile).filter(
        models.CodeFile.id == file_id,
        models.CodeFile.user_id == user.id
    ).first()
    if not f:
        raise HTTPException(404, "Code file not found")
    referencing, note = find_potential_impact(db, f.group, entity_name, exclude_file_id=file_id)
    return ImpactOut(entity_name=entity_name, referencing_files=referencing, note=note)
