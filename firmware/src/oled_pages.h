#pragma once

// Small OLED page rotator for status screens
namespace OledPages {
  void begin();
  void showNext();
  void showHome(const char *ipOrStatus);
  void showGesture(const char *gesture);
  void showPower(uint32_t uptimeMs, uint32_t freeHeap);
  void tick(); // auto-rotate optional
  void setAutoRotate(bool on);
}
