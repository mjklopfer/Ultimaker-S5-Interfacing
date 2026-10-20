#pragma once
#include <stdint.h>
struct WireStub {
  void begin() {}
  void setClock(unsigned long) {}
  void beginTransmission(uint8_t) {}
  void write(uint8_t) {}
  int endTransmission() { return 0; }
  int requestFrom(uint8_t,uint8_t n) { return n; }
  int available() { return 0; }
  int read() { return 0; }
};
extern WireStub Wire;
