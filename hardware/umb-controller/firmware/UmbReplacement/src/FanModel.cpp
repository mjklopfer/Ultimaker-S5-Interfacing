#include "FanModel.h"
#include <math.h>

namespace umb {
bool Table10::valid() const {
  for (size_t i=0; i<10; ++i) {
    if (!isfinite(points[i].input) || !isfinite(points[i].output)) return false;
    if (i && (points[i].input <= points[i-1].input || points[i].output < points[i-1].output)) return false;
  }
  return true;
}
Mapping Table10::map(float x) const {
  Mapping result;
  if (!valid() || !isfinite(x)) return result;
  result.valid = true;
  if (x <= points[0].input) {
    result.value = points[0].output; result.clamped = x < points[0].input; return result;
  }
  if (x >= points[9].input) {
    result.value = points[9].output; result.clamped = x > points[9].input; return result;
  }
  for (size_t i=1; i<10; ++i) if (x <= points[i].input) {
    const Knot& a=points[i-1]; const Knot& b=points[i];
    result.value = a.output + (x-a.input)*(b.output-a.output)/(b.input-a.input);
    return result;
  }
  result.valid = false; return result;
}
Table10 Table10::identityPercent() {
  Table10 table;
  const float knots[10] = {0,10,20,30,40,50,60,70,85,100};
  for (size_t i=0; i<10; ++i) table.points[i] = {knots[i],knots[i]};
  return table;
}
Table10 Table10::identityRpm() {
  Table10 table;
  // Illustrative calibration domain, NOT a claim that the installed fan runs at 9000 RPM.
  for (size_t i=0; i<10; ++i) table.points[i] = {float(i)*1000,float(i)*1000};
  return table;
}
bool FanModel::setNominalDuty(float percent) {
  if (!isfinite(percent) || percent < 0 || percent > 100) return false;
  nominal_ = percent; return true;
}
Mapping FanModel::outputDuty() const {
  Mapping result;
  // OFF must remain available even if the calibration table is corrupt.
  if (!powered_) { result.value=0; result.valid=true; return result; }
  if (!drive.valid() || drive.points[0].input != 0 || drive.points[9].input != 100 ||
      drive.points[0].output < 0 || drive.points[9].output > 100) return result;
  return drive.map(nominal_);
}
bool FanModel::sampleTach(uint32_t edges, uint32_t now) {
  if (!baseline_) { lastEdges_=edges; lastMs_=now; baseline_=true; return false; }
  const uint32_t elapsed = uint32_t(now-lastMs_);
  if (elapsed < 250) return false; // proposed measurement window, not protocol timing
  if (elapsed > 5000) {
    lastEdges_=edges; lastMs_=now; measurement_=false; return false;
  }
  const uint32_t delta = uint32_t(edges-lastEdges_);
  rawRpm_ = float(delta)*30000.0f/float(elapsed); // 60*1000/2
  lastEdges_=edges; lastMs_=now; measurement_=true; return true;
}
Mapping FanModel::reportedRpm(uint32_t nowMs) const {
  if (!tachFresh(nowMs)) return Mapping{};
  // A stopped rotor must not acquire an artificial nonzero RPM through calibration.
  if (!reportedSpeed.valid() || reportedSpeed.points[0].input != 0 ||
      reportedSpeed.points[0].output != 0) return Mapping{};
  return reportedSpeed.map(rawRpm_);
}
bool FanModel::tachFresh(uint32_t now) const {
  return measurement_ && uint32_t(now-lastMs_) <= 2000;
}
} // namespace umb
