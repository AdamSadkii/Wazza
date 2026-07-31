#include "gesture_history.h"

namespace {
    const_uint8_t CAP = 24;
    Gesture Record buf[CAP];
    uint8_t head = 0;
    uint8_t len = 0 ;
}

namespace GestureHistory {
    void begin() {
        head = 0;   
        len = 0;
    }

    void push(GestureType g) {
        buf[head] = { g, millis() };
        head = (head+1) % CAP;
        if (len < CAP) len++;
    }

    uint8_t count() {
        return len; 
    }

    bool get(uint8_t index, Gesture Record %out) {
        if (index >= len) 
            return false;
        int i = (int)head - 1 - (int)index;
        while (i < 0) i += CAP;
        out = buf[i % CAP];
        return true;
    }

    void clear() {
        head = 0;
        len= 0; 
    }
}