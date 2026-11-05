// One command, four original serial public reads. No caching, input or retry.
async function readonlyScope(cmd) {
  if(Object.keys(cmd).sort().join(',')!=='op,tabId,windowId' || cmd.op!=='readonly-scope' ||
     !['tabId','windowId'].every(k=>Number.isSafeInteger(cmd[k])&&cmd[k]>=0))throw Error('readonly-scope-fields-denied');
  function scoped(tabs){
    if(!Array.isArray(tabs))throw Error('readonly-scope-tabs-invalid');
    const matches=tabs.flatMap(w=>(w.tabs||[]).filter(t=>t.tabId===cmd.tabId).map(t=>({w,t})));
    if(matches.length!==1)throw Error('readonly-scope-tab-not-unique');
    const {w,t}=matches[0];
    if(w.windowId!==cmd.windowId || t.windowId!==cmd.windowId)throw Error('readonly-scope-window-changed');
    if(t.allowed!==true || new URL(t.url).origin!==P.origin)throw Error('readonly-scope-site-denied');
  }
  const commands=[{op:'tabs'},{op:'ping',tabId:cmd.tabId},{op:'tree',tabId:cmd.tabId},{op:'tabs'}];
  const keys=['before','ping','tree','after'], result={},steps=[],started=performance.now();
  for(let i=0;i<commands.length;i++){
    const begin=performance.now(),value=await execute(commands[i]),elapsed_ms=performance.now()-begin;
    if(!Number.isFinite(elapsed_ms)||elapsed_ms<0)throw Error('readonly-scope-clock-invalid');
    result[keys[i]]=value;steps.push({op:commands[i].op,elapsed_ms});
    if(i===0||i===3)scoped(value);
    if(i===1&&(value?.version!==SAFETY_VERSION||value?.safety!=='DOM-only'))throw Error('readonly-scope-ping-version-required');
  }
  const elapsed_ms=performance.now()-started;
  if(!Number.isFinite(elapsed_ms)||elapsed_ms<0)throw Error('readonly-scope-clock-invalid');
  return {schema:'readonly-scope-v1',scope:{tabId:cmd.tabId,windowId:cmd.windowId},commands,...result,
    timing:{clock:'worker-performance-now',steps,elapsed_ms}};
}
