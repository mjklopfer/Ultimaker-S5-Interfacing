#pragma once
// UNTESTED on STM32/S5 hardware. One compiled role per physical controller.
#include <Arduino.h>
#include <Wire.h>
#include "Stm32BenchConfig.h"
#include "UmbProtocol.h"
#include "Controller.h"
#include "ShtSampler.h"

#if (defined(UMB_BUILD_AIR_MANAGER) + defined(UMB_BUILD_MATERIAL_STATION)) != 1
#error "Select exactly one role; use two controllers for both accessories."
#endif

namespace stm32bench {
umb::Environment environment;
umb::Hardware unboundHardware; // rejects stock requests without a real backend
#if defined(UMB_BUILD_AIR_MANAGER)
umb::ReplacementDevice device(umb::Role::AirManager, unboundHardware, environment);
#else
umb::ReplacementDevice device(umb::Role::MaterialStation, unboundHardware, environment);
#endif
umb::Router router;
umb::RequestParser parser;
umb::Reply reply;
uint32_t lastByteMs = 0;
uint8_t replyBytes[umb::MaxPayload + 4];

#if UMB_ENABLE_TRANSPORT
// Explicit STM32duino constructor avoids assuming a default Serial1 pin map.
HardwareSerial accessoryUart(UMB_UART_RX_PIN, UMB_UART_TX_PIN);
#endif
#if UMB_ENABLE_SENSORS
TwoWire sensorWire(UMB_I2C_SDA_PIN, UMB_I2C_SCL_PIN);
#if defined(UMB_BUILD_AIR_MANAGER)
ShtSampler sensors(environment, sensorWire, 0, 4, true);
#else
ShtSampler sensors(environment, sensorWire, 4, 1, false);
#endif
#endif
bool roleEnabled = false;
} // namespace stm32bench

void setup() {
  using namespace stm32bench;
  // No default debug UART: board ST-LINK/USB routing must be chosen explicitly.
#if UMB_BOARD_CONFIGURED
  const uint32_t rolePin = UMB_ROLE_ENABLE_PIN;
  pinMode(rolePin, INPUT_PULLUP);
  roleEnabled = digitalRead(rolePin) == 0;
#endif
  // Address zero is a fixture choice for each isolated bench target.
  // Real chain enumeration/address assignment is NOT implemented.
  if (roleEnabled) router.attach(0, device);
  router.enableWrites(false);
#if UMB_ENABLE_SENSORS
  if (roleEnabled) { sensorWire.begin(); sensorWire.setClock(100000); }
#endif
#if UMB_ENABLE_TRANSPORT
  if (roleEnabled) accessoryUart.begin(115200, SERIAL_8E1);
#endif
}

void loop() {
  using namespace stm32bench;
  environment.nowMs = millis();
  if (!roleEnabled) return;
#if UMB_ENABLE_TRANSPORT
  if (uint32_t(millis() - lastByteMs) > 100) parser.reset();
  while (accessoryUart.available()) {
    lastByteMs = millis();
    const auto event = parser.feed(uint8_t(accessoryUart.read()));
    if (event == umb::RequestParser::Complete && router.handle(parser.request(), reply)) {
      const size_t n = umb::encodeReply(reply, replyBytes, sizeof replyBytes);
      accessoryUart.write(replyBytes, n);
    }
  }
#endif
#if UMB_ENABLE_SENSORS
  sensors.tick(millis());
#endif
  // Hardware PWM/tach, chain/bootstrap and motion backends remain unimplemented.
}
