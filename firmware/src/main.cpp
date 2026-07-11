// Wazza wand firmware

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_SSD1306.h>
#include <FastLED.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

#include "config.h"
#include "secrets.h"

Adafruit_MPU6050 mpu;
Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
WebSocketsClient ws;
CRGB leds[NUM_LEDS];

bool mpuOk = false;
bool oledOk = false;
unsigned long lastGestureMs = 0;
unsigned long lastTelemetryMs = 0;

// OLED
void oledShow(const String &line1, const String &line2 = "") {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(0, 4);
  oled.println(line1);
  if (line2.length()) {
    oled.setCursor(0, 18);
    oled.println(line2);
  }
  oled.display();
}

// LEDs
void ledsFill(uint8_t r, uint8_t g, uint8_t b) {
  fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
  FastLED.show();
}

void ledsFlash(const CRGB &color, int times = 2, int onMs = 120) {
  for (int i = 0; i < times; i++) {
    fill_solid(leds, NUM_LEDS, color);
    FastLED.show();
    delay(onMs);
    FastLED.clear(true);
    delay(onMs);
  }
}

// WebSocket
void sendJson(JsonDocument &doc) {
  String out;
  serializeJson(doc, out);
  ws.sendTXT(out);
}

void sendEvent(const char *type, const char *value) {
  JsonDocument doc;
  doc["type"] = type;
  doc["value"] = value;
  doc["ms"] = millis();
  sendJson(doc);
}

void handleCommand(const String &payload) {
  JsonDocument doc;
  if (deserializeJson(doc, payload) != DeserializationError::Ok) return;
  const char *cmd = doc["cmd"] | "";

  if (strcmp(cmd, "led") == 0) {
    ledsFill(doc["r"] | 0, doc["g"] | 0, doc["b"] | 0);
  } else if (strcmp(cmd, "led_off") == 0) {
    FastLED.clear(true);
  } else if (strcmp(cmd, "oled") == 0) {
    oledShow(doc["line1"] | "", doc["line2"] | "");
  } else if (strcmp(cmd, "flash") == 0) {
    ledsFlash(CRGB(doc["r"] | 255, doc["g"] | 255, doc["b"] | 255),
              doc["times"] | 2);
  }
}

void onWsEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      sendEvent("hello", "wazza-wand");
      oledShow("Wazza online", WiFi.localIP().toString());
      break;
    case WStype_DISCONNECTED:
      oledShow("Backend lost", "reconnecting...");
      break;
    case WStype_TEXT:
      handleCommand(String((char *)payload, length));
      break;
    default:
      break;
  }
}

// Gestures
void detectGesture(const sensors_event_t &accel, const sensors_event_t &gyro) {
  unsigned long now = millis();
  if (now - lastGestureMs < GESTURE_COOLDOWN_MS) return;

  float ax = accel.acceleration.x;
  float ay = accel.acceleration.y;
  float az = accel.acceleration.z;
  float accelMag = sqrtf(ax * ax + ay * ay + az * az) - 9.81f;

  const char *gesture = nullptr;
  if (accelMag > FLICK_THRESHOLD) {
    gesture = "flick";
  } else if (gyro.gyro.z > SWIPE_THRESHOLD) {
    gesture = "swipe_left";
  } else if (gyro.gyro.z < -SWIPE_THRESHOLD) {
    gesture = "swipe_right";
  }

  if (gesture) {
    lastGestureMs = now;
    sendEvent("gesture", gesture);
    ledsFlash(CRGB::Purple, 1);
  }
}

// Telemetry
void sendTelemetry(const sensors_event_t &accel, const sensors_event_t &gyro) {
  JsonDocument doc;
  doc["type"] = "imu";
  doc["ax"] = accel.acceleration.x;
  doc["ay"] = accel.acceleration.y;
  doc["az"] = accel.acceleration.z;
  doc["gx"] = gyro.gyro.x;
  doc["gy"] = gyro.gyro.y;
  doc["gz"] = gyro.gyro.z;
  doc["ms"] = millis();
  sendJson(doc);
}

// Buttons
void pollButtons() {
  static bool lastAction = HIGH, lastBoot = HIGH;
  bool action = digitalRead(PIN_BTN_ACTION);
  bool boot = digitalRead(PIN_BTN_BOOT);

  if (action == LOW && lastAction == HIGH) sendEvent("button", "action");
  if (boot == LOW && lastBoot == HIGH) sendEvent("button", "boot");

  lastAction = action;
  lastBoot = boot;
}

// Setup
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_ACTION, INPUT_PULLUP);
  pinMode(PIN_BTN_BOOT, INPUT_PULLUP);

  FastLED.addLeds<WS2812B, PIN_WS2812_DIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(80);
  ledsFill(0, 0, 30);

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  oledShow("Wazza booting...");

  mpuOk = mpu.begin();
  if (mpuOk) {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);
  } else {
    Serial.println("MPU6050 not found!");
    oledShow("IMU missing!");
  }

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  oledShow("WiFi...", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.printf("\nWiFi up: %s\n", WiFi.localIP().toString().c_str());

  ws.begin(BACKEND_HOST, BACKEND_PORT, "/");
  ws.onEvent(onWsEvent);
  ws.setReconnectInterval(2000);

  ledsFill(0, 30, 0);
}

// Loop
void loop() {
  ws.loop();
  pollButtons();

  if (mpuOk) {
    sensors_event_t accel, gyro, temp;
    mpu.getEvent(&accel, &gyro, &temp);
    detectGesture(accel, gyro);

    unsigned long now = millis();
    if (TELEMETRY_INTERVAL_MS > 0 && now - lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
      lastTelemetryMs = now;
      if (ws.isConnected()) sendTelemetry(accel, gyro);
    }
  }

  delay(1000 / GESTURE_SAMPLE_HZ);
}
