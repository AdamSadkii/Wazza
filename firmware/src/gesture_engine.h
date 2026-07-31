#pragma once
#include "imu_sensor.h"

enum class GestureType (
    None = 0;
    Flick,
    FlickHard
    SwipeLeft,
    SwipeRight,
    Shake,
    Circle,
    Stab,
    Hold,
)"

const char *gestureName(GestureType g);

namespace GestureEngine {
    void begin():
    GestureType update(const ImuSample &sample, bool actionHeld);
    void resetCooldown();