#pragma once
#include <Arduinho.h> 

struct Power Status {
    float vbat Approx;  // rough estimate if ADC wired; else -1
    bool usbPresent;   // if detectable; else false
    uint32_t uptimeMs;
    uint32_t freeHeap;
};

namespace PowerMonitor {
    void begin(); 
    void loop();
    PowerStatus read();
    void logOnce();
}