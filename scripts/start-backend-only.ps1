# Start Backend and API Gateway only
# Useful for testing without AI/Voice services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Backend Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "[1/2] Starting Backend Service (port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\backend'; Write-Host 'Starting Backend...' -ForegroundColor Green; mvn spring-boot:run"
Start-Sleep -Seconds 5

# Start API Gateway
Write-Host "[2/2] Starting API Gateway (port 8002)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\MoneyOps\api-gateway'; Write-Host 'Starting API Gateway...' -ForegroundColor Green; mvn spring-boot:run"

Write-Host ""
Write-Host "Backend services starting..." -ForegroundColor Green
Write-Host "Backend:     http://localhost:8000" -ForegroundColor White
Write-Host "API Gateway: http://localhost:8002" -ForegroundColor White
