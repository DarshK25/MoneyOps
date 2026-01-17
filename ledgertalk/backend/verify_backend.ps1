$baseUrl = "http://localhost:8080/api"

Write-Host "1. Testing Registration..."
$registerBody = @{
    name = "Verify User"
    email = "verify_" + (Get-Random) + "@example.com"
    password = "password123"
    orgName = "Verify Org"
} | ConvertTo-Json

try {
    $regResponse = Invoke-RestMethod -Uri "$baseUrl/auth/register" -Method Post -Body $registerBody -ContentType "application/json"
    $token = $regResponse.data.accessToken
    Write-Host "   Success! Token received." -ForegroundColor Green
} catch {
    Write-Host "   Registration Failed: $_" -ForegroundColor Red
    exit
}

Write-Host "`n2. Testing Document Creation..."
$docBody = @{
    name = "TestDoc.txt"
    type = "TXT"
    size = 123
    mimeType = "text/plain"
} | ConvertTo-Json

$headers = @{
    Authorization = "Bearer $token"
}

try {
    $docResponse = Invoke-RestMethod -Uri "$baseUrl/documents" -Method Post -Body $docBody -ContentType "application/json" -Headers $headers
    Write-Host "   Success! Document created with ID: $($docResponse.data.id)" -ForegroundColor Green
} catch {
    Write-Host "   Document Creation Failed: $_" -ForegroundColor Red
}

Write-Host "`nVerification Complete."
