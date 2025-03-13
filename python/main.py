from typing	import Dict, Union,	Optional
from fastapi import	FastAPI, WebSocket
from fastapi.responses import RedirectResponse
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
# --- Global variables ---

serial_handler = None
json_data =	None
reader_thread =	None
json_data_consumed = False
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

def	reader():
	global serial_handler, json_data, json_data_consumed, first_data_json, threshold, force, lara, unblock_pressure_flag
	serial_handler.write('{"connected":	1}')
	flag_error_sent = False
	flag_warning_sent = False
	start_time = time.time()
	while not stop_event.is_set():
		if serial_handler and not serial_handler.output.empty():
			json_data =	serial_handler.output.get()
			if not first_data_json:
				first_data_json	= json_data
			json_data_consumed = False
			unblock_start_time = None
			if lara is not None:
				if lara.robot.program_status() == "PAUSED":
					print("Robot is paused")
				if lara.collided:
					print("Robot collided")
				if "force" in json_data:
					force =	float(json_data["force"])
					if force > threshold and lara is not None and not flag_error_sent:
						lara.robot.power('off')
						emit_error(1, f"Force exceeded {threshold}, robot powered off")
						flag_error_sent = True
					if force > threshold - (threshold * 0.1) and lara is not None and not flag_warning_sent:
						lara.robot.pause()
						emit_warning(1, f"Force near threshold {threshold}")
						flag_warning_sent = True
					else:
						flag_error_sent = False
						flag_warning_sent = False
					if unblock_pressure_flag:
						if force <(threshold_default/2):
							if unblock_start_time is None:
								unblock_start_time = current_milli_time()
							else:
								if current_milli_time() - unblock_start_time > 2000:
									unblock_pressure_flag = False
									threshold = threshold_default
									unblock_start_time = None

@asynccontextmanager
async def lifespan(app:	FastAPI):
	global serial_handler, reader_thread, stop_event, lara, ip
	serial_handler = Plunger("COM13", 115200)
	serial_handler.start()
	#connect to the	robot
	lara = Lara()
	await lara.connect_socket()
	print("Connected to the	robot")
	lara.robot.turn_off_jog()
	# #	Start the reader thread
	stop_event.clear()
	reader_thread =	threading.Thread(target=reader,	daemon=True)
	reader_thread.start()
	try:
		yield
	finally:
		# Stop the reader thread and clean up
		stop_event.set()
		if reader_thread:
			reader_thread.join()
		serial_handler.stop()

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

active_websockets = []

async def broadcast(message: dict):
	global active_websockets
	# Broadcast the message to all connected websockets
	disconnected = []
	for connection in active_websockets:
		try:
			await connection.send_json(message)
		except Exception as e:
			print("Broadcast error, removing websocket:", e)
			disconnected.append(connection)
	for connection in disconnected:
		active_websockets.remove(connection)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
	global lara, json_data, threshold, is_paused, force, json_data_consumed, first_data_json, autonomous_control_flag
	counter = 0
	await websocket.accept()
	active_websockets.append(websocket)
	last_time = current_milli_time()
	last_time_between = current_milli_time()
	# Send the first data json to all clients
	if first_data_json:
		print("Sending first data json: " + str(first_data_json))
		await broadcast(first_data_json)
	
	try:
		while True:
			if not json_data_consumed and json_data is not None:
				await broadcast(json_data)
				json_data_consumed = True
				counter += 1
			if not error_queue.empty():
					error = error_queue.get()
					await broadcast({
						"error": {
							"error_code": error[0],
							"error_message": error[1]
						}
					})
			if not warning_queue.empty():
				warning = warning_queue.get()
				await broadcast({
					"warning": {
						"warning_code": warning[0],
						"warning_message": warning[1]
					}
				})
			if current_milli_time() - last_time > 500:
				await broadcast({"autonomous_control": autonomous_control_flag})
				last_time = current_milli_time()
			#print time between loops
			# print(f"Time between loops: {current_milli_time() - last_time_between}")
			time_between = current_milli_time() - last_time_between
			if time_between > 50:
				print(f"Time between loops: {time_between}")
			last_time_between = current_milli_time()
			await asyncio.sleep(0.03)
	except Exception as e:
		print("Websocket exception:", e)
	finally:
		if websocket in active_websockets:
			active_websockets.remove(websocket)

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

@app.get("/current_pump_pressure")
def	get_current_pump_pressure():
	global json_data
	if json_data is not None:
		if "pump_sensor" in json_data:
			return {"pressure": json_data["pump_sensor"]}
	return {"pressure": 0}

tray = None
socket_pose	= None
#try to load tray and socket pose from config.json

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
	global lara, socket_pose, json_data
	error = await asyncio.to_thread(lara.move_to_pose, tray.get_cell_robot_orientation(row, col))
	if error:
		return {"error": error}
	return {"success": "Moved to cell"}

@app.post("/tare")
def	tare():
	global serial_handler
	serial_handler.write(f'{{"tare": 1}}')
	return {"success": "Tare command sent"}

@app.post("/retract")
async def retract(distance = -0.15):
	global lara, socket_pose, json_data, threshold, threshold_default, unblock_pressure_flag
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
	global lara, socket_pose, json_data
	# lara.move_to_pose_from_retract(tray.get_cell_robot_orientation(row, col))
	await asyncio.to_thread(lara.move_to_pose_from_retract, tray.get_cell_robot_orientation(row, col))
	return {"success": "Moved to cell and retracted"}

@app.get("/getOffset")
def	get_offset():
	global offset_x
	return {"offset_x": offset_x}

@app.post("/moveToSocketRetract")
async def move_to_socket_retract():
	global lara, socket_pose, json_data
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
	global lara, socket_pose, json_data, firstTimeSocketMove, tag_pose
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

@app.post("/to_tray")
async def to_tray():
	global lara
	current_joint_angles = await lara.async_robot.get_current_joint_angles()
	lara.robot.set_mode("Automatic")
	try:
		joint_property = {
			"speed": 50.0,
			"acceleration": 50.0,
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
					-0.5235,
					-0.056414989727909474,
					1.5068518732631686,
					0.0006344149059273136,
					1.6912666241349086,
					2.322130079912925
				],
				[
					1.5707873386262174,
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
	global lara
	current_joint_angles = await asyncio.to_thread(lara.robot.get_current_joint_angles)
	await asyncio.to_thread(lara.robot.set_mode, "Automatic")
	try: 
		joint_property = {
				"speed": 50.0,
				"acceleration": 50.0,
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
						1.5707873386262174,
						-0.056414989727909474,
						1.5068518732631686,
						0.0006344149059273136,
						1.6912666241349086,
						2.322130079912925
					],
					[
						-0.5235,
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

@app.post("/moveUntilPressure")
async def move_until_pressure(pressure: float = 1000.0, wiggle_room: float = 300.0):
	global lara, json_data, threshold, force, threshold_press, unblock_pressure_flag
	error = None
	current_force = 0
	unblock_pressure_flag = False
	threshold = threshold_press
	# Store starting position
	start_position = lara.current_pose_raw().position
	await lara.set_translation_speed_mms(1)
	MAX_DEPTH = 0.010  # 10mm or 0.01m
	
	# First stage: Move down continuously until near target pressure
	print(f"Starting move, start height: {lara.pose.position.z * 1000} mm")
	
	counter = 0
	while True:
		print(f"Height: {lara.current_pose_raw().position.z * 1000} mm")
		
		# Check maximum depth for safety
		if  lara.current_pose_raw().position.z - start_position.z < -MAX_DEPTH:
			print("Maximum depth reached")
			error = "Maximum depth reached"
			break
			
		# Check if we have force data
		if json_data is not None and "force" in json_data:
			current_force = float(json_data["force"])
			print(f"Current force: {current_force}")
			
			# Stop when we get close to target pressure
			if current_force > (pressure - wiggle_room):
				print(f"Initial pressure target reached: {current_force}")
				break
				
			# Continue jogging down
			lara.start_moving(0, 0, -1, 0, 0, 0)
			await asyncio.sleep(0.01)
			counter += 1
			if counter > 10000:
				error = "Counter exceeded"
				break
	lara.stopMoving()
	if error:
		return {"error": error}
	# Second stage if pressure is higher than 3000
	if current_force > 3000:
		res =  await fine_adjust_pressure(pressure, wiggle_room)
		unblock_pressure_flag = True
		return res
	else:
		unblock_pressure_flag = True
		return {"success": "Pressure reached target"}

async def fine_adjust_pressure(pressure: float = 1000.0, wiggle_room: float = 50.0):
	global lara, json_data
	error = None
	try:
		print(f"Starting fine pressure adjustment to target {pressure}±{wiggle_room}")
		await lara.set_translation_speed_mms(0.5)
		
		# Track consecutive readings within threshold to ensure stability
		stable_count = 0
		required_stable_readings = 10  # Number of consecutive readings needed to confirm stability
		current_force = 0
		
		for i in range(200):  # Maximum iterations
			if json_data is not None and "force" in json_data:
				current_force = float(json_data["force"])
				print(f"Current force: {current_force}, target: {pressure}±{wiggle_room}")
				
				if current_force < pressure - wiggle_room:
					# Too little pressure, move down
					print("Pressure too low - moving down")
					lara.start_moving(0, 0, -0.1, 0, 0, 0)
					lara.stopMoving()
					stable_count = 0
				elif current_force > pressure + wiggle_room:
					# Too much pressure, move up
					print("Pressure too high - moving up")
					lara.start_moving(0, 0, 0.1, 0, 0, 0)
					lara.stopMoving()
					stable_count = 0
				else:
					# Within threshold, increase stable count
					print(f"Within threshold, stable count: {stable_count}/{required_stable_readings}")
					lara.stopMoving()
					stable_count += 1
					if stable_count >= required_stable_readings:
						print("Pressure stabilized within threshold")
						break
				await asyncio.sleep(0.02)
			if i == 199:
				error = "Failed to stabilize pressure within maximum iterations"
	except Exception as e:
		error = str(e)
		print(f"Error during pressure adjustment: {error}")
	finally:
		lara.stopMoving()
		if error:
			return {"error": error}
		return {"success": f"Force stabilized at {current_force} (target: {pressure}±{wiggle_room})"}

@app.post("/EmergencyStop")
def emergency_stop():
	global lara
	lara.robot.power('off')
	emit_warning(1, "Emergency stop triggered")
	return {"success": "Emergency stop"}

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
	
@app.post("/togglePump")
def	toggle_pump(boolean	: bool):
	global serial_handler
	serial_handler.write(f'{{"pump": {100 if boolean else 0}}}')
	return {"pump":	100	if boolean else	0}

class LedStateModel(BaseModel):
	leds: List[int]	 # or List[bool], depending	on your	usage

@app.post("/setLeds")
def	set_leds(led_data: LedStateModel):
	"""
	Just sets the LED states in one	shot.
	Example	payload:
	{
	  "leds": [1, 0, 1, 1, 0, 1, 0]
	}
	"""
	payload	= {"leds": led_data.leds}
	serial_handler.write(json.dumps(payload))  # Chuck it to the microcontroller
	return payload

@app.get("/orientation_data")
def	get_orientation_data():
	global lara
	orientation	= lara.pose.orientation.to_euler().to_dict(degrees=True)
	return orientation

@app.post("/setBrightness")
def	set_brightness(newBrightness : int):
	global serial_handler
	serial_handler.write(f'{{"brightness": {newBrightness}}}')
	return {"brightness": newBrightness}

@app.post("/setHSL")
def	set_hsl(hue	: float, sat : float, light	: float):
	global serial_handler
	serial_handler.write(f'{{"hue":	{hue}, "sat": {sat}, "light": {light}}}')
	return {"hue": hue,	"sat": sat,	"light": light}

@app.post("/setHeater")
def	setHeater(newHeat :	int):
	global serial_handler
	serial_handler.write(f'{{"setTemp":	{newHeat}}}')
	return {"setTemp": newHeat}

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
		