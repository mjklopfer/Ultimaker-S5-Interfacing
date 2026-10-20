#pragma once
#include <stddef.h>
#include <stdint.h>

namespace umb {
constexpr size_t MaxPayload = 255;
constexpr size_t MaxRegisters = 256;
enum Command : uint8_t { Next = 0x00, Name = 0x01, Read = 0x02, Write = 0x03,
                        MonitorOn = 0x10, MonitorOff = 0x11, Poll = 0x1f };
enum class Result { Ok, UnknownRegister, ReadOnly, Unavailable, BadValue };
enum class Separator { Nul, LiteralBackslashX00 };
struct Request { uint8_t address = 0, command = 0, length = 0; uint8_t payload[MaxPayload] = {}; };
struct Reply { uint8_t command = 0, length = 0; uint8_t payload[MaxPayload] = {}; };
uint8_t crc8(const uint8_t* bytes, size_t count, uint8_t initial = 0);
size_t encodeRequest(const Request&, uint8_t* output, size_t capacity);
size_t encodeReply(const Reply&, uint8_t* output, size_t capacity);

// Call reset after a transport timeout. The electrical adapter owns TX direction,
// echo handling, line idle and byte timing; this parser makes no electrical assumptions.
class RequestParser {
 public:
  enum Event { Incomplete, Complete, BadCrc };
  Event feed(uint8_t byte);
  void reset();
  const Request& request() const { return request_; }
 private:
  Request request_;
  uint16_t position_ = 0;
  uint8_t crc_ = 0;
};

class Registers {
 public:
  virtual ~Registers() {}
  virtual size_t count() const = 0;
  virtual bool name(size_t ordinal, char* output, size_t capacity) const = 0;
  virtual Result read(size_t ordinal, char* output, size_t capacity) = 0;
  virtual Result write(size_t, const char*) { return Result::ReadOnly; }
};

// Only the OPERATIONAL phase. attach() is a bench binding, not UMB enumeration.
// A single MCU can dispatch two logical addresses after a future bootstrap adapter
// has negotiated them. There is no claim that stock S5 discovery will accept this yet.
class Router {
 public:
  bool attach(uint8_t address, Registers& registers);
  void enableWrites(bool enabled) { writesEnabled_ = enabled; }
  void setMonitorSeparator(Separator separator) { separator_ = separator; }
  bool handle(const Request& request, Reply& reply); // false => no response to another address
 private:
  struct Device {
    uint8_t address = 0xff;
    Registers* registers = nullptr;
    uint8_t monitors[(MaxRegisters + 7) / 8] = {};
    size_t cursor = 0;
  } devices_[2];
  bool writesEnabled_ = false;
  Separator separator_ = Separator::Nul;
};
} // namespace umb
