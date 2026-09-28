from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app import models
from app.schemas import ChatRequest, ChatResponse, ChatSourceOut
from app.services.retrieval_service import semantic_search
from app.services import llm_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

INSUFFICIENT_EVIDENCE_MSG = "I couldn't find sufficient evidence in the uploaded material to answer that."

SYSTEM_PROMPT = (
    "You are EVOSearch's document assistant. Answer the user's question using "
    "ONLY the provided evidence excerpts. Each excerpt is labeled with a "
    "source number. Rules:\n"
    "1. Never invent facts, dates, page numbers, or sources not in the evidence.\n"
    "2. If the evidence is insufficient or doesn't address the question, say so plainly.\n"
    "3. Clearly distinguish evidence from your own interpretation.\n"
    "4. Reference sources inline like [1], [2] matching the excerpt numbers.\n"
    "5. Be concise by default; expand only if the question asks for detail.\n"
    "Return ONLY JSON with keys: answer (string), confidence (0.0-1.0 float), "
    "used_sources (array of integers referencing the excerpt numbers actually used)."
)


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    try:
        if req.session_id:
            session = db.query(models.ChatSession).filter(
                models.ChatSession.id == req.session_id,
                models.ChatSession.user_id == user.id
            ).first()
            if not session:
                raise HTTPException(404, "Chat session not found")
        else:
            session = models.ChatSession(
                user_id=user.id,
                title=req.question[:80], 
                scope_group=req.group, 
                scope_document_id=req.document_id,
            )
            db.add(session)
            db.flush()

        # Add user message
        db.add(models.ChatMessage(
            session_id=session.id,
            role="user",
            content=req.question,
        ))
        db.flush()

        filters = {}
        if req.document_id:
            filters["document_id"] = req.document_id
        if req.group:
            filters["group"] = req.group
        filters["user_id"] = user.id

        hits = semantic_search(db, req.question, top_k=6, filters=filters)

        if not hits:
            db.add(models.ChatMessage(
                session_id=session.id,
                role="assistant",
                content=INSUFFICIENT_EVIDENCE_MSG,
                sources=[],
                confidence=0.0,
            ))
            db.commit()
            return ChatResponse(
                session_id=session.id,
                answer=INSUFFICIENT_EVIDENCE_MSG,
                confidence=0.0,
                sources=[],
                insufficient_evidence=True,
            )

        excerpt_block = "\n\n".join(
            f"[{i+1}] (document: {h['document_filename']}, page: {h['page']})\n{h['text']}"
            for i, h in enumerate(hits)
        )

        answer_text = None
        confidence = 0.5
        used_indices = list(range(len(hits)))

        if llm_service.is_available():
            result = llm_service.call_structured(
                SYSTEM_PROMPT,
                f"Question: {req.question}\n\nEvidence:\n{excerpt_block}",
                max_tokens=900,
            )
            if isinstance(result, dict) and "answer" in result:
                answer_text = result["answer"]
                confidence = float(result.get("confidence", 0.6))
                used = result.get("used_sources")
                if isinstance(used, list) and used:
                    used_indices = [i - 1 for i in used if isinstance(i, int) and 1 <= i <= len(hits)]

        if answer_text is None:
            top = hits[0]
            page_suffix = f", page {top['page']}" if top['page'] else ""
            answer_text = (
                f"Based on the most relevant excerpt (from '{top['document_filename']}'"
                f"{page_suffix}): {top['text'][:500]}"
            )
            confidence = round(min(0.6, top["similarity"]), 3)
            used_indices = [0]

        sources = [
            ChatSourceOut(
                document_id=hits[i]["document_id"],
                document_filename=hits[i]["document_filename"],
                chunk_id=hits[i]["chunk_id"],
                page=hits[i]["page"],
                similarity=hits[i]["similarity"],
            )
            for i in used_indices if 0 <= i < len(hits)
        ]

        db.add(models.ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer_text,
            sources=[s.model_dump() for s in sources],
            confidence=confidence,
        ))
        db.commit()

        return ChatResponse(
            session_id=session.id,
            answer=answer_text,
            confidence=confidence,
            sources=sources,
            insufficient_evidence=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Chat error: {str(e)}")


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "confidence": m.confidence,
            "created_at": m.created_at,
        }
        for m in session.messages
    ]


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == user.id
    ).order_by(models.ChatSession.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at,
        }
        for s in sessions
    ]
