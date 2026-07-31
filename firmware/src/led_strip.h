#pragma once
#include <Arduino.h> 
#include <FastLED.h> 

namespace LedStrip {
    bool begin();
    void setBrightness(uint8_t b);
    void fill(uint8_t r, uint8_t g, uint8_t b);
    void clear();
    void flash(uint8_t r, uint8_t g, uint8_t b, int times = 2, int onMs = 120)
    void rainbowStep();
    void pulse(uint8_t r, uint8_t g, uint8_t b, uint8_t phase);
    void spellpreview(const char *spellName);
}