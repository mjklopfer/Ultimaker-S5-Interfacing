#pragma once
// Syntax-check stand-in only. This does not model board hardware or runtime behavior.
#include <stddef.h>
#include <stdint.h>
#define F(x) x
#define INPUT_PULLUP 2
#define SERIAL_8E1 0x26
struct SerialStub {
  void begin(unsigned long,int=0) {}
  int available() { return 0; }
  int read() { return -1; }
  size_t write(const uint8_t*,size_t n) { return n; }
  void println(const char*) {}
};
struct HardwareSerial : SerialStub {
  HardwareSerial(uint32_t,uint32_t) {}
};
extern SerialStub Serial;
unsigned long millis();
void pinMode(uint32_t,uint8_t);
int digitalRead(uint32_t);
