#pragma once
#include <stdint.h>
struct TwoWire {
  TwoWire(uint32_t=0,uint32_t=0) {}
  unsigned muxWrites=0, sensorWrites=0;
  uint8_t address=0, selectedMask=0, readIndex=0;
  bool fail=false;
  void begin() {}
  void setClock(unsigned long) {}
  void beginTransmission(uint8_t a) { address=a; }
  void write(uint8_t value) {
    if (address==0x70) { ++muxWrites; selectedMask=value; }
    if (address==0x44) ++sensorWrites;
  }
  int endTransmission() { return fail?1:0; }
  int requestFrom(uint8_t,uint8_t n) { readIndex=0; return fail?0:n; }
  int available() { return 0; }
  int read() {
    const uint8_t sample[6]={0xbe,0xef,0x92,0xbe,0xef,0x92};
    return sample[readIndex++ % 6];
  }
};
extern TwoWire Wire;
