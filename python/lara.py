from neura.neurapy.robot import Robot
from space import Pose, Vector3, Quaternion, Euler
import aiohttp
import asyncio
import socketio
import logging



logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)

class Lara:
    def __init__(self):
        self.robot = Robot()
        self.joints = {
            "joint1": 0,
            "joint2": 0,
            "joint3": 0,
            "joint4": 0,
            "joint5": 0,
            "joint6": 0,
        }
        self.vector = Vector3(0, 0, 0)
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.max_rotation_speed = 0.2617994  # rad/s
        self.max_translation_speed = 0.25    # m/s
        self.customC = 60

    async def connect_socket(self):
        if not self.sio.connected:
            await self.sio.connect('http://192.168.2.13:8081')

    async def on_connect(self):
        print('connection established')

    async def on_disconnect(self):
        print('disconnected from server')

    def deg2rad(self, deg):
        return deg * 0.0174533

    async def set_translation_speed(self, speed):
        if speed > self.max_translation_speed:
            speed = self.max_translation_speed
            print("Speed is too high, setting to 0.25")
        elif speed < 0:
            print("Speed cannot be negative, setting to 0")
            speed = 0
        await self.connect_socket()
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                "http://192.168.2.13:8081/api/cartesian",
                headers={"Content-Type": "application/json"},
                json={"linearVelocity": speed}
            ) as response:
                logging.info(await response.text())
        await self.sio.emit("linearveltrigger", {"data": True})

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
                headers={"Content-Type": "application/json"},
                json={"rotationSpeed": speed}
            ) as response:
                logging.info(await response.text())
        await self.sio.emit("rotationalveltrigger", {"data": True})

    async def setRotSpeedDegS(self, deg_s):
        rotational_speed = (deg_s / 180) * self.max_rotation_speed
        print(f"Setting rotational speed to {rotational_speed} rad/s or {deg_s} deg/s")
        await self.set_rotation_speed(rotational_speed)

    async def setTranslationSpeedMMs(self, mm_s):
        linear_speed = (mm_s / 1000) * self.max_translation_speed
        print(f"Setting translation speed to {linear_speed} m/s or {mm_s} mm/s")
        await self.set_translation_speed(linear_speed)

    async def start_movement_slider(self, q0, q1, q2, q3, q4, q5):
        data = {
            'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
            'status': True, 'joint': False, 'cartesian': True, 'freedrive': False,
            'button': False, 'slider': True, 'goto': False, 'threeD': False,
            'reference': "Base", 'absrel': "Absolute",
        }
        await self.sio.emit('CartesianSlider', data)

    async def stop_movement_slider(self, q0, q1, q2, q3, q4, q5):
        data = {
            'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
            'status': False, 'joint': False, 'cartesian': True, 'freedrive': False,
            'button': False, 'slider': True, 'goto': False, 'threeD': False,
            'reference': "Base", 'absrel': "Absolute",
        }
        await self.sio.emit('CartesianSlider', data)


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

    def get_pose(self) -> Pose:
        pose = self.robot.robot_status("cartesianPosition")
        position = Vector3(pose[0], pose[1], pose[2])
        orientation = Quaternion(pose[6], pose[5], pose[4], pose[3])
        return Pose(position, orientation)