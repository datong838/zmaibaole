// Offline worker integration: simulated Chrome APIs + loopback HTTP; no browser launch.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'../extension');
let queued=null,posted=null,downloads=[],store={},messages=[],injections=[];
let reloads=0,reloadFailure=false,recordURL='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123',updates=new Set();
const noop=()=>{};
const context={URL,AbortSignal,Date,crypto:require('node:crypto').webcrypto,console,
  setTimeout:(f,ms)=>ms>=1000?setTimeout(f,ms):undefined,clearTimeout,
  fetch:async (url,init)=>{
    assert.ok(url.startsWith('http://127.0.0.1:17341/bridge/'));
    const data=JSON.parse(init.body);
    assert.equal(init.headers.Authorization,'Bearer test-key');
    if(url.endsWith('/poll'))return {ok:true,json:async()=>({job:queued})};
    posted=data;return {ok:true,json:async()=>({accepted:true})};
  },
  chrome:{
    runtime:{id:'a'.repeat(32),getManifest:()=>({version:'1.0.0'}),getURL:s=>'chrome-extension://'+'a'.repeat(32)+'/'+s,onInstalled:{addListener:noop},onStartup:{addListener:noop},onMessage:{addListener:noop}},
    tabs:{update:async(id,opts)=>({id,...opts}),get:async id=>({id,windowId:1,active:true,status:'complete',title:'抖音来客',url:id===777?recordURL:id===999?'https://other.test/':'https://life.douyin.com/p/life_comment/management'}),sendMessage:async(id,m)=>{messages.push(m);return {ok:true,result:m.op==='ping'?{version:'dom-only-20261021-11'}:{fixture:'tree'}};},create:async()=>{},
      onUpdated:{addListener:f=>updates.add(f),removeListener:f=>updates.delete(f)},reload:async(id,options)=>{reloads++;assert.equal(id,777);assert.equal(options.bypassCache,false);assert.equal(store['records-reload:refresh-success-1']?.state==='intent'||store['records-reload:refresh-unknown-1']?.state==='intent',true);if(reloadFailure)throw Error('mock-reload-unknown');for(const f of [...updates])f(id,{status:'loading'});for(const f of [...updates])f(id,{status:'complete'});}},
    windows:{update:async()=>({focused:true}),get:async()=>({focused:true}),getAll:async()=>[{id:1,focused:true,type:'normal',tabs:[{id:123,windowId:1,title:'抖音来客',url:'https://life.douyin.com/p/life_comment/management',active:true}]}]},
    scripting:{executeScript:async arg=>{assert.equal(arg.world,'ISOLATED');injections.push(arg);}},
    downloads:{search:async()=>downloads},
    storage:{session:{get:async key=>({[key]:store[key]}),set:async obj=>{Object.assign(store,obj);}}},
    alarms:{onAlarm:{addListener:noop},create:async()=>{}},action:{onClicked:{addListener:noop}}
  }
};
context.importScripts=(...files)=>{
  for(const file of files){
    if(file==='config.js')context.LOCAL_BRIDGE_CONFIG={base:'http://127.0.0.1:17341',bridgeToken:'test-key'};
    else vm.runInContext(fs.readFileSync(path.join(dir,file),'utf8'),context);
  }
};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(dir,'worker.js'),'utf8'),context);
async function run(command){queued={id:'fixture-job',command};posted=null;await vm.runInContext('tick()',context);assert.ok(posted);return posted;}
(async()=>{
  for(let i=0;i<20;i++)await Promise.resolve();
  assert.equal(fs.readFileSync(path.join(dir,'sw3.js'),'utf8'),fs.readFileSync(path.join(dir,'worker.js'),'utf8'));
  for(const name of ['sw.js','sw2.js','sw4.js'])assert.equal(fs.readFileSync(path.join(dir,name),'utf8'),fs.readFileSync(path.join(dir,'worker.js'),'utf8'));
  let r=await run({op:'tabs'});assert.equal(r.result[0].tabs[0].allowed,true);
  r=await run({op:'activate',tabId:123});assert.equal(r.ok,true);assert.equal(r.result.active,true);assert.equal(r.result.windowFocused,true);assert.equal(r.result.tabId,123);
  r=await run({op:'activate',tabId:999});assert.equal(r.ok,false);
  r=await run({op:'tree',tabId:123});assert.equal(r.ok,true);assert.equal(injections.length,1);assert.equal(messages[0].channel,'local-dom-export-v1');
  r=await run({op:'tree',tabId:999});assert.equal(r.ok,false);assert.equal(injections.length,1);
  r=await run({op:'cookies',tabId:123});assert.equal(r.ok,false);
  const refresh={op:'reload-records',tabId:777,groupid:'123',reloadKey:'refresh-success-1'};
  r=await run(refresh);assert.equal(r.ok,true);assert.equal(r.result.reloaded,true);assert.equal(reloads,1);assert.equal(updates.size,0);
  r=await run(refresh);assert.equal(r.ok,true);assert.equal(r.result.reused,true);assert.equal(reloads,1);
  for(const bad of [{...refresh,tabId:123},{...refresh,groupid:'999'},{...refresh,groupid:'123&x=y'},{...refresh,url:recordURL}]){r=await run(bad);assert.equal(r.ok,false);assert.equal(reloads,1);}
  reloadFailure=true;r=await run({...refresh,reloadKey:'refresh-unknown-1'});assert.equal(r.ok,false);assert.equal(reloads,2);assert.equal(updates.size,0);
  reloadFailure=false;r=await run({...refresh,reloadKey:'refresh-unknown-1'});assert.equal(r.ok,false);assert.match(r.error,/unknown-no-replay/);assert.equal(reloads,2);
  recordURL='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123&groupid=123';r=await run({...refresh,reloadKey:'another-refresh-1'});assert.equal(r.ok,false);assert.equal(reloads,2);
  recordURL='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123';
  downloads=[];r=await run({op:'download-begin',tabId:123});const ticket=r.result.ticket;
  r=await run({op:'download-status',ticket});assert.equal(r.result.state,'pending');
  downloads=[{id:1,url:'https://other.test/a.xlsx',filename:'/tmp/a.xlsx',state:'complete',exists:true}];
  r=await run({op:'download-status',ticket});assert.equal(r.result.state,'pending');
  downloads=[{id:2,url:'blob:https://life.douyin.com/fixture',filename:'/tmp/report.xlsx',state:'in_progress'}];
  r=await run({op:'download-status',ticket});assert.equal(r.result.state,'in_progress');
  downloads[0].state='complete';downloads[0].exists=true;
  r=await run({op:'download-status',ticket});assert.equal(r.result.path,'/tmp/report.xlsx');assert.equal(r.result.state,'complete');
  downloads.push({id:3,referrer:'https://life.douyin.com/',url:'https://cdn.test/other.xlsx',filename:'/tmp/other.xlsx',state:'complete'});
  r=await run({op:'download-status',ticket});assert.equal(r.ok,false);assert.match(r.error,/ambiguous/);
  r=await run({op:'download-status',ticket,filename:'report.xlsx'});assert.equal(r.result.path,'/tmp/report.xlsx');
  downloads=[{id:4,url:'https://life.douyin.com/a.xlsx',filename:'/tmp/a.xlsx',state:'interrupted',error:'NETWORK_FAILED'}];
  r=await run({op:'download-status',ticket});assert.equal(r.ok,false);assert.match(r.error,/interrupted/);
  r=await run({op:'download-status',ticket:'missing'});assert.equal(r.ok,false);
  console.log('Worker protocol/download/activation cases passed (mock Chrome).');
})().catch(e=>{console.error(e);process.exitCode=1;});
