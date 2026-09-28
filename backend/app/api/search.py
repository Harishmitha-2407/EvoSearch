from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app import models
from app.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.services.retrieval_service import semantic_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(req: SearchRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    filters = req.filters.model_dump() if req.filters else {}
    filters['user_id'] = user.id  # Add user filter
    results = semantic_search(db, req.query, top_k=req.top_k, filters=filters)
    return SearchResponse(
        query=req.query,
        results=[SearchResultItem(**r) for r in results],
        insufficient_evidence=len(results) == 0,
    )
