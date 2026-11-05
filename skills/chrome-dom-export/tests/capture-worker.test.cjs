// Offline only. A mocked onClicked observation is not proof of real activeTab grant.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const png='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg==';
const event=()=>({listeners:new Set(),addListener(f){this.listeners.add(f);},removeListener(f){this.listeners.delete(f);},emit(...args){for(const f of this.listeners)f(...args);}});
let tab={id:7,windowId:1,url:'https://life.douyin.com/p/governance?groupid=123',title:'抖音来客',active:true,status:'complete'},focused=true,captures=0,store={},during=null,whileIntent=null;
const chrome={runtime:{id:'a'.repeat(32),getManifest:()=>({permissions:['tabs','scripting','activeTab']})},storage:{session:{get:async k=>({[k]:store[k]}),set:async v=>{Object.assign(store,v);if(whileIntent&&Object.keys(v).some(k=>k.startsWith('capture-visible:')))whileIntent();}}},
 tabs:{get:async id=>({...tab,id}),query:async()=>[{...tab}],onActivated:event(),onUpdated:event(),captureVisibleTab:async(id,opts)=>{assert.equal(id,1);assert.equal(opts.format,'png');captures++;if(during)during();return png;}},
 windows:{get:async id=>({id,focused}),onFocusChanged:event()}};
const c={chrome,URL,Date,crypto:require('node:crypto').webcrypto};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/capture-worker.js'),'utf8'),c);
const invoke=(name,arg)=>{c.arg=arg;return vm.runInContext(name+'(arg)',c);};
const cmd={op:'capture-visible',tabId:7,windowId:1,groupid:'123',captureKey:'fixture-capture-1'};
(async()=>{
 await assert.rejects(()=>invoke('captureVisible',cmd),/real-extension-action/);assert.equal(captures,0);
 assert.equal(await invoke('captureAction',tab),true);
 let status=await invoke('captureGrantStatus',{op:'capture-grant-status',tabId:7,windowId:1,groupid:'123'});
 assert.equal(status.invocationObserved,true);assert.equal(status.permissionUnprovenUntilCapture,true);
 let r=await invoke('captureVisible',cmd);assert.equal(r.viewport_only,true);assert.equal(r.imageDataUrl,png);assert.equal(captures,1);
 assert.ok(!JSON.stringify(store).includes('data:image'));assert.equal(chrome.tabs.onActivated.listeners.size,0);
 await assert.rejects(()=>invoke('captureVisible',cmd),/key-already-issued/);assert.equal(captures,1);
 for(const change of [{windowId:99},{groupid:'999'},{tabId:99},{captureKey:'x'},{url:tab.url}]){
  await assert.rejects(()=>invoke('captureVisible',{...cmd,...change}));assert.equal(captures,1);
 }
 focused=false;await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-capture-2'}));focused=true;
 tab.active=false;await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-capture-2'}));tab.active=true;
 during=()=>chrome.tabs.onActivated.emit({windowId:1,tabId:99});await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-capture-2'}),/scope-changed/);assert.equal(captures,2);
 during=null,whileIntent=null;await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-capture-2'}),/key-already-issued/);assert.equal(captures,2);
 tab.url+='&groupid=123';await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-capture-3'}));assert.equal(captures,2);
 tab.url=tab.url.replace('&groupid=123','');
 whileIntent=()=>{chrome.tabs.onActivated.emit({windowId:1,tabId:99});chrome.tabs.onActivated.emit({windowId:1,tabId:7});};
 const beforeRace=captures;await assert.rejects(()=>invoke('captureVisible',{...cmd,captureKey:'fixture-intent-gap-race'}),/scope-changed-before/);assert.equal(captures,beforeRace);
 whileIntent=null;
 console.log('Visible capture/action/scope/idempotency cases passed (mock Chrome; no real authorization).');
})().catch(e=>{console.error(e);process.exitCode=1;});
