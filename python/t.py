import pybullet as p
import time
import pybullet_data
import math

# File paths
robot_arm_urdf = r"C:\Users\nxp84358\Documents\GitHub\lara-control\static\urdf\lara10\lara10.urdf"

# Connect to physics client
physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -10)
planeId = p.loadURDF("plane.urdf")

# Load the robot arm URDF with a fixed base.
startPos = [0, 0, 1]
startOrientation = p.getQuaternionFromEuler([0, 0, 0])
robotArmId = p.loadURDF(robot_arm_urdf, startPos, startOrientation, useFixedBase=True)

# Determine the number of joints and assume the last joint is the end-effector.
num_joints = p.getNumJoints(robotArmId)
end_effector_index = num_joints - 1
print("Number of joints:", num_joints)

# Initial manual target (position and orientation euler angles)
target_position = [-0.131, -0.7, 0.128]  # x, y, z
target_euler = [0, 0, 3.14]             # roll, pitch, yaw

# Delta increments for manual control
delta_pos = 0.01
delta_angle = 0.05  # in radians

print("Manual control keys:")
print(" x: decrease 'j', increase 'l'")
print(" y: decrease 'k', increase 'i'")
print(" z: decrease 'o', increase 'u'")
print(" roll: decrease 's', increase 'w'")
print(" pitch: decrease 'd', increase 'a'")
print(" yaw: decrease 'c', increase 'z'")

# Main simulation loop
while True:
    keys = p.getKeyboardEvents()
    
    # Position control
    if ord('j') in keys and keys[ord('j')] & p.KEY_WAS_TRIGGERED:
        target_position[0] -= delta_pos
    if ord('l') in keys and keys[ord('l')] & p.KEY_WAS_TRIGGERED:
        target_position[0] += delta_pos
    if ord('k') in keys and keys[ord('k')] & p.KEY_WAS_TRIGGERED:
        target_position[1] -= delta_pos
    if ord('i') in keys and keys[ord('i')] & p.KEY_WAS_TRIGGERED:
        target_position[1] += delta_pos
    if ord('o') in keys and keys[ord('o')] & p.KEY_WAS_TRIGGERED:
        target_position[2] -= delta_pos
    if ord('u') in keys and keys[ord('u')] & p.KEY_WAS_TRIGGERED:
        target_position[2] += delta_pos

    # Orientation control (Euler angles)
    if ord('s') in keys and keys[ord('s')] & p.KEY_WAS_TRIGGERED:
        target_euler[0] -= delta_angle
    if ord('w') in keys and keys[ord('w')] & p.KEY_WAS_TRIGGERED:
        target_euler[0] += delta_angle
    if ord('d') in keys and keys[ord('d')] & p.KEY_WAS_TRIGGERED:
        target_euler[1] -= delta_angle
    if ord('a') in keys and keys[ord('a')] & p.KEY_WAS_TRIGGERED:
        target_euler[1] += delta_angle
    if ord('c') in keys and keys[ord('c')] & p.KEY_WAS_TRIGGERED:
        target_euler[2] -= delta_angle
    if ord('z') in keys and keys[ord('z')] & p.KEY_WAS_TRIGGERED:
        target_euler[2] += delta_angle

    # Get target orientation as quaternion from current euler values.
    target_orientation = p.getQuaternionFromEuler(target_euler)

    # Optionally print the current target (position and angles)
    print("Target position:", target_position, "Target Euler:", target_euler, end="\r")

    # Compute inverse kinematics for the desired target pose.
    joint_poses = p.calculateInverseKinematics(robotArmId, end_effector_index,
                                               target_position,
                                               target_orientation)
    # Command each joint with the computed angles.
    for joint_index in range(len(joint_poses)):
        p.setJointMotorControl2(robotArmId,
                                joint_index,
                                p.POSITION_CONTROL,
                                joint_poses[joint_index])

    # Step simulation.
    p.stepSimulation()
    time.sleep(1. / 240.)
