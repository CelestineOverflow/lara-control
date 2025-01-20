#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_MAX31865.h"
#include <ArduinoJson.h>
#include <NeoPixelBus.h>
#include "HX71708.h"

#define RREF         402.0
#define RNOMINAL     100.0
#define pump_pwm     9
#define fan_pwm      5
#define heater_pwm   12
#define SK6812_PIN   18

// Temperature boundaries
#define MIN_TEMP     -60.0
#define MAX_TEMP     250.0

// PID constants
float Kp = 20.0, Ki = 0.2, Kd = 5.0;

// Setpoint
float setTemperature = 0.0;
bool  hasSetTemp     = false;

// PID terms
float integralTerm   = 0.0;
float lastError      = 0.0;
unsigned long lastPidTime = 0;

bool reportStateFlag = false;


float lastTemp = 0.0;
Adafruit_MAX31865 thermo = Adafruit_MAX31865(1, 0, 3, 2);

int pump_percentage   = 0;
int fan_percentage    = 0;
int heater_percentage = 0;

#define LED_COUNT 7
bool ledState[LED_COUNT] = {true, true, true, true, true, true, true};

// *** We store the color that each LED should have when it's on. ***
NeoPixelBus<NeoGrbFeature, NeoWs2812xMethod> strip(LED_COUNT, SK6812_PIN);
RgbColor savedColor[LED_COUNT]; // Each LED’s saved color

// Thermal runaway check
static const unsigned long THERMAL_RUNAWAY_CHECK_INTERVAL = 30000;
static const float DELTA_IMPROVEMENT_THRESHOLD = 3.0;
static const float STABLE_THRESHOLD            = 5.0;

unsigned long lastRunawayCheckTime  = 0;
float         lastRunawayCheckDelta = 0.0;

int  errorCode             = 0;
bool thermalRunawayCleared = false;
#define ERR_NONE            0
#define ERR_THERMAL_RUNAWAY 1


// Global "previous" state tracking
static int   oldPump   = -1;
static int   oldFan    = -1;
static float oldForce  = NAN;

// For temperature objects, we might track each sub-field separately
static float oldTemp   = NAN;
static bool  oldHasSetTemp = false;
static float oldSetTemp    = NAN;

// Track LED states for change detection
static bool  oldLedState[LED_COUNT] = {false, false, false, false, false, false, false};


// Quick brightness function
void changeBrightness(int brightness) {
  // Just modifies each LED’s brightness if it’s “on”
  for (int i = 0; i < LED_COUNT; i++) {
    if (ledState[i]) {
      // Convert saved color to HSB, change only brightness
      HsbColor hsb(savedColor[i]);
      hsb.B = (float)brightness / 255.0f; 
      RgbColor newCol(hsb);
      savedColor[i] = newCol;  // Keep the new brightness in savedColor
      strip.SetPixelColor(i, newCol);
    } else {
      // LED is off, keep it off
      strip.SetPixelColor(i, RgbColor(0, 0, 0));
    }
  }
  strip.Show();
}

// Convert HSL to RGB for NeoPixelBus
void setHSL(float hue, float sat, float light) {
  // We apply the same color to all LEDs that are turned “on”.
  HsbColor hsb(hue / 360.0f, sat / 100.0f, light / 100.0f);
  RgbColor rgb(hsb);

  // Update savedColor for each LED that’s on, but leave off ones black.
  for (int i = 0; i < LED_COUNT; i++) {
    if (ledState[i]) {
      savedColor[i] = rgb; 
      strip.SetPixelColor(i, rgb);
    } else {
      strip.SetPixelColor(i, RgbColor(0, 0, 0));
    }
  }
  strip.Show();
}

void controlTemperature(float currentTemp) {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastPidTime) / 1000.0f;
  lastPidTime = currentTime;
  if (dt <= 0.0f) return;

  float error = setTemperature - currentTemp;
  integralTerm += (error * dt);
  //clamp integral term to prevent windup
  if (integralTerm > 100) integralTerm = 100;
  if (integralTerm < 0)   integralTerm = 0;
  float derivative = (error - lastError) / dt;
  float output = (Kp * error) + (Ki * integralTerm) + (Kd * derivative);
  lastError = error;

  if (output < 0)   output = 0;
  if (output > 100) output = 100;

  heater_percentage = (int)output;
  analogWrite(heater_pwm, map(heater_percentage, 0, 100, 0, 255));
}

// void checkThermalRunaway() {
//   float currentDelta = fabs(setTemperature - lastTemp);
//   if (currentDelta <= STABLE_THRESHOLD) {
//     lastRunawayCheckTime  = millis();
//     lastRunawayCheckDelta = currentDelta;
//     return;
//   }

//   unsigned long now = millis();
//   if (now - lastRunawayCheckTime >= THERMAL_RUNAWAY_CHECK_INTERVAL) {
//     float improvement = lastRunawayCheckDelta - currentDelta;
//     if (heater_percentage > 0 && improvement < DELTA_IMPROVEMENT_THRESHOLD) {
//       errorCode = ERR_THERMAL_RUNAWAY;
//     }
//     lastRunawayCheckTime  = now;
//     lastRunawayCheckDelta = currentDelta;
//   }
// }

void reportError(int code) {
  if (code == ERR_THERMAL_RUNAWAY) {
    DynamicJsonDocument doc(128);
    doc["error"] = "THERMAL_RUNAWAY";
    doc["msg"]   = "No significant improvement towards setpoint; heater disabled.";
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void handleErrors() {
  if (errorCode == ERR_NONE) return;
  heater_percentage = 0;
  analogWrite(heater_pwm, 0);
  reportError(errorCode);
}

void clearError() {
  errorCode             = ERR_NONE;
  thermalRunawayCleared = true;
}

void serial_connected_sequence() {
  tare();
  // turn on pump, fan
  pump_percentage = 100;
  fan_percentage  = 100;
  analogWrite(pump_pwm, map(pump_percentage, 0, 100, 0, 255));
  analogWrite(fan_pwm,  map(fan_percentage,  0, 100, 0, 255));

  for (int i = 0; i < LED_COUNT; i++) {
    strip.SetPixelColor(i, RgbColor(0, 0, 255));
    strip.Show();
    delay(100);
  }
  for (int i = 0; i < LED_COUNT; i++) {
    strip.SetPixelColor(i, RgbColor(0, 255, 0));
    strip.Show();
    delay(100);
  }
  for (int i = 0; i < LED_COUNT; i++) {
    strip.SetPixelColor(i, RgbColor(255, 0, 0));
    strip.Show();
    delay(100);
  }
  changeBrightness(255);
  pump_percentage = 0;
  fan_percentage  = 0;
  analogWrite(pump_pwm, 0);
  analogWrite(fan_pwm,  0);

}
bool firstrun = true;
DynamicJsonDocument start_json(256);

void reportState() {
  DynamicJsonDocument doc(256);
  bool somethingChanged = false;

  // 1) Pump
  if (pump_percentage != oldPump) {
    doc["pump"] = pump_percentage;   // only send if changed
    oldPump = pump_percentage;
    somethingChanged = true;
  }

  // 2) Fan
  if (fan_percentage != oldFan) {
    doc["fan"] = fan_percentage;
    oldFan = fan_percentage;
    somethingChanged = true;
  }

  // 3) Force (load cell reading)
  float currentForce = readHX71708();
  // if oldForce is NaN or differs enough from currentForce
  if (isnan(oldForce) || fabs(oldForce - currentForce) > 0.0001) {
    doc["force"] = currentForce;
    oldForce = currentForce;
    somethingChanged = true;
  }

  // 4) LED array
  // We also want to add a “ledChanged” flag if *any* LED differs
  bool ledChanged = false;
  for (int i = 0; i < LED_COUNT; i++) {
    if (oldLedState[i] != ledState[i]) {
      ledChanged = true;
      break;
    }
  }
  if (ledChanged) {
    JsonArray ledArr = doc.createNestedArray("leds");
    for (int i = 0; i < LED_COUNT; i++) {
      ledArr.add(ledState[i]);
      oldLedState[i] = ledState[i];  // update old
    }
    // You could also add a separate boolean to indicate that the LED array changed:
    doc["ledChanged"] = true;
    somethingChanged = true;
  }

  // 5) Temperature object (only if there’s new data or something changed)
  //    We can create a sub-object and only populate changed fields inside it.
  float temp = thermo.temperature(RNOMINAL, RREF);
  bool tempObjectNeeded = false;
  DynamicJsonDocument temperatureObj(64);

  if (!isnan(temp)) {
    temperatureObj["current"] = temp;
    temperatureObj["heater"] = heater_percentage;
    temperatureObj["target"] = setTemperature;
    oldTemp = temp;
    tempObjectNeeded = true;
  }

  // If we needed the sub-object for anything
  if (tempObjectNeeded) {
    doc["temperature"] = temperatureObj;
    somethingChanged = true;
  }

  // 6) Errors: if you want partial updates for error states as well
  static int oldFault     = -999;
  static int oldErrorCode = -999;
  int faultReading = thermo.readFault();
  if (faultReading != oldFault || errorCode != oldErrorCode) {
    JsonObject errors = doc.createNestedObject("errors");
    errors["fault"]     = faultReading;
    errors["errorCode"] = errorCode;
    oldFault     = faultReading;
    oldErrorCode = errorCode;
    somethingChanged = true;
  }

  // 7) If something changed, serialize. If nothing changed, do nothing.
  if (somethingChanged) {
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void processCommand() {
  if (!Serial.available()) return;
  String command = Serial.readStringUntil('\n');
  command.trim();

  DynamicJsonDocument doc(256);
  DeserializationError error = deserializeJson(doc, command);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (!doc["connected"].isNull()) {
    reportStateFlag = true;
    Serial.println("Connected! Reporting state...");
    serial_connected_sequence();
  }

  if (!doc["pump"].isNull()) {
    int val = constrain(doc["pump"].as<int>(), 0, 100);
    pump_percentage = val;
    analogWrite(pump_pwm, map(val, 0, 100, 0, 255));
  }

  if (!doc["heater"].isNull()) {
    int val = constrain(doc["heater"].as<int>(), 0, 100);
    heater_percentage = val;
    analogWrite(heater_pwm, map(val, 0, 100, 0, 255));
  }

  if (!doc["fan"].isNull()) {
    int val = constrain(doc["fan"].as<int>(), 0, 100);
    fan_percentage = val;
    analogWrite(fan_pwm, map(val, 0, 100, 0, 255));
  }

  // The part that toggles LEDs on/off based on your boolean array
  if (!doc["leds"].isNull()) {
    JsonArray leds = doc["leds"].as<JsonArray>();
    for (int i = 0; i < LED_COUNT; i++) {
      ledState[i] = leds[i];
    }
    // Now apply the saved color if on, or black if off
    for (int i = 0; i < LED_COUNT; i++) {
      if (ledState[i]) {
        strip.SetPixelColor(i, savedColor[i]);
      } else {
        strip.SetPixelColor(i, RgbColor(0, 0, 0));
      }
    }
    strip.Show();
  }

  if (!doc["brightness"].isNull()) {
    int val = constrain(doc["brightness"].as<int>(), 0, 255);
    changeBrightness(val);
  }

  // HSL
  // If you set a new HSL color, it overwrites the savedColor for each LED that’s on
  if (!doc["hue"].isNull() && !doc["sat"].isNull() && !doc["light"].isNull()) {
    float h = doc["hue"].as<float>();
    float s = doc["sat"].as<float>();
    float l = doc["light"].as<float>();
    setHSL(h, s, l);
  }

  if (!doc["setTemp"].isNull()) {
    float requestedSetpoint = doc["setTemp"].as<float>();
    if (requestedSetpoint < MIN_TEMP) requestedSetpoint = MIN_TEMP;
    if (requestedSetpoint > MAX_TEMP) requestedSetpoint = MAX_TEMP;
    setTemperature         = requestedSetpoint;
    hasSetTemp             = true;
    lastRunawayCheckTime   = millis();
    lastRunawayCheckDelta  = fabs(setTemperature - lastTemp);
  }

  if (!doc["Kp"].isNull()) Kp = doc["Kp"].as<float>();
  if (!doc["Ki"].isNull()) Ki = doc["Ki"].as<float>();
  if (!doc["Kd"].isNull()) Kd = doc["Kd"].as<float>();

  if (!doc["clearError"].isNull()) {
    clearError();
  }

  DynamicJsonDocument responseDoc(128);
  responseDoc["status"] = "ok";
  serializeJson(responseDoc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  Serial.println("Starting up...");
  thermo.begin(MAX31865_2WIRE);
  pinMode(pump_pwm,   OUTPUT);
  pinMode(fan_pwm,    OUTPUT);
  pinMode(heater_pwm, OUTPUT);
  initHX71708();
  analogWrite(pump_pwm, 0);
  analogWrite(fan_pwm,  0);
  digitalWrite(heater_pwm, LOW);
  strip.Begin();
  // By default, let's store them as white
  for (int i = 0; i < LED_COUNT; i++) {
    savedColor[i] = RgbColor(255, 255, 255); 
    // If ledState[i] is true, turn it on. Otherwise, black.
    if (ledState[i]) {
      strip.SetPixelColor(i, savedColor[i]);
    } else {
      strip.SetPixelColor(i, RgbColor(0, 0, 0));
    }
  }
  strip.Show();
  lastPidTime          = millis();
  lastRunawayCheckTime = millis();
}

void loop() {
  processCommand();

  if (errorCode == ERR_NONE) {
    float measuredTemp = thermo.temperature(RNOMINAL, RREF);
    uint8_t fault = thermo.readFault();

    if (fault) {
      heater_percentage = 0;
      analogWrite(heater_pwm, 0);
      thermo.clearFault();
    } else {
      if (!isnan(measuredTemp)) {
        lastTemp = measuredTemp;
      }
      if (hasSetTemp && lastTemp >= MIN_TEMP && lastTemp <= MAX_TEMP) {
        controlTemperature(lastTemp);
      } else {
        heater_percentage = 0;
        analogWrite(heater_pwm, 0);
      }
    }
  }
  if (reportStateFlag) {
    reportState();
  }
  // reportState();
  handleErrors();
  delay(1);
}
