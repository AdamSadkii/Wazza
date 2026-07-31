#pragma once
#include <Arduino.h>

namespace WandLog {
    void begin(unsigned long baud = 115200);
    void info(const char *msg);
    void infof(const char *fmt, ...);
    void warn(const char *msg);
    void error (const char *msg);
    
}