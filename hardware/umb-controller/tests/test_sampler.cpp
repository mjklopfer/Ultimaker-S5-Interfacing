#include <assert.h>
#include <stdio.h>
#include "ShtSampler.h"

int main() {
  umb::Environment airEnvironment, materialEnvironment;
  TwoWire airBus, materialBus;
  ShtSampler air(airEnvironment,airBus,0,4,true);
  ShtSampler material(materialEnvironment,materialBus,4,1,false);
  for (uint32_t i=0;i<4;++i) { air.tick(i*20); air.tick(i*20+10); }
  assert(airBus.muxWrites==4 && airBus.selectedMask==8);
  assert(airBus.sensorWrites==4 && materialBus.sensorWrites==0);
  for (unsigned i=0;i<4;++i) assert(airEnvironment.samples[i].valid);
  assert(!airEnvironment.samples[4].valid);
  material.tick(0);material.tick(10);
  assert(materialBus.muxWrites==0 && materialBus.sensorWrites==1);
  assert(materialEnvironment.samples[4].valid);
  for (unsigned i=0;i<4;++i) assert(!materialEnvironment.samples[i].valid);
  materialBus.fail=true;
  material.tick(2010);
  assert(!materialEnvironment.samples[4].valid);
  assert(airEnvironment.samples[0].valid); // other controller remains independent
  ShtSampler bad(airEnvironment,airBus,4,2,true);
  const auto previous=airBus.muxWrites;bad.tick(0);
  assert(airBus.muxWrites==previous); // invalid layout never indexes past the array
  puts("PASS: independent role buses, probe ownership, invalidation and bounds");
}
