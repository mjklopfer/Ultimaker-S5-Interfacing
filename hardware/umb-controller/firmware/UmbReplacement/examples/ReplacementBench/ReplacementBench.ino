// UNTESTED ON REAL HARDWARE. Sample only; transport and outputs default disabled.
// DRAFT: a disabled bench entry point, NOT a stock-S5 plug-in accessory.
// Install firmware/UmbReplacement as an Arduino library. Target proposal: Mega 2560.
#include <Arduino.h>
#include <Wire.h>
#include <UmbProtocol.h>
#include <Controller.h>
#include <FanModel.h>
#include "ShtSampler.h"

constexpr bool ENABLE_UMB_TRANSPORT = false; // electrical interface/bootstrap unverified
constexpr bool ENABLE_SENSORS = false;      // enable after sensor wiring is reviewed
constexpr uint8_t AIR_MODE_PIN=22, MATERIAL_MODE_PIN=23; // active-low jumpers, INPUT_PULLUP
// PROVISIONAL: UART1 RX19/TX18; I2C SDA20/SCL21; PWM OC3A/D5; tach interrupt D2.
// No fan or motor pins are configured as outputs in this draft.
umb::Environment environment;
umb::Hardware unboundHardware; // rejects stock endpoint reads/writes until implemented
umb::ReplacementDevice air(umb::Role::AirManager,unboundHardware,environment);
umb::ReplacementDevice material(umb::Role::MaterialStation,unboundHardware,environment);
umb::Router router;
umb::RequestParser parser;
umb::Reply reply;
ShtSampler sensors(environment);
uint32_t lastByteMs=0;
uint8_t replyBytes[umb::MaxPayload+4];

void setup() {
  Serial.begin(115200); // USB/debug, separate from the hardware accessory UART
  pinMode(AIR_MODE_PIN,INPUT_PULLUP); pinMode(MATERIAL_MODE_PIN,INPUT_PULLUP);
  const auto mode=umb::Mode::fromJumpers(digitalRead(AIR_MODE_PIN),digitalRead(MATERIAL_MODE_PIN));
  // MANUAL BENCH addresses. Real host-negotiated enumeration is not implemented.
  // Boot-time role latching prevents a hot jumper change from changing device identity.
  if (mode.material) router.attach(0,material);
  if (mode.air) router.attach(mode.material?1:0,air);
  router.enableWrites(false);
  // Default NUL monitor separator is a bench hypothesis; validate against a capture.
  // Alternative available: router.setMonitorSeparator(umb::Separator::LiteralBackslashX00);
  if (ENABLE_SENSORS) {
    Wire.begin(); Wire.setClock(100000);
    #if defined(WIRE_HAS_TIMEOUT)
      Wire.setWireTimeout(3000,true);
    #endif
  }
  if (ENABLE_UMB_TRANSPORT) Serial1.begin(115200,SERIAL_8E1);
  Serial.println(F("UMB replacement draft: bootloader and actuators unimplemented; writes disabled."));
}
void loop() {
  environment.nowMs=millis();
  // Service RX ahead of sensor work. Parser retains partial packets between loops.
  if (ENABLE_UMB_TRANSPORT) {
    if (uint32_t(millis()-lastByteMs)>100) parser.reset(); // bench timeout, tune from capture
    while (Serial1.available()) {
      lastByteMs=millis();
      const auto event=parser.feed(uint8_t(Serial1.read()));
      if (event==umb::RequestParser::Complete && router.handle(parser.request(),reply)) {
        const size_t n=umb::encodeReply(reply,replyBytes,sizeof replyBytes);
        // Electrical adapter must supply direction control/echo suppression IF required.
        Serial1.write(replyBytes,n);
      }
    }
  }
  if (ENABLE_SENSORS) sensors.tick(millis());
  // Future: atomic tach snapshots, 25kHz hardware PWM, feedback-driven AMS state
  // machines and bounded motion scheduling. Do not put blocking motor loops here.
}
