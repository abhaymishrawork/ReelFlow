@echo off
cd /d "%~dp0"
echo Starting ReelFlow website on http://localhost:8765  (close this window to stop)
python web\app.py
pause
