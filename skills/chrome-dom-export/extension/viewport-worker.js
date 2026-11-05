async function viewportProof(cmd){
  if(Object.keys(cmd).sort().join(',')!=='dom_sha256,elements,groupid,op,source_sha256,tabId,windowId')throw Error('viewport-proof-fields-denied');
  const scope=await captureScope(cmd);
  const result=await content(cmd);
  const after=await captureScope(cmd);
  if(JSON.stringify(scope)!==JSON.stringify(after)||result.url!==scope.url||JSON.stringify(result.scope)!==JSON.stringify({tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid}))throw Error('viewport-proof-scope-changed');
  return {...result,safety_version:SAFETY_VERSION};
}
