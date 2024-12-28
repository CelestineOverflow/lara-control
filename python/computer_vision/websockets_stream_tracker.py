from mjpeg_streamer import MjpegServer, Stream
import cv2
import numpy as np	
import scipy as sp
import json, math
from pupil_apriltags import Detector
import sys
import argparse
import websockets
import time
import asyncio
import threading
import signal
import time

debug = True
tolerance = 0.5

at_detector = Detector(
        families="tag36h11",
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
)

# Load Calibration File

def load_calibration_file(calibration_file_path):
    #reconstruct the camera matrix and distortion coefficients
    with open(calibration_file_path, 'r') as infile:
        reconstruction = json.load(infile)
        mtx = np.array(reconstruction['mtx'])
        dist = np.array(reconstruction['dist'])
    return mtx, dist

calibration_path = r'calibration_data.json'
mtx, dist = load_calibration_file(calibration_path)
fx, fy, cx, cy = mtx[0,0], mtx[1,1], mtx[0,2], mtx[1,2]
mtx = [fx, fy, cx, cy]



        
def detector_superimpose(img, detector, tag_size=0.02):
    global client_udp
    global tag_id
    global save_offset
    global tags_in_view
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detections = detector.detect(gray, estimate_tag_pose= True, camera_params=(mtx), tag_size=tag_size)
    detectionsVectors = {}
    for d in detections:
        cv2.circle(img, (int(d.center[0]), int(d.center[1])), 5, (0, 0, 255), -1) 
        print(d.corners)
        cv2.putText(img, str(d.tag_id), (int(d.center[0]), int(d.center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #draw corners
        pose_data = d.pose_R, d.pose_t
        rvec, tvec = pose_data[0], pose_data[1]
        #rotation matrix to quaternion
        quat = sp.spatial.transform.Rotation.from_matrix(rvec).as_quat()
        euler = sp.spatial.transform.Rotation.from_matrix(rvec).as_euler('xyz', degrees=True)
        z_angle = euler[2]
        delta_y = tvec[0][0] * 1000
        delta_x = tvec[1][0] * 1000 
        delta_z = tvec[2][0] * 1000
        yaw = z_angle
        color = (0, 0, 255)
        if moveArm and d.tag_id == tag_id:
            color = (255, 0, 0)
            # Draw in green in the top left corner word "tracking"
            cv2.putText(img, "Tracking", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(img, str(d.tag_id), (int(d.center[0]), int(d.center[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(img, str(round(delta_x, 2)) + "mm", (int(d.center[0])+ 30, int(d.center[1]) + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.putText(img, str(round(delta_y, 2)) + "mm", (int(d.center[0])+ 30, int(d.center[1]) + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.putText(img, str(round(delta_z, 2)) + "mm", (int(d.center[0])+ 30, int(d.center[1]) + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.putText(img, "yaw: " + str(round(yaw, 2)), (int(d.center[0])+ 30, int(d.center[1]) + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        detectionsVectors[d.tag_id] = {
            "x": delta_x,
            "y": delta_y,
            "z": delta_z,
            "yaw": yaw
        }
    return img, detectionsVectors

async def handle_client(websocket, path):
    while True:
        try:
            message = await websocket.recv()
            print(message)
            data = json.loads(message)
            global tag_id
            global moveArm
            global trackoffset
            global save_offset
            global tags_in_view
            #ws.send(json.dumps({"command": "basictrack", "tag_id": tag_id, "moveArm": moveArm}))
            # if data['command'] == "basictrack":
            #     tag_id = data['tag_id']
            #     moveArm = data['moveArm']
            #     trackoffset = False
            #     await asyncio.sleep(1)
            # #ws.send(json.dumps({"command": "trackWithOffset", "tag_id": tag_id, "moveArm": moveArm}))
            # if data['command'] == "trackWithOffset":
            #     print("tracking with offset")
            #     #get last known position of the tag
            #     if not tag_id in tags_in_view:
            #         with open('settings/tags_offset.json') as f:
            #             offset = json.load(f)
            #             last_position = offset[str(tag_id)]['arm_position']
            #             safe_move(x=last_position['x'], y=last_position['y'], yaw=last_position['yaw'])
            #     tag_id = data['tag_id']
            #     moveArm = data['moveArm']
            #     trackoffset = True
            #     await asyncio.sleep(1)
            # #ws.send(json.dumps({"command": "setTrackOffset", "tag_id": tag_id}))
            # if data['command'] == "setTrackOffset":
            #     tag_id = data['tag_id']
            #     save_offset = True
        except json.JSONDecodeError:
            print("Invalid JSON")
            continue
        except websockets.ConnectionClosed:
            print("Connection closed")
            break
def start_server():
    asyncio.set_event_loop(asyncio.new_event_loop())
    start_server = websockets.serve(handle_client, "localhost", 6969)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Websockets Cameras')
    parser.add_argument('--camera-index', type=int, default=0, help='Index of the camera to use')
    parser.add_argument('--port', type=int, default=1337, help='Port number to use for the MJPEG server')
    parser.add_argument('--show', type=bool, default=False, help='Show the camera feed')
    args = parser.parse_args()
    cap = cv2.VideoCapture(0) 
    # set autofocus to off
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    #get current focus value
    focus = 100
    focus = 100
    if cap.get(cv2.CAP_PROP_FOCUS) != focus:
        cap.set(cv2.CAP_PROP_FOCUS, focus)
    else:
        cap.set(cv2.CAP_PROP_FOCUS, focus+1)


    print("Starting server")
    stream = Stream("my_camera", size=(640, 480), quality=50, fps=30)
    server = MjpegServer("localhost", args.port)
    server.add_stream(stream)
    server.start()

    #start the websocket server
    t = threading.Thread(target=start_server)
    t.start()


    while 1:
        try:
            #check if the camera is opened
            if not cap.isOpened():
                print("Camera is not opened")
                while not cap.isOpened():
                    cap = cv2.VideoCapture(args.camera_index)
                    time.sleep(30)
            _, frame = cap.read()
            frame, detections = detector_superimpose(frame, at_detector)
            if args.show:
                cv2.imshow(stream.name, frame)
                if cv2.waitKey(1) == ord("q"):
                    break

            stream.set_frame(frame)
        except KeyboardInterrupt:
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)
        except Exception as e:
            print(e)
            server.stop()
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)

