# pragma once
# include <Arduino.h>

enum class LedFxMode {
    off = 0,
    Solid,
    Pulse,
    Rainbow,
    Chase,
    Sparkle,
    Breath,
};

namespace LedFX {
    void begin();
    void setMode(LedFXMode mode); 
    LedFxMode mode();
    void setColor(uint8_t r, uint8_t g, uint8_t b);
    void setSpeed(uint8_t speed); // 1..10
    void tick(); // call from Loop, non-blocking
    void playSpellBurst(const char *spellName);
}
