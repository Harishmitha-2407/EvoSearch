#!/usr/bin/env python3
print("[1] Python started", flush=True)

try:
    print("[2] Importing app.config...", flush=True)
    from app.config import settings
    print(f"[3] ✅ Config imported OK: {settings.APP_NAME}", flush=True)
except Exception as e:
    print(f"[3] ❌ Config import failed: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("[4] Done!", flush=True)
