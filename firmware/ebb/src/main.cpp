#include <Arduino.h>
#include <HardwareSerial.h>
#include <Adafruit_NeoPixel.h>
#include "Adafruit_MAX31865.h"
#include "HX71708.h"
#include <ArduinoJson.h>
#include "thermalControl.h"
// Peripherals
#define PUMP_PWN PA0
#define FAN_PWM PA1
#define HEATER_PWM PB13
// Stepper Motor 1
#define TMC2209_STEPPER1_EN PD2
#define TMC2209_STEPPER1_STEP PD0
#define TMC2209_STEPPER1_DIR PD1
#define TMC2209_STEPPER1_UART PA15
// Endstops
#define ENDSTOP1 PB6
#define ENDSTOP2 PB5
#define ENDSTOP3 PB7
// RGB LED
#define SK6812_PIN PD3
#define SK6812_NUM_LEDS 6

// MAX31865
#define MAX31865_CS PA4
#define MAX31865_SCLK PA5
#define MAX31865_MISO PA6
#define MAX31865_MOSI PA7
// ADXL345
#define ADXL345_CS PB12
#define ADXL345_SCLK PB10
#define ADXL345_MISO PB2
#define ADXL345_MOSI PB11
#define RREF 430.0
#define RNOMINAL 100.0
// ADC
#define ADChn PB1
// Temperature boundaries

Adafruit_NeoPixel pixels(SK6812_NUM_LEDS, SK6812_PIN, NEO_GRB + NEO_KHZ800);
bool ledState[SK6812_NUM_LEDS] = {true, true, true, true, true, true};

//{"color":[{"r":255,"g":0,"b":0},{"r":0,"g":255,"b":0},{"r":0,"g":0,"b":255},{"r":255,"g":255,"b":0},{"r":0,"g":255,"b":255},{"r":255,"g":0,"b":255}]}

uint32_t savedColor[SK6812_NUM_LEDS] = {0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0x00FFFF, 0xFF00FF}; // Default colors for each LED

Adafruit_MAX31865 thermo = Adafruit_MAX31865(MAX31865_CS, MAX31865_MOSI, MAX31865_MISO, MAX31865_SCLK);
// Global Variables
// PID constants
static int pump_percentage = 0;
static int fan_percentage = 0;
static unsigned int previous_pump_duty_cycle = 0;
static unsigned int previous_fan_duty_cycle = 0;
static int heater_duty_cycle = 0;

// Other
static bool reportStateFlag = false;
#include "stm32g0xx.h"
void setup()
{
  analogWrite(PUMP_PWN, 0);
  analogWrite(FAN_PWM, 0);
  analogWrite(HEATER_PWM, 0);
  Serial.begin(115200);
  while (!Serial)
    delay(10);
  Serial.println("Starting up...");
  thermo.begin(MAX31865_2WIRE);
  thermo.autoConvert(true);
  Serial.println("Thermocouple initialized.");
  pixels.begin();
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    pixels.setPixelColor(i, savedColor[i]);
    pixels.show(); 
    delay(100); 
  }
  pixels.show(); 
  Serial.println("HX71708 ini...");
  initHX71708();
  Serial.println("HX71708 initialized.");
  Serial.println("finish up...");
}

long lastCallTime = 0;               // Variable to store the last call time for non-blocking read
long lasttemperature_read = 0;       // Variable to store the last temperature read time
long lasttemperature_read_valid = 0; // Variable to store the last valid temperature read time

void reportState()
{
  DynamicJsonDocument doc(256);
  bool somethingChanged = false;
  // 1) Pump
  if (pump_percentage != previous_pump_duty_cycle)
  {
    doc["pump"] = pump_percentage;
    previous_pump_duty_cycle = pump_percentage;
    somethingChanged = true;
  }

  // 2) Fan
  if (fan_percentage != previous_fan_duty_cycle)
  {
    doc["fan"] = fan_percentage;
    previous_fan_duty_cycle = fan_percentage;
    somethingChanged = true;
  }

  // 3) Force (load cell reading)
  float currentForce = readHX71708();
  if (!isnan(currentForce))
  {
    doc["force"] = currentForce;
    somethingChanged = true;
  }
  // 4) temperature
  if (lasttemperature_read == 0 || millis() - lasttemperature_read > 100)
  {
    lasttemperature_read = millis();
    float temp = thermo.temperature(RNOMINAL, RREF);
    DynamicJsonDocument temperatureObj(64);
    if (!isnan(temp))
    {
      temperatureObj["current"] = temp;
      temperatureObj["heater"] = getHeater();
      temperatureObj["target"] = getTargetTemperature();
      doc["temperature"] = temperatureObj;
      somethingChanged = true;
      // if temperature is above 60 degrees, set the fan from 20% to 100% based on the temperature up to 150c
      if (temp > 60.0)
      {
        fan_percentage = map(temp, 60, 150, 40, 100);
        analogWrite(FAN_PWM, map(fan_percentage, 0, 100, 0, 255));
        doc["fan"] = fan_percentage;
      }
      else
      {
        fan_percentage = 0; // turn off fan if temperature is below 60 degrees
        analogWrite(FAN_PWM, 0);
      }
      analogWrite(HEATER_PWM, map(updateThermalControl(temp), 0, 100, 0, 255));
      lasttemperature_read_valid = millis(); // Update the last valid temperature read time
    }
  }

  if (somethingChanged)
  {
    serializeJson(doc, Serial);
    Serial.println();
  }
}


#define BOOTLOADER_START 0x1FFF0000U   // AN2606 – system memory base :contentReference[oaicite:0]{index=0}

void __attribute__((noreturn)) enterBootloader()
{
    typedef void (*JumpFunc)(void);
    uint32_t bootAddr = BOOTLOADER_START;

    __disable_irq();             // 1. no interrupts

    /* 2. put the chip back to reset-like state */
    HAL_RCC_DeInit();
    HAL_DeInit();
    SysTick->CTRL = 0;

    /* 3. remap system memory at 0x0000_0000 */
    SYSCFG->CFGR1 = (SYSCFG->CFGR1 & ~SYSCFG_CFGR1_MEM_MODE_Msk) |
                    (0x1 << SYSCFG_CFGR1_MEM_MODE_Pos);   // MEM_MODE = 0b01

    /* 4. set MSP to the bootloader’s stack pointer */
    __set_MSP(*((uint32_t *)bootAddr));

    /* 5. jump to its reset handler */
    JumpFunc bootJump = (JumpFunc)(*((uint32_t *)(bootAddr + 4)));
    bootJump();                  // never returns
    while (1);                   // safety
}

void serial_connected_sequence()
{
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    pixels.setPixelColor(i, pixels.Color(0, 0, 255));
    pixels.show();
    delay(100);
  }
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    pixels.setPixelColor(i, pixels.Color(0, 255, 0));
    pixels.show();
    delay(100);
  }
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    pixels.setPixelColor(i, pixels.Color(255, 0, 0));
    pixels.show();
    delay(100);
  }
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    savedColor[i] = pixels.Color(255, 255, 255); // default white
    pixels.setPixelColor(i, savedColor[i]);
    pixels.show();
    delay(100);
  }
}

void changeBrightness(int brightness)
{
  // Just modifies each LED’s brightness if it’s “on”
  for (int i = 0; i < SK6812_NUM_LEDS; i++)
  {
    if (ledState[i])
    {
      pixels.setBrightness(brightness);
    }
    else
    {
      // LED is off, keep it off
      pixels.setPixelColor(i, pixels.Color(0, 0, 0));
    }
  }
  pixels.show();
}

void processCommand()
{
  if (!Serial.available())
    return;
  String command = Serial.readStringUntil('\n');
  command.trim();

  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, command);
  if (error)
  {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (!doc["connected"].isNull())
  {
    reportStateFlag = true;
    Serial.println("Connected! Reporting state...");
    serial_connected_sequence();
  }
  if (!doc["tare"].isNull())
  {
    tare();
  }
  if (!doc["pump"].isNull())
  {
    int val = constrain(doc["pump"].as<int>(), 0, 100);
    pump_percentage = val;
    analogWrite(PUMP_PWN, map(val, 0, 100, 0, 255));
  }
  if (!doc["leds"].isNull())
  {
    JsonArray leds = doc["leds"].as<JsonArray>();
    for (int i = 0; i < SK6812_NUM_LEDS; i++)
    {
      ledState[i] = leds[i].as<bool>();
      pixels.setPixelColor(i,
                           ledState[i] ? savedColor[i] : pixels.Color(0, 0, 0));
    }
    pixels.show();
  }

  if (!doc["brightness"].isNull())
  {
    int val = constrain(doc["brightness"].as<int>(), 0, 255);
    changeBrightness(val);
  }

  // color command
  if (!doc["color"].isNull())
  {
    JsonArray colors = doc["color"].as<JsonArray>();
    for (int i = 0; i < SK6812_NUM_LEDS && i < colors.size(); i++)
    {
      if (colors[i].is<JsonObject>())
      {
        JsonObject c = colors[i];
        uint32_t col = pixels.Color(c["r"] | 0, c["g"] | 0, c["b"] | 0);
        savedColor[i] = col;
        ledState[i] = true; // 2️⃣ force ON
        pixels.setPixelColor(i, col);
      }
    }
    pixels.show();
  }
  if (!doc["setTemp"].isNull())
  {
    float requestedSetpoint = doc["setTemp"].as<float>();
    setTargetTemperature(requestedSetpoint);
  }

  if (!doc["bootloader"].isNull() && doc["bootloader"].as<bool>())
  {
      Serial.println("Jumping to bootloader…");
      Serial.flush();              // make sure the ACK is out
      enterBootloader();           // never returns
  }

  if (!doc["setTemp"].isNull())
  {
    float requestedSetpoint = doc["setTemp"].as<float>();
    setTargetTemperature(requestedSetpoint);
  }

  DynamicJsonDocument responseDoc(128);
  responseDoc["status"] = "ok";
  serializeJson(responseDoc, Serial);
  Serial.println();
}

void loop()
{
  processCommand();
  if (reportStateFlag)
  {
    reportState();
  }
  delay(100); // Adjust the delay as needed
}
