import arm_api

arm_api.set_heater(175) # Set the heater to 175 degrees
'''
Set the heater to 175 degrees C, returns inmediately
'''
arm_api.set_heater(0) # Set the heater to off
'''
Set the heater off, returns inmediately
'''
arm_api.wait_for_temperature(60) # Set the heater to 60 degrees and wait for it to reach that temperature
'''
Set the heater to 60 degrees C, returns only once the temperature is reached
'''

