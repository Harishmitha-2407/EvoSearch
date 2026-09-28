#!/usr/bin/env python3
print("[1] Starting...", flush=True)

print("[2] Importing sentence_transformers check...", flush=True)
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers is available", flush=True)
except ImportError:
    print("❌ sentence_transformers not available (this is OK)", flush=True)

print("[3] Done!", flush=True)
