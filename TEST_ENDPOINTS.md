# API Testing Guide - PowerShell

## Test 1: Health Check ✅
```powershell
curl -X GET http://localhost:8001/api/v1/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "uptime_seconds": 2.29,
  "checks": {"api": "healthy"}
}
```

---

## Test 2: Intent Classification
**Using Invoke-WebRequest (PowerShell native):**
```powershell
$body = @{
    user_input = "Create invoice for Acme Corp for 50,000 rupees"
    industry = "IT & Software"
    has_gst = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/v1/test/intent-classification" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | Select-Object -Expand Content | ConvertFrom-Json
```

**OR using curl (Windows 10+):**
```powershell
curl -X POST http://localhost:8001/api/v1/test/intent-classification `
  -H "Content-Type: application/json" `
  -d '{"user_input":"Create invoice for Acme Corp for 50,000 rupees"}'
```

Expected:
```json
{
  "success": true,
  "user_input": "Create invoice for Acme Corp for 50,000 rupees",
  "classification": {
    "intent": "INVOICE_CREATE",
    "confidence": 0.9,
    "category": "OPERATIONAL",
    "primary_agent": "FINANCE_AGENT"
  }
}
```

---

## Test 3: Entity Extraction
```powershell
$body = @{
    user_input = "Create invoice for Acme Corp for 50,000 rupees due next month"
    intent = "INVOICE_CREATE"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/v1/test/entity-extraction" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | Select-Object -Expand Content | ConvertFrom-Json
```

Expected:
```json
{
  "success": true,
  "user_input": "Create invoice for Acme Corp for 50,000 rupees due next month",
  "extracted_entities": {
    "entities": [
      {"type": "AMOUNT", "value": "50000", "confidence": 0.95},
      {"type": "CLIENT_NAME", "value": "Acme Corp", "confidence": 0.9}
    ]
  }
}
```

---

## Test 4: Strategic Intent (Problem Diagnosis)
```powershell
$body = @{
    user_input = "Why is my revenue down 15% this quarter?"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/v1/test/intent-classification" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | Select-Object -Expand Content | ConvertFrom-Json
```

Expected:
```json
{
  "success": true,
  "classification": {
    "intent": "PROBLEM_DIAGNOSIS",
    "confidence": 0.87,
    "category": "STRATEGIC",
    "primary_agent": "STRATEGY_AGENT",
    "complexity": "STRATEGIC"
  }
}
```

---

## Test 5: Simple Prompt Test
```powershell
$body = @{
    prompt = "What are the key metrics for a SaaS business?"
    temperature = 0.3
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/v1/test/simple-prompt" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | Select-Object -Expand Content | ConvertFrom-Json
```

---

## Troubleshooting

### If you get "Not Found" (404):
1. Check server is running: `Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"}`
2. Restart server from `/MoneyOps/ai-gateway` directory:
   ```powershell
   uvicorn app.main:app --reload --port 8001
   ```

### If you get "Connection refused":
- Server not started. Run: `uvicorn app.main:app --reload --port 8001`
- Check port 8001 is not in use: `Get-NetTCPConnection -LocalPort 8001`

### If response says "Field required":
- Missing required fields in JSON body
- Verify JSON is valid: Use `| ConvertTo-Json` to validate

