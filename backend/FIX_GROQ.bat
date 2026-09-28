@echo off
REM Fix Groq and httpx compatibility

echo Installing compatible versions...
pip install --upgrade httpx
pip install --upgrade groq

echo.
echo Done! Now run:
echo python test_groq_direct.py
pause
