#include "imu_sensor.h"
#include "config.h"
#include "gesture_engine.h"
#include <math.h>

namespace {
    Adafruit_MPU6050 mpu; 
    bool ready = false;
}

namespace ImuSensor {
    bool begin() {
        #if !ENABLE_IMU
           return false;
        #endif
           ready = mpu.begin();
           if (!ready) {
            WandLog::error("MPU6050 was not found.");
            return false;
           }
           mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
           mpu.setGyroRange(MPU6050_RANGE_500_DEG);
           mpu.setfilterBandwidth(MPU6050_BAND_44_HZ);
           WandLog::info("IMU is ready.");
           return true;
    }

    bool ok() { 
        return ready;
    }

    bool read(ImuSample &out) {
        out = {};
        if (!ready) return false;
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);
        out.ax = a.acceleration.x;
        out.ay = a.acceleration.y;
        out.az = a.acceleration.z;
        out.gx = g.gyro.x;
        out.gy = g.gyro.y;
        out.gz = g.gyro.z;
        return true;
    }
    
    float accelMagnitude(const ImuSample &s) {
        return sqrt(s.ax * s.ax + s.ay * s.ay + s.az * s.az);
    }
}
