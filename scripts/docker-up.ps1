$ErrorActionPreference = "Stop"

Set-Location -Path (Join-Path $PSScriptRoot "..")

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    $dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $dockerPath) {
        $env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path
        $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    }
}

if (-not $dockerCmd) {
    Write-Error "Docker CLI is not available in PATH. Install Docker Desktop, restart terminal, and try again."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Starting containers..."
docker compose -f docker/docker-compose.yml up --build -d

Write-Host "Container status:"
docker compose -f docker/docker-compose.yml ps

Write-Host "Checking backend health..."
try {
    $response = Invoke-WebRequest -UseBasicParsing "http://localhost:8000/api/health" -TimeoutSec 15
    Write-Host $response.Content
}
catch {
    Write-Warning "Health endpoint is not reachable yet. Check logs with: docker compose -f docker/docker-compose.yml logs -f backend"
}
