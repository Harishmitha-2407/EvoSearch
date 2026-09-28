from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from app.dependencies import get_db
from app import models

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/{group}")
def get_timeline(group: str, db: Session = Depends(get_db)):
    """Per-topic evolution timeline showing documents in chronological order with their claims."""
    # Get all documents in the group, sorted by year/date
    docs = db.query(models.Document).filter(models.Document.group == group).order_by(
        models.Document.year.asc().nullslast(), 
        models.Document.created_at.asc()
    ).all()
    
    if not docs:
        return []
    
    # Build a list of documents with their claims
    timeline_events = []
    for doc in docs:
        claims = db.query(models.Claim).filter(models.Claim.document_id == doc.id).all()
        
        for claim in claims:
            timeline_events.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "year": doc.year,
                "version_label": doc.version_label,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "topic": claim.topic,
                "statement": claim.normalized_statement or claim.original_statement,
                "importance": claim.importance,
                "page": claim.page,
                "requirement_strength": claim.requirement_strength,
            })
    
    # Group by topic
    by_topic = defaultdict(list)
    for event in timeline_events:
        by_topic[event["topic"]].append(event)
    
    # Format for frontend
    timeline = []
    for topic, events in by_topic.items():
        # Sort events by date
        events_sorted = sorted(events, key=lambda e: (e["year"] is None, e["year"] or 0, e["created_at"] or ""))
        timeline.append({
            "topic": topic, 
            "events": events_sorted,
            "document_count": len(set(e["document_id"] for e in events))
        })
    
    timeline.sort(key=lambda t: t["topic"])
    return timeline


@router.get("/{group}/knowledge-map")
def knowledge_map(group: str, db: Session = Depends(get_db)):
    """A simplified topic <-> document graph: each topic node connects to
    every document version that contains a claim about it. Kept intentionally
    readable rather than exhaustive, per spec section 15."""
    docs = db.query(models.Document).filter(models.Document.group == group).all()
    doc_ids = [d.id for d in docs]
    claims = db.query(models.Claim).filter(models.Claim.document_id.in_(doc_ids)).all() if doc_ids else []

    topics = sorted({c.topic for c in claims})
    nodes = (
        [{"id": f"topic:{t}", "label": t, "type": "topic"} for t in topics] +
        [{"id": f"doc:{d.id}", "label": f"{d.filename} ({d.version_label or d.year or ''})", "type": "document"} for d in docs]
    )

    edges = []
    seen = set()
    for c in claims:
        key = (c.topic, c.document_id)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"source": f"topic:{c.topic}", "target": f"doc:{c.document_id}"})

    return {"group": group, "nodes": nodes, "edges": edges}
