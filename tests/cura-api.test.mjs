import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdtemp,writeFile,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';

test('Cura settings, slicing and export requests stay bound to approval and machine',async t=>{
  let machine='test-s5';const writes=[];
  const mock=createServer(async(req,res)=>{
    assert.equal(req.headers['x-cura-bridge-token'],'mock-secret');
    let body='';for await(const chunk of req)body+=chunk;
    const payload=JSON.parse(body);res.setHeader('content-type','application/json');
    if(req.url==='/v1/commands/inspect')return res.end(JSON.stringify({machine:{id:machine,name:'Mock S5'}}));
    if(req.url==='/v1/commands/get_settings')return res.end(JSON.stringify({settings:{layer_height:{value:0.2}}}));
    writes.push({url:req.url,payload});res.end(JSON.stringify({accepted:true}));
  });
  await new Promise(resolve=>mock.listen(0,'127.0.0.1',resolve));t.after(()=>mock.close());
  const folder=await mkdtemp(path.join(tmpdir(),'cura-state-test-'));t.after(()=>rm(folder,{recursive:true,force:true}));
  const staging=path.join(folder,'staged');await mkdir(staging);
  const connection=path.join(folder,'connection.json');
  await writeFile(connection,JSON.stringify({host:'127.0.0.1',port:mock.address().port,token:'mock-secret'}));
  process.env.CURA_MCP_BRIDGE_CONNECTION_PATH=connection;process.env.CURA_MCP_PRINT_FILE_ROOT=staging;
  const {handleCuraApi}=await import('../src/cura-api.mjs');
  assert.equal((await handleCuraApi('cura_settings',{keys:['layer_height']})).settings.layer_height.value,0.2);
  const action={action:'set_settings',values:{layer_height:0.15},extruder:0};
  const c=await handleCuraApi('confirm_cura_operation',action);
  assert.equal(writes.length,0);
  await handleCuraApi('cura_operation',{...action,confirmation_token:c.confirmation_token});
  assert.equal(writes.length,1);assert.equal(writes[0].payload.values.layer_height,0.15);
  await assert.rejects(()=>handleCuraApi('cura_operation',{...action,confirmation_token:c.confirmation_token}),/Confirmation/);
  const slice=await handleCuraApi('confirm_cura_operation',{action:'slice'});machine='another-printer';
  await assert.rejects(()=>handleCuraApi('cura_operation',{action:'slice',confirmation_token:slice.confirmation_token}),/machine changed/);
  await assert.rejects(()=>handleCuraApi('confirm_cura_operation',{action:'export_gcode',file_path:path.join(folder,'outside.gcode')}),/staging/);
  for(const action of [{action:'slice'},{action:'export_gcode',file_path:path.join(staging,'test.gcode'),build_plate:0}]){
    const c=await handleCuraApi('confirm_cura_operation',action);
    await handleCuraApi('cura_operation',{...action,confirmation_token:c.confirmation_token});
  }
  assert.deepEqual(writes.map(w=>w.url),['/v1/commands/set_settings','/v1/commands/slice','/v1/commands/export_gcode']);
});
