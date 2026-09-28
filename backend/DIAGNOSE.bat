@echo off
echo.
echo ========================================
echo EVOSearch Backend Diagnostics
echo ========================================
echo.

REM Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

echo [1/6] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo [2/6] Checking dependencies...
pip list | find "fastapi" >nul
if %errorlevel% neq 0 (
    echo ERROR: FastAPI not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)
echo OK: Dependencies installed

echo.
echo [3/6] Testing config import...
python -c "from app.config import settings; print('OK: Config loaded - APP_NAME=%s' % settings.APP_NAME)" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Config import failed!
    pause
    exit /b 1
)

echo.
echo [4/6] Testing database import...
python -c "from app.database import engine, Base; print('OK: Database engine created')" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Database import failed!
    pause
    exit /b 1
)

echo.
echo [5/6] Testing models import...
python -c "from app.models import User; print('OK: Models loaded')" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Models import failed!
    pause
    exit /b 1
)

echo.
echo [6/6] Testing main app import...
python -c "from app.main import app; print('OK: App loaded with %d routes' % len(app.routes))" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Main app import failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ALL DIAGNOSTICS PASSED!
echo ========================================
echo.
echo The backend is ready to start. Run: START_SERVER.bat
echo.
pause
