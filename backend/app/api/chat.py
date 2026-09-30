from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app import models
from app.schemas import ChatRequest, ChatResponse, ChatSourceOut
from app.services.retrieval_service import semantic_search
from app.services import llm_service, vector_service
from app.services.embedding_service import embed_query
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])

INSUFFICIENT_EVIDENCE_MSG = "I couldn't find sufficient evidence in the uploaded material to answer that."

SYSTEM_PROMPT = (
    "You are EVOSearch's document and code assistant. Answer the user's question using "
    "ONLY the provided evidence excerpts. Each excerpt is labeled with a source number.\n\n"
    "CRITICAL RULES:\n"
    "1. ONLY use evidence provided - never invent facts, dates, or sources.\n"
    "2. If evidence is insufficient to answer the question, respond: 'I couldn't find sufficient evidence in the uploaded material to answer that.'\n"
    "3. For conceptual questions (e.g., 'what is X?'), provide a clear explanation based on evidence.\n"
    "4. For code questions (e.g., 'explain code line by line'), provide detailed line-by-line breakdown.\n"
    "5. For questions asking 'what is X?', look for docstrings, comments, or contextual clues about what X does.\n"
    "6. Reference sources inline like [1], [2] matching the excerpt numbers.\n"
    "7. Be concise by default; expand only if the question asks for detail.\n\n"
    "Return ONLY valid JSON with keys: answer (string), confidence (0.0-1.0 float), "
    "used_sources (array of integers referencing the excerpt numbers actually used in your answer)."
)


def search_code_entities(db: Session, query: str, user_id: str, top_k: int = 6, code_file_id: str = None):
    """Search code entities using semantic search and metadata filters."""
    query_vec = embed_query(query)
    raw_hits = vector_service.search("code_entities", query_vec, top_k=max(top_k * 6, 40))
    
    results = []
    for vector_ref, score in raw_hits:
        if score < settings.SEARCH_SIMILARITY_THRESHOLD:
            continue
        entity = db.query(models.CodeEntity).filter(models.CodeEntity.vector_ref == vector_ref).first()
        if not entity:
            continue
        code_file = db.query(models.CodeFile).filter(models.CodeFile.id == entity.code_file_id).first()
        if not code_file or code_file.user_id != user_id:
            continue
        if code_file_id and code_file.id != code_file_id:
            continue
        
        # Prioritize source_snippet (full code), then signature, then name
        code_text = entity.source_snippet or entity.signature or f"{entity.entity_type}: {entity.name}"
        
        results.append({
            "chunk_id": entity.id,
            "document_id": code_file.id,
            "document_filename": code_file.filename,
            "text": code_text,
            "similarity": round(score, 4),
            "page": None,
            "section": entity.name,
            "group": code_file.group,
            "year": None,
        })
        if len(results) >= top_k:
            break
    
    return results


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
        
        # Always search code entities - they can provide context/examples too
        code_hits = search_code_entities(db, req.question, user.id, top_k=6, code_file_id=req.document_id)
        
        # Combine and rank by similarity
        all_hits = hits + code_hits
        all_hits = sorted(all_hits, key=lambda x: x['similarity'], reverse=True)[:6]

        if not all_hits:
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
            for i, h in enumerate(all_hits)
        )

        answer_text = None
        confidence = 0.5
        used_indices = list(range(len(all_hits)))

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
                    used_indices = [i - 1 for i in used if isinstance(i, int) and 1 <= i <= len(all_hits)]

        if answer_text is None:
            top = all_hits[0]
            page_suffix = f", page {top['page']}" if top['page'] else ""
            section_suffix = f" ({top['section']})" if top['section'] else ""
            
            # Create a better fallback based on question type
            if "what is" in req.question.lower() or "explain" in req.question.lower():
                answer_text = (
                    f"Based on the code from '{top['document_filename']}'{section_suffix}{page_suffix}:\n\n"
                    f"{top['text']}\n\n"
                    f"This shows the implementation of {top['section']}."
                )
            else:
                answer_text = (
                    f"Based on the most relevant excerpt from '{top['document_filename']}'"
                    f"{section_suffix}{page_suffix}:\n{top['text'][:500]}"
                )
            confidence = round(min(0.6, top["similarity"]), 3)
            used_indices = [0]

        sources = [
            ChatSourceOut(
                document_id=all_hits[i]["document_id"],
                document_filename=all_hits[i]["document_filename"],
                chunk_id=all_hits[i]["chunk_id"],
                page=all_hits[i]["page"],
                similarity=all_hits[i]["similarity"],
            )
            for i in used_indices if 0 <= i < len(all_hits)
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
