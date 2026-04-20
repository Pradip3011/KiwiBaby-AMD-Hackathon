Set WshShell = CreateObject("WshShell")
' Launch Backend and Ngrok in Hidden Mode (0 = Hidden)
WshShell.Run "cmd.exe /c cd /d E:\AGENTIC AI\AI\AI-TESTCASE-AGENT\backend && .\.venv\Scripts\activate && uvicorn app.main:app --port 8001", 0
WshShell.Run "cmd.exe /c ngrok http 8001", 0