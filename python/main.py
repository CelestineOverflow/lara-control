from typing import Dict, Union, Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List
from tray import Tray
from space import Euler, Vector3, Vector2, Quaternion, PoseCartesian, Pose
import numpy as np
from lara import Lara
import os
from plunger import Plunger
from scipy.spatial.transform import Rotation as R
import json
import udp_server as udp
import time 

serial_handler = None
json_data = None
udp_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global serial_handler, udp_server
    serial_handler = Plunger("COM13", 115200)
    serial_handler.start()
    # Start the UDP server+
    udp_server = udp.UDPServer(
        ip='localhost',
        port=8765,
        buffer_size=1024,
    )
    yield
    # Clean up the 
    serial_handler.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

lara = Lara()

robotJoints = {
    "joint1": 0,
    "joint2": 0,
    "joint3": 0,
    "joint4": 0,
    "joint5": 0,
    "joint6": 0,
    "x": 0,
    "y": 0,
    "z": 0,
    "a": 0,
    "b": 0,
    "c": 0,
}

class RobotJointsModel(BaseModel):
    joint1: float
    joint2: float
    joint3: float
    joint4: float
    joint5: float
    joint6: float

class RobotCartesianModel(BaseModel):
    x: float
    y: float
    z: float
    a: float
    b: float
    c: float

class GenerateTrayRequest(BaseModel):
    offset_x: Optional[float] = 0.0
    offset_y: Optional[float] = 0.0
    offset_z: Optional[float] = 0.0

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

is_paused = False
threshold = 3000.0
force = 0.0
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global lara, serial_handler, json_data, threshold, is_paused, force
    await websocket.accept()
    while True:
        if not serial_handler.output.empty():
            json_data = serial_handler.output.get()
            #add field to json_data to indicate if the robot is paused
            json_data["is_paused"] = is_paused
            if "force" in json_data:
                force = float(json_data["force"])
                if force > threshold:
                    lara.robot.pause()
                    is_paused = True
            await websocket.send_json(json_data)
        await asyncio.sleep(0.1)


@app.post("/setPause")
def set_pause(pause: bool):
    print("Setting pause to", pause)
    global lara, is_paused
    if pause:
        lara.robot.pause()
    else:
        lara.robot.unpause()
    is_paused = pause
    return {"is_paused": is_paused}
@app.post("/changeMode")
def change_mode(mode: str):
    global lara
    mode = mode.lower()
    if mode == "teach":
        lara.robot.set_mode("Teach")
    elif mode == "semiautomatic":
        lara.robot.set_mode("SemiAutomatic")
    elif mode == "automatic":
        lara.robot.set_mode("Automatic")
    else:
        return {"error": "Invalid mode"}
    return {"mode": lara.robot.get_mode()}
@app.get("/mode")
def get_mode():
    global lara
    return {"mode": lara.robot.get_mode()}
@app.post("/resetRobot")
def reset_robot():
    global lara
    lara.robot.reset_error()
@app.get("/sim_or_emulation")
def sim_or_emulation():
    global lara
    return {"context": lara.robot.get_sim_or_real()}
@app.post("/set_sim_or_emulation")
def set_sim_or_emulation(mode: str):
    global lara
    lara.robot.set_sim_real(mode)
    return {"context": lara.robot.get_sim_or_real()}

@app.post("/pose")
def pose(pose: RobotJointsModel):
    global lara
    joint_property = {
        "speed": 50.0,
        "acceleration": 50.0,
        "safety_toggle": True,
        "target_joint": [
            pose.joint1, pose.joint2, pose.joint3, pose.joint4, pose.joint5, pose.joint6
        ],
        "current_joint_angles": lara.robot.robot_status("jointAngles")
    }
    lara.robot.move_joint(**joint_property)
    return lara.robot.robot_status("jointAngles")

@app.post("/sendPoseArray")
def sendPoseArray(poses: List[RobotJointsModel]):
    global lara
    joint_property = {
        "speed": 50.0,
        "acceleration": 50.0,
        "safety_toggle": True,
        "target_joint": [pose for pose in poses],
        "current_joint_angles": lara.robot.robot_status("jointAngles")
    }
    print(joint_property)
    lara.robot.move_joint(**joint_property)
    return lara.robot.robot_status("jointAngles")

@app.post("/sendCartesianPoseArray")
def sendCartesianPoseArray(
    speed: float,
    acceleration: float,
    poses: List[RobotCartesianModel]
):
    global lara
    lara.robot.set_mode("Automatic")
    linear_property = {
        "speed": speed,
        "acceleration": acceleration,
        "blend_radius": 0.005,
        "target_pose": [
            [pose.x, pose.y, pose.z, pose.a, pose.b, pose.c] for pose in poses
        ],
        "current_joint_angles": lara.robot.robot_status("jointAngles"),
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

    lara.robot.move_linear(**linear_property)
    lara.robot.stop()
    lara.robot.set_mode("Teach")
    return lara.robot.robot_status("jointAngles")


tray = None
socket_pose = None
#try to load tray and socket pose from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        if "socket_pose" in config:
            socket_pose = Pose.from_json(config["socket_pose"])
            print("Loaded socket pose from config.json")
        if "tray" in config:
            tray = Tray.from_dict(config["tray"])
            print("Loaded tray from config.json")
except FileNotFoundError:
    pass
except json.JSONDecodeError:
    print("Invalid JSON in config.json")

@app.post("/setSocket")
def set_socket():
    global lara, socket_pose, udp_server
    socket_pose = lara.get_pose()
    # Read existing config or initialize empty
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    # Update the socket_pose
    config["socket_pose"] = socket_pose.to_dict()

    message = udp_server.receive_data()
    if message:
        print(f"Message from queue: {message}")
        config["socket_tag_pose"] = message
    # Write the updated config back to the file
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    return socket_pose

@app.post("/setTray")
def set_tray():
    global lara, tray
    current_pose = lara.get_pose()
    tray = Tray(pose=current_pose)
    # Read existing config or initialize empty
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}
    # Update the tray
    config["tray"] = tray.to_dict()

    # Write the updated config back to the file
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)        
    return tray.get_cell_positions()

@app.get("/getTray")
def get_tray():
    global tray
    return tray.get_cell_positions()


@app.post("/getOrientation")
def get_orientation():
    global lara
    return lara.get_pose().to_dict()


def rotate_vector(x, y, angle):
    angle = np.deg2rad(angle)
    x_new = x * np.cos(angle) - y * np.sin(angle)
    y_new = x * np.sin(angle) + y * np.cos(angle)
    return x_new, y_new

def current_milli_time():
    return round(time.time() * 1000)

target_camera_translation = Vector3(-0.00033, -0.0033, 0)

# Try to load target_camera_translation from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        if "target_camera_translation" in config:
            tct = config["target_camera_translation"]
            target_camera_translation = Vector3(tct["x"], tct["y"], tct["z"])
            print("Loaded target_camera_translation from config.json")
        else:
            print("Using default target_camera_translation")
except FileNotFoundError:
    print("config.json not found. Using default target_camera_translation")
except json.JSONDecodeError:
    print("Invalid JSON in config.json. Using default target_camera_translation")

@app.post("/setTarget")
def set_target():
    global target_camera_translation, udp_server
    message = udp_server.receive_data()
    if message:
        target_camera_translation = Vector3(-message["0"]["x"], -message["0"]["y"], 0)
        print(f"Target camera translation: {target_camera_translation}")
        # Read existing config or initialize empty
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    config = {}
        else:
            config = {}
        # Update the target_camera_translation
        config["target_camera_translation"] = {
            "x": target_camera_translation.x,
            "y": target_camera_translation.y,
            "z": target_camera_translation.z
        }
        # Write the updated config back to the file
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    return target_camera_translation.to_dict()

@app.post("/moveToTag")
async def move_to_tag_jog():
    global lara, json_data, udp_server, target_camera_translation
    message = None
    pose_correct = False
    current_camera_translation = Vector3(0, 0, 0)
    distance = 0.00005
    current_speed = 0.05 # m/s
    timeout_ms = 100
    await lara.set_translation_speed(current_speed)
    async def send_jog_commands():
        start_time = current_milli_time()
        while not pose_correct:
            lara.robot.jog(set_jogging_external_flag=1)
            await asyncio.sleep(0.0001)
            if current_milli_time() - start_time > timeout_ms and not message:
                break
            else:
                start_time = current_milli_time()
    jog_task = None
    while not pose_correct:
        message = udp_server.receive_data()
        if message:
            try:
                current_camera_translation = Vector3(message["0"]["x"], message["0"]["y"], 0)
                z_height = message["0"]["z"]
                movement = target_camera_translation + current_camera_translation
                current_distance = movement.magnitude()
                if current_distance < 0.01 and current_speed > 0.01:
                    current_speed = 0.01
                    await lara.set_translation_speed(current_speed)
                if current_distance < 0.005 and current_speed > 0.001:
                    current_speed = 0.001
                    await lara.set_translation_speed(current_speed)
                if current_distance < 0.002 and current_speed > 0.0005 and z_height < 0.039:
                    current_speed = 0.0005
                    timeout_ms = 1
                    await lara.set_translation_speed(current_speed)
                if current_distance < distance and z_height < 0.039:
                    pose_correct = True
                    lara.robot.turn_off_jog()
                    break
                print(f"Current speed: {current_speed * 1000} mm/s, Current distance: {current_distance * 1000} mm, Z: {z_height}")
                if not jog_task:
                    jog_task = asyncio.create_task(send_jog_commands())
                if jog_task.done():
                    jog_task = asyncio.create_task(send_jog_commands())
                x, y = rotate_vector(movement.x, movement.y, -message["0"]["yaw"] * np.pi / 180)
                if z_height > 0.039 and abs(x) < 0.001 and abs(y) < 0.001:
                    x = 0
                    y = 0
                    z = 0.1
                else:
                    x *= 1000
                    y *= 1000
                    z = 0
                lara.robot.turn_on_jog(
                    jog_velocity=[min(max(x, -1), 1), min(max(y, -1), 1), -z, 0, 0, -message["0"]["yaw"] * np.pi / 180],
                    jog_type='Cartesian'
                )
            except Exception as e:
                print(e)
        await asyncio.sleep(0.01)
    if jog_task:
        jog_task.cancel()
    lara.robot.turn_off_jog()
    return lara.robot.robot_status("jointAngles")

@app.post("/moveToCell")
def move_to_cell(row: int = 0, col: int = 0, speed: float = 0.1, acceleration: float = 0.01):
    global lara, socket_pose, json_data
    move_to_pose(tray.get_cell_robot_orientation(row, col))

@app.post("/moveToSocket")
def move_to_socket():
    global lara, socket_pose, json_data
    move_to_pose(socket_pose)

@app.post("/moveToSocketTracked")
def move_to_socket_tracked():
    global lara, socket_pose, json_data
    hover_pose(socket_pose, offset=-0.2)    
    move_to_tag()
    current_pose = lara.get_pose()

    move_to_relative(Pose(
        position=Vector3(
            x=current_pose.position.x,
            y=current_pose.position.y,
            z=current_pose.position.z - 0.1
        ),
        orientation=current_pose.orientation
    ))
    move_to_tag()
    current_pose = lara.get_pose()
    move_to_relative(Pose(
        position=Vector3(
            x=current_pose.position.x,
            y=current_pose.position.y,
            z=current_pose.position.z - 0.075
        ),
        orientation=current_pose.orientation
    ))
    move_to_tag()
    current_pose = lara.get_pose()
    move_to_relative(Pose(
        position=Vector3(
            x=current_pose.position.x,
            y=current_pose.position.y,
            z=current_pose.position.z - 0.01
        ),
        orientation=current_pose.orientation
    ))
    move_to_tag()
    current_pose = lara.get_pose()
    move_to_relative(Pose(
        position=Vector3(
            x=current_pose.position.x,
            y=current_pose.position.y,
            z=current_pose.position.z - 0.01
        ),
        orientation=current_pose.orientation
    ))
    move_to_tag()

def to_degrees(radians):
    return radians * 180 / np.pi

def hover_pose(targePose : Pose, offset = -0.3):
    global lara, json_data
    # get the current arm position
    current_pose = lara.get_pose()
    current_pose_orientation_euler = current_pose.orientation.to_euler(order="xyz")
    print(f"Current Orientation Euler:  a: {to_degrees(current_pose_orientation_euler.z)}, b: {to_degrees(current_pose_orientation_euler.y)}, c: {to_degrees(current_pose_orientation_euler.x)}")
    # create steps
    steps = []
    # first step is the current position
    steps.append(PoseCartesian(position=current_pose.position, orientation=current_pose.orientation.to_euler(order="xyz")))
    print(f"P1: {current_pose.position.x}, {current_pose.position.y}, {current_pose.position.z}, {to_degrees(current_pose_orientation_euler.x)}, {to_degrees(current_pose_orientation_euler.y)}, {to_degrees(current_pose_orientation_euler.z)}")
    offset = np.array([0, 0, offset])
    original_form_matrix = R.from_euler("xyz", [current_pose_orientation_euler.z, current_pose_orientation_euler.y, current_pose_orientation_euler.x]).as_matrix()
    offset_t = original_form_matrix @ offset
    new_position = Vector3(
        current_pose.position.x + offset_t[0],
        current_pose.position.y + offset_t[1],
        current_pose.position.z + offset_t[2]
    )
    # second step is the current position + offset
    steps.append(PoseCartesian(position=new_position, orientation=current_pose.orientation.to_euler(order="xyz")))
    # third step is target position + offset
    target_position = targePose.position
    target_orientation = targePose.orientation.to_euler(order="xyz")
    target_orientation_matrix = R.from_euler("xyz", [target_orientation.z, target_orientation.y, target_orientation.x]).as_matrix()
    offset_t = target_orientation_matrix @ offset
    new_position = Vector3(
        target_position.x + offset_t[0],
        target_position.y + offset_t[1],
        target_position.z + offset_t[2]
    )
    steps.append(PoseCartesian(position=new_position, orientation=target_orientation))
    lara.robot.set_mode("Automatic")
    linear_property = {
        "speed": 0.1,
        "acceleration": 0.01,
        "blend_radius": 0.005,
        "target_pose": [
            [step.position.x, step.position.y, step.position.z, step.orientation.z, step.orientation.y, step.orientation.x] for step in steps
        ],
        "current_joint_angles": lara.robot.robot_status("jointAngles"),
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
    
    lara.robot.move_linear(**linear_property)
    lara.robot.stop()
    lara.robot.set_mode("Teach")
    return lara.robot.robot_status("jointAngles")

def move_to_pose(targePose : Pose):
    global lara, json_data
    # get the current arm position
    current_pose = lara.get_pose()
    current_pose_orientation_euler = current_pose.orientation.to_euler(order="xyz")
    print(f"Current Orientation Euler:  a: {to_degrees(current_pose_orientation_euler.z)}, b: {to_degrees(current_pose_orientation_euler.y)}, c: {to_degrees(current_pose_orientation_euler.x)}")
    # create steps
    steps = []
    # first step is the current position
    steps.append(PoseCartesian(position=current_pose.position, orientation=current_pose.orientation.to_euler(order="xyz")))
    print(f"P1: {current_pose.position.x}, {current_pose.position.y}, {current_pose.position.z}, {to_degrees(current_pose_orientation_euler.x)}, {to_degrees(current_pose_orientation_euler.y)}, {to_degrees(current_pose_orientation_euler.z)}")
    offset = np.array([0, 0, -.3])
    original_form_matrix = R.from_euler("xyz", [current_pose_orientation_euler.z, current_pose_orientation_euler.y, current_pose_orientation_euler.x]).as_matrix()
    offset_t = original_form_matrix @ offset
    new_position = Vector3(
        current_pose.position.x + offset_t[0],
        current_pose.position.y + offset_t[1],
        current_pose.position.z + offset_t[2]
    )
    # second step is the current position + offset
    steps.append(PoseCartesian(position=new_position, orientation=current_pose.orientation.to_euler(order="xyz")))
    # third step is target position + offset
    target_position = targePose.position
    target_orientation = targePose.orientation.to_euler(order="xyz")
    target_orientation_matrix = R.from_euler("xyz", [target_orientation.z, target_orientation.y, target_orientation.x]).as_matrix()
    offset_t = target_orientation_matrix @ offset
    new_position = Vector3(
        target_position.x + offset_t[0],
        target_position.y + offset_t[1],
        target_position.z + offset_t[2]
    )
    steps.append(PoseCartesian(position=new_position, orientation=target_orientation))
    # fourth step is the target position
    steps.append(PoseCartesian(position=target_position, orientation=target_orientation))
    lara.robot.set_mode("Automatic")
    linear_property = {
        "speed": 0.1,
        "acceleration": 0.01,
        "blend_radius": 0.005,
        "target_pose": [
            [step.position.x, step.position.y, step.position.z, step.orientation.z, step.orientation.y, step.orientation.x] for step in steps
        ],
        "current_joint_angles": lara.robot.robot_status("jointAngles"),
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
    
    lara.robot.move_linear(**linear_property)
    lara.robot.stop()
    lara.robot.set_mode("Teach")
    return lara.robot.robot_status("jointAngles")

def move_to_relative(targePose : Pose):
    global lara, json_data
    # get the current arm position
    current_pose = lara.get_pose()
    current_pose_orientation_euler = current_pose.orientation.to_euler(order="xyz")
    print(f"Current Orientation Euler:  a: {to_degrees(current_pose_orientation_euler.z)}, b: {to_degrees(current_pose_orientation_euler.y)}, c: {to_degrees(current_pose_orientation_euler.x)}")
    # create steps
    steps = []
    steps.append(PoseCartesian(position=current_pose.position, orientation=current_pose.orientation.to_euler(order="xyz")))
    steps.append(PoseCartesian(position= targePose.position, orientation=targePose.orientation.to_euler(order="xyz")))
    lara.robot.set_mode("Automatic")
    linear_property = {
        "speed": 0.1,
        "acceleration": 0.01,
        "blend_radius": 0.005,
        "target_pose": [
            [step.position.x, step.position.y, step.position.z, step.orientation.z, step.orientation.y, step.orientation.x] for step in steps
        ],
        "current_joint_angles": lara.robot.robot_status("jointAngles"),
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
    
    lara.robot.move_linear(**linear_property)
    lara.robot.stop()
    lara.robot.set_mode("Teach")
    return lara.robot.robot_status("jointAngles")

@app.post("/set_jogging_speed")
async def set_jogging_speed(speed: float):
    global lara
    await lara.set_translation_speed(speed)

MAX_SPEED = 0.01  # Maximum allowable speed
DIRECTION = -1  # 1 for up, -1 for down

@app.post("/moveUntilPressure")
async def move_until_pressure(pressure: float = 1000.0, Kp: float = 0.00001, wiggle_room: float = 300.0):
    print(f"Pressure: {pressure}, Kp: {Kp}")
    global lara, DIRECTION
    i = 0
    consecutive_within_wiggle = 0
    while i < 1000:
        if not serial_handler.output.empty():
            json_data = serial_handler.output.get()
            #add field to json_data to indicate if the robot is paused
            json_data["is_paused"] = is_paused
            if "force" in json_data:
                force = float(json_data["force"])
                error = pressure - force
                speed = Kp * error
                speed = max(min(speed, MAX_SPEED), -MAX_SPEED)
                speed *= DIRECTION
                # Check if the force is within the wiggle room
                if abs(error) <= wiggle_room:
                    consecutive_within_wiggle += 1
                    if consecutive_within_wiggle >= 20:
                        lara.robot.turn_off_jog()
                        break
                else:
                    consecutive_within_wiggle = 0
                    # Update jog velocity
                    lara.robot.turn_off_jog()
                    lara.robot.turn_on_jog(
                        jog_velocity=[0, 0, speed, 0, 0, 0],
                        jog_type='Cartesian'
                    )
                    print(f"Force: {force}, Speed: {speed}")
                    lara.robot.jog(set_jogging_external_flag=1)
                    i += 1
                    await asyncio.sleep(0.01)
    lara.robot.turn_off_jog()
    return {"force": force, "i": i} 
    
@app.post("/EmergencyStop")
def emergency_stop():
    global lara
    lara.robot.power('off')

@app.post("/togglePump")
def toggle_pump(boolean : bool):
    global serial_handler
    serial_handler.write(f'{{"pump": {100 if boolean else 0}}}')
    return {"pump": 100 if boolean else 0}

@app.post("/get_camera_data")
def get_camera_data():
    global udp_server
    data = udp_server.receive_data()
    return {"data": data}

@app.post("/setBrightness")
def toggle_pump(newBrightness : int):
    global serial_handler
    serial_handler.write(f'{{"brightness": {newBrightness}}}')
    return {"brightness": newBrightness}

@app.post("/setHeater")
def toggle_pump(newHeat : int):
    global serial_handler
    serial_handler.write(f'{{"heater": {newHeat}}}')
    return {"heater": newHeat}


@app.post("/TurnJogOff")
def turn_jog_off():
    global lara
    lara.robot.turn_off_jog()

if __name__ == "__main__":
    import uvicorn
    import threading
    uvicorn.run(app, host="localhost", port=1442)
 