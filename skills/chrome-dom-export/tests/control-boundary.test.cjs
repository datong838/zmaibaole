const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const base=path.join(__dirname,'..'),id='a'.repeat(32),url=`chrome-extension://${id}/control.html`,origin=`chrome-extension://${id}`;
const worker=fs.readFileSync(path.join(base,'extension/worker.js'),'utf8');
const control=fs.readFileSync(path.join(base,'extension/control.js'),'utf8');
const noop=()=>{};
async function harness(){
 let listener,polls=0;const ctx={URL,AbortSignal,console,setTimeout:noop,
  importScripts:()=>{},LOCAL_BRIDGE_CONFIG:{base:'http://127.0.0.1:17341',bridgeToken:'synthetic-not-real'},DOM_EXPORT_POLICY:{origin:'https://life.douyin.com'},
  fetch:async(u,options)=>{assert.equal(u,'http://127.0.0.1:17341/bridge/poll');assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');assert.equal(options.cache,'no-store');polls++;return {ok:true,json:async()=>({job:null})};},
  chrome:{runtime:{id,getURL:s=>`chrome-extension://${id}/${s}`,getManifest:()=>({version:'test'}),onMessage:{addListener:f=>listener=f},onInstalled:{addListener:noop},onStartup:{addListener:noop}},alarms:{create:async()=>{},onAlarm:{addListener:noop}},action:{onClicked:{addListener:noop}}}};
 vm.createContext(ctx);vm.runInContext(worker,ctx);await new Promise(setImmediate);polls=0;
 return {ctx,count:()=>polls,message:async(m,s)=>{let result;const ret=listener(m,s,r=>result=r);await new Promise(setImmediate);return {ret,result};}};
}
const sender=()=>({id,url,origin,frameId:0,tab:{id:17,windowId:8,url}});
test('own exact control extension tab polls once with fixed credential-free loopback transport',async()=>{
 const h=await harness(),r=await h.message({type:'tick'},sender());assert.equal(r.ret,true);assert.equal(h.count(),1);assert.equal(r.result.connected,true);assert.equal(r.result.request_accepted,true);assert.equal(r.result.control_protocol,'local-dom-control-v1');assert.equal(r.result.sender_context.document_kind,'extension-tab');
});
test('own extension sender permits optional absent metadata but rejects conflicting metadata',async()=>{
 const h=await harness(),s=sender();delete s.tab;assert.equal((await h.message({type:'tick'},s)).result.request_accepted,true);assert.equal(h.count(),1);delete s.frameId;delete s.origin;const r=await h.message({type:'tick'},s);assert.equal(r.result.request_accepted,true);assert.equal(r.result.sender_context.document_kind,'extension-page');assert.equal(r.result.sender_context.origin_present,false);assert.equal(r.result.sender_context.frame_present,false);assert.equal(h.count(),2);
});
test('content, foreign extension, lookalike URLs, query/hash, origin, iframe and malformed tab cannot poll',async()=>{
 const cases=[s=>s.id='b'.repeat(32),s=>s.url='https://life.douyin.com/',s=>s.url=url+'.evil',s=>s.url=url+'?x=1',s=>s.url=url+'#x',s=>s.origin='null',s=>s.origin='https://life.douyin.com',s=>s.frameId=1,s=>s.tab.url='https://life.douyin.com/',s=>s.tab.pendingUrl='https://other.invalid/',s=>s.tab.id=-1,s=>s.tab.id='17',s=>delete s.tab.windowId,s=>s.tab=null];
 for(const mutate of cases){const h=await harness(),s=sender();mutate(s);const r=await h.message({type:'tick'},s);assert.equal(r.ret,false);assert.equal(r.result.error,'control-request-denied');assert.equal(h.count(),0);assert.deepEqual(Object.keys(r.result).sort(),['control_protocol','error','request_accepted']);}
});
test('payload is not an authorization source; other operations/extra fields denied without poll',async()=>{
 const h=await harness();for(const m of [null,[],{type:'tick',tabId:17},{type:'execute'},{type:'tick',sender:sender()}])assert.equal((await h.message(m,sender())).result.request_accepted,false);assert.equal(h.count(),0);
});
async function panel(response,{throws=false}={}){
 const elements=new Map(['identity','status','refresh'].map(k=>[k,{textContent:'',addEventListener:noop}]));let calls=0,interval=0;const ctx={document:{getElementById:k=>elements.get(k)},performance:{now:()=>25},chrome:{runtime:{id,getManifest:()=>({version:'test'}),reload:()=>{throw Error('must not reload');},sendMessage:async m=>{calls++;assert.deepEqual(JSON.parse(JSON.stringify(m)),{type:'tick'});if(throws)throw Error('synthetic-secret-not-for-output');return response;}}},setInterval:(_f,ms)=>{interval=ms;}};vm.createContext(ctx);vm.runInContext(control,ctx);await new Promise(setImmediate);return {state:JSON.parse(elements.get('status').textContent),calls,interval,text:elements.get('status').textContent};
}
test('undefined/null worker response becomes explicit no-response diagnostic rather than blank',async()=>{
 for(const response of [undefined,null]){const r=await panel(response);assert.equal(r.state.state,'no-response');assert.equal(r.state.error,'worker-returned-no-response');assert.equal(r.calls,1);assert.equal(r.interval,1500);assert.equal(r.state.rpc_elapsed_ms,0);}
});
test('panel distinguishes denial, version mismatch and malformed state',async()=>{
 const proto={control_protocol:'local-dom-control-v1',request_accepted:true};
 assert.equal((await panel({...proto,request_accepted:false})).state.state,'request-denied');
 for(const value of ['secret',[],{connected:true},{...proto,control_protocol:'other'},{...proto}])assert.equal((await panel(value)).state.state,'unexpected-response');
});
test('busy/idle/success/disconnect diagnostics keep payload, credentials and exception text out of page',async()=>{
 const proto={control_protocol:'local-dom-control-v1',request_accepted:true};
 assert.equal((await panel({...proto,busy:true})).state.state,'busy');
 const idle=await panel({...proto,connected:true,idle:true,private_extra:'synthetic-secret'});assert.equal(idle.state.idle,true);assert.equal(idle.text.includes('synthetic-secret'),false);
 const disconnected=await panel({...proto,connected:false,error:'synthetic-secret'});assert.equal(disconnected.state.state,'disconnected');assert.equal(disconnected.state.error,'worker-reported-error');assert.equal(disconnected.text.includes('synthetic-secret'),false);
 const success=await panel({...proto,connected:true,ok:false});assert.equal(success.state.last_job_ok,false);
 const failed=await panel(undefined,{throws:true});assert.equal(failed.state.state,'transport-error');assert.equal(failed.text.includes('synthetic-secret'),false);
});
test('rpc bound and polling cadence unchanged; active worker has no debug permissions',()=>{
 assert.match(worker,/C\.base!=='http:\/\/127\.0\.0\.1:17341'/);assert.match(worker,/credentials:'omit'/);assert.match(worker,/periodInMinutes:0\.5/);assert.match(control,/setInterval\(poll,1500\)/);const manifest=JSON.parse(fs.readFileSync(path.join(base,'extension/manifest.json'),'utf8'));assert.equal(manifest.permissions.includes('debugger'),false);assert.equal(manifest.permissions.includes('cookies'),false);assert.equal(fs.readFileSync(path.join(base,'extension',manifest.background.service_worker),'utf8'),worker);assert.doesNotMatch(worker,/chrome\.debugger/);
});

test('panel exposes only bounded sender diagnostic fields',async()=>{const r=await panel({control_protocol:'local-dom-control-v1',request_accepted:true,connected:true,sender_context:{document_kind:'extension-tab',origin_present:true,frame_present:false,private_extra:'synthetic-secret'}});assert.equal(r.state.sender_context.document_kind,'extension-tab');assert.equal(r.text.includes('synthetic-secret'),false);});
