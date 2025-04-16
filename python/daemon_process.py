import colorama
colorama.init()
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
import json
import process_manager
import ctypes
import os
from mdns_utils import register_mdns_service
import argparse

processes = []

import time

g_show = False

def show_console(show=True):
    global g_show
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    SW_SHOW = 5
    SW_HIDE = 0

    hWnd = kernel32.GetConsoleWindow()
    if hWnd:
        if show:
            g_show = True 
            user32.ShowWindow(hWnd, SW_SHOW) # show the window
            user32.SetForegroundWindow(hWnd) # focus on the windows
        else:
            g_show = False
            user32.ShowWindaedow(hWnd, SW_HIDE)




@asynccontextmanager
async def lifespan(app: FastAPI):
    global processes
    show_console()
    processes = process_manager.start_processes()
    yield
    # Kill the processes
    if processes:
        for p in processes:
            p.kill()

app = FastAPI(lifespan=lifespan)

active_websockets = []
import traceback
async def broadcast(message: dict):
	global active_websockets
	# Broadcast the message to all connected websockets
	disconnected = []
	for connection in active_websockets:
		try:
			await connection.send_json(message)
		except WebSocketDisconnect:
			disconnected.append(connection)
	for connection in disconnected:
		if connection in active_websockets:  # Check if connection is still in the list
			active_websockets.remove(connection)

def generate_state():
    state = {}
    if not processes:
        return json.dumps(state)
    for p in processes:
        state[p.script_name] = p.__dict__()
    #add the state of this process 
    state['daemon'] = {"pid": os.getpid(), "running": True, "debug": g_show}
    return json.dumps(state)

@app.get("/restart_process")
async def restart_process(script_name: str):
    for p in processes:
        if p.script_name == script_name:
            p.restart()
            return JSONResponse(content={"status": "success", "message": f"Process {script_name} restarted"})
    return JSONResponse(content={"status": "error", "message": f"Process {script_name} not found"})

@app.get("/kill_process")
async def kill_process(script_name: str):
    for p in processes:
        if p.script_name == script_name:
            p.kill()
            return JSONResponse(content={"status": "success", "message": f"Process {script_name} killed"})
    return JSONResponse(content={"status": "error", "message": f"Process {script_name} not found"})

@app.get("/show_process")
async def show_process(script_name: str):
    for p in processes:
        if p.script_name == script_name:
            p.toggle_view()
            return JSONResponse(content={"status": "success", "message": f"Process {script_name} debug set to {p.debug}"})
    return JSONResponse(content={"status": "error", "message": f"Process {script_name} not found"})

@app.get("/")
async def root():
    return HTMLResponse(content="<html><head><meta http-equiv='refresh' content='0; url=/docs'></head></html>")
last_time = time.time()
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global last_time
    await websocket.accept()
    active_websockets.append(websocket)
    while True:
        last_time = time.time()
        try:
            await broadcast(generate_state())
        except WebSocketDisconnect:
            if websocket in active_websockets:
                active_websockets.remove(websocket)
            break 
        await asyncio.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process manager')
    parser.add_argument('--host', type=bool, default=False, help='Host for the WebSocket server')
    parser.add_argument('--port', type=int, default=8765, help='Port for the WebSocket server')
    parser.add_argument('--service-name', type=str, default="process_manager", help='Name of the mDNS service')
    args = parser.parse_args()


    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    HOST = "192.168.2.209"  # Default IP address

    if args.host:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        HOST = socket.gethostbyname(socket.gethostname())
    print(f"Running process manager server => {HOST}:{args.port}")
    uvicorn.run(app, host=HOST, port=args.port)

    register_mdns_service(args.service_name, args.port)