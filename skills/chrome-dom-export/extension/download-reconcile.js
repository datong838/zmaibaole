/* Read-only continuation of an already journalled export download. No download API. */
async function reconcileDownload(cmd) {
  if(Object.keys(cmd).sort().join(',')!=='filename,groupid,op,since,tabId,ticket')throw Error('download-reconcile-fields-denied');
  if(!Number.isSafeInteger(cmd.tabId)||cmd.tabId<0||typeof cmd.groupid!=='string'||!/^\d{1,32}$/.test(cmd.groupid)||typeof cmd.ticket!=='string'||!/^[-A-Za-z0-9]{16,128}$/.test(cmd.ticket))throw Error('download-reconcile-scope-invalid');
  if(typeof cmd.filename!=='string'||!/^门店评价_全部门店_\d{4}_\d{2}_\d{2}-\d{4}_\d{2}_\d{2}\.xlsx$/.test(cmd.filename))throw Error('download-reconcile-filename-invalid');
  const since=Date.parse(cmd.since),age=Date.now()-since;
  if(typeof cmd.since!=='string'||!Number.isFinite(since)||age<0||age>24*60*60*1000)throw Error('download-reconcile-time-invalid');
  const tab=await target(cmd.tabId),url=new URL(tab.url);
  if(url.pathname!=='/p/fulfillsettle/export_records/20101'||url.searchParams.getAll('groupid').length!==1||url.searchParams.get('groupid')!==cmd.groupid)throw Error('download-reconcile-record-context-invalid');
  const downloads=await chrome.downloads.search({startedAfter:new Date(since).toISOString()});
  const matches=downloads.filter(item=>{
    const name=item.filename?.split(/[\\/]/).pop();
    // Chrome may add a collision suffix; it is not silently accepted.
    if(name!==cmd.filename)return false;
    return [item.url,item.finalUrl,item.referrer].some(value=>{
      try{
        const source=new URL(String(value||'').replace(/^blob:/,''));
        return source.origin===P.origin || (source.protocol==='https:' && (source.hostname==='douyinstatic.com'||source.hostname.endsWith('.douyinstatic.com')));
      }catch{return false;}
    });
  });
  const after=await target(cmd.tabId);
  if(after.url!==tab.url||after.windowId!==tab.windowId)throw Error('download-reconcile-context-changed');
  if(matches.length>1)throw Error('download-reconcile-ambiguous-no-replay');
  if(!matches.length)return {state:'pending',ticket:cmd.ticket,reconciled:true,readonly:true};
  const item=matches[0];
  if(item.state==='interrupted')throw Error('download-reconcile-interrupted-no-replay');
  return {state:item.state,downloadId:item.id,path:item.filename,exists:item.exists,bytesReceived:item.bytesReceived,totalBytes:item.totalBytes,ticket:cmd.ticket,reconciled:true,readonly:true};
}
