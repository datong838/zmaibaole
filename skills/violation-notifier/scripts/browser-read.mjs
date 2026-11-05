// Installed bridge route is pure intake; existing host reader remains separate.
export {intakeViolationTrees} from './semantic-intake.mjs';
/* Codex existing extension tab; public DOM APIs only. No debugging connection.
 * Profile remains unaccepted until actual DOM/pagination/detail calibration.
 */
export function validateProfile(profile){
  if(profile?.status!=='live-validated'||!profile.revision)throw Error('live-profile-not-accepted');
  for(const name of ['row','noticeId','subject','reason','objectType','objectName','actions','effectiveness','rectification','date','next','total','dateInput'])
    if(!profile[name])throw Error('profile-missing:'+name);
  return profile;
}
export function createReader(tab,job,profile){
  validateProfile(profile);
  if(job.account_verified!==true||!job.identity||['provider','account_id','manager'].some(k=>!job.identity[k]))throw Error('account-unverified');
  let verified=false;
  return {
    // Each operation is awaited in its own active host invocation; no background calls.
    async context(){
      const u=new URL(await tab.url());
      if(u.origin!=='https://life.douyin.com'||u.searchParams.get('groupid')!==String(job.groupid))throw Error('company-origin-mismatch');
      verified=true;return {url:u.href,groupid:String(job.groupid)};
    },
    async snapshot(){
      if(!verified)throw Error('context-required');
      const snapshot=await tab.playwright.domSnapshot();
      if(/安全验证|滑块验证|扫码登录|账号异常|风险验证|请完成验证/.test(snapshot))throw Error('risk-stop');
      return snapshot;
    },
    async openCenter(){
      if(!verified)throw Error('context-required');
      const target=tab.playwright.getByText('违规中心',{exact:true});
      if(await target.count()!==1)throw Error('center-not-unique');await target.click({timeoutMs:5000});
    },
    async openRecords(){
      if(!verified)throw Error('context-required');
      const target=tab.playwright.getByText('违规记录',{exact:true});
      if(await target.count()!==1)throw Error('records-not-unique');await target.click({timeoutMs:5000});
    },
    async openDetail(noticeId){
      if(!verified)throw Error('context-required');
      const row=tab.playwright.locator(profile.row).filter({has:tab.playwright.getByText(noticeId,{exact:true})});
      const target=row.getByText('查看详情',{exact:true});
      if(await target.count()!==1)throw Error('notice-detail-not-unique');await target.click({timeoutMs:5000});
    },
    async readRecordPage(){
      if(!verified)throw Error('context-required');
      return tab.playwright.evaluate(({p,job})=>{
        const visible=e=>e&&!!e.getClientRects().length;
        const unique=(scope,s)=>{const es=[...scope.querySelectorAll(s)].filter(visible);if(es.length!==1)throw Error('DOM-not-unique:'+s);return es[0];};
        const text=(scope,s)=>{const el=unique(scope,s);return (el.value??el.innerText??'').trim();};
        if(/安全验证|扫码登录|风险验证/.test(document.body.innerText))throw Error('risk-stop');
        const date=text(document,p.dateInput);
        if(date!==job.start.replaceAll('-','/')+' ~ '+job.end.replaceAll('-','/'))throw Error('date-filter-mismatch');
        const totalText=text(document,p.total);const found=totalText.match(/^(?:全部|共)\s*(\d+)(?:条)?$/);
        if(!found)throw Error('record-total-unverified');
        const rows=[...document.querySelectorAll(p.row)].filter(visible).map(row=>({
          notice_id:text(row,p.noticeId).replace(/^ID[:：]\s*/,''),subject:text(row,p.subject),reason:text(row,p.reason),
          object_type:text(row,p.objectType),object_name:text(row,p.objectName),actions:[text(row,p.actions)],
          effectiveness_status:text(row,p.effectiveness),rectification_status:text(row,p.rectification),date:text(row,p.date)
        }));
        const next=[...document.querySelectorAll(p.next)].filter(visible);
        if(next.length>1)throw Error('pagination-ambiguous');
        return {rows,total:Number(found[1]),has_next:next.length===1&&!next[0].disabled&&next[0].getAttribute('aria-disabled')!=='true',
          all_pages_read:false,profile_revision:p.revision};
      },{p:profile,job});
    }
  };
}
// Analysis/all reasons, cross-page traversal, public advice extraction and actual
// screenshot saving require live calibration. No unknown selectors or mutation fallback.
