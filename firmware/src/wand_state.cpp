#include "wand_state.h"
#include "oled_ui.h"
#include "wand_log.h"
#include <string.h>

namespace {
    WandMode current = WandMode::Boot;
    bool backend = false; 
    char lastGest[24] = "none";
    char lastErr[48] = "";
}

namespace WandState {
    void begin() {
        current = WandMode::Boot;
        backend = false;
        strcpy(lastGest, "none");
        lastErr[0] = '\0';
    }

    void setMode(WandMode mode) {
        current = mode;
        OledUi::showStatus("Mode", modeName());
        WandLog::infof("mode-%s", modeName());
    }

    WandMode mode() {
        return current;
    }

    const char *modeName() {
        switch (current) {
            case WandMode::Boot: return "boot";
            case WandMode::Idle: return "idle";
            case WandMode::Armed: return "armed";
            case WandMode::Casting: return "casting";
            case WandMode::Error: return "error";
            default: return "unknown";
        }
    }

    void setLastGesture(const char *name) {
        if (!name) return;
        strncpy(lastGest, name, sizeof(lastGest) - 1);
        lastGest[sizeof(lastGest) - 1] = '\0';
    }

    const char *lastGesture() {
        return lastGest;
    }

    void setBackendOnline(bool online) {
        backend = online;
        if (online && current == WandMode::Offline)
           setMode(WandMode::Idle);
        if (!online && current != WandMode::Boot)
           setMode(WandMode::Offline);
    }

    bool backendOnline() {
        return backend;
    }

    void noteError(const char *msg) {
        if (!msg) return; 
        strncpy(lastErr, msg, sizeof(lastErr) -1);
        lastErr[sizeof(lastErr) - 1] = '\0';
        setMode(WandMode::Error);
        WandLog::error(lastErr);
    }

    const char *lastError() {
        return lastErr;
    }
}