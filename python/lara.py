import aiohttp
import asyncio
import socketio
import logging
import time
import numpy as np
from scipy.spatial.transform import	Rotation as R
from neura.neurapy.robot import	Robot
from space import Pose,	Vector3, Quaternion, Euler,	PoseCartesian

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)

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
		self.sio.on('heartbeat_check', self.send_hearbeat)
		self.max_rotation_speed = 0.2617994	# rad/s
		self.max_translation_speed =	0.25	# m/s
		self.pose: Pose = Pose(Vector3(0, 0, 0),	Quaternion(0, 0, 0, 1))
		# For tracking heartbeats & slider calls
		self.last_slider_call = 0.0
		self.heartbeat_task = None
		self.heartbeat_running =	False
		self.cartesian_slider_data =	{}
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
	async def connect_socket(self):
		if not self.sio.connected:
			await self.sio.connect('http://192.168.2.13:8081')
	async def on_connect(self):
		print('connection established')
	async def on_disconnect(self):
		print('disconnected from	server')
	async def send_hearbeat(self, *args):
		"""Send a single	heartbeat."""
		print("Sending heartbeat.")
		await self.sio.emit("heartbeat_response", True)
	async def run_heartbeats_in_background(self):
		"""Background task that sends a heartbeat every 1 second
		as long as slider calls keep	coming in <0.5s	intervals."""
		self.heartbeat_running =	True
		print("Heartbeat	background task	started.")
		try:
			while True:
				# Sleep 1 second	between	heartbeats
				await asyncio.sleep(.7)
				# If there's	been a gap >= 0.5s since the last slider call, stop
				if (time.time() - self.last_slider_call)	>= 0.5:
					print("Slider gap >= 0.5s, stopping heartbeat.")
					break
				# Otherwise,	send a heartbeat
				await self.send_hearbeat()
		finally:
			self.heartbeat_running =	False
			print("Heartbeat	background task	stopped.")
	
	def deg2rad(self, deg):
		return deg *	0.0174533
	async def set_translation_speed(self, speed):
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
		await self.sio.emit("linearveltrigger", {"data":	True})
		await asyncio.sleep(0.5)
	
	async def set_rotation_speed(self, speed):
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
		await self.sio.emit("rotationalveltrigger", {"data":	True})
	async def setRotSpeedDegS(self, deg_s):
		rotational_speed	= (deg_s / 180)	* self.max_rotation_speed
		print(f"Setting rotational speed	to {rotational_speed} rad/s	or {deg_s} deg/s")
		await self.set_rotation_speed(rotational_speed)
	async def setTranslationSpeedMMs(self, mm_s):
		linear_speed	= (mm_s	/ 1000)	* self.max_translation_speed
		print(f"Setting translation speed to {linear_speed} m/s or {mm_s} mm/s")
		await self.set_translation_speed(linear_speed)
	async def start_movement_slider(self, q0, q1, q2, q3, q4, q5):
		"""
		Called roughly every	0.5s to move the slider.
		We update the last_slider_call time here	to let
		our background task know	we are still active.
		"""
		self.last_slider_call = time.time()	# track	the	call time
		data= {
		'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
		'status': True, 'joint':	False, 'cartesian':	True, 'freedrive': False,
		'button': False,	'slider': True,	'goto':	False, 'threeD': False,
		'reference':	"Base",	'absrel': "Absolute",
		}
		await self.sio.emit('CartesianSlider', data)
		
	async def stop_movement_slider(self,	q0,	q1,	q2,	q3,	q4,	q5):
		data	= {
			'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
			'status': False,	'joint': False,	'cartesian': True, 'freedrive':	False,
			'button': False,	'slider': True,	'goto':	False, 'threeD': False,
			'reference':	"Base",	'absrel': "Absolute",
		}
		await self.sio.emit('CartesianSlider', data)
	def move_to_pose(self, pose: Pose):
        # First step: use the current pose
		steps = []
		steps.append(PoseCartesian(position=self.pose.position, orientation=self.pose.orientation.to_euler(order="xyz")))

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
		self.robot.set_mode("Automatic")
		linear_property = {
			"speed": 0.1,
			"acceleration": 0.01,
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
		self.robot.move_linear(**linear_property)
		self.robot.stop()
		self.robot.set_mode("Teach")
		return self.robot.robot_status("jointAngles")
	
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

if __name__	== "__main__":
	import asyncio
	async def main():
		lara	= Lara()
		print(lara.init_lara())
		await lara.connect_socket()
		await lara.sio.wait()
	asyncio.run(main())