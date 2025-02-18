from typing	import Dict, Union,	Optional
from fastapi import	FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib	import asynccontextmanager
from fastapi.middleware.cors import	CORSMiddleware
import asyncio
from typing	import List
from tray import Tray
from space import Euler, Vector3, Quaternion, Matrix4, Pose
import numpy as np
from lara import Lara
import os
from plunger import	Plunger
from scipy.spatial.transform import	Rotation as R
import json
import udp_server as udp
import threading
import time
import queue
import logging

# --- Global variables ---

serial_handler = None
json_data =	None
udp_server = None
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


def emit_error(error_code: int, error_message: str):
	error_queue.put((error_code, error_message))

def emit_warning(warning_code: int, warning_message: str):
	warning_queue.put((warning_code, warning_message))

def	reader():
	global serial_handler, json_data, json_data_consumed, first_data_json
	serial_handler.write('{"connected":	1}')
	flag_error_sent = False
	flag_warning_sent = False
	while not stop_event.is_set():
		if serial_handler and not serial_handler.output.empty():
			json_data =	serial_handler.output.get()
			if not first_data_json:
				first_data_json	= json_data
			json_data_consumed = False
			#
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
				# else:
				# 	lara.robot.unpause()
				# 	if lara.collided:
				# 		print(f"collided unblock counter {unblock_collided_counter}")
				# 		unblock_collided_counter += 1
				# 		if unblock_collided_counter	> 10:
				# 			await lara.reset_collision()
				# 			unblock_collided_counter = 0

		time.sleep(0.001)

@asynccontextmanager
async def lifespan(app:	FastAPI):
	global serial_handler, udp_server, reader_thread, stop_event, lara, ip
	serial_handler = Plunger("COM13", 115200)
	serial_handler.start()
	
	# # Start	the	UDP	server
	# udp_server = udp.UDPServer(
	# 	ip=ip,
	# 	port=8765,
	# 	buffer_size=1024,
	# )

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
		print("Closing the UDP server")

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

is_paused =	False
threshold =	10000.0
force =	0.0

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
	global lara, json_data, threshold, is_paused, force, json_data_consumed, first_data_json
	counter = 0
	await websocket.accept()
	active_websockets.append(websocket)
	
	# Send the first data json to all clients
	if first_data_json:
		print("Sending first data json: " + str(first_data_json))
		await broadcast(first_data_json)
	
	try:
		while True:
			if not json_data_consumed and json_data is not None:
				await broadcast(json_data)
				await asyncio.sleep(0.01)
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
			
			await asyncio.sleep(0.01)
	except Exception as e:
		print("Websocket exception:", e)
	finally:
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

@app.post("/setSocket")
def	set_socket():
	global lara, socket_pose, udp_server
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

def	current_milli_time():
	return round(time.time() * 1000)

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

@app.post("/setTarget")
def	set_target():
	global target_camera_translation, udp_server
	message	= udp_server.receive_data()
	if message:
		target_camera_translation =	Vector3(-message["0"]["x"],	-message["0"]["y"],	0)
		print(f"Target camera translation: {target_camera_translation}")
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
		# Update the target_camera_translation
		config["target_camera_translation"]	= {
			"x": target_camera_translation.x,
			"y": target_camera_translation.y,
			"z": target_camera_translation.z
		}
		# Write	the	updated	config back	to the file
		with open(config_path, "w")	as f:
			json.dump(config, f, indent=4)
	return target_camera_translation.to_dict()

pose_correct = False
@app.post("/moveToCell")
def	move_to_cell(row: int =	0, col:	int	= 0):
	global lara, socket_pose, json_data
	error = lara.move_to_pose(tray.get_cell_robot_orientation(row, col))
	if error:
		return {"error": error}
	return {"success": "Moved to cell"}

@app.post("/tare")
def	tare():
	global serial_handler
	serial_handler.write(f'{{"tare": 1}}')
	return {"success": "Tare command sent"}


@app.post("/retract")
def	retract(distance = -0.15):
	global lara, socket_pose, json_data
	#if the value is not negative then throw an error
	distance = float(distance)
	if distance >= 0.0:
		return {"error": "Distance must be negative"}
	lara.retract(distance)

@app.post("/moveToCellRetract")
def	move_to_cell_retract(row: int =	0, col:	int	= 0):
	global lara, socket_pose, json_data
	lara.move_to_pose_from_retract(tray.get_cell_robot_orientation(row, col))


@app.get("/getOffset")
def	get_offset():
	global offset_x
	return {"offset_x": offset_x}

@app.post("/moveToSocketRetract")
async def move_to_socket_retract():
	global lara, socket_pose, json_data
	await lara.set_translation_speed_mms(4)
	await lara.set_rotation_speed_degs(1)
	lara.move_to_pose_tag_from_retract(socket_pose)
	loop = asyncio.get_running_loop()
	def blocking_call():
		return requests.post(
			'http://192.168.2.209:1447/AlignToTag',
			params={'offsetx': offset_x, 'offsety': 0},
			headers={'accept': 'application/json'}
		)
	response = await loop.run_in_executor(None, blocking_call)
	print(f"Response from AlignToTag: {response.text}")
	#set the current pose as the socket pose
	set_socket()




@app.post("/moveToSocket")
async def move_to_socket():
	global lara, socket_pose, json_data, offset_x
	lara.move_to_pose_tag(socket_pose)
	await lara.set_translation_speed_mms(4)
	await lara.set_rotation_speed_degs(1)
	loop = asyncio.get_running_loop()

	def blocking_call():
		return requests.post(
			'http://192.168.2.209:1447/AlignToTag',
			params={'offsetx': offset_x, 'offsety': 0},
			headers={'accept': 'application/json'}
		)

	response = await loop.run_in_executor(None, blocking_call)
	print(f"Response from AlignToTag: {response.text}")
	#set the current pose as the socket pose
	set_socket()
@app.post("/mock_up_move")
async def mock_up_move():
	await lara.start_movement_slider(0,	0, 0, 0, 0, 0)


@app.post("/moveUntilPressure")
async def move_until_pressure(pressure:	float =	1000.0,	wiggle_room: float = 300.0):
	global lara, json_data,	threshold, force, is_paused
	start_position = lara.pose.position	# Store	the	start position
	await lara.set_translation_speed_mms(1)
	move_z = -1 # Direction	to move	in
	MAX_DEPTH =	0.010 #	10mm or 0.01m
	# Move the robot down until	the	force exceeds the threshold	or the maximum depth is reached
	await asyncio.sleep(1)
	print(f"Starting move, start height: {lara.pose.position.z * 1000} mm")
	lara.robot.turn_on_jog(
		jog_velocity=[0, 0, move_z,	0, 0, 0], 
		jog_type='Cartesian'
	)
	for	i in range(1000):
		print(f"height:	{lara.pose.position.z *	1000} mm")
		if lara.pose.position.z	- start_position.z < -MAX_DEPTH:
			break
		# check	if the force exceeds the threshold
		if force > pressure	+ wiggle_room:
			break
		if json_data is not	None:
			if "force" in json_data:
				force =	float(json_data["force"])
				print(f"Current	force: {force}")
				if force > pressure	+ wiggle_room:
					print(f"Force {force} exceeds pressure {pressure} +	wiggle_room	{wiggle_room}. Breaking	loop.")
					break
		lara.robot.jog(set_jogging_external_flag = 1)
		await asyncio.sleep(0.001)
		if i == 999:
			lara.robot.turn_off_jog()
			return {"error": "Force	did	not	exceed threshold within	1000 iterations."}
	lara.robot.turn_off_jog()
	print("Stopped all movements.")



@app.post("/testJog")
async def testJog():
	global lara, json_data,	threshold, force, is_paused
	start_position = lara.pose.position	# Store	the	start position
	await lara.setTranslationSpeedMMs(0.5)
	move_z = -1 # Direction	to move	in
	MAX_DEPTH =	0.010 #	10mm or 0.01m
	await asyncio.sleep(1)

	print(f"Starting move, start height: {lara.pose.position.z * 1000} mm")

	for	k in range(100):
		#go	down 10mm
		print(f"height:	{lara.pose.position.z *	1000} mm")
		for	i in range(10):
			print(f"down")
			lara.robot.turn_on_jog(
			jog_velocity=[0, 0, move_z,	0, 0, 0], 
			jog_type='Cartesian'
			)
			lara.robot.jog(set_jogging_external_flag = 1)
			await asyncio.sleep(0.1)
			move_z = -move_z#
		#go	up 10mm
		
		for	i in range(10):
			print(f"up")
			lara.robot.turn_on_jog(
				jog_velocity=[0, 0, -move_z, 0, 0, 0], 
				jog_type='Cartesian'
			)
			lara.robot.jog(set_jogging_external_flag = 1)
			await asyncio.sleep(0.1)
	lara.robot.turn_off_jog()
	print("Stopped all movements.")


@app.post("/testJog2")
async def testJog2():
	global lara, json_data,	threshold, force, is_paused
	start_position = lara.pose.position	# Store	the	start position
	await lara.setTranslationSpeedMMs(0.5)
	move_z = -1 # Direction	to move	in
	MAX_DEPTH =	0.010 #	10mm or 0.01m
	await asyncio.sleep(1)

	print(f"Starting move, start height: {lara.pose.position.z * 1000} mm")

	for	i in range(1000):
		print(f"height:	{lara.pose.position.z *	1000} mm")
		if lara.pose.position.z	- start_position.z < -MAX_DEPTH:
			print("Max depth reached")
			break
		await lara.start_movement_slider(0,	0, move_z, 0, 0, 0)
		await asyncio.sleep(0.01)
		move_z = -move_z
	await lara.stop_movement_slider(0, 0, 0, 0, 0, 0)
	print("Stopped all movements.")

@app.post("/EmergencyStop")
def	emergency_stop():
	global lara
	lara.robot.power('off')

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


@app.post("/get_camera_data")
def	get_camera_data():
	global udp_server
	data = udp_server.receive_data()
	return {"data":	data}

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


@app.post("/TurnJogOff")
def	turn_jog_off():
	global lara
	lara.robot.turn_off_jog()

if __name__	== "__main__":
	import uvicorn
	import threading
	import requests
	
	uvicorn.run(app, host=ip, port=1442)
		