@echo off
cd python
start "api" cmd /k "python main.py"
start "camera" cmd /k "python camera.py"
cd ..
start "web app" cmd /k "npm run dev -- --host"