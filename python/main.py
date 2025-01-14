from typing import Dict, Union, Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List
from tray import Tray
from space import Euler, Vector3, Quaternion, Matrix4, Pose
import numpy as np
from lara import Lara
import os
from plunger import Plunger
from scipy.spatial.transform import Rotation as R
import json
import udp_server as udp
import threading
import time 
import logging

# --- Global variables ---

serial_handler = None
json_data = None
udp_server = None
reader_thread = None
json_data_consumed = False
first_data_json = None
stop_event = threading.Event()
lara : Lara = None

logging.getLogger('lara').setLevel(logging.ERROR)

def reader():
    global serial_handler, json_data, json_data_consumed, first_data_json
    serial_handler.write('{"connected": 1}')
    while not stop_event.is_set():
        if serial_handler and not serial_handler.output.empty():
            json_data = serial_handler.output.get()
            if not first_data_json:
                first_data_json = json_data
            json_data_consumed = False
        time.sleep(0.001)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global serial_handler, udp_server, reader_thread, stop_event, lara
    serial_handler = Plunger("COM13", 115200)
    serial_handler.start()
    
    # Start the UDP server
    udp_server = udp.UDPServer(
        ip='localhost',
        port=8765,
        buffer_size=1024,
    )

    #connect to the robot
    lara = Lara()
    await lara.connect_socket()
    print("Connected to the robot")

    # # Start the reader thread
    stop_event.clear()
    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    try:
        yield
    finally:
        # Stop the reader thread and clean up
        stop_event.set()
        if reader_thread:
            reader_thread.join()
        serial_handler.stop()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)



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
    global lara, json_data, threshold, is_paused, force, json_data_consumed, first_data_json
    await websocket.accept()
    #send the first data json to the client
    if first_data_json:
        print("Sending first data json" + str(first_data_json))
        await websocket.send_json(first_data_json)
    while True:
        if not json_data_consumed and json_data is not None:
            json_data["is_paused"] = is_paused
            lara.robot.unpause()
            if "force" in json_data:
                force = float(json_data["force"])
                if force > threshold and lara is not None:
                    lara.robot.pause()
                    is_paused = True
            await websocket.send_json(json_data)
            await asyncio.sleep(0.01)
            json_data_consumed = True

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
    socket_pose = lara.pose
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
    current_pose = lara.pose
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


def rotate_vector(x, y, angle):
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

pose_correct = False

import math
def normalized_rotation_speed(current_yaw, target_yaw):
   """
   Calculate the normalized rotation speed to move a robot arm towards a target yaw.
   Args:
       current_yaw (float): The current yaw angle in radians.
       target_yaw (float): The target yaw angle in radians.
   Returns:
       float: A value between -1 and 1, where:
              -1 indicates full speed clockwise,
               1 indicates full speed counter-clockwise,
               and values closer to 0 indicate proximity to the target angle.
   """
   # Calculate the shortest angle difference normalized to [-π, π]
   angle_difference = math.atan2(math.sin(target_yaw - current_yaw), math.cos(target_yaw - current_yaw))
   # Normalize to range [-1, 1] based on the angle difference
   normalized_speed = angle_difference / math.pi  # Divide by π for scaling
   return normalized_speed

@app.post("/aling_z_axis")
async def aling_z_axis():
    global lara, json_data, udp_server, target_camera_translation
    message = None
    speed = 1  # Initial speed in mm/s
    await lara.setTranslationSpeedMMs(speed)
    await lara.setRotSpeedDegS(100)
    #0.5 x
    counter = 0
    counter2 = 0
    rot_z = 0
    while True:
        counter += 1
        message = udp_server.receive_data()
        if message:
            quat = Quaternion(
                message['0']['quaternion']['x'],
                message['0']['quaternion']['y'],
                message['0']['quaternion']['z'],
                message['0']['quaternion']['w']
            )
            rot_z = quat.to_euler().z
            if rot_z < 0.1 and rot_z > -0.1:
                print(f"rot_z = {rot_z}")
                break
            #bound it either 1 or -1 depending on the sign
            rot_z = 1 if rot_z > 0 else -1
        await lara.start_movement_slider(0, 0, 0, 0, 0, -rot_z)
        await asyncio.sleep(0.05)
        if counter > 100:
            print("rot_z = ", rot_z)
            rot_z = -rot_z
            counter = 0
        counter2 += 1
        if counter2 > 10000:
            break
    await lara.stop_movement_slider(0, 0, 0, 0, 0, 0)


@app.post("/Aling_XY")
async def aling_xy():
    global lara, json_data, udp_server, target_camera_translation
    message = None
    speed = 1
    error = 0.1 / 1000  # 0.1mm
    await lara.setTranslationSpeedMMs(speed)
    await lara.setRotSpeedDegS(100)
    while True:
        message = udp_server.receive_data()
        if message:
            position = Vector3(message["0"]["x"], message["0"]["y"], message["0"]["z"])
            if position.x < error and position.x > -error and position.y < error and position.y > -error:
                break
            # Move the robot towards the target position
            await lara.start_movement_slider(0, 0, 0, 0, 0, 0)
            await asyncio.sleep(0.05)
    await lara.stop_movement_slider(0, 0, 0, 0, 0, 0)
    return {"position": lara.pose.position.to_dict()}


@app.post("/computePose")
async def compute():
   global lara, udp_server
   while True:
        message = udp_server.receive_data()
        if not message:
            continue
        # 1) Build the detected pose (tag in camera frame) from the data
        position = Vector3(
            message["0"]["x"],
            message["0"]["y"],
            message["0"]["z"]
        )
        quaternion = Quaternion(
            message["0"]["quaternion"]["x"],
            message["0"]["quaternion"]["y"],
            message["0"]["quaternion"]["z"],
            message["0"]["quaternion"]["w"]
        )
        detected_pose = Pose(position, quaternion)
        # 2) Camera offset pose
        offset_camera_pose = Pose(
            position=Vector3(0, 0, 0),
            orientation=Quaternion(0, 0, 0, 1)
        )
        # 3) Current robot pose in the world
        lara_global_pose = lara.pose
        # ---- Convert to 4x4 transforms ----
        T_robot_world   = Matrix4.from_pose(lara_global_pose)    # Robot in world
        T_camera_robot  = Matrix4.from_pose(offset_camera_pose)   # Camera in robot
        T_tag_camera    = Matrix4.from_pose(detected_pose)        # Tag in camera
        # 4) Compute T_tag_world
        T_tag_world = T_robot_world * T_camera_robot * T_tag_camera
        # 5) For a simple “align” scenario, let’s say we want the end-effector exactly where the tag is
        T_robot_world_desired = T_tag_world
        # 6) Compute the delta transform from the robot’s current pose to the desired
        T_delta = T_robot_world.inverse() * T_robot_world_desired
        # 7) Extract the translation + rotation from T_delta
        delta_q, delta_t = T_delta.to_quaternion_translation()
        # Custom offset 
        Offset = Euler(0.0, 0.0, Euler.to_rad(-24)).to_quaternion()
        delta_t = delta_t.rotate(Offset)
        delta_euler = delta_q.to_euler(order='xyz')
        # Convert radians to degrees 
        delta_rx_deg = np.degrees(delta_euler.x)
        delta_ry_deg = np.degrees(delta_euler.y)
        delta_rz_deg = np.degrees(delta_euler.z)
        p = {
            "x": delta_t.x * 1000,
            "y": delta_t.y * 1000,
            "z": delta_t.z * 1000,
            "rx": delta_rx_deg,
            "ry": delta_ry_deg,
            "rz": delta_rz_deg
        }
        return p

@app.post("/moveToCell")
def move_to_cell(row: int = 0, col: int = 0):
    global lara, socket_pose, json_data
    lara.move_to_pose(tray.get_cell_robot_orientation(row, col))

@app.post("/moveToSocket")
def move_to_socket():
    global lara, socket_pose, json_data
    lara.move_to_pose(socket_pose)


@app.post("/moveUntilPressure")
async def move_until_pressure(pressure: float = 1000.0, wiggle_room: float = 300.0):
    global lara, json_data, threshold, force, is_paused
    start_position = lara.pose.position # Store the start position
    await lara.setTranslationSpeedMMs(0.5)
    move_z = -1 # Direction to move in
    MAX_DEPTH = 0.010 # 10mm or 0.01m
    # Move the robot down until the force exceeds the threshold or the maximum depth is reached
    print(f"Starting move, start height: {lara.pose.position.z * 1000} mm")
    for i in range(1000):
        print(f"height: {lara.pose.position.z * 1000} mm")
        if lara.pose.position.z - start_position.z < -MAX_DEPTH:
            break
        # check if the force exceeds the threshold
        if force > pressure + wiggle_room:
            break
        if json_data is not None:
            if "force" in json_data:
                force = float(json_data["force"])
                print(f"Current force: {force}")
                if force > pressure + wiggle_room:
                    print(f"Force {force} exceeds pressure {pressure} + wiggle_room {wiggle_room}. Breaking loop.")
                    break
        await lara.start_movement_slider(0, 0, move_z, 0, 0, 0)
        await asyncio.sleep(0.01)
        if i == 999:
            await lara.stop_movement_slider(0, 0, 0, 0, 0, 0)
            return {"error": "Force did not exceed threshold within 1000 iterations."}
    # counter = 10
    # for i in range(1000):
    #     print(f"Second loop iteration {i+1}/100")
    #     if json_data is not None:
    #         if "force" in json_data:
    #             force = float(json_data["force"])
    #             print(f"Current force: {force}")
    #             if force > pressure + wiggle_room:
    #                 move_z = 0.3
    #                 counter = 10
    #                 print(f"Force {force} > pressure + wiggle_room. Setting move_z to {move_z} and resetting counter.")
    #                 await lara.start_movement_slider(0, 0, move_z, 0, 0, 0)
    #             elif force < pressure - wiggle_room:
    #                 move_z = -0.3
    #                 counter = 10
    #                 print(f"Force {force} < pressure - wiggle_room. Setting move_z to {move_z} and resetting counter.")
    #                 await lara.start_movement_slider(0, 0, move_z, 0, 0, 0)
    #             else:
    #                 counter -= 1
    #                 print(f"Force within wiggle room. Decrementing counter to {counter}")
    #                 if counter == 0:
    #                     print("Counter reached zero. Exiting loop.")
    #                     break
    #         await asyncio.sleep(0.01)
    await lara.stop_movement_slider(0, 0, 0, 0, 0, 0)
    print("Stopped all movements.")
@app.post("/EmergencyStop")
def emergency_stop():
    global lara
    lara.robot.power('off')

@app.post("/togglePump")
def toggle_pump(boolean : bool):
    global serial_handler
    serial_handler.write(f'{{"pump": {100 if boolean else 0}}}')
    return {"pump": 100 if boolean else 0}

class LedStateModel(BaseModel):
    leds: List[int]  # or List[bool], depending on your usage

@app.post("/setLeds")
def set_leds(led_data: LedStateModel):
    """
    Just sets the LED states in one shot.
    Example payload:
    {
      "leds": [1, 0, 1, 1, 0, 1, 0]
    }
    """
    payload = {"leds": led_data.leds}
    serial_handler.write(json.dumps(payload))  # Chuck it to the microcontroller
    return payload

@app.get("/orientation_data")
def get_orientation_data():
    global lara
    orientation = lara.pose.orientation.to_euler().to_dict(degrees=True)
    return orientation


@app.post("/get_camera_data")
def get_camera_data():
    global udp_server
    data = udp_server.receive_data()
    return {"data": data}

@app.post("/setBrightness")
def set_brightness(newBrightness : int):
    global serial_handler
    serial_handler.write(f'{{"brightness": {newBrightness}}}')
    return {"brightness": newBrightness}

@app.post("/setHSL")
def set_hsl(hue : float, sat : float, light : float):
    global serial_handler
    serial_handler.write(f'{{"hue": {hue}, "sat": {sat}, "light": {light}}}')
    return {"hue": hue, "sat": sat, "light": light}

@app.post("/setHeater")
def setHeater(newHeat : int):
    global serial_handler
    serial_handler.write(f'{{"setTemp": {newHeat}}}')
    return {"setTemp": newHeat}


@app.post("/TurnJogOff")
def turn_jog_off():
    global lara
    lara.robot.turn_off_jog()

if __name__ == "__main__":
    import uvicorn
    import threading
    uvicorn.run(app, host="localhost", port=1442)
 