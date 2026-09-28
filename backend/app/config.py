"""
Central configuration for EVOSearch backend.
All values are overridable via environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    APP_NAME: str = "EVOSearch"
    ENV: str = Field(default="development")

    DATABASE_URL: str = Field(default="sqlite:///./data/evosearch.db")

    STORAGE_PATH: str = Field(default="./data/uploads")
    VECTOR_INDEX_PATH: str = Field(default="./data/vector_index")

    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = Field(default=384)

    # Optional. If unset, EVOSearch runs in "heuristic mode" for claim
    # extraction / summaries / explanations / chat instead of calling an LLM.
    ANTHROPIC_API_KEY: str = Field(default="")
    GROQ_API_KEY: str = Field(default="")
    LLM_PROVIDER: str = Field(default="anthropic")
    LLM_MODEL: str = Field(default="llama-3.1-70b-versatile")

    CHUNK_SIZE_TOKENS: int = Field(default=220)
    CHUNK_OVERLAP_TOKENS: int = Field(default=40)

    SEARCH_SIMILARITY_THRESHOLD: float = Field(default=0.25)
    CLAIM_ALIGNMENT_THRESHOLD: float = Field(default=0.55)

    MAX_UPLOAD_MB: int = Field(default=25)

    SECRET_KEY: str = Field(default="dev-secret-change-me")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Create necessary directories
try:
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.VECTOR_INDEX_PATH, exist_ok=True)
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_path:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")
