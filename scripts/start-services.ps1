# MoneyOps Services Startup Script
# This script starts all MoneyOps microservices in order

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MoneyOps Services Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found in root directory!" -ForegroundColor Red
    Write-Host "Please create .env file with required configuration." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Found .env configuration" -ForegroundColor Green
Write-Host ""

# Service ports
$BACKEND_PORT = 8000
$AI_GATEWAY_PORT = 8001
$API_GATEWAY_PORT = 8002
$VOICE_SERVICE_PORT = 8003
$FRONTEND_PORT = 5173

Write-Host "Service Ports:" -ForegroundColor Cyan
Write-Host "  Backend:      http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "  AI Gateway:   http://localhost:$AI_GATEWAY_PORT" -ForegroundColor White
Write-Host "  API Gateway:  http://localhost:$API_GATEWAY_PORT" -ForegroundColor White
Write-Host "  Voice Service: http://localhost:$VOICE_SERVICE_PORT" -ForegroundColor White
Write-Host "  Frontend:     http://localhost:$FRONTEND_PORT" -ForegroundColor White
Write-Host ""

Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C in each terminal to stop a service" -ForegroundColor Yellow
Write-Host ""

# Start Backend
Write-Host "[1/5] Starting Backend Service (port $BACKEND_PORT)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\backend'; Write-Host 'Starting Backend...' -ForegroundColor Green; mvn spring-boot:run"
Start-Sleep -Seconds 3

# Start AI Gateway
Write-Host "[2/5] Starting AI Gateway (port $AI_GATEWAY_PORT)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\ai-gateway'; Write-Host 'Starting AI Gateway...' -ForegroundColor Green; python -m uvicorn app.main:app --host 0.0.0.0 --port $AI_GATEWAY_PORT --reload"
Start-Sleep -Seconds 3

# Start API Gateway
Write-Host "[3/5] Starting API Gateway (port $API_GATEWAY_PORT)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\api-gateway'; Write-Host 'Starting API Gateway...' -ForegroundColor Green; mvn spring-boot:run"
Start-Sleep -Seconds 3

# Start Voice Service
Write-Host "[4/5] Starting Voice Service (port $VOICE_SERVICE_PORT)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\voice-service'; Write-Host 'Starting Voice Service...' -ForegroundColor Green; python voice_agent_worker.py"
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "[5/5] Starting Frontend (port $FRONTEND_PORT)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\Frontend'; Write-Host 'Starting Frontend...' -ForegroundColor Green; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are starting in separate windows." -ForegroundColor Yellow
Write-Host "Wait 30-60 seconds for all services to be ready." -ForegroundColor Yellow
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:$FRONTEND_PORT" -ForegroundColor White
Write-Host ""
Write-Host "To stop services: Close each terminal window or press Ctrl+C" -ForegroundColor Yellow
