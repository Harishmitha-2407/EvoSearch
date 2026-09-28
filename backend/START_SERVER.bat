@echo off
echo.
echo ========================================
echo Starting EVOSearch Backend Server
echo ========================================
echo.

REM Check if venv is activated
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate.bat
    pause
    exit /b 1
)

REM Activate venv and start server
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Starting uvicorn server on http://localhost:8000
echo API Docs available at http://localhost:8000/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
