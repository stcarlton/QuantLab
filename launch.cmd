@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%src"

if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
  echo Missing virtual environment python at ".venv\Scripts\python.exe"
  echo Run: python -m venv .venv ^&^& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

"%SCRIPT_DIR%.venv\Scripts\python.exe" -m quantlab.scripts.launch %*
