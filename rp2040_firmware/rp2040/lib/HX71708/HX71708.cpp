#include "HX71708.h"
#include <Arduino.h>

static float fifo[FIFO_SIZE];

long SCALE_CALIBRATION_OFFSET = -159795;
float SCALE_CALIBRATION_FACTOR = 231.0983;


static void fifo_init()
{
  int count = 0;
  while (count < FIFO_SIZE)
  {
    float reading = readProcessed();
    if (!isnan(reading))
    {
      fifo[count] = reading;
      count++;
    }
  }
}

void tare() {
    long readings[10];
    long firstReading = readRaw();
    int currentReading = 0;
    while (1) {
        long newReading = readRaw();
        if (newReading < firstReading + 100 && newReading > firstReading - 100) {
            Serial.println("Tare reading: " + String(newReading));
            readings[currentReading] = newReading;
            currentReading++;
            if (currentReading == 10) {
                break;
            }
        }
    }
    long sum = 0.0;
    for (int i = 0; i < 10; i++) {
        sum += readings[i];
    }
    SCALE_CALIBRATION_OFFSET = -(sum / 10);
}

void initHX71708()
{
  pinMode(HX717_SCK_PIN, OUTPUT);
  pinMode(HX717_DOUT_PIN, INPUT);
  digitalWrite(HX717_SCK_PIN, LOW);
  tare();
  fifo_init();
}

long readRaw()
{
  // Wait for DOUT to go LOW
  if (digitalRead(HX717_DOUT_PIN) == LOW)
  {
    delayMicroseconds(10);
    long reading = 0;

    // Read 24 bits
    for (int i = 0; i < 24; i++)
    {
      digitalWrite(HX717_SCK_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(HX717_SCK_PIN, LOW);
      reading <<= 1;
      reading |= digitalRead(HX717_DOUT_PIN);
    }

    // Sign extend if the 24th bit (MSB) is 1
    if (reading & 0x800000)
    {
      reading |= 0xFF000000;
    }

    // Extra pulses to finish the cycle
    for (int i = 0; i < 4; i++)
    {
      digitalWrite(HX717_SCK_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(HX717_SCK_PIN, LOW);
    }
    return reading;
  }
  return NAN;
}

float readProcessed()
{
  long reading = readRaw();
  if (!isnan(reading))
  {
    float _reading = (reading + SCALE_CALIBRATION_OFFSET);
    return _reading / SCALE_CALIBRATION_FACTOR;
  }
  return NAN;
}

static bool   outlierCandidateActive = false;
static float  outlierCandidateValue  = 0.0f;

float readHX71708()
{
    float reading = readProcessed();
    if (!isnan(reading))
    {
        float avg = (fifo[0] + fifo[1]) / 2.0f;
        if (outlierCandidateActive)
        {
            float diff = fabsf(reading - outlierCandidateValue);

            if (diff <= OUTLIER_THRESHOLD)
            {
                // The new reading matches the outlier candidate -> both are valid
                // So we shift in the candidate AND the new reading

                // First shift: put candidate at the end
                for (int i = 0; i < FIFO_SIZE - 1; i++)
                {
                    fifo[i] = fifo[i + 1];
                }
                fifo[FIFO_SIZE - 1] = outlierCandidateValue;

                // Second shift: put current reading at the end
                for (int i = 0; i < FIFO_SIZE - 1; i++)
                {
                    fifo[i] = fifo[i + 1];
                }
                fifo[FIFO_SIZE - 1] = reading;

                // Done with that candidate
                outlierCandidateActive = false;
            }
            else
            {
                // The outlier candidate was indeed crap. Discard it.
                outlierCandidateActive = false;

                // Now check if the current reading itself is suspicious
                if (fabsf(reading - avg) > OUTLIER_THRESHOLD)
                {
                    // Store the new outlier as a candidate
                    outlierCandidateValue  = reading;
                    outlierCandidateActive = true;
                }
                else
                {
                    // Current reading is fine, shift it in
                    for (int i = 0; i < FIFO_SIZE - 1; i++)
                    {
                        fifo[i] = fifo[i + 1];
                    }
                    fifo[FIFO_SIZE - 1] = reading;
                }
            }
        }
        else
        {
            // No existing candidate
            if (fabsf(reading - avg) > OUTLIER_THRESHOLD)
            {
                // Mark this reading as a candidate outlier to confirm on next sample
                outlierCandidateValue  = reading;
                outlierCandidateActive = true;
            }
            else
            {
                // Reading looks normal, shift it in
                for (int i = 0; i < FIFO_SIZE - 1; i++)
                {
                    fifo[i] = fifo[i + 1];
                }
                fifo[FIFO_SIZE - 1] = reading;
            }
        }
    }

    // Compute the average of the FIFO
    float sum = 0.0f;
    for (int i = 0; i < FIFO_SIZE; i++)
    {
        sum += fifo[i];
    }
    return sum / FIFO_SIZE;
}