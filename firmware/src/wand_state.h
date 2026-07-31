#pragma once
#include <Arduino.h>

enum class WandMode {
    Boot = 0,
    Idle,
    Armed,
    Casting,
    Offline,
    Error,
};

namespace WandState {
    void begin(); 
    void setMode(WandMode mode);
    WandMode mode();
    const char *modeName();
    void setLastGesture(const char *name);
    const char *lastGesture();
    void setBackendOnline(bool online);
    bool backendOnline();
    void noteError(const char *msg);
    const char *lastError();
}