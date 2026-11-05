/* Pure local-dom-bridge JSON intake. No browser calls, evaluate, React or APIs.
 * A mocked profile is not live acceptance. No field is inferred from missing DOM.
 */
export const BACKEND='local-dom-bridge';
export function intakeViolationTrees(observation,job,profile){
  const stop=code=>{throw Error(code);};
  try{
    if(profile?.status!=='live-validated'||!profile.revision)stop('profile-awaiting-live-validation');
    if(observation?.source!==BACKEND)stop('backend-source-mismatch');
    if(job.account_verified!==true||!job.identity||['provider','account_id','manager'].some(k=>!job.identity[k]))stop('account-unverified');
    if(!/^\d{4}-\d{2}-\d{2}$/.test(job.start)||!/^\d{4}-\d{2}-\d{2}$/.test(job.end_exclusive)||!(job.start<job.end_exclusive))stop('job-date-range-invalid');
    const end=new Date(Date.parse(job.end_exclusive+'T00:00:00Z')-86400000).toISOString().slice(0,10);
    const matches=(n,ref)=>{
      if(typeof ref==='string'&&ref)return n.selector===ref;
      if(!ref||typeof ref!=='object'||Array.isArray(ref)||!Object.keys(ref).length||Object.keys(ref).some(k=>!['selector','role','name','attributes'].includes(k)))stop('profile-matcher-missing-or-invalid');
      return (!ref.selector||n.selector===ref.selector)&&(!ref.role||n.role===ref.role)&&(ref.name===undefined||n.name===ref.name)&&Object.entries(ref.attributes||{}).every(([k,v])=>n.attributes?.[k]===v);
    };
    function view(o){
      if(o?.source!==BACKEND)stop('page-source-mismatch');
      if(!o.tab||String(o.tab.id)!==String(o.tab_id))stop('tab-binding-missing');
      let url;try{url=new URL(o.tab.url);}catch{stop('tab-url-invalid');}
      if(url.origin!=='https://life.douyin.com'||url.searchParams.get('groupid')!==String(job.groupid))stop('company-origin-mismatch');
      const t=o.tree;if(!t?.root||t.kind!=='DOM-derived semantic tree (not native AX)'||t.truncated!==false)stop('tree-incomplete');
      if(t.url!==url.origin+url.pathname)stop('tree-tab-path-mismatch');
      if(!o.observed_at||!/(Z|[+-]\d\d:\d\d)$/.test(o.observed_at)||!Number.isFinite(Date.parse(o.observed_at)))stop('observation-timezone-required');
      const nodes=[];function walk(n,depth=0){if(!n||typeof n!=='object'||depth>200||nodes.length>=10000)stop('tree-invalid-or-too-large');nodes.push(n);for(const c of n.children||[])walk(c,depth+1);}walk(t.root);
      const find=(ref,scope=nodes)=>{const found=scope.filter(n=>matches(n,ref));if(found.length!==1)stop('selector-not-unique');return found[0];};
      const text=n=>{if((n.children||[]).length)stop('aggregate-text-requires-leaf-selector');const value=String(n.attributes?.value??n.name??'').trim();if(value.length>=800||n.truncated===true)stop('node-text-may-be-truncated');return value;};
      const val=(ref,scope)=>text(find(ref,scope));
      const descendants=n=>{const out=[];function visit(x){out.push(x);for(const c of x.children||[])visit(c);}visit(n);return out;};
      for(const k of ['provider','account_id','manager'])if(val(profile.identity?.[k])!==job.identity[k])stop('identity-tree-mismatch:'+k);
      return {o,url,nodes,find,text,val,descendants};
    }
    const integer=(s,label)=>{const m=String(s).match(/^(?:(?:总违规|全部|共|违规总数)\s*)?(\d+)(?:\s*条)?$/);if(!m)stop(label+'-not-explicit');return Number(m[1]);};
    const selected=n=>n.attributes?.['aria-selected']==='true'||n.attributes?.['aria-pressed']==='true'||n.attributes?.['aria-checked']==='true';
    const array=(s,label)=>{const a=s.split(/[、；;\n]+/).map(x=>x.trim()).filter(Boolean);if(!a.length||a.some(x=>/…|\.\.\./.test(x)))stop(label+'-missing-or-truncated');return a;};
    function pages(name){
      const input=observation[name];if(!Array.isArray(input)||!input.length)stop(name+'-pages-missing');
      const p=profile[name];if(!p)stop(name+'-profile-missing');
      let total=null;const rows=[],seen=new Set(),stamps=[];
      input.forEach((o,i)=>{
        const v=view(o);stamps.push(o.observed_at);
        if(v.val(p.dateInput).replaceAll('/','-')!==job.start+' ~ '+end)stop(name+'-date-filter-mismatch');
        const scope=v.find(p.scope);if(v.text(scope)!=='全部'||!selected(scope))stop(name+'-all-scope-unverified');
        if(!p.otherFilters||!Object.keys(p.otherFilters).length)stop(name+'-other-filters-profile-missing');
        for(const filter of Object.values(p.otherFilters))if(v.val(filter.locator)!==filter.expected)stop(name+'-unexpected-filter');
        if(name==='records'){
          const unread=v.find(p.unreadOnly);if(unread.attributes?.['aria-checked']!=='false')stop('records-unread-filter-unverified');
        }else{
          const all=v.find(p.allReasons);if(v.text(all)!=='全部'||!selected(all))stop('analysis-all-reasons-unverified');
        }
        const n=integer(v.val(p.total),name+'-total');if(total!==null&&n!==total)stop(name+'-total-changed');total=n;
        if(integer(v.val(p.currentPage),name+'-page')!==i+1)stop(name+'-page-order-invalid');
        const next=v.find(p.next);if(typeof next.disabled!=='boolean'&&next.attributes?.['aria-disabled']===undefined)stop(name+'-next-state-unverified');
        const disabled=next.disabled===true||next.attributes?.['aria-disabled']==='true';
        if(disabled!==(i===input.length-1))stop(name+'-pagination-incomplete');
        const container=v.find(p.root);const rs=v.descendants(container).filter(n=>matches(n,p.row));
        for(const row of rs){
          const sub=v.descendants(row);let r,key;
          if(name==='analysis'){
            r={violation_type:v.val(p.violationType,sub),object_types:array(v.val(p.objectTypes,sub),'analysis-object-types'),count:integer(v.val(p.count,sub),'analysis-count')};
            if(!r.violation_type||/…|\.\.\./.test(r.violation_type)||r.count<=0)stop('analysis-row-incomplete');key=r.violation_type+'|'+[...r.object_types].sort().join('|');
          }else{
            const id=row.attributes?.[p.idAttribute];if(!id)stop('notice-stable-id-missing');
            r={notice_id:String(id),subject:v.val(p.subject,sub)};if(!r.subject||/…|\.\.\./.test(r.subject))stop('record-subject-truncated');key=r.notice_id;
          }
          if(seen.has(key))stop(name+'-duplicate-row');seen.add(key);rows.push(r);
        }
        if(!rs.length&&total!==0)stop(name+'-empty-page-with-positive-total');
      });
      if(name==='analysis'&&rows.reduce((sum,r)=>sum+r.count,0)!==total)stop('analysis-total-mismatch');
      if(name==='records'&&rows.length!==total)stop('records-total-mismatch');
      return {rows,total,stamps,start:job.start,end_exclusive:job.end_exclusive,scope:'全部',all_pages_read:true,filters_verified:true,...(name==='analysis'?{all_reasons_read:true}:{unread_only:false})};
    }
    const analysis=pages('analysis'),records=pages('records');
    if(analysis.total!==records.total)stop('analysis-record-count-needs-reconciliation');
    const details=observation.details;if(!Array.isArray(details)||details.length!==records.total)stop('record-details-incomplete');
    const seenDetails=new Set(),stamps=[...analysis.stamps,...records.stamps];
    for(const o of details){
      const v=view(o),p=profile.detail;if(!p)stop('detail-profile-missing');stamps.push(o.observed_at);
      const id=v.val(p.noticeId).replace(/^ID[:：]\s*/,'');if(seenDetails.has(id))stop('duplicate-detail-id');seenDetails.add(id);
      const row=records.rows.find(r=>r.notice_id===id);if(!row)stop('detail-notice-not-in-records');
      if(v.val(p.subject)!==row.subject)stop('detail-subject-mismatch');
      const raw=v.find(p.date),date=String(raw.attributes?.datetime??v.text(raw)).slice(0,10);
      if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(Date.parse(date+'T00:00:00Z'))||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date)stop('detail-absolute-date-missing');
      if(!(job.start<=date&&date<job.end_exclusive))stop('detail-date-outside-filter');
      const full={};for(const k of ['reason','object_type','object_name','effectiveness_status','rectification_status','public_recommendation']){
        full[k]=v.val(p[k]);if(!full[k]||/…|\.\.\./.test(full[k]))stop('detail-field-missing-or-truncated:'+k);
      }
      Object.assign(row,full,{date,actions:array(v.val(p.actions),'detail-actions'),detail_read:true});
    }
    // All page evidence belongs to the same Shanghai observation day. Caller keeps
    // original tree documents/hashes; success does not attest their acquisition.
    const shanghaiDay=s=>new Date(Date.parse(s)+8*3600000).toISOString().slice(0,10);
    if(new Set(stamps.map(shanghaiDay)).size!==1)stop('observation-days-inconsistent');
    delete analysis.stamps;delete records.stamps;
    return {ok:true,backend:BACKEND,live_accepted:false,capture:{company:job.company,groupid:String(job.groupid),url:observation.records[0].tab.url,source:BACKEND,observed_at:stamps.sort((a,b)=>Date.parse(a)-Date.parse(b)).at(-1),account_verified:true,identity:job.identity,start:job.start,end_exclusive:job.end_exclusive,analysis,records,profile_revision:profile.revision}};
  }catch(error){return {ok:false,backend:BACKEND,live_accepted:false,gaps:[String(error.message)]};}
}
