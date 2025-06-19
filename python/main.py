from typing	import Dict, Union,	Optional
from fastapi import	FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
from contextlib	import asynccontextmanager
from fastapi.middleware.cors import	CORSMiddleware
import asyncio
from typing	import List
from tray import Tray
from space import Euler, Vector3, Quaternion, Matrix4, Pose, PoseCartesian
import numpy as np
from lara import Lara
import os
from plunger import	Plunger
from scipy.spatial.transform import	Rotation as R
import json
import threading
import time
import queue
import logging
import traceback
import json
# --- Global variables ---
ip = "192.168.2.209"
first_data_json	= None
stop_event = threading.Event()
lara : Lara	= None
offset_x = 3.4
logging.getLogger('lara').setLevel(logging.ERROR)
error_queue = queue.Queue()
warning_queue = queue.Queue()
is_paused =	False
force =	0.0
threshold_default = 1000.0 # Default threshold value for force
threshold_press = 10000.0 # Threshold value for force to trigger fine adjustment
threshold =	threshold_default
unblock_pressure_flag = False
autonomous_control_flag = False

def emit_error(error_code: int, error_message: str):
	error_queue.put((error_code, error_message))

def emit_warning(warning_code: int, warning_message: str):
	warning_queue.put((warning_code, warning_message))

def	current_milli_time():
	return round(time.time() * 1000)

@asynccontextmanager
async def lifespan(app:	FastAPI):
	print("Starting up...")
	global lara
	lara = Lara()
	await lara.connect_socket()
	print("Connected to the	robot")
	lara.robot.turn_off_jog()
	yield
	print("Shutting down...")

app	= FastAPI(lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Allow all origins
	allow_credentials=True,
	allow_methods=["*"],  # Allow all methods
	allow_headers=["*"],  # Allow all headers
)

class GenerateTrayRequest(BaseModel):
	offset_x: Optional[float] =	0.0
	offset_y: Optional[float] =	0.0
	offset_z: Optional[float] =	0.0

@app.get("/")
def	read_root():
	return RedirectResponse(url="/docs")

class ConnectionManager:
	def __init__(self):
		self.active_connections: list[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_text(message)

	async def broadcast(self, message):
		if not isinstance(message, str):
			message = json.dumps(message)
		for connection in self.active_connections.copy():
			try:
				await connection.send_text(message)
			except (WebSocketDisconnect, RuntimeError):
				self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
	global lara, threshold, is_paused
	await manager.connect(websocket)

	try:
		while True:
			if not error_queue.empty():
					error = error_queue.get()
					await manager.broadcast({
						"error": {
							"error_code": error[0],
							"error_message": error[1]
						}
					})
			if not warning_queue.empty():
				warning = warning_queue.get()
				await manager.broadcast({
					"warning": {
						"warning_code": warning[0],
						"warning_message": warning[1]
					}
				})
			await asyncio.sleep(0.1)  # Adjust the sleep time as needed
	except WebSocketDisconnect:
		manager.disconnect(websocket)


@app.post("/setPause")
def	set_pause(pause: bool):
	print("Setting pause to", pause)
	global lara, is_paused
	if pause:
		lara.robot.pause()
	else:
		lara.robot.unpause()
	is_paused =	pause
	return {"is_paused": is_paused}

@app.post("/changeMode")
def	change_mode(mode: str):
	global lara
	mode = mode.lower()
	if mode	== "teach":
		lara.robot.set_mode("Teach")
	elif mode == "semiautomatic":
		lara.robot.set_mode("SemiAutomatic")
	elif mode == "automatic":
		lara.robot.set_mode("Automatic")
	else:
		return {"error": "Invalid mode"}
	return {"mode":	lara.robot.get_mode()}

@app.get("/mode")
def	get_mode():
	global lara
	return {"mode":	lara.robot.get_mode()}

@app.post("/resetRobot")
def	reset_robot():
	global lara
	lara.robot.reset_error()

@app.get("/sim_or_emulation")
def	sim_or_emulation():
	global lara
	return {"context": lara.robot.get_sim_or_real()}

@app.post("/set_sim_or_emulation")
def	set_sim_or_emulation(mode: str):
	global lara
	lara.robot.set_sim_real(mode)
	return {"context": lara.robot.get_sim_or_real()}

tray = None
socket_pose	= None

try:
	with open("config.json", "r") as f:
		config = json.load(f)
		if "socket_pose" in config:
			socket_pose	= Pose.from_json(config["socket_pose"])
			print("Loaded socket pose from config.json")
		if "tray" in config:
			tray = Tray.from_dict(config["tray"])
			print("Loaded tray from	config.json")
except FileNotFoundError:
	pass
except json.JSONDecodeError:
	print("Invalid JSON	in config.json")

@app.post("/setAutonomousControl")
def set_autonomous_control(autonomous_control: bool):
	global autonomous_control_flag
	autonomous_control_flag = autonomous_control
	return {"autonomous_control": autonomous_control_flag}

@app.post("/setSocket")
def	set_socket():
	global lara, socket_pose
	socket_pose	= lara.pose
	# Read existing	config or initialize empty
	config_path	= "config.json"
	if os.path.exists(config_path):
		with open(config_path, "r")	as f:
			try:
				config = json.load(f)
			except json.JSONDecodeError:
				config = {}
	else:
		config = {}
	# Update the socket_pose
	config["socket_pose"] =	socket_pose.to_dict()
	# Write	the	updated	config back	to the file
	with open(config_path, "w")	as f:
		json.dump(config, f, indent=4)
	return socket_pose.to_dict()

@app.get("/getSocket")
def	get_socket():
	global socket_pose
	return socket_pose.to_dict()

@app.post("/setTray")
def	set_tray():
	global lara, tray
	current_pose = lara.pose
	tray = Tray(pose=current_pose)
	# Read existing	config or initialize empty
	config_path	= "config.json"
	if os.path.exists(config_path):
		with open(config_path, "r")	as f:
			try:
				config = json.load(f)
			except json.JSONDecodeError:
				config = {}
	else:
		config = {}
	# Update the tray
	config["tray"] = tray.to_dict()

	# Write	the	updated	config back	to the file
	with open(config_path, "w")	as f:
		json.dump(config, f, indent=4)			
	return tray.get_cell_positions()

@app.get("/getTray")
def	get_tray():
	global tray
	return tray.get_cell_positions()

def	rotate_vector(x, y, angle):
	x_new =	x *	np.cos(angle) -	y *	np.sin(angle)
	y_new =	x *	np.sin(angle) +	y *	np.cos(angle)
	return x_new, y_new

target_camera_translation =	Vector3(-0.00033, -0.0033, 0)

# Try to load target_camera_translation	from config.json
try:
	with open("config.json", "r") as f:
		config = json.load(f)
		if "target_camera_translation" in config:
			tct	= config["target_camera_translation"]
			target_camera_translation =	Vector3(tct["x"], tct["y"],	tct["z"])
			print("Loaded target_camera_translation	from config.json")
		else:
			print("Using default target_camera_translation")
except FileNotFoundError:
	print("config.json not found. Using	default	target_camera_translation")
except json.JSONDecodeError:
	print("Invalid JSON	in config.json.	Using default target_camera_translation")

pose_correct = False
@app.post("/moveToCell")
async def move_to_cell(row: int = 0, col: int = 0):
	global lara, socket_pose
	error = await asyncio.to_thread(lara.move_to_pose, tray.get_cell_robot_orientation(row, col))
	if error:
		return {"error": error}
	return {"success": "Moved to cell"}



@app.post("/to_tray")
async def to_tray():
	global lara, tray
	cell_a0 = tray.get_cell_robot_orientation(0, 0)
	cell_a0_position = cell_a0.position
	#compute headint using x and y
	heading_tray = np.arctan2(cell_a0_position.y, cell_a0_position.x)
	current_joint_angles = await lara.async_robot.get_current_joint_angles()
	lara.robot.set_mode("Automatic")
	try:
		joint_property = {
			"speed": 50.0,
			"acceleration": 3.0,
			"safety_toggle": True,
			"target_joint": [
				[
					current_joint_angles[0],
					current_joint_angles[1],
					current_joint_angles[2],
					current_joint_angles[3],
					current_joint_angles[4],
					current_joint_angles[5]
				],
				[
					current_joint_angles[0],
					-0.056414989727909474,
					1.5068518732631686,
					0.0006344149059273136,
					1.6912666241349086,
					2.322130079912925
				],
				[
					heading_tray,
					-0.056414989727909474,
					1.5068518732631686,
					0.0006344149059273136,
					1.6912666241349086,
					2.322130079912925
				]
				
			],
			"current_joint_angles":  lara.robot.get_current_joint_angles()
		}
		await asyncio.to_thread(lara.robot.move_joint, **joint_property)
		lara.robot.stop() # if there are multiple motions than,this needs to be called only once at the end of the script
		lara.robot.set_mode("Teach")
		return {"success": "ok"}
	except Exception as e:
		error = str(e)
		emit_error(1, error)
		return {"error": "IK Failure"}
	
@app.post("/to_socket")
async def to_socket():
	global lara, socket_pose
	socket_position = socket_pose.position
	heading_socket = np.arctan2(socket_position.y, socket_position.x)
	current_joint_angles = await asyncio.to_thread(lara.robot.get_current_joint_angles)
	await asyncio.to_thread(lara.robot.set_mode, "Automatic")
	try: 
		joint_property = {
				"speed": 50.0,
				"acceleration": 3.0,
				"safety_toggle": True,
				"target_joint": [
					[
						current_joint_angles[0],
						current_joint_angles[1],
						current_joint_angles[2],
						current_joint_angles[3],
						current_joint_angles[4],
						current_joint_angles[5]
					],
					[
						current_joint_angles[0],
						-0.056414989727909474,
						1.5068518732631686,
						0.0006344149059273136,
						1.6912666241349086,
						2.322130079912925
					],
					[
						heading_socket,
						-0.056414989727909474,
						1.5068518732631686,
						0.0006344149059273136,
						1.6912666241349086,
						2.322130079912925
					]
					
				],
				"current_joint_angles":  lara.robot.get_current_joint_angles()
			}
		await asyncio.to_thread(lara.robot.move_joint, **joint_property)
		lara.robot.stop()
		lara.robot.set_mode("Teach")
		return {"success": "ok"}
	except Exception as e:
		error = str(e)
		emit_error(1, error)
		return {"error": "IK Failure"}

@app.post("/retract")
async def retract(distance = -0.15):
	global lara, socket_pose, threshold, threshold_default, unblock_pressure_flag
	#if the value is not negative then throw an error
	distance = float(distance)
	if distance >= 0.0:
		return {"error": "Distance must be negative"}
	# lara.retract(distance)
	await asyncio.to_thread(lara.retract, distance)
	threshold = threshold_default
	unblock_pressure_flag = False
	return {"success": "Retracted"}

@app.post("/moveToCellRetract")
async def move_to_cell_retract(row: int = 0, col: int = 0):
	global lara, socket_pose
	# lara.move_to_pose_from_retract(tray.get_cell_robot_orientation(row, col))
	await asyncio.to_thread(lara.move_to_pose_from_retract, tray.get_cell_robot_orientation(row, col))
	return {"success": "Moved to cell and retracted"}

@app.get("/getOffset")
def	get_offset():
	global offset_x
	return {"offset_x": offset_x}

@app.post("/moveToSocketRetract")
async def move_to_socket_retract():
	global lara, socket_pose
	try:
		await asyncio.to_thread(lara.move_to_pose_tag_from_retract, socket_pose)
		await lara.set_translation_speed_mms(4)
		await lara.set_rotation_speed_degs(1)
		loop = asyncio.get_running_loop()
		def blocking_call():
			return requests.post(
				'http://192.168.2.209:1447/AlingMove',
				headers={'accept': 'application/json'}
			)
		response = await loop.run_in_executor(None, blocking_call)
		#check for errors in json response
		response_json = response.json()
		if "error" in response_json:
			#Response from AlignToTag: {"error":"No data received from the camera"}
			return response_json
		print(f"Response from AlignToTag: {response.text}")
		set_socket()
	except Exception as e:
		return {"error": f"Error during first-time socket move: {str(e)}"}

async def get_camera_pose() -> Pose:
	"""
	Makes a request to get the camera pose data from the camera server.
	Uses run_in_executor to handle the blocking HTTP request asynchronously.
	
	Returns:
		dict: The pose data containing position and orientation information.
	"""
	try:
		loop = asyncio.get_running_loop()
		def blocking_request():
			return requests.get(
				'http://192.168.2.209:1447/get_pose',
				headers={'accept': 'application/json'}
			)
		
		response = await loop.run_in_executor(None, blocking_request)
		response.raise_for_status()  # Raise an exception for error status codes
		response_data = response.json()
		print(f"Camera pose response: {response_data}")
		# {'pose': {'position': {'x': 0.002536922718224708, 'y': 0.0016317179141842983, 'z': 0.14855312461243356}, 'orientation': {'x': -0.14951492301593602, 'y': -0.0028587180024886062, 'z': -0.0008303562976694001, 'w': 0.988754987868754}}}
		pose = Pose.from_json(response_data["pose"])
		return pose
	except Exception as e:
		error_traceback = traceback.format_exc()
		print(f"Error in get_camera_pose:\n{error_traceback}")
		emit_error(1, f"Error in get_camera_pose: {str(e)}")
		return None
	
firstTimeSocketMove = True
tag_pose : Pose = None

@app.post("/moveToSocket")
async def move_to_socket():
	global lara, socket_pose, firstTimeSocketMove, tag_pose
	try:
		await asyncio.to_thread(lara.move_to_pose_tag, socket_pose)
		await lara.set_translation_speed_mms(4)
		await lara.set_rotation_speed_degs(1)
		loop = asyncio.get_running_loop()
		def blocking_call():
			return requests.post(
				'http://192.168.2.209:1447/AlingMove',
				headers={'accept': 'application/json'}
			)
		response = await loop.run_in_executor(None, blocking_call)
		response.raise_for_status()  # Add this to check for HTTP errors
		print(f"Response from AlignToTag: {response.text}")
		set_socket()
		firstTimeSocketMove = False
		return {"status": "First-time socket move completed successfully"}
	except Exception as e:
		emit_error(1, f"Error during first-time socket move: {str(e)}")
		return {"error": f"Error during first-time socket move: {str(e)}"}
	
@app.get("/distance_to_socket")
def distance_to_socket():
	global lara, socket_pose
	if socket_pose is None:
		raise ValueError("Socket pose not set")
	current_pose = lara.current_pose_raw()
	dx = socket_pose.position.x - current_pose.position.x
	dy = socket_pose.position.y - current_pose.position.y
	dz = socket_pose.position.z - current_pose.position.z
	dxy = np.sqrt(dx**2 + dy**2)
	distance = np.sqrt(dx**2 + dy**2 + dz**2)
	return {
		"distance": distance,
		"dx": dx,
		"dy": dy,
		"dz": dz,
		"dxy": dxy
	}

@app.get("/distance_to_cell")
def distance_to_cell(row: int = 0, col: int = 0):
	global lara, tray
	if tray is None:
		raise ValueError("Tray not set")
	cell_pose = tray.get_cell_robot_orientation(row, col)
	current_pose = lara.current_pose_raw()
	dx = cell_pose.position.x - current_pose.position.x
	dy = cell_pose.position.y - current_pose.position.y
	dz = cell_pose.position.z - current_pose.position.z
	dxy = np.sqrt(dx**2 + dy**2)
	distance = np.sqrt(dx**2 + dy**2 + dz**2)
	return {
		"distance": distance,
		"dx": dx,
		"dy": dy,
		"dz": dz,
		"dxy": dxy
	}


@app.post("/moveToSocketSmart")
async def move_to_socket_smart():
	global lara, socket_pose, firstTimeSocketMove, tag_pose
	if socket_pose is None:
		return {"error": "Socket pose not set"}
	current_pose = lara.current_pose_raw()
	#if we are at below the soocket pose in z plus 0.3 then we first retract 0.3m
	if current_pose.position.z < socket_pose.position.z + 0.3:
		await asyncio.to_thread(lara.retract, -0.3)
	#we then check how far we are from the socket pose in x and y
	distance = distance_to_socket()
	if distance["dxy"] > 0.5:
		#we use move to socket
		await to_socket()
	#finally we move to the socket pose without retracting
	await move_to_socket_retract()
	return {"success": "Moved to socket"}

@app.post("/moveToCellSmart")
async def move_to_cell_smart(row: int = 0, col: int = 0):
	global lara, socket_pose
	cell_pose = tray.get_cell_robot_orientation(row, col)
	if cell_pose is None:
		return {"error": "Cell pose not set"}
	current_pose = lara.current_pose_raw()
	#if we are at below the cell pose in z plus 0.3 then we first retract 0.3m
	if current_pose.position.z < cell_pose.position.z + 0.3:
		await asyncio.to_thread(lara.retract, -0.3)
	#we then check how far we are from the cell pose in x and y
	distance = distance_to_cell(row, col)
	if distance["dxy"] > 0.5:
		#we use move to cell
		await to_tray()
	error = await asyncio.to_thread(lara.move_to_pose_from_retract, tray.get_cell_robot_orientation(row, col))
	if error:
		return {"error": error}
	return {"success": "Moved to cell"}

@app.post("/EmergencyStop")
def emergency_stop():
	global lara
	lara.robot.power('off')
	emit_warning(1, "Emergency stop triggered")
	return {"success": "Emergency stop"}

API_FILE = "arm_api.py"

@app.get("/api_version")
def api_version():
	global API_FILE
	if os.path.exists(API_FILE):
		with open(API_FILE, 'r') as file:
			for line in file:
				if line.startswith('__version__'):
					version = line.split('=')[1].strip().strip('"').strip("'")
					return {"version": version}
				
@app.get("/api_module")
def api_module():
	global API_FILE
	if os.path.exists(API_FILE):
		return FileResponse(API_FILE)
	else:
		return {"error": "API module not found"}
	
@app.get("/api_download")
def api_download():
	global API_FILE
	if os.path.exists(API_FILE):
		return FileResponse(API_FILE, media_type='application/octet-stream', filename=API_FILE)
	else:
		return {"error": "API module not found"}

@app.post("/zero_rotation")
async def zero_rotation():
	global lara
	import socketio
	sio = socketio.AsyncClient(logger=False, engineio_logger=False)
	await sio.connect('http://192.168.2.13:8081')
	async def heart_beat(*args, **kwargs):
		await sio.emit('heartbeat_response', True)
		print("Heartbeat response")
	sio.on('heartbeat_check', heart_beat)
	print()
	# Target: {'x': 3.1415795473339365, 'y': -5.071154926206134e-06, 'z': 9.237616908519541e-06}
	
	# Define wiggle room for float comparisons
	wiggle_room = 0.01
	
	while True:
		current_pose = lara.current_pose_raw()
		euler = current_pose.orientation.to_euler()
		
		# Check if orientation is close to target values
		# x should be close to pi, y and z close to 0
		if (abs(euler.x - 3.14159) < wiggle_room and 
			abs(euler.y) < wiggle_room and 
			abs(euler.z) < wiggle_room):
			break
			
		await sio.emit('CartesianGotoManual', {
			"x": current_pose.position.x,
			"y": current_pose.position.y,
			"z": current_pose.position.z,
			"a": 3.141593,
			"b": 0,
			"c": 0,
			"status": True,
			"joint": False,
			"cartesian": True,
			"freedrive": False,
			"button": False,
			"slider": False,
			"goto": True,
			"threeD": False,
			"reference": "Base",
			"absrel": "Absolute"
		})
		await asyncio.sleep(1)
	
	# stop the robot
	await sio.emit('CartesianGotoManual', {
		"x": 0,
		"y": 0,
		"z": 0,
		"a": 0,
		"b": 0,
		"c": 0,
		"status": False,
		"joint": False,
		"cartesian": False,
		"freedrive": False,
		"button": False,
		"slider": False,
		"goto": False,
		"threeD": False,
		"reference": "Base",
		"absrel": "Absolute"
	})

	# Close the connection
	await sio.disconnect()
	return {"success": "Zeroed rotation"}
	

class LedStateModel(BaseModel):
	leds: List[int]	 # or List[bool], depending	on your	usage


@app.get("/orientation_data")
def	get_orientation_data():
	global lara
	orientation	= lara.pose.orientation.to_euler().to_dict(degrees=True)
	return orientation

@app.get("/getJointTorques")
def	get_joint_torques():
	global lara
	torques =  lara.robot.get_current_joint_torques()
	return {"torques": torques}

@app.post("/TurnJogOff")
def	turn_jog_off():
	global lara
	lara.robot.turn_off_jog()

if __name__	== "__main__":
	import uvicorn
	import threading
	import requests
	uvicorn.run(app, host=ip, port=1442)
		