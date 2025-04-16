import cv2
import subprocess
# Define the ffmpeg command.
# Note:
# - '-s' sets the resolution to 1280x720.
# - '-r' sets the frame rate to 60 fps.
# - We're using the mpegts container over UDP.
ffmpeg_command = [
   'ffmpeg',
   '-y',  # Overwrite output files if needed.
   '-f', 'rawvideo',
   '-vcodec', 'rawvideo',
   '-pix_fmt', 'bgr24',
   '-s', '1280x720',  # 720p resolution.
   '-r', '60',       # 60 fps.
   '-i', '-',        # Read input from stdin.
   '-c:v', 'libx264',
   '-preset', 'ultrafast',
   '-f', 'mpegts',   # Use MPEG-TS as the container format.
   'udp://127.0.0.1:1334'  # Stream to localhost on port 1334.
]
# Start the ffmpeg process.
process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
# Open the default camera.
cap = cv2.VideoCapture(0)
# Set the camera's resolution and fps (if supported by your device).
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 60)
while True:
    ret, frame = cap.read()
    cv2.imshow("Camera", frame)
        # Check if the user pressed 'q' to exit.
    if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    if not ret:
        break
    # Write the raw frame data to ffmpeg's stdin.
    process.stdin.write(frame.tobytes())
# Cleanup
cap.release()
process.stdin.close()
process.wait()