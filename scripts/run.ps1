# One-command launch for AOST Tamil on native Windows.
#     powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
# Opens the API and the web app in their own windows, then your browser.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "gemma2:9b" }

# Make sure Ollama is running.
try { Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null }
catch {
    Write-Host "Starting Ollama..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 5
}

# Confirm the model is present.
$tags = Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 5
if (-not ($tags.models.name -match [regex]::Escape(($model -split ":")[0]))) {
    throw "Model '$model' is not pulled. Run scripts\setup.ps1 (or: ollama pull $model)."
}

# Start the API in its own window.
$api = @"
`$env:TRANSLITERATE_BACKEND='ollama'; `$env:OCR_BACKEND='tesseract'; `$env:OLLAMA_MODEL='$model'
uv run uvicorn --app-dir apps/api/src tamil_edu_api.main:app --port 8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $api

# Start the web app in its own window.
Start-Process powershell -ArgumentList "-NoExit", "-Command", "pnpm --filter web dev"

Write-Host "`nStarting... the first translation takes ~15-30s while the model loads." -ForegroundColor Yellow
Start-Sleep 10
Start-Process "http://localhost:3000"
Write-Host "Open http://localhost:3000  (close the two PowerShell windows to stop)" -ForegroundColor Green
