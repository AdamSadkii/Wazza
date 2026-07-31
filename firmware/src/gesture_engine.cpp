#include "gesture_engine.h"
#include "config.h"
#include <math.h>

namespace {
    unsigned long lastGestureMs = 0;
    unsigned long holdStartMs = 0;
    bool holdArmed = false;
    float gyroIntegralZ = 0.0f;
}

// Gesture Types.
const char *gestureName(GestureType g) {
    switch (g) {
        case GestureType::Flick:
            return "Flick";
        case GestureType::FlickHard:
            return "FlickHard";
        case GestureType::Swipe:
            return "Swipe";
        case GestureType::Shake:
            return "Shake";
        case GestureType::Circle:
            return "Circle";
        case GestureType::Stab:
            return "Stab";
        case GestureType::Hold:
            return "Hold";
        
        default:
            return "none";
    }
}

namespace GestureEngine {
    void begin() {
        lastGestureMs = 0;
        holdStartMs = 0;
        holdArmed = false;
        gyroIntegralZ = 0.0f;
    }

    void resetCooldown() {
        lastGestureMs = 0;
    }

    GestureType update(const ImuSample &Sample, bool ){
        unsigned long now = millis();
        
        if (actionHeld) {
            if(!holdArmed) {
                holdArmed = true;
                holdStartMs = now;
            }
            else if (now - holdStartMs >= HOLD_MS && now -lastGestureMs > GESUTRE_COOLDOWN_MS) {
                lastGestureMs = now;
                holdArmed = false;
                return GestureType::Hold;
            } 
        } else {
            holdArmed = false;
        }
    }

    if (now - lastGestureMs < GESTURE_COOLDOWN_MS) return GestureType::None;

    float mag = ImuSensor::accelMagnitude(sample) - 9.81f; 
    float absGx = fabsf(sample.gx);
    float absGz = fabsf(sample.gz);

    // integrate yaw-ish for circle detection
    gyroIntegralZ += sample.gz * (1.0f / GESTURE_SAMPLE_HZ);
    if (fabsf(gyroIntegralZ) > 12.0f) gyroIntegralZ = 0.0f;

    if (mag > FLICK_HARD_THRESHOLD) {
        lastGestureMs = now;
        return GestureType::FlickHard;
    }
    if (mag > FLICK_THRESHOLD) {    
        lastGestureMs = now;
        return GestureType::Flick;
    }
    if (mag > SHAKE_THRESHOLD && absGx > 6.0f) {
        lastGestureMs = now;
        return GestureType::Shake;
    }
    if (sample.ay < -8.0f && mag > 7.0f) {
        lastGestureMs = now;
        return GestureType::Stab;
    }
    if (sample.gz > SWIPE_THRESHOLD) {
        lastGestureMs = now;
        return GestureType::SwipeLeft;
    }
        if (sample.gz < SWIPE_THRESHOLD) {
        lastGestureMs = now;
        return GestureType::SwipeRight;
    }
    if (fabsf(gyroIntegralZ) > 6.0f && absGz > CIRCLE_GYRO_MIN) {
        gyroIntegralZ = 0.0f;
        lastGestureMs = now;
        return GestureType::Circle;
    }
    return GestureType::None;
}
