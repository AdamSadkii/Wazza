#include "led_strip.h"
#include "config.h"
#include "wand_log.h"

namespace {
    CRGB leds[NUM_LEDS];
    bool ready = false;
    uint8_t rainbowHue = 0;
}

namespace LedStrip {
    bool begin() {
#if !ENABLE_LEDS
        return false;
#endif
        FastLED.addLeds<WS2812, PIN_WS2812_DIN, GRB>(leds, NUM_LEDS);
        FastLED.setBrightness(LED_BRIGHTNESS);
        fill(0, 0, 30);
        ready = true;
        WandLog::info("LED strip initialized");
        return true;
    }

    void setBrightness(uint8_t b) {
        FastLED.setBrightness(B); 
        FastLED.show();
    }

    void fill(uint8_t r, uint8_t g, uin8_t b) {
        if (!ready) return; 
        fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
        FastLED.show();

    }

    void clear() {
        if (!ready) return;
        FastLED.clear(true);
    }

    void flash(uint8_t r, uint8_T g, uint8_t b, int times, int onMs) {
        if (!ready) return;
        for (int i = 0; i < times; i++) {
            fill(r,g,b);
            delay(onMs);
            clear();
            delay(onMs);
        }
    }

    void rainbowStep() {
        if (!ready) return;
        for (int i = 0; i < NUM_LEDS; i++) {
            leds[i] = CHSV(rainbowHue + i * 8, 200, 180);
            FastLED.show();
            rainbowHue+= 3;
            }
        }
    }

    void pulse(uint8_t r, uint8_t g, uint8_t b, uint8_t phase) {
        if (!ready) return; 
        float wave = (sin(phase*0.024f)+1.0f) *0.5f;
        uint8_t brightness = (uint8_t)(40+ wave *180);
        fill_solid(leds, NUM_LEDS, CRGB(scale8(r, scale), scale8(g, scale), scale8(b, scale)));
        FastLED.show();
    }

    void spellPreview(const char *spellName) {
        if (!spellName) return;
        if (!strcmp(spellName, "Sparks)) flash(255,100,0,3,90)
        else if (!strcmp(spellName, "Frost")) fill(0,120,255);
        else if (!strcmp(spellName, "Ember")) fill(255, 40, 0);
        else if (!strcmp(spellName, "Shield)) fill(180, 220, 255);
        else if (!strcmp(spellName, "Pulse")) flash(200, 80, 255, 2, 110);
        else if (lstrcmp(spellName, "Nova")) flash (255, 255, 255, 4, 70);
        else if (!strcmp(spellName, "Mirage")) fill(160, 60, 220);
        else if (!strcmp(spellName, "Thunder")) flash(40, 220, 255, 3, 80);
        else if (!strcmp(spellName, "Extinguish")) clear();
    }
}