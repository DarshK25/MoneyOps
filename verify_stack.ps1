$root = "C:\DARSH\MoneyOps"
$feDir = "$root\MoneyOps\Frontend"
$aiDir = "$root\MoneyOps\ai-gateway"
$feLog = "$root\fe.log"
$aiLog = "$root\ai.log"

Write-Host "=== MoneyOps Stack Verification ==="

Write-Host "Starting Frontend..."
$feJob = Start-Job -ScriptBlock { param($d) cd $d; npm run dev 2>&1 } -ArgumentList $feDir

Write-Host "Starting AI Gateway..."
$aiJob = Start-Job -ScriptBlock { param($d) cd $d; uvicorn app.main:app --host 0.0.0.0 --port 8005 2>&1 } -ArgumentList $aiDir

Write-Host "Waiting 30s for services to start..."
Start-Sleep 30

Write-Host "`n=== Checking Services ==="
$feOk = $false; $aiOk = $false
try { $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5; $feOk = $r.StatusCode -eq 200 } catch { Write-Host "Frontend: FAILED - $_" }
try { $r = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/health" -UseBasicParsing -TimeoutSec 5; $aiOk = $r.StatusCode -eq 200 } catch { Write-Host "AI Gateway: FAILED - $_" }

if ($feOk) { Write-Host "Frontend: OK (port 3000)" }
if ($aiOk) { Write-Host "AI Gateway: OK (port 8005)" }

Write-Host "`n=== Frontend Log ==="
Receive-Job -Job $feJob -ErrorAction SilentlyContinue | Select-Object -Last 10
Write-Host "`n=== AI Gateway Log ==="
Receive-Job -Job $aiJob -ErrorAction SilentlyContinue | Select-Object -Last 10

Stop-Job $feJob -ErrorAction SilentlyContinue
Stop-Job $aiJob -ErrorAction SilentlyContinue
Remove-Job $feJob -ErrorAction SilentlyContinue
Remove-Job $aiJob -ErrorAction SilentlyContinue
Write-Host "`n=== Verification Complete ==="
