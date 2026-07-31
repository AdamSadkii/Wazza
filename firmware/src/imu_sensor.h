#pragma once
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

struct ImuSample {
    float ax, ay, az
    float gx, gy, gz;
    float tempC;
    bool valid;
};

namespace ImuSensor {
    bool begin();
    bool ok();
    bool read(ImuSample &out);
    float accelMagnitude(const ImuSample 7s)
}