$env:JWT_SECRET = "xxMln7ov8Z3pEr3zpwdsaJrlR8rJ+qHBzCYO7wTAhPU="
$env:DDL_AUTO = "none"
$dir = "C:\DARSH\MoneyOps"

# Backend
Start-Job -Name Backend -ScriptBlock {
    $env:JWT_SECRET = "xxMln7ov8Z3pEr3zpwdsaJrlR8rJ+qHBzCYO7wTAhPU="
    $env:DDL_AUTO = "none"
    java -jar "C:\DARSH\MoneyOps\MoneyOps\backend\target\moneyops-backend-0.1.0.jar" --server.port=8000
} | Out-Null

# API Gateway (after build completes)
Start-Job -Name APIGateway -ScriptBlock {
    $env:JWT_SECRET = "xxMln7ov8Z3pEr3zpwdsaJrlR8rJ+qHBzCYO7wTAhPU="
    $jar = "C:\DARSH\MoneyOps\MoneyOps\api-gateway\target\api-gateway-0.0.1-SNAPSHOT.jar"
    if (-not (Test-Path $jar)) {
        Set-Location "C:\DARSH\MoneyOps\MoneyOps\api-gateway"
        mvn package -DskipTests
    }
    java -jar $jar --server.port=8002
} | Out-Null

# AI Gateway
Start-Job -Name AIGateway -ScriptBlock {
    Set-Location "C:\DARSH\MoneyOps\MoneyOps\ai-gateway"
    uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
} | Out-Null

# Voice Service
Start-Job -Name VoiceService -ScriptBlock {
    Set-Location "C:\DARSH\MoneyOps\MoneyOps\voice-service"
    & "venv\Scripts\python" -m app.agent.entrypoint start
} | Out-Null

# Frontend
Start-Job -Name Frontend -ScriptBlock {
    Set-Location "C:\DARSH\MoneyOps\MoneyOps\Frontend"
    npx vite --port 3000 --host
} | Out-Null

Write-Host "All 5 services launched!"
Get-Job | Select-Object Id, Name, State
# Keep the script alive to monitor
Start-Sleep 99999
