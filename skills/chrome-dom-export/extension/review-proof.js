/* Independent normal-review evidence; external review_key is never a DOM ID. */
(()=>{
 const BUILD='review-complete-normal-list-v4';
 if(globalThis.__localReviewProof?.build===BUILD)return;
 let epoch=0;const watched=new Map(),ancestors=new Set();let binding=null;
 const rects=e=>JSON.stringify([...e.getClientRects()].map(r=>[r.left,r.top,r.right,r.bottom,r.width,r.height]));
 const sample=()=>{for(const [e,old] of watched){const value=rects(e);if(value!==old){watched.set(e,value);epoch++;}}};
 const frame=()=>{sample();globalThis.requestAnimationFrame(frame)};if(typeof requestAnimationFrame==='function')requestAnimationFrame(frame);
 // Only bound elements affect this proof; unrelated page mutations are not evidence drift.
 new MutationObserver(records=>{if(records.some(r=>ancestors.has(r.target)||[...watched.keys()].some(e=>e===r.target||e.contains(r.target))))epoch++;}).observe(document.documentElement,{subtree:true,attributes:true,childList:true,characterData:true});
 for(const event of ['scroll','resize','focus','blur'])globalThis.addEventListener(event,()=>epoch++,true);
 const norm=s=>String(s??'').replace(/\s+/g,' ').trim();
 function need(ok,code){if(!ok)throw Error(code)}
 const keys=(o,ks)=>need(o&&Object.keys(o).sort().join(',')===ks.sort().join(','),'review-proof-fields-invalid');
 const cls=(e,c)=>e.classList?e.classList.contains(c):String(e.getAttribute('class')||'').split(/\s+/).includes(c);
 function validate(c){
  keys(c,['op','tabId','windowId','groupid','source_sha256','dom_sha256','scope','reviews','channel']);
  need(c.op==='review-viewport-proof'&&/^\d{1,32}$/.test(c.groupid)&&/^[a-f0-9]{64}$/.test(c.source_sha256)&&/^[a-f0-9]{64}$/.test(c.dom_sha256),'review-proof-scope-invalid');
  const exclusive=c.scope?.scope_mode==='verified-complete-normal-list';keys(c.scope,['list','date','negative','count','other_filters','date_text','active_class','normal_count',...(exclusive?['scope_mode','complete_list']:['boundary'])]);if(exclusive){keys(c.scope.complete_list,['pager','total','current','previous','next']);need(c.scope.normal_count<=10,'review-proof-complete-list-count-invalid');}
  need(typeof c.scope.date_text==='string'&&/^\d{4}-\d\d-\d\d ~ \d{4}-\d\d-\d\d$/.test(c.scope.date_text)&&Number.isSafeInteger(c.scope.normal_count)&&c.scope.normal_count>0&&typeof c.scope.active_class==='string'&&c.scope.active_class,'review-proof-query-invalid');
  keys(c.scope.other_filters,['评价类型','评价来源','评价状态']);
  const selectors=[...['list','date','negative','count'].map(k=>c.scope[k]),...(exclusive?Object.values(c.scope.complete_list):[c.scope.boundary]),...Object.values(c.scope.other_filters)];
  need(Array.isArray(c.reviews)&&c.reviews.length>0&&c.reviews.length<=30,'review-proof-reviews-invalid');const seen=new Set();
  for(const r of c.reviews){keys(r,['review_key','card','store','customer','body','heart','store_text','customer_text','body_text',...(r.body_text_schema==='public-visible-text-v2'?['body_text_schema']:[])]);need(typeof r.review_key==='string'&&/^\d{1,32}:verified-tuple-sha256:[a-f0-9]{64}$/.test(r.review_key)&&r.review_key.startsWith(c.groupid+':')&&!seen.has(r.review_key),'review-proof-external-key-invalid');seen.add(r.review_key);selectors.push(...['card','store','customer','body','heart'].map(k=>r[k]));for(const k of ['store_text','customer_text','body_text'])need(typeof r[k]==='string'&&r[k].length<(k==='body_text'&&r.body_text_schema==='public-visible-text-v2'?16001:800)&&(k==='body_text'||r[k].length>0),'review-proof-text-invalid');}
  need(selectors.every(s=>typeof s==='string'&&s.length>0&&s.length<=2000),'review-proof-selector-invalid');
 }
 function reviewGeometry(el,view){
  const r=el.getBoundingClientRect();let rendered=r.width>0&&r.height>0,stable=true,clipped=false;
  // Intersect only public DOM boxes locally; no rectangle leaves the proof.
  let visibleLeft=Math.max(r.left,view.left),visibleTop=Math.max(r.top,view.top),visibleRight=Math.min(r.right,view.right),visibleBottom=Math.min(r.bottom,view.bottom);
  for(let p=el;p;p=p.parentElement){const st=getComputedStyle(p);
   if(st.display==='none'||st.visibility==='hidden'||st.visibility==='collapse'||st.contentVisibility==='hidden'||Number(st.opacity)===0)rendered=false;
   if(st.transform&&st.transform!=='none'||st.clip&&st.clip!=='auto'||st.clipPath&&st.clipPath!=='none'||st.maskImage&&st.maskImage!=='none'||st.webkitMaskImage&&st.webkitMaskImage!=='none'||st.filter&&st.filter!=='none'||st.zoom&&!['1','normal'].includes(String(st.zoom))||st.opacity!==undefined&&!['0','1'].includes(String(st.opacity)))stable=false;
   if(typeof p.getAnimations==='function'&&p.getAnimations().some(a=>a.playState==='running'||a.pending===true))stable=false;
   if(p!==el){const pr=p.getBoundingClientRect(),left=pr.left+(p.clientLeft||0),top=pr.top+(p.clientTop||0),right=left+p.clientWidth,bottom=top+p.clientHeight;
    if(['hidden','clip','auto','scroll'].includes(st.overflowX)){if(r.left<left||r.right>right)clipped=true;visibleLeft=Math.max(visibleLeft,left);visibleRight=Math.min(visibleRight,right);}
    if(['hidden','clip','auto','scroll'].includes(st.overflowY)){if(r.top<top||r.bottom>bottom)clipped=true;visibleTop=Math.max(visibleTop,top);visibleBottom=Math.min(visibleBottom,bottom);}}
  }
  const contained=!clipped&&r.left>=view.left&&r.top>=view.top&&r.right<=view.right&&r.bottom<=view.bottom;
  const unclipped=el.scrollHeight<=el.clientHeight+1&&el.scrollWidth<=el.clientWidth+1;
  return {rendered,visible_region:visibleRight>visibleLeft&&visibleBottom>visibleTop,viewport_contained:contained,text_unclipped:unclipped,unsupported_css_absent:stable,occlusion_verified:false,fully_visible:rendered&&contained&&unclipped&&stable};
 }
 async function proof(c,one,readTree){
  validate(c);const nextBinding=JSON.stringify({source:c.source_sha256,reviews:c.reviews.map(r=>[r.review_key,r.card]),scope:c.scope});if(binding!==nextBinding){watched.clear();ancestors.clear();binding=nextBinding;epoch++;}sample();const get=s=>one({by:'selector',value:s});
  const url=new URL(location.href);need(url.origin==='https://life.douyin.com'&&url.pathname==='/p/life_comment/management'&&url.searchParams.getAll('groupid').length===1&&url.searchParams.get('groupid')===c.groupid,'review-proof-current-scope-mismatch');
  need(document.visibilityState==='visible'&&document.hasFocus(),'review-proof-page-not-focused');
  const vv=globalThis.visualViewport;need(!vv||vv.scale===1&&vv.offsetLeft===0&&vv.offsetTop===0,'review-proof-zoom-unverified');
  const view={left:0,top:0,right:Math.min(document.documentElement.clientWidth,vv?.width??Infinity),bottom:Math.min(document.documentElement.clientHeight,vv?.height??Infinity)};
  const s=c.scope,list=get(s.list),date=get(s.date),negative=get(s.negative),count=get(s.count),children=Array.from(list.children);let normal,sectionWatch;
  need(cls(list,'commentList-hkujq4'),'review-proof-normal-list-unverified');
  if(s.scope_mode==='verified-complete-normal-list'){
    const exactClass=(e,c)=>e?.getAttribute('class')===c,exactSet=(e,cs)=>{const actual=String(e?.getAttribute('class')||'').split(/\s+/).filter(Boolean);return new Set(actual).size===cs.length&&cs.every(c=>actual.includes(c));};
    const p=s.complete_list,pager=get(p.pager),total=get(p.total),current=get(p.current),previous=get(p.previous),next=get(p.next),header=children[0];normal=children.slice(1,-1);
    need(children.length===s.normal_count+2&&exactSet(header,['header-sQid1u','commentListHeader-jKdTh_'])&&header.contains(count)&&normal.every(e=>exactClass(e,'commentItem-jrXo5p'))&&normal.length===s.normal_count&&children.at(-1)===pager&&exactClass(pager,'pagination-GXvAPk')&&list.querySelectorAll('.foldTitleContainer-DwIByI').length===0,'review-proof-complete-list-shape-invalid');
    const pc=Array.from(pager.children),group=pc[1],gc=Array.from(group?.children||[]);
    need(pc.length===2&&pc[0]===total&&exactClass(total,'text-bjyZFG')&&norm(total.innerText)==='共'+s.normal_count+'条记录'&&exactClass(group,'buttonGroup-GDbp9Y')&&gc.length===3&&gc[0]===previous&&gc[1]===current&&gc[2]===next&&norm(current.innerText)==='1/1'&&exactClass(current,'text-bjyZFG')&&[previous,next].every(e=>exactSet(e,['button-j4VxiA','isDisabled-unTBS6'])&&!norm(e.innerText)),'review-proof-complete-pagination-invalid');sectionWatch=[list,header,pager,total,current,previous,next];
  }else{
    const boundary=get(s.boundary);need(cls(boundary,'foldTitleContainer-DwIByI')&&boundary.parentElement===list,'review-proof-normal-boundary-unverified');const cutoff=children.indexOf(boundary);normal=children.slice(0,cutoff).filter(e=>cls(e,'commentItem-jrXo5p'));need(cutoff>=0,'review-proof-normal-count-mismatch');sectionWatch=[boundary];
  }
  need(normal.length===s.normal_count&&norm(count.innerText)==='已筛选'+s.normal_count+'条','review-proof-normal-count-mismatch');
  need(norm(date.value)===s.date_text&&norm(negative.innerText)==='中差评（1-3心）'&&cls(negative,s.active_class),'review-proof-query-changed');
  for(const selector of Object.values(s.other_filters))need(norm(get(selector).value)==='全部','review-proof-other-filter-changed');
  const selected=[];const geometry=reviewGeometry;
  const cards=new Set();
  for(const r of c.reviews){const card=get(r.card);need(normal.includes(card)&&!cards.has(card),'review-proof-folded-or-duplicate-card');cards.add(card);const fields={};
   for(const [field,klass] of [['store','poiName-W9HDFV'],['customer','nickName-wB7fZf'],['body','text-Hl9jZe'],['heart','score-R2K3dS']]){const el=get(r[field]);need(card.contains(el)&&cls(el,klass),'review-proof-field-outside-card');need(card.querySelectorAll('.'+klass).length===1,'review-proof-field-not-unique');if(field!=='heart'){need(field==='body'&&r.body_text_schema==='public-visible-text-v2'?String(el.innerText).normalize('NFC').replace(/\r\n?/g,'\n').trim()===r.body_text:norm(el.innerText)===norm(r[field+'_text']),'review-proof-field-text-changed:'+field);need(card.querySelectorAll('.'+klass).length===1,'review-proof-field-not-unique');}fields[field]=el;}
   for(const el of [card,...Object.values(fields),date,negative,...sectionWatch]){if(!watched.has(el)){need(watched.size<3000,'review-proof-layout-watch-limit');watched.set(el,rects(el));}for(let p=el.parentElement;p;p=p.parentElement)ancestors.add(p);}
   const detail={};for(const [name,el] of Object.entries(fields))detail[name]=geometry(el,view);
   const cardGeometry=geometry(card,view),core=g=>g.rendered&&g.viewport_contained&&g.unsupported_css_absent;
   const eligible=core(cardGeometry)&&detail.body.rendered&&detail.body.visible_region&&detail.body.unsupported_css_absent&&['store','customer','heart'].every(k=>detail[k].fully_visible);
   selected.push({review_key:r.review_key,card:r.card,store:r.store_text,customer:r.customer_text,body:r.body_text,heart_region_visible:detail.heart.fully_visible,normal_section:true,text_complete_in_image:detail.body.fully_visible,card_visible:eligible,geometry:{card:cardGeometry,...detail}});
  }
  const query={date:s.date_text,negative_filter:'中差评（1-3心）',normal_count:s.normal_count,...(s.scope_mode==='verified-complete-normal-list'?{scope_mode:s.scope_mode,normal_list_complete:true,pagination:{total:s.normal_count,current:'1/1',previous_disabled:true,next_disabled:true}}:{fold_boundary:s.boundary}),other_filters:{'评价类型':'全部','评价来源':'全部','评价状态':'全部'}};
  const beforeEpoch=epoch;const bytes=new TextEncoder().encode(JSON.stringify({query,reviews:selected}));const semanticHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');sample();need(epoch===beforeEpoch,'review-proof-layout-or-dom-changed');
  return {source:'local-dom-bridge',method:'public-DOM-normal-review-viewport-proof',source_sha256:c.source_sha256,reference_dom_sha256:c.dom_sha256,semantic_sha256:semanticHash,epoch,url:location.href,scope:{tabId:c.tabId,windowId:c.windowId,groupid:c.groupid},query,reviews:selected,occlusion_verified:false,visibility_method:'public-DOM-rendering-and-viewport-only',viewport_only:true,pixel_coordinates_returned:false,pixel_actions_used:false,all_cards_visible:selected.every(r=>r.card_visible)};
 }
 globalThis.__localReviewProof={build:BUILD,validate,proof};
})();
