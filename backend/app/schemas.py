from pydantic import BaseModel
from typing import Optional, List, Any
import datetime as dt


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserOut] = None
    token: Optional[str] = None


class PasswordValidationResponse(BaseModel):
    is_valid: bool
    requirements: dict  # {uppercase: bool, lowercase: bool, number: bool, special: bool, length: bool}


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    group: str
    version_label: Optional[str] = None
    year: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    short_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    key_topics: List[str] = []
    document_type_guess: Optional[str] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


class ClaimOut(BaseModel):
    id: str
    topic: str
    original_statement: str
    normalized_statement: str
    requirement_strength: Optional[str]
    scope: Optional[str]
    importance: float
    page: Optional[int]

    class Config:
        from_attributes = True


class SearchFilter(BaseModel):
    group: Optional[str] = None
    year: Optional[int] = None
    file_type: Optional[str] = None
    document_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    filters: Optional[SearchFilter] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    text: str
    similarity: float
    page: Optional[int] = None
    section: Optional[str] = None
    group: Optional[str] = None
    year: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    insufficient_evidence: bool = False


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    group: Optional[str] = None


class ChatSourceOut(BaseModel):
    document_id: str
    document_filename: str
    chunk_id: str
    page: Optional[int] = None
    similarity: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    confidence: float
    sources: List[ChatSourceOut]
    insufficient_evidence: bool = False


class ChangeOut(BaseModel):
    id: str
    topic: str
    change_type: str
    semantic_change: Optional[str]
    previous_text: Optional[str]
    current_text: Optional[str]
    explanation: Optional[str]
    confidence: float
    from_year: Optional[int]
    to_year: Optional[int]
    from_version_label: Optional[str]
    to_version_label: Optional[str]

    class Config:
        from_attributes = True


class ComparisonRequest(BaseModel):
    document_id_a: str
    document_id_b: str


class TimelineEntry(BaseModel):
    topic: str
    events: List[dict]


class CodeEntityOut(BaseModel):
    id: str
    entity_type: str
    name: str
    parent: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    signature: Optional[str]
    docstring: Optional[str]

    class Config:
        from_attributes = True


class CodeFileOut(BaseModel):
    id: str
    filename: str
    language: str
    group: str
    version_label: Optional[str]
    status: str
    error_message: Optional[str] = None
    entities: List[CodeEntityOut] = []

    class Config:
        from_attributes = True


class CodeCompareRequest(BaseModel):
    from_file_id: str
    to_file_id: str


class CodeChangeOut(BaseModel):
    id: str
    change_type: str
    entity_name: str
    entity_type: Optional[str]
    previous_code: Optional[str]
    current_code: Optional[str]
    explanation: Optional[str]
    category: Optional[str]
    confidence: float

    class Config:
        from_attributes = True


class ImpactOut(BaseModel):
    entity_name: str
    referencing_files: List[dict]
    note: str


class SuggestionOut(BaseModel):
    category: str
    description: str
    evidence: Optional[str]
    location: Optional[str]
    confidence: float


class HealthOut(BaseModel):
    status: str
    database: str
    vector_store: str
    llm_provider: str
    embedding_model: str
