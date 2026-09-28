import sys
print("Testing imports step by step...", flush=True)

print("1. Config...", flush=True)
from app.config import settings
print("✅ Config", flush=True)

print("2. Database...", flush=True)
from app.database import SessionLocal
print("✅ Database", flush=True)

print("3. Models...", flush=True)
from app.models import User
print("✅ Models", flush=True)

print("4. Auth API...", flush=True)
from app.api import auth
print("✅ Auth API", flush=True)

print("All imports successful!")
