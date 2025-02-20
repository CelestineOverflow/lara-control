@echo off
cd python
start "api" cmd /k "python daemon_process.py"
cd ..
start "web app" cmd /k "npm run dev -- --host"
