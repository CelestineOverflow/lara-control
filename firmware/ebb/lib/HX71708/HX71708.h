#pragma once

#include <Arduino.h>


#define HX717_DOUT_PIN PB4
#define HX717_SCK_PIN PB3

extern long SCALE_CALIBRATION_OFFSET;
extern float SCALE_CALIBRATION_FACTOR;

#define FIFO_SIZE                   5
#define OUTLIER_THRESHOLD           100.0

void initHX71708();
long readRaw();
long readOffset();
float readHX71708();
void tare();
float readProcessed();