import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
const pending=new Map();
const root=path.resolve(process.env.CURA_MCP_PRINT_FILE_ROOT||path.join(process.cwd(),'print_files'));
const connectionPath=process.env.CURA_MCP_BRIDGE_CONNECTION_PATH||(process.platform === 'darwin' ? path.join(os.homedir(),'Library/Application Support/cura/5.13/cura-mcp-bridge.json') : path.join(process.env.APPDATA || path.join(os.homedir(),'AppData','Roaming'),'cura','5.13','cura-mcp-bridge.json'));
const schema={action:{type:'string',enum:['set_settings','slice','export_gcode','save_project']},
  extruder:{type:'integer',minimum:0},values:{type:'object',additionalProperties:true},
  file_path:{type:'string'},build_plate:{type:'integer',minimum:0},
  mode:{type:'string',enum:['save','save_as'],description:'save overwrites the known current project; save_as selects a new name and/or folder.'},
  file_name:{type:'string',description:'Save As filename; .3mf is appended if omitted. No folder separators.'},
  folder:{type:'string',description:'Absolute Save As folder. Omit to use the current project folder or Cura save folder.'},
  create_folder:{type:'boolean',description:'Explicitly create a missing destination folder when executing Save As.'}};
function tool(name,description,properties,required,readOnlyHint){return {name,description,
  inputSchema:{type:'object',properties,required,additionalProperties:false},
  annotations:{readOnlyHint,destructiveHint:!readOnlyHint,openWorldHint:false}};}
export const curaApiTools=[
  tool('cura_inspect','Read the live Cura machine/profile, extruders/materials, scene objects, backend state and sliced build plates, explicitly on its main thread.',{},[],true),
  tool('cura_settings','Read effective global or extruder settings. Omit keys to list available setting keys; provide at most 200 keys for values.',{keys:{type:'array',items:{type:'string'}},extruder:{type:'integer',minimum:0}},[],true),
  tool('confirm_cura_operation','Prepare a five-minute one-use confirmation for exact settings, slicing, G-code export or project Save/Save As. Project confirmation shows the resolved destination and binds existing-file SHA256. Show the changes before executing.',schema,['action'],false),
  tool('cura_operation','Apply approved Cura settings, slice, export G-code, or save a full 3MF project. Project saves return an operation_id; poll cura_project_save_status for completion. Never prints or uploads automatically.',{...schema,confirmation_token:{type:'string'}},['action','confirmation_token'],false),
  tool('cura_project_save_status','Read completion, validated archive size/hash or failure for a project save. A running response is not a completed save.',{operation_id:{type:'string'}},['operation_id'],true),
  tool('cura_path_info','Inspect one absolute path from Cura itself: existence, type, readability, resolved path and OS error. Does not return file contents.',{file_path:{type:'string'}},['file_path'],true)
];
function normalized(args){
  const {confirmation_token,...request}=args;
  if(!schema.action.enum.includes(request.action))throw new Error('Unknown Cura action');
  if(request.action==='set_settings' && (!request.values || !Object.keys(request.values).length))throw new Error('Provide settings values');
  if(request.action==='export_gcode'){
    if(!request.file_path || !path.isAbsolute(request.file_path) || !request.file_path.toLowerCase().endsWith('.gcode'))throw new Error('Absolute .gcode output path required');
    const resolved=path.resolve(request.file_path);
    const parent=fs.realpathSync(path.dirname(resolved));
    const relative=path.relative(fs.realpathSync(root),parent);
    if(relative.startsWith('..') || path.isAbsolute(relative) || fs.existsSync(resolved))throw new Error('Export must create a new file below the staging folder');
    request.file_path=path.join(parent,path.basename(resolved));
  }
  return request;
}
async function command(name,body){
  const c=JSON.parse(fs.readFileSync(connectionPath,'utf8'));
  if(c.host!=='127.0.0.1' || !Number.isInteger(c.port) || !c.token)throw new Error('Invalid loopback connection');
  const response=await fetch(`http://${c.host}:${c.port}/v1/commands/${name}`,{method:'POST',
    headers:{'X-Cura-Bridge-Token':c.token,'content-type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(8000)});
  const result=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(`Cura command ${name} returned HTTP ${response.status}: ${result.error || 'request rejected'}`);
  return result;
}
function canonical(value){
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value && typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
export async function handleCuraApi(name,args){
  if(name==='cura_inspect')return command('inspect',{});
  if(name==='cura_settings')return command('get_settings',args);
  if(name==='cura_project_save_status')return command('project_save_status',args);
  if(name==='cura_path_info')return command('path_info',args);
  let request=normalized(args);
  if(request.action==='save_project'){
    if(request.file_path || request.values || request.extruder!==undefined || request.build_plate!==undefined)throw new Error('Project save uses mode, file_name and folder, not file_path/settings');
    const {action,...options}=request;
    request={action,...await command('plan_project_save',options)};
  }
  const fingerprint=canonical(request);
  const state=await command('inspect',{});
  const machine=state.machine.id;
  if(name==='confirm_cura_operation'){
    const token=crypto.randomUUID();pending.set(token,{fingerprint,machine,expires:Date.now()+300000});
    return {confirmation_token:token,expires_in_seconds:300,machine:state.machine,request,
      warning:'Approve these exact Cura workspace changes before execution. No physical print is started.'};
  }
  const record=pending.get(args.confirmation_token);pending.delete(args.confirmation_token);
  if(!record || record.expires<Date.now() || record.fingerprint!==fingerprint || record.machine!==machine)throw new Error('Confirmation missing, expired, reused, mismatched or active Cura machine changed');
  const {action,...body}=request;
  return command(action,body);
}
