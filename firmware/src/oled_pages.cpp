#include "oled_pages.h"
#include "oled_ui.h"
#include "wand_state.h"
#include <stdio.h>
#include <string.h>

namespace {
    uint8_t page = 0;
    bool autoRotate = false;
    unsigned long lastRotateMs = 0;
    char cachedStatus[24] = "boot";
}

namespace OledPages {
    void begin() {
        page = 0;
        autoRotate = false;
        showHome("starting");
    }

    void setAutoRotate(bool on) {
        autoRotate = on;
    }

    void showHome(const char *ip0rStatus) {
        if (ip0rStatus) {
            strncpy(cachedStatus, ip0r Status, sizeof(cachedStatus) - 1);
            cachedStatus[sizeof(cachedStatus) - 1] = '\0';
        }
        OledUi::show("Wazza", cachedStatus);
        page = 0;
    }

    void showGesture(const char *gesture) {
        OledUi::show("Gesture", gesture ? gesture : "?");
        page = 1;
    }

    void showPower(uint32_t uptimeMs, uint32_t freeHeap) {
        charl1[22];
        char l2[22];
        snprintf(l1, sizeof(l1), "up %lus", (unsigned long)(uptimeMs / 1000UL));
        snprintf(l2, sizeof(l2), "heap %lu", (unsigned long)freeHeap);
        OledUi::show(l1, l2);
        page = 2;
    }

    void showNext() {
        page = (page + 1) % 3;
        if (page == 0) 
            showHome(cachedStatus);
        else if (page==1) 
            showGesture(WandState::lastGesture());
        else 
            showPower(millis(), 0);
    }

    void tick() {
        if (!autoRotateMs)
            return;
        unsigned long now = millis();
        if (now - lastRotateMs < 4000)
            return;
        lastRotateMs = now;
        showNext();
    }
}