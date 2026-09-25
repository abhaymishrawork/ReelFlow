@echo off
rem Run by Windows Task Scheduler every hour. Log: projects\auto_captions.log
cd /d "%~dp0.."
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python tools\auto_captions.py --all >> projects\auto_captions.log 2>&1
