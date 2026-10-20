#include "Controller.h"
#include "ObservedCatalog.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

namespace umb {
static size_t stockCount(Role r) { return r == Role::AirManager ? AirCount : MaterialCount; }
static bool customName(size_t index, char* out, size_t cap) {
  int n = -1;
  if (index < 4) n = snprintf(out, cap, "custom.chamberTemperature.%u", unsigned(index));
  else if (index < 8) n = snprintf(out, cap, "custom.chamberHumidity.%u", unsigned(index-4));
  else if (index == 8) n = snprintf(out, cap, "custom.materialTemperature.0");
  else if (index == 9) n = snprintf(out, cap, "custom.materialHumidity.0");
  else if (index < 15) n = snprintf(out, cap, "custom.sensorValid.%u", unsigned(index-10));
  else if (index < 20) n = snprintf(out, cap, "custom.sensorAgeMs.%u", unsigned(index-15));
  return n >= 0 && size_t(n) < cap;
}
static bool fixedHundredths(float value, char* out, size_t cap) {
  if (!isfinite(value) || value < -100000 || value > 100000) return false;
  // Avoid AVR printf float support and heap-backed Arduino String.
  const long scaled = lroundf(value * 100.0f);
  const unsigned long magnitude = scaled < 0 ? static_cast<unsigned long>(-scaled) : static_cast<unsigned long>(scaled);
  const int n = snprintf(out, cap, "%s%lu.%02lu", scaled < 0 ? "-" : "", magnitude/100, magnitude%100);
  return n >= 0 && size_t(n) < cap;
}
size_t ReplacementDevice::count() const { return stockCount(role_) + 20; }
bool ReplacementDevice::name(size_t i, char* out, size_t cap) const {
  if (i >= count()) return false;
  const size_t stock = stockCount(role_);
  if (i >= stock) return customName(i-stock, out, cap);
  return catalogName(role_ == Role::AirManager, i, out, cap);
}
Result ReplacementDevice::read(size_t i, char* out, size_t cap) {
  if (i >= count()) return Result::UnknownRegister;
  const size_t stock = stockCount(role_);
  if (i < stock) {
    char key[100];
    if (!name(i, key, sizeof key)) return Result::Unavailable;
    return hardware_.read(role_, key, out, cap);
  }
  i -= stock;
  if (i >= 10) {
    const size_t sensor = i < 15 ? i-10 : i-15;
    const uint32_t value = i < 15 ? (environment_.fresh(sensor) ? 1 : 0) :
      (environment_.samples[sensor].valid ? uint32_t(environment_.nowMs-environment_.samples[sensor].sampledAtMs) : 0xffffffffu);
    const int n = snprintf(out, cap, "%lu", static_cast<unsigned long>(value));
    return n >= 0 && size_t(n) < cap ? Result::Ok : Result::Unavailable;
  }
  const size_t sensor = i < 4 ? i : (i < 8 ? i-4 : 4);
  if (!environment_.fresh(sensor)) return Result::Unavailable;
  const bool temperature = i < 4 || i == 8;
  const Sample& s = environment_.samples[sensor];
  return fixedHundredths(temperature ? s.temperatureC : s.humidityRH, out, cap) ? Result::Ok : Result::Unavailable;
}
Result ReplacementDevice::write(size_t i, const char* value) {
  if (i >= count()) return Result::UnknownRegister;
  if (i >= stockCount(role_) || !catalogWritable(role_ == Role::AirManager, i)) return Result::ReadOnly;
  char key[100];
  if (!name(i, key, sizeof key)) return Result::Unavailable;
  // Hardware implementation must validate numeric bounds, command sequencing and
  // feedback/interlocks BEFORE accepting. Unknown stock register permissions are denied.
  return hardware_.write(role_, key, value);
}
bool decodeSht4x(const uint8_t b[6], float& t, float& rh) {
  for (uint8_t offset = 0; offset <= 3; offset += 3) {
    uint8_t crc = 0xff;
    for (uint8_t i = 0; i < 2; ++i) {
      crc ^= b[offset+i];
      for (uint8_t bit = 0; bit < 8; ++bit)
        crc = uint8_t((crc & 0x80) ? (crc << 1) ^ 0x31 : crc << 1);
    }
    if (crc != b[offset+2]) return false;
  }
  const uint16_t rawT = uint16_t(uint16_t(b[0]) << 8) | b[1];
  const uint16_t rawRH = uint16_t(uint16_t(b[3]) << 8) | b[4];
  t = -45.0f + 175.0f * rawT / 65535.0f;
  rh = -6.0f + 125.0f * rawRH / 65535.0f;
  if (rh < 0) rh = 0;
  if (rh > 100) rh = 100;
  return true;
}
} // namespace umb
