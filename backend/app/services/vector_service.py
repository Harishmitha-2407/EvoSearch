"""
Vector storage with in-memory fallback when FAISS is unavailable.
We keep one index per "namespace" (currently: 'chunks' and 'code_entities').
"""
import os
import threading
import numpy as np
from app.config import settings

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

_lock = threading.Lock()
_indices: dict[str, any] = {}
_in_memory_vectors: dict[str, list] = {}  # Fallback: store vectors in memory


def _index_path(namespace: str) -> str:
    return os.path.join(settings.VECTOR_INDEX_PATH, f"{namespace}.faiss")


def _get_index(namespace: str):
    if not FAISS_AVAILABLE:
        return None
    if namespace in _indices:
        return _indices[namespace]
    path = _index_path(namespace)
    if os.path.exists(path):
        idx = faiss.read_index(path)
    else:
        idx = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
    _indices[namespace] = idx
    return idx


def _persist(namespace: str):
    if not FAISS_AVAILABLE or namespace not in _indices:
        return
    faiss.write_index(_indices[namespace], _index_path(namespace))


def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two normalized vectors."""
    return float(np.dot(v1, v2))


def add_vectors(namespace: str, vectors: np.ndarray) -> list[int]:
    """Adds vectors, returns their integer positions (vector_ref values)."""
    with _lock:
        if not FAISS_AVAILABLE:
            # Fallback: store in memory
            if namespace not in _in_memory_vectors:
                _in_memory_vectors[namespace] = []
            start = len(_in_memory_vectors[namespace])
            for vec in vectors:
                _in_memory_vectors[namespace].append(vec.astype("float32").tolist())
            return list(range(start, start + len(vectors)))
        
        idx = _get_index(namespace)
        start = idx.ntotal
        idx.add(vectors.astype("float32"))
        _persist(namespace)
        return list(range(start, start + vectors.shape[0]))


def search(namespace: str, query_vector: np.ndarray, top_k: int = 8):
    """Returns list of (vector_ref, similarity) sorted by similarity desc."""
    if not FAISS_AVAILABLE:
        # Fallback: in-memory search
        if namespace not in _in_memory_vectors or not _in_memory_vectors[namespace]:
            return []
        
        similarities = []
        for i, vec_list in enumerate(_in_memory_vectors[namespace]):
            vec = np.array(vec_list, dtype="float32")
            sim = _cosine_similarity(query_vector.astype("float32"), vec)
            similarities.append((i, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    with _lock:
        idx = _get_index(namespace)
        if idx.ntotal == 0:
            return []
        q = query_vector.reshape(1, -1).astype("float32")
        scores, ids = idx.search(q, min(top_k, idx.ntotal))
        results = []
        for score, vec_id in zip(scores[0], ids[0]):
            if vec_id == -1:
                continue
            results.append((int(vec_id), float(score)))
        return results


def stats(namespace: str) -> dict:
    if not FAISS_AVAILABLE:
        count = len(_in_memory_vectors.get(namespace, []))
        return {"namespace": namespace, "count": count, "dim": settings.EMBEDDING_DIM}
    idx = _get_index(namespace)
    return {"namespace": namespace, "count": idx.ntotal, "dim": idx.d}
