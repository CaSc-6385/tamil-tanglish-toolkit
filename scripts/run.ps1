# One-command launch for AOST Tamil on native Windows.
#     powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
# Opens the API and the web app in their own windows, then your browser.

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

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

# Start the API in its own window. Each window explicitly cd's to the project root —
# Start-Process does NOT reliably inherit the current folder on Windows, and starting
# in the wrong folder is a common cause of "localhost refused to connect" (the server
# never finds the workspace and exits).
$api = @"
Set-Location '$root'
`$env:TRANSLITERATE_BACKEND='ollama'; `$env:OCR_BACKEND='tesseract'; `$env:OLLAMA_MODEL='$model'
uv run uvicorn --app-dir apps/api/src tamil_edu_api.main:app --port 8000
"@
Start-Process powershell -WorkingDirectory $root -ArgumentList "-NoExit", "-Command", $api

# Start the web app in its own window.
$web = "Set-Location '$root'; pnpm --filter web dev"
Start-Process powershell -WorkingDirectory $root -ArgumentList "-NoExit", "-Command", $web

# Wait until the web server is actually accepting connections before opening the
# browser. Next.js's first compile on Windows can take 20-40s, and opening too early
# is what causes "localhost refused to connect".
function Wait-Port($port, $timeoutSec) {
    for ($i = 0; $i -lt $timeoutSec; $i++) {
        try {
            $c = New-Object Net.Sockets.TcpClient
            $c.Connect("localhost", $port); $c.Close(); return $true
        }
        catch { Start-Sleep 1 }
    }
    return $false
}

Write-Host "`nStarting servers... (first compile can take 20-40s on Windows)" -ForegroundColor Yellow
if (Wait-Port 3000 120) {
    Start-Process "http://localhost:3000"
    Write-Host "Open http://localhost:3000  (close the two PowerShell windows to stop)" -ForegroundColor Green
}
else {
    Write-Host "Web server didn't come up within 2 min. Check 'Window B' (pnpm dev) for errors," -ForegroundColor Red
    Write-Host "then open http://localhost:3000 manually once it says 'Ready'." -ForegroundColor Red
}
Write-Host "Note: the first translation also takes ~15-30s while the model loads." -ForegroundColor Yellow
