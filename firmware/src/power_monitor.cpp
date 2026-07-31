#include "power_monitor.h"
#include "wand_log.h"

#if defined(ARDUINO_ARCH_ESP32)
#include <esp_system.h> 
#endif

namespace {
    unsigned long lastLogMs = 0;
}

namespace PowerMonitor {
    void begin() {
        WandLog::info("Power monitor ready"); // informational message for power monitor initialization.]
    }

    void loop() {
        // reserved for periodic sampling if VBAT ADC is wired later
    }

    PowerStatus read() {
        PowerStatus s{};
        s.vbatApprox = -1.0f;
        s.usbPresent = false;
        s.uptimeMs = millis();
    #if defined(ARDUINO_ARCH_ESP32)
        s.vbatApprox = -1.0f; // placeholder for actual VBAT reading
        s.usbPresent = false;
        s.uptimeMs = millis();
    #if defined(ARDUINO_ARCH_ESP32)
        s.freeHeap = ESP.getFreeHeap();
    #else
        s.freeHeap = 0;
    #endif
        return s;
    }

    void logOnce() {
        unsigned long now = millis();
        if (now - lastLogMs < 10000) return;
        lastLogMs = now;
        PowerStatus s = read();
        WandLog::infof("uptime=%lums heap=%lu", (unsigned long)s.uptimeMs, (unsigned long)s.freeHeap);
    }
}