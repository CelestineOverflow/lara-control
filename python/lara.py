from neura.neurapy.robot import Robot
from space import Pose, Vector3, Quaternion
import aiohttp
import asyncio
import socketio
import logging


#pip install python-socketio==4.*

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

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
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)

    async def on_connect(self):
        print('connection established')

    async def on_disconnect(self):
        print('disconnected from server')

    async def set_translation_speed(self, speed):
        if speed > 0.25:
            speed = 0.25
            print("Speed is too high, setting to 0.25")
        elif speed < 0:
            print("Speed cannot be negative, setting to 0")
            speed = 0
        if not self.sio.connected:
            await self.sio.connect('http://192.168.2.13:8081')
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                "http://192.168.2.13:8081/api/cartesian",
                headers={"Content-Type": "application/json"},
                json={"linearVelocity": speed}
            ) as response:
                print(await response.text())
                await self.sio.emit("linearveltrigger", {"data": True})

    async def set_rotation_speed(self, speed):
        if speed > 0.2617994: # radians per second
            speed = 0.2617994
            print("Speed is too high, setting to 0.2617994")
        elif speed < 0:
            print("Speed cannot be negative, setting to 0")
            speed = 0
        if not self.sio.connected:
            await self.sio.connect('http://192.168.2.13:8081')
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                "http://192.168.2.13:8081/api/cartesian",
                headers={"Content-Type": "application/json"},
                json={"rotationSpeed": speed}
            ) as response:
                print(await response.text())
                await self.sio.emit("rotationalveltrigger", {"data": True})
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
        pose = Pose(position, orientation)
        return pose