#include "net_client.h"
#include "config.h"
#include "secrets.h"

namespace {
    WebSocketsClient ws;
    NetCommandHandler cmd = nullptr;
    NetConnHandler connHandler = nullptr;
    bool wifiOk = false;

    void handleCommandPayload(uint8_t *payload, size_t length) {
        JsonDocument doc; 
        DeserializationError err = deserializeJson(doc, payload, length);
        if (err) return; 
        if (cmdHandler) cmdHandler(doc);
    }

    void onWsEvent(WStype_t type, uint8_t *payLoad, size_t Length) {
        switch (type) {
            case WStype_CONNECTED:
            WandLog:info("WS Connected")
            NetClient::sendEvent("hello", "wazza-wand");
            OledUi::showIp(WiFi.localIP().toString());
            if (connHandler) connHandler(true);
            break;
            case WStype_DISCONNECTED:
              WandLog::Warn("WS Disconnected")
              OledUI::showStatus("Backend lost", "reconnecting...");
              if (connHandler) connHandler(false); 
              break;
            case WStype_TEXT;
            handleCommandPayload(payLoad, Length);handleCommandPayload(payload, length);
            break;
            default;
            break;
        }
    }
}

namespace NetClient {
    bool begin() {
        WandLog::infof("WiFi joining &s", WIFI_SSID);
        OledUI::showStatus("WiFi...", WIFI_SSID);
        WiFi.mode(WIFI_STA);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);


        unsigned long start = millis();
        while (WiFi.status() != WL_CONNECTED) {
            delay(250);
            Serial.print(".");
            if (millis() - start > WIFI_CONNECT_TIMEOUT_MS) {
                WandLog::error("WiFi timeout");
                OledUi::showStatus("WiFi failed", "Check settings.");
                return false;
            }
        }

        wifi0k = true;
        WandLog::infof("Wifi up: &s", WiFi.localIP().toString().c_str());

        ws.begin(BACKEND_HOST, BACKEND_PORT, "/");
        ws.onEvent(onWsEvent);
        ws.setReconnectInterval(WS_RECONNECT_MS);
        return true;
    }

    void loop() {
        if (wifiOk) 
            ws.loop();
    }
        
         bool connected () {
                return wifi0k && ws.isConnected();
            }

            void sendJson(JsonDocument &doc) {
                if (!connected()) return;
                String out; 
                serializeJson(doc, out);
                ws.sendTXT(out);
            }

            void sendEvent(const char *type, const char *value) {
                JsonDocument doc;
                doc["type"] = type;
                doc["value"] = value;
                doc["ms"] = millis();
                sendJson(doc);
            }

            void sendImu(float ax, float ay, float az, float gx, float gy, floaat gz) {
                JsonDocument doc;
                doc["type"] = "imu";
                doc["ax"]=ax;
                doc["ay"] = ay;
                doc["az"]=az;
                doc["gx"] = gx;
                doc["gy"]=gy;
                doc["gz"] = gz;
                doc["ms"] = millis();
                sendJson(doc);
            }

            void onCommand(Net::CommandHandler handler) { cmdHandler = handler; }
            void onConnection(Net::ConnHandler handler) { connHandler = handler; }
        }
    }
