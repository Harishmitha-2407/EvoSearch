@echo off
REM Start EVOSearch Application
REM This script starts both backend and frontend

echo ================================================
echo Starting EVOSearch Authentication System
echo ================================================

REM Check if running as admin (optional but helpful)
REM Change to backend directory and start backend
cd backend
echo.
echo Starting Backend on http://localhost:8001...
echo.
start cmd /k "venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

REM Wait a moment for backend to start
timeout /t 3

REM Change to frontend directory and start frontend
cd ../frontend
echo.
echo Starting Frontend on http://localhost:5173...
echo.
start cmd /k "npm run dev"

REM Wait for both to start
timeout /t 5

REM Open browser
echo.
echo Opening browser...
timeout /t 2
start http://localhost:5173/signup

echo.
echo ================================================
echo EVOSearch is starting!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8001
echo ================================================
echo.
pause
