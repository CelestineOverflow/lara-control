@echo off
cd python
start "api" cmd /k "python daemon_process.py"
cd ..
start "web app" cmd /k "npm run dev -- --host"

start "test_control" cmd.exe /K "cd /D C:\Users\nxp84358\Documents\GitHub\test_control && npm start"
