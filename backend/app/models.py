"""
Normalized relational models.

Vector embeddings themselves are NOT stored here - they live in the FAISS
index (see services/vector_service.py). Rows here store a `vector_ref`
(an integer position in the FAISS index) so we can go from a FAISS hit
back to its metadata, and vice versa.
"""
import uuid
import datetime as dt
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


# ---------------------------------------------------------------- users

class User(Base):
    """User authentication and account."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)  # stored as lowercase
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    code_files = relationship("CodeFile", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


def gen_id():
    return str(uuid.uuid4())


def now():
    return dt.datetime.utcnow()


# ---------------------------------------------------------------- documents

class Document(Base):
    """A single uploaded file. Multiple Documents can belong to the same
    `group` (e.g. 'Security Policy') representing different versions."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf/docx/txt/md/csv/json/yaml
    size_bytes = Column(Integer, default=0)
    checksum = Column(String, index=True)
    storage_path = Column(String, nullable=False)

    group = Column(String, index=True, default="Ungrouped")
    version_label = Column(String, nullable=True)
    year = Column(Integer, nullable=True)

    status = Column(String, default="pending")  # pending/processing/ready/failed
    error_message = Column(Text, nullable=True)

    short_summary = Column(Text, nullable=True)
    detailed_summary = Column(Text, nullable=True)
    key_topics = Column(JSON, default=list)
    document_type_guess = Column(String, nullable=True)

    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"), index=True)
    chunk_index = Column(Integer)
    text = Column(Text)
    page = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    vector_ref = Column(Integer, nullable=True)  # position in FAISS index
    created_at = Column(DateTime, default=now)

    document = relationship("Document", back_populates="chunks")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"), index=True)
    chunk_id = Column(String, ForeignKey("chunks.id"), nullable=True)

    topic = Column(String, index=True)
    original_statement = Column(Text)
    normalized_statement = Column(Text)
    requirement_strength = Column(String, nullable=True)  # mandatory/recommended/optional/none
    scope = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    page = Column(Integer, nullable=True)
    vector_ref = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=now)

    document = relationship("Document", back_populates="claims")


class Change(Base):
    """A detected change between a claim in an older document/version and a
    claim (or absence of a claim) in a newer one."""
    __tablename__ = "changes"

    id = Column(String, primary_key=True, default=gen_id)
    group = Column(String, index=True)
    topic = Column(String, index=True)

    change_type = Column(String)  # ADDED/REMOVED/MODIFIED/UNCHANGED
    semantic_change = Column(String, nullable=True)  # REQUIREMENT_STRENGTHENED etc.

    previous_claim_id = Column(String, ForeignKey("claims.id"), nullable=True)
    current_claim_id = Column(String, ForeignKey("claims.id"), nullable=True)

    previous_text = Column(Text, nullable=True)
    current_text = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    confidence = Column(Float, default=0.5)

    from_year = Column(Integer, nullable=True)
    to_year = Column(Integer, nullable=True)
    from_version_label = Column(String, nullable=True)
    to_version_label = Column(String, nullable=True)

    created_at = Column(DateTime, default=now)


# ---------------------------------------------------------------------- code

class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    filename = Column(String, nullable=False)
    language = Column(String, nullable=False)
    group = Column(String, index=True, default="Ungrouped")  # e.g. "auth.py" lineage
    version_label = Column(String, nullable=True)
    storage_path = Column(String)
    checksum = Column(String)
    raw_text = Column(Text)
    status = Column(String, default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)

    user = relationship("User", back_populates="code_files")
    entities = relationship("CodeEntity", back_populates="code_file", cascade="all, delete-orphan")


class CodeEntity(Base):
    """A function, class/method, import, or route extracted from a code file."""
    __tablename__ = "code_entities"

    id = Column(String, primary_key=True, default=gen_id)
    code_file_id = Column(String, ForeignKey("code_files.id"), index=True)

    entity_type = Column(String)  # function/class/method/import/route
    name = Column(String, index=True)
    parent = Column(String, nullable=True)  # containing class for methods
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    source_snippet = Column(Text, nullable=True)
    vector_ref = Column(Integer, nullable=True)

    code_file = relationship("CodeFile", back_populates="entities")


class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(String, primary_key=True, default=gen_id)
    group = Column(String, index=True)
    from_file_id = Column(String, ForeignKey("code_files.id"), nullable=True)
    to_file_id = Column(String, ForeignKey("code_files.id"), nullable=True)

    change_type = Column(String)  # ADDED_FUNCTION/REMOVED_FUNCTION/MODIFIED_FUNCTION/...
    entity_name = Column(String, index=True)
    entity_type = Column(String, nullable=True)
    previous_code = Column(Text, nullable=True)
    current_code = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g. security-sensitive
    confidence = Column(Float, default=0.5)

    created_at = Column(DateTime, default=now)


class AnalysisResult(Base):
    """Improvement suggestions for documents or code."""
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=gen_id)
    target_type = Column(String)  # document/code
    target_id = Column(String, index=True)
    category = Column(String)
    description = Column(Text)
    evidence = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=now)


# ---------------------------------------------------------------------- chat

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String, nullable=True)
    scope_group = Column(String, nullable=True)  # optionally restrict to a doc group
    scope_document_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("chat_sessions.id"), index=True)
    role = Column(String)  # user/assistant
    content = Column(Text)
    sources = Column(JSON, default=list)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=now)

    session = relationship("ChatSession", back_populates="messages")
