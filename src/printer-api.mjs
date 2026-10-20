import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';

const directory = path.dirname(fileURLToPath(import.meta.url));
const specs = Object.fromEntries(['printer', 'cluster'].map(name => [name,
  JSON.parse(fs.readFileSync(path.join(directory, '../api-specs', `${name}.json`), 'utf8'))]));
// Preserve vendor Swagger; add only independently source-observed local routes.
const webuiSupplement = JSON.parse(fs.readFileSync(path.join(directory, '../api-specs/webui-supplement.json'), 'utf8'));
if (webuiSupplement.basePath !== specs.printer.basePath) throw new Error('Web UI supplement base path mismatch');
for (const [endpoint, operations] of Object.entries(webuiSupplement.paths)) {
  if (specs.printer.paths[endpoint]) throw new Error('Web UI supplement must not override vendor endpoints');
  specs.printer.paths[endpoint] = operations;
}
const confirmations = new Map();
import {printerBaseUrl} from './printer-config.mjs';
const root = path.resolve(process.env.CURA_MCP_PRINT_FILE_ROOT || path.join(process.cwd(), 'print_files'));
const shared = {
  api: {type:'string', enum:['printer','cluster']},
  endpoint: {type:'string', description:'Exact endpoint template from printer_api_catalog, e.g. /printer/heads/{head_id}/position.'},
  path_parameters: {type:'object', additionalProperties:{type:['string','number']}},
  query: {type:'object', additionalProperties:true},
  body: {description:'JSON body (object, scalar or array) according to endpoint schema.'},
  form: {type:'object', additionalProperties:{type:['string','number','boolean']}},
  files: {type:'array', items:{type:'object',properties:{field:{type:'string'},file_path:{type:'string'}},required:['field','file_path'],additionalProperties:false}}
};
function tool(name,description,properties,required,readOnlyHint) {
  return {name,description,inputSchema:{type:'object',properties,required,additionalProperties:false},
    annotations:{readOnlyHint,destructiveHint:!readOnlyHint,openWorldHint:true}};
}
export const printerApiTools = [
  tool('printer_api_catalog','Inspect all documented local S5 printer/cluster R/W endpoints and schemas. Specify api + endpoint to include operation details and definitions.',
    {api:shared.api,endpoint:shared.endpoint},[],true),
  tool('printer_api_read','GET a documented bounded local printer endpoint. Does not support unbounded camera streams. May return network/system details; request only what is needed.',
    shared,['api','endpoint'],true),
  tool('confirm_printer_api_write','Prepare a one-use five-minute confirmation bound to the exact documented write request and current printer state. Show the request and effect to the human and obtain specific approval before printer_api_write. Does not perform the write.',
    {...shared,method:{type:'string',enum:['POST','PUT','DELETE']}},['api','endpoint','method'],false),
  tool('printer_api_write','Execute an explicitly approved documented S5 write with its matching confirmation token. Includes motion, temperature, pause/abort/resume, jobs/materials/configuration/firmware/network operations. Do not invoke without the human approving the exact action. Auth pairing stores credentials in the OS credential store and needs approval on the printer display.',
    {...shared,method:{type:'string',enum:['POST','PUT','DELETE']},confirmation_token:{type:'string'}},['api','endpoint','method','confirmation_token'],false)
];

function transport(args) {
  return new Promise((resolve,reject) => {
    const child = spawn(process.env.CURA_MCP_PYTHON || (process.platform === 'win32' ? 'python' : '/usr/bin/python3'),[path.join(directory,'printer_request.py')],{stdio:['pipe','pipe','pipe']});
    let output='';
    child.stdout.on('data',chunk=>output+=chunk);
    child.stderr.resume();
    const timer=setTimeout(()=>child.kill(),30000);
    child.on('error',error=>{clearTimeout(timer);reject(error);});
    child.on('close',code=>{
      clearTimeout(timer);
      if(code!==0)return reject(new Error('Printer request worker failed'));
      try{resolve(JSON.parse(output));}catch{reject(new Error('Invalid printer response'));}
    });
    child.stdin.end(JSON.stringify({...args,base_url:printerBaseUrl()}));
  });
}

function prepare(args,method) {
  const spec=specs[args.api];
  const operation=spec?.paths[args.endpoint]?.[method.toLowerCase()];
  if(!operation)throw new Error('Endpoint/method is not in the printer-provided API catalog.');
  let endpoint=args.endpoint.replace(/\{([^}]+)\}/g,(_,key)=>{
    const value=args.path_parameters?.[key];
    if(value===undefined || !/^[\w .,@:-]+$/.test(String(value)) || String(value)==='..' || String(value)==='.')throw new Error(`Invalid path parameter: ${key}`);
    return encodeURIComponent(value);
  });
  if(endpoint.includes('?') || endpoint.includes('#') || endpoint.includes('..'))throw new Error('Invalid endpoint');
  const request={path:spec.basePath+endpoint,method};
  for(const key of ['query','body','form'])if(args[key]!==undefined)request[key]=args[key];
  if(args.files)request.files=args.files.map(file=>{
    const resolved=fs.realpathSync(file.file_path);
    const relative=path.relative(fs.realpathSync(root),resolved);
    if(relative.startsWith('..') || path.isAbsolute(relative) || !fs.statSync(resolved).isFile())throw new Error('Files must be staged below the configured print_files folder');
    if(!/^[\w.-]+$/.test(file.field) || !/^[\w .-]+$/.test(path.basename(resolved)))throw new Error('Invalid multipart field/filename');
    return {path:resolved,field:file.field,name:path.basename(resolved),sha256:crypto.createHash('sha256').update(fs.readFileSync(resolved)).digest('hex')};
  });
  if(method==='GET' && ['body','form','files'].some(key=>request[key]!==undefined))throw new Error('Read requests do not accept bodies');
  if(request.body!==undefined && (request.form || request.files))throw new Error('Choose JSON or form data');
  const params=[...(spec.paths[args.endpoint].parameters||[]),...(operation.parameters||[])];
  for(const parameter of params.filter(p=>p.required)) {
    const exists=parameter.in==='path' ? args.path_parameters?.[parameter.name]!==undefined
      :parameter.in==='query' ? args.query?.[parameter.name]!==undefined
      :parameter.in==='body' ? args.body!==undefined
      :parameter.in==='formData' ? args.form?.[parameter.name]!==undefined || args.files?.some(f=>f.field===parameter.name)
      :true;
    if(!exists)throw new Error(`Required ${parameter.in} parameter missing: ${parameter.name}`);
  }
  return request;
}
function canonical(value) {
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value && typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
async function state() {
  const response=await transport({path:'/api/v1/printer/status',method:'GET'});
  if(response.http_status!==200)throw new Error('Cannot establish printer state; refusing write');
  return response.data;
}
function busyAllowed(request) {
  return request.path==='/api/v1/auth/request' || request.path==='/api/v1/print_job/state' ||
    /^\/api\/v1\/printer\/led(?:\/(?:hue|saturation|brightness|blink))?$/.test(request.path) ||
    request.path==='/api/v1/printer/validate_header' ||
    /^\/cluster-api\/v1\/printers\/[^/]+\/(?:action\/)?identify$/.test(request.path) ||
    /^\/cluster-api\/v1\/print_jobs\/[^/]+\/action$/.test(request.path);
}

export async function handlePrinterApi(name,args) {
  if(name==='printer_api_catalog') {
    if(args.endpoint) {
      const spec=specs[args.api];
      if(!spec?.paths[args.endpoint])throw new Error('Unknown API/endpoint');
      return {api:args.api,base_path:spec.basePath,endpoint:args.endpoint,operations:spec.paths[args.endpoint],definitions:spec.definitions};
    }
    return {apis:Object.fromEntries(Object.entries(specs).filter(([key])=>!args.api || key===args.api).map(([key,spec])=>
      [key,{base_path:spec.basePath,endpoints:Object.entries(spec.paths).map(([endpoint,ops])=>({endpoint,methods:Object.keys(ops).filter(m=>['get','post','put','delete','patch'].includes(m))}))}]))};
  }
  const method=name==='printer_api_read'?'GET':args.method;
  if(name!=='printer_api_read' && !['POST','PUT','DELETE'].includes(method))throw new Error('Invalid write method');
  const request=prepare(args,method);
  if(name==='printer_api_read') {
    if(/\/stream$|\/feed$|\/diagnostics\//.test(request.path))throw new Error('Use snapshot/status endpoints; unbounded streams and active diagnostic sampling are not read-only bridge operations');
    return transport(request);
  }
  const current=await state();
  if(current!=='idle' && !busyAllowed(request))throw new Error('Printer is busy; motion/configuration/upload writes are blocked. Pause/resume/abort require exact action confirmation.');
  const fingerprint=canonical(request);
  if(name==='confirm_printer_api_write') {
    const token=crypto.randomUUID();
    confirmations.set(token,{fingerprint,state:current,expires:Date.now()+300000});
    return {confirmation_token:token,expires_in_seconds:300,printer_status:current,
      request:{method,path:request.path,has_body:request.body!==undefined,has_form:!!request.form,files:request.files?.map(f=>({name:f.name,sha256:f.sha256}))},
      warning:'Approval must identify the exact endpoint, request payload, target and effect. This operation can change hardware, interrupt a print, remove data or change network/firmware.'};
  }
  const confirmed=confirmations.get(args.confirmation_token);
  confirmations.delete(args.confirmation_token);
  if(!confirmed || confirmed.expires<Date.now() || confirmed.fingerprint!==fingerprint || confirmed.state!==current)throw new Error('Confirmation is missing, expired, reused, mismatched or printer state changed');
  return transport(request);
}
