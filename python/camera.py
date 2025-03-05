import asyncio
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import numpy as np
import json, math
import socket
import threading
import queue
from scipy.spatial.transform import	Rotation
from pupil_apriltags import	Detector
from mjpeg_streamer	import MjpegServer,	Stream
import time
from fastapi import	FastAPI, WebSocket
from contextlib	import asynccontextmanager
from fastapi.middleware.cors import	CORSMiddleware
from space import Euler, Vector3, Quaternion, Matrix4, Pose, PoseCartesian, Vector2, deg2rad, scale_values
from lara import Lara

# -------------------- GLOBAL FLAGS	--------------------
lara = Lara()
states = ["normal",	"square_detector", "tag_detector"]
state =	states[2]
current_camera_index = 0
change_camera_flag = False
original_capture_resoltion = (3840,	2160)
frame_rate = 30
ip = "192.168.2.209"
close_up_resolution = (1280, 720)
far_resolution = (1920, 1080)
current_setting_resolution = far_resolution
current_data = None
# Intrinsics
mtx	= None
dist = None
_offset_pos = Vector3(0, 0, 0)
_offset_quat = Quaternion(0, 0, 0, 1)
offset_tag = Pose(_offset_pos, _offset_quat)
try:
	with open('offset_tag.json', 'r') as f:
		offset_tag_json = f.read()
		offset_tag = Pose.from_json(offset_tag_json)

except FileNotFoundError:
	print("No offset tag file found")
except json.JSONDecodeError:
	print("Error reading offset tag file")

# ---------------------	API	---------------------
@asynccontextmanager
async def lifespan(app:	FastAPI):	
	global camera_thread, stop_camera_thread
	stop_camera_thread = False

	# Detector Thread 


	# Start	your camera	loop in a thread
	camera_thread =	threading.Thread(target=camera_loop, daemon=True)
	camera_thread.start()

	#connect to the	robot
	lara = Lara()
	lara.robot.stop()
	await lara.connect_socket()
	print("Connected to the	robot")
	lara.robot.turn_off_jog()

	try:
		yield
	finally:
		# Stop the reader thread and clean up
		print("Stopping the camera thread")
		stop_camera_thread = True
		camera_thread.join()
		print("Disconnected from the robot")



app	= FastAPI(lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Allow all origins
	allow_credentials=True,
	allow_methods=["*"],  # Allow all methods
	allow_headers=["*"],  # Allow all headers
)

@app.post("/set_state/{new_state}")
def	set_state(new_state: str):
	global state
	if new_state not in states:
		return {"status": "error", "message": "Invalid state"}
	state =	new_state
	return {"status": "ok",	"new_state": state}




@app.post("/test_area")
async def test_area(x: float, y: float, z: float):
	global lara
	x = x / 1000
	y = y / 1000
	z = z / 1000
	err = move_relative(x, y, z, 0, 0, 0)
	if not err:
		return {"error": "No movement detected"}
	else:
		return {"status": "ok"}

def move_relative(x, y, z, rx, ry, rz):
	'''
	Move robot relative to current position
	
	Args:
		x, y, z: relative movement in meters
		rx, ry, rz: relative rotation in radians
		
	Returns:
		bool: True if movement was successful (robot moved), False otherwise
	'''
	global lara
	
	# Get current TCP pose
	current_tcp_pose = lara.robot.get_tcp_pose()
	
	# Calculate target pose
	target_pose = [
		current_tcp_pose[0] + x,
		current_tcp_pose[1] + y,
		current_tcp_pose[2] + z,
		current_tcp_pose[3] + rx,
		current_tcp_pose[4] + ry,
		rz
	]
	
	# Setup movement properties
	linear_property = {
		"speed": 0.25,
		"acceleration": 0.1,
		"blending_mode": 1,
		"blend_radius": 0.005,
		"target_pose": [
			current_tcp_pose,
			target_pose
		],
		"current_joint_angles": lara.robot.robot_status("jointAngles"),
		"dwell_time_left": 0.0,
		"dwell_time_right": 0.0,
		"elevation": 0.0,
		"azimuth": 0.0
	}
	
	# Execute movement
	lara.robot.set_mode("Automatic")
	err = lara.robot.move_linear(**linear_property)
	time.sleep(0.5)
	
	# Get new pose after movement
	new_pose = lara.robot.get_tcp_pose()
	
	# Define thresholds for determining if movement occurred
	position_threshold_mm = 0.1  # 0.1mm
	rotation_threshold_deg = 0.1  # 0.1 degrees
	
	# Calculate differences
	diff_x = abs(new_pose[0] - current_tcp_pose[0]) * 1000  # convert to mm
	diff_y = abs(new_pose[1] - current_tcp_pose[1]) * 1000
	diff_z = abs(new_pose[2] - current_tcp_pose[2]) * 1000
	diff_rx = abs(new_pose[3] - current_tcp_pose[3]) * 180 / math.pi  # convert to degrees
	diff_ry = abs(new_pose[4] - current_tcp_pose[4]) * 180 / math.pi
	diff_rz = abs(new_pose[5] - current_tcp_pose[5]) * 180 / math.pi
	
	# Check if movement was significant
	position_moved = (diff_x > position_threshold_mm or 
					 diff_y > position_threshold_mm or 
					 diff_z > position_threshold_mm)
					 
	rotation_moved = (diff_rx > rotation_threshold_deg or 
					 diff_ry > rotation_threshold_deg or 
					 diff_rz > rotation_threshold_deg)
	
	# Return False if there was significant movement
	result =  (position_moved or rotation_moved)
	print(f"Position moved: {position_moved}, Rotation moved: {rotation_moved}")
	return result


@app.post("/SetOffSet")
async def setOffset():
	global current_data, offset_tag
	offset_tag = Pose(Vector3(0, 0, 0), Quaternion(0, 0, 0, 1))
	await asyncio.sleep(0.5)
	counter = 0
	while True:
		counter += 1
		if current_data:
			try:
				offset_tag = current_data[0]
				offset_tag_json = offset_tag.to_json()
				with open('offset_tag.json', 'w') as f:
					f.write(offset_tag_json)
				return {"status": "ok"}
			except KeyError:
				continue
		await asyncio.sleep(0.5)
		if counter > 10:
			return {"error": "No data received from the camera"}
@app.post("/AlingMove")
async def AlingMove():
	global lara, current_data
	counter = 0
	flag_buffered_movement = False
	current_translation_speed = 4
	await lara.set_translation_speed_mms(current_translation_speed)
	import socketio
	sio = socketio.AsyncClient(logger=False, engineio_logger=False)
	await sio.connect('http://192.168.2.13:8081')
	async def heart_beat(*args, **kwargs):
		await sio.emit('heartbeat_response', True)
		print("Heartbeat response")
	sio.on('heartbeat_check', heart_beat)
	async def start_movement_slider(q0, q1, q2, q3, q4, q5):
		data = {
			'q0': q0,
			'q1': q1,
			'q2': q2,
			'q3': q3,
			'q4': q4,
			'q5': q5,
			'status': True,
			'joint': False,
			'cartesian': True,
			'freedrive': False,
			'button': False,
			'slider': True,
			'goto': False,
			'threeD': False,
			'reference': "Base",
			'absrel': "Absolute",
		}
		await sio.emit('CartesianSlider', data)
	async def stop_movement_slider(q0, q1, q2, q3, q4, q5):
		data = {
			'q0': q0,
			'q1': q1,
			'q2': q2,
			'q3': q3,
			'q4': q4,
			'q5': q5,
			'status': False,
			'joint': False,
			'cartesian': True,
			'freedrive': False,
			'button': False,
			'slider': True,
			'goto': False,
			'threeD': False,
			'reference': "Base"
		}
		await sio.emit('CartesianSlider', data)

	#rough alligment phase
	detection_timeout = 0.25 # 250ms
	last_detection_time = time.time()
	success = True
	while True:
		if current_data:
			counter += 1
			tag0 = current_data.get(0)
			position = tag0.position
			quaternion = tag0.orientation
			print(f"Position: {position.x * 1000:.2f} mm, {position.y * 1000:.2f} mm, {position.z * 1000:.2f} mm")
			last_detection_time = time.time()
			current_arm_pose = lara.current_pose_raw()
			current_arm_orientation = current_arm_pose.orientation
			current_arm_orientation_euler = current_arm_orientation.to_euler()

			current_tag_orientation = quaternion.to_euler()
			angle_tag_z = current_tag_orientation.z
			angle_arm_z = current_arm_orientation_euler.z
			# print(f"Tag angle: {angle_tag_z * 180 / math.pi:.2f} Arm angle: {angle_arm_z * 180 / math.pi:.2f}")
			V2 = Vector2(position.x, position.y)
			V2 = V2.rotate(angle_arm_z)
			
			# print(f"Original x: {position.x * 1000:.2f} mm Original y: {position.y * 1000:.2f}")
			# print(f"Test x: {V2.x * 1000:.2f} mm Test y: {V2.y * 1000:.2f} mm, rotation: {angle_arm_z }")
			tcp_pose = lara.robot.get_tcp_pose()
			# print(f"Tag angle: {angle_tag_z * 180 / math.pi:.2f}")
			# print(f"Arm angle: {tcp_pose[3] * 180 / math.pi:.2f}")
			# print(f"Arm angle 3 : {tcp_pose[3] * 180 / math.pi:.2f}")
			# print(f"Arm angle 4 : {tcp_pose[4] * 180 / math.pi:.2f}")
			# print(f"Arm angle 5 : {tcp_pose[5] * 180 / math.pi:.2f}")
			if position.z < 0.01:
				break
			#starting tolerances
			tolerance = 0.01 # 20mm
			rotation_tolerance = deg2rad(1) # 2 degrees
			if position.z < 0.1: # less than 100mm
				tolerance = 0.05 # 10mm
				rotation_tolerance = deg2rad(0.75)
			if position.z < 0.05: # less than 50mm
				tolerance = 0.003 # 5mm
				rotation_tolerance = deg2rad(0.5)
			if position.z < 0.03: # less than 30mm
				tolerance = 0.002 # 2mm
				rotation_tolerance = deg2rad(0.2)
			if success:
				flag_buffered_movement = True
				await stop_movement_slider(0, 0, 0, 0, 0, 0)
				#add to the final tcp pose the z angle of the tag
				final_z_angle = tcp_pose[5] - angle_tag_z
				#normalize the angle between -pi and pi
				final_z_angle = (final_z_angle + math.pi) % (2 * math.pi) - math.pi
				success = move_relative(-V2.x, -V2.y, 0, 0, 0, final_z_angle)
				await asyncio.sleep(0.05)
			else:
				if flag_buffered_movement:
					lara.robot.stop()
					lara.robot.set_mode("Teach")
					lara.robot.unpause()
					flag_buffered_movement = False
					await asyncio.sleep(0.3)
				await start_movement_slider(0, 0, -1, 0, 0, 0)
				await asyncio.sleep(0.05)
				if not (abs(V2.x) < tolerance and abs(V2.y) < tolerance and abs(angle_tag_z) < rotation_tolerance):
					print("Movement needed")
					success = True
				
		else:
			if time.time() - last_detection_time > detection_timeout:
				await start_movement_slider(0, 0, 0, 0, 0, 0)
				await asyncio.sleep(0.5)
				lara.robot.stop()
				lara.robot.set_mode("Teach")
				return {"error": "No data received from the camera"}
			await asyncio.sleep(0.05)
	lara.robot.stop()
	lara.robot.set_mode("Teach")
	lara.robot.unpause()
	lara.robot.stop()
	#fine alligment phase
	await lara.set_translation_speed_mms(1)#
	detection_timeout = 0.2 # 200ms
	last_detection_time = time.time()
	while True:
		if current_data:
			counter += 1
			tag0 = current_data.get(0)
			position = tag0.position
			quaternion = tag0.orientation
			last_detection_time = time.time()
			if position.z < 0.005: # 5mm
				break
			V2 = Vector2(position.x, position.y)
			V2 = V2.rotate(angle_arm_z)
			#0.1 mm precision
			if abs(V2.x) < 0.0001 and abs(V2.y) < 0.0001:
				# await start_movement_slider(0, 0, -1, 0, 0, 0)
				lara.robot.turn_on_jog(jog_velocity=[0, 0, -1, 0, 0, 0], jog_type='Cartesian')
				lara.robot.jog(set_jogging_external_flag=1)
			else:
				# await start_movement_slider(-V2.x, -V2.y, 0, 0, 0, 0)
				lara.robot.turn_on_jog(jog_velocity=[-V2.x, -V2.y, 0, 0, 0, 0], jog_type='Cartesian')
				lara.robot.jog(set_jogging_external_flag=1)
			await asyncio.sleep(0.05)
		else:
			if time.time() - last_detection_time > detection_timeout:
				lara.robot.turn_off_jog()
				await asyncio.sleep(0.5)
				lara.robot.stop()
				return {"error": "No data received from the camera"}
			await asyncio.sleep(0.05)
	lara.robot.turn_off_jog()
	lara.robot.stop()
	await asyncio.sleep(0.5)
	await sio.disconnect()
	return {"status": "ok"}

@app.post("/Retract")
async def Retract():
	global lara
	lara.retract()


@app.get("/get_pose")
async def get_pose():
	counter = 0
	while True:
		if current_data:
			return {"pose": current_data[0]}
		await asyncio.sleep(0.1)
		counter += 1
		if counter > 10:
			return {"error": "No data received from the camera"}


@app.post("/set_camera/{index}")
def	set_camera(index: int):
	global current_camera_index, change_camera_flag
	current_camera_index = index
	change_camera_flag = True
	return {"state": state,	"camera": current_camera_index}

@app.post("/set_rotation_speed/{speed}")
async def set_rotation_speed(speed: int):
	global lara
	await lara.set_rotation_speed_degs(speed)
	return {"status": "ok"}

@app.get("/get_state")
def	get_state():
	return {"state": state,	"camera": current_camera_index}

def	sharpned_image(image, alpha=1.5, beta=-0.5):
	# Applying the sharpening filter
	sharpened =	cv2.convertScaleAbs(image, alpha=alpha,	beta=beta)
	return sharpened

def	open_camera(idx):
	cap	= cv2.VideoCapture(idx,	cv2.CAP_MSMF)
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

	if not cap.isOpened():
		raise Exception(f"Could	not	open camera	with index {idx}")
	return cap


def	detect_squares(frame, min_area=10000):
	"""
	Return two lists:
	1. valid_squares that meet the area	threshold
	2. filtered_squares	that don't meet	the	area threshold
	"""
	# Convert to grayscale
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	# Blur to reduce noise
	gray_blur =	cv2.GaussianBlur(gray, (11,	11), 0)
	# Sharpen the image
	gray_blur =	sharpned_image(gray_blur, alpha=2, beta=-0.5)

	#--- SOBEL EDGE	DETECTION ---
	sobelx = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=3)
	sobely = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=3)
	sobel_mag =	cv2.magnitude(sobelx, sobely)
	sobel_mag =	cv2.convertScaleAbs(sobel_mag)

	# Threshold	those edges
	_, sobel_bin = cv2.threshold(sobel_mag,	frame_rate,	255, cv2.THRESH_BINARY)

	# Morphological	close to fill gaps
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
	closed = cv2.morphologyEx(sobel_bin, cv2.MORPH_CLOSE, kernel)

	# Find contours
	contours, _	= cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	valid_squares =	[]
	filtered_squares = []

	for	cnt	in contours:
		epsilon	= 0.05 * cv2.arcLength(cnt,	True)
		approx = cv2.approxPolyDP(cnt, epsilon,	True)

		if len(approx) == 4	and	cv2.isContourConvex(approx):
			area = cv2.contourArea(approx)
			x, y, w, h = cv2.boundingRect(approx)
			aspect_ratio = float(w)	/ h
			# If the shape is more or less square
			if 0.8 <= aspect_ratio <= 1.2:
				if area	>= min_area:
					valid_squares.append(approx)
				else:
					filtered_squares.append(approx)

	return valid_squares, filtered_squares,	closed

def	square_superimpose(frame):
	valid_squares, small_squares, binary_mask =	detect_squares(frame, min_area=5000)

	# Draw big squares in green
	for	sq in valid_squares:
		cv2.drawContours(frame,	[sq], -1, (0, 255, 0), 3)

	# Draw small squares in red
	for	sq in small_squares:
		cv2.drawContours(frame,	[sq], -1, (0, 0, 255), 3)
	return frame, binary_mask


# -------------------- Camera Presets --------------------
camera_presets = {
	0: {
		'rotate': False,
		'calibration_path':	'computer_vision/calibration_data.json',
	},
	2: {
		'rotate': False,
		'calibration_path':	'computer_vision/calibration_data_close_up.json',
	}
}
# ----------------------------------------------------------

last_tag_data =	{}	# {	tag_id:	{"corners":	[(x1,y1),..], "hist": <numpy array>} }

camera_fits	= {}

def	compute_histogram(image, corners):
	pts	= np.array(corners,	dtype=np.int32)
	mask = np.zeros(image.shape[:2], dtype=np.uint8)
	cv2.fillConvexPoly(mask, pts, 255)
	roi	= cv2.bitwise_and(image, image,	mask=mask)
	hist = cv2.calcHist([roi], [0],	mask, [256], [0, 256])
	cv2.normalize(hist,	hist, alpha=0, beta=256, norm_type=cv2.NORM_MINMAX)
	return hist

def	draw_histogram(img,	hist, tag_id, x_offset=20, y_offset=20):
	if hist	is None:
		return

	hist_img_w,	hist_img_h = 512, 200
	hist_img = np.zeros((hist_img_h, hist_img_w, 3), dtype=np.uint8)

	cv2.line(hist_img, (0, hist_img_h -	1),	(hist_img_w	- 1, hist_img_h	- 1), (255,	255, 255), 1)
	for	i in range(1, 256):
		cv2.line(
			hist_img,
			(i - 1, hist_img_h - 1 - int(hist[i	- 1])),
			(i,		hist_img_h - 1 - int(hist[i])),
			(0,	255, 255),
			1
		)

	h, w, _	= img.shape
	if y_offset	+ hist_img_h < h and x_offset +	hist_img_w < w:
		roi	= img[y_offset:y_offset	+ hist_img_h, x_offset:x_offset	+ hist_img_w]
		blended	= cv2.addWeighted(roi, 0.5,	hist_img, 0.5, 0)
		img[y_offset:y_offset +	hist_img_h,	x_offset:x_offset +	hist_img_w]	= blended

	cv2.putText(
		img,
		f"Hist Tag {tag_id}",
		(x_offset, y_offset	- 5),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.5,
		(0,	255, 255),
		1
	)

def	getAvailableCameras():
	available_cameras =	[]
	for	i in range(10):
		try:
			camera = cv2.VideoCapture(i)
			if camera.isOpened():
				print("Camera index:", i)
				camera.release()
				available_cameras.append(i)
		except:
			pass
	return available_cameras

at_detector	= Detector(
	families="tag36h11",
	nthreads=8,
	quad_decimate=1.0,
	quad_sigma=0.0,
	refine_edges=1,
	decode_sharpening=1,
	debug=0
)



def	load_calibration_file(calibration_file_path):
	global mtx,	dist
	with open(calibration_file_path, 'r') as infile:
		reconstruction = json.load(infile)
		mtx_arr	= np.array(reconstruction['mtx'])
		dist_arr = np.array(reconstruction['dist'])
		fx,	fy,	cx,	cy = mtx_arr[0,	0],	mtx_arr[1, 1], mtx_arr[0, 2], mtx_arr[1, 2]
		# adjust for the capture resolution	from original
		fx *= current_setting_resolution[0]	/ original_capture_resoltion[0]
		fy *= current_setting_resolution[1]	/ original_capture_resoltion[1]
		cx *= current_setting_resolution[0]	/ original_capture_resoltion[0]
		cy *= current_setting_resolution[1]	/ original_capture_resoltion[1]

		mtx	= [fx, fy, cx, cy]
		dist = dist_arr

def	undistort_image(image, mtx,	dist):
	mtx_np = np.array([[mtx[0],	0,		mtx[2]],
					   [0,		mtx[1],	mtx[3]],
					   [0,		0,		1]], dtype=np.float32)
	return cv2.undistort(image,	mtx_np,	dist, None,	mtx_np)

FONT_SCALE_ID =	1.4
FONT_SCALE_INFO	= 1.0
FONT_THICKNESS = 4
BOX_THICKNESS =	4



def	add_vertical_gradient(image, top_value=1.3,	bottom_value=1.0):
	"""
	Applies	a vertical brightness gradient to the image.
	The	top	of the image is multiplied by `top_value`,
	and	it transitions linearly	to `bottom_value` at the bottom.
	Parameters:
		image: BGR image (as read by cv2)
		top_value (float): brightness multiplier at the	top
		bottom_value (float): brightness multiplier	at the bottom
	Returns:
		gradient_image:	Image with a vertical brightness gradient
	"""
	# Convert the image	to float [0,1] for safe	multiplication
	float_img =	image.astype(np.float32) / 255.0
	height,	width =	image.shape[:2]
	# Create a 1D array	that goes from top_value to bottom_value
	# shape: (height,)
	vertical_profile = np.linspace(top_value, bottom_value,	height,	dtype=np.float32)
	# Reshape to (height, 1) then tile across width	-> (height,	width)
	vertical_mask =	np.tile(vertical_profile.reshape(-1, 1), (1, width))
	# If the image has 3 channels, we need to expand the mask
	# shape	-> (height,	width, 3)
	if len(float_img.shape)	== 3 and float_img.shape[2]	== 3:
		vertical_mask =	cv2.merge([vertical_mask, vertical_mask, vertical_mask])
	# Multiply the image by the	mask
	gradient_img = float_img * vertical_mask
	# Clip to [0, 1], convert back to uint8
	gradient_img = np.clip(gradient_img, 0, 1)
	gradient_img = (gradient_img * 255).astype(np.uint8)
	return gradient_img


def	detector_superimpose(img, detector,	tag_size=0.014,	current_camera_index=0):
	global last_tag_data, current_setting_resolution, change_camera_flag, close_up_resolution, far_resolution, offset_tag

	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	img	= undistort_image(img, mtx,	dist)

	detections = detector.detect(
		gray,
		estimate_tag_pose=True,
		camera_params=(mtx),
		tag_size=tag_size
	)
	detectionsVectors =	{}

	h, w, _	= img.shape
	center_x, center_y = w // 2, h // 2
	cv2.line(img, (center_x, 0), (center_x,	h),	(255, 255, 255), 2)
	cv2.line(img, (0, center_y), (w, center_y),	(255, 255, 255), 2)
	cv2.circle(img,	(center_x, center_y), 20, (255,	255, 255), 2)

	camera_matrix =	np.array([
		[mtx[0], 0, 	 mtx[2]],
		[0,		 mtx[1], mtx[3]],
		[0,		 0, 	 1]
	], dtype=np.float32)
	dist_coeffs	= dist.astype(np.float32)

	current_frame_tags = set()

	for	d in detections:
		current_frame_tags.add(d.tag_id)
		corners	= d.corners
		center = (int(d.center[0]),	int(d.center[1]))
		cv2.circle(img,	center,	8, (0, 255,	0),	-1)
		cv2.putText(img, f"ID: {d.tag_id}",
					(center[0] + 10, center[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX,
					FONT_SCALE_ID,
					(0,	255, 0),
					FONT_THICKNESS)

		for	i in range(4):
			pt1	= (int(corners[i][0]), int(corners[i][1]))
			pt2	= (int(corners[(i +	1) % 4][0]), int(corners[(i	+ 1) % 4][1]))
			cv2.line(img, pt1, pt2,	(0,	255, 0), BOX_THICKNESS)

		rmat, tvec = d.pose_R, d.pose_t
		quat = Rotation.from_matrix(rmat).as_quat()

		raw_y =	-tvec[0][0] 
		raw_x =	-tvec[1][0]
		raw_z =	tvec[2][0]
		_tag_position =  Vector3(raw_x, raw_y, raw_z) - offset_tag.position
		#todo add the offsetquat
		detectionsVectors[d.tag_id] = Pose(_tag_position,  Quaternion(x=quat[0], y=quat[1], z=quat[2], w=quat[3]))
		#check if tag 0 is closer than 10mm
		if d.tag_id == 0:
			if raw_z < 0.03 and current_setting_resolution != close_up_resolution:
				print("Changing camera resolution to close up")
				current_setting_resolution = close_up_resolution
				change_camera_flag = True
			elif raw_z >= 0.04 and current_setting_resolution != far_resolution: # histeresis
				print("Changing camera resolution to far")
				current_setting_resolution = far_resolution
				change_camera_flag = True

		rvec, _	= cv2.Rodrigues(rmat)
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
			f"x: {detectionsVectors[d.tag_id].position.x*1000:.2f} mm",
			f"y: {detectionsVectors[d.tag_id].position.y*1000:.2f} mm",
			f"z: {detectionsVectors[d.tag_id].position.z*1000:.2f} mm",
			f"pitch: {pitch:.2f}",
			f"roll:	{roll:.2f}",
			f"yaw: {yaw:.2f}",
		]
		
		for	i, text	in enumerate(text_lines):
			cv2.putText(
				img,
				text,
				(center[0] + 10, center[1] + frame_rate	+ i	* frame_rate),
				cv2.FONT_HERSHEY_SIMPLEX,
				FONT_SCALE_INFO,
				(0,	0, 255),
				2
			)


	return img,	detectionsVectors


command_queue =	queue.Queue()

def	initialize_camera(index):
	preset = camera_presets.get(index, {})
	load_calibration_file(preset.get('calibration_path', ''))
	rotate = preset.get('rotate', False)
	return rotate


def	open_camera_with_retry(camera_index, max_retries=-1, delay_seconds=5):
	"""
	Tries to open the specified	camera index, and if it fails,
	retries	every `delay_seconds` until	success	or until `max_retries` is reached.
	If max_retries < 0, it will	retry forever.
	Returns	a cv2.VideoCapture if successful, or None if not.
	"""
	attempt	= 0
	while True:
		cap	= cv2.VideoCapture(camera_index, cv2.CAP_MSMF)
		if cap.isOpened():
			return cap

		cap.release()
		attempt	+= 1
		print(f"Failed to open camera {camera_index}, attempt {attempt}. "
			  f"Retrying in {delay_seconds}	seconds...")
		time.sleep(delay_seconds)

		if max_retries >= 0	and	attempt	>= max_retries:
			print(f"Max	retries	({max_retries})	reached. Giving	up on camera {camera_index}.")
			return None
		


def	camera_loop():
	global current_camera_index, change_camera_flag, state, ip, current_data
	"""
	This function runs in a	background thread.
	It continuously	grabs frames from the camera
	and	processes them (or superimposes	AprilTags, etc.).
	Meanwhile, FastAPI is running in the main thread.
	"""
	global stop_camera_thread

	# Start	your MJPEG server and streaming
	stream = Stream("my_camera", size=(1280, 720), quality=50, fps=frame_rate)
	server = MjpegServer(ip, 1692)
	server.add_stream(stream)
	server.start()

	# Some initialization
	camera_indices = list(camera_presets.keys())
	if not camera_indices:
		print("No camera presets defined. Exiting camera loop.")
		return

	initial_camera = camera_indices[current_camera_index]
	rotate_camera =	initialize_camera(initial_camera)

	cap	= open_camera_with_retry(initial_camera, max_retries=-1, delay_seconds=5)
	if cap is None:
		print(f"Could not open camera {initial_camera} after retries. Exiting camera loop.")
		return

	cap.set(cv2.CAP_PROP_FRAME_WIDTH, current_setting_resolution[0])
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, current_setting_resolution[1])
	cap.set(cv2.CAP_PROP_FPS, frame_rate)
	is_calibrating = False

	while not stop_camera_thread:
		if not is_calibrating:
			ret, frame = cap.read()
			if not ret:
				print("Failed to grab frame. Will try to reconnect in 5	seconds...")
				cap.release()
				time.sleep(5)
				cap	= open_camera_with_retry(
					camera_indices[current_camera_index],
					max_retries=-1,	
					delay_seconds=5
				)
				if cap is None:
					print("Could not re-open camera	after retries. Exiting camera loop.")
					break
				cap.set(cv2.CAP_PROP_FRAME_WIDTH, current_setting_resolution[0])
				cap.set(cv2.CAP_PROP_FRAME_HEIGHT, current_setting_resolution[1])
				cap.set(cv2.CAP_PROP_FPS, frame_rate)
				continue

			if rotate_camera:
				frame =	cv2.rotate(frame, cv2.ROTATE_180)
			if state == "square_detector":
				frame, binary_mask = square_superimpose(frame)
			elif state == "tag_detector":
				frame, detections =	detector_superimpose(
					frame, at_detector,	0.0115582191781, camera_indices[current_camera_index]
				)
				if detections:
					current_data = detections
				else:
					current_data = None
			resized	= cv2.resize(frame,	(1280, 720))
			# cv2.imshow(stream.name, resized)
			if change_camera_flag:
				cap.release()
				new_camera = camera_indices[current_camera_index]
				rotate_camera =	initialize_camera(new_camera)
				cap	= open_camera_with_retry(new_camera)
				if cap is None:
					print(f"Failed to open camera {new_camera} after retries. Exiting loop.")
					break
				cap.set(cv2.CAP_PROP_FRAME_WIDTH, current_setting_resolution[0])
				cap.set(cv2.CAP_PROP_FRAME_HEIGHT, current_setting_resolution[1])
				cap.set(cv2.CAP_PROP_FPS, frame_rate)
				print(f"Switched to camera {new_camera}")
				change_camera_flag = False
			
			key	= cv2.waitKey(1) & 0xFF

			if key == ord('q'):
				# If user hits 'q' in the OpenCV window, let's break out
				break
			
			elif key == ord('r'):
				rotate_camera =	not	rotate_camera
				print(f"Rotation now {rotate_camera}")
			elif key == ord('c'):
				print("Entering	calibration	mode. Press	'x'	to exit	and	fit	polynomials.")
				is_calibrating = True
				cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)

			stream.set_frame(resized)

	# When we exit the while loop or get a stop	signal,	shut down
	print("Exiting camera_loop()...")
	server.stop()
	cap.release()
	cv2.destroyAllWindows()


# ----------------------------------------------------------

if __name__	== "__main__":
	import uvicorn
	import threading
	uvicorn.run(app, host="192.168.2.209", port=1447)
	