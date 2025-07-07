#include "thermalControl.h"
#include <Arduino.h>

static float Kp = 20.0, Ki = 0.2, Kd = 5.0, integralTerm = 0.0, lastError = 0.0;
static unsigned long lastPidTime = 0;
static float setTemperature = 0.0;
static bool enalbleThermalControl = true;
static int heaterPercentage = 0;

void setTargetTemperature(float targetTemperature){
    if (targetTemperature < MIN_TEMP) targetTemperature = MIN_TEMP;
    if (targetTemperature > MAX_TEMP) targetTemperature = MAX_TEMP;
    setTemperature = targetTemperature;
    integralTerm   = 0.0; // Reset integral term on new setpoint
    lastError      = 0.0; // Reset last error on new setpoint
    lastPidTime    = millis(); // Reset PID time
    heaterPercentage = 0; // Reset heater percentage
}

int updateThermalControl(float currentTemperature){
  if(!enalbleThermalControl) {
    return 0; // Thermal control is disabled
  }
  unsigned long currentTime = millis();
  float dt = (currentTime - lastPidTime) / 1000.0f;
  lastPidTime = currentTime;
  if (dt <= 0.0f) return heaterPercentage; // Avoid division by zero

  float error = setTemperature - currentTemperature;
  integralTerm += (error * dt);
  //clamp integral term to prevent windup
  if (integralTerm > 100) integralTerm = 100;
  if (integralTerm < 0)   integralTerm = 0;
  float derivative = (error - lastError) / dt;
  float output = (Kp * error) + (Ki * integralTerm) + (Kd * derivative);
  lastError = error;

  if (output < 0)   output = 0;
  if (output > 100) output = 100;

  heaterPercentage = (int)output;
  return heaterPercentage; // Return the heater duty cycle
}




float getTargetTemperature() {
    return setTemperature;
}

int getHeater() {
    return heaterPercentage;
}