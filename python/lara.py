import aiohttp
import asyncio
import socketio
import logging
import time
import numpy as np
from scipy.spatial.transform import	Rotation as R
from neura.neurapy.robot import	Robot
from space import Pose,	Vector3, Quaternion, Euler,	PoseCartesian
import requests

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)

from websockets.sync.client import connect
import json		
link = "ws://192.168.2.209:8083"
		
class AsyncWrapper:
	def __init__(self, robot):
		self._robot = robot
	def __getattr__(self, name):
		attr = getattr(self._robot, name)
		if callable(attr):
			async def wrapper(*args, **kwargs):
				return await asyncio.to_thread(attr, *args, **kwargs)
			return wrapper
		return attr



class Lara:
	def __init__(self):
		self.robot =	Robot()
		self.joints = {
			"joint1": 0,
			"joint2": 0,
			"joint3": 0,
			"joint4": 0,
			"joint5": 0,
			"joint6": 0,
		}
		self.sio	= socketio.AsyncClient(logger=False, engineio_logger=False)
		self.sio.on('Cartesian_Pose', self.__set_cartesian_pose)
		self.sio.on('Joint_Angle', self.__set_joint_angle)
		self.sio.on('connect', self.on_connect)
		self.sio.on('disconnect', self.on_disconnect)
		self.sio.on('heartbeat_check', self.send_hearbeat_response)
		self.sio.on('error', self.report_error)
		self.sio.on('CollisionDetected', self.on_collision_effect)
		self.max_rotation_speed = 0.2617994	# rad/s
		self.max_translation_speed =	0.25	# m/s
		self.pose: Pose = Pose(Vector3(0, 0, 0),	Quaternion(0, 0, 0, 1))
		# For tracking heartbeats & slider calls
		self.last_slider_call = 0.0
		self.heartbeat_task = None
		self.heartbeat_running =	False
		self.cartesian_slider_data =	{}
		self.collided = False
		self.started_movement_slider = False
		self.current_linear_speed = None # Meters
		self.current_rotation_speed = None # Rads
		self.async_robot = AsyncWrapper(self.robot)


	async def report_error(self, data):
		print(f"Error: {data}")
	async def __set_joint_angle(self, data) -> None:
		self.joints = {
			"joint1": data['A1'],
			"joint2": data['A2'],
			"joint3": data['A3'],
			"joint4": data['A4'],
			"joint5": data['A5'],
			"joint6": data['A6'],
	   }
	async def __set_cartesian_pose(self,	data) -> None:
		self.pose = Pose(
			Vector3(x=data['X'],y=data['Y'], z=data['Z']),
			Quaternion(x=data['_X'],y=data['_Y'], z=data['_Z'],	w=data['_W'])
		)
	async def on_collision_effect(self, args):
		print(f"Collision detected: {args}")
		await asyncio.sleep(2)
		self.collided = True
	async def reset_collision(self):
		await self.sio.emit("reset_collision", {"reset": True})
		await asyncio.sleep(0.5)
		response = requests.get("http://192.168.2.13:8081/api/cartesian")
		data = response.json()

		self.collided = False
	async def fetch_cartesian_pose(self):
		response = requests.get("http://192.168.2.13:8081/api/cartesianpose")
		data = response.json()
		data = data[0]
		self.pose = Pose(
			Vector3(x=data['X'],y=data['Y'], z=data['Z']),
			Quaternion(x=data['_X'],y=data['_Y'], z=data['_Z'],	w=data['_W'])
		)

	async def connect_socket(self):
		if not self.sio.connected:
			await self.sio.connect('http://192.168.2.13:8081')
		await self.fetch_cartesian_pose()
	async def on_connect(self):
		print('connection established')
	async def on_disconnect(self):
		print('disconnected from	server')

	def rot_speed_deg_is_close_to_current(self, deg_s, tol=0.1):
		current_rad = self.current_rotation_speed
		target_rad = deg_s * 0.0174533
		diff = abs(current_rad - target_rad)
		print("----- DEBUG: rot_speed_deg_is_close_to_current -----")
		print(f"Current rotation speed (rad/s): {current_rad}")
		print(f"Target rotation speed (rad/s): {target_rad}")
		print(f"Difference: {diff} (tolerance: {tol})")
		print("------------------------------------------------------")
		return diff < tol
	


	async def send_hearbeat_response(self, *args):
		"""Send a heartbeat response to request."""
		# print("Sending heartbeat.")
		await self.sio.emit("heartbeat_response", True)
	def deg2rad(self, deg):
		return deg *	0.0174533
	
	async def set_translation_speed(self, speed):
		self.current_linear_speed = speed
		if speed > self.max_translation_speed:
			speed = self.max_translation_speed
			print("Speed	is too high, setting to 0.25")
		elif speed < 0:
			print("Speed	cannot be negative,	setting	to 0")
			speed = 0
		await self.connect_socket()
		async with aiohttp.ClientSession() as session:
			async with session.patch(
				"http://192.168.2.13:8081/api/cartesian",
				headers={"Content-Type":	"application/json"},
				json={"linearVelocity": speed}
			) as response:
				logging.info(await response.text())
		await asyncio.sleep(0.2)
		await self.sio.emit("linearveltrigger", {"data":	True})
		await asyncio.sleep(0.2)
		
	
	async def set_rotation_speed(self, speed):
		self.current_rotation_speed = speed
		if speed > self.max_rotation_speed:
			speed = self.max_rotation_speed
			print("Speed is too high, setting to 0.2617994")
		elif speed < 0:
			print("Speed cannot be negative, setting to 0")
			speed = 0
		await self.connect_socket()
		async with aiohttp.ClientSession() as session:
			async with session.patch(
				"http://192.168.2.13:8081/api/cartesian",
				headers={"Content-Type":	"application/json"},
				json={"rotationSpeed": speed}
			) as response:
				logging.info(await response.text())
		await asyncio.sleep(0.2)
		await self.sio.emit("linearveltrigger", {"data":	True})
		await asyncio.sleep(0.2)
		
	def setRotSpeedDegSNoAsync(self, deg_s):
		rad_s = deg_s * 0.0174533
		print(f"Setting rotational speed to {rad_s} rad/s or {deg_s} deg/s")
		asyncio.run(self.set_rotation_speed(rad_s))

	def setTranslationSpeedMMsNoAsync(self, mm_s):
		linear_speed = mm_s / 1000
		print(f"Setting translation speed to {linear_speed} m/s or {mm_s} mm/s")
		asyncio.run(self.set_translation_speed(linear_speed))

	async def set_translation_speed_mms(self, mm_s):
		linear_speed = mm_s / 1000
		print(f"Setting translation speed to {linear_speed} m/s or {mm_s} mm/s")
		await self.set_translation_speed(linear_speed)

	async def set_rotation_speed_degs(self, deg_s):
		rad_s = deg_s * 0.0174533
		print(f"Setting rotational speed to {rad_s} rad/s or {deg_s} deg/s")
		await self.set_rotation_speed(rad_s)
	async def start_movement_slider(self,q0, q1, q2, q3, q4, q5):
		data = {
			'q0': q0,
			'q1': q1,
			'q2': q2,
			'q3': q3,
			'q4': q4,
			'q5': q5,
			'status': True,
			'joint': False,
			'cartesian': True,
			'freedrive': False,
			'button': False,
			'slider': True,
			'goto': False,
			'threeD': False,
			'reference': "Base",
			'absrel': "Absolute",
		}
		await self.sio.emit('CartesianSlider', data)
		
	async def stop_movement_slider(self, q0, q1, q2, q3, q4, q5):
		data = {
			'q0': q0,
			'q1': q1,
			'q2': q2,
			'q3': q3,
			'q4': q4,
			'q5': q5,
			'status': False,
			'joint': False,
			'cartesian': True,
			'freedrive': False,
			'button': False,
			'slider': True,
			'goto': False,
			'threeD': False,
			'reference': "Base",
			'absrel': "Absolute",
		}
		await self.sio.emit('CartesianSlider', data)

	def retract(self, distance = -0.3):
        # First step: use the current pose
		steps = []
		steps.append(self.current_pose())
		# Second step: move 0.3 m along the local Z-axis (normal) of the current orientation
		offset = np.array([0, 0, distance])
		rotation_matrix = R.from_quat([
			self.pose.orientation.x,
			self.pose.orientation.y,
			self.pose.orientation.z,
			self.pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset

		new_position = Vector3(
			self.pose.position.x + offset_global[0],
			self.pose.position.y + offset_global[1],
			self.pose.position.z + offset_global[2]
		)
		steps.append(PoseCartesian(position=new_position, orientation=self.pose.orientation.to_euler(order="xyz")))
		#move
		self.__move_to_steps(steps)
	
	def move_to_pose_from_retract(self, pose: Pose):
		print(f"Moving to pose: {pose}")
        # First step: use the current pose (retracted)
		steps = []
		steps.append(self.current_pose())
		# Second step is target position + offset
		offset = np.array([0, 0, -0.3])
		rotation_matrix = R.from_quat([
			pose.orientation.x,
			pose.orientation.y,
			pose.orientation.z,
			pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset
		new_position = Vector3(
			pose.position.x + offset_global[0],
			pose.position.y + offset_global[1],
			pose.position.z + offset_global[2]
		)
		steps.append(PoseCartesian(position=new_position, orientation=pose.orientation.to_euler(order="xyz")))
		#fourth step is the target position
		steps.append(PoseCartesian(position=pose.position, orientation=pose.orientation.to_euler(order="xyz")))
		#move
		self.__move_to_steps(steps)
	

	
	def __move_to_steps(self, steps):
		if not steps:
			raise ValueError("No steps provided")
		error = False
		print(f"Moving: {len(steps)} steps")
		try: 
			self.robot.set_mode("Automatic")
			linear_property = {
			"speed": 0.2,
			"acceleration": 0.001,
			"blend_radius": 0.005,
			"target_pose": [
				[step.position.x, step.position.y, step.position.z, step.orientation.x, step.orientation.y, step.orientation.z] for step in steps
			],
			"current_joint_angles": self.robot.robot_status("jointAngles"),
			"weaving": False,
			"pattern": 1,
			"amplitude": 0.006,
			"amplitude_left": 0.0,
			"amplitude_right": 0.0,
			"frequency": 1.5,
			"dwell_time_left": 0.0,
			"dwell_time_right": 0.0,
			"elevation": 0.0,
			"azimuth": 0.0
			}
			self.robot.unpause()
			self.robot.move_linear(**linear_property)
			print("Movement done")
			self.robot.stop()
			print("Stopped")
		except Exception as e:
			print(f"Error: {e}")
			error = True
		finally:
			self.robot.set_mode("Teach")
			if error:
				raise ValueError("Error occurred during movement")
			else:
				print("Movement completed successfully")


	def move_to_pose(self, pose: Pose):
		'''
		Moves to the target position by performing a retract along the normal then moving toward the target position
		'''
		print(f"Moving to pose: {pose}")
        # First step: use the current pose
		steps = []
		steps.append(self.current_pose())

		# Second step: move 0.3 m along the local Z-axis (normal) of the current orientation
		offset = np.array([0, 0, -0.3])
		rotation_matrix = R.from_quat([
			self.pose.orientation.x,
			self.pose.orientation.y,
			self.pose.orientation.z,
			self.pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset

		new_position = Vector3(
			self.pose.position.x + offset_global[0],
			self.pose.position.y + offset_global[1],
			self.pose.position.z + offset_global[2]
		)

		steps.append(PoseCartesian(position=new_position, orientation=self.pose.orientation.to_euler(order="xyz")))
		# third step is target position + offset
		rotation_matrix = R.from_quat([
			pose.orientation.x,
			pose.orientation.y,
			pose.orientation.z,
			pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset
		new_position = Vector3(
			pose.position.x + offset_global[0],
			pose.position.y + offset_global[1],
			pose.position.z + offset_global[2]
		)
		steps.append(PoseCartesian(position=new_position, orientation=pose.orientation.to_euler(order="xyz")))
		# fourth step is the target position
		steps.append(PoseCartesian(position=pose.position, orientation=pose.orientation.to_euler(order="xyz")))
		# 
		return self.__move_to_steps(steps)
	
	def move_to_pose_cartesian_from_current(self, pose: PoseCartesian):
		'''
		Moves to the target position by performing a retract along the normal then moving toward the target position
		'''
		print(f"Moving to pose: {pose}")
		# First step: use the current pose
		steps = []
		steps.append(self.current_pose())
		# Second step is the target position
		steps.append(pose)
		# 
		return self.__move_to_steps(steps)
	
	def move_to_pose_tag_from_retract(self, pose: Pose):
		'''
		Moves to tag pose, to be used only with retract movement before hand
		'''
		# First step: use the current pose (retracted)
		steps = []
		steps.append(self.current_pose())
		# Second step is target position + offset
		offset = np.array([0, 0, -0.15])
		rotation_matrix = R.from_quat([
			pose.orientation.x,
			pose.orientation.y,
			pose.orientation.z,
			pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset
		new_position = Vector3(
			pose.position.x + offset_global[0],
			pose.position.y + offset_global[1],
			pose.position.z + offset_global[2]
		)
		steps.append(PoseCartesian(position=new_position, orientation=pose.orientation.to_euler(order="xyz")))
		self.__move_to_steps(steps)

	def move_from_current_direct(self, pose: Pose):
		'''
		Moves to tag pose, to be used only with retract movement before hand
		'''
		# First step: use the current pose (retracted)
		steps = []
		steps.append(self.current_pose())
		# Second step is target position + offset
		steps.append(PoseCartesian(position=pose.position, orientation=pose.orientation.to_euler(order="xyz")))
		self.__move_to_steps(steps)

	
	def move_to_pose_tag(self, pose: Pose):
		print(f"Moving to pose: {pose}")
        # First step: use the current pose
		steps = []
		print(f"Current pose: {self.current_pose()}")
		steps.append(self.current_pose())
		

		# Second step: move 0.3 m along the local Z-axis (normal) of the current orientation
		offset = np.array([0, 0, -0.3])
		rotation_matrix = R.from_quat([
			self.pose.orientation.x,
			self.pose.orientation.y,
			self.pose.orientation.z,
			self.pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset

		new_position = Vector3(
			self.pose.position.x + offset_global[0],
			self.pose.position.y + offset_global[1],
			self.pose.position.z + offset_global[2]
		)

		steps.append(PoseCartesian(position=new_position, orientation=self.pose.orientation.to_euler(order="xyz")))
		#third step is target position + offset
		offset = np.array([0, 0, -0.15])
		rotation_matrix = R.from_quat([
			pose.orientation.x,
			pose.orientation.y,
			pose.orientation.z,
			pose.orientation.w
		]).as_matrix()
		offset_global = rotation_matrix @ offset
		new_position = Vector3(
			pose.position.x + offset_global[0],
			pose.position.y + offset_global[1],
			pose.position.z + offset_global[2]
		)
		steps.append(PoseCartesian(position=new_position, orientation=pose.orientation.to_euler(order="xyz")))
		self.__move_to_steps(steps)

	def current_pose(self) -> PoseCartesian:
		pose = self.robot.get_tcp_pose_quaternion() # [X,Y,Z,w,x,y,z] 
		return Pose(
			position=Vector3(x=pose[0], y=pose[1], z=pose[2]),
			orientation=Quaternion(x=pose[4], y=pose[5], z=pose[6], w=pose[3])
		).to_Cartesian()
		
	def current_pose_raw(self) -> Pose:
		pose = self.robot.get_tcp_pose_quaternion() # [X,Y,Z,w,x,y,z]
		qt = Quaternion(x=pose[4], y=pose[5], z=pose[6], w=pose[3])
		qt = qt * Quaternion(1, 0, 0, 0).invert()
		p =  Pose(
			position=Vector3(x=pose[0], y=pose[1], z=pose[2]),
			orientation=Quaternion(x=pose[4], y=pose[5], z=pose[6], w=pose[3])
		)
		return p

	def move_to_pose_relative(self, relative: Pose):
		pose = self.robot.get_tcp_pose_quaternion()
		#last 4 values are quaternion
		quat = pose[-4:]
		rpy = self.robot.quaternion_to_rpy(quat[0], quat[1], quat[2], quat[3])
		pose = pose[:-4]
		pose.extend(rpy)
		relative_rpy = relative.orientation.to_euler(order="xyz")
		# get current cartesian positio
		linear_property = {
		"speed": 0.008,
		"acceleration": 1.0,
		"blend_radius": 0.005,
		"target_pose": [
		
			[
					pose[0],
					pose[1],
					pose[2],
					pose[3],
					pose[4],
					pose[5]
			],
			[
					pose[0] - relative.position.x,
					pose[1] - relative.position.y,
					pose[2] - relative.position.z,
					pose[3],
					pose[4],
					pose[5],
			],
		],
		"current_joint_angles":self.robot.robot_status("jointAngles"),
		}
		self.robot.move_linear(**linear_property)
		self.robot.stop()
	
	async def move(self, v: Vector3, r: Vector3 = Vector3(0, 0, 0), along_normal: bool = False):
		if along_normal:
			a, b = 0, 0
			c = 0 + self.deg2rad(self.customC)
			euler = Euler(a, b, c)
			rot_matrix = euler.to_matrix()
			movement_vector = rot_matrix @ v
		else:
			movement_vector = v
		for _ in range(10):
			await self.start_movement_slider(
				movement_vector.x, movement_vector.y, movement_vector.z,
				r.x, r.y, r.z
			)
			await asyncio.sleep(0.1)
		await self.stop_movement_slider(0, 0, 0, 0, 0, 0)

	def init_lara(self):
		return {
			"robot_name": self.robot.robot_name,
			"dof": self.robot.dof,
			"platform": self.robot.platform,
			"payload": self.robot.payload,
			"kURL": self.robot.kURL,
			"robot_urdf_path": self.robot.robot_urdf_path,
			"current_tool": self.robot.current_tool,
			"connection": self.robot.connection,
			"version": self.robot.version
		}
	
	def send_echo(self, message="Echo received"):
		data_echo = {
			"command": "echo",
			"message": message
		}
		global link
		with connect(link) as websocket:
			websocket.send(json.dumps(data_echo))
			reply = websocket.recv()
			print(f"Echo reply: {reply}")

	def stopMoving(self):
		data_stop_moving = {
			"command": "stopMoving"
		}
		global link
		with connect(link) as websocket:
			websocket.send(json.dumps(data_stop_moving))
			reply = websocket.recv()

	
	def start_moving(self, q0=0, q1=0, q2=0, q3=0, q4=0, q5=0, absrel="Absolute", reference="Base"):
		global link
		data_start_moving = {
			"command": "startMoving",
			"q0": q0,
			"q1": q1,
			"q2": q2,
			"q3": q3,
			"q4": q4,
			"q5": q5,
			"absrel": absrel,
			"reference": reference
		}
		with connect(link) as websocket:
			websocket.send(json.dumps(data_start_moving))
			reply = websocket.recv()

	
if __name__	== "__main__":
	import asyncio
	async def main():
		lara	= Lara()
		print(lara.init_lara())
		await lara.connect_socket()
		await lara.sio.wait()
	asyncio.run(main())