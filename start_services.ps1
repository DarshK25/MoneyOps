$commonEnv = @{
    JWT_SECRET = "xxMln7ov8Z3pEr3zpwdsaJrlR8rJ+qHBzCYO7wTAhPU="
    JWT_EXPIRATION = "86400000"
    BACKEND_CORE_URL = "http://localhost:8000"
    AI_GATEWAY_URL = "http://localhost:8005"
    VOICE_SERVICE_URL = "http://localhost:8003"
    GATEWAY_PUBLIC_ENDPOINTS = "/api/auth/login,/api/auth/register,/actuator/health,/actuator/ready,/oauth2,/oauth2/**,/login,/login/**"
}

function Set-EnvVars {
    param($envMap)
    foreach ($kv in $envMap.GetEnumerator()) {
        [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "Process")
    }
}

Set-EnvVars $commonEnv

$jobs = @()

$jobs += Start-Job -Name "backend" -ScriptBlock {
    param($dir, $envVars)
    foreach ($kv in $envVars.GetEnumerator()) {
        [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "Process")
    }
    Set-Location $dir
    java -jar target\moneyops-backend-0.1.0.jar 2>&1 | Out-File "$dir\..\..\backend_out.log"
} -ArgumentList "C:\DARSH\MoneyOps\MoneyOps\backend", $commonEnv

Start-Sleep 10

$jobs += Start-Job -Name "apigateway" -ScriptBlock {
    param($dir, $envVars)
    foreach ($kv in $envVars.GetEnumerator()) {
        [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "Process")
    }
    Set-Location $dir
    java -jar target\api-gateway-1.0.0.jar --spring.profiles.active=dev 2>&1 | Out-File "$dir\..\..\apigateway_out.log"
} -ArgumentList "C:\DARSH\MoneyOps\MoneyOps\api-gateway", $commonEnv

$jobs += Start-Job -Name "aigw" -ScriptBlock {
    param($dir)
    Set-Location $dir
    uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload 2>&1 | Out-File "$dir\..\..\aigw_out.log"
} -ArgumentList "C:\DARSH\MoneyOps\MoneyOps\ai-gateway"

$jobs += Start-Job -Name "voice" -ScriptBlock {
    param($dir)
    Set-Location $dir
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 2>&1 | Out-File "$dir\..\..\voice_out.log"
} -ArgumentList "C:\DARSH\MoneyOps\MoneyOps\voice-service"

$jobs += Start-Job -Name "frontend" -ScriptBlock {
    param($dir)
    Set-Location $dir
    npx vite --port 3000 --host 2>&1 | Out-File "$dir\..\..\frontend_out.log"
} -ArgumentList "C:\DARSH\MoneyOps\MoneyOps\Frontend"

Write-Output "All services launched:"
$jobs | Format-Table Id, Name, State
