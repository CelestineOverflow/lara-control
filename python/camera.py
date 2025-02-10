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
from scipy.optimize	import curve_fit
import time
from typing	import Dict, Union,	Optional
from fastapi import	FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib	import asynccontextmanager
from fastapi.middleware.cors import	CORSMiddleware
from space import Euler, Vector3, Quaternion, Matrix4, Pose, PoseCartesian
from lara import Lara



lara = Lara()

# -------------------- GLOBAL FLAGS	--------------------

states = ["normal",	"square_detector", "tag_detector"]
state =	states[2]
current_camera_index = 1
change_camera_flag = False
original_capture_resoltion = (3840,	2160)
capture_resolution = (1920,	1080)
frame_rate = 30
ip = "192.168.2.209"
# ---------------------	API	---------------------
@asynccontextmanager
async def lifespan(app:	FastAPI):	
	global camera_thread, stop_camera_thread
	stop_camera_thread = False

	# Start	your camera	loop in a thread
	camera_thread =	threading.Thread(target=camera_loop, daemon=True)
	camera_thread.start()

	#connect to the	robot
	lara = Lara()
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
		await lara.disconnect_socket()
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


current_data = None

@app.post("/AlignToTag")
def align_to_tag(offsetx:	float =	0, offsety:	float =	0):
	global lara, current_data
	# current_trans_speed = 4
	# current_rot_speed = 1
	# lara.setTranslationSpeedMMsNoAsync(current_trans_speed)
	# lara.setRotSpeedDegSNoAsync(current_rot_speed)
	#convert the offset	to meters with a max value of 10mm in each direction
	if offsetx > 10 or offsetx < -10 or offsety	> 10 or offsety	< -10:
		return {"error": "Offset values	must be between	-10	and	10 mm"}
	offsetx	/= 1000
	offsety	/= 1000
	z_final_height = (5 / 1000)
	current_movement_vector	= Vector3(0, 0, 0)
	current_rotation_vector	= Vector3(0, 0, 0)
	start_height = None
	last_height = False
	# Thread control variables
	jog_thread = None
	stop_jog_event = threading.Event()
	save_data = True




	def jog_background_task(stop_event: threading.Event):
		"""
		Sends the jog flag every 10ms until stop_event is set or 500ms elapse.
		Prints the time in between in milliseconds.
		"""
		start_time = time.time()
		while (time.time() - start_time < 0.5) and not stop_event.is_set():
			lara.robot.jog(set_jogging_external_flag=1)
			current_time = time.time()
			time_in_between = (current_time - start_time) * 1000  # Convert to milliseconds
			# print(f"Time in between: {time_in_between:.2f} ms")
			start_time = current_time
	def	start_jog(velocity):
		"""
		Turns on jog and starts	the	background thread.
		"""
		nonlocal jog_thread, stop_jog_event
		# Stop any existing	thread
		if jog_thread and jog_thread.is_alive():
			stop_jog_event.set()
			jog_thread.join()
		# Turn on jog
		lara.robot.turn_on_jog(jog_velocity=velocity, jog_type='Cartesian')
		# Start	background thread
		stop_jog_event = threading.Event()
		jog_thread = threading.Thread(target=jog_background_task, args=(stop_jog_event,), daemon=True)
		jog_thread.start()

	def	stop_jog():
		"""
		Turns off jog and stops	the	background thread.
		"""
		nonlocal jog_thread, stop_jog_event
		stop_jog_event.set()
		lara.robot.turn_off_jog()
		if jog_thread and jog_thread.is_alive():
			jog_thread.join()
	poses = {}
	while True:
		if current_data:
			try:
				position = Vector3(
				x=current_data[0]['x'],
				y=current_data[0]['y'],
				z=current_data[0]['z']
				)
				quaternion = Quaternion(
					x=current_data[0]['quaternion']['x'],
					y=current_data[0]['quaternion']['y'],
					z=current_data[0]['quaternion']['z'],
					w=current_data[0]['quaternion']['w']
				)
			#if key error continue
			except KeyError:
				continue

			detected_pose =	Pose(position, quaternion)
			# 2) Camera	offset pose
			offset_camera_pose = Pose(
				position=Vector3(0.0, 0.0, 0.0),
				orientation=Quaternion(0, 0, 0, 1)
			)
			# 3) Custom	offset pose
			custom_offset =	Pose(
				position=Vector3(-offsetx, -offsety, 0),
				orientation=Quaternion(0, 0, 0, 1)
			)
			# 4) Current robot pose	in the world
			lara_global_pose = lara.pose
			# ---- Convert to 4x4 transforms ----
			T_robot_world	= Matrix4.from_pose(lara_global_pose)	 # Robot in world
			T_camera_robot	= Matrix4.from_pose(offset_camera_pose)	  # Camera in robot
			T_tag_camera	= Matrix4.from_pose(detected_pose)		  # Tag	in camera
			T_custom_offset	= Matrix4.from_pose(custom_offset)		  # Custom offset
			# 5) Compute T_tag_world
			T_tag_world	= T_robot_world	* T_camera_robot * T_tag_camera	* T_custom_offset
			# 6) For a simple “align” scenario,	let’s say we want the end-effector exactly where the tag is
			T_robot_world_desired =	T_tag_world
			# 7) Compute the delta transform from the robot’s current pose to the desired
			T_delta	= T_robot_world.inverse() *	T_robot_world_desired
			# 8) Extract the translation + rotation	from T_delta
			delta_q, delta_t = T_delta.to_quaternion_translation()
			# 9) Save pose data
			if start_height is None:
				start_height = (delta_t.z - z_final_height)
				poses["start"] = {
					"tag": detected_pose.to_dict(),
					"robot": lara.current_pose().to_dict()
				}
				with open("poses.json", "r") as f:
					last_data = f.read()
					if last_data:
						last_data = json.loads(last_data)
						print(last_data)
						# {'start': {'tag': {'position': [0.006143113998528555, 3.539078098373626e-05, 0.15121875647756386], 'orientation': [-0.1405898207550043, -0.00013636909131212118, 0.001801615349748799, 0.990066279541768]}, 'robot': {'position': [-0.15054610319842335, -0.5042284902953714, 0.21357617464788223], 'orientation': [-3.141576975550517, 2.6772147986742212e-05, -0.6197900824584184]}}, 'last': {'tag': {'position': [0.005648809324801668, 8.474977878136805e-05, 0.1359475291901317], 'orientation': [0.09830618284612178, -0.008742056127883127, 0.0021144961202943114, 0.9951155710645067]}, 'robot': {'position': [-0.15050097488787906, -0.5042355261944492, 0.19531571921122606], 'orientation': [-3.141581273516387, 3.0063411917469196e-05, -0.6196937818443564]}}}
						#check distance against start in x y z of the current tag detection with the past start tag detection
						last_tag_start = last_data["start"]["tag"]
						x_error = abs(last_tag_start["position"][0] - detected_pose.position.x)
						y_error = abs(last_tag_start["position"][1] - detected_pose.position.y)
						z_error = abs(last_tag_start["position"][2] - detected_pose.position.z)
						print(f"X error: {x_error * 1000:.2f} mm Y error: {y_error * 1000:.2f} mm Z error: {z_error * 1000:.2f} mm")
						if x_error < 0.01 and y_error < 0.01 and z_error < 0.10:
							#move arm to last position to speed up the process
							print("Moving arm to known position")
							save_data = False
							last_arm_pose = last_data["last"]["robot"]
							cartesianPose = PoseCartesian.from_dict(last_arm_pose)
							lara.move_to_pose_cartesian_from_current(cartesianPose)
			#check if last 10mm
			else:
				if abs(delta_t.z - z_final_height) < 0.01 and last_height == False:
					print("Last 10mm")
					poses[f"last"] = {
						"tag": detected_pose.to_dict(),
						"robot": lara.current_pose().to_dict()
					}
					last_height = True


			

			# print(f"Delta translation: {(delta_t.z - z_final_height) * 1000:.2f} mm")
			# rotation
			rot_z =	delta_q.to_euler().z
			allowed_error_rot =	0.5
			if abs(delta_t.z) >	((50 / 1000) + z_final_height):
				allowed_error_rot =	0.2
			elif abs(delta_t.z)	> ((30 / 1000) + z_final_height):
				allowed_error_rot =	0.1
			else:
				allowed_error_rot =	0.01		
			if not (rot_z <	allowed_error_rot and rot_z	> -allowed_error_rot):
				current_movement_vector.x =	0
				current_movement_vector.y =	0
				current_movement_vector.z =	0
				current_rotation_vector.x =	0
				current_rotation_vector.y =	0
				current_rotation_vector.z =	-1 if rot_z	> 0	else 1
				start_jog([current_movement_vector.x, current_movement_vector.y, current_movement_vector.z, current_rotation_vector.x, current_rotation_vector.y, current_rotation_vector.z])
				continue # Skip	the	translation	if the rotation	is not aligned
			# translation
			fine_tune_speed	= 0.1
			normal_speed = 1.0
			Kp = 25.0

			# X	movement
			err_x =	delta_t.x
			if abs(err_x) <	0.0001:
				current_movement_vector.x =	0
			else:
				proportional_speed_x = -Kp * err_x
				if abs(proportional_speed_x) < fine_tune_speed:
					proportional_speed_x = fine_tune_speed if proportional_speed_x > 0 else	-fine_tune_speed
				elif abs(proportional_speed_x) > normal_speed:
					proportional_speed_x = normal_speed	if proportional_speed_x	> 0	else -normal_speed
				current_movement_vector.x =	proportional_speed_x

			# Y	movement
			err_y =	delta_t.y
			if abs(err_y) <	0.0001:
				current_movement_vector.y =	0
			else:
				proportional_speed_y = -Kp * err_y
				if abs(proportional_speed_y) < fine_tune_speed:
					proportional_speed_y = fine_tune_speed if proportional_speed_y > 0 else	-fine_tune_speed
				elif abs(proportional_speed_y) > normal_speed:
					proportional_speed_y = normal_speed	if proportional_speed_y	> 0	else -normal_speed
				current_movement_vector.y =	proportional_speed_y

			# Z	movement
		
			if abs(delta_t.z) >	((50 / 1000) + z_final_height):
				allowed_error_xy = 10 /	1000
			elif abs(delta_t.z)	> ((30 / 1000) + z_final_height):
				allowed_error_xy = 3 / 1000
			elif abs(delta_t.z)	> ((5 /	1000) +	z_final_height):
				allowed_error_xy = 1 / 1000
			else: 
				allowed_error_xy = 0.1 / 1000			
			if not (abs(delta_t.x) < allowed_error_xy and abs(delta_t.y) < allowed_error_xy):
				current_movement_vector.z =	0
				current_rotation_vector.x =	0
				current_rotation_vector.y =	0
				current_rotation_vector.z =	0
				start_jog([current_movement_vector.x, current_movement_vector.y, current_movement_vector.z, current_rotation_vector.x, current_rotation_vector.y, current_rotation_vector.z])
				if allowed_error_xy	== 0.1 / 1000:
					#we should not use threading here, fine tuning

					lara.robot.turn_on_jog(
						jog_velocity=[0, 0, 0, 0, 0, 0],
						jog_type='Cartesian'
					)
					lara.robot.jog(set_jogging_external_flag = 1)
				continue
			else:
				if abs(delta_t.z) <	z_final_height:
					break
				else:
					current_movement_vector.x =	0
					current_movement_vector.y =	0
					current_movement_vector.z =	-1
					current_rotation_vector.x =	0
					current_rotation_vector.y =	0
					current_rotation_vector.z =	0
					start_jog([current_movement_vector.x, current_movement_vector.y, current_movement_vector.z, current_rotation_vector.x, current_rotation_vector.y, current_rotation_vector.z])
		time.sleep(0.01)
	stop_jog()
	# Save the poses to a json file
	if save_data:
		with open("poses.json", "w") as f:
			json.dump(poses, f, indent=4)
	return {"status": "ok"}


@app.post("/set_camera/{index}")
def	set_camera(index: int):
	global current_camera_index, change_camera_flag
	current_camera_index = index
	change_camera_flag = True
	return {"state": state,	"camera": current_camera_index}

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
	1: {
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
	nthreads=1,
	quad_decimate=4.0,
	quad_sigma=0.0,
	refine_edges=1,
	decode_sharpening=1,
	debug=0
)

# Intrinsics
mtx	= None
dist = None

def	load_calibration_file(calibration_file_path):
	global mtx,	dist
	with open(calibration_file_path, 'r') as infile:
		reconstruction = json.load(infile)
		mtx_arr	= np.array(reconstruction['mtx'])
		dist_arr = np.array(reconstruction['dist'])
		fx,	fy,	cx,	cy = mtx_arr[0,	0],	mtx_arr[1, 1], mtx_arr[0, 2], mtx_arr[1, 2]
		# adjust for the capture resolution	from original
		fx *= capture_resolution[0]	/ original_capture_resoltion[0]
		fy *= capture_resolution[1]	/ original_capture_resoltion[1]
		cx *= capture_resolution[0]	/ original_capture_resoltion[0]
		cy *= capture_resolution[1]	/ original_capture_resoltion[1]

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

def	polynomial_model(z,	a, b, c):
	return a * (z ** 2) + b	* z	+ c

def	apply_camera_offsets(cam_index,	raw_x, raw_y, raw_z):
	if cam_index not in camera_fits:
		return raw_x, raw_y
	coeffs_x = camera_fits[cam_index].get("coeffs_x", None)
	coeffs_y = camera_fits[cam_index].get("coeffs_y", None)
	if coeffs_x	is None	or coeffs_y	is None:
		return raw_x, raw_y
	offset_x = polynomial_model(raw_z, *coeffs_x)
	offset_y = polynomial_model(raw_z, *coeffs_y)
	corrected_x	= raw_x	+ offset_x
	corrected_y	= raw_y	+ offset_y
	return corrected_x,	corrected_y


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
	global last_tag_data

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
		raw_z =	tvec[2][0] - 0.020 # offset	for	the	camera

		detectionsVectors[d.tag_id]	= {
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
			f"x: {raw_x*1000:.2f} mm",
			f"y: {raw_y*1000:.2f} mm",
			f"z: {raw_z*1000:.2f} mm",
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

		tag_hist = compute_histogram(gray, corners)
		last_tag_data[d.tag_id]	= {
			"corners": corners,
			"hist":	tag_hist
		}

	# Show old bounding	boxes for tags not seen	this frame
	for	stored_tag_id, data	in last_tag_data.items():
		if stored_tag_id not in current_frame_tags:
			old_corners	= data["corners"]
			for	i in range(4):
				pt1	= (int(old_corners[i][0]), int(old_corners[i][1]))
				pt2	= (int(old_corners[(i +	1) % 4][0]), int(old_corners[(i	+ 1) % 4][1]))
				cv2.line(img, pt1, pt2,	(255, 0, 255), BOX_THICKNESS)

	y_offset = 20
	for	tag_id,	data in last_tag_data.items():
		draw_histogram(img,	data["hist"], tag_id, x_offset=20, y_offset=y_offset)
		y_offset += 140

	return img,	detectionsVectors

def	send_udp_data(data):
	global current_data
	current_data = data

command_queue =	queue.Queue()

def	udp_server():
	UDP_IP = "0.0.0.0"
	UDP_PORT = 9876
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))
	sock.setblocking(False)

	while True:
		try:
			data, addr = sock.recvfrom(1024)
			command	= data.decode().strip()
			command_queue.put(command)
		except BlockingIOError:
			pass
		except Exception as e:
			print(f"UDP	server error: {e}")
			break

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
	global current_camera_index, change_camera_flag, state, ip
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

	cap.set(cv2.CAP_PROP_FRAME_WIDTH, capture_resolution[0])
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_resolution[1])
	cap.set(cv2.CAP_PROP_FPS, frame_rate)

	udp_thread = threading.Thread(target=udp_server, daemon=True)
	udp_thread.start()
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
				cap.set(cv2.CAP_PROP_FRAME_WIDTH, capture_resolution[0])
				cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_resolution[1])
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
				send_udp_data(detections)

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
				cap.set(cv2.CAP_PROP_FRAME_WIDTH, capture_resolution[0])
				cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_resolution[1])
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

			# Check	any	commands from UDP
			if not command_queue.empty():
				command	= command_queue.get().split(" ")
				if command[0] == "switch_camera":
					# ...
					pass

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
	