print("Testing individual routers...", flush=True)

try:
    print("1. Importing health...", flush=True)
    from app.api import health
    print("✅ health OK", flush=True)
except Exception as e:
    print(f"❌ health failed: {e}", flush=True)

try:
    print("2. Importing documents...", flush=True)
    from app.api import documents
    print("✅ documents OK", flush=True)
except Exception as e:
    print(f"❌ documents failed: {e}", flush=True)

try:
    print("3. Importing search...", flush=True)
    from app.api import search
    print("✅ search OK", flush=True)
except Exception as e:
    print(f"❌ search failed: {e}", flush=True)

try:
    print("4. Importing chat...", flush=True)
    from app.api import chat
    print("✅ chat OK", flush=True)
except Exception as e:
    print(f"❌ chat failed: {e}", flush=True)

try:
    print("5. Importing comparison...", flush=True)
    from app.api import comparison
    print("✅ comparison OK", flush=True)
except Exception as e:
    print(f"❌ comparison failed: {e}", flush=True)

try:
    print("6. Importing code...", flush=True)
    from app.api import code
    print("✅ code OK", flush=True)
except Exception as e:
    print(f"❌ code failed: {e}", flush=True)

try:
    print("7. Importing timeline...", flush=True)
    from app.api import timeline
    print("✅ timeline OK", flush=True)
except Exception as e:
    print(f"❌ timeline failed: {e}", flush=True)

print("Done!")
