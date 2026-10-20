#include "UmbProtocol.h"
#include <string.h>

namespace umb {
uint8_t crc8(const uint8_t* data, size_t size, uint8_t crc) {
  while (size--) {
    crc ^= *data++;
    for (uint8_t bit = 0; bit < 8; ++bit)
      crc = uint8_t((crc & 0x80) ? (crc << 1) ^ 0x07 : crc << 1);
  }
  return crc;
}
size_t encodeRequest(const Request& r, uint8_t* out, size_t cap) {
  const size_t size = size_t(r.length) + 5;
  if (cap < size) return 0;
  out[0] = 0xff; out[1] = r.address; out[2] = r.command; out[3] = r.length;
  memcpy(out + 4, r.payload, r.length);
  out[size - 1] = crc8(out + 1, size - 2);
  return size;
}
size_t encodeReply(const Reply& r, uint8_t* out, size_t cap) {
  const size_t size = size_t(r.length) + 4;
  if (cap < size) return 0;
  out[0] = 0xff; out[1] = r.command; out[2] = r.length;
  memcpy(out + 3, r.payload, r.length);
  out[size - 1] = crc8(out + 1, size - 2);
  return size;
}
void RequestParser::reset() { position_ = 0; crc_ = 0; }
RequestParser::Event RequestParser::feed(uint8_t b) {
  if (!position_) {
    if (b == 0xff) { position_ = 1; crc_ = 0; }
    return Incomplete;
  }
  if (position_ == 1) request_.address = b;
  else if (position_ == 2) request_.command = b;
  else if (position_ == 3) request_.length = b;
  else if (position_ == uint16_t(request_.length) + 4) {
    const bool valid = crc_ == b;
    reset();
    return valid ? Complete : BadCrc;
  } else request_.payload[position_ - 4] = b;
  crc_ = crc8(&b, 1, crc_);
  ++position_;
  return Incomplete;
}
bool Router::attach(uint8_t address, Registers& registers) {
  if (address >= 0xfe || registers.count() > MaxRegisters) return false;
  for (const auto& d : devices_) if (d.registers && d.address == address) return false;
  for (auto& d : devices_) if (!d.registers) {
    d.address = address; d.registers = &registers; return true;
  }
  return false;
}
static void error(Reply& r, uint8_t code = 0xfd) {
  r.command = 0xfe; r.length = 1; r.payload[0] = code;
}
static bool textReply(Reply& r, const char* text) {
  const size_t n = strlen(text);
  if (n > MaxPayload) { error(r); return false; }
  memcpy(r.payload, text, n); r.length = uint8_t(n); return true;
}
static void putIndex(uint8_t* p, size_t ordinal) {
  // Locally chosen opaque wire index. It is NOT a known stock-device index.
  const uint16_t wire = uint16_t(ordinal + 1);
  p[0] = uint8_t(wire >> 8); p[1] = uint8_t(wire);
}
static bool getIndex(const uint8_t* p, size_t count, size_t& ordinal) {
  const uint16_t wire = uint16_t(uint16_t(p[0]) << 8) | p[1];
  if (!wire || wire > count) return false;
  ordinal = wire - 1; return true;
}
bool Router::handle(const Request& q, Reply& r) {
  Device* device = nullptr;
  for (auto& d : devices_) if (d.registers && d.address == q.address) device = &d;
  if (!device) return false;
  Registers& regs = *device->registers;
  r.command = q.command; r.length = 0;
  size_t i = 0;
  char text[MaxPayload + 1] = {};
  if (q.command == Next) {
    if (q.length == 2) {
      if (!getIndex(q.payload, regs.count(), i)) { error(r); return true; }
      ++i;
    } else if (q.length != 0) { error(r); return true; }
    r.length = 2;
    if (i < regs.count()) putIndex(r.payload, i);
    else r.payload[0] = r.payload[1] = 0;
  } else if (q.command == Name || q.command == Read ||
             q.command == MonitorOn || q.command == MonitorOff) {
    if (q.length != 2 || !getIndex(q.payload, regs.count(), i)) { error(r); return true; }
    if (q.command == Name) {
      if (!regs.name(i, text, sizeof text)) error(r);
      else textReply(r, text);
    } else if (q.command == Read) {
      if (regs.read(i, text, sizeof text) != Result::Ok) error(r);
      else textReply(r, text);
    } else {
      const uint8_t mask = uint8_t(1u << (i % 8));
      if (q.command == MonitorOn) device->monitors[i / 8] |= mask;
      else device->monitors[i / 8] &= uint8_t(~mask);
    }
  } else if (q.command == Write) {
    // count byte includes NUL, followed by that many bytes, then two index bytes.
    const size_t valueLength = q.length ? q.payload[0] : 0;
    if (!writesEnabled_ || valueLength < 1 || q.length != valueLength + 3 ||
        q.payload[valueLength] != 0 ||
        !getIndex(q.payload + valueLength + 1, regs.count(), i)) { error(r); return true; }
    for (size_t n = 1; n < valueLength; ++n) {
      if (q.payload[n] < 0x20 || q.payload[n] > 0x7e) { error(r); return true; }
    }
    memcpy(text, q.payload + 1, valueLength);
    if (regs.write(i, text) != Result::Ok) error(r);
  } else if (q.command == Poll) {
    if (q.length) { error(r); return true; }
    const size_t count = regs.count();
    const uint8_t escaped[] = {'\\', 'x', '0', '0'};
    const size_t sepSize = separator_ == Separator::Nul ? 1 : 4;
    for (size_t visited = 0; visited < count; ++visited) {
      i = (device->cursor + visited) % count;
      if (!(device->monitors[i / 8] & uint8_t(1u << (i % 8)))) continue;
      if (regs.read(i, text, sizeof text) != Result::Ok) continue;
      const size_t size = strlen(text);
      if (size + 2 + sepSize > MaxPayload) continue; // one value cannot fit a monitor record
      if (size_t(r.length) + size + 2 + sepSize > MaxPayload) {
        device->cursor = i; return true; // whole records only; resume on next poll
      }
      putIndex(r.payload + r.length, i); r.length += 2;
      memcpy(r.payload + r.length, text, size); r.length = uint8_t(r.length + size);
      if (separator_ == Separator::Nul) r.payload[r.length++] = 0;
      else { memcpy(r.payload + r.length, escaped, 4); r.length += 4; }
    }
    device->cursor = 0;
  } else error(r, 0xfe);
  return true;
}
} // namespace umb
