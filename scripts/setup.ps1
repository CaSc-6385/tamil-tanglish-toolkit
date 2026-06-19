# One-command native-Windows setup for AOST Tamil.
# Run from the project folder in PowerShell:
#     powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
# It installs Ollama + the model + Tesseract + uv/Node/pnpm + all deps, and — unlike
# doing it by hand — REFRESHES PATH after each install so you never hit "not recognized".

$ErrorActionPreference = "Stop"

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "User")
}
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Say($m) { Write-Host "`n> $m" -ForegroundColor Yellow }
function Ok($m) { Write-Host "  OK: $m" -ForegroundColor Green }

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "gemma2:9b" }

if (-not (Have "winget")) {
    throw "winget not found. Install 'App Installer' from the Microsoft Store, then re-run."
}
function Winstall($id) {
    winget install -e --id $id --accept-package-agreements --accept-source-agreements
    Refresh-Path
}

Say "Git";        if (Have "git") { Ok "present" }      else { Winstall "Git.Git" }
Say "Ollama";     if (Have "ollama") { Ok "present" }   else { Winstall "Ollama.Ollama" }
Say "uv";         if (Have "uv") { Ok "present" }       else { Winstall "astral-sh.uv" }
Say "Node.js";    if (Have "node") { Ok "present" }     else { Winstall "OpenJS.NodeJS.LTS" }
Say "pnpm";       if (Have "pnpm") { Ok "present" }     else { npm install -g pnpm; Refresh-Path }

Say "Tesseract (OCR, optional)"
if (Have "tesseract") { Ok "present" } else {
    Winstall "UB-Mannheim.TesseractOCR"
    $tessDir = "C:\Program Files\Tesseract-OCR"
    if (Test-Path $tessDir) { $env:Path += ";$tessDir" }
}

Say "Starting Ollama and pulling model: $model (~5.4 GB, one time)"
try { Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null }
catch { Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden; Start-Sleep 5 }
ollama pull $model

Say "Python dependencies (uv sync)";  uv sync --all-extras
Say "Web dependencies (pnpm install)"; pnpm install

Write-Host "`nSetup complete. Now run:  powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1" -ForegroundColor Green
