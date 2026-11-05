/* Pure data intake for installed local DOM bridge. No browser, evaluate, network,
 * credentials or arbitrary action execution. Tree selectors are opaque exact keys.
 * Success verifies a scoped observation, never attests live UI acceptance.
 */
export const BACKEND='local-dom-bridge';
export function intakeReviewTree(observation,job,profile){
  const gaps=[];
  const stop=code=>{throw Error(code);};
  try{
    if(profile?.status!=='live-validated'||!profile.revision)stop('profile-awaiting-live-validation');
    for(const key of ['root','row','filteredCount','idAttribute','store','customer','text','date','stars','action','activeNegative','dateInput'])
      if(!profile[key])stop('profile-field-missing:'+key);
    if(!profile.foldBoundary&&profile.normalRootIsExclusive!==true)stop('normal-section-boundary-unverified');
    const {tree,tab,observed_at}=observation??{};
    if(observation?.source!==BACKEND)stop('backend-source-mismatch');
    if(!tab?.url||String(tab.id)!==String(observation.tab_id))stop('tab-observation-binding-missing');
    let url;try{url=new URL(tab.url);}catch{stop('tab-url-invalid');}
    if(url.origin!=='https://life.douyin.com'||url.searchParams.get('groupid')!==String(job.groupid))stop('company-origin-mismatch');
    if(!tree?.root||tree.kind!=='DOM-derived semantic tree (not native AX)'||tree.truncated!==false)stop('tree-incomplete-or-unrecognized');
    if(tree.url!==url.origin+url.pathname)stop('tree-tab-path-mismatch');
    if(!observed_at||!/(Z|[+-]\d\d:\d\d)$/.test(observed_at)||!Number.isFinite(Date.parse(observed_at)))stop('observation-timezone-required');
    if(job.account_verified!==true||!job.identity||['provider','account_id','manager'].some(k=>!job.identity[k]))stop('account-unverified');
    // Index metadata only. Never consume aggregate container names; they can contain
    // descendants from folded section. Folded subtree is discarded before descent.
    const matches=(n,ref)=>{
      if(typeof ref==='string')return n.selector===ref;
      if(!ref||typeof ref!=='object'||Array.isArray(ref)||!Object.keys(ref).length||Object.keys(ref).some(k=>!['selector','role','name','attributes'].includes(k)))stop('profile-matcher-invalid');
      return (!ref.selector||n.selector===ref.selector)&&(!ref.role||n.role===ref.role)&&(ref.name===undefined||n.name===ref.name)&&Object.entries(ref.attributes||{}).every(([k,v])=>n.attributes?.[k]===v);
    };
    const nodes=[];let boundary=null;
    function walk(n){
      if(!n||typeof n!=='object')stop('tree-node-invalid');
      if(profile.foldBoundary&&matches(n,profile.foldBoundary)){if(boundary)stop('fold-boundary-ambiguous');boundary=n;nodes.push(n);return;}
      nodes.push(n);for(const c of n.children||[])walk(c);
    }
    walk(tree.root);
    const select=(list,key)=>{const found=list.filter(n=>matches(n,key));if(found.length!==1)stop('selector-not-unique:'+key);return found[0];};
    const descendants=n=>{const out=[];function visit(x){if(x===boundary)return;out.push(x);for(const c of x.children||[])visit(c);}visit(n);return out;};
    const attrs=n=>n.attributes??{};
    const text=n=>{if((n.children||[]).length)stop('aggregate-text-requires-leaf-selector:'+n.selector);const value=String(attrs(n).value??n.name??'').trim();if(value.length>=800||n.truncated===true)stop('node-text-may-be-truncated');return value;};
    const value=(scope,key)=>text(select(scope,key));
    const root=select(nodes,profile.root),rootNodes=descendants(root);
    if(!boundary&&profile.normalRootIsExclusive!==true)stop('fold-boundary-unverified');
    const active=select(nodes,profile.activeNegative),a=attrs(active);
    if(!['true'].includes(a['aria-pressed'])&&!['true'].includes(a['aria-selected'])&&!(profile.activeClass&&String(a.class||'').split(/\s+/).includes(profile.activeClass)))stop('negative-filter-not-active');
    if(text(active)!=='中差评（1-3心）')stop('negative-filter-label-mismatch');
    const range=value(nodes,profile.dateInput).replaceAll('/','-');
    if(range!==job.start+' ~ '+job.end)stop('date-filter-mismatch');
    const count=value(nodes,profile.filteredCount).match(/^评价\s*已筛选\s*(\d+)\s*条$|^已筛选\s*(\d+)\s*条$/);
    if(!count)stop('filtered-count-unverified');
    const total=Number(count[1]??count[2]);
    const other_filters={};
    for(const name of ['评价类型','评价来源','评价状态']){
      if(!profile.otherFilters?.[name])stop('other-filter-profile-missing:'+name);
      if(value(nodes,profile.otherFilters[name])!=='全部')stop('other-filter-not-default');other_filters[name]='全部';
    }
    const rows=[];
    for(const r of rootNodes.filter(n=>matches(n,profile.row))){
      if(boundary&&nodes.indexOf(r)>nodes.indexOf(boundary))continue;
      const scope=descendants(r),id=attrs(r)[profile.idAttribute];if(!id)stop('stable-review-id-missing');
      const dn=select(scope,profile.date),sn=select(scope,profile.stars);
      const date=String(attrs(dn).datetime??text(dn)).slice(0,10);
      if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(Date.parse(date+'T00:00:00Z'))||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date)stop('absolute-review-date-missing');
      if(date<job.start||date>=job.end_exclusive)stop('row-date-outside-filter');
      const rating=attrs(sn)['data-rating']??attrs(sn)['aria-label']??text(sn);
      const match=String(rating).match(/^([1-3])(?:\s*(?:星|心|分))?$/);if(!match)stop('explicit-negative-stars-missing');
      const action=value(scope,profile.action);if(!['投诉','查看投诉结果'].includes(action))stop('unknown-complaint-action');
      const store=value(scope,profile.store),customer=value(scope,profile.customer);if(!store||!customer)stop('review-fields-missing');
      rows.push({review_id:String(id),section:'filtered',store,customer,date,stars:Number(match[1]),text:value(scope,profile.text),product:profile.product?value(scope,profile.product):'',action});
    }
    if(new Set(rows.map(r=>r.review_id)).size!==rows.length)stop('duplicate-review-id');
    if(rows.length!==total)stop('pagination-incomplete');
    return {ok:true,backend:BACKEND,live_accepted:false,capture:{account_verified:true,identity:job.identity,source:BACKEND,company:job.company,groupid:String(job.groupid),url:url.href,
      start:job.start,end_exclusive:job.end_exclusive,observed_at,negative_filter:'中差评（1-3心）',filter_active:true,other_filters,
      fold_boundary_verified:true,all_pages_read:true,filtered_count:total,rows,profile_revision:profile.revision}};
  }catch(error){gaps.push(String(error.message));return {ok:false,backend:BACKEND,live_accepted:false,submission_enabled:false,gaps};}
}
