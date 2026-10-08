@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if exist "..\venv\Scripts\python.exe" set "PYTHON=..\venv\Scripts\python.exe"
echo Starting CareerMatch AI at http://127.0.0.1:8000 ...
%PYTHON% -c "import fastapi, uvicorn, pydantic, httpx, pypdf, docx, dotenv" >nul 2>&1
if errorlevel 1 %PYTHON% -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1
cd backend
%PYTHON% -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
