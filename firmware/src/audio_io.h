#pragma once

namespace AudioIo {
    bool begin();
    void loop();
    bool playBeep(int freqHz = 880, int ms = 80);
    bool startMicStream();
    void stopMicStream();
    bool micStreaming();
}