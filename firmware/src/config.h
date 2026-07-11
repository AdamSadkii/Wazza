#pragma once

// ---- Pin map (matches the k KiCad board) ----
#define PIN_I2C_SDA 21
#define PIN_I2C_SCL 5

#define PIN_WS2812_DIN 16
#define NUM_LEDS 8  // 1 onboard + strip on J2; adjust to your strip length

#define PIN_BTN_BOOT 0   // SW3, active low
#define PIN_BTN_ACTION 4 // SW2, active low

// I2S audio (MAX98357A amp + SPH0645 mic share the clock lines)
#define PIN_I2S_BCLK 15
#define PIN_I2S_LRCLK 26
#define PIN_I2S_AMP_DIN 33
#define PIN_I2S_MIC_DOUT 35

// ---- OLED ----
#define OLED_WIDTH 128
#define OLED_HEIGHT 32
#define OLED_ADDR 0x3C

// ---- Gesture detection tuning ----
#define GESTURE_SAMPLE_HZ 100
// Acceleration magnitude (minus gravity) that counts as a flick, in m/s^2
#define FLICK_THRESHOLD 12.0f
// Gyro magnitude that counts as a swipe, in rad/s
#define SWIPE_THRESHOLD 5.0f
// Minimum ms between reported gestures
#define GESTURE_COOLDOWN_MS 400

// ---- Telemetry ----
// How often to stream raw IMU frames to the backend (ms). 0 = disabled.
#define TELEMETRY_INTERVAL_MS 100
