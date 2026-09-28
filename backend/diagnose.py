#!/usr/bin/env python3
"""EVOSearch Backend Diagnostics - Verify all imports work correctly."""

import sys
import subprocess

def print_header(text):
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def test_import(step_num, description, import_statement):
    """Test a single import and report status."""
    print(f"[{step_num}] {description}...", end=" ", flush=True)
    try:
        exec(import_statement)
        print("✅ OK")
        return True
    except Exception as e:
        print(f"❌ FAILED")
        print(f"    Error: {str(e)[:100]}")
        return False

def main():
    print_header("EVOSearch Backend Diagnostics")
    
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}\n")
    
    all_passed = True
    
    # Test 1: Config
    all_passed &= test_import(
        1, "Loading configuration",
        "from app.config import settings; assert settings.APP_NAME"
    )
    
    # Test 2: Database
    all_passed &= test_import(
        2, "Creating database engine",
        "from app.database import engine, Base; assert engine"
    )
    
    # Test 3: Models
    all_passed &= test_import(
        3, "Loading ORM models",
        "from app.models import User, Document; assert User"
    )
    
    # Test 4: Services - Auth
    all_passed &= test_import(
        4, "Loading auth service",
        "from app.services import auth_service; assert auth_service"
    )
    
    # Test 5: Services - Embedding (key one that was hanging)
    all_passed &= test_import(
        5, "Loading embedding service (lazy-loaded)",
        "from app.services import embedding_service; assert embedding_service._cache is None"
    )
    
    # Test 6: Services - Vector
    all_passed &= test_import(
        6, "Loading vector service",
        "from app.services import vector_service; assert vector_service"
    )
    
    # Test 7: Services - LLM
    all_passed &= test_import(
        7, "Loading LLM service",
        "from app.services import llm_service; assert llm_service"
    )
    
    # Test 8: API Routes
    all_passed &= test_import(
        8, "Loading auth API routes",
        "from app.api import auth; assert auth.router"
    )
    
    all_passed &= test_import(
        9, "Loading document API routes",
        "from app.api import documents; assert documents.router"
    )
    
    # Test 9: Main App (the big one)
    print(f"[10] Loading main FastAPI application...", end=" ", flush=True)
    try:
        from app.main import app
        num_routes = len(app.routes)
        print(f"✅ OK ({num_routes} routes)")
    except Exception as e:
        print(f"❌ FAILED")
        print(f"    Error: {str(e)[:100]}")
        all_passed = False
    
    # Final result
    print_header("Diagnostics Complete")
    
    if all_passed:
        print("✅ ALL TESTS PASSED!\n")
        print("Your backend is ready to start. Run:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n")
        print("Then access:")
        print("  - API Docs: http://localhost:8000/docs")
        print("  - Frontend: http://localhost:3000\n")
        return 0
    else:
        print("❌ SOME TESTS FAILED\n")
        print("Please fix the errors above before starting the server.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
