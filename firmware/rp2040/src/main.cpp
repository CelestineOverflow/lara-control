#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MAX31865.h>
#include <ArduinoJson.h>
#include <NeoPixelBus.h>
#define RREF 402.0
#define RNOMINAL 100.0
#define pump_pwm 9
#define fan_pwm 5
#define heater_pwm 12
#define DYLY_LOADCELL
#define HX717_SCK 10
#define HX717_DOUT 11
#if defined(DYLY_LOADCELL)
#define SCALE_CALIBRATION_FACTOR 231.0983
#define SCALE_CALIBRATION_OFFSET -25000.00
#define SK6812_PIN 18
#endif
Adafruit_MAX31865 thermo = Adafruit_MAX31865(1, 0, 3, 2); // Adjusted SPI pins
int pump_percentage = 0;
int fan_percentage = 0;
int heater_percentage = 0;
#define LED_COUNT 7

NeoPixelBus<NeoGrbFeature, NeoWs2812xMethod> strip(LED_COUNT, SK6812_PIN);
#define colorSaturation 255

RgbColor red(colorSaturation, 0, 0);
RgbColor green(0, colorSaturation, 0);
RgbColor blue(0, 0, colorSaturation);
RgbColor white(colorSaturation);
RgbColor black(0);

HslColor hslRed(red);
HslColor hslGreen(green);
HslColor hslBlue(blue);
HslColor hslWhite(white);
HslColor hslBlack(black);


#define FIFO_SIZE 10
float fifo[FIFO_SIZE];


float readHX71708()
{
  if (digitalRead(HX717_DOUT) == LOW)
  {
    delayMicroseconds(10);
    long reading = 0; 
    for (int i = 0; i < 24; i++)
    {
      // Most significant bit first
      digitalWrite(HX717_SCK, HIGH);
      delayMicroseconds(1);
      digitalWrite(HX717_SCK, LOW);
      reading = reading << 1;
      reading = reading | digitalRead(HX717_DOUT);
    }
    // Sign extend if necessary
    if (reading & 0x800000)
    {                        // Check if the 24th bit is 1 (negative)
      reading |= 0xFF000000; // Extend sign for correct 32-bit representation
    }
    // Extra pulses to finish reading cycle
    for (int i = 0; i < 4; i++)
    {
      digitalWrite(HX717_SCK, HIGH);
      delayMicroseconds(1);
      digitalWrite(HX717_SCK, LOW);
    }
    return ((reading + SCALE_CALIBRATION_OFFSET) / SCALE_CALIBRATION_FACTOR);
  }
  return NAN; 
}

void changeBrightness(int brightness)
{
  for (int i = 0; i < LED_COUNT; i++)
  {
    RgbColor newColor(brightness);
    strip.SetPixelColor(i, newColor);
    strip.Show();
  }
  strip.Show();
}

void reportState()
{
  StaticJsonDocument<256> doc;
  doc["pump"] = pump_percentage;
  doc["fan"] = fan_percentage;
  doc["heater"] = heater_percentage;
  doc["force"] = fifo[0];
  doc["temperature"] = thermo.temperature(RNOMINAL, RREF);
  // doc["temperature"] = 24.5;
  serializeJson(doc, Serial);
  Serial.println();
}
void processCommand()
{
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any leading/trailing whitespace
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, command);
    if (error)
    {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.c_str());
      return;
    }
    // Check and set PWM values based on the JSON keys
    if (doc.containsKey("pump"))
    {
      int pump_value = doc["pump"];
      pump_value = constrain(pump_value, 0, 100);
      pump_percentage = pump_value;
      analogWrite(pump_pwm, map(pump_value, 0, 100, 0, 255));
    }
    if (doc.containsKey("heater"))
    {
      int heater_value = doc["heater"];
      heater_value = constrain(heater_value, 0, 100);
      heater_percentage = heater_value;
      analogWrite(heater_pwm, map(heater_value, 0, 100, 0, 255));
    }
    if (doc.containsKey("fan"))
    {
      int fan_value = doc["fan"];
      fan_value = constrain(fan_value, 0, 100);
      fan_percentage = fan_value;
      analogWrite(fan_pwm, map(fan_value, 0, 100, 0, 255));
    }
    if (doc.containsKey("brightness"))
    {
      int brightness = doc["brightness"];
      brightness = constrain(brightness, 0, 255);
      changeBrightness(brightness);
    }
    // Send back a response upon completion
    StaticJsonDocument<128> responseDoc;
    responseDoc["status"] = "ok";
    serializeJson(responseDoc, Serial);
    Serial.println();
  }
}
void setup()
{
  Serial.begin(115200);
  thermo.begin(MAX31865_2WIRE);
  pinMode(pump_pwm, OUTPUT);
  pinMode(fan_pwm, OUTPUT);
  pinMode(heater_pwm, OUTPUT);
  pinMode(HX717_SCK, OUTPUT);
  pinMode(HX717_DOUT, INPUT);
  // Initialize PWM outputs to 0
  analogWrite(pump_pwm, 0);
  analogWrite(fan_pwm, 0);
  // analogWrite(heater_pwm, 100);
  digitalWrite(heater_pwm, LOW);//active high
  // Initialize SK6812 RGB LED
  strip.Begin();
  strip.Show();
  // Init the fifo with the first reading from hx711
  for (int i = 0; i < FIFO_SIZE; i++)
  {
    while(1){
      delay(10);
      float reading = readHX71708();
      if (!isnan(reading))
      {
      fifo[i] = reading;
      break;
      }

    }
  }
  for (int i = 0; i < LED_COUNT; i++)
  {
    strip.SetPixelColor(i, white);
  }
  strip.Show();
}

float getAverage()
{
  float sum = 0;
  for (int i = 0; i < FIFO_SIZE; i++)
  {
    sum += fifo[i];
  }
  return sum / FIFO_SIZE;
}


const float threshold = 500.0;

void loop()
{
  float _latest = readHX71708();
  if (!isnan(_latest))
  {
    
    //check the new reading against the previous reading
    //if the difference is greater than threshold.0, then we have a spike 
    //and we should ignore the reading
    float average = getAverage();
  //shift the values in the fifo
    for (int i = 0; i < FIFO_SIZE - 1; i++)
    {
      fifo[i] = fifo[i + 1];
    }
    if (abs(_latest - average) < threshold)
    {
      
      fifo[FIFO_SIZE - 1] = _latest;
    }
    else
    {
      //add the avg +- threshold value to the fifo
      bool isPositive = _latest > average;
      fifo[FIFO_SIZE - 1] = average + (isPositive ? threshold : -threshold);
    }
    
  }
  processCommand();
  reportState();
  delay(1);
}