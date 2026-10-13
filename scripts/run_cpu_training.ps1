param([int]$TestProcessId = 0)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$logDirectory = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$env:HF_HUB_OFFLINE = '1'
if ($TestProcessId -gt 0) {
    Wait-Process -Id $TestProcessId -ErrorAction SilentlyContinue
} else {
    & $pythonPath -u scripts/train_model.py --device cpu --threads 4 --max-length 32 --max-steps 1 --eval-examples 1 --output .venv/models/phi3-cpu-test
    if ($LASTEXITCODE -ne 0) { throw 'CPU verification failed; full training was not started.' }
}
$metricsPath = Join-Path $projectRoot '.venv\models\phi3-cpu-test\training_metrics.json'
if (-not (Test-Path -LiteralPath $metricsPath)) { throw 'CPU verification did not save its metrics; full training was not started.' }
$metrics = Get-Content -LiteralPath $metricsPath -Raw | ConvertFrom-Json
if ($metrics.steps -lt 1) { throw 'CPU verification did not complete a training step.' }
& $pythonPath -u scripts/train_model.py --device cpu --threads 4 --max-length 128 --eval-examples 4 1> logs/cpu-training.log 2> logs/cpu-training-errors.log
if ($LASTEXITCODE -ne 0) { throw 'CPU training failed; inspect logs/cpu-training-errors.log.' }
