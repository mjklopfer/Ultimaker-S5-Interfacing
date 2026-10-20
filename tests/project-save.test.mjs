import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';

test('project Save/Save As bind exact destination and disk version; status/path reads are read-only',async t=>{
  const folder=await mkdtemp(path.join(tmpdir(),'cura-save-test-'));t.after(()=>rm(folder,{recursive:true,force:true}));
  let current=path.join(folder,'current.3mf'),hash='original-disk-hash';const writes=[];
  const mock=createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;
    const args=JSON.parse(body);res.setHeader('content-type','application/json');
    if(req.url.endsWith('/inspect'))return res.end(JSON.stringify({machine:{id:'s5'}}));
    if(req.url.endsWith('/plan_project_save')){
      const mode=args.mode||'save';
      if(mode==='save'&&(args.folder||args.file_name)){res.statusCode=400;return res.end(JSON.stringify({error:'Use save_as'}));}
      const target=mode==='save'?current:path.join(args.folder||path.dirname(current),args.file_name||path.basename(current));
      return res.end(JSON.stringify({mode,file_path:target,source_project:current,expected_sha256:mode==='save'?hash:null,create_folder:!!args.create_folder}));
    }
    if(req.url.endsWith('/project_save_status'))return res.end(JSON.stringify({operation_id:args.operation_id,status:'completed',sha256:'saved-hash'}));
    if(req.url.endsWith('/path_info'))return res.end(JSON.stringify({path:args.file_path,readable:true}));
    writes.push(args);res.end(JSON.stringify({operation_id:'save-1',status:'running'}));
  });
  await new Promise(resolve=>mock.listen(0,'127.0.0.1',resolve));t.after(()=>mock.close());
  const connection=path.join(folder,'connection.json');
  await writeFile(connection,JSON.stringify({host:'127.0.0.1',port:mock.address().port,token:'mock-token'}));
  process.env.CURA_MCP_BRIDGE_CONNECTION_PATH=connection;
  const {handleCuraApi}=await import('../src/cura-api.mjs');
  const same={action:'save_project',mode:'save'};
  const a=await handleCuraApi('confirm_cura_operation',same);
  assert.equal(a.request.file_path,current);assert.equal(writes.length,0);
  assert.equal((await handleCuraApi('cura_operation',{...same,confirmation_token:a.confirmation_token})).status,'running');
  await assert.rejects(()=>handleCuraApi('cura_operation',{...same,confirmation_token:a.confirmation_token}),/Confirmation/);
  const stale=await handleCuraApi('confirm_cura_operation',same);hash='external-change';
  await assert.rejects(()=>handleCuraApi('cura_operation',{...same,confirmation_token:stale.confirmation_token}),/mismatched/);
  const renamed={action:'save_project',mode:'save_as',file_name:'renamed.3mf'};
  const b=await handleCuraApi('confirm_cura_operation',renamed);
  assert.equal(b.request.file_path,path.join(folder,'renamed.3mf'));
  await assert.rejects(()=>handleCuraApi('cura_operation',{...renamed,file_name:'other.3mf',confirmation_token:b.confirmation_token}),/mismatched/);
  const relocated={action:'save_project',mode:'save_as',file_name:'moved.3mf',folder:path.join(folder,'new'),create_folder:true};
  const c=await handleCuraApi('confirm_cura_operation',relocated);
  await handleCuraApi('cura_operation',{...relocated,confirmation_token:c.confirmation_token});
  assert.equal(writes[1].file_path,path.join(folder,'new','moved.3mf'));
  const status=await handleCuraApi('cura_project_save_status',{operation_id:'save-1'});
  assert.equal(status.status,'completed');
  assert.equal((await handleCuraApi('cura_path_info',{file_path:current})).readable,true);
  assert.equal(writes.length,2);
  await assert.rejects(()=>handleCuraApi('confirm_cura_operation',{...same,folder}),/Use save_as/);
  await assert.rejects(()=>handleCuraApi('confirm_cura_operation',{...same,file_path:current}),/not file_path/);
});
