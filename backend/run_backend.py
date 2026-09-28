#!/usr/bin/env python3
"""
Simple backend startup script for EVOSearch.
This script starts the FastAPI server on port 8000.
"""

import sys
import subprocess

def main():
    print("\n" + "=" * 60)
    print("  EVOSearch Backend Server")
    print("=" * 60 + "\n")
    
    print("Checking dependencies...")
    try:
        import uvicorn
        print("✅ uvicorn found\n")
    except ImportError:
        print("❌ uvicorn not found!")
        print("Please install dependencies: pip install -r requirements.txt\n")
        return 1
    
    print("Starting server on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Shutdown: Press Ctrl+C\n")
    print("=" * 60 + "\n")
    
    try:
        # Run uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
