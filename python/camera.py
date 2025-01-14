import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import numpy as np
import json, math
import socket
import threading
import queue
from scipy.spatial.transform import Rotation
from pupil_apriltags import Detector
from mjpeg_streamer import MjpegServer, Stream
from scipy.optimize import curve_fit
import time
from typing import Dict, Union, Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware





# -------------------- GLOBAL FLAGS --------------------

states = ["normal", "square_detector", "tag_detector"]
state = states[2]
current_camera_index = 0
change_camera_flag = False

# --------------------- API ---------------------
app = FastAPI()

@app.on_event("startup")
def on_startup():
    """
    FastAPI event that fires when the server starts.
    We'll spin up the camera loop in a separate thread here.
    """
    print("Starting the application")
    global camera_thread, stop_camera_thread
    stop_camera_thread = False

    # Start your camera loop in a thread
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()

@app.on_event("shutdown")
def on_shutdown():
    """
    FastAPI event that fires when the server is shutting down.
    We signal the camera loop thread to stop.
    """
    print("Stopping the application")
    global stop_camera_thread
    stop_camera_thread = True

    # Wait for the camera thread to cleanly exit
    if 'camera_thread' in globals():
        camera_thread.join()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/set_state/{new_state}")
def set_state(new_state: str):
    global state
    if new_state not in states:
        return {"status": "error", "message": "Invalid state"}
    state = new_state
    return {"status": "ok", "new_state": state}

@app.post("/set_camera/{index}")
def set_camera(index: int):
    global current_camera_index, change_camera_flag
    current_camera_index = index
    change_camera_flag = True
    return {"state": state, "camera": current_camera_index}

@app.get("/get_state")
def get_state():
    return {"state": state, "camera": current_camera_index}

def sharpned_image(image, alpha=1.5, beta=-0.5):
    # Applying the sharpening filter
    sharpened = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return sharpened

def open_camera(idx):
    cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

    if not cap.isOpened():
        raise Exception(f"Could not open camera with index {idx}")
    return cap


def detect_squares(frame, min_area=10000):
    """
    Return two lists:
    1. valid_squares that meet the area threshold
    2. filtered_squares that don't meet the area threshold
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Blur to reduce noise
    gray_blur = cv2.GaussianBlur(gray, (11, 11), 0)
    # Sharpen the image
    gray_blur = sharpned_image(gray_blur, alpha=2, beta=-0.5)

    #--- SOBEL EDGE DETECTION ---
    sobelx = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=3)
    sobel_mag = cv2.magnitude(sobelx, sobely)
    sobel_mag = cv2.convertScaleAbs(sobel_mag)

    # Threshold those edges
    _, sobel_bin = cv2.threshold(sobel_mag, 30, 255, cv2.THRESH_BINARY)

    # Morphological close to fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(sobel_bin, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_squares = []
    filtered_squares = []

    for cnt in contours:
        epsilon = 0.05 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            area = cv2.contourArea(approx)
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            # If the shape is more or less square
            if 0.8 <= aspect_ratio <= 1.2:
                if area >= min_area:
                    valid_squares.append(approx)
                else:
                    filtered_squares.append(approx)

    return valid_squares, filtered_squares, closed

def square_superimpose(frame):
    valid_squares, small_squares, binary_mask = detect_squares(frame, min_area=5000)

    # Draw big squares in green
    for sq in valid_squares:
        cv2.drawContours(frame, [sq], -1, (0, 255, 0), 3)

    # Draw small squares in red
    for sq in small_squares:
        cv2.drawContours(frame, [sq], -1, (0, 0, 255), 3)
    return frame, binary_mask


# -------------------- Camera Presets --------------------
camera_presets = {
    2: {
        'rotate': False,
        'calibration_path': 'computer_vision/calibration_data.json',
    },
    1: {
        'rotate': True,
        'calibration_path': 'computer_vision/calibration_data_close_up.json',
    }
}
# ----------------------------------------------------------

last_tag_data = {}  # { tag_id: {"corners": [(x1,y1),..], "hist": <numpy array>} }

camera_fits = {}

def compute_histogram(image, corners):
    pts = np.array(corners, dtype=np.int32)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, pts, 255)
    roi = cv2.bitwise_and(image, image, mask=mask)
    hist = cv2.calcHist([roi], [0], mask, [256], [0, 256])
    cv2.normalize(hist, hist, alpha=0, beta=256, norm_type=cv2.NORM_MINMAX)
    return hist

def draw_histogram(img, hist, tag_id, x_offset=20, y_offset=20):
    if hist is None:
        return

    hist_img_w, hist_img_h = 512, 200
    hist_img = np.zeros((hist_img_h, hist_img_w, 3), dtype=np.uint8)

    cv2.line(hist_img, (0, hist_img_h - 1), (hist_img_w - 1, hist_img_h - 1), (255, 255, 255), 1)
    for i in range(1, 256):
        cv2.line(
            hist_img,
            (i - 1, hist_img_h - 1 - int(hist[i - 1])),
            (i,     hist_img_h - 1 - int(hist[i])),
            (0, 255, 255),
            1
        )

    h, w, _ = img.shape
    if y_offset + hist_img_h < h and x_offset + hist_img_w < w:
        roi = img[y_offset:y_offset + hist_img_h, x_offset:x_offset + hist_img_w]
        blended = cv2.addWeighted(roi, 0.5, hist_img, 0.5, 0)
        img[y_offset:y_offset + hist_img_h, x_offset:x_offset + hist_img_w] = blended

    cv2.putText(
        img,
        f"Hist Tag {tag_id}",
        (x_offset, y_offset - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1
    )

def getAvailableCameras():
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
    decode_sharpening=1,
    debug=0
)

# Intrinsics
mtx = None
dist = None

def load_calibration_file(calibration_file_path):
    global mtx, dist
    with open(calibration_file_path, 'r') as infile:
        reconstruction = json.load(infile)
        mtx_arr = np.array(reconstruction['mtx'])
        dist_arr = np.array(reconstruction['dist'])
        fx, fy, cx, cy = mtx_arr[0, 0], mtx_arr[1, 1], mtx_arr[0, 2], mtx_arr[1, 2]
        mtx = [fx, fy, cx, cy]
        dist = dist_arr

def undistort_image(image, mtx, dist):
    mtx_np = np.array([[mtx[0], 0,      mtx[2]],
                       [0,      mtx[1], mtx[3]],
                       [0,      0,      1]], dtype=np.float32)
    return cv2.undistort(image, mtx_np, dist, None, mtx_np)

FONT_SCALE_ID = 1.4
FONT_SCALE_INFO = 1.0
FONT_THICKNESS = 4
BOX_THICKNESS = 4

def polynomial_model(z, a, b, c):
    return a * (z ** 2) + b * z + c

def apply_camera_offsets(cam_index, raw_x, raw_y, raw_z):
    if cam_index not in camera_fits:
        return raw_x, raw_y
    coeffs_x = camera_fits[cam_index].get("coeffs_x", None)
    coeffs_y = camera_fits[cam_index].get("coeffs_y", None)
    if coeffs_x is None or coeffs_y is None:
        return raw_x, raw_y
    offset_x = polynomial_model(raw_z, *coeffs_x)
    offset_y = polynomial_model(raw_z, *coeffs_y)
    corrected_x = raw_x + offset_x
    corrected_y = raw_y + offset_y
    return corrected_x, corrected_y

def detector_superimpose(img, detector, tag_size=0.014, current_camera_index=0):
    global last_tag_data

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = undistort_image(img, mtx, dist)

    detections = detector.detect(
        gray,
        estimate_tag_pose=True,
        camera_params=(mtx),
        tag_size=tag_size
    )
    detectionsVectors = {}

    h, w, _ = img.shape
    center_x, center_y = w // 2, h // 2
    cv2.line(img, (center_x, 0), (center_x, h), (255, 255, 255), 2)
    cv2.line(img, (0, center_y), (w, center_y), (255, 255, 255), 2)
    cv2.circle(img, (center_x, center_y), 20, (255, 255, 255), 2)

    camera_matrix = np.array([
        [mtx[0], 0,      mtx[2]],
        [0,      mtx[1], mtx[3]],
        [0,      0,      1]
    ], dtype=np.float32)
    dist_coeffs = dist.astype(np.float32)

    current_frame_tags = set()

    for d in detections:
        current_frame_tags.add(d.tag_id)
        corners = d.corners
        center = (int(d.center[0]), int(d.center[1]))
        cv2.circle(img, center, 8, (0, 255, 0), -1)
        cv2.putText(img, f"ID: {d.tag_id}",
                    (center[0] + 10, center[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    FONT_SCALE_ID,
                    (0, 255, 0),
                    FONT_THICKNESS)

        for i in range(4):
            pt1 = (int(corners[i][0]), int(corners[i][1]))
            pt2 = (int(corners[(i + 1) % 4][0]), int(corners[(i + 1) % 4][1]))
            cv2.line(img, pt1, pt2, (0, 255, 0), BOX_THICKNESS)

        rmat, tvec = d.pose_R, d.pose_t
        quat = Rotation.from_matrix(rmat).as_quat()

        raw_y = -tvec[0][0]
        raw_x = -tvec[1][0]
        raw_z = tvec[2][0]

        detectionsVectors[d.tag_id] = {
            "x": raw_x,
            "y": raw_y,
            "z": raw_z,
            "camera": current_camera_index,
            "quaternion": {
                "x": quat[0],
                "y": quat[1],
                "z": quat[2],
                "w": quat[3]
            }
        }

        rvec, _ = cv2.Rodrigues(rmat)
        cv2.drawFrameAxes(
            img,
            camera_matrix,
            dist_coeffs,
            rvec.astype(np.float32),
            tvec.astype(np.float32),
            0.025
        )

        pitch, roll, yaw = Rotation.from_matrix(rmat).as_euler('xyz')
        text_lines = [
            f"x: {raw_x*1000:.2f} mm",
            f"y: {raw_y*1000:.2f} mm",
            f"z: {raw_z*1000:.2f} mm",
            f"pitch: {pitch:.2f}",
            f"roll: {roll:.2f}",
            f"yaw: {yaw:.2f}",
        ]
        
        for i, text in enumerate(text_lines):
            cv2.putText(
                img,
                text,
                (center[0] + 10, center[1] + 30 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                FONT_SCALE_INFO,
                (0, 0, 255),
                2
            )

        tag_hist = compute_histogram(gray, corners)
        last_tag_data[d.tag_id] = {
            "corners": corners,
            "hist": tag_hist
        }

    # Show old bounding boxes for tags not seen this frame
    for stored_tag_id, data in last_tag_data.items():
        if stored_tag_id not in current_frame_tags:
            old_corners = data["corners"]
            for i in range(4):
                pt1 = (int(old_corners[i][0]), int(old_corners[i][1]))
                pt2 = (int(old_corners[(i + 1) % 4][0]), int(old_corners[(i + 1) % 4][1]))
                cv2.line(img, pt1, pt2, (255, 0, 255), BOX_THICKNESS)

    y_offset = 20
    for tag_id, data in last_tag_data.items():
        draw_histogram(img, data["hist"], tag_id, x_offset=20, y_offset=y_offset)
        y_offset += 140

    return img, detectionsVectors

def send_udp_data(data):
    UDP_IP = "localhost"
    UDP_PORT = 8765
    MESSAGE = json.dumps(data).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    sock.close()

command_queue = queue.Queue()

def udp_server():
    UDP_IP = "0.0.0.0"
    UDP_PORT = 9876
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            command_queue.put(command)
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"UDP server error: {e}")
            break

def fit_polynomial_for_offsets(offsets):
    z_vals = []
    off_x = []
    off_y = []

    for data in offsets:
        z_vals.append(data["raw_z"])
        offset_x_val = data["ideal_x"] - data["raw_x"]
        offset_y_val = data["ideal_y"] - data["raw_y"]
        off_x.append(offset_x_val)
        off_y.append(offset_y_val)

    z_vals = np.array(z_vals, dtype=float)
    off_x = np.array(off_x, dtype=float)
    off_y = np.array(off_y, dtype=float)

    popt_x, _ = curve_fit(polynomial_model, z_vals, off_x)
    popt_y, _ = curve_fit(polynomial_model, z_vals, off_y)

    return popt_x.tolist(), popt_y.tolist()

def save_camera_fits(cam_index, coeffs_x, coeffs_y):
    data = {
        "coeffs_x": coeffs_x,
        "coeffs_y": coeffs_y
    }
    fname = f"camera_{cam_index}_offsets.json"
    with open(fname, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved polynomial offset fits to {fname}")

def load_camera_fits(cam_index):
    fname = f"camera_{cam_index}_offsets.json"
    try:
        with open(fname, 'r') as f:
            data = json.load(f)
            return data["coeffs_x"], data["coeffs_y"]
    except:
        return None, None

def calibration_routine(cap, rotate_flag, current_camera_index):
    import math
    offsets_data = []
    measure_count = 0
    assume_center_is_zero = True  # or tweak if needed

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera feed is messed up during calibration. Exiting calibration.")
            break

        if rotate_flag:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        displayed_frame, detections = detector_superimpose(frame, at_detector, 0.01, current_camera_index)
        cv2.putText(
            displayed_frame,
            "CALIBRATION MODE: Press 'Space' to record data, 'x' to finish",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 0),
            2
        )

        cv2.imshow("Calibration", displayed_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('x'):
            if len(offsets_data) < 2:
                print("Not enough data to do a polynomial fit. Bailing out.")
            else:
                coeffs_x, coeffs_y = fit_polynomial_for_offsets(offsets_data)
                camera_fits[current_camera_index] = {
                    "coeffs_x": coeffs_x,
                    "coeffs_y": coeffs_y
                }
                save_camera_fits(current_camera_index, coeffs_x, coeffs_y)
            print("Exiting calibration mode.")
            cv2.destroyWindow("Calibration")
            return

        elif key == ord(' '):
            if not detections:
                print("No tag detected—can't record. Try again.")
                continue

            tag_id = list(detections.keys())[0]
            pose_data = detections[tag_id]
            measure_count += 1

            raw_x = pose_data["raw_x"]
            raw_y = pose_data["raw_y"]
            raw_z = pose_data["raw_z"]

            ideal_x = 0.0
            ideal_y = 0.0

            offsets_data.append({
                "measurement_index": measure_count,
                "tag_id": tag_id,
                "raw_x": raw_x,
                "raw_y": raw_y,
                "raw_z": raw_z,
                "ideal_x": ideal_x,
                "ideal_y": ideal_y
            })

            print(f"Recorded measurement {measure_count}: "
                  f"raw=({raw_x:.4f}, {raw_y:.4f}, {raw_z:.4f}), ideal=(0,0)")

def initialize_camera(index):
    preset = camera_presets.get(index, {})
    load_calibration_file(preset.get('calibration_path', ''))
    rotate = preset.get('rotate', False)
    cx, cy = load_camera_fits(index)
    if cx and cy:
        camera_fits[index] = {"coeffs_x": cx, "coeffs_y": cy}
        print(f"Loaded polynomial offset fits for camera {index}: X={cx}, Y={cy}")
    return rotate

###
### CHANGES FOR RETRY: A helper function to open a camera with retry
###
def open_camera_with_retry(camera_index, max_retries=-1, delay_seconds=5):
    """
    Tries to open the specified camera index, and if it fails,
    retries every `delay_seconds` until success or until `max_retries` is reached.
    If max_retries < 0, it will retry forever.
    Returns a cv2.VideoCapture if successful, or None if not.
    """
    attempt = 0
    while True:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_MSMF)
        if cap.isOpened():
            return cap

        cap.release()
        attempt += 1
        print(f"Failed to open camera {camera_index}, attempt {attempt}. "
              f"Retrying in {delay_seconds} seconds...")
        time.sleep(delay_seconds)

        if max_retries >= 0 and attempt >= max_retries:
            print(f"Max retries ({max_retries}) reached. Giving up on camera {camera_index}.")
            return None
        


def camera_loop():
    global current_camera_index, change_camera_flag, state
    """
    This function runs in a background thread.
    It continuously grabs frames from the camera
    and processes them (or superimposes AprilTags, etc.).
    Meanwhile, FastAPI is running in the main thread.
    """
    global stop_camera_thread

    # Start your MJPEG server and streaming
    stream = Stream("my_camera", size=(1280, 720), quality=50, fps=30)
    server = MjpegServer("localhost", 1692)
    server.add_stream(stream)
    server.start()

    # Some initialization
    camera_indices = list(camera_presets.keys())
    if not camera_indices:
        print("No camera presets defined. Exiting camera loop.")
        return

    initial_camera = camera_indices[current_camera_index]
    rotate_camera = initialize_camera(initial_camera)

    cap = open_camera_with_retry(initial_camera, max_retries=-1, delay_seconds=5)
    if cap is None:
        print(f"Could not open camera {initial_camera} after retries. Exiting camera loop.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
    cap.set(cv2.CAP_PROP_FPS, 30)

    udp_thread = threading.Thread(target=udp_server, daemon=True)
    udp_thread.start()
    is_calibrating = False

    while not stop_camera_thread:
        if not is_calibrating:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Will try to reconnect in 5 seconds...")
                cap.release()
                time.sleep(5)
                cap = open_camera_with_retry(
                    camera_indices[current_camera_index],
                    max_retries=-1, 
                    delay_seconds=5
                )
                if cap is None:
                    print("Could not re-open camera after retries. Exiting camera loop.")
                    break
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
                cap.set(cv2.CAP_PROP_FPS, 30)
                continue

            if rotate_camera:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            if state == "square_detector":
                frame, binary_mask = square_superimpose(frame)
            elif state == "tag_detector":
                frame, detections = detector_superimpose(
                    frame, at_detector, 0.0115582191781, camera_indices[current_camera_index]
                )
                send_udp_data(detections)

            resized = cv2.resize(frame, (1280, 720))
            cv2.imshow(stream.name, resized)
            if change_camera_flag:
                cap.release()
                new_camera = camera_indices[current_camera_index]
                rotate_camera = initialize_camera(new_camera)
                cap = open_camera_with_retry(new_camera)
                if cap is None:
                    print(f"Failed to open camera {new_camera} after retries. Exiting loop.")
                    break
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
                cap.set(cv2.CAP_PROP_FPS, 30)
                print(f"Switched to camera {new_camera}")
            
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                # If user hits 'q' in the OpenCV window, let's break out
                break
            
            elif key == ord('r'):
                rotate_camera = not rotate_camera
                print(f"Rotation now {rotate_camera}")
            elif key == ord('c'):
                print("Entering calibration mode. Press 'x' to exit and fit polynomials.")
                is_calibrating = True
                cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)

            # Check any commands from UDP
            if not command_queue.empty():
                command = command_queue.get().split(" ")
                if command[0] == "switch_camera":
                    # ...
                    pass

            stream.set_frame(resized)

        else:
            # Run calibration routine until user exits
            calibration_routine(
                cap, rotate_camera, camera_indices[current_camera_index]
            )
            is_calibrating = False

    # When we exit the while loop or get a stop signal, shut down
    print("Exiting camera_loop()...")
    server.stop()
    cap.release()
    cv2.destroyAllWindows()


# ----------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    import threading
    uvicorn.run(app, host="localhost", port=1447)
    