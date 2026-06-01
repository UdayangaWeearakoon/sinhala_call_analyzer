' Sinhala Call Analytics — Pipeline Launcher (silent, no window)
' Used by Windows Task Scheduler to run the pipeline without a console window.

Dim shell, pythonExe, projectDir, command
pythonExe = "C:\Users\udaya\OneDrive\Desktop\sinhala_call_analytics\.venv\Scripts\python.exe"
projectDir = "C:\Users\udaya\OneDrive\Desktop\sinhala_call_analytics"

Set shell = CreateObject("WScript.Shell")
command = """" & pythonExe & """ -m src.pipeline.main --watch"
shell.CurrentDirectory = projectDir
shell.Run command, 0, False
