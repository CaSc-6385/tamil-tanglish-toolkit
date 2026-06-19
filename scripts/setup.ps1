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
# zstd: Ollama's model layers are zstd-compressed; without it `ollama pull`
# extraction can fail on a clean Windows box ("program not found"). Install first.
Say "zstd";       if (Have "zstd") { Ok "present" }      else { Winstall "Facebook.Zstandard" }
Say "Ollama";     if (Have "ollama") { Ok "present" }   else { Winstall "Ollama.Ollama" }
Say "uv";         if (Have "uv") { Ok "present" }       else { Winstall "astral-sh.uv" }
Say "Node.js 20+"
$nodeOk = $false
if (Have "node") {
    $maj = [int]((node --version) -replace 'v(\d+).*', '$1')
    if ($maj -ge 20) { Ok "present ($(node --version))"; $nodeOk = $true }
    else { Write-Host "  Node $(node --version) is too old (need 20+) — installing LTS" -ForegroundColor Yellow }
}
if (-not $nodeOk) { Winstall "OpenJS.NodeJS.LTS" }

# pnpm via corepack (bundled with Node), pinned to the repo's pnpm@9.12.0. This avoids
# `npm install -g pnpm` pulling a "latest" pnpm that's too new for your Node and crashes
# on every run — the usual cause of the web server never starting.
Say "pnpm 9.12.0 (via corepack)"
corepack enable
corepack prepare pnpm@9.12.0 --activate
Refresh-Path
Ok "pnpm $(pnpm --version)"

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
