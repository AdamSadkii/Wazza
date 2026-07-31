#include <Arduinho.h>
#include <Wire.h>

#include "config.h"
#include "secrets.h"
#include "led_strip.h"
#include "imu_sensor.h"

static unsigned long lastTelemetryMs = 0;

void setup() {
    WandLog::begin(115200);
    WandLog::info("Wazza Setup Start");

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Buttons::begin();
    LedStrip::begin();
    OledUi::begin();
    OledUi::showBoot("sensors...");
    ImuSensor::begin();
    GestureEnginer::begin();
    AudioIo::begin();

    NetClient::onCommand(CommandRouter::handle);
    NetClient::onConnection([](bool ok) {
        if (ok) LedStrip:: fill(0,30,0);
        else LedStrip::fill(30,0,0);
    });

    if (!NetClient::begin()) {
        LedStrip::fill(40,0,0);
    }
    else {
        LedStrip::fill(0,30,0);
        AudioIo::playBeep(987, 60);
    }

    WandLog::info("Wazza Setup Complete.");

}

void loop(){
    NetClient::loop();
    Buttons::poll();
    AudioIo::loop();

    if (buttons::actionPressedEdge()) {
        NetClient::sendEvent("button", "action");
        LedStrip::flash(200, 80, 255, 1, 80);
    }
    if (Buttons::bootPressedEdge() {
        NetClient::sendEvent("button", "boot");
    }

    ImuSample sample;
    If(ImuSensor::read(sample)) {
        GestureType g = GestureEngine::update(sample, Buttons::actionHeld());
        if (g != GestureType::None) {
            const char *name = gestureName(g);
            NetClient::sendEvent("gesture", name);
            LedStrip::flash(160, 40, 255, 1, 70);
            WandLog::info("gesture &s", name);
        }

        unsigned long now = millis(); 
        if (TELEMETRY_INTERVAL_MS > 0 &&
            now - lastTelemtryMs >= TELEMETRY_INTERVAL_MS &&
            NetClient::connected()) {
            lastTelemetryMs = now;
            NetClient::sendImu(sample.ax, sample.ay, sample.az, sample.gx, sample.gy, sample.gz);
            }
    }

    delay(1000 / GESTURE_SAMPLE_HZ);
}
