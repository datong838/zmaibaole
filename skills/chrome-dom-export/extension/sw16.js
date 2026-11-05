importScripts('config.js','policy.js','capture-worker.js','download-reconcile.js','viewport-worker.js','readonly-scope-worker.js');
const C=globalThis.LOCAL_BRIDGE_CONFIG, P=globalThis.DOM_EXPORT_POLICY;
const SAFETY_VERSION='dom-only-20261021-11';
let busy=false;
let pollTimer=null;
async function rpc(path,body) {
  if(C.base!=='http://127.0.0.1:17341') throw Error('fixed loopback address required');
  const r=await fetch(C.base+path,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+C.bridgeToken},body:JSON.stringify(body),signal:AbortSignal.timeout(8000),credentials:'omit',cache:'no-store',redirect:'error'});
  if(!r.ok) throw Error('bridge HTTP '+r.status);
  return r.json();
}
async function target(id) {
  if(!Number.isSafeInteger(id)) throw Error('integer tabId required');
  const t=await chrome.tabs.get(id);
  if(!t.url || new URL(t.url).origin!==P.origin) throw Error('tab is not allowed site');
  return t;
}
async function content(cmd) {
  await target(cmd.tabId);
  // Install in an existing, already logged-in tab without reloading Chrome or the page.
  // ISOLATED is extension content-script execution, not a debugging session.
  await chrome.scripting.executeScript({target:{tabId:cmd.tabId},files:['policy.js','viewport-proof.js','review-proof.js','region-proof.js','content.js'],world:'ISOLATED'});
  const probe=await chrome.tabs.sendMessage(cmd.tabId,{op:'ping',channel:'local-dom-export-v1'},{frameId:0});
  if(!probe?.ok||probe.result?.version!==SAFETY_VERSION)throw Error('stale-content-version: reload reviewed extension before any operation');
  const r=cmd.op==='ping'?probe:await chrome.tabs.sendMessage(cmd.tabId,{...cmd,channel:'local-dom-export-v1'},{frameId:0});
  if(!r?.ok) throw Error(r?.error || 'content script unavailable');
  return r.result;
}
function sourceAllowed(d) {
  return [d.url,d.finalUrl,d.referrer].some(s=>{
    try {return new URL(String(s || '').replace(/^blob:/,'')).origin===P.origin;} catch{return false;}
  });
}
function recordScope(t,cmd){
  if(!Number.isSafeInteger(cmd.tabId)||cmd.tabId<0||typeof cmd.groupid!=='string'||!/^\d{1,32}$/.test(cmd.groupid)||typeof cmd.reloadKey!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}$/.test(cmd.reloadKey))throw Error('invalid-record-reload-scope');
  const u=new URL(t.url);
  if(t.id!==cmd.tabId||u.origin!==P.origin||u.pathname!=='/p/fulfillsettle/export_records/20101'||u.searchParams.getAll('groupid').length!==1||u.searchParams.get('groupid')!==cmd.groupid)throw Error('record-reload-tab-url-group-mismatch');
  return t;
}
function reloadCompletion(tabId){
  let started=false,timer,listener;
  const cleanup=()=>{clearTimeout(timer);chrome.tabs.onUpdated.removeListener(listener);};
  const promise=new Promise((resolve,reject)=>{
    listener=(id,change)=>{if(id!==tabId)return;if(change.status==='loading')started=true;if(started&&change.status==='complete'){cleanup();resolve();}};
    chrome.tabs.onUpdated.addListener(listener);
    timer=setTimeout(()=>{cleanup();reject(Error('record-reload-completion-unknown-no-replay'));},15000);
  });
  // The API reload callback may fail before the load event; avoid an unhandled timeout.
  promise.catch(()=>{});return {promise,cancel:cleanup};
}
async function reloadRecords(cmd){
  if(Object.keys(cmd).sort().join(',')!=='groupid,op,reloadKey,tabId')throw Error('record-reload-fields-denied');
  const before=recordScope(await target(cmd.tabId),cmd),key='records-reload:'+cmd.reloadKey;
  const old=(await chrome.storage.session.get(key))[key];
  const scope={tabId:before.id,windowId:before.windowId,groupid:cmd.groupid,url:before.url};
  if(old){
    if(JSON.stringify(old.scope)!==JSON.stringify(scope))throw Error('record-reload-key-scope-conflict');
    if(old.state==='complete')return {...old.result,reused:true};
    throw Error('record-reload-outcome-unknown-no-replay');
  }
  const intent={state:'intent',scope,issuedAt:new Date().toISOString()};
  await chrome.storage.session.set({[key]:intent});
  const completion=reloadCompletion(before.id);
  try{
    await chrome.tabs.reload(before.id,{bypassCache:false});
    await completion.promise;
    const after=recordScope(await target(before.id),cmd);
    if(after.url!==before.url||after.windowId!==before.windowId||after.status!=='complete')throw Error('record-reload-after-scope-mismatch-no-replay');
    const result={...scope,reloaded:true,loadComplete:true,observedAt:new Date().toISOString(),reloadKey:cmd.reloadKey,safety_version:SAFETY_VERSION};
    await chrome.storage.session.set({[key]:{...intent,state:'complete',result}});return result;
  }catch(e){
    completion.cancel();await chrome.storage.session.set({[key]:{...intent,state:'unknown',error:String(e.message||e)}});throw e;
  }
}
async function execute(cmd) {
  if(cmd.op==='readonly-scope')return readonlyScope(cmd);
  if(cmd.op==='dom-region-proof'){
    if(Object.keys(cmd).sort().join(',')!=='base,groupid,op,purpose,selectors,tabId,windowId')throw Error('region-fields-denied');
    const before=await captureScope(cmd),result=await content(cmd),after=await captureScope(cmd);
    if(JSON.stringify(before)!==JSON.stringify(after)||result.url!==before.url||JSON.stringify(result.scope)!==JSON.stringify({tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid}))throw Error('region-scope-changed');
    return {...result,base_proof:{...result.base_proof,safety_version:SAFETY_VERSION},safety_version:SAFETY_VERSION};
  }
  if(cmd.op==='review-viewport-proof'){
    if(Object.keys(cmd).sort().join(',')!=='dom_sha256,groupid,op,reviews,scope,source_sha256,tabId,windowId')throw Error('review-proof-fields-denied');
    const before=await captureScope(cmd),result=await content(cmd),after=await captureScope(cmd);
    if(JSON.stringify(before)!==JSON.stringify(after)||result.url!==before.url||JSON.stringify(result.scope)!==JSON.stringify({tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid}))throw Error('review-proof-scope-changed');
    return {...result,safety_version:SAFETY_VERSION};
  }
  if(cmd.op==='viewport-proof')return viewportProof(cmd);
  if(cmd.op==='download-reconcile')return reconcileDownload(cmd);
  if(cmd.op==='capture-visible')return captureVisible(cmd);
  if(cmd.op==='capture-grant-status')return captureGrantStatus(cmd);
  if(cmd.op==='tabs') {
    const windows=await chrome.windows.getAll({populate:true});
    return windows.map(w=>({windowId:w.id,focused:w.focused,type:w.type,tabs:(w.tabs || []).map(t=>({tabId:t.id,windowId:t.windowId,title:t.title,url:t.url,active:t.active,allowed:!!t.url && t.url.startsWith(P.origin+'/')}))}));
  }
  if(cmd.op==='reload-records')return reloadRecords(cmd);
  if(cmd.op==='activate') {
    const t=await target(cmd.tabId);
    await chrome.windows.update(t.windowId,{focused:true});
    await chrome.tabs.update(t.id,{active:true});
    const actual=await chrome.tabs.get(t.id),win=await chrome.windows.get(t.windowId);
    if(!actual.active||!win.focused)throw Error('existing-tab-focus-not-confirmed');
    return {tabId:actual.id,windowId:actual.windowId,url:actual.url,title:actual.title,active:true,windowFocused:true,observedAt:new Date().toISOString(),safety_version:SAFETY_VERSION};
  }
  if(['ping','tree','find','click','hover','filter','scroll'].includes(cmd.op)) return content(cmd);
  if(cmd.op==='download-begin') {
    await target(cmd.tabId);
    const ticket=crypto.randomUUID();
    const baseline=(await chrome.downloads.search({startedAfter:new Date(Date.now()-60000).toISOString()})).map(d=>d.id);
    const record={tabId:cmd.tabId,since:new Date().toISOString(),baseline,expires:Date.now()+10*60000};
    await chrome.storage.session.set({[ticket]:record});
    return {ticket,since:record.since,expires:record.expires};
  }
  if(cmd.op==='download-status') {
    const rec=(await chrome.storage.session.get(cmd.ticket))[cmd.ticket];
    if(!rec || rec.expires<Date.now()) throw Error('download ticket missing or expired');
    const all=await chrome.downloads.search({startedAfter:rec.since});
    const matches=all.filter(d=>!rec.baseline.includes(d.id) && sourceAllowed(d) && P.downloadExtensions.some(x=>d.filename?.toLowerCase().endsWith('.'+x)) && (!cmd.filename || d.filename.split(/[\\/]/).pop()===cmd.filename));
    if(matches.length>1) throw Error('ambiguous downloads: specify exact filename; never guess');
    if(!matches.length) return {state:'pending',note:'No matching site download; cross-domain source without site referrer is intentionally rejected.'};
    const d=matches[0];
    if(d.state==='interrupted') throw Error('download interrupted: '+(d.error || 'unknown'));
    return {state:d.state,downloadId:d.id,path:d.filename,exists:d.exists,bytesReceived:d.bytesReceived,totalBytes:d.totalBytes};
  }
  throw Error('unsupported operation');
}
async function tick() {
  if(busy) return {busy:true};
  if(pollTimer!==null){clearTimeout(pollTimer);pollTimer=null;}
  busy=true;
  let continuePolling=false;
  try {
    const alarm=await chrome.alarms.get('dom-bridge-poll');
    if(!alarm || alarm.name!=='dom-bridge-poll' || alarm.periodInMinutes!==0.5)throw Error('poll-recovery-alarm-unavailable');
    const {job}=await rpc('/bridge/poll',{extensionId:chrome.runtime.id,version:chrome.runtime.getManifest().version,safety_version:SAFETY_VERSION});
    if(!job){continuePolling=true;return {connected:true,idle:true};}
    let response;
    try {response={ok:true,result:await execute(job.command)};} catch(e) {response={ok:false,error:String(e.message || e)};}
    // A delivered action is NEVER replayed after a network failure.
    await rpc('/bridge/result',{id:job.id,...response});
    continuePolling=true;
    return {connected:true,lastJob:job.id,ok:response.ok,error:response.error};
  } catch(e) {
    // Stop on poll/result uncertainty. A later alarm/control polls only new jobs.
    return {connected:false,error:String(e.message || e)};
  } finally {
    busy=false;
    // Keep the existing bounded server long-poll available across idle periods.
    // One timer + busy owner; no command or result is retained for retry.
    if(continuePolling && typeof setTimeout==='function') {
      pollTimer=setTimeout(()=>{pollTimer=null;void tick();},50);
    }
  }
}
chrome.alarms.onAlarm.addListener(a=>{if(a.name==='dom-bridge-poll') void tick();});
async function setup() {await chrome.alarms.create('dom-bridge-poll',{periodInMinutes:0.5});void tick();}
chrome.runtime.onInstalled.addListener(setup);
chrome.runtime.onStartup.addListener(setup);
const CONTROL_PROTOCOL='local-dom-control-v1';
function ownControlSender(s){
  // Chrome supplies sender metadata; message payload cannot choose these fields.
  // Exact top-level extension document only, including a control page in a tab.
  const url=chrome.runtime.getURL('control.html');
  if(!s || s.id!==chrome.runtime.id || s.url!==url ||
     (s.origin!==undefined && s.origin!=='chrome-extension://'+chrome.runtime.id) ||
     (s.frameId!==undefined && s.frameId!==0))return false;
  if(s.tab!==undefined){
    const t=s.tab;
    if(!t || !Number.isSafeInteger(t.id) || t.id<0 ||
       !Number.isSafeInteger(t.windowId) || t.windowId<0 || t.url!==url ||
       (t.pendingUrl!==undefined && t.pendingUrl!==url))return false;
  }
  return true;
}
chrome.runtime.onMessage.addListener((m,s,send)=>{
  if(!ownControlSender(s) || !m || typeof m!=='object' || Array.isArray(m) ||
     Object.keys(m).length!==1 || m.type!=='tick'){
    // A bounded generic denial is safe for untrusted callers; never poll for them.
    send({control_protocol:CONTROL_PROTOCOL,request_accepted:false,error:'control-request-denied'});
    return false;
  }
  const sender_context={document_kind:s.tab===undefined?'extension-page':'extension-tab',origin_present:s.origin!==undefined,frame_present:s.frameId!==undefined};
  tick().then(result=>send({...result,control_protocol:CONTROL_PROTOCOL,request_accepted:true,sender_context}),
    ()=>send({control_protocol:CONTROL_PROTOCOL,request_accepted:true,connected:false,error:'control-tick-failed'}));
  return true;
});
chrome.action.onClicked.addListener(tab=>{void captureAction(tab).then(handled=>{if(!handled)return chrome.tabs.create({url:chrome.runtime.getURL('control.html')});}).catch(()=>{});});


// Ensure the existing alarm is registered after an explicit extension refresh.
setup();
