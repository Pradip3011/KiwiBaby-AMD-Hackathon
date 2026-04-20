@echo off
title PJ AGENTIC SENTINEL: SECURITY CHALLENGE
color 0A
cls
echo 🛡️ PJ AGENTIC SENTINEL: SYSTEM IS CLOAKED.
echo ──────────────────────────────────────────
set /p "pass=🔐 ENTER PJ ARCHITECT CODE: "

:: Verify the secret code
if "%pass%"=="PJ@novvickey30117" (
    echo ✅ IDENTITY VERIFIED. RESTORING WORKSPACE...
    taskkill /f /im ngrok.exe
    taskkill /f /im python.exe
    
    :: Re-launch in VISIBLE mode
    start cmd /k "cd /d E:\AGENTIC AI\AI\AI-TESTCASE-AGENT\backend && .\.venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8001"
    start cmd /k "ngrok http 8001"
    
    echo ✨ Auckland Bridge is now Visible. Welcome back, Boss.
    timeout /t 5
) else (
    echo 🚨 INTRUDER ALERT! WRONG CODE.
    echo 🔒 Locking System and Alerting Mobile...
    :: This locks the Windows screen instantly
    rundll32.exe user32.dll,LockWorkStation
)