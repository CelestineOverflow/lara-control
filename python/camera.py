
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import numpy as np	
import scipy as sp
import json, math
from pupil_apriltags import Detector
from mjpeg_streamer import MjpegServer, Stream
import socket
from websockets.sync.client import connect
import threading
import queue



def getAvailibleCameras():
    available_cameras = []
    for i in range(10):
        try:
            camera = cv2.VideoCapture(i)
            if camera.isOpened():
                print("Camera index:", i)
                camera.release()
                available_cameras.append(i)
        except:
            pass
    return available_cameras

at_detector = Detector(
        families="tag36h11",
        nthreads=1,
        quad_decimate=4.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
)

# Load Calibration File

mtx = None
dist = None

def load_calibration_file(calibration_file_path):
    global mtx, dist
    #reconstruct the camera matrix and distortion coefficients
    with open(calibration_file_path, 'r') as infile:
        reconstruction = json.load(infile)
        mtx = np.array(reconstruction['mtx'])
        dist = np.array(reconstruction['dist'])
        fx, fy, cx, cy = mtx[0,0], mtx[1,1], mtx[0,2], mtx[1,2]
        mtx = [fx, fy, cx, cy]



camera_indices = [0, 1, 2]
current_camera_index = 0
calibration_path = r'C:\Labhandler\cobot\python\computer_vision\calibration_data.json'
calibration_path_2 = r'C:\Labhandler\cobot\python\computer_vision\calibration_data_close_up.json'

load_calibration_file(calibration_path)



def undistort_image(image, mtx, dist):
    # Convert mtx back to numpy array
    mtx_np = np.array([[mtx[0], 0, mtx[2]], [0, mtx[1], mtx[3]], [0, 0, 1]])
    #undistort the image
    return cv2.undistort(image, mtx_np, dist, None, mtx_np)


def detector_superimpose(img, detector, tag_size=0.0111897893172):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #undistort the image
    gray = undistort_image(gray, mtx, dist)
    detections = detector.detect(gray, estimate_tag_pose= True, camera_params=(mtx), tag_size=tag_size)
    detectionsVectors = {}
    for d in detections:
        cv2.circle(img, (int(d.center[0]), int(d.center[1])), 5, (0, 0, 255), -1)
        cv2.putText(img, str(d.tag_id), (int(d.center[0]), int(d.center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #draw corners
        pose_data = d.pose_R, d.pose_t
        rvec, tvec = pose_data[0], pose_data[1]
        #rotation matrix to quaternion
        quat = sp.spatial.transform.Rotation.from_matrix(rvec).as_quat()
        euler = sp.spatial.transform.Rotation.from_matrix(rvec).as_euler('xyz', degrees=True)
        #
        str_euler = "x: " + str(round(euler[0], 2)) + " y: " + str(round(euler[1], 2)) + " z: " + str(round(euler[2], 2))
        z_angle = euler[2]
        speed = 100
        delta_y = tvec[0][0]
        delta_x = tvec[1][0]
        delta_z = tvec[2][0]
        yaw = z_angle


        
        detectionsVectors[d.tag_id] = {
            "x": delta_x,
            "y": delta_y,
            "z": delta_z,
            "yaw": yaw,
            "camera": current_camera_index,
            "quaternion": {
                "x": quat[0],
                "y": quat[1],
                "z": quat[2],
                "w": quat[3]
            }
        }
        #
        #shot the id on the center of the tag
        cv2.putText(img, str(d.tag_id), (int(d.center[0]), int(d.center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #draw the distance from the camera
        cv2.putText(img, str(round(delta_x*1000, 2)) + "mm", (int(d.center[0]), int(d.center[1]) + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(img, str(round(delta_y*1000, 2)) + "mm", (int(d.center[0]), int(d.center[1]) + 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(img, str(round(delta_z*1000, 2)) + "mm", (int(d.center[0]), int(d.center[1]) + 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #draw the yaw
        cv2.putText(img, "yaw: " + str(round(yaw, 2)), (int(d.center[0]), int(d.center[1]) + 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #draw the new x and y
        cv2.putText(img, "x: " + str(round(delta_x, 2)), (int(d.center[0]), int(d.center[1]) + 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(img, "y: " + str(round(delta_y, 2)), (int(d.center[0]), int(d.center[1]) + 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return img, detectionsVectors


def send_udp_data(data):
    # Send data to the Unity server
    UDP_IP = "localhost"
    UDP_PORT = 8765
    MESSAGE = json.dumps(data).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    sock.close()

command_queue = queue.Queue()

def udp_server():
    UDP_IP = "0.0.0.0"  # Listen on all interfaces
    UDP_PORT = 9876  # Port to listen on

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)  # Non-blocking socket

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            command_queue.put(command)
        except BlockingIOError:
            pass  # No data received
        except Exception as e:
            print(f"UDP server error: {e}")
            break



if __name__ == "__main__":
    #mjpeg server
    stream = Stream("my_camera", size=(1920, 1080), quality=50, fps=30)
    server = MjpegServer("localhost", 1692)
    server.add_stream(stream)
    server.start()
    #camera settings

    cap = cv2.VideoCapture(camera_indices[current_camera_index], cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Start the UDP server in a separate thread
     
    udp_thread = threading.Thread(target=udp_server, daemon=True)
    udp_thread.start()

    #main loop
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        frame, detections = detector_superimpose(frame, at_detector)
        send_udp_data(detections)
        #downscale the image 1/8
        resized = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
        cv2.imshow(stream.name, resized)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Switch cameras
            cap.release()
            # Open Camera Calibration
            if current_camera_index == 1:
                load_calibration_file(calibration_path)
            else:
                load_calibration_file(calibration_path_2)
            current_camera_index = (current_camera_index + 1) % len(camera_indices)
            cap = cv2.VideoCapture(camera_indices[current_camera_index], cv2.CAP_MSMF)
            # Re-apply camera settings
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
            cap.set(cv2.CAP_PROP_FPS, 30)
        if not command_queue.empty():
            command = command_queue.get()
            #separate the command from the arguments
            command = command.split(" ")
            if command[0] == "switch_camera":
                if command[1] == "0":
                    load_calibration_file(calibration_path)
                else:
                    load_calibration_file(calibration_path_2)
        stream.set_frame(frame)

    server.stop()
    cap.release()
    cv2.destroyAllWindows()
    # Start a UDP server to listen for commands

