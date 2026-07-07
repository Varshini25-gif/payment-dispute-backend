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
    Write-Error "Docker CLI is not available in PATH."
}

Write-Host "Stopping and removing containers..."
docker compose -f docker/docker-compose.yml down
