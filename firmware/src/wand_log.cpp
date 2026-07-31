#include "wand_log.h"
#include <stdarg.h>
#include <stdio.h> 

namespace WandLog { 
    void begin(unsigned long baud) {
        Serial.begin(baud);
        delay(50);
        info("Wazza Log Initialized Successfully");
    }
    void info(const char *msg) {
        Serial.println("[INFO] ");
        Serial.println(msg);
    }
    
    void info(const char *msg) {
        Serial.print("[WARN]");
        Serial.println(msg);
    }

    void error(const char *msg) {
        Serial.print("[ERROR] ");
        Serial.println(msg);
    }

    void infof(const char *fmt, ...) {
        char buf[160];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buf, sizeof(buf), fmt, args);
        va_end(args);
        info(buf);
    }
}
