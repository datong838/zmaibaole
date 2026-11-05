/* Existing Codex host tab ONLY. No launch/connect/debug/cookies/network APIs.
 * Reviewed DOM selectors are a versioned site profile, not model-chosen steps.
 * This adapter deliberately has no submit, fill, or arbitrary click operation.
 */
export function validateProfile(p){
  if(p?.status!=='live-validated'||!p.revision)throw Error('profile-awaiting-live-validation');
  for(const key of ['root','row','filteredCount','idAttribute','store','customer','text','date','stars','action','activeNegative','dateInput'])
    if(typeof p[key]!=='string'||!p[key])throw Error('profile-field-missing:'+key);
  if(!p.foldBoundary&&p.normalRootIsExclusive!==true)throw Error('normal-section-boundary-unverified');
  return p;
}
export async function inspectReviews(tab,job,profile){
  validateProfile(profile);
  if(job.account_verified!==true||!job.identity||['provider','account_id','manager'].some(k=>!job.identity[k]))throw Error('account-unverified');
  const u=new URL(await tab.url());
  if(u.origin!=='https://life.douyin.com'||u.searchParams.get('groupid')!==String(job.groupid))throw Error('company-origin-mismatch');
  return tab.playwright.evaluate(({p,job,url})=>{
    const visible=e=>e&&!!e.getClientRects().length;
    const unique=(scope,sel)=>{const es=[...scope.querySelectorAll(sel)].filter(visible);if(es.length!==1)throw Error('DOM-selector-not-unique:'+sel);return es[0];};
    const value=(scope,sel)=>{const e=unique(scope,sel);return (e.value??e.innerText??'').trim();};
    const dialogs=[...document.querySelectorAll('[role=dialog]')].filter(visible);
    if(dialogs.some(e=>/安全验证|滑块验证|扫码登录|账号异常|风险验证|请完成验证/.test(e.innerText)))throw Error('connection-risk-stop');
    const root=unique(document,p.root),filter=unique(document,p.activeNegative),range=value(document,p.dateInput);
    if(filter.getAttribute('aria-pressed')!=='true'&&filter.getAttribute('aria-selected')!=='true'&&!(p.activeClass&&filter.classList.contains(p.activeClass)))throw Error('negative-filter-not-active');
    if(range!==job.start+' ~ '+job.end)throw Error('date-filter-mismatch');
    const text=value(document,p.filteredCount);
    const counts=[...text.matchAll(/已筛选\s*(\d+)\s*条/g)].map(x=>Number(x[1]));
    if(counts.length!==1)throw Error('filtered-count-ambiguous');
    const boundaryNodes=p.foldBoundary?[...document.querySelectorAll(p.foldBoundary)].filter(visible):[];
    if(boundaryNodes.length!==1&&p.normalRootIsExclusive!==true)throw Error('fold-boundary-not-unique');
    if(boundaryNodes.length>1)throw Error('fold-boundary-ambiguous');
    const boundary=boundaryNodes[0]||null;
    const rows=[...root.querySelectorAll(p.row)].filter(visible).map(row=>{
      if(boundary&&row.contains(boundary))throw Error('review-container-crosses-fold-boundary');
      // DOM order, never screenshot coordinates. Excluded folded rows are not read.
      if(boundary&&!(row.compareDocumentPosition(boundary)&Node.DOCUMENT_POSITION_FOLLOWING))return null;
      const id=row.getAttribute(p.idAttribute);if(!id)throw Error('stable-review-id-missing');
      const rawDate=value(row,p.date),stars=Number(value(row,p.stars));
      if(!/^\d{4}-\d{2}-\d{2}$/.test(rawDate)||![1,2,3].includes(stars))throw Error('date-or-rating-not-explicit');
      return {review_id:id,section:'filtered',store:value(row,p.store),customer:value(row,p.customer),
        text:value(row,p.text),date:rawDate,stars,action:value(row,p.action),product:p.product?value(row,p.product):''};
    }).filter(Boolean);
    // Until paginated traversal is observed, never claim the whole list was read.
    if(rows.length!==counts[0])throw Error('pagination-requires-live-adapter');
    const otherFilters={};
    for(const name of ['评价类型','评价来源','评价状态']){
      const input=[...document.querySelectorAll('input')].filter(e=>visible(e)&&e.getAttribute('aria-label')===name);
      if(input.length!==1||input[0].value!=='全部')throw Error('other-filter-not-default');otherFilters[name]='全部';
    }
    return {account_verified:true,identity:job.identity,source:'codex-existing-extension',company:job.company,groupid:String(job.groupid),url,
      start:job.start,end_exclusive:job.end_exclusive,negative_filter:'中差评（1-3心）',filter_active:true,
      fold_boundary_verified:true,all_pages_read:true,filtered_count:counts[0],other_filters:otherFilters,
      rows,observed_at:new Date().toISOString(),profile_revision:p.revision};
  },{p:profile,job,url:u.href});
}
export async function openComplaint(tab,job,profile,reviewId){
  const capture=await inspectReviews(tab,job,profile);
  const row=capture.rows.filter(r=>r.review_id===reviewId);
  if(row.length!==1)throw Error('review-not-in-current-filter');
  const label=row[0].action;
  if(!['投诉','查看投诉结果'].includes(label))throw Error('unreviewed-action');
  // CSS attribute escaping only; ID is from the immediately preceding live DOM.
  const escaped=String(reviewId).replace(/[\\"\n\r]/g,c=>'\\'+c.codePointAt(0).toString(16)+' ');
  const target=tab.playwright.locator(profile.row+'['+profile.idAttribute+'="'+escaped+'"]')
    .getByText(label,{exact:true});
  if(await target.count()!==1||!await target.isVisible())throw Error('complaint-action-not-unique');
  await target.click({timeoutMs:5000});
  return {review_id:reviewId,opened:label,submission_enabled:false};
}
export async function readDialog(tab){
  const dialog=tab.playwright.getByRole('dialog');
  if(await dialog.count()!==1||!await dialog.isVisible())throw Error('dialog-not-unique');
  return {text:await dialog.innerText(),submission_enabled:false};
}
