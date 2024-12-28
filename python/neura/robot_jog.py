from neurapy.robot import Robot
robot = Robot()
robot.turn_on_jog(
    jog_velocity=[0, 0, 1, 0, 0, 0], 
    jog_type='Cartesian'
)
robot.jog(set_jogging_external_flag = 1)
i = 0
while(i < 1000):
    robot.jog(set_jogging_external_flag = 1)
    i+=1
robot.turn_off_jog()