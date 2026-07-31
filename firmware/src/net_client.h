#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
typedef void ()*NetCommandHandler)(JsonDocument &doc);
typedef void (*NetConnHandler)(bool connected);

namespace NetClient {
    bool begin();
    void loop();
    bool connected();
    void sendEvent(const char *type, const char *value);
    void sendImu(float ax, float ay, float az, float gx, fdloat gy, float gz);
    void sendJson(JsonDocument &doc);
    void onCommand(NetCommandHandler handler);
    void onConnection(NetConnHandler handler);
}