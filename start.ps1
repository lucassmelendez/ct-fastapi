# CowTracker FastAPI with Chilean Central Bank Integration - PowerShell Startup Script
# This script will install dependencies, start the server, and run tests

Write-Host "🐄 CowTracker with Chilean Central Bank Integration" -ForegroundColor Green
Write-Host "🚀 PowerShell Startup Script" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Yellow

# Change to project directory
Set-Location "c:\Users\daner\Documents\GitHub\ct-fastapi"

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ and add it to your PATH." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Blue
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies." -ForegroundColor Red
    exit 1
}

# Start the server
Write-Host "`n🚀 Starting FastAPI server..." -ForegroundColor Blue
Write-Host "📍 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🧪 Test Interface: file:///c:/Users/daner/Documents/GitHub/ct-fastapi/test_bcentral.html" -ForegroundColor Cyan

# Start server in background and open browser
Start-Process python -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--port", "8000" -WindowStyle Hidden

# Wait for server to start
Write-Host "`n⏳ Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test server health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Server started successfully!" -ForegroundColor Green
        
        # Open browser to documentation
        Start-Process "http://localhost:8000/docs"
        
        # Run comprehensive tests
        Write-Host "`n🧪 Running API tests..." -ForegroundColor Blue
        python startup.py
        
    } else {
        Write-Host "❌ Server health check failed." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Server is not responding. Please check the console for errors." -ForegroundColor Red
    Write-Host "💡 Try running manually: python -m uvicorn main:app --reload --port 8000" -ForegroundColor Yellow
}

Write-Host "`n🎯 Manual Commands:" -ForegroundColor Blue
Write-Host "Start server: python -m uvicorn main:app --reload --port 8000" -ForegroundColor White
Write-Host "Run tests: python startup.py" -ForegroundColor White
Write-Host "Test specific endpoint: python test_server.py" -ForegroundColor White

Write-Host "`n📋 Project Files:" -ForegroundColor Blue
Write-Host "Main application: main.py" -ForegroundColor White
Write-Host "Central Bank service: bcentral_service.py" -ForegroundColor White
Write-Host "Configuration: config.py" -ForegroundColor White
Write-Host "Environment variables: .env" -ForegroundColor White
Write-Host "Test interface: test_bcentral.html" -ForegroundColor White

Write-Host "`n⏹️  Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
