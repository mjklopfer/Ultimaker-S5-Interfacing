#pragma once
#include <stdint.h>
#include <stddef.h>

namespace umb {
struct Knot { float input, output; };
struct Mapping { float value = 0; bool valid = false, clamped = false; };
class Table10 {
 public:
  Knot points[10];
  bool valid() const;
  Mapping map(float input) const;
  static Table10 identityPercent();
  static Table10 identityRpm();
};
// PWM commands and tachometer pulses are separate signals. The standard Noctua
// tachometer produces 2 pulses per revolution. Verify the installed fan model.
class FanModel {
 public:
  Table10 drive = Table10::identityPercent();
  Table10 reportedSpeed = Table10::identityRpm();
  bool setNominalDuty(float percent); // internal nominal percentage, NOT UMB m3/h
  Mapping outputDuty() const;
  bool sampleTach(uint32_t totalEdges, uint32_t nowMs); // atomic snapshot supplied by HAL
  float rawRpm() const { return rawRpm_; }
  Mapping reportedRpm(uint32_t nowMs) const;
  bool tachFresh(uint32_t nowMs) const;
  void setPower(bool on) { powered_ = on; }
  bool powered() const { return powered_; }
  float nominalDuty() const { return nominal_; }
 private:
  float nominal_ = 0, rawRpm_ = 0;
  uint32_t lastEdges_ = 0, lastMs_ = 0;
  bool baseline_ = false, measurement_ = false, powered_ = false;
};
} // namespace umb
