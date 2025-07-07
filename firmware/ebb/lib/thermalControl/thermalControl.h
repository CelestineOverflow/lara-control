#pragma once
#include <Arduino.h>

#define MIN_TEMP     -60.0
#define MAX_TEMP     250.0

void setTargetTemperature(float targetTemperature);
int updateThermalControl(float currentTemperature);
float getTargetTemperature();
int getHeater();