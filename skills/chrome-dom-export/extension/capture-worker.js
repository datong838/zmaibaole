// Proposal only. Public visible-tab evidence, never input targeting or OS capture.
const CAPTURE_SAFETY='dom-only-20261021-11';
function captureFields(cmd,operation){
  const expected=operation==='capture-visible'?['captureKey','groupid','op','tabId','windowId']:['groupid','op','tabId','windowId'];
  if(Object.keys(cmd).sort().join(',')!==expected.sort().join(',')||!Number.isSafeInteger(cmd.tabId)||cmd.tabId<0||!Number.isSafeInteger(cmd.windowId)||cmd.windowId<0||typeof cmd.groupid!=='string'||!/^\d{1,32}$/.test(cmd.groupid))throw Error('capture-explicit-scope-required');
  if(operation==='capture-visible'&&(typeof cmd.captureKey!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}$/.test(cmd.captureKey)))throw Error('capture-stable-key-required');
}
async function captureScope(cmd){
  const t=await chrome.tabs.get(cmd.tabId),w=await chrome.windows.get(cmd.windowId),u=new URL(t.url);
  const active=await chrome.tabs.query({active:true,windowId:cmd.windowId});
  if(u.origin!=='https://life.douyin.com'||u.searchParams.getAll('groupid').length!==1||u.searchParams.get('groupid')!==cmd.groupid||t.id!==cmd.tabId||t.windowId!==cmd.windowId||!t.active||w.id!==cmd.windowId||!w.focused||active.length!==1||active[0].id!==cmd.tabId||t.status!=='complete'||t.pendingUrl)throw Error('capture-target-not-active-focused-stable-site');
  return {tabId:t.id,windowId:t.windowId,groupid:cmd.groupid,url:t.url,title:t.title};
}
async function captureGrantStatus(cmd){
  captureFields(cmd,'capture-grant-status');const scope=await captureScope(cmd);
  const grant=(await chrome.storage.session.get('capture-grant:'+scope.tabId))['capture-grant:'+scope.tabId];
  const matches=grant&&JSON.stringify(grant.scope)===JSON.stringify(scope)&&grant.safety_version===CAPTURE_SAFETY;
  return {scope,invocationObserved:!!matches,grant:matches?grant:null,extensionId:chrome.runtime.id,
    permissionUnprovenUntilCapture:true,safety_version:CAPTURE_SAFETY};
}
async function captureAction(tab){
  let u;try{u=new URL(tab.url);}catch{return false;}
  if(u.origin!=='https://life.douyin.com')return false;
  if(!chrome.runtime.getManifest().permissions.includes('activeTab'))throw Error('activeTab-not-declared');
  const groupid=u.searchParams.get('groupid');
  const scope=await captureScope({tabId:tab.id,windowId:tab.windowId,groupid});
  // Only the real Chrome action listener calls this function. Loopback commands,
  // content scripts and control-page buttons have no grant operation.
  await chrome.storage.session.set({['capture-grant:'+tab.id]:{scope,nonce:crypto.randomUUID(),
    invokedAt:new Date().toISOString(),via:'chrome.action.onClicked',safety_version:CAPTURE_SAFETY}});
  return true;
}
async function captureVisible(cmd){
  captureFields(cmd,'capture-visible');
  let changed=false,before=null,status=null,intent=null,issued=false;
  const key='capture-visible:'+cmd.captureKey;
  // Observe the entire asynchronous scope/grant/intent interval, not just the API.
  const activated=info=>{if(info.windowId===cmd.windowId)changed=true;};
  const updated=(id,change)=>{if(id===cmd.tabId&&(change.status==='loading'||change.url))changed=true;};
  const focused=()=>{changed=true;};
  chrome.tabs.onActivated.addListener(activated);chrome.tabs.onUpdated.addListener(updated);chrome.windows.onFocusChanged.addListener(focused);
  try{
    before=await captureScope(cmd);
    status=await captureGrantStatus({op:'capture-grant-status',tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid});
    if(!status.invocationObserved)throw Error('capture-requires-real-extension-action-invocation');
    if((await chrome.storage.session.get(key))[key])throw Error('capture-key-already-issued-use-local-evidence-no-replay');
    intent={state:'intent',scope:before,grantNonce:status.grant.nonce,issuedAt:new Date().toISOString()};
    await chrome.storage.session.set({[key]:intent});issued=true;
    const immediate=await captureScope(cmd);
    if(changed||JSON.stringify(before)!==JSON.stringify(immediate))throw Error('capture-scope-changed-before-image');
    const data=await chrome.tabs.captureVisibleTab(cmd.windowId,{format:'png'});
    const after=await captureScope(cmd);
    if(changed||JSON.stringify(before)!==JSON.stringify(after))throw Error('capture-scope-changed-during-image');
    if(typeof data!=='string'||!data.startsWith('data:image/png;base64,')||data.length>6_000_000)throw Error('capture-png-format-or-size-invalid');
    const observedAt=new Date().toISOString();
    await chrome.storage.session.set({[key]:{...intent,state:'complete',observedAt,viewport_only:true}});
    return {before,after,grant:status.grant,observedAt,captureKey:cmd.captureKey,viewport_only:true,
      imageDataUrl:data,safety_version:CAPTURE_SAFETY,capture_method:'chrome.tabs.captureVisibleTab',pixel_actions_used:false};
  }catch(e){if(issued)await chrome.storage.session.set({[key]:{...intent,state:'unknown',error:String(e.message||e)}});throw e;}
  finally{chrome.tabs.onActivated.removeListener(activated);chrome.tabs.onUpdated.removeListener(updated);chrome.windows.onFocusChanged.removeListener(focused);}
}
