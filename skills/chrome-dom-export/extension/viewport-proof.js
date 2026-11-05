/* Read-only semantic coverage proof. Bounded overlay candidates contain no coordinates or text. */
(()=>{
  const BUILD='viewport-notice-business-cells-v13-fractional-auto-padding-v1',INSTALL='reviewed-v12-to-v13-once-v1';
  const priorViewportProof=globalThis.__localViewportProof;
  if(priorViewportProof?.build===BUILD){if(priorViewportProof.installation_contract!==INSTALL)throw Error('viewport-proof-installation-marker-mismatch');return;}
  if(priorViewportProof&&(priorViewportProof.build!=='viewport-notice-business-cells-v12-rectification-projection-v3'||priorViewportProof.installation_contract!==undefined))throw Error('viewport-proof-unreviewed-resident-generation');
  let epoch=0;
  const watched=new Map();let watchBinding=null;
  const rectKey=el=>JSON.stringify([...el.getClientRects()].map(r=>[r.left,r.top,r.right,r.bottom,r.width,r.height]));
  const sample=()=>{for(const [el,old] of watched){const value=rectKey(el);if(value!==old){watched.set(el,value);epoch++;}}if(typeof stableWatched!=='undefined')for(const [el,old] of stableWatched){const value=rectKey(el);if(value!==old){stableWatched.set(el,value);stableEpoch++;}}};
  const monitor=()=>{sample();globalThis.requestAnimationFrame(monitor)};
  if(typeof globalThis.requestAnimationFrame==='function')globalThis.requestAnimationFrame(monitor);
  let stableEpoch=0,stableTimerNodes=new Set(),stableRectificationNodes=new Set(),stableBinding=null;
  const stableWatched=new Map();
  function timerOnly(record){
    const target=record.target,owner=target?.nodeType===3?target.parentElement:target;
    const pattern=stableRectificationNodes.has(owner)?rectificationTimerPattern:timerPattern;
    if(!stableTimerNodes.has(owner)||!pattern.test(String(owner.innerText||'')))return false;
    if(record.type==='characterData')return pattern.test(String(record.oldValue||''))&&pattern.test(String(target.nodeValue||''));
    if(record.type==='childList')return [...record.addedNodes,...record.removedNodes].every(n=>n.nodeType===3&&pattern.test(String(n.nodeValue||'')));
    return false;
  }
  const change=records=>{epoch++;if(!records||!records.length||!Array.isArray(records)||records.some(r=>!timerOnly(r)))stableEpoch++};
  new MutationObserver(change).observe(document.documentElement,{subtree:true,attributes:true,childList:true,characterData:true,characterDataOldValue:true});
  globalThis.addEventListener('scroll',change,true);globalThis.addEventListener('resize',change,true);globalThis.addEventListener('focus',change,true);globalThis.addEventListener('blur',change,true);
  function need(ok,code){if(!ok)throw Error(code)}
  function keys(o,expected){need(o&&Object.keys(o).sort().join(',')===expected.sort().join(','),'viewport-proof-fields-invalid')}
  function validate(cmd){
    keys(cmd,['op','tabId','windowId','groupid','source_sha256','dom_sha256','elements','channel']);
    need(cmd.op==='viewport-proof'&&/^\d{1,32}$/.test(cmd.groupid)&&/^[a-f0-9]{64}$/.test(cmd.source_sha256)&&/^[a-f0-9]{64}$/.test(cmd.dom_sha256),'viewport-proof-scope-invalid');
    need(Array.isArray(cmd.elements)&&cmd.elements.length>0&&cmd.elements.length<=100,'viewport-proof-elements-invalid');
    const seen=new Set();
    for(const e of cmd.elements){
      keys(e,['key','kind','locator','expected_text','notice_id']);
      need(typeof e.key==='string'&&/^[A-Za-z0-9_.:-]{1,100}$/.test(e.key)&&!seen.has(e.key),'viewport-proof-key-invalid');seen.add(e.key);
      need(['date-filter','header','row'].includes(e.kind)&&typeof e.expected_text==='string'&&e.expected_text.length>0&&e.expected_text.length<800,'viewport-proof-expected-text-invalid');
      need(e.kind==='row'?typeof e.notice_id==='string'&&e.notice_id.length>0&&e.expected_text.includes(e.notice_id):e.notice_id===null,'viewport-proof-notice-id-invalid');
      const q=e.locator;need(q&&Object.keys(q).every(k=>['by','value','name'].includes(k))&&['selector','text','role'].includes(q.by)&&typeof q.value==='string'&&q.value.length>0,'viewport-proof-locator-invalid');
    }
    need(cmd.elements.some(e=>e.kind==='date-filter')&&cmd.elements.some(e=>e.kind==='header')&&cmd.elements.some(e=>e.kind==='row'),'viewport-proof-required-kinds-missing');
  }
  const intersects=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
  const contained=(a,b)=>a.left>=b.left&&a.top>=b.top&&a.right<=b.right&&a.bottom<=b.bottom;
  function unsupportedStyle(style,node){
    // CSS declarations can persist while idle. Only instantiated active/pending
    // motion rejects coverage; the before/after epoch still detects layout drift.
    return Boolean(style.transform&&style.transform!=='none'||style.zoom&&!['1','normal'].includes(String(style.zoom))||style.clip&&style.clip!=='auto'||style.clipPath&&style.clipPath!=='none'||style.maskImage&&style.maskImage!=='none'||style.webkitMaskImage&&style.webkitMaskImage!=='none'||style.filter&&style.filter!=='none'||style.opacity!==undefined&&Number(style.opacity)!==1||typeof node.getAnimations==='function'&&node.getAnimations().some(a=>a.pending===true||!['finished','idle'].includes(a.playState)));
  }
  const GOV_SCHEMA='gov-records-stable5-v1',PROVIDER_SCHEMA='gov-records-provider-scope-v2',MANUAL_CONTRACT='notice-five-business-cells-v2';
  const RECTIFICATION_CONTRACT='gov-records-rectification-display-v3',RECTIFICATION_SCHEMA='gov-records-stable5-rectification-v3',RECTIFICATION_PROVIDER_SCHEMA='gov-records-provider-rectification-v3',RECTIFICATION_MARKER='rectification-v3';
  const rectificationTimerPattern=/^(?:0|[1-9][0-9]*)天(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$/;
  const GOV_HEADERS=['违规原因','处置主体','违规对象','处置生效状态','处置方式','违规时间','整改状态','申诉状态','违约金状态','操作'];
  const timerPattern=/^(?:[0-9]+天[0-9]{2}:[0-9]{2}:[0-9]{2}|(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])$/;
  const classes=n=>String(n.attributes?.class||'').split(/\s+/).filter(Boolean);
  function treeNodes(n){return [n,...(n.children||[]).flatMap(treeNodes)]}
  function govOne(ns,why){need(ns.length===1,'governance-projection-'+why);return ns[0]}
  function govSignature(n,text){const a=n.attributes||{};return [n.selector??null,n.tag??null,n.role??null,text===undefined?n.name||'':text,a.class||'',a.value??null,n.disabled??false,...['aria-disabled','aria-checked','aria-selected','aria-pressed'].map(k=>a[k]??null)]}
  function govNode(n,masks){
    if(['input','textarea','select'].includes(n.tag)&&n.name!=='违规时间')return [['excluded-form-control',n.selector??null,n.tag],[]];
    return [govSignature(n,masks.get(n.selector)),(n.children||[]).map(c=>govNode(c,masks))];
  }
  function projectionSchema(contract,provider=false){need(contract===null||contract===RECTIFICATION_CONTRACT,'governance-projection-contract-unreviewed');return contract?(provider?RECTIFICATION_PROVIDER_SCHEMA:RECTIFICATION_SCHEMA):(provider?PROVIDER_SCHEMA:GOV_SCHEMA)}
  function commandProjection(cmd){
    const keys=cmd.elements.map(e=>e.key),marked=keys.some(k=>k.includes(':rectification-'));
    if(!marked)return null;
    need(keys.length>0&&keys.every(k=>k.startsWith((k.startsWith(MANUAL_CONTRACT+':')?MANUAL_CONTRACT:BUSINESS_CONTRACT)+':'+RECTIFICATION_MARKER+':')),'viewport-proof-projection-namespace-invalid');return RECTIFICATION_CONTRACT;
  }
  function rectificationMask(cell){
    if(!treeNodes(cell).some(n=>String(n.name||'').startsWith('待整改')))return {masks:new Map(),timers:[]};
    const inner=cell.children||[];need(inner.length===1,'governance-projection-rectification-wrapper');const wrapper=inner[0],parts=wrapper.children||[];
    need(wrapper.tag==='div'&&JSON.stringify(classes(wrapper))==='["multi_text-ElDZAk"]'&&parts.length===2,'governance-projection-rectification-wrapper');const [label,valuebox]=parts,leaves=valuebox.children||[];
    need(label.tag==='div'&&JSON.stringify(classes(label))==='["multi_text_top-gLB_CR"]'&&label.name==='待整改'&&!(label.children||[]).length&&valuebox.tag==='div'&&JSON.stringify(classes(valuebox))==='["multi_text_second-sudxus"]'&&leaves.length===1,'governance-projection-rectification-shape');const leaf=leaves[0],value=leaf.name||'';
    need(leaf.tag==='span'&&!(leaf.children||[]).length&&!Object.keys(leaf.attributes||{}).length&&rectificationTimerPattern.test(value)&&value.match(rectificationTimerPattern)?.[0]===value,'governance-projection-rectification-timer');
    need([cell,wrapper,label,valuebox,leaf].every(n=>n.role===(n===cell?'cell':'generic')&&(n.disabled??false)===false&&Object.keys(n.attributes||{}).every(k=>['class','role'].includes(k))),'governance-projection-rectification-noninteractive-shape');
    need(valuebox.name===value&&wrapper.name==='待整改 '+value&&cell.name==='待整改 '+value,'governance-projection-rectification-aggregate');return {masks:new Map([[cell.selector,'待整改 <rectification-countdown>'],[wrapper.selector,'待整改 <rectification-countdown>'],[valuebox.selector,'<rectification-countdown>'],[leaf.selector,'<rectification-countdown>']]),timers:[leaf.selector]};
  }
  function govRow(row,contract=null){
    projectionSchema(contract);
    const cells=row.children||[];need(cells.length===10&&cells.every(c=>c.tag==='td'&&c.role==='cell'&&classes(c).includes('governance_merchant-Table-Cell')),'governance-projection-ten-cells-required');
    const masks=new Map(),timers=[],appeal=cells[7],leaves=treeNodes(appeal).filter(n=>n.tag==='span'&&!(n.children||[]).length&&timerPattern.test(n.name||''));
    if(leaves.length){
      const leaf=govOne(leaves,'timer-not-unique'),inner=appeal.children||[];
      need(inner.length===1&&JSON.stringify(classes(inner[0]))==='["multi_text-ElDZAk"]','governance-projection-timer-wrapper');
      const parts=inner[0].children||[];
      need(parts.length===2&&JSON.stringify(classes(parts[0]))==='["multi_text_top-gLB_CR"]'&&parts[0].name==='待申诉'&&!(parts[0].children||[]).length&&JSON.stringify(classes(parts[1]))==='["multi_text_second-sudxus"]'&&(parts[1].children||[]).length===1&&parts[1].children[0]===leaf,'governance-projection-timer-shape');
      const value=leaf.name;need(parts[1].name===value&&inner[0].name==='待申诉 '+value&&appeal.name==='待申诉 '+value,'governance-projection-timer-aggregate');
      for(const n of [appeal,inner[0]])masks.set(n.selector,'待申诉 <appeal-countdown>');
      for(const n of [parts[1],leaf])masks.set(n.selector,'<appeal-countdown>');timers.push(leaf.selector);
    }
    if(contract){const extra=rectificationMask(cells[6]);for(const [key,value] of extra.masks)masks.set(key,value);timers.push(...extra.timers);}
    return {cells,masks,timers};
  }
  function governanceProjection(tree,groupid,actualURL=null,contract=null){
    const schema=projectionSchema(contract,actualURL!==null);
    need(tree.truncated===false&&tree.url==='https://life.douyin.com/p/governance/violation_list','governance-projection-tree-scope');
    const ns=treeNodes(tree.root);need(ns.length<10000,'governance-projection-tree-bound');const refs=[],timers=[],rectificationTimers=[];
    function pick(test,why){const n=govOne(ns.filter(test),why);refs.push(n.selector);return n}
    const cards=ns.filter(n=>String(n.attributes?.class||'').includes('UserCard-index-module__outer--'));let card;
    if(actualURL===null)card=pick(n=>cards.includes(n),'identity');else{const u=new URL(actualURL);need(u.origin==='https://life.douyin.com'&&u.pathname==='/p/governance/violation_list'&&u.searchParams.getAll('groupid').length===1&&u.searchParams.get('groupid')===String(groupid),'governance-projection-actual-url-scope');need(cards.length<=1,'governance-projection-identity-not-unique');card=cards[0]||null;}
    const provider=pick(n=>String(n.attributes?.class||'').includes('Profile-index-module__title--')&&/^服务商[0-9]+$/.test(n.name||''),'provider');
    const date=pick(n=>n.tag==='input'&&n.role==='textbox'&&n.name==='违规时间'&&classes(n).includes('governance_merchant-input'),'date');
    const table=pick(n=>n.tag==='table'&&classes(n).includes('governance_merchant-Table-Implement'),'table');
    const heads=treeNodes(table).filter(n=>n.tag==='th'&&n.role==='columnheader');need(JSON.stringify(heads.map(n=>n.name))===JSON.stringify(GOV_HEADERS),'governance-projection-headers');refs.push(...heads.map(n=>n.selector));
    const alltab=pick(n=>classes(n).includes('governance_merchant-tab-bar-item-active')&&/^全部\s*[0-9]+$/.test(n.name||''),'all');
    const unread=pick(n=>n.tag==='label'&&n.name==='只看未读'&&classes(n).includes('governance_merchant-checkbox'),'unread');need(treeNodes(unread).filter(n=>classes(n).includes('governance_merchant-checkbox-icon-uncheck')).length===1,'governance-projection-unread-off');
    const pager=pick(n=>classes(n).includes('governance_merchant-pager'),'pager');need(treeNodes(pager).filter(n=>classes(n).includes('governance_merchant-pager-item-checked')).length===1,'governance-projection-current-page');
    const rows=treeNodes(table).filter(n=>n.tag==='tr'&&(n.children||[]).some(c=>c.tag==='td'));need(rows.length>0&&rows.length<=10,'governance-projection-row-count');
    const out=[],ids=[],rowTexts=new Map();
    for(const row of rows){
      need(row.role==='row'&&classes(row).includes('governance_merchant-Table-Row'),'governance-projection-row-semantics');const {cells,masks,timers:ts}=govRow(row,contract),found=[...String(cells[0].name||'').matchAll(/ID:\s*([A-Za-z0-9_-]+)/g)].map(m=>m[1]);
      need(found.length===1&&!ids.includes(found[0]),'governance-projection-notice-id');ids.push(found[0]);timers.push(...ts);rectificationTimers.push(...treeNodes(cells[6]).filter(n=>ts.includes(n.selector)).map(n=>n.selector));refs.push(row.selector);out.push([govSignature(row,''),cells.map(c=>govNode(c,masks))]);rowTexts.set(row.selector,JSON.stringify([found[0],...cells.slice(0,5).map(c=>c.name||'')]));
    }
    return {...(contract?{rectification_timers:rectificationTimers}:{}),value:[schema,String(groupid),tree.url,govNode(provider,new Map()),actualURL===null?govNode(card,new Map()):['actual-url',actualURL],govNode(date,new Map()),heads.map(h=>govNode(h,new Map())),govNode(alltab,new Map()),govNode(unread,new Map()),govNode(pager,new Map()),ids,out],refs,timers,rowTexts,provider:provider.name,visibleCard:card,dateSelector:date.selector,headerSelectors:heads.slice(0,5).map(n=>n.selector)};
  }

  function diagnosticSelector(el){
    const parts=[];
    for(let node=el;node&&node.nodeType===1;node=node.parentElement){
      if(node.id&&typeof CSS!=='undefined'){parts.unshift('#'+CSS.escape(node.id));break;}
      const tag=String(node.tagName||'').toLowerCase();
      if(!tag)return null;
      const siblings=Array.from(node.parentElement?.children||[]).filter(n=>n.tagName===node.tagName);
      parts.unshift(tag+(siblings.length>1?':nth-of-type('+(siblings.indexOf(node)+1)+')':''));
      if(parts.length>=32)return null;
    }
    const value=parts.join(' > ');return value.length<=1500?value:null;
  }
  function overlayDiagnostic(candidate,style,rects){
    return {selector:diagnosticSelector(candidate),tag:String(candidate.tagName||'').toLowerCase(),
      class:String(candidate.getAttribute?.('class')||'').slice(0,500),class_truncated:String(candidate.getAttribute?.('class')||'').length>500,
      position:style.position,pointer_events:style.pointerEvents,opacity:style.opacity,
      background_color:style.backgroundColor,background_image_present:!!style.backgroundImage&&style.backgroundImage!=='none',
      has_text:!!String(candidate.innerText||'').trim()};
  }
  function diagnosticRect(rect){return Object.fromEntries(['left','top','right','bottom','width','height'].map(k=>[k,Number.isFinite(rect[k])?rect[k]:null]))}
  function diagnosticMetrics(node){
    const style=getComputedStyle(node),result={rect:diagnosticRect(node.getBoundingClientRect())};
    for(const key of ['clientLeft','clientTop','clientWidth','clientHeight','scrollLeft','scrollTop','scrollWidth','scrollHeight'])result[key]=Number.isFinite(node[key])?node[key]:null;
    result.style=Object.fromEntries(['display','position','overflowX','overflowY','scrollbarGutter','transform','zoom','borderLeftWidth','borderRightWidth','borderTopWidth','borderBottomWidth','paddingLeft','paddingRight','paddingTop','paddingBottom'].map(k=>[k,typeof style[k]==='string'?style[k]:null]));
    return result;
  }
  function overflowClipBox(node,style,rect,fractionalHidden=false){
    const conservative={left:rect.left+node.clientLeft,top:rect.top+node.clientTop,right:rect.left+node.clientLeft+node.clientWidth,bottom:rect.top+node.clientTop+node.clientHeight};
    // Exact observed zero-border table family with no reserved layout gutter.
    // CSSOM offset/client sizes round to integers; the clip edge itself does not.
    if(fractionalHidden&&node.tagName==='DIV'&&node.getAttribute('class')==='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable'&&
      style.overflowX==='auto'&&style.overflowY==='auto'&&style.scrollbarGutter==='auto'&&style.scrollbarWidth==='auto'&&
      style.display==='block'&&style.position==='relative'&&style.boxSizing==='border-box'&&['paddingLeft','paddingRight','paddingTop','paddingBottom'].every(k=>style[k]==='0px')&&
      style.transform==='none'&&['1','normal'].includes(String(style.zoom))&&!unsupportedStyle(style,node)&&
      ['borderLeftWidth','borderRightWidth','borderTopWidth','borderBottomWidth'].every(k=>style[k]==='0px')&&node.clientLeft===0&&node.clientTop===0&&
      ['clientWidth','clientHeight','offsetWidth','offsetHeight','scrollWidth','scrollHeight'].every(k=>Number.isSafeInteger(node[k])&&node[k]>0)&&
      node.offsetWidth===node.clientWidth&&node.offsetHeight===node.clientHeight&&
      ['left','top','right','bottom','width','height'].every(k=>Number.isFinite(rect[k]))&&rect.width>0&&rect.height>0&&
      rect.right-rect.left===rect.width&&rect.bottom-rect.top===rect.height&&Math.round(rect.width)===node.offsetWidth&&Math.round(rect.height)===node.offsetHeight){
      let defaultScrollbar=false;
      try{defaultScrollbar=['::-webkit-scrollbar','::-webkit-scrollbar:horizontal','::-webkit-scrollbar:vertical'].every(p=>{
        const s=getComputedStyle(node,p);return p==='::-webkit-scrollbar'?s.display==='inline'&&s.width==='auto'&&s.height==='auto':s.display===''&&s.width===''&&s.height==='';
      });}catch{/* Unknown scrollbar geometry retains the conservative clip. */}
      if(defaultScrollbar)return {left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom};
    }
    // Overflow hidden clips at the padding box, whereas CSSOM clientTop/Left
    // and client dimensions are integer-rounded. No tolerance is introduced.
    // https://www.w3.org/TR/css-overflow-3/#valdef-overflow-hidden
    // https://drafts.csswg.org/cssom-view/#dom-element-clienttop
    if(!fractionalHidden||style.overflowX!=='hidden'||style.overflowY!=='hidden'||style.scrollbarGutter!=='auto'||style.transform!=='none'||unsupportedStyle(style,node))return conservative;
    if(!['block','flow-root','inline-block','flex','inline-flex','grid','inline-grid','table-cell'].includes(style.display))return conservative;
    if(!['left','top','right','bottom','width','height'].every(k=>Number.isFinite(rect[k]))||rect.width<0||rect.height<0||rect.right<rect.left||rect.bottom<rect.top)return conservative;
    const keys=['borderLeftWidth','borderTopWidth','borderRightWidth','borderBottomWidth'],widths=keys.map(k=>/^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px$/.test(String(style[k]))?Number.parseFloat(style[k]):NaN);
    if(!widths.every(Number.isFinite)||widths[0]+widths[2]>rect.width||widths[1]+widths[3]>rect.height)return conservative;
    return {left:rect.left+widths[0],top:rect.top+widths[1],right:rect.right-widths[2],bottom:rect.bottom-widths[3]};
  }
  function geometry(el,view,fractionalHidden=false){
    let rendered=true,clipped=false,textClipped=false,unsupported=false,occluded=false;
    const containmentReasons=[],containmentKeys=new Set(),targetSelector=diagnosticSelector(el);
    function containmentReason(offender,ancestor,axis,reason,checked,clip){
      const entry={target_selector:targetSelector,offender_selector:diagnosticSelector(offender),ancestor_selector:ancestor?diagnosticSelector(ancestor):null,axis,reason};
      const key=JSON.stringify(entry);if(containmentKeys.has(key))return;containmentKeys.add(key);
      if(containmentReasons.length<12){
        const lo=axis==='x'?'left':'top',hi=axis==='x'?'right':'bottom';
        containmentReasons.push({...entry,offender:diagnosticMetrics(offender),ancestor:ancestor?diagnosticMetrics(ancestor):null,checked_rect:diagnosticRect(checked),clip_box:{left:clip.left,top:clip.top,right:clip.right,bottom:clip.bottom},axis_excess:{leading:Math.max(0,clip[lo]-checked[lo]),trailing:Math.max(0,checked[hi]-clip[hi])}});
      }
    }
    const subtree=[el,...el.querySelectorAll('*')];
    for(const node of subtree){
      const style=getComputedStyle(node),rects=[...node.getClientRects()];
      if(typeof node.checkVisibility==='function'&&!node.checkVisibility({contentVisibilityAuto:true,opacityProperty:true,visibilityProperty:true})){if(node===el)rendered=false;else continue;}
      if(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse'||Number(style.opacity)===0){
        if(node===el)rendered=false;else continue;
      }
      if(unsupportedStyle(style,node))unsupported=true;
      if(style.clipPath&&style.clipPath!=='none'||style.maskImage&&style.maskImage!=='none'||style.contentVisibility==='hidden')unsupported=true;
      // A clamp declaration alone does not mean any text is omitted.
      // Actual overflowing content remains ineligible until visibly expanded.
      if(style.webkitLineClamp&&style.webkitLineClamp!=='none'&&style.webkitLineClamp!=='0'&&(node.scrollHeight>node.clientHeight||node.scrollWidth>node.clientWidth))textClipped=true;
      if(node.scrollHeight>node.clientHeight&&['hidden','clip','auto','scroll'].includes(style.overflowY))textClipped=true;
      if(node.scrollWidth>node.clientWidth&&['hidden','clip','auto','scroll'].includes(style.overflowX))textClipped=true;
      if(node===el&&!rects.some(r=>r.width>0&&r.height>0))rendered=false;
      for(const rect of rects){
        if(rect.width<=0||rect.height<=0)continue;
        if(!contained(rect,view)){
          clipped=true;
          if(rect.left<view.left||rect.right>view.right)containmentReason(node,null,'x','outside-viewport',rect,view);
          if(rect.top<view.top||rect.bottom>view.bottom)containmentReason(node,null,'y','outside-viewport',rect,view);
        }
        for(let p=node.parentElement;p;p=p.parentElement){
          const ps=getComputedStyle(p),r=p.getBoundingClientRect();
          if(ps.display==='none'||ps.visibility==='hidden'||ps.visibility==='collapse'||Number(ps.opacity)===0)rendered=false;
          if(unsupportedStyle(ps,p))unsupported=true;
          const box=overflowClipBox(p,ps,r,fractionalHidden);
          if(['hidden','clip','auto','scroll'].includes(ps.overflowX)&&(rect.left<box.left||rect.right>box.right)){clipped=true;containmentReason(node,p,'x','ancestor-overflow',rect,box);}
          if(['hidden','clip','auto','scroll'].includes(ps.overflowY)&&(rect.top<box.top||rect.bottom>box.bottom)){clipped=true;containmentReason(node,p,'y','ancestor-overflow',rect,box);}
        }
      }
    }
    const target=[...el.getClientRects()].filter(r=>r.width>0&&r.height>0);
    const possible_overlays=[];let possible_overlay_count=0;
    // Fail closed on possible painted overlays. No point probing or hit testing.
    for(const candidate of document.querySelectorAll('*')){
      if(candidate===el||el.contains(candidate)||candidate.contains(el))continue;
      const style=getComputedStyle(candidate);
      if(style.display==='none'||style.visibility==='hidden'||Number(style.opacity)===0)continue;
      // Relative/static overlap can also paint over the target. Conservatively
      // reject every intersecting non-ancestor, without z-order or hit testing.
      const overlapping=[...candidate.getClientRects()].filter(r=>r.width>0&&r.height>0&&target.some(t=>intersects(t,r)));
      if(overlapping.length){occluded=true;possible_overlay_count++;if(possible_overlays.length<12)possible_overlays.push(overlayDiagnostic(candidate,style,overlapping));}
    }
    return {containment_diagnostic:{purpose:'readonly-containment-diagnostic-only',scope:'target-and-descendants',...(containmentKeys.size?{coordinate_space:'CSS-viewport-diagnostic-only'}:{}),reasons:containmentReasons,reason_count:containmentKeys.size,truncated:containmentKeys.size>containmentReasons.length},possible_overlay_diagnostic:{purpose:'readonly-overlay-diagnostic-only',candidates:possible_overlays,candidate_count:possible_overlay_count,truncated:possible_overlay_count>possible_overlays.length},rendered,viewport_contained:!clipped,text_unclipped:!textClipped,unsupported_css_absent:!unsupported,possible_overlay_absent:!occluded,fully_visible:rendered&&!clipped&&!textClipped&&!unsupported&&!occluded};
  }
  const BUSINESS_CONTRACT='notice-five-business-cells-v1';
  const BUSINESS_FIELDS=['reason','subject','object','effective_status','disposal'];
  function unsupportedCSSDiagnostic(el){
    const candidates=[],seen=new Set(),nodes=[...new Set([el,...el.querySelectorAll('*'),...(()=>{const a=[];for(let p=el.parentElement;p;p=p.parentElement)a.push(p);return a;})()])];let count=0;
    const clean=v=>String(v??'').replace(/url\([^)]*\)/gi,'url(<uri-omitted>)').slice(0,160);
    for(const node of nodes){const style=getComputedStyle(node),ancestor=node!==el&&!el.contains(node);if(!ancestor&&(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse'||Number(style.opacity)===0))continue;
      const reasons=[];for(const [field,defaults] of [['transform',['none']],['zoom',['1','normal']],['clip',['auto']],['clipPath',['none']],['maskImage',['none']],['webkitMaskImage',['none']],['filter',['none']]])if(style[field]&&!defaults.includes(String(style[field])))reasons.push(field);
      if(style.opacity!==undefined&&Number(style.opacity)!==1)reasons.push('opacity');if(style.contentVisibility==='hidden')reasons.push('contentVisibility');
      const animations=typeof node.getAnimations==='function'?node.getAnimations().filter(a=>a.pending===true||!['finished','idle'].includes(a.playState)):[];if(animations.length)reasons.push('active-or-pending-animation');if(!reasons.length)continue;
      const selector=diagnosticSelector(node),key=selector||node;if(seen.has(key))continue;seen.add(key);count++;
      if(candidates.length<12)candidates.push({selector,tag:String(node.tagName||'').toLowerCase(),relation:node===el?'target':ancestor?'ancestor':'descendant',reasons,style:Object.fromEntries(['transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','contentVisibility'].map(k=>[k,clean(style[k])])),animations:animations.slice(0,8).map(a=>({pending:a.pending===true,play_state:clean(a.playState)})),animation_count:animations.length,animations_truncated:animations.length>8});
    }
    return {purpose:'readonly-unsupported-css-diagnostic-only',candidates,candidate_count:count,truncated:count>candidates.length};
  }
  function supportedIdentityBadges(el,diagnostic){
    const tokens=n=>String(n.getAttribute?.('class')||'').split(/\s+/).filter(Boolean).sort().join(' '),same=(n,tag,classes)=>n?.tagName===tag&&tokens(n)===classes.split(' ').sort().join(' '),nodes=[el,...el.querySelectorAll('*')],out=[];
    const badgeClass='governance_merchant-badge-sup governance_merchant-badge-sup-placement-top-right governance_merchant-badge-sup-show',dotClass='governance_merchant-badge-dot governance_merchant-badge-dot-placement-top-right governance_merchant-badge-type-danger';
    if(el.tagName!=='TD'||diagnostic.truncated)return out;
    for(const candidate of diagnostic.candidates){
      if(candidate.relation!=='descendant'||candidate.reasons.length!==1||candidate.reasons[0]!=='transform'||candidate.animation_count!==0)continue;
      const found=nodes.filter(n=>diagnosticSelector(n)===candidate.selector);if(found.length!==1)continue;const node=found[0],children=[...node.children];if(!same(node,'SUP',badgeClass)||children.length!==1||!same(children[0],'DIV',dotClass)||children[0].children.length||String(node.innerText||'').trim()||String(children[0].innerText||'').trim())continue;
      if([node,children[0]].some(n=>n.getAttribute('role')!=null||n.getAttribute('tabindex')!=null||n.tabIndex>=0||n===document.activeElement))continue;
      const transform=getComputedStyle(node).transform,match=/^matrix\(([^()]*)\)$/.exec(transform);if(!match)continue;const values=match[1].split(',').map(s=>s.trim());if(values.length!==6||values.some(v=>!/^[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:e[-+]?[0-9]+)?$/i.test(v)))continue;const numbers=values.map(Number);if(numbers.some((n,i)=>!Number.isFinite(n)||n!==[1,0,0,1,0,0][i]))continue;
      out.push({selector:candidate.selector,class:node.getAttribute('class'),child_selector:diagnosticSelector(children[0]),child_class:children[0].getAttribute('class'),classification:'reviewed-static-identity-2d-badge-v1',computed_transform:transform,identity_components:numbers,active_or_pending_animation_count:0,text_present:false,interactive:false,geometry_changed:false,original_css_retained:true});
    }
    return out;
  }
  // Failure-only public geometry; never returns text/value or authorizes capture.
  function businessTextGeometryFailure(code,el,node,original,textRect,view,rects,conditions,ancestor=null){
    const selector=n=>{const found=diagnosticSelector(n),raw=String(found||'');return {value:found==null?'<selector-unavailable>':/https?:|data:|file:/i.test(raw)?'<selector-uri-omitted>':raw.slice(0,512),truncated:found==null||raw.length>512};};
    const rect=r=>Object.fromEntries(['left','top','right','bottom','width','height'].map(k=>[k,Number.isFinite(r?.[k])?r[k]:null]));
    const cell=selector(el),target=selector(node),parent=ancestor?selector(ancestor.node):null;
    const diagnostic={schema:'business-text-geometry-failure-v1',build:BUILD,geometry_decision_changed:false,capture_certified:false,pixel_input_actions:false,coordinate_space:'CSS-viewport-diagnostic-only',cell:{selector:cell.value,tag:String(el.tagName||'').toLowerCase().slice(0,32)},node:{selector:target.value,tag:String(node.tagName||'').toLowerCase().slice(0,32)},original_rect:rect(original),text_rect:rect(textRect),view:rect(view),cell_client_rects:rects.slice(0,16).map(rect),cell_client_rect_count:rects.length,failed_conditions:conditions,...(ancestor?{ancestor:{selector:parent.value,clip_box:rect(ancestor.box),overflow_x:String(ancestor.style.overflowX||'').slice(0,16),overflow_y:String(ancestor.style.overflowY||'').slice(0,16)}}:{}),truncated:cell.truncated||target.truncated||!!parent?.truncated||rects.length>16};
    throw Error(code+':'+JSON.stringify(diagnostic));
  }
  function businessTextLeafEvidence(el,view,sourceNode,supportedBadges=[]){
    const schema='source-bound-public-text-grapheme-clips-v1',limits={nodes:64,parts:64,text_units:16000,graphemes:512,rectangles:2048,ancestors:40};
    const fail=code=>{throw Error(code)},norm=s=>String(s??'').replace(/\s+/g,' ').trim();
    const box=r=>{const b=Object.fromEntries(['left','top','right','bottom','width','height'].map(k=>[k,r[k]]));if(!Object.values(b).every(Number.isFinite)||b.width<0||b.height<0||b.right-b.left!==b.width||b.bottom-b.top!==b.height)fail('leaf-invalid-rect');return b;};
    try{
      if(!sourceNode||sourceNode.selector!==diagnosticSelector(el)||sourceNode.tag!=='td')fail('leaf-source-cell-required');
      if(typeof Intl?.Segmenter!=='function'||typeof document.createRange!=='function')fail('leaf-range-or-segmenter-unavailable');
      const source=[],visit=n=>{if(source.length>=limits.nodes)fail('leaf-node-budget');if(!n||typeof n.selector!=='string'||typeof n.name!=='string'||!Array.isArray(n.children))fail('leaf-source-node-shape');source.push(n);for(const c of n.children)visit(c);};visit(sourceNode);
      if(new Set(source.map(n=>n.selector)).size!==source.length)fail('leaf-duplicate-source-owner');
      const actual=[],stack=[el];let visited=0,totalParts=0,textUnits=0;while(stack.length){const n=stack.pop();if(++visited>limits.nodes)fail('leaf-actual-node-budget');if(n.nodeType===1)actual.push(n);for(let i=n.childNodes.length-1;i>=0;i--)stack.push(n.childNodes[i]);}
      const owners=[],leaves=[],segmenter=new Intl.Segmenter(undefined,{granularity:'grapheme'});let units=0,rectangles=0,full=true,excerptEligible=true;
      const cell=box(el.getBoundingClientRect()),viewport={...view,width:view.right-view.left,height:view.bottom-view.top};
      for(const src of source){
        const matches=actual.filter(n=>diagnosticSelector(n)===src.selector);if(matches.length!==1)fail('leaf-owner-not-unique');const owner=matches[0],style=getComputedStyle(owner);
        if(owner.tagName.toLowerCase()!==src.tag||['INPUT','TEXTAREA','SELECT','IFRAME','CANVAS','VIDEO','SCRIPT','STYLE'].includes(owner.tagName))fail('leaf-source-owner-kind');
        const badge=supportedBadges.find(b=>b.selector===src.selector),nontextBadge=Boolean(badge&&norm(src.name)===''&&actual.filter(n=>n===owner||owner.contains(n)).every(n=>[...n.childNodes].every(c=>c.nodeType!==3||!norm(c.nodeValue))));
        if(style.display==='none'||['hidden','collapse'].includes(style.visibility)||Number(style.opacity)!==1||unsupportedStyle(style,owner)&&!nontextBadge)fail('leaf-owner-not-public');
        for(const pseudo of ['::before','::after']){const content=getComputedStyle(owner,pseudo).content;if(!['none','normal','""',"''"].includes(content))fail('leaf-generated-text-unreviewed');}
        const renderedParts=[];const parts=[],expectedChildren=src.children.map(n=>n.selector),elementChildren=[];let rendered='';
        for(let index=0;index<owner.childNodes.length;index++){
          if(++totalParts>limits.parts)fail('leaf-child-parts-budget');const child=owner.childNodes[index];
          if(child.nodeType===1){const selector=diagnosticSelector(child);if(!expectedChildren.includes(selector)){const cs=getComputedStyle(child);if(cs.display==='none'||['hidden','collapse'].includes(cs.visibility)||Number(cs.opacity)===0)continue;fail('leaf-unbound-visible-child');}parts.push({kind:'element',child_index:index,selector});elementChildren.push(selector);rendered+=source.find(n=>n.selector===selector).name;renderedParts.push(source.find(n=>n.selector===selector).name);continue;}
          if(child.nodeType!==3){if(child.nodeType!==8)fail('leaf-unreviewed-child-kind');continue;}
          const text=String(child.nodeValue??'');textUnits+=text.length;if(textUnits>limits.text_units)fail('leaf-text-budget');parts.push({kind:'text',child_index:index,text});rendered+=text;renderedParts.push(text);if(!norm(text))continue;
          // Bidi ordering is represented by rects, not inferred from increasing x.
          // Explicit formatting/isolated zero-width characters cannot certify text.
          if(/[\u200b\u200e\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]/u.test(text))fail('leaf-invisible-formatting-unreviewed');
          const ancestors=[];for(let a=owner;a;a=a.parentElement){if(ancestors.length>=limits.ancestors)fail('leaf-ancestor-budget');const as=getComputedStyle(a);if(unsupportedStyle(as,a))fail('leaf-ancestor-effect-unreviewed');const r=overflowClipBox(a,as,a.getBoundingClientRect(),true);const clipSource={rect:box(a.getBoundingClientRect()),metrics:Object.fromEntries(['clientLeft','clientTop','clientWidth','clientHeight','offsetWidth','offsetHeight','scrollWidth','scrollHeight'].map(k=>[k,a[k]])),style:Object.fromEntries(['display','position','boxSizing','paddingLeft','paddingRight','paddingTop','paddingBottom','borderLeftWidth','borderTopWidth','borderRightWidth','borderBottomWidth','overflowX','overflowY','scrollbarGutter','scrollbarWidth','transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','textOverflow','webkitLineClamp'].map(k=>[k,String(as[k]??'')])),scrollbar_pseudo:null};if(a.tagName==='DIV'&&a.getAttribute('class')==='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable'){clipSource.table_container=true;clipSource.scrollbar_pseudo=Object.fromEntries(['::-webkit-scrollbar','::-webkit-scrollbar:horizontal','::-webkit-scrollbar:vertical'].map(p=>{const ps=getComputedStyle(a,p);return [p,Object.fromEntries(['display','width','height'].map(k=>[k,ps[k]]))]}));}else clipSource.table_container=false;const ellipsis={text_overflow:as.textOverflow||'',line_clamp:String(as.webkitLineClamp||''),overflow_x:as.overflowX||'',overflow_y:as.overflowY||'',client_width:a.clientWidth,client_height:a.clientHeight,scroll_width:a.scrollWidth,scroll_height:a.scrollHeight};ancestors.push({selector:diagnosticSelector(a),clip_source:clipSource,ellipsis,x:['hidden','clip','auto','scroll'].includes(as.overflowX),y:['hidden','clip','auto','scroll'].includes(as.overflowY),box:{left:r.left,top:r.top,right:r.right,bottom:r.bottom}});}
          for(const a of ancestors){const e=a.ellipsis;if((e.text_overflow==='ellipsis'||/^[1-9][0-9]*$/.test(e.line_clamp))&&[e.overflow_x,e.overflow_y].includes('hidden')&&(e.scroll_width>e.client_width||e.scroll_height>e.client_height))full=false;}
          let visibleAny=false;const segments=[];for(const item of segmenter.segment(text)){
            if(!norm(item.segment))continue;if(/^[\p{Mark}\p{Format}]+$/u.test(item.segment))fail('leaf-grapheme-without-base');if(++units>limits.graphemes)fail('leaf-grapheme-budget');const start=item.index,end=start+item.segment.length,range=document.createRange();let rs;
            try{range.setStart(child,start);range.setEnd(child,end);rs=[...range.getClientRects()];}finally{range.detach?.();}
            if(!rs.length)fail('leaf-nonempty-grapheme-no-rect');const rects=[];
            for(const r of rs){if(++rectangles>limits.rectangles)fail('leaf-rect-budget');const b=box(r);if(b.width<=0||b.height<=0)fail('leaf-nonempty-grapheme-zero-rect');let complete=contained(b,viewport)&&contained(b,cell),visible={...b};for(const a of ancestors){if(a.x&&(b.left<a.box.left||b.right>a.box.right)||a.y&&(b.top<a.box.top||b.bottom>a.box.bottom))complete=false;const e=a.ellipsis,supported=(e.text_overflow==='ellipsis'||/^[1-9][0-9]*$/.test(e.line_clamp))&&[e.overflow_x,e.overflow_y].includes('hidden')&&(e.scroll_width>e.client_width||e.scroll_height>e.client_height);if(supported){if(a.x){visible.left=Math.max(visible.left,a.box.left);visible.right=Math.min(visible.right,a.box.right);}if(a.y){visible.top=Math.max(visible.top,a.box.top);visible.bottom=Math.min(visible.bottom,a.box.bottom);}}else if(a.x&&(visible.left<a.box.left||visible.right>a.box.right)||a.y&&(visible.top<a.box.top||visible.bottom>a.box.bottom))excerptEligible=false;}if(visible.right>visible.left&&visible.bottom>visible.top){visibleAny=true;if(!contained(visible,viewport)||!contained(visible,cell))excerptEligible=false;}full=full&&complete;rects.push(b);}
            segments.push({start,end,rects});
          }
          if(!visibleAny)excerptEligible=false;leaves.push({owner_selector:src.selector,child_index:index,segments,ancestors});
        }
        const expectedText=norm(src.name);let cursor=0,pendingSpace=false,pendingLayout=false,previousKind=null;for(const part of parts){if(previousKind==='element'||part.kind==='element')pendingLayout=true;const value=part.kind==='text'?part.text:source.find(n=>n.selector===part.selector).name;for(const ch of value){if(/\s/u.test(ch)){if(cursor>0)pendingSpace=true;continue;}if(pendingSpace&&cursor>0){if(expectedText[cursor]!==' ')fail('leaf-source-owner-aggregate-changed');cursor++;}else if(pendingLayout&&cursor>0&&expectedText[cursor]===' ')cursor++;if(expectedText.slice(cursor,cursor+ch.length)!==ch)fail('leaf-source-owner-aggregate-changed');cursor+=ch.length;pendingSpace=false;pendingLayout=false;}previousKind=part.kind;}if(JSON.stringify(elementChildren)!==JSON.stringify(expectedChildren)||cursor!==expectedText.length)fail('leaf-source-owner-aggregate-changed');owners.push({selector:src.selector,identity_badge_exemption:nontextBadge?badge.selector:null,parts,pseudo:{before:getComputedStyle(owner,'::before').content,after:getComputedStyle(owner,'::after').content}});
      }
      return {schema,limits,cell,viewport,owners,leaves,full,excerpt_eligible:excerptEligible,unavailable:null};
    }catch(e){return {schema,limits,cell:null,viewport:null,owners:[],leaves:[],full:false,excerpt_eligible:false,unavailable:String(e.message||e)};}
  }

  function businessGeometry(el,view,allowEllipsis,manualContext=null,sourceNode=null){
    const unresolved=[];
    const reject=(code,node,original,textRect,rects,conditions,ancestor=null)=>{
      let error;try{businessTextGeometryFailure(code,el,node,original,textRect,view,rects,conditions,ancestor);}catch(e){error=e;}
      if(!manualContext||el.tagName!=='TD'||node===el||!el.contains(node))throw error;
      const own=el.getBoundingClientRect(),union=manualContext.union,parents=[];for(let n=node;n&&n!==el;n=n.parentElement){parents.push(n);need(parents.length<=32,'manual-text-parent-bound');}
      const safe=parents.every(n=>!['BUTTON','INPUT','TEXTAREA','SELECT','A','IFRAME','CANVAS','VIDEO'].includes(n.tagName)&&!n.isContentEditable&&!(Number.isInteger(n.tabIndex)&&n.tabIndex>=0)&&!['button','link','textbox','checkbox','radio','combobox','menuitem'].includes(n.getAttribute?.('role')));
      if(!(safe&&textRect.right>textRect.left&&textRect.bottom>textRect.top&&contained(textRect,view)&&contained(textRect,union)&&textRect.top>=own.top&&textRect.bottom<=own.bottom&&(textRect.left<own.left||textRect.right>own.right)&&(!ancestor||ancestor.node===el&&conditions.ancestor_clip_x&&!conditions.ancestor_clip_y)))throw error;
      need(unresolved.length<16,'manual-text-overflow-bound');const diagnostic=JSON.parse(error.message.slice(code.length+1));need(!diagnostic.truncated,'manual-text-diagnostic-truncated');unresolved.push({classification:'source-own-horizontal-text-overflow-v1',notice_id:manualContext.notice_id,tr_selector:manualContext.tr_selector,union_box:{...union,width:union.right-union.left,height:union.bottom-union.top},diagnostic,original_rejection:code,quality_review_required:true,text_complete_in_image:false,coverage_certified:false});
    };
    const recursive=geometry(el,view,true),rects=[...el.getClientRects()].filter(r=>r.width>0&&r.height>0);let complete=rects.length>0;
    for(const rect of rects){
      if(!contained(rect,view))complete=false;
      for(let p=el.parentElement;p;p=p.parentElement){const s=getComputedStyle(p),box=overflowClipBox(p,s,p.getBoundingClientRect(),true);
        if(['hidden','clip','auto','scroll'].includes(s.overflowX)&&(rect.left<box.left||rect.right>box.right))complete=false;
        if(['hidden','clip','auto','scroll'].includes(s.overflowY)&&(rect.top<box.top||rect.bottom>box.bottom))complete=false;
      }
    }
    const clips=[];
    for(const node of [el,...el.querySelectorAll('*')]){
      const style=getComputedStyle(node),publicText=node===el&&node.tagName==='INPUT'?String(node.value||''):String(node.innerText||'');if(!publicText.trim()||style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse'||Number(style.opacity)===0)continue;
      const x=node.scrollWidth>node.clientWidth&&['hidden','clip','auto','scroll'].includes(style.overflowX),y=node.scrollHeight>node.clientHeight&&['hidden','clip','auto','scroll'].includes(style.overflowY);
      if(!x&&!y)continue;need(clips.length<64,'business-text-clip-limit');
      const supported=(style.textOverflow==='ellipsis'||/^[1-9][0-9]*$/.test(String(style.webkitLineClamp)))&&[style.overflowX,style.overflowY].includes('hidden');
      clips.push({selector:diagnosticSelector(node),supported,text_overflow:style.textOverflow||'',line_clamp:String(style.webkitLineClamp||''),overflow_x:style.overflowX||'',overflow_y:style.overflowY||'',client_width:node.clientWidth,client_height:node.clientHeight,scroll_width:node.scrollWidth,scroll_height:node.scrollHeight});
    }
    // Only actual supported clipping may explain lost text. Non-text SVG/icon
    // rectangles do not determine the TD's own box, but textual descendants do.
    if(complete)for(const node of [el,...el.querySelectorAll('*')]){
      if(['SVG','IMG','PATH','G'].includes(node.tagName)||!String(node===el&&node.tagName==='INPUT'?node.value||'':node.innerText||'').trim())continue;
      const ns=getComputedStyle(node);if(ns.display==='none'||ns.visibility==='hidden'||ns.visibility==='collapse'||Number(ns.opacity)===0)continue;
      for(const original of [...node.getClientRects()].filter(r=>r.width>0&&r.height>0)){
        let textRect={left:original.left,top:original.top,right:original.right,bottom:original.bottom};
        for(let parent=node;parent;parent=parent.parentElement){
          const ps=getComputedStyle(parent),clip=clips.find(c=>c.selector===diagnosticSelector(parent));
          if(clip?.supported){const box=overflowClipBox(parent,ps,parent.getBoundingClientRect(),true);
            if(['hidden','clip','auto','scroll'].includes(ps.overflowX)){textRect.left=Math.max(textRect.left,box.left);textRect.right=Math.min(textRect.right,box.right);}
            if(['hidden','clip','auto','scroll'].includes(ps.overflowY)){textRect.top=Math.max(textRect.top,box.top);textRect.bottom=Math.min(textRect.bottom,box.bottom);}
          }
          if(parent===el)break;
        }
        const positive=textRect.right>textRect.left&&textRect.bottom>textRect.top,viewContained=contained(textRect,view),cellContained=rects.some(box=>contained(textRect,box));
        if(!(positive&&viewContained&&cellContained))reject('business-text-geometry-unreviewed',node,original,textRect,rects,{non_positive:!positive,outside_view:!viewContained,outside_cell:!cellContained});
        for(let parent=node.parentElement;parent;parent=parent.parentElement){const ps=getComputedStyle(parent),box=overflowClipBox(parent,ps,parent.getBoundingClientRect(),true);
          const x=['hidden','clip','auto','scroll'].includes(ps.overflowX)&&(textRect.left<box.left||textRect.right>box.right),y=['hidden','clip','auto','scroll'].includes(ps.overflowY)&&(textRect.top<box.top||textRect.bottom>box.bottom);
          if(x||y)reject('business-text-ancestor-clip-unreviewed',node,original,textRect,rects,{ancestor_clip_x:x,ancestor_clip_y:y},{node:parent,box,style:ps});
        }
      }
    }
    const diagnostic=unsupportedCSSDiagnostic(el),supported=supportedIdentityBadges(el,diagnostic),cssAbsent=recursive.unsupported_css_absent||!diagnostic.truncated&&diagnostic.candidate_count>0&&diagnostic.candidate_count===supported.length;
    const leaf=el.tagName==='TD'?businessTextLeafEvidence(el,view,sourceNode,supported):null;
    const text_unclipped=clips.length===0&&!unresolved.length&&(!leaf||leaf.full),ellipsis_supported=clips.every(c=>c.supported)&&!unresolved.length&&(!leaf||leaf.excerpt_eligible),eligible=recursive.rendered&&complete&&cssAbsent&&(text_unclipped||allowEllipsis&&ellipsis_supported);
    return {...(leaf?{text_leaf_evidence:leaf}:{}),...(unresolved.length?{unresolved_own_text_overflow:unresolved}:{}),supported_static_identity_transforms:supported,recursive_unsupported_css_absent:recursive.unsupported_css_absent,unsupported_css_diagnostic:diagnostic,rendered:recursive.rendered,box_viewport_contained:complete,unsupported_css_absent:cssAbsent,text_unclipped,ellipsis_supported,text_clips:clips,evidence_eligible:eligible,preview_required:eligible&&!text_unclipped,occlusion_verified:false};
  }
  // Inspection only: these values never participate in geometry/eligibility.
  function businessClipInspection(rows,one,view){
    const result={schema:'business-cell-clip-inspection-v1',purpose:'readonly-public-clip-diagnostic-only',geometry_decision_changed:false,pixel_input_actions:false,coordinate_space:'CSS-viewport-diagnostic-only',pixel_coordinates_returned:true,limits:{containers:1,text_cells:3,elements:32,text_nodes:64,ranges_per_text:8,ancestors_per_text:8,visited_nodes:256},container_count:0,containers:[],text_cell_count:0,text_cells:[],truncated:false};
    try{
      const candidates=[],parents=new Set();
      for(const row of rows)for(const cell of row.cells){const g=cell.geometry;if(!g.rendered||!g.unsupported_css_absent||g.box_viewport_contained||g.evidence_eligible)continue;
        const el=one({by:'selector',value:cell.selector}),rects=[...el.getClientRects()].filter(r=>r.width>0&&r.height>0);if(el.tagName!=='TD'||!rects.length||!rects.every(r=>contained(r,view)))continue;
        const found=[];for(let n=el.parentElement;n;n=n.parentElement){const s=getComputedStyle(n);if(n.tagName==='DIV'&&n.getAttribute('class')==='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable'&&s.overflowX==='auto'&&s.overflowY==='auto')found.push(n);}
        if(found.length!==1)continue;parents.add(found[0]);candidates.push({cell,el,parent:found[0]});
      }
      result.container_count=parents.size;if(parents.size!==1){result.unavailable='common-auto-container-not-unique';return result;}
      const metric=node=>{const m=diagnosticMetrics(node),s=getComputedStyle(node);for(const key of ['offsetWidth','offsetHeight'])m[key]=Number.isFinite(node[key])?node[key]:null;
        for(const key of ['scrollbarWidth','boxSizing','textOverflow','webkitLineClamp','whiteSpace','gap','columnGap','rowGap','alignItems','justifyContent'])m.style[key]=typeof s[key]==='string'?s[key].slice(0,100):null;return m;};
      const parent=[...parents][0],scrollbar={};
      for(const pseudo of ['::-webkit-scrollbar','::-webkit-scrollbar:horizontal','::-webkit-scrollbar:vertical']){try{const s=getComputedStyle(parent,pseudo);scrollbar[pseudo]=Object.fromEntries(['display','width','height'].map(k=>[k,typeof s[k]==='string'?s[k].slice(0,100):null]));}catch{scrollbar[pseudo]={unavailable:true};}}
      result.containers.push({selector:diagnosticSelector(parent),metrics:metric(parent),scrollbar_pseudo:scrollbar});
      const textCandidates=candidates.filter(c=>c.cell.index===2);result.text_cell_count=textCandidates.length;result.truncated=textCandidates.length>3;
      for(const candidate of textCandidates.slice(0,3)){
        const {el,cell}=candidate,item={selector:cell.selector,notice_id:rows.find(r=>r.cells.includes(cell)).notice_id,metrics:metric(el),elements:[],text_nodes:[],visited_nodes:0,text_node_count:0,range_count:0,truncated:false,range_api_available:typeof document.createRange==='function',no_text_values_returned:true},elements=new Map();
        const addElement=node=>{const selector=diagnosticSelector(node);if(!selector)return null;if(!elements.has(selector)){if(elements.size>=32){item.truncated=true;return null;}elements.set(selector,{selector,tag:node.tagName,metrics:metric(node)});}return selector;};
        addElement(el);
        const visible=owner=>{for(let n=owner;n;n=n.parentElement){const s=getComputedStyle(n);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||s.contentVisibility==='hidden'||Number(s.opacity)===0||typeof n.checkVisibility==='function'&&!n.checkVisibility({contentVisibilityAuto:true,opacityProperty:true,visibilityProperty:true}))return false;if(n===el)return true;}return false;};
        const visit=node=>{
          if(++item.visited_nodes>256){item.truncated=true;return;}
          if(node.nodeType===3){const owner=node.parentElement;if(!owner||!visible(owner))return;item.text_node_count++;if(item.text_nodes.length>=64){item.truncated=true;return;}
            // Do not read input values, hidden text or editable content. The
            // enclosing first-five source TD was already semantically verified.
            let unsafe=false;for(let n=owner;n;n=n.parentElement){if(['INPUT','TEXTAREA','SELECT','IFRAME','SCRIPT','STYLE'].includes(n.tagName)||['textbox','combobox','searchbox'].includes(n.getAttribute?.('role'))||n.isContentEditable||n.hasAttribute?.('contenteditable'))unsafe=true;if(n===el)break;}if(unsafe){item.unsupported_public_text_context=true;return;}
            const publicText=String(node.nodeValue??''),length=publicText.length;if(!length||!publicText.trim())return;const entry={owner_selector:addElement(owner),child_index:[...(owner.childNodes||[])].indexOf(node),text_length:length,rects:[],range_count:0,ranges_truncated:false,clipping_ancestors:[],ancestors_truncated:false};
            for(let n=owner;n;n=n.parentElement){const s=getComputedStyle(n);if(['hidden','clip','auto','scroll'].includes(s.overflowX)||['hidden','clip','auto','scroll'].includes(s.overflowY)){if(entry.clipping_ancestors.length>=8){entry.ancestors_truncated=true;item.truncated=true;break;}entry.clipping_ancestors.push({selector:addElement(n),ellipsis_declaration:s.textOverflow==='ellipsis'||/^[1-9][0-9]*$/.test(String(s.webkitLineClamp))});}if(n===el)break;}
            if(length>16000){entry.unavailable='public-text-length-limit';item.truncated=true;}
            else if(item.range_api_available){let range;try{range=document.createRange();range.selectNodeContents(node);const rects=range.getClientRects(),count=rects.length;entry.range_count=count;entry.ranges_truncated=count>8;item.range_count+=count;if(entry.ranges_truncated)item.truncated=true;entry.rects=Array.from({length:Math.min(count,8)},(_,i)=>diagnosticRect(rects[i]));}catch{entry.unavailable='public-range-read-failed';}finally{range?.detach?.();}}
            item.text_nodes.push(entry);return;
          }
          if(node.nodeType!==1||['INPUT','TEXTAREA','SELECT','IFRAME','SCRIPT','STYLE','SVG','IMG'].includes(node.tagName)||['textbox','combobox','searchbox'].includes(node.getAttribute?.('role'))||node.isContentEditable||node.hasAttribute?.('contenteditable'))return;
          for(const child of node.childNodes||[]){if(item.visited_nodes>=256){item.truncated=true;break;}visit(child);}
        };
        visit(el);item.elements=[...elements.values()];result.truncated=result.truncated||item.truncated;result.text_cells.push(item);
      }
      return result;
    }catch{return {...result,unavailable:'bounded-public-diagnostic-unavailable'};}
  }
  const PARTIAL_CELL='partial-cell-original-clip-preview-v1';
  // Separate preview proof: never changes businessGeometry or full eligibility.
  function partialCellPreviews(rows,one,view){
    const previews=[],inspections=[];
    const box=r=>{const v={left:r.left,top:r.top,right:r.right,bottom:r.bottom};v.width=v.right-v.left;v.height=v.bottom-v.top;need(Object.values(v).every(Number.isFinite)&&v.width>0&&v.height>0,'partial-invalid-box');return v;};
    const intersection=(a,b)=>box({left:Math.max(a.left,b.left),top:Math.max(a.top,b.top),right:Math.min(a.right,b.right),bottom:Math.min(a.bottom,b.bottom)});
    const visible=n=>{const s=getComputedStyle(n);return s.display!=='none'&&!['hidden','collapse'].includes(s.visibility)&&s.contentVisibility!=='hidden'&&Number(s.opacity)!==0&&!(typeof n.checkVisibility==='function'&&!n.checkVisibility({contentVisibilityAuto:true,opacityProperty:true,visibilityProperty:true}));};
    const absent=v=>!v||v==='none',transparent=v=>!v||v==='transparent'||/^rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(v);
    let shadowContext=null;
    function outerAncestorShadow(n,s){
      // W3C css-backgrounds-3 §6.1.1: outer shadows are knocked out inside
      // the border box. The safe rectangle additionally excludes all corners
      // and borders; no shadow pixels are removed or classified as no-paint.
      const expected='rgba(0, 104, 173, 0.04) -8px 0px 40px 0px';
      if(!shadowContext||n.tagName!=='SECTION'||diagnosticSelector(n)!=='#main-app > section > section'||s.boxShadow!==expected||!shadowContext.elements.every(el=>n!==el&&n.contains(el)))return null;
      const rects=[...n.getClientRects()];if(rects.length!==1)return null;const bounds=box(rects[0]),radii={},borders={},px=v=>typeof v==='string'&&/^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px$/.test(v)?Number.parseFloat(v):NaN;
      for(const corner of ['TopLeft','TopRight','BottomRight','BottomLeft']){const raw=s['border'+corner+'Radius'],parts=typeof raw==='string'?raw.trim().split(/\s+/):[];if(![1,2].includes(parts.length))return null;const values=parts.map(px);if(!values.every(Number.isFinite))return null;radii[corner]={raw,x:values[0],y:values[1]??values[0]};}
      for(const side of ['Top','Right','Bottom','Left']){const raw=s['border'+side+'Width'],width=px(raw);if(!Number.isFinite(width))return null;borders[side]={raw,width};}
      const safe=box({left:bounds.left+Math.max(radii.TopLeft.x,radii.BottomLeft.x,borders.Left.width),right:bounds.right-Math.max(radii.TopRight.x,radii.BottomRight.x,borders.Right.width),top:bounds.top+Math.max(radii.TopLeft.y,radii.TopRight.y,borders.Top.width),bottom:bounds.bottom-Math.max(radii.BottomLeft.y,radii.BottomRight.y,borders.Bottom.width)});
      if(!shadowContext.elements.every(el=>contained(box(el.getBoundingClientRect()),safe))||typeof n.getAnimations!=='function')return null;
      const animations=n.getAnimations();if(animations.length>8||animations.some(a=>a.pending===true||!['finished','idle'].includes(a.playState)))return null;
      const otherEffects=Object.fromEntries(['transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','backdropFilter','borderImageSource','mixBlendMode','webkitBoxReflect','textShadow','outlineStyle','outlineWidth'].map(k=>[k,String(s[k]??'')]));
      return {other_public_effects:otherEffects,animations:animations.map(a=>({pending:a.pending===true,play_state:String(a.playState)})),classification:'observed-outer-ancestor-shadow-outside-business-crop-v1',selector:diagnosticSelector(n),tag:'section',box_shadow:s.boxShadow,inset:false,bounds,radii,borders,safe_box:safe,contains_all_five_raw_cells:true,original_pixels_preserved:true,visual_review_required:true};
    }
    function safeStyle(n){const s=getComputedStyle(n),unsupported=unsupportedStyle(s,n),ancestorShadow=absent(s.boxShadow)?null:outerAncestorShadow(n,s);const bounded=!unsupported&&absent(s.backdropFilter)&&absent(s.borderImageSource)&&(!s.mixBlendMode||s.mixBlendMode==='normal')&&absent(s.webkitBoxReflect)&&(absent(s.boxShadow)||Boolean(ancestorShadow))&&absent(s.textShadow)&&(!s.outlineStyle||s.outlineStyle==='none'||s.outlineWidth==='0px');
      if(!bounded){
        // Diagnostic only, after preserving the exact original guard result.
        // No text/value/class lookup or geometry/action is added here.
        const fields=['transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','backdropFilter','borderImageSource','mixBlendMode','webkitBoxReflect','boxShadow','textShadow','outlineStyle','outlineWidth'];
        const clean=v=>String(v??'').replace(/url\([^)]*\)/gi,'url(<uri-omitted>)').slice(0,240),style=Object.fromEntries(fields.map(k=>[k,clean(s[k])])),truncated_fields=fields.filter(k=>String(s[k]??'').length>240);
        const failed={transform:Boolean(s.transform&&s.transform!=='none'),zoom:Boolean(s.zoom&&!['1','normal'].includes(String(s.zoom))),clip:Boolean(s.clip&&s.clip!=='auto'),clipPath:Boolean(s.clipPath&&s.clipPath!=='none'),maskImage:Boolean(s.maskImage&&s.maskImage!=='none'),webkitMaskImage:Boolean(s.webkitMaskImage&&s.webkitMaskImage!=='none'),filter:Boolean(s.filter&&s.filter!=='none'),opacity:s.opacity!==undefined&&Number(s.opacity)!==1,backdropFilter:!absent(s.backdropFilter),borderImageSource:!absent(s.borderImageSource),mixBlendMode:Boolean(s.mixBlendMode&&s.mixBlendMode!=='normal'),webkitBoxReflect:!absent(s.webkitBoxReflect),boxShadow:!absent(s.boxShadow),textShadow:!absent(s.textShadow),outline:!(!s.outlineStyle||s.outlineStyle==='none'||s.outlineWidth==='0px')};
        let animation={api_available:typeof n.getAnimations==='function',sampled_after_original_rejection:true,states:[],count:0,active_or_pending_count:0,truncated:false};
        if(animation.api_available)try{const all=n.getAnimations();animation.count=all.length;animation.truncated=all.length>8;animation.states=all.slice(0,8).map(a=>({pending:a.pending===true,play_state:clean(a.playState)}));animation.active_or_pending_count=animation.states.filter(a=>a.pending||!['finished','idle'].includes(a.play_state)).length;animation.active_or_pending_count_semantics='bounded-sample-only';}catch{animation.unavailable='public-animation-read-failed';}
        failed.sampled_active_or_pending_animation=animation.active_or_pending_count>0;
        const error=Error('partial-unbounded-effect');error.public_effect_diagnostic={schema:'partial-cell-public-effect-diagnostic-v1',selector:diagnosticSelector(n),tag:String(n.tagName||'').toLowerCase().slice(0,32),style,truncated_fields,original_guard_rejected:true,original_unsupported_style_rejected:unsupported,failed_conditions:failed,animation,geometry_decision_changed:false};throw error;
      }
      if(ancestorShadow)shadowContext.preserved.set(ancestorShadow.selector,ancestorShadow);
      for(const pseudo of ['::before','::after']){const p=getComputedStyle(n,pseudo);need(!p.content||['none','normal'].includes(p.content)||p.display==='none'||p.visibility==='hidden'||Number(p.opacity)===0,'partial-generated-paint');}return s;}
    for(const row of rows){
      if(row.cells.every(c=>c.geometry.evidence_eligible)||!row.cells.every(c=>c.geometry.rendered&&c.geometry.unsupported_css_absent))continue;
      const inspection={notice_id:row.notice_id,contract:PARTIAL_CELL,accepted:false};
      try{
        need(row.cells.length===5&&row.cells.every((c,i)=>c.index===i),'partial-five-source-cells');const elements=row.cells.map(c=>one({by:'selector',value:c.selector}));shadowContext={elements,preserved:new Map()};
        const parents=elements.map(el=>{const a=[];for(let n=el.parentElement;n;n=n.parentElement)if(n.tagName==='DIV'&&n.getAttribute('class')==='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable')a.push(n);need(a.length===1,'partial-table-container-not-unique');return a[0];});
        need(parents.every(n=>n===parents[0]),'partial-container-mismatch');const parent=parents[0],ps=safeStyle(parent),pr=box(parent.getBoundingClientRect());
        need(absent(ps.backgroundImage)&&ps.overflowX==='auto'&&ps.overflowY==='auto'&&parent.clientTop===0&&parent.clientLeft===0&&['borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','paddingTop','paddingRight','paddingBottom','paddingLeft'].every(k=>ps[k]==='0px'),'partial-container-structure');
        need(Number.isInteger(parent.clientHeight)&&parent.clientHeight===parent.offsetHeight&&parent.scrollHeight===parent.clientHeight&&Math.abs(pr.height-parent.clientHeight)<=.5&&Math.abs(pr.width-parent.clientWidth)<=.5,'partial-container-rounding-unproven');
        const cells=[];let textCount=0,paintCount=0;
        for(let i=0;i<5;i++){
          const source=row.cells[i],el=elements[i];inspection.current_cell={index:i,selector:source.selector};const raw=box(el.getBoundingClientRect()),style=safeStyle(el);need(el.tagName==='TD'&&contained(raw,view),'partial-cell-outside-viewport');let clip=raw;const clips=[];
          for(let n=el.parentElement;n;n=n.parentElement){const s=safeStyle(n),r=n.getBoundingClientRect();if(['hidden','clip','auto','scroll'].includes(s.overflowX)||['hidden','clip','auto','scroll'].includes(s.overflowY)){
            const b=overflowClipBox(n,s,r,true),v={left:raw.left,top:raw.top,right:raw.right,bottom:raw.bottom};
            if(['hidden','clip','auto','scroll'].includes(s.overflowX)){v.left=b.left;v.right=b.right;}if(['hidden','clip','auto','scroll'].includes(s.overflowY)){v.top=b.top;v.bottom=b.bottom;}
            clip=intersection(clip,v);clips.push({selector:diagnosticSelector(n),box:box(v)});
          }}
          need(clip.left===raw.left&&clip.right===raw.right&&clip.top===raw.top&&clip.bottom<raw.bottom&&raw.bottom-clip.bottom<=.5,'partial-only-original-bottom-strip');
          need(clips.some(c=>c.selector===diagnosticSelector(parent)&&c.box.bottom===clip.bottom),'partial-not-observed-container-clip');
          const nodes=[el,...el.querySelectorAll('*')];need(nodes.length<=160,'partial-node-limit');const text=[],paint=[],structural=[],labelClips=[],supportedClips=[];
          const nodeSelector=n=>n===el?source.selector:diagnosticSelector(n);
          function activeEllipsis(n){const s=getComputedStyle(n);return (n.scrollWidth>n.clientWidth||n.scrollHeight>n.clientHeight)&&(s.textOverflow==='ellipsis'||/^[1-9][0-9]*$/.test(String(s.webkitLineClamp)))&&[s.overflowX,s.overflowY].includes('hidden');}
          function knownLabel(owner,t,r){
            const parent=owner.parentElement,tagClass='governance_merchant-tag governance_merchant-tag-size-sm governance_merchant-tag-default-light tag-pd6WUO';
            if(i!==2||owner.tagName!=='SPAN'||owner.getAttribute('class')!==tagClass||parent?.getAttribute('class')!=='title-AbHLxL'||owner.children.length||String(t.nodeValue)!=='商品'||[...owner.childNodes].filter(n=>n.nodeType===3&&String(n.nodeValue).trim()).length!==1||owner.scrollWidth!==owner.clientWidth||owner.scrollHeight!==owner.clientHeight)return null;
            const own=box(owner.getBoundingClientRect());if(!contained(r,own)||r.left<raw.left||r.left>=raw.right||r.right<=raw.right||r.top<clip.top||r.bottom>clip.bottom||style.overflowX!=='hidden'||style.overflowY!=='hidden')return null;
            const siblings=[...parent.children];if(siblings.length!==2||siblings[0].getAttribute('class')!=='overhide-dQaf8m'||siblings[1]!==owner||!activeEllipsis(siblings[0]))return null;
            let firstChar;const first=document.createRange();try{first.setStart(t,0);first.setEnd(t,1);const rs=[...first.getClientRects()];need(rs.length===1&&contained(rs[0],clip),'partial-label-prefix-not-visible');firstChar=box(rs[0]);}finally{first.detach?.();}
            return {classification:'platform-original-clipped-product-label-v1',selector:nodeSelector(owner),text:'商品',range:r,owner_box:own,visible_box:intersection(r,clip),clipping_cell:source.selector,first_character_range:firstChar,own_ellipsis_active:false,text_complete_in_image:false,original_pixels_preserved:true};
          }
          for(const n of nodes){
            if(!visible(n))continue;inspection.current_public_node={selector:nodeSelector(n),tag:n.tagName};need(!['INPUT','TEXTAREA','SELECT','IFRAME','CANVAS','VIDEO','SCRIPT','STYLE'].includes(n.tagName)&&!n.isContentEditable&&!n.hasAttribute?.('contenteditable')&&!['textbox','combobox','searchbox'].includes(n.getAttribute?.('role')),'partial-unsafe-node');const s=safeStyle(n),nr=n.getBoundingClientRect(),selector=nodeSelector(n);if(!(nr.width>0&&nr.height>0)){need(!String(n.innerText||'').trim()&&!['IMG','SVG'].includes(n.tagName),'partial-empty-business-box');continue;}const r=box(nr);
            const borders=Object.fromEntries(['Top','Right','Bottom','Left'].map(side=>[side.toLowerCase(),{width:s['border'+side+'Width']||'0px',style:s['border'+side+'Style']||'none',color:s['border'+side+'Color']||''}]));
            const isLabel=n.tagName==='SPAN'&&n.getAttribute('class')==='governance_merchant-tag governance_merchant-tag-size-sm governance_merchant-tag-default-light tag-pd6WUO'&&i===2;
            if(n===el){need(absent(s.backgroundImage),'partial-cell-background-image');for(const b of Object.values(borders))need(b.style==='none'||b.width==='0px'||b.style==='solid'&&Number.isFinite(devicePixelRatio)&&devicePixelRatio>=.25&&devicePixelRatio<=16&&/^\d+(?:\.\d{1,6})?px$/.test(b.width)&&parseFloat(b.width)*devicePixelRatio<=1+.5e-6*devicePixelRatio+1e-12,'partial-cell-structural-border');structural.push({selector,classification:'cropped-uniform-cell-background-and-border',background_color:s.backgroundColor||'transparent',borders,omitted_bottom_css_px:raw.bottom-clip.bottom});}
            else if(!transparent(s.backgroundColor)||!absent(s.backgroundImage)||Object.values(borders).some(b=>b.style!=='none'&&b.width!=='0px')){need(contained(r,clip)||isLabel&&r.top>=clip.top&&r.bottom<=clip.bottom&&r.left>=clip.left,'partial-descendant-paint-lost');paint.push({selector,kind:isLabel?'platform-label-background':'CSS-box',bounds:r,original_clip:isLabel&&!contained(r,clip)});}
            if(['IMG','SVG'].includes(n.tagName)){need(contained(r,clip),'partial-image-paint-lost');paint.push({selector,kind:n.tagName,bounds:r});if(n.tagName==='IMG')need(n.complete===true&&n.naturalWidth>0&&n.naturalHeight>0,'partial-image-not-loaded');}
            if(n.tagName==='SVG'||n.closest?.('svg')){let paintedBox=r;if(s.stroke&&s.stroke!=='none'&&s.stroke!=='transparent'){need(/^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px$/.test(s.strokeWidth)&&Number.isFinite(Number(s.strokeMiterlimit))&&Number(s.strokeMiterlimit)>=1&&Number(s.strokeMiterlimit)<=1000&&(!s.vectorEffect||s.vectorEffect==='none'),'partial-svg-stroke-unknown');const d=parseFloat(s.strokeWidth)*Math.max(2,Number(s.strokeMiterlimit));paintedBox=box({left:r.left-d,top:r.top-d,right:r.right+d,bottom:r.bottom+d});}need(contained(paintedBox,clip),'partial-svg-paint-lost');if(n.tagName!=='SVG')paint.push({selector,kind:'SVG-descendant',bounds:paintedBox});continue;}
            for(const t of n.childNodes||[]){if(t.nodeType!==3)continue;const value=String(t.nodeValue??'');if(!value.trim())continue;need(value.length<=16000&&++textCount<=128,'partial-text-limit');let range;try{range=document.createRange();range.selectNodeContents(t);const rs=[...range.getClientRects()];need(rs.length>0&&rs.length<=8,'partial-text-ranges');for(const original of rs){let r=box(original);const label=knownLabel(n,t,r);if(label){labelClips.push(label);r=label.visible_box;}else for(let a=n;a&&a!==el;a=a.parentElement){if(activeEllipsis(a)){const as=getComputedStyle(a),ab=overflowClipBox(a,as,a.getBoundingClientRect(),true);r=intersection(r,ab);supportedClips.push(nodeSelector(a));}}
              inspection.last_public_text_range={owner_selector:selector,original_range:box(original),visible_range:r,cell_visible_box:clip};need(contained(r,clip),'partial-business-text-lost');for(let a=n;a&&a!==el;a=a.parentElement){const as=getComputedStyle(a),ab=overflowClipBox(a,as,a.getBoundingClientRect(),true);need(!(['hidden','clip','auto','scroll'].includes(as.overflowX)&&(r.left<ab.left||r.right>ab.right))&&!(['hidden','clip','auto','scroll'].includes(as.overflowY)&&(r.top<ab.top||r.bottom>ab.bottom)),'partial-unexplained-inner-text-clip');}
              text.push({owner_selector:selector,child_index:[...n.childNodes].indexOf(t),text_length:value.length,original_range:box(original),visible_range:r,classification:label?'platform-original-clipped-label':contained(original,r)?'unclipped':'active-own-ellipsis'});
            }}finally{range?.detach?.();}}
          }
          need(text.length>0&&paintCount+paint.length<=128,'partial-no-text-or-paint-limit');paintCount+=paint.length;
          // The only unsupported text overflow allowed is the source object TD
          // containing the separately measured 商品 fragment; it is NOT ellipsis.
          for(const c of source.geometry.text_clips)need(c.supported||i===2&&c.selector===source.selector&&labelClips.length===1,'partial-unexplained-text-overflow');
          need(labelClips.length<=1&&paint.filter(p=>p.original_clip).every(p=>labelClips.some(l=>l.selector===p.selector)),'partial-label-not-unique-or-unproven');cells.push({index:i,field:source.field,selector:source.selector,raw_box:raw,visible_box:clip,ancestor_clips:clips,omitted_bottom_css_px:raw.bottom-clip.bottom,text_ranges:text,paint_bounds:paint,structural_omissions:structural,platform_label_clips:labelClips,supported_ellipsis_selectors:[...new Set(supportedClips)],text_complete_in_image:false});
        }
        need(cells.every(c=>c.visible_box.bottom===cells[0].visible_box.bottom),'partial-row-bottom-mismatch');
        const proof={contract:PARTIAL_CELL,notice_id:row.notice_id,tr_selector:row.tr_selector,container_selector:diagnosticSelector(parent),device_pixel_ratio:devicePixelRatio,container_metrics:{...diagnosticMetrics(parent),offsetHeight:parent.offsetHeight,offsetWidth:parent.offsetWidth},...(shadowContext.preserved.size?{preserved_ancestor_shadows:[...shadowContext.preserved.values()]}:{}),cells,original_full_flags_unchanged:true,quality_review_required:true,text_unclipped:false,original_pixels_preserved:true};previews.push(proof);inspection.accepted=true;delete inspection.current_cell;delete inspection.current_public_node;delete inspection.last_public_text_range;
      }catch(e){inspection.reason=String(e.message||e).slice(0,160);if(e.public_effect_diagnostic)inspection.effect_diagnostic=e.public_effect_diagnostic;}inspections.push(inspection);
    }
    return {partial_cell_previews:previews,partial_cell_inspections:inspections};
  }

  // Comprehensive inspection of already source-verified, viewport-contained
  // candidate TDs. Pure measurements only: this never certifies paint or relaxes
  // partial/full eligibility. Pseudo boxes deliberately remain unresolved.
  function businessPaintInspection(rows,one,view){
    const limits={rows:3,elements:200,text_nodes:160,ranges_per_text:16,ancestors_per_cell:16,text_length:16000,style_value_chars:240,serialized_chars:4000000};
    const result={schema:'source-business-cell-paint-inspection-v1',purpose:'readonly-diagnostic-not-capture-certification',capture_certified:false,geometry_decision_changed:false,pixel_input_actions:false,coordinate_space:'CSS-viewport-diagnostic-only',limits,candidate_count:0,rows:[],elements:[],text_nodes:[],failures:[],truncated:false};
    const fields=['content','display','visibility','contentVisibility','opacity','position','inset','top','right','bottom','left','width','height','minWidth','maxWidth','minHeight','maxHeight','boxSizing','marginTop','marginRight','marginBottom','marginLeft','paddingTop','paddingRight','paddingBottom','paddingLeft','borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','borderTopStyle','borderRightStyle','borderBottomStyle','borderLeftStyle','borderTopColor','borderRightColor','borderBottomColor','borderLeftColor','borderTopLeftRadius','borderTopRightRadius','borderBottomRightRadius','borderBottomLeftRadius','borderImageSource','borderImageOutset','borderImageWidth','borderImageSlice','backgroundColor','backgroundImage','backgroundRepeat','backgroundPosition','backgroundSize','backgroundClip','backgroundOrigin','backgroundAttachment','filter','backdropFilter','boxShadow','textShadow','outlineStyle','outlineWidth','outlineOffset','transform','transformOrigin','zoom','clip','clipPath','maskImage','webkitMaskImage','webkitBoxReflect','overflowX','overflowY','contain','isolation','mixBlendMode','zIndex','pointerEvents','textOverflow','webkitLineClamp','whiteSpace','lineHeight','fontSize','letterSpacing','verticalAlign','willChange','animationName','animationDuration','animationPlayState','transitionProperty','transitionDuration'];
    const cache=new Map(),registered=new Map();let textCount=0;
    const truncated=why=>{result.truncated=true;if(!result.limit_reasons)result.limit_reasons=[];if(!result.limit_reasons.includes(why))result.limit_reasons.push(why);};
    const fail=(code,detail)=>{if(result.failures.length<400)result.failures.push({code,...detail});else truncated('failure-list');};
    function style(n,pseudo){let c=cache.get(n);if(!c){c={};cache.set(n,c);}const key=pseudo||'element';if(!(key in c))c[key]=getComputedStyle(n,pseudo);return c[key];}
    function css(s){const values={},uri_omitted_fields=[],truncated_fields=[];for(const k of fields){const raw=String(s[k]??'');if(/url\s*\(|\b(?:https?:|data:|blob:|file:|chrome-extension:)/i.test(raw)){values[k]='<CSS URI value omitted>';uri_omitted_fields.push(k);}else values[k]=raw.slice(0,limits.style_value_chars);if(raw.length>limits.style_value_chars)truncated_fields.push(k);}return {values,uri_omitted_fields,truncated_fields};}
    const isVisible=n=>{for(let p=n;p;p=p.parentElement){const s=style(p);if(s.display==='none'||['hidden','collapse'].includes(s.visibility)||s.contentVisibility==='hidden'||Number(s.opacity)===0)return false;}return !(typeof n.checkVisibility==='function'&&!n.checkVisibility({contentVisibilityAuto:true,opacityProperty:true,visibilityProperty:true}));};
    const unsafe=n=>['INPUT','TEXTAREA','SELECT','IFRAME','SCRIPT','STYLE'].includes(n.tagName)||n.isContentEditable||n.hasAttribute?.('contenteditable')||['textbox','combobox','searchbox'].includes(n.getAttribute?.('role'));
    function node(n,relation){
      if(registered.has(n))return registered.get(n).selector;
      if(registered.size>=limits.elements){truncated('elements');return null;}
      const selector=diagnosticSelector(n),s=style(n),item={selector,tag:String(n.tagName||'').toLowerCase(),relation,rect:diagnosticRect(n.getBoundingClientRect()),client_rects:[...n.getClientRects()].slice(0,16).map(diagnosticRect),metrics:Object.fromEntries(['clientLeft','clientTop','clientWidth','clientHeight','scrollWidth','scrollHeight','scrollLeft','scrollTop','offsetWidth','offsetHeight'].map(k=>[k,Number.isFinite(n[k])?n[k]:null])),style:css(s),pseudo:{},animations:{api_available:typeof n.getAnimations==='function',states:[],count:0,truncated:false}};
      for(const pseudo of ['::before','::after']){try{const p=style(n,pseudo),generated=!!p.content&&!['none','normal'].includes(p.content)&&p.display!=='none'&&p.visibility!=='hidden'&&Number(p.opacity)!==0;item.pseudo[pseudo]={...css(p),generated_under_original_guard:generated,actual_bounds_available:false,paint_bounds_status:'unresolved-pseudo-element'};if(generated)fail('original-generated-paint-guard',{selector,pseudo});}catch{item.pseudo[pseudo]={unavailable:'public-pseudo-style-read-failed'};fail('pseudo-style-unavailable',{selector,pseudo});}}
      if(item.animations.api_available)try{const all=n.getAnimations();item.animations.count=all.length;item.animations.truncated=all.length>8;item.animations.states=all.slice(0,8).map(a=>({pending:a.pending===true,play_state:String(a.playState||'').slice(0,32)}));}catch{item.animations.unavailable='public-animation-read-failed';}
      const effectKeys=['transform','filter','backdropFilter','clipPath','maskImage','webkitMaskImage','borderImageSource','webkitBoxReflect','boxShadow','textShadow'];for(const k of effectKeys)if(s[k]&&s[k]!=='none')fail('public-effect-present',{selector,field:k});
      registered.set(n,item);result.elements.push(item);return selector;
    }
    try{
      const candidates=[];
      for(const row of rows){if(row.cells.length!==5||row.cells.every(c=>c.geometry.evidence_eligible)||!row.cells.every(c=>c.geometry.rendered))continue;const es=row.cells.map(c=>one({by:'selector',value:c.selector}));if(es.every(e=>[...e.getClientRects()].length===1&&contained(e.getBoundingClientRect(),view)))candidates.push({row,es});}
      result.candidate_count=candidates.length;if(candidates.length>limits.rows)truncated('rows');
      for(const {row,es} of candidates.slice(0,limits.rows)){
        const r={notice_id:row.notice_id,tr_selector:row.tr_selector,cells:[]};result.rows.push(r);
        for(let index=0;index<5;index++){
          const el=es[index],source=row.cells[index],cell={index,field:source.field,selector:source.selector,raw_box:diagnosticRect(el.getBoundingClientRect()),element_selectors:[],ancestor_selectors:[],paint_bounds:[],text_indices:[],complete:true};r.cells.push(cell);
          const ancestors=[];for(let a=el.parentElement;a;a=a.parentElement){if(ancestors.length>=limits.ancestors_per_cell){truncated('ancestors');cell.complete=false;break;}ancestors.push(a);const key=node(a,'candidate-cell-ancestor-CSS-only');if(key)cell.ancestor_selectors.push(key);else cell.complete=false;}
          const nodes=[],pending=[el];let visited=0;
          while(pending.length&&visited<160){const n=pending.pop();visited++;if(unsafe(n)){fail('unsafe-text-context-excluded',{selector:diagnosticSelector(n),cell:source.selector});continue;}if(!isVisible(n))continue;nodes.push(n);const children=n.children||[];for(let j=Math.min(children.length,160)-1;j>=0;j--)pending.push(children[j]);if(children.length>160){truncated('direct-children');cell.complete=false;}}
          if(pending.length){truncated('nodes-per-cell');cell.complete=false;}
          for(const n of nodes){
            // No text/value reads from controls, hidden/editable branches or
            // outside the five verified business cells. Ancestors are CSS only.
            let bad=false;for(let a=n;a;a=a.parentElement){if(unsafe(a)){bad=true;break;}if(a===el)break;}if(bad){fail('unsafe-text-context-excluded',{selector:diagnosticSelector(n),cell:source.selector});continue;}if(!isVisible(n))continue;
            const selector=node(n,'candidate-business-cell-or-descendant');if(!selector){cell.complete=false;continue;}cell.element_selectors.push(selector);const s=style(n),nr=diagnosticRect(n.getBoundingClientRect());
            if(['IMG','SVG','CANVAS','VIDEO'].includes(n.tagName))cell.paint_bounds.push({selector,kind:n.tagName,bounds:nr,...(n.tagName==='IMG'?{complete:n.complete===true,natural_width:n.naturalWidth,natural_height:n.naturalHeight}:{}),bounds_complete_paint_claimed:false});
            if(['SVG','PATH','G','IMG','CANVAS','VIDEO'].includes(n.tagName)||n.closest?.('svg'))continue;
            const direct=n.childNodes||[];if(direct.length>160){truncated('direct-text-children');cell.complete=false;}for(let ti=0;ti<Math.min(direct.length,160);ti++){const t=direct[ti];if(t.nodeType!==3)continue;const value=String(t.nodeValue??'');if(!value.trim())continue;if(++textCount>limits.text_nodes){truncated('text-nodes');cell.complete=false;break;}const entry={cell:source.selector,owner_selector:selector,child_index:ti,text_length:value.length,rects:[],clips:[],text_values_returned:false};cell.text_indices.push(result.text_nodes.length);result.text_nodes.push(entry);
              if(value.length>limits.text_length){entry.unavailable='public-text-length-limit';cell.complete=false;truncated('text-length');continue;}let range;try{range=document.createRange();range.selectNodeContents(t);const rs=[...range.getClientRects()];entry.range_count=rs.length;if(rs.length>limits.ranges_per_text){truncated('text-ranges');cell.complete=false;}entry.rects=rs.slice(0,limits.ranges_per_text).map(diagnosticRect);
                const chain=[];for(let a=n;a;a=a.parentElement){if(chain.length>=limits.ancestors_per_cell){truncated('text-ancestors');cell.complete=false;break;}chain.push(a);if(a===ancestors.at(-1))break;}
                for(const a of chain){const as=style(a);if(!['hidden','clip','auto','scroll'].includes(as.overflowX)&&!['hidden','clip','auto','scroll'].includes(as.overflowY))continue;const b=overflowClipBox(a,as,a.getBoundingClientRect(),true),selector=diagnosticSelector(a);entry.clips.push({selector,box:b,overflow_x:as.overflowX,overflow_y:as.overflowY,ellipsis_declaration:as.textOverflow==='ellipsis'||/^[1-9][0-9]*$/.test(String(as.webkitLineClamp)),own_scroll_width:a.scrollWidth,own_client_width:a.clientWidth,own_scroll_height:a.scrollHeight,own_client_height:a.clientHeight});
                  for(const rect of entry.rects)if(['hidden','clip','auto','scroll'].includes(as.overflowX)&&(rect.left<b.left||rect.right>b.right)||['hidden','clip','auto','scroll'].includes(as.overflowY)&&(rect.top<b.top||rect.bottom>b.bottom))fail('public-text-range-clip',{cell:source.selector,owner_selector:entry.owner_selector,ancestor_selector:selector,range:rect,clip_box:b});}
                for(const rect of entry.rects){if(!contained(rect,cell.raw_box))fail('public-text-range-outside-own-cell',{cell:source.selector,owner_selector:selector,range:rect});if(!contained(rect,view))fail('public-text-range-outside-viewport',{cell:source.selector,owner_selector:selector,range:rect});}
              }catch{entry.unavailable='public-range-read-failed';cell.complete=false;fail('text-range-unavailable',{selector,cell:source.selector});}finally{range?.detach?.();}
            }
          }
          for(const p of cell.paint_bounds)if(!contained(p.bounds,cell.raw_box)||!contained(p.bounds,view))fail('image-or-SVG-bounds-outside-cell-or-viewport',{cell:source.selector,...p});
        }
      }
    }catch{result.unavailable='bounded-source-business-paint-inspection-failed';result.truncated=true;}
    if(JSON.stringify(result).length>limits.serialized_chars){result.elements=[];result.text_nodes=[];result.failures=[];for(const row of result.rows)for(const c of row.cells){c.element_selectors=[];c.text_indices=[];c.complete=false;}truncated('serialized-payload');}
    return result;
  }

  function manualCellPreviews(rows,one,view){
    const out=[];
    for(const row of rows){
      const cells=[];
      for(const cell of row.cells){
        const el=one({by:'selector',value:cell.selector}),raw=el.getBoundingClientRect();
        if(!cell.geometry.rendered||!cell.geometry.unsupported_css_absent||raw.left<view.left||raw.right>view.right)break;
        let visible={left:Math.max(raw.left,view.left),top:Math.max(raw.top,view.top),right:Math.min(raw.right,view.right),bottom:Math.min(raw.bottom,view.bottom)};const clips=[];
        for(let a=el.parentElement;a;a=a.parentElement){const st=getComputedStyle(a);if(['hidden','clip','scroll','auto'].includes(st.overflowX)||['hidden','clip','scroll','auto'].includes(st.overflowY)){const b=overflowClipBox(a,st,a.getBoundingClientRect());if(['hidden','clip','scroll','auto'].includes(st.overflowX)){visible.left=Math.max(visible.left,b.left);visible.right=Math.min(visible.right,b.right);}if(['hidden','clip','scroll','auto'].includes(st.overflowY)){visible.top=Math.max(visible.top,b.top);visible.bottom=Math.min(visible.bottom,b.bottom);}clips.push({selector:diagnosticSelector(a),box:b,overflow_x:st.overflowX,overflow_y:st.overflowY});}need(clips.length<=32,'manual-preview-clip-bound');}
        if(!(visible.left<visible.right&&visible.top<visible.bottom))break;
        const box=r=>({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.right-r.left,height:r.bottom-r.top});
        cells.push({index:cell.index,field:cell.field,selector:cell.selector,raw_box:box(raw),visible_box:box(visible),ancestor_clips:clips,text_complete_in_image:false});
      }
      if(cells.length===5)out.push({contract:'manual-local-business-preview-v2',notice_id:row.notice_id,tr_selector:row.tr_selector,cells,original_full_flags_unchanged:true,decorative_paint:'unresolved',quality_review_required:true,coverage_certified:false});
    }
    return out;
  }
  function businessEvidence(cmd,one,readTree,view){
    const tree=readTree(),ns=treeNodes(tree.root),manual=cmd.elements.every(e=>e.key.startsWith(MANUAL_CONTRACT+':')),projection=governanceProjection(tree,cmd.groupid,manual?location.href:null,commandProjection(cmd)),rows=[],headers=[];
    for(let i=0;i<5;i++){
      const th=govOne(ns.filter(n=>n.tag==='th'&&n.role==='columnheader'&&n.name===GOV_HEADERS[i]),'business-header');
      const label=govOne(treeNodes(th).filter(n=>classes(n).includes('governance_merchant-Table-HeadCellContentTitle')),'business-header-label');need(!(label.children||[]).length&&label.name===GOV_HEADERS[i],'business-header-label-not-exact-leaf');
      const el=one({by:'selector',value:label.selector}),thEl=one({by:'selector',value:th.selector});need(thEl.tagName==='TH'&&thEl.contains(el)&&el.classList?.contains('governance_merchant-Table-HeadCellContentTitle')&&String(el.innerText||'').replace(/\s+/g,' ').trim()===label.name,'business-live-header-label-changed');
      headers.push({field:GOV_HEADERS[i],th_selector:th.selector,selector:label.selector,text:label.name,text_selectors:[label.selector],geometry:businessGeometry(el,view,false)});
    }
    for(const [selector,text] of projection.rowTexts){
      const tr=govOne(ns.filter(n=>n.selector===selector),'business-row'),el=one({by:'selector',value:selector}),live=Array.from(el.children||[]);need(el.tagName==='TR'&&live.length===10&&live.every(n=>n.tagName==='TD'),'business-live-ten-direct-cells');
      const id=JSON.parse(text)[0],boxes=live.slice(0,5).map(c=>c.getBoundingClientRect()),union={left:Math.min(...boxes.map(b=>b.left)),top:Math.min(...boxes.map(b=>b.top)),right:Math.max(...boxes.map(b=>b.right)),bottom:Math.max(...boxes.map(b=>b.bottom))},cells=tr.children.slice(0,5).map((cell,i)=>{
        const c=one({by:'selector',value:cell.selector});need(live[i]===c&&c.getAttribute('role')==='cell'&&String(c.innerText||'').replace(/\s+/g,' ').trim()===cell.name,'business-live-cell-order-or-text-changed');
        return {index:i,field:BUSINESS_FIELDS[i],selector:cell.selector,text:cell.name,text_selectors:treeNodes(cell).filter(n=>n.name&&!['img','svg','input','textarea','select'].includes(n.tag)).map(n=>n.selector),box:diagnosticRect(c.getBoundingClientRect()),geometry:businessGeometry(c,view,true,manual?{notice_id:id,tr_selector:selector,union}:null,cell)};
      });rows.push({notice_id:id,tr_selector:selector,cells});
    }
    const date=one({by:'selector',value:projection.dateSelector});
    return {evidence_contract:BUSINESS_CONTRACT,business_viewport:{...view,width:view.right-view.left,height:view.bottom-view.top},...(manual?{preview_contract:MANUAL_CONTRACT,manual_preview_viewport:{width:view.right,height:view.bottom},manual_local_previews:manualCellPreviews(rows,one,view).filter(p=>rows.find(r=>r.notice_id===p.notice_id)?.cells.every(c=>c.geometry.text_leaf_evidence?.excerpt_eligible===true)),public_identity:{provider:projection.provider,actual_url:location.href,visible_card:projection.visibleCard}}:{...(()=>{const p=partialCellPreviews(rows,one,view);return {...p,partial_cell_previews:p.partial_cell_previews.filter(p=>rows.find(r=>r.notice_id===p.notice_id)?.cells.every(c=>c.geometry.text_leaf_evidence?.excerpt_eligible===true))};})(),business_clip_inspection:businessClipInspection(rows,one,view)}),business_headers:headers,business_cells:rows,business_date:{selector:projection.dateSelector,text:String(date.value??date.innerText??'').replace(/\s+/g,' ').trim(),geometry:businessGeometry(date,view,false)}};
  }

  async function stableProof(cmd,one,readTree,business=false){
    const u=new URL(location.href);need(u.origin==='https://life.douyin.com'&&u.pathname==='/p/governance/violation_list'&&u.searchParams.getAll('groupid').length===1&&u.searchParams.get('groupid')===cmd.groupid,'viewport-proof-page-scope-invalid');
    need(document.visibilityState==='visible'&&document.hasFocus(),'viewport-proof-page-not-focused');
    const vv=globalThis.visualViewport;need(!vv||vv.scale===1&&vv.offsetLeft===0&&vv.offsetTop===0,'viewport-proof-zoom-offset-unverified');
    const view={left:0,top:0,right:Math.min(document.documentElement.clientWidth,vv?.width??Infinity),bottom:Math.min(document.documentElement.clientHeight,vv?.height??Infinity)};need(view.right>0&&view.bottom>0,'viewport-proof-empty-viewport');
    const manual=business&&cmd.elements.every(e=>e.key.startsWith(MANUAL_CONTRACT+':'));const tree=readTree(),projection=governanceProjection(tree,cmd.groupid,manual?location.href:null,commandProjection(cmd)),binding=JSON.stringify([cmd.source_sha256,cmd.dom_sha256,cmd.elements]);
    const dates=cmd.elements.filter(e=>e.kind==='date-filter'),headers=cmd.elements.filter(e=>e.kind==='header');
    need(dates.length===1&&dates[0].locator.by==='selector'&&dates[0].locator.value===projection.dateSelector&&headers.length===5&&headers.every(e=>e.locator.by==='selector')&&JSON.stringify(headers.map(e=>e.locator.value).sort())===JSON.stringify([...projection.headerSelectors].sort()),'viewport-proof-projection-required-fields');
    if(stableBinding!==binding){stableWatched.clear();stableBinding=binding;}
    stableTimerNodes=new Set(projection.timers.map(value=>one({by:'selector',value})));stableRectificationNodes=new Set((projection.rectification_timers||[]).map(value=>one({by:'selector',value})));
    const watches=[...projection.refs.map(value=>one({by:'selector',value})),...cmd.elements.map(e=>one(e.locator))];
    for(const el of watches)for(let p=el;p;p=p.parentElement)if(!stableWatched.has(p)){need(stableWatched.size<2000,'viewport-proof-layout-watch-too-large');stableWatched.set(p,rectKey(p));}
    sample();const before=stableEpoch;
    const elements=cmd.elements.map(e=>{
      const el=one(e.locator);let text;
      if(e.kind==='row'){
        need(el.tagName==='TR'&&projection.rowTexts.has(e.locator.value),'viewport-proof-row-semantics-missing');text=projection.rowTexts.get(e.locator.value);need(JSON.parse(text)[0]===e.notice_id,'viewport-proof-projection-row-id-conflict');
        const cs=Array.from(el.children||[]);need(cs.length===10&&cs.every(c=>c.tagName==='TD'),'viewport-proof-ten-live-cells-required');
        // All five business-cell rectangles remain sampled even when only a
        // sibling appeal countdown changes. Actual TR crop remains the caller.
        for(const cell of cs.slice(0,5))if(!stableWatched.has(cell))stableWatched.set(cell,rectKey(cell));
        need(JSON.stringify([e.notice_id,...cs.slice(0,5).map(c=>String(c.innerText||'').replace(/\s+/g,' ').trim())])===text,'viewport-proof-live-five-cells-conflict');
      }else text=String(el.value??el.innerText??'').replace(/\s+/g,' ').trim();
      need(text===e.expected_text,'viewport-proof-semantic-text-changed:'+e.key);
      return {key:e.key,kind:e.kind,notice_id:e.notice_id,locator:e.locator,text,...geometry(el,view,true)};
    });
    const bytes=new TextEncoder().encode(JSON.stringify(projection.value));
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');need(hash===cmd.dom_sha256,'viewport-proof-projection-sha-mismatch');
    const businessFacts=business?businessEvidence(cmd,one,readTree,view):{};
    if(business)for(const row of businessFacts.business_cells)for(const cell of row.cells){const el=one({by:'selector',value:cell.selector});if(!stableWatched.has(el))stableWatched.set(el,rectKey(el));}
    if(business)for(const h of businessFacts.business_headers){const el=one({by:'selector',value:h.selector});if(!stableWatched.has(el))stableWatched.set(el,rectKey(el));}
    await Promise.resolve();sample();need(stableEpoch===before,'viewport-proof-dom-or-layout-changed');
    return {source:'local-dom-bridge',method:'public-DOM-semantic-viewport-proof',source_sha256:cmd.source_sha256,dom_sha256:hash,epoch:stableEpoch,url:location.href,viewport_only:true,pixel_coordinates_returned:business||elements.some(e=>e.containment_diagnostic.reason_count>0),pixel_actions_used:false,elements,diagnostic_build:BUILD,
      ...businessFacts,hash_contract:projectionSchema(commandProjection(cmd),manual),hash_scope:'versioned-public-DOM-projection',all_fully_visible:elements.every(e=>e.fully_visible),scope:{tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid}};
  }

  async function proof(cmd,one,readTree){
    validate(cmd);sample();
    const names=cmd.elements.map(e=>e.key),business=names.some(k=>k.startsWith('notice-five-business-cells-')),gov=names.some(k=>k.startsWith('gov-records-'));
    if(business){commandProjection(cmd);need(!gov&&(names.every(k=>k.startsWith(BUSINESS_CONTRACT+':'))||names.every(k=>k.startsWith(MANUAL_CONTRACT+':'))),'viewport-proof-business-schema-invalid');return stableProof(cmd,one,readTree,true);}
    if(gov)need(names.every(k=>k.startsWith(GOV_SCHEMA+':')),'viewport-proof-projection-schema-invalid');
    if(gov)return stableProof(cmd,one,readTree);
    const binding=JSON.stringify([cmd.source_sha256,cmd.dom_sha256,cmd.elements]);
    if(watchBinding!==binding){watched.clear();watchBinding=binding;}
    const selected=cmd.elements.map(e=>one(e.locator));
    for(const el of selected)for(let p=el;p;p=p.parentElement)if(!watched.has(p)){need(watched.size<2000,'viewport-proof-layout-watch-too-large');watched.set(p,rectKey(p));}
    const beforeEpoch=epoch;
    const u=new URL(location.href);need(u.origin==='https://life.douyin.com'&&u.searchParams.getAll('groupid').length===1&&u.searchParams.get('groupid')===cmd.groupid,'viewport-proof-page-scope-invalid');
    need(document.visibilityState==='visible'&&document.hasFocus(),'viewport-proof-page-not-focused');
    const vv=globalThis.visualViewport;need(!vv||vv.scale===1&&vv.offsetLeft===0&&vv.offsetTop===0,'viewport-proof-zoom-offset-unverified');
    const view={left:0,top:0,right:Math.min(document.documentElement.clientWidth,vv?.width??Infinity),bottom:Math.min(document.documentElement.clientHeight,vv?.height??Infinity)};
    need(view.right>0&&view.bottom>0,'viewport-proof-empty-viewport');
    const tree=readTree();need(tree.truncated===false,'viewport-proof-tree-truncated');
    const elements=cmd.elements.map(e=>{
      const el=one(e.locator);
      if(e.kind==='row')need(el.tagName==='TR'||el.getAttribute?.('role')==='row','viewport-proof-row-semantics-missing');
      const text=String(el.value??el.innerText??'').replace(/\s+/g,' ').trim();
      need(text===e.expected_text,'viewport-proof-semantic-text-changed:'+e.key);
      return {key:e.key,kind:e.kind,notice_id:e.notice_id,locator:e.locator,text, ...geometry(el,view)};
    });
    const publicTree=JSON.stringify(tree);const bytes=new TextEncoder().encode(publicTree);
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    need(hash===cmd.dom_sha256,'viewport-proof-observed-dom-sha-mismatch');
    await Promise.resolve();sample();need(epoch===beforeEpoch,'viewport-proof-dom-or-layout-changed');
    return {source:'local-dom-bridge',method:'public-DOM-semantic-viewport-proof',source_sha256:cmd.source_sha256,dom_sha256:hash,epoch,
      url:location.href,viewport_only:true,pixel_coordinates_returned:elements.some(e=>e.containment_diagnostic.reason_count>0),pixel_actions_used:false,diagnostic_build:BUILD,elements,
      all_fully_visible:elements.every(e=>e.fully_visible),scope:{tabId:cmd.tabId,windowId:cmd.windowId,groupid:cmd.groupid}};
  }
  globalThis.__localViewportProof={build:BUILD,installation_contract:INSTALL,previous_build:priorViewportProof?.build??null,epoch_origin:'new-zero-no-history-continuity',proof,geometry,validate,governanceProjection,overflowClipBox,businessGeometry,businessClipInspection,partialCellPreviews,businessPaintInspection};
})();
