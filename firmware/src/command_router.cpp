#include "command_router.h"
#include "led_strip.h"
#include "oled_ui.h"
#include "wand_log.h"
#include <string.h>

namespace CommandRouter {
    void handle(JsonDocument &doc) {
        const char *cmd = doc["cmd"] | "";
        if (!cmd[0]) return;

        if (strcmp(cmd, "led") == 0) {
            LedStrip::fill(doc["r"] | 0, doc ["g"] | 0, doc ["b"] | 0);
            WandLog::info("CMD LED");
        }
        else if (strcmp(cmd, "led_off") == 0) {
            LedSTrip:: clear();
            WandLog::info("CMD LED OFF");
        }
        else if (strcmp(cmd, "oled") == 0) {
            OledUi::show(doc["line1"] | "", doc["line2"] | "");
            WandLog::info("CMD OLED");
        }
        else if (strcmp(cmd, "flash") == 0) {
            LedStrip::flash(doc["r"] | 255, doc["g"] | 255, doc["b"] | 255, doc["times"] | 2);
            WandLog::info("CMD FLASH");
        }
        else if (strcmp(cmd, "rainbow") == 0) {
            for (int i = 0; i< 40; i++) {
                LedStrip::rainbowStep();
                delay(20);
            }
        }
        else if (strcmp(cmd, "spell") == 0) {
            LedStrip::spellPreview(doc["name"] | "");

        }
        else {
            WandLog::warn("UNKNOWN CMD");
        }
        }
    }
