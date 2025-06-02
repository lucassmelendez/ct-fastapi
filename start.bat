@echo off
echo 🐄 CowTracker with Chilean Central Bank Integration
echo 🚀 Quick Start Script
echo ==============================================

cd /d "c:\Users\daner\Documents\GitHub\ct-fastapi"

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Starting FastAPI server...
echo 📍 Server: http://localhost:8000
echo 📖 Docs: http://localhost:8000/docs
echo.

start "" "http://localhost:8000/docs"

python -m uvicorn main:app --reload --port 8000

pause
