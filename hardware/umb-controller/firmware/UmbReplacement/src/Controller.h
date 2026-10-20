#pragma once
#include "UmbProtocol.h"

namespace umb {
enum class Role { AirManager, MaterialStation };
struct Mode {
  bool air = false, material = false;
  static Mode fromJumpers(bool airPinHigh, bool materialPinHigh) {
    Mode m; m.air = !airPinHigh; m.material = !materialPinHigh; return m;
  }
};
enum class SlotCommand : uint8_t {
  Load=1, Unload=2, Eject=3, Pause=4, Resume=5, EndOfFilamentReset=6,
  Park=7, RecoverError=8, ExpectRetract=9, LoadToPrinthead=10, Error=11, BreakFailedAssist=12
};
enum class NfcCommand : uint8_t { Nop=0, ScanOnce=1, ScanForever=2, Read=3, Write=4,
                                ScanBay=5, RfRegulationTest=6 };
inline uint32_t packedNfcCommand(NfcCommand cmd, uint8_t bay, uint8_t page) {
  return (uint32_t(page) << 16) | (uint32_t(bay) << 8) | uint8_t(cmd);
}
struct Sample {
  float temperatureC = 0, humidityRH = 0;
  uint32_t sampledAtMs = 0;
  bool valid = false;
  Sample() {}
  Sample(float t,float h,uint32_t at,bool good):temperatureC(t),humidityRH(h),sampledAtMs(at),valid(good) {}
};
struct Environment {
  Sample samples[5]; // slots 0..3: Air chamber probes; slot 4: Material-local probe
  uint32_t nowMs = 0;
  static constexpr uint32_t StaleAfterMs = 10000; // proposed policy, not a stock constant
  bool fresh(size_t i) const {
    return i < 5 && samples[i].valid && uint32_t(nowMs - samples[i].sampledAtMs) <= StaleAfterMs;
  }
};
// Hardware/application boundary. Implement using measured feedback and real state
// machines. Default refuses ALL stock values and writes: no fake READY/loaded state.
class Hardware {
 public:
  virtual ~Hardware() {}
  virtual Result read(Role, const char*, char*, size_t) { return Result::Unavailable; }
  virtual Result write(Role, const char*, const char*) { return Result::Unavailable; }
};
class ReplacementDevice : public Registers {
 public:
  ReplacementDevice(Role role, Hardware& hardware, Environment& env)
      : role_(role), hardware_(hardware), environment_(env) {}
  size_t count() const override;
  bool name(size_t, char*, size_t) const override;
  Result read(size_t, char*, size_t) override;
  Result write(size_t, const char*) override;
 private:
  Role role_;
  Hardware& hardware_;
  Environment& environment_;
};
// SHT4x command 0xFD result: temp MSB,LSB,CRC, RH MSB,LSB,CRC.
// Independent CRC polynomial 0x31, initial FF; NOT the UMB CRC.
bool decodeSht4x(const uint8_t bytes[6], float& temperatureC, float& humidityRH);
} // namespace umb
