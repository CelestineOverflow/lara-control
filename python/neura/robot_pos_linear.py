from neurapy.robot import Robot
r = Robot()
linear_property = {
 "speed": 0.008,
 "acceleration": 1.0,
 "blend_radius": 0.005,
 "target_pose": [
    [
            -0.084,
            -0.5305,
            0.3,
            3.141592653589793,
            0.0,
            0.0
    ],
    [
            -0.084,
            -0.5305,
            0.6,
            3.141592653589793,
            0.0,
            0.0
    ],
 ],
 "current_joint_angles":r.robot_status("jointAngles"),
 "weaving":True,
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
r.move_linear(**linear_property)
r.stop()