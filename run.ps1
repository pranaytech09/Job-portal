$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$python = "python"
if (Test-Path ".venv\Scripts\python.exe") { $python = ".venv\Scripts\python.exe" }
elseif (Test-Path "..\venv\Scripts\python.exe") { $python = "..\venv\Scripts\python.exe" }
Write-Host "Starting CareerMatch AI at http://127.0.0.1:8000 ..." -ForegroundColor Green
& $python -c "import fastapi, uvicorn, pydantic, httpx, pypdf, docx, dotenv" 2>$null
if ($LASTEXITCODE -ne 0) { & $python -m pip install -r "backend\requirements.txt" }
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
Set-Location -Path "$PSScriptRoot\backend"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
