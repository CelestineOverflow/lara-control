from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiortc import RTCPeerConnection, RTCSessionDescription
import cv2
import asyncio
import multiprocessing
import threading
import queue
import json
import numpy as np
from pupil_apriltags import Detector
import scipy as sp
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Camera Settings
at_detector = Detector(
    families="tag36h11",
    nthreads=2,
    quad_decimate=2.0,  # Reduce resolution for faster detection
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0
)

with open('computer_vision\\calibration_data.json', 'r') as infile:
    reconstruction = json.load(infile)
    mtx = np.array(reconstruction['mtx'])
    dist = np.array(reconstruction['dist'])

fx, fy, cx, cy = mtx[0, 0], mtx[1, 1], mtx[0, 2], mtx[1, 2]
mtx = [fx, fy, cx, cy]

# Create a queue to hold frames
frame_queue = queue.Queue()

def detector_superimpose(img, tag_size=0.02):
    global at_detector
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detections = at_detector.detect(gray, estimate_tag_pose=True, camera_params=mtx, tag_size=tag_size)
    detectionsVectors = {}
    for d in detections:
        # print the corners coordinates
        # print(d.corners)
        cv2.circle(img, (int(d.center[0]), int(d.center[1])), 5, (0, 0, 255), -1)
        cv2.putText(img, str(d.tag_id), (int(d.center[0]), int(d.center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        pose_data = d.pose_R, d.pose_t
        rvec, tvec = pose_data[0], pose_data[1]
        quat = sp.spatial.transform.Rotation.from_matrix(rvec).as_quat()
        euler = sp.spatial.transform.Rotation.from_matrix(rvec).as_euler('xyz', degrees=True)
        z_angle = euler[2]
        delta_y = tvec[0][0] * 1000
        delta_x = tvec[1][0] * 1000
        delta_z = tvec[2][0] * 1000
        yaw = z_angle
        color = (255, 0, 0)
        cv2.putText(img, "Tracking", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(img, str(round(delta_x, 2)) + "mm", (int(d.center[0]) + 30, int(d.center[1]) + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(img, str(round(delta_y, 2)) + "mm", (int(d.center[0]) + 30, int(d.center[1]) + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(img, str(round(delta_z, 2)) + "mm", (int(d.center[0]) + 30, int(d.center[1]) + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(img, "yaw: " + str(round(yaw, 2)), (int(d.center[0]) + 30, int(d.center[1]) + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        detectionsVectors[d.tag_id] = {
            "x": delta_x,
            "y": delta_y,
            "z": delta_z,
            "yaw": yaw
        }
    return img, detectionsVectors

counter = 0

def display_frames(fps=10):

    """Function to display frames at a controlled frame rate."""
    global counter
    interval = 1 / fps
    last_time = time.time()
    while True:
        frame = None
        while not frame_queue.empty():
            frame = frame_queue.get()
        

        if frame is None:
            time.sleep(0.01)
            continue

        # save the frame to file
        

        gray = cv2.cvtColor(frame ,cv2.COLOR_BGR2GRAY)
        result, corners = cv2.findChessboardCorners(gray, (5,5), cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)
        # Process and display the frame
        frame, _ = detector_superimpose(frame)
        
        if result == True:
            print(f"Saving frame {counter}")
            cv2.imwrite(f"captured/frame_{counter}.jpg", frame)
            counter += 1
        cv2.drawChessboardCorners(frame, (5,5), corners, result)
        cv2.imshow("Video", frame)
        

        # Frame rate control
        elapsed = time.time() - last_time
        if elapsed < interval:
            time.sleep(interval - elapsed)
        last_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

# Start the display thread
display_thread = threading.Thread(target=display_frames, args=(24,))  # Adjust FPS as needed
display_thread.start()

@app.post("/offer")
async def offer(sdp_offer: dict):
    print("Received offer")
    pc = RTCPeerConnection()

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            print("Video track received")

            async def read_frames():
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="bgr24")
                        # print(img.shape)
                        img = cv2.resize(img, (1000, 1000))  # Adjust to match your expected resolution
                        
                        frame_queue.put(img)
                    except Exception as e:
                        print(f"Error receiving frame: {e}")
                        break

            # Create a task to consume frames from the incoming track
            asyncio.create_task(read_frames())

    # Set remote description
    offer = RTCSessionDescription(sdp=sdp_offer["sdp"], type=sdp_offer["type"])
    await pc.setRemoteDescription(offer)

    # Create and set local description
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=1446, reload=False, workers=1)

    # When the server stops, stop the display thread
    frame_queue.put(None)
    display_thread.join()