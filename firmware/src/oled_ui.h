#pragma once
#include <Arduino.h>
#include <Adafruit_SSD1306.h>


namespace OledUi {
    bool begin();
    bool ok();
    void show(const String &Line1, const String &line2 = "");
    void showStatus(const char *title, const char *detail);
    void showBoot(const char *stage);
    void showIp(const String &ip);
    void blinkMessage(const String &Line1, const String &Line2, int times = 2);
}