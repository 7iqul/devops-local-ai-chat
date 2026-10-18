$ErrorActionPreference = 'Stop'
$models = @('qwen2.5:3b', 'llama3.2:3b')

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $dockerDirectories = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin'),
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin')
    )
    foreach ($directory in $dockerDirectories) {
        if (Test-Path -LiteralPath (Join-Path $directory 'docker.exe')) {
            $env:PATH = "$directory;$env:PATH"
            break
        }
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI was not found. Install Docker Desktop, start it, and open a new PowerShell window.'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Engine is unavailable. Start Docker Desktop and wait for the engine to show Running.'
}

Write-Host 'Building the website and starting Docker Compose services...' -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed to build or start the services.' }

$ollamaReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    $health = docker inspect --format='{{.State.Health.Status}}' devops-guide-ollama 2>$null
    if ($LASTEXITCODE -eq 0 -and $health -eq 'healthy') { $ollamaReady = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ollamaReady) {
    docker compose logs --tail 40 ollama
    throw 'Ollama did not become healthy. Review the logs above and retry.'
}

foreach ($model in $models) {
    Write-Host "Checking $model..." -ForegroundColor Cyan
    $listed = docker compose exec -T ollama ollama list 2>$null | Out-String
    if ($LASTEXITCODE -ne 0) { throw 'Could not query the Ollama container.' }
    if ($listed -notmatch [regex]::Escape($model)) {
        Write-Host "Downloading $model. Internet is required for this first-time step." -ForegroundColor Yellow
        docker compose exec -T ollama ollama pull $model
        if ($LASTEXITCODE -ne 0) { throw "Downloading $model failed. Reconnect to the internet and run .\prepare.ps1 again." }
    } else {
        Write-Host "$model is already available." -ForegroundColor Green
    }
}

Write-Host ''
Write-Host 'Setup is complete. Open http://localhost:8000 and use the chat button in the lower-right corner.' -ForegroundColor Green
Write-Host 'Try both local models, then disconnect the internet and repeat the demo.' -ForegroundColor Green
