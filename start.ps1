# MoneyOps Quick Start Script
# Usage: .\start.ps1 [service]
#   .\start.ps1           - Start all services
#   .\start.ps1 backend   - Start only backend
#   .\start.ps1 gateway   - Start API gateway
#   .\start.ps1 ai        - Start AI gateway
#   .\start.ps1 frontend  - Start frontend
#   .\start.ps1 voice     - Start voice service

param(
    [string]$service = "all"
)

$ErrorActionPreference = "Continue"
$rootDir = $PSScriptRoot
$servicesDir = Join-Path $rootDir "MoneyOps"

if (!(Test-Path (Join-Path $rootDir ".env"))) {
    Write-Host "ERROR: .env file not found at $rootDir\.env" -ForegroundColor Red
    exit 1
}

$jobs = @{}

function Start-ServiceWithLog {
    param([string]$name, [string]$command, [string]$workDir, [string]$logFile)
    
    $logDir = Split-Path $logFile -Parent
    if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    
    Write-Host "Starting $name..." -ForegroundColor Yellow
    
    if ($IsWindows) {
        $job = Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", $command -WorkingDirectory $workDir -PassThru -RedirectStandardOutput $logFile
    } else {
        $job = Start-Process -NoNewWindow -FilePath "bash" -ArgumentList "-c", $command -WorkingDirectory $workDir -PassThru
        $output = "$command > $logFile 2>&1 &"
        Invoke-Expression $output
    }
    
    return $job
}

function Start-Backend {
    $jarFile = Get-ChildItem -Path (Join-Path $servicesDir "backend\target") -Filter "moneyops-backend-*.jar" | Select-Object -First 1
    if (!$jarFile) {
        Write-Host "Backend JAR not found. Building first..." -ForegroundColor Yellow
        Push-Location (Join-Path $servicesDir "backend")
        mvn package -DskipTests -q
        Pop-Location
        $jarFile = Get-ChildItem -Path (Join-Path $servicesDir "backend\target") -Filter "moneyops-backend-*.jar" | Select-Object -First 1
    }
    if ($jarFile) {
        Start-ServiceWithLog -name "Backend (port 8000)" -command "java -jar `"$($jarFile.FullName)`" --server.port=8000" -workDir $servicesDir -logFile (Join-Path $servicesDir "backend\backend_out.log")
    }
}

function Start-AIGateway {
    Start-ServiceWithLog -name "AI Gateway (port 8005)" -command "cd ai-gateway && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005" -workDir $servicesDir -logFile (Join-Path $servicesDir "ai-gateway\ai-gateway.log")
}

function Start-APIGateway {
    $jarFile = Get-ChildItem -Path (Join-Path $servicesDir "api-gateway\target") -Filter "api-gateway-*.jar" | Select-Object -First 1
    if (!$jarFile) {
        Write-Host "API Gateway JAR not found. Building first..." -ForegroundColor Yellow
        Push-Location (Join-Path $servicesDir "api-gateway")
        mvn package -DskipTests -q
        Pop-Location
        $jarFile = Get-ChildItem -Path (Join-Path $servicesDir "api-gateway\target") -Filter "api-gateway-*.jar" | Select-Object -First 1
    }
    if ($jarFile) {
        Start-ServiceWithLog -name "API Gateway (port 8002)" -command "java -jar `"$($jarFile.FullName)`" --server.port=8002" -workDir $servicesDir -logFile (Join-Path $servicesDir "api-gateway\api-gateway.log")
    }
}

function Start-Frontend {
    if (!(Test-Path (Join-Path $servicesDir "Frontend\node_modules"))) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Push-Location (Join-Path $servicesDir "Frontend")
        npm install --silent
        Pop-Location
    }
    Start-ServiceWithLog -name "Frontend (port 3000)" -command "npx vite --port 3000 --host" -workDir (Join-Path $servicesDir "Frontend") -logFile (Join-Path $servicesDir "Frontend\frontend.log")
}

function Start-VoiceService {
    Start-ServiceWithLog -name "Voice Service (port 8003)" -command "cd voice-service && python -m app.agent.entrypoint start" -workDir $servicesDir -logFile (Join-Path $servicesDir "voice-service\voice-service.log")
}

switch ($service.ToLower()) {
    "backend"  { Start-Backend }
    "ai"       { Start-AIGateway }
    "gateway"  { Start-APIGateway }
    "frontend" { Start-Frontend }
    "voice"    { Start-VoiceService }
    "all"      {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  MoneyOps - Starting All Services" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Start-Backend
        Start-Sleep -Seconds 3
        Start-AIGateway
        Start-APIGateway
        Start-VoiceService
        Start-Frontend
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  All services starting..." -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  Backend:      http://localhost:8000"
        Write-Host "  AI Gateway:   http://localhost:8005"
        Write-Host "  API Gateway:  http://localhost:8002"
        Write-Host "  Voice Service: http://localhost:8003"
        Write-Host "  Frontend:     http://localhost:3000"
        Write-Host ""
        Write-Host "Log files are in each service directory."
    }
    default {
        Write-Host "Unknown service: $service" -ForegroundColor Red
        Write-Host "Usage: .\start.ps1 [backend|ai|gateway|frontend|voice|all]"
    }
}
