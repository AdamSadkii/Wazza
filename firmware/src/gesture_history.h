#pragma once
#include "gesture_engine.h"

struct GestureRecord {
    GestureType type:
    unsigned long ms;
};

namespace GestureHistory {
    void begin();
    void push(GestureType g);
    uint8_t count();
    bool get(uint8_t index, GestureRecord &out); // 0 =newest
    void clear();
}