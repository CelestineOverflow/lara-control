#pragma once

#include <Arduino.h>

#ifndef HX717_DOUT_PIN
#define HX717_DOUT_PIN 11
#endif

#ifndef HX717_SCK_PIN
#define HX717_SCK_PIN 10
#endif

extern long SCALE_CALIBRATION_OFFSET;
extern float SCALE_CALIBRATION_FACTOR;

#define FIFO_SIZE                   3
#define OUTLIER_THRESHOLD           500.0

void initHX71708();
long readRaw();
float readHX71708();
void tare();
float readProcessed();