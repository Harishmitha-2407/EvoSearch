#!/usr/bin/env python3
import sys
import traceback

print("Python version:", sys.version, flush=True)
print("Testing embedding service import...", flush=True)

try:
    print("Step 1: Import config...", flush=True)
    from app.config import settings
    print("✅ Config OK", flush=True)
    print(f"  VECTOR_INDEX_PATH: {settings.VECTOR_INDEX_PATH}", flush=True)
    
    print("Step 2: Import embedding_service...", flush=True)
    from app.services import embedding_service
    print("✅ Embedding service OK", flush=True)
    
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print("Done!", flush=True)
