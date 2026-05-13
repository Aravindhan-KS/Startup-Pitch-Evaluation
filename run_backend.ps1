# Run the FastAPI backend with optional environment configuration
# PowerShell script for Windows

$ErrorActionPreference = "Stop"

# Default values
$BackendDir = "backend"
$PythonCmd = if ($env:PYTHON_CMD) { $env:PYTHON_CMD } else { "python" }
$Host_Addr = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$Port = if ($env:PORT) { $env:PORT } else { "8000" }
$Reload = if ($env:RELOAD) { $env:RELOAD } else { "true" }

# Load .env if present
if (Test-Path ".env") {
    Write-Host "Loading .env file..." -ForegroundColor Green
    $envContent = Get-Content ".env" | Select-String -NotMatch "^#|^$"
    foreach ($line in $envContent) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

# Check if running from repo root
if (-not (Test-Path $BackendDir)) {
    Write-Host "Error: backend/ directory not found. Run from repo root." -ForegroundColor Red
    exit 1
}

# Ensure venv is active or warn user
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Warning: No virtual environment active. Consider activating one:" -ForegroundColor Yellow
    Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
}

# Check if fastapi is installed
$fastapi_installed = & $PythonCmd -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Green
    & pip install -r backend/requirements.txt
}

# Display startup info
$ScoringMode = if ($env:USE_HEURISTIC_PIPELINE -eq "true") { "heuristic" } else { "neural-network" }
Write-Host "Starting FastAPI backend..." -ForegroundColor Green
Write-Host "  Host: $Host_Addr"
Write-Host "  Port: $Port"
Write-Host "  Reload: $Reload"
Write-Host "  Scoring Mode: $ScoringMode"
Write-Host ""
Write-Host "API Docs: http://$Host_Addr`:$Port/docs" -ForegroundColor Cyan
Write-Host "Health: http://$Host_Addr`:$Port/health" -ForegroundColor Cyan
Write-Host ""

# Start the app
Push-Location $BackendDir
if ($Reload -eq "true") {
    & $PythonCmd -m uvicorn app.main:app --host $Host_Addr --port $Port --reload
} else {
    & $PythonCmd -m uvicorn app.main:app --host $Host_Addr --port $Port
}
Pop-Location
