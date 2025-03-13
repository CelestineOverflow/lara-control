@echo off
cd python
start "api" cmd /k "python daemon_process.py"
cd ..
start "front_end" cmd /k "cd front_end && npm run dev -- --host"
start "jog_control" cmd.exe /K "cd /DC:\Users\nxp84358\Documents\GitHub\lara-control\jog_control && npm start"
