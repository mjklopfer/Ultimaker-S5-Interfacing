#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <Controller.h>

// Five SHT45s at 0x44 on separate TCA9548A channels 0..4. Nonblocking conversion
// scheduling avoids delay(10) five times while a UART packet is arriving.
class ShtSampler {
 public:
  explicit ShtSampler(umb::Environment& e): env_(e) {}
  void tick(uint32_t now) {
    if (!waiting_) {
      if (int32_t(now-nextMs_)<0) return;
      Wire.beginTransmission(0x70); Wire.write(uint8_t(1u<<channel_));
      if (Wire.endTransmission()!=0) { finish(now,false); return; }
      Wire.beginTransmission(0x44); Wire.write(uint8_t(0xfd));
      if (Wire.endTransmission()!=0) { finish(now,false); return; }
      startedMs_=now; waiting_=true; return;
    }
    if (uint32_t(now-startedMs_)<10) return;
    uint8_t b[6];
    if (Wire.requestFrom(uint8_t(0x44),uint8_t(6))!=6) {
      while (Wire.available()) Wire.read();
      finish(now,false); return;
    }
    for (uint8_t i=0;i<6;++i) b[i]=uint8_t(Wire.read());
    float t=0,h=0;
    const bool good=umb::decodeSht4x(b,t,h);
    if (good) { env_.samples[channel_].temperatureC=t; env_.samples[channel_].humidityRH=h; }
    finish(now,good);
  }
 private:
  umb::Environment& env_;
  uint8_t channel_=0;
  bool waiting_=false;
  uint32_t startedMs_=0,nextMs_=0;
  void finish(uint32_t now,bool valid) {
    env_.samples[channel_].valid=valid;
    if (valid) env_.samples[channel_].sampledAtMs=now;
    waiting_=false;
    if (++channel_==5) { channel_=0; nextMs_=now+2000; }
    else nextMs_=now;
  }
};
