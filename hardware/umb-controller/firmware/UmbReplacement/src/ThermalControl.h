#pragma once
#include "Controller.h"

namespace umb {
enum class ThermalMode { FollowFeedForward, TrimFeedForward, LocalFeedback };
enum class Aggregation { Mean, Maximum };
enum class ThermalStatus { Off, Following, Trimming, Local, NoSensors, NoFeedForward,
                           InvalidConfiguration, InvalidTiming };
struct ThermalConfig {
  ThermalMode mode = ThermalMode::FollowFeedForward; // local loop OFF by default
  Aggregation aggregate = Aggregation::Maximum;
  uint8_t sensorMask = 0x0f; // four CHAMBER sensors; material sensor cannot control chamber
  float targetC = 35.0f;    // local proposed target, not read from a known UMB register
  float kp = 5.0f, ki = 0.05f; // illustration only: percent/C, percent/(C*s), UN-TUNED
  float trimLimitPercent = 20.0f;
};
struct ThermalOutput {
  float nominalDuty = 0, temperatureC = 0;
  bool valid = false, feedForwardIgnored = false;
  ThermalStatus status = ThermalStatus::InvalidConfiguration;
};
class ThermalControl {
 public:
  ThermalConfig config;
  ThermalOutput update(const Environment&, bool hostFanPower,
                       bool feedForwardValid, float nominalFeedForward, float elapsedSeconds);
  void reset() { integral_=0; }
 private:
  float integral_ = 0;
};
} // namespace umb
