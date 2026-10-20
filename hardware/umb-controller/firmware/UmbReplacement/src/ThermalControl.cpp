#include "ThermalControl.h"
#include <math.h>
namespace umb {
static float bounded(float x,float low,float high) { return x<low?low:(x>high?high:x); }
ThermalOutput ThermalControl::update(const Environment& env,bool power,bool ffValid,float ff,float dt) {
  ThermalOutput out;
  if (!power) { reset(); out.valid=true; out.status=ThermalStatus::Off; return out; }
  ffValid = ffValid && isfinite(ff) && ff>=0 && ff<=100;
  if (config.mode == ThermalMode::FollowFeedForward) {
    reset(); out.valid=ffValid; out.nominalDuty=ffValid?ff:0;
    out.status=ffValid?ThermalStatus::Following:ThermalStatus::NoFeedForward; return out;
  }
  if (!isfinite(config.targetC) || config.targetC<5 || config.targetC>50 ||
      !isfinite(config.kp) || !isfinite(config.ki) || config.kp<0 || config.ki<0 ||
      !isfinite(config.trimLimitPercent) || config.trimLimitPercent<0 || config.trimLimitPercent>100 ||
      !config.sensorMask || (config.sensorMask & 0xf0)) {
    reset(); return out;
  }
  float t=0; uint8_t count=0;
  for (uint8_t i=0;i<4;++i) if (config.sensorMask & (1u<<i)) {
    // Fail the selected set if ANY required sensor is stale or invalid. Do not
    // silently change the aggregation when a hottest-zone sensor disappears.
    if (!env.fresh(i) || !isfinite(env.samples[i].temperatureC)) {
      reset(); out.status=ThermalStatus::NoSensors; return out;
    }
    const float value=env.samples[i].temperatureC;
    if (!count || (config.aggregate==Aggregation::Maximum && value>t)) t=value;
    else if (config.aggregate==Aggregation::Mean) t+=value;
    ++count;
  }
  if (config.aggregate==Aggregation::Mean) t/=count;
  out.temperatureC=t;
  if (config.mode==ThermalMode::TrimFeedForward && !ffValid) {
    reset(); out.status=ThermalStatus::NoFeedForward; return out;
  }
  if (!isfinite(dt) || dt<=0 || dt>5) {
    reset(); out.status=ThermalStatus::InvalidTiming; return out;
  }
  const float error=t-config.targetC; // exhaust fan cools: hotter => higher PWM
  const bool trim=config.mode==ThermalMode::TrimFeedForward;
  const float base=trim?ff:0;
  const float low=trim?-config.trimLimitPercent:0;
  const float high=trim?config.trimLimitPercent:100;
  const float candidate=bounded(integral_+config.ki*error*dt,low,high);
  const float raw=base+config.kp*error+candidate;
  const float rawCorrection=config.kp*error+candidate;
  // Conditional integration: stop winding up at fan OR trim saturation, but
  // allow an error that moves the output back toward the usable range.
  const bool highSaturated=raw>100 || rawCorrection>high;
  const bool lowSaturated=raw<0 || rawCorrection<low;
  if ((!highSaturated && !lowSaturated) || (highSaturated && error<0) || (lowSaturated && error>0))
    integral_=candidate;
  const float correction=bounded(config.kp*error+integral_,low,high);
  out.nominalDuty=bounded(base+correction,0,100);
  out.valid=true; out.feedForwardIgnored=!trim;
  out.status=trim?ThermalStatus::Trimming:ThermalStatus::Local;
  return out;
}
} // namespace umb
