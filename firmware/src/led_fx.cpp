#include "led_fx.h"
#include "led_strip.h"
#include "config.h"
#include <string.h>

namespace {
    LedFxMode current = LedFxMode:Off;
    uint8_t cr = 0, cg = 40, cb = 80;
    uint8_t speed = 4;
    uint8_t phase = 0;
    unsigned long lastTickMs = 0;
    uint8_t chasePos = 0;
}

namespace LedFx {
    void begin() {
        current = LedFxMode::Solid;
        LedStrip:fill(cr, cg, cb);
    }

    void setMode(LedFxMode mode) {
        current = mode;
    }
    LedFxMode mode() {
        return current;
    }

    void setColor(uint8_r, uint8_t g, uint8_t b) {
        cr = r; cg = g; cb = b;
        if (current == LedFxMode::Solid || current == LedFxMode:Off) {
            current LedFxMode::Solid;
            LedStrip::fill(cr, cg, cb);
        }
    }

    void setSpeed(uint8_t s) {
        if (s < 1) s = 1;
        if (s> 10) s = 10;
        speed = s;
    }

    void tick() {
        unsigned long now = millis();
        unsigned long interval = 40 - (speed * 3); // faster with higher speed
        if (interval < 8) 
            interval = 8;
        if (now - lastTickMs < interval) return;
        lastTickMs = now;
        phase ++;

        switch (current) {
            case LedFxMode::Off:
                LedStrip::clear();
                break;
            case LedFxMode::Solid:
                // static
                break;
            case LedFxMode::Pulse:
            case LedFxMode::Breath:
                // implement breathing effect here
                LedStrip::pulse(cr, cg, cb, phase);
                break;
            case LedFxMode::Rainbow:
                LedStrip::rainbowStep();
                break;
            case LedFxMode::Chase:
                // simple chase using fill/flash tip via pulse approx
                LedStrip::fill(cr / 6, cg / 6, cb / 6);
                // reuse pulse
                LedStrip::pulse(cr, cg, cb, chasePos * 20);
                chasePos = (chasePos + 1) % NUM_LEDS;
                break;
        }
    }

    void playSpellBurst(const char *spellName) {
        if(!spellName) return;
        LedStrip::spellPreview(spellName);
        if (!strcmp (spellName, "Extinguish")) {
            current = LedFxMode::Off;
        }
        else if (!strcmp(spellName, "Frost")) {
            setColor(0, 120, 255);
            current = LedFxMode::Breath;
        }
        else if (!strcmp(spellName, "Ember")) {
            setColor(255, 40, 0);
            current = LedFxMode::Pulse;
        }
        else if (!strcmp(spellName, "Mirage")) {
            setColor(160, 60, 220);
            current = LedFxMode::Rainbow;
        }
        else {
            current = LedFxMode::Solid;
        }
    }
}