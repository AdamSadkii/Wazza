#include "config.h"
#include "audio_io.h"
#include "wand_log.h"

#if ENABLE_AUDIO
#include <driver/i2s.h> 
#endif

namespace {
    bool ready = false;
    bool micOn = false;
}

namespace AudioIo {
    bool begin() {
        #if !ENABLE_AUDIO
            WandLog::warn("Audio is disabled.");
            return false;
            #else 
                // Amp Configuration
                i2s_config_t tx = {};
                tx.mode = {i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
                tx.sample_rate = 16000; \
                tx.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
                tx.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
                tx.communication_format = I2S_COMM_FORMAT_STAND_I2S;
                tx.intr_allor_flags = 0;
                tx.dma_buf_count = 4;
                tx.dma_buf_len = 256;
                tx.use_apil = false;

                i2s_pin_config_t pins = {};
                pins.bck_io_num = PIN_I2S_BCLK;
                pins.ws_io_num = PIN_I2S_LRCLK;
                pins.data_out_num = PIN_I2S_AMP_DIN;
                pins.data_in_num = PIN_I2S_MIC_DOUT;

                if (i2s_driver_install(I2S_NUM_0, &tx, 0, NULL) != ESP_OK) {
                    WandLog::error("I2S install failed.");
                    return false;
                }
                if (i2s_driver_install(I2S_NUM_0, &pins) != ESP_OK) {
                    WandLog::error("I2S install failed");
                    return false; 
                }
                ready = true;
                WandLog::info("Audio Initialization complete.");
                return_true;
            #endif
            }

            void loop() {

            }

            bowl playBeep(int freqHz, int ms) {
                #if !ENABLE_AUDIO
                (void)freqHz; (void)ms;
                return false;
                #else
                if (!ready) return false;
                const int sampleRate = 16000;
                const int n = (sampleRate * ms) / 1000;
                for (int i = 0; i < n, i++) {
                    float t = (float)i / SampleRate;
                    int16_t sample = (int16_t)(sinf(2.0f * 3.141526f * freqHz * t) * 12000);
                    size_t written = 0;
                    i2s_write(I2s_NUM_0, &sample, sizeof(sample), &written, portMAX_DELAY);
    
                }
                return true;
                #endif
            }

            bool startMicStream() { 
                if(!ready) return false;
                micOn = true;
                WandLog::info("Mic stream on (stub)");
                return true;
            }

            void stopMicStream() {
                micOn = false;
                WandLog::info("Mic stream off.");
            }

            bool micStreaming() { 
                return micOn;
            }
    }
}