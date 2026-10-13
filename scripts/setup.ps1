$ErrorActionPreference = "Stop"
Write-Host "Setting up EGSPEC AI Chatbot..." -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

$dirs = @("data", "vector_db", "models", "logs", "frontend\assets", "src\monitor")
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "1. Put official PDFs/TXT/HTML/MD files inside data\"
Write-Host "2. Run: python scripts\ingest_documents.py"
Write-Host "3. Run: python scripts\download_model.py"
Write-Host "4. Run everything: python main.py"
