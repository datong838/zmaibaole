document.getElementById('identity').textContent='Extension ID: '+chrome.runtime.id;
const loadedVersion=chrome.runtime.getManifest().version;
const versionLabel=document.getElementById('loaded-version');
if(versionLabel) versionLabel.textContent=`已加载扩展版本：${loadedVersion}`;
document.getElementById('status').textContent=`DOM-only bridge ${loadedVersion}；无自动刷新。`;
document.getElementById('refresh').addEventListener('click',()=>{
  document.getElementById('status').textContent='正在加载已审核的扩展更新；不会重启Chrome或网站。';
  chrome.runtime.reload();
});
const CONTROL_PROTOCOL='local-dom-control-v1';
async function poll(){
  const started=performance.now();
  const show=value=>{document.getElementById('status').textContent=JSON.stringify({...value,rpc_elapsed_ms:Math.max(0,Math.round(performance.now()-started))});};
  try{
    const result=await chrome.runtime.sendMessage({type:'tick'});
    if(result===undefined || result===null){show({state:'no-response',error:'worker-returned-no-response'});return;}
    if(typeof result!=='object' || Array.isArray(result) || result.control_protocol!==CONTROL_PROTOCOL || typeof result.request_accepted!=='boolean'){
      show({state:'unexpected-response',error:'control-response-protocol-mismatch'});return;
    }
    if(!result.request_accepted){show({state:'request-denied',error:'control-request-denied'});return;}
    if(result.busy===true){show({state:'busy',request_accepted:true});return;}
    if(typeof result.connected!=='boolean'){show({state:'unexpected-response',error:'control-response-state-missing'});return;}
    // Do not dump arbitrary worker payload or exception strings into the page.
    const sender=result.sender_context;
    const sender_context=sender && ['extension-tab','extension-page'].includes(sender.document_kind) && typeof sender.origin_present==='boolean' && typeof sender.frame_present==='boolean'
      ?{document_kind:sender.document_kind,origin_present:sender.origin_present,frame_present:sender.frame_present}:undefined;
    show({state:result.connected?'connected':'disconnected',request_accepted:true,
      ...(sender_context?{sender_context}:{}),
      ...(typeof result.idle==='boolean'?{idle:result.idle}:{}),
      ...(typeof result.ok==='boolean'?{last_job_ok:result.ok}:{}),
      ...(result.error?{error:'worker-reported-error'}:{})});
  }catch(e){show({state:'transport-error',error:'control-message-failed'});}
}
setInterval(poll,1500);void poll();
