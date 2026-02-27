# Quick API Test
Write-Host ""
Write-Host "======================================================================"
Write-Host "QUICK INTEGRATION TEST"
Write-Host "======================================================================"
Write-Host ""

# Test 1: Health
Write-Host "1. Testing API Health..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get -UseBasicParsing
    Write-Host "   OK - API is healthy: $($response.service)" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - Cannot connect to API" -ForegroundColor Red
    Write-Host "   Make sure server is running!" -ForegroundColor Yellow
    exit 1
}

# Test 2: Satellites
Write-Host ""
Write-Host "2. Testing Satellite Management..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/satellites/manage" -Method Get -UseBasicParsing
    Write-Host "   OK - Found $($response.count) satellites" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - $_" -ForegroundColor Red
}

# Test 3: History
Write-Host ""
Write-Host "3. Testing History..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/history/statistics?days=30" -Method Get -UseBasicParsing
    Write-Host "   OK - Total analyses: $($response.statistics.total_analyses)" -ForegroundColor Green
    Write-Host "   OK - Avg probability: $($response.statistics.average_probability)" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - $_" -ForegroundColor Red
}

# Test 4: Alerts
Write-Host ""
Write-Host "4. Testing Alerts..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/alerts" -Method Get -UseBasicParsing
    Write-Host "   OK - Found $($response.count) active alerts" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - $_" -ForegroundColor Red
}

# Test 5: Maneuver Calculator
Write-Host ""
Write-Host "5. Testing Maneuver Calculator..."
try {
    $body = @{
        satellite_position = @(6800, 0, 0)
        satellite_velocity = @(0, 7.5, 0)
        debris_position = @(6805, 10, 0)
        debris_velocity = @(0, 7.4, 0)
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/maneuver/calculate" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "   OK - Generated $($response.count) maneuver options" -ForegroundColor Green
    Write-Host "   OK - Recommended: $($response.comparison.recommended.name)" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "BASIC TESTS COMPLETE"
Write-Host "======================================================================"
Write-Host ""
