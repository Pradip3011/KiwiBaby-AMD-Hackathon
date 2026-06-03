Set oShell = CreateObject("WScript.Shell")
' Use the full path to your workspace
oShell.Run "cmd /c cd /d ""E:\AGENTIC AI\AI\AI-TESTCASE-AGENT"" && python monitor.py", 0, False