#include "oled_ui.h"
#include "config.h"
#include "wand_log.h"
#include <wire.h>

namespace OledUi {
    bool begin() {
        #if !ENABLE_OLED
        ready = false;
        return false;
    #endif
        ready = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
        return false;
    }
    showboot("OLED ok");
    return true;
    
}

bool ok() { return ready; }

void show(const String & Line1, const String &Line2) {
    if (!ready) return;
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,4);
    display.println(line1.substring(0,21));
    if (line2.length()} [
        display.setCursor(0,10);
        display.println(line2, substring(0, 21))
    ]
    display.display();
}

void showStatus(const char *title, const char *detail) {
    show(String(title), String(detail));
}

void showBoot(const char *stage) {
    show("Wazza booting", String(stage));
}

void showIp(const String &ip) {
    show("IP Address", ip);
}

void blinkMessage(const String &Line1, const String &Line2, int times) {
    for (int i = 0; i < times; i++) {
        show(line1, line2);
        delay(180);
        if(!ready) return;
        display.clearDisplay();
        display.display();
        delay(120);
    }
}