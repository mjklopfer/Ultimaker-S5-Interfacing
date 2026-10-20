#include "UmbProtocol.h"
#include "Controller.h"
#include "FanModel.h"
#include "ThermalControl.h"
#include "ObservedCatalog.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <vector>
using namespace umb;

struct FakeRegisters : Registers {
  unsigned writes=0; char value[16]="12.5";
  size_t count() const override { return 2; }
  bool name(size_t i,char* out,size_t cap) const override {
    return snprintf(out,cap,"bench.value.%u",unsigned(i))<int(cap);
  }
  Result read(size_t,char* out,size_t cap) override {
    return snprintf(out,cap,"%s",value)<int(cap)?Result::Ok:Result::Unavailable;
  }
  Result write(size_t,const char* text) override {
    ++writes; snprintf(value,sizeof value,"%s",text); return Result::Ok;
  }
};
Request req(uint8_t address,uint8_t command,std::initializer_list<uint8_t> bytes={}) {
  Request r; r.address=address; r.command=command; r.length=uint8_t(bytes.size());
  size_t i=0; for(auto b:bytes)r.payload[i++]=b; return r;
}
size_t ordinal(ReplacementDevice& device,const char* wanted) {
  char name[100];
  for(size_t i=0;i<device.count();++i)if(device.name(i,name,sizeof name)&&!strcmp(name,wanted))return i;
  assert(false); return 0;
}
bool closeTo(float a,float b) { return fabsf(a-b)<0.01f; }
void protocol() {
  const uint8_t check[]={'1','2','3','4','5','6','7','8','9'};
  assert(crc8(check,sizeof check)==0xf4);
  Request q=req(7,Write,{2,'1',0,0x12,0x34});
  uint8_t bytes[260]; const size_t n=encodeRequest(q,bytes,sizeof bytes);
  assert(n==10 && bytes[0]==255 && bytes[1]==7);
  assert(!encodeRequest(q,bytes,9));
  RequestParser parser; assert(parser.feed(42)==RequestParser::Incomplete);
  for(size_t i=0;i<n-1;++i)assert(parser.feed(bytes[i])==RequestParser::Incomplete);
  assert(parser.feed(bytes[n-1])==RequestParser::Complete);
  assert(parser.request().address==7 && !memcmp(parser.request().payload,q.payload,q.length));
  bytes[n-1]^=1;
  for(size_t i=0;i<n-1;++i)parser.feed(bytes[i]);
  assert(parser.feed(bytes[n-1])==RequestParser::BadCrc);
  // Zero and maximum length packets, embedded FF, then timeout reset/resync.
  q=req(0,Poll); size_t z=encodeRequest(q,bytes,sizeof bytes);
  for(size_t i=0;i<z-1;++i)parser.feed(bytes[i]);
  assert(parser.feed(bytes[z-1])==RequestParser::Complete);
  q.length=255; memset(q.payload,0xff,255); z=encodeRequest(q,bytes,sizeof bytes);
  for(size_t i=0;i<z-1;++i)parser.feed(bytes[i]);
  assert(parser.feed(bytes[z-1])==RequestParser::Complete);
  parser.feed(255); parser.feed(1); parser.reset();
  q=req(0,Read,{0,1});z=encodeRequest(q,bytes,sizeof bytes);
  for(size_t i=0;i<z-1;++i)parser.feed(bytes[i]);
  assert(parser.feed(bytes[z-1])==RequestParser::Complete);
  FakeRegisters a,b; Router router; Reply reply;
  assert(router.attach(0,a)&&router.attach(1,b));
  assert(!router.attach(0,a)&&!router.attach(0xfe,a));
  assert(!router.handle(req(2,Next),reply));
  assert(router.handle(req(0,Next),reply)&&reply.length==2&&reply.payload[1]==1);
  router.handle(req(0,Next,{0,1}),reply);assert(reply.payload[1]==2);
  router.handle(req(0,Next,{0,2}),reply);assert(reply.payload[0]==0&&reply.payload[1]==0);
  router.handle(req(0,Name,{0,1}),reply);assert(reply.command==Name&&reply.length==13);
  router.handle(req(0,Read,{0,1}),reply);assert(reply.length==4);
  const auto write=req(0,Write,{2,'1',0,0,1});
  router.handle(write,reply);assert(reply.command==0xfe&&a.writes==0);
  router.enableWrites(true);router.handle(write,reply);
  assert(reply.command==Write&&reply.length==0&&a.writes==1&&b.writes==0);
  router.handle(req(0,Write,{2,'1','X',0,1}),reply);assert(reply.command==0xfe&&a.writes==1);
  router.handle(req(0,Write,{3,'1',0,0,0,1}),reply);assert(reply.command==0xfe&&a.writes==1);
  router.handle(req(0,Write,{2,0xff,0,0,1}),reply);assert(reply.command==0xfe&&a.writes==1);
  router.handle(req(0,Read,{0,0}),reply);assert(reply.command==0xfe);
  router.handle(req(0,0x77),reply);assert(reply.command==0xfe&&reply.payload[0]==0xfe);
  router.handle(req(0,MonitorOn,{0,1}),reply);assert(reply.command==MonitorOn);
  router.handle(req(0,Poll),reply);assert(reply.length==4&&reply.payload[3]==0);
  router.handle(req(1,Poll),reply);assert(reply.length==0); // logical-device isolation
  router.setMonitorSeparator(Separator::LiteralBackslashX00);
  router.handle(req(0,Poll),reply);assert(reply.length==7&&!memcmp(reply.payload+3,"\\x00",4));
  uint8_t encoded[259];size_t responseSize=encodeReply(reply,encoded,sizeof encoded);
  assert(responseSize==reply.length+4u&&crc8(encoded+1,responseSize-2)==encoded[responseSize-1]);
  router.handle(req(0,MonitorOff,{0,1}),reply);router.handle(req(0,Poll),reply);assert(reply.length==0);
  router.handle(req(0,Poll,{1}),reply);assert(reply.command==0xfe);
}
void domains() {
  assert(!Mode::fromJumpers(true,true).air&&!Mode::fromJumpers(true,true).material);
  assert(Mode::fromJumpers(false,true).air&&!Mode::fromJumpers(false,true).material);
  assert(!Mode::fromJumpers(true,false).air&&Mode::fromJumpers(true,false).material);
  assert(Mode::fromJumpers(false,false).air&&Mode::fromJumpers(false,false).material);
  assert(packedNfcCommand(NfcCommand::Read,5,7)==0x070503);
  Environment env;Hardware hardware;ReplacementDevice air(Role::AirManager,hardware,env);
  ReplacementDevice material(Role::MaterialStation,hardware,env);
  const size_t temp=ordinal(air,"custom.chamberTemperature.0");char text[100];
  assert(air.read(temp,text,sizeof text)==Result::Unavailable);
  env.nowMs=1000;env.samples[0]={-0.25f,42.5f,900,true};
  assert(air.read(temp,text,sizeof text)==Result::Ok&&!strcmp(text,"-0.25"));
  assert(air.write(temp,"12")==Result::ReadOnly);
  env.nowMs=20000;assert(air.read(temp,text,sizeof text)==Result::Unavailable);
  assert(air.read(ordinal(air,"custom.sensorValid.0"),text,sizeof text)==Result::Ok&&!strcmp(text,"0"));
  assert(air.read(ordinal(air,"data.fanSpeedMeasured.0"),text,sizeof text)==Result::Unavailable);
  assert(material.write(ordinal(material,"prefeeder_0.printer_command.0"),"1")==Result::Unavailable);
  assert(air.count()<=MaxRegisters&&material.count()<=MaxRegisters);
  // Sensirion CRC known check BE EF -> 92; use it for both words.
  uint8_t sample[6]={0xbe,0xef,0x92,0xbe,0xef,0x92};float t,rh;
  assert(decodeSht4x(sample,t,rh));assert(t>80&&rh>80);
  sample[2]^=1;assert(!decodeSht4x(sample,t,rh));
  for(bool isAir:{false,true}) {
    const size_t count=isAir?AirCount:MaterialCount;
    for(size_t i=0;i<count;++i){assert(catalogName(isAir,i,text,sizeof text));assert(strlen(text)>0);}
  }
}
void fan() {
  Table10 table=Table10::identityPercent();assert(table.valid());
  assert(closeTo(table.map(77).value,77));assert(table.map(-1).clamped&&table.map(101).clamped);
  table.points[5].output=55;assert(closeTo(table.map(45).value,47.5));
  table.points[5].input=table.points[4].input;assert(!table.valid()&&!table.map(45).valid);
  FanModel f;assert(f.setNominalDuty(50));assert(closeTo(f.outputDuty().value,0));
  f.setPower(true);assert(closeTo(f.outputDuty().value,50));assert(!f.setNominalDuty(101));
  assert(!f.sampleTach(100,0));assert(!f.reportedRpm(0).valid);
  assert(f.sampleTach(200,1000)&&closeTo(f.rawRpm(),3000));
  assert(closeTo(f.reportedRpm(1000).value,3000)&&f.tachFresh(2000)&&!f.tachFresh(4000));
  assert(!f.reportedRpm(4000).valid);
  f.reportedSpeed.points[3].output=3100;assert(closeTo(f.reportedRpm(1000).value,3100));
  assert(closeTo(f.rawRpm(),3000)); // reporting calibration never changes raw tachometer
  assert(f.sampleTach(200,2000)&&f.rawRpm()==0&&f.reportedRpm(2000).value==0);
  assert(!f.sampleTach(300,8000)&&!f.reportedRpm(8000).valid);
  FanModel wrap;assert(!wrap.sampleTach(0xfffffffa,0xfffffe00));
  assert(wrap.sampleTach(4,488)&&closeTo(wrap.rawRpm(),300)); // edges and millis wrap
  f.drive.points[9].output=101;assert(!f.outputDuty().valid);
  f.setPower(false);assert(f.outputDuty().valid&&f.outputDuty().value==0);
}
void thermal() {
  Environment env;env.nowMs=100;
  for(size_t i=0;i<5;++i)env.samples[i]={40,20,100,true};
  ThermalControl c;auto out=c.update(env,true,true,45,1);
  assert(out.valid&&out.nominalDuty==45&&out.status==ThermalStatus::Following);
  c.config.mode=ThermalMode::LocalFeedback;out=c.update(env,true,false,0,1);
  assert(out.valid&&out.feedForwardIgnored&&out.nominalDuty>25);
  c.config.sensorMask=1;env.samples[1].valid=false;
  assert(c.update(env,true,false,0,1).valid); // only selected sensor required
  c.config.sensorMask=3;assert(!c.update(env,true,false,0,1).valid);
  c.config.sensorMask=0x10;assert(!c.update(env,true,false,0,1).valid); // no material sensor in chamber loop
  c.config.sensorMask=1;c.config.mode=ThermalMode::TrimFeedForward;c.reset();
  out=c.update(env,true,true,50,1);assert(out.valid&&out.nominalDuty==70&&!out.feedForwardIgnored);
  assert(!c.update(env,true,false,0,1).valid);
  out=c.update(env,false,false,0,1);assert(out.valid&&out.nominalDuty==0&&out.status==ThermalStatus::Off);
  c.config.mode=ThermalMode::LocalFeedback;c.config.sensorMask=1;c.config.ki=100;
  for(int i=0;i<100;++i)assert(c.update(env,true,false,0,1).nominalDuty<=100);
  env.samples[0].temperatureC=30;assert(c.update(env,true,false,0,1).nominalDuty==0);
  env.nowMs=20000;assert(!c.update(env,true,false,0,1).valid);
  env.nowMs=100;assert(!c.update(env,true,false,0,6).valid);
  c.config.aggregate=Aggregation::Mean;c.config.sensorMask=3;env.samples[1]={44,20,100,true};
  env.samples[0].temperatureC=40;out=c.update(env,true,false,0,1);
  assert(closeTo(out.temperatureC,42));
}
int main() { protocol();domains();fan();thermal();puts("PASS: protocol, roles/catalog, environment, tach/LUT and optional thermal loop"); }
