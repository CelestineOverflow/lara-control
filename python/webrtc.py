import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
from webrtc_streamer import WebRTCStreamer
import cv2
from pupil_apriltags import Detector

at_detector = Detector(
   families="tag36h11",
   nthreads=16,
   quad_decimate=4.0,
   quad_sigma=0.0,
   refine_edges=1,
   decode_sharpening=0.25,
   debug=0
)

# Create the WebRTC streamer with high quality settings
streamer = WebRTCStreamer(
    host="192.168.2.209", 
    port=5176,
    cors_origin="http://192.168.2.209:5173",
    default_width=1920,
    default_height=1080,
    default_fps=30,
    default_bitrate=10000  # 10 Mbps for high quality
)
# Add a stream
streamer.add_stream("default", 1920, 1080, 30, 5000)

# Start the server in background
streamer.start()

# Open camera
cap = cv2.VideoCapture(0)
# set the camera resolution to 1280x720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
# set the camera FPS to 60
cap.set(cv2.CAP_PROP_FPS, 60)

try:
    while True:
        _, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = at_detector.detect(gray)
        # write the resolution on the frame as text 
        height, width, _ = frame.shape
        resolution_text = f"Resolution: {width}x{height}"
        # draw the detections on the frame
        for detection in detections:
            # draw the tag border
            cv2.polylines(frame, [detection.corners.astype(int)], isClosed=True, color=(0, 255, 0), thickness=2)
            # draw the center of the tag
            cv2.circle(frame, tuple(detection.center.astype(int)), 5, (0, 0, 255), -1)
            # draw the ID of the tag
            cv2.putText(frame, str(detection.tag_id), tuple(detection.center.astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, resolution_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Camera", frame)
        # Send the frame to WebRTC streamer
        # stream.set_frame(frame)
        streamer.set_frame(frame, "default")
        
        
        if cv2.waitKey(1) == ord("q"):
            break
finally:
    # Clean up
    streamer.stop()
    # server.stop()
    cap.release()
    cv2.destroyAllWindows()