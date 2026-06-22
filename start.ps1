# Smart Study Agent - Launcher Script
# Usage: .\start.ps1
# This sets all required env vars and launches the ADK web playground.

param(
    [switch]$RunOnly,
    [string]$Message = ""
)

# ---------------------------------------------------------------
# 1. Load credentials from .env file
# ---------------------------------------------------------------
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#=][^=]*)=(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "Env:\$key" -Value $value
        }
    }
    Write-Host "✅ Loaded credentials from .env" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  .env file not found." -ForegroundColor Yellow
    exit 1
}

# ---------------------------------------------------------------
# 2. Launch playground or run a single query
# ---------------------------------------------------------------
if ($RunOnly -and $Message) {
    Write-Host ""
    Write-Host "🤖 Querying agent: $Message" -ForegroundColor Cyan
    Write-Host ""
    uv run adk run app "$Message"
} else {
    Write-Host ""
    Write-Host "🚀 Launching Smart Study Agent playground..." -ForegroundColor Cyan
    Write-Host "   Open http://localhost:8000/dev-ui in your browser." -ForegroundColor White
    Write-Host "   Press Ctrl+C to stop the server." -ForegroundColor DarkGray
    Write-Host ""
    uv run adk web .
}
