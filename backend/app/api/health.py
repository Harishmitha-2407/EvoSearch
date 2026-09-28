from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.services import llm_service, vector_service
from app.config import settings
from app.schemas import HealthOut

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    try:
        stats = vector_service.stats("chunks")
        vector_status = f"ok ({stats['count']} vectors)"
    except Exception:
        vector_status = "error"

    return HealthOut(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        vector_store=vector_status,
        llm_provider="groq (configured)" if llm_service.is_available() else "not configured - heuristic mode",
        embedding_model=settings.EMBEDDING_MODEL,
    )
