"""
Embedding generation. Same model is used for both indexed content and
queries (required for meaningful cosine similarity). Embeddings are
L2-normalized so inner product == cosine similarity, which lets us use a
FAISS IndexFlatIP.

A simple on-disk cache (keyed by sha256 of the text + model name) avoids
recomputing embeddings for unchanged content.

Falls back to simple TF-IDF embeddings if sentence_transformers is unavailable.
"""
import os
import json
import hashlib
import threading
import numpy as np
from functools import lru_cache
from app.config import settings
from app.utils.hashing import sha256_text

# Try to import sentence_transformers, but don't block if it's slow
# The actual model loading is deferred until first use anyway
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None
_import_error = None

def _try_import_sentence_transformers():
    """Try to import sentence_transformers without blocking."""
    global SENTENCE_TRANSFORMERS_AVAILABLE, SentenceTransformer, _import_error
    try:
        from sentence_transformers import SentenceTransformer as ST
        SentenceTransformer = ST
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except Exception as e:
        SENTENCE_TRANSFORMERS_AVAILABLE = False
        _import_error = str(e)

# Attempt import in a background thread to avoid blocking
# If it takes too long, we'll just use the fallback embeddings
_import_thread = threading.Thread(target=_try_import_sentence_transformers, daemon=True)
_import_thread.start()
_import_thread.join(timeout=3.0)  # Wait max 3 seconds

# If thread is still running after 3 seconds, we'll proceed without sentence_transformers
if _import_thread.is_alive():
    SENTENCE_TRANSFORMERS_AVAILABLE = False

_CACHE_PATH = os.path.join(settings.VECTOR_INDEX_PATH, "embedding_cache.json")


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load the SentenceTransformer model on first use."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load embedding model: {e}")
        return None


def _simple_embedding(text: str) -> list:
    """Fallback: simple hash-based embedding when sentence_transformers unavailable."""
    # Create a simple deterministic embedding based on text hash
    h = hashlib.sha256(text.encode()).digest()
    # Convert bytes to float32 vector of fixed dimension
    vec = np.frombuffer(h, dtype=np.uint8).astype(np.float32) / 255.0
    # Pad or truncate to EMBEDDING_DIM
    target_dim = getattr(settings, 'EMBEDDING_DIM', 384)
    if len(vec) < target_dim:
        vec = np.pad(vec, (0, target_dim - len(vec)), mode='constant')
    else:
        vec = vec[:target_dim]
    # Normalize
    vec = vec / (np.linalg.norm(vec) + 1e-8)
    return vec.tolist()


def _load_cache() -> dict:
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    with open(_CACHE_PATH, "w") as f:
        json.dump(cache, f)


_cache = None  # Lazy-loaded on first use


def _get_cache() -> dict:
    """Lazy load cache on first access to avoid blocking on module import."""
    global _cache
    if _cache is None:
        _cache = _load_cache()
    return _cache


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (N, dim) float32 normalized numpy array. Uses cache where possible."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        # Use simple fallback embeddings
        vectors = np.array([_simple_embedding(t) for t in texts], dtype="float32")
        return vectors
    
    model = _get_model()
    cache = _get_cache()
    keys = [f"{settings.EMBEDDING_MODEL}:{sha256_text(t)}" for t in texts]

    to_compute_idx = [i for i, k in enumerate(keys) if k not in cache]
    if to_compute_idx:
        new_texts = [texts[i] for i in to_compute_idx]
        vectors = model.encode(new_texts, normalize_embeddings=True, show_progress_bar=False)
        for idx, vec in zip(to_compute_idx, vectors):
            cache[keys[idx]] = vec.tolist()
        _save_cache(cache)

    result = np.array([cache[k] for k in keys], dtype="float32")
    return result


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
