#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <Controller.h>

// Air controller: four SHT45s at 0x44 on mux channels 0..3.
// Material controller: one SHT45 directly on its separate I2C bus, sample slot 4.
// Scheduling avoids a blocking conversion delay while UART packets arrive.
class ShtSampler {
 public:
  ShtSampler(umb::Environment& e, TwoWire& wire, uint8_t first, uint8_t count, bool mux)
      : env_(e), wire_(wire), first_(first), count_(count), mux_(mux) {}
  void tick(uint32_t now) {
    if (count_ == 0 || first_ >= 5 || count_ > 5 - first_) return;
    if (!waiting_) {
      if (int32_t(now-nextMs_)<0) return;
      if (mux_) {
        wire_.beginTransmission(0x70); wire_.write(uint8_t(1u<<channel_));
        if (wire_.endTransmission()!=0) { finish(now,false); return; }
      }
      wire_.beginTransmission(0x44); wire_.write(uint8_t(0xfd));
      if (wire_.endTransmission()!=0) { finish(now,false); return; }
      startedMs_=now; waiting_=true; return;
    }
    if (uint32_t(now-startedMs_)<10) return;
    uint8_t b[6];
    if (wire_.requestFrom(uint8_t(0x44),uint8_t(6))!=6) {
      while (wire_.available()) wire_.read();
      finish(now,false); return;
    }
    for (uint8_t i=0;i<6;++i) b[i]=uint8_t(wire_.read());
    float t=0,h=0;
    const bool good=umb::decodeSht4x(b,t,h);
    if (good) { env_.samples[first_ + channel_].temperatureC=t; env_.samples[first_ + channel_].humidityRH=h; }
    finish(now,good);
  }
 private:
  umb::Environment& env_;
  TwoWire& wire_;
  uint8_t first_, count_;
  bool mux_;
  uint8_t channel_=0;
  bool waiting_=false;
  uint32_t startedMs_=0,nextMs_=0;
  void finish(uint32_t now,bool valid) {
    env_.samples[first_ + channel_].valid=valid;
    if (valid) env_.samples[first_ + channel_].sampledAtMs=now;
    waiting_=false;
    if (++channel_==count_) { channel_=0; nextMs_=now+2000; }
    else nextMs_=now;
  }
};
