$ErrorActionPreference = "Stop"

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    $dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $dockerPath) {
        $env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path
        $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    }
}

if (-not $dockerCmd) {
    Write-Host "Docker CLI not found in PATH." -ForegroundColor Red
    Write-Host "Install Docker Desktop and restart your terminal."
    exit 1
}

Write-Host "Docker CLI:" -ForegroundColor Green
docker --version

Write-Host "Docker Compose:" -ForegroundColor Green
docker compose version

try {
    docker info | Out-Null
    Write-Host "Docker daemon is running." -ForegroundColor Green
}
catch {
    Write-Host "Docker daemon is not reachable. Start Docker Desktop and wait until it is ready." -ForegroundColor Yellow
    exit 1
}
