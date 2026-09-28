print("Testing main app import...", flush=True)

print("Importing main...", flush=True)
from app.main import app
print("✅ Main app imported successfully!", flush=True)

print("App created with", len(app.routes), "routes", flush=True)
