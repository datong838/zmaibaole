(() => {
  const VERSION='dom-only-20261103-12';
  const BUILD='configured-exact-company-v2';
  const COMPANY_POLICY='configured-exact-company-v2';
  const REVISION='w96-account-dismiss-v3-card-fields-retention-v2-anchor-current';
  const previous=globalThis.__localDomExportController;
  if(previous?.version===VERSION&&previous?.build===BUILD&&previous?.company_policy===COMPANY_POLICY&&previous?.revision===REVISION)return;
  if(previous?.listener)chrome.runtime.onMessage.removeListener(previous.listener);
  const P = globalThis.DOM_EXPORT_POLICY;
  const normalize = s => String(s || "").replace(/\s+/g, " ").trim();
  const blocked = /回复|投诉|发送|发布|提交|删除|保存|购买|支付|退出登录|密码|验证码|授权|签约|确认订单/;
  const excluded = e => !!e.closest('script,style,noscript,template,input[type=password],input[type=hidden],[autocomplete*=password],[autocomplete=one-time-code]');
  // Exact zero opacity is not visible. Tiny positive/unknown opacity stays
  // conservatively visible; never hide a real error using an arbitrary threshold.
  function opacityVisible(e,memo,ownStyle) {
    const chain=[];let shown=true,n=e;
    while(n&&n.nodeType===1) {
      if(memo?.has(n)){shown=memo.get(n);break;}
      chain.push(n);const style=n===e?ownStyle:getComputedStyle(n),value=style.opacity;
      if((typeof value==='string'&&value.trim()!==''||typeof value==='number')&&Number(value)===0&&style.display!=='contents'&&n.getClientRects().length>0){shown=false;break;}
      n=n.parentElement;
    }
    if(memo)for(const node of chain)memo.set(node,shown);
    return shown;
  }
  function visibleInRead(e,memo) {
    if(excluded(e)||e.closest('[hidden],[aria-hidden="true"]')||e.getClientRects().length===0)return false;
    const style=getComputedStyle(e);
    if(style.visibility==='hidden')return false;
    // Existing UI/input visibility is unchanged; only message-content leaves
    // get the extra ancestor-opacity test needed by the exact error classifier.
    if(!e.classList?.contains('life-core-message-content'))return true;
    return opacityVisible(e,memo,style);
  }
  const visible=e=>visibleInRead(e,null);
  function role(e) {
    if (e.getAttribute('role')) return e.getAttribute('role');
    if (e.tagName === 'BUTTON') return 'button';
    if (e.tagName === 'A' && e.hasAttribute('href')) return 'link';
    if (e.tagName === 'TEXTAREA') return 'textbox';
    if (e.tagName === 'INPUT') return ['checkbox','radio'].includes(e.type) ? e.type : e.type === 'button' || e.type === 'submit' ? 'button' : 'textbox';
    return ({SELECT:'combobox',OPTION:'option',IMG:'img',MAIN:'main',NAV:'navigation',ASIDE:'complementary',DIALOG:'dialog',TABLE:'table',TR:'row',TH:'columnheader',TD:'cell',H1:'heading',H2:'heading',H3:'heading'})[e.tagName] || 'generic';
  }
  function name(e) {
    if (e.getAttribute('aria-label')) return normalize(e.getAttribute('aria-label'));
    const labelled = e.getAttribute('aria-labelledby');
    if (labelled) return normalize(labelled.split(/\s+/).map(id=>(e.ownerDocument||document).getElementById(id)?.textContent || '').join(' '));
    if (e.labels?.length) return normalize(Array.from(e.labels).map(x=>x.textContent).join(' '));
    if (e.tagName === 'INPUT' || e.tagName === 'TEXTAREA') return normalize(e.getAttribute('placeholder'));
    return normalize(e.innerText || e.getAttribute('alt') || e.getAttribute('title'));
  }
  function selector(e) {
    const parts=[],body=(e.ownerDocument||document).body;
    while(e && e.nodeType===1 && e!==body) {
      if(e.id) { parts.unshift('#'+CSS.escape(e.id)); break; }
      const tag=e.tagName.toLowerCase();
      const siblings=Array.from(e.parentElement?.children || []).filter(s=>s.tagName===e.tagName);
      parts.unshift(tag+(siblings.length>1?`:nth-of-type(${siblings.indexOf(e)+1})`:'')); e=e.parentElement;
    }
    return parts.join(' > ') || 'body';
  }
  function resolve(q) {
    if (!q || !['text','role','selector'].includes(q.by)) throw Error('locator must use text, role or selector');
    if (typeof q.value !== 'string' || !q.value.trim() || q.value.length>1000) throw Error('invalid locator value');
    const opacityMemo=new WeakMap();
    let es=Array.from(document.querySelectorAll(q.by==='selector'?q.value:'body *')).filter(e=>visibleInRead(e,opacityMemo));
    if(q.by==='role') es=es.filter(e=>role(e)===q.value && (q.name===undefined || name(e)===q.name));
    if(q.by==='text') {
      es=es.filter(e=>name(e)===q.value);
      es=es.filter(e=>!Array.from(e.children).some(c=>visible(c)&&name(c)===q.value));
    }
    return es;
  }
  function governanceRoot(e){
    const g=P.governanceCenter;
    if(!g||![g.path,g.recordsPath].includes(location.pathname))return null;
    const root=e.closest('#'+g.rootId);
    return root&&root.id===g.rootId&&root.contains(e)&&visible(root)?root:null;
  }
  function governanceDate(e){
    if(e.tagName!=='INPUT')return false;
    const g=P.governanceCenter,root=governanceRoot(e);if(!root)return false;
    const box=e.closest('.'+g.dateRoot+'.'+g.dateRange);
    const candidates=[...root.querySelectorAll('input')].filter(x=>visible(x)&&(x.getAttribute('placeholder')===g.datePlaceholder||(location.pathname===g.recordsPath&&name(x)==='违规时间'))&&x.closest('.'+g.dateRoot+'.'+g.dateRange));
    return e.tagName==='INPUT'&&role(e)==='textbox'&&String(e.type||'text')==='text'&&(e.getAttribute('placeholder')===g.datePlaceholder||(location.pathname===g.recordsPath&&name(e)==='违规时间'))&&box&&root.contains(box)&&candidates.length===1&&candidates[0]===e;
  }
  function governanceCalendarRule(e){
    const g=P.governanceCenter;if(!g||![g.path,g.recordsPath].includes(location.pathname))return null;
    const calendar=e.closest('.'+g.calendar);if(!calendar||!visible(calendar))return null;
    const calendars=[...document.querySelectorAll('.'+g.calendar)].filter(visible);
    const views=[...calendar.querySelectorAll('.'+g.calendarView)].filter(visible);
    const viewsValid=views.length===2&&['start','end'].every(side=>views.filter(v=>v.classList.contains('governance_merchant-date-position-'+side)).length===1);
    const inputs=[...document.querySelectorAll('#'+g.rootId+' input')].filter(x=>visible(x)&&governanceDate(x));
    if(calendars.length!==1||calendars[0]!==calendar||!viewsValid||inputs.length!==1)throw Error('governance calendar owner ambiguous');
    const view=e.closest('.'+g.calendarView);if(!view||!views.includes(view))throw Error('governance calendar view missing');
    const title=[...view.querySelectorAll('.governance_merchant-date-title')].filter(visible);
    if(title.length!==1||!/^\d{4}年\d{1,2}月$/.test(name(title[0])))throw Error('governance calendar title invalid');
    const cs=String(e.getAttribute('class')||'').split(/\s+/);
    if(e.tagName==='DIV'&&cs.includes('governance_merchant-date-item')){
      const cell=e.parentElement,wrapper=cell&&String(cell.getAttribute('class')||'').split(/\s+/),base=['governance_merchant-date-date','governance_merchant-date-item','governance_merchant-date-grid-in'],allowed=[...base,'governance_merchant-date-selected','governance_merchant-date-today','governance_merchant-date-state-start','governance_merchant-date-state-end','governance_merchant-date-state-in','governance_merchant-date-state-single'];
      if(!cell||cell.tagName!=='SPAN'||!wrapper.includes(g.calendarDay)||!wrapper.includes('governance_merchant-date-grid-in')||cell.children.length!==1||cell.children[0]!==e||e.children.length||name(cell)!==name(e)||!/^(?:[1-9]|[12][0-9]|3[01])$/.test(name(e))||!base.every(c=>cs.includes(c))||!cs.every(c=>allowed.includes(c)))throw Error('governance calendar date item unreviewed');
      if(wrapper.includes('governance_merchant-date-disabled')||e.closest('.governance_merchant-date-row-disabled'))throw Error('governance calendar day disabled');
      return {kind:'filter',scope:'governance-observed-calendar-date-item-v2'};
    }
    if(e.tagName==='DIV'&&name(e)===''&&(cs.includes('governance_merchant-date-nav-prev')||cs.includes('governance_merchant-date-nav-next'))){
      const icons=[...e.querySelectorAll('span')].filter(x=>visible(x)&&['left','right'].some(direction=>x.classList.contains('governance_merchant-icon-'+direction)));
      if(icons.length!==1)throw Error('only observed month navigation allowed');
      return {kind:'filter',scope:'governance-observed-calendar-month'};
    }
    throw Error('governance calendar target not reviewed');
  }
  function governanceRecordsRule(e,root){
    const g=P.governanceCenter;if(location.pathname!==g.recordsPath)return null;
    const tables=[...root.querySelectorAll('table.'+g.recordsTable)].filter(visible);if(tables.length!==1)throw Error('governance records table not unique');
    const table=tables[0],headers=[...table.querySelectorAll('thead th')].map(name);
    if(headers.join('|')!=='违规原因|处置主体|违规对象|处置生效状态|处置方式|违规时间|整改状态|申诉状态|违约金状态|操作')throw Error('governance records headers changed');
    const n=name(e),form=e.closest('form')||e.closest('div.lifep-search-form');
    // B86: the records search controls moved from a <form> to div.lifep-search-form;
    // the reviewed query button admission accepts either container, every other
    // condition (unique visible 查询 button, governance_merchant-btn class, root
    // containment) is unchanged.
    if(n==='查询'&&e.tagName==='BUTTON'&&form&&root.contains(form)&&e.classList.contains('governance_merchant-btn')){
      const buttons=[...form.querySelectorAll('button')].filter(x=>visible(x)&&name(x)==='查询');if(buttons.length!==1||buttons[0]!==e)throw Error('governance query ambiguous');
      return {kind:'filter',scope:'governance-records-query'};
    }
    const row=e.closest('tr.'+g.recordsRow);
    if(n==='查看详情'&&e.tagName==='A'&&e.classList.contains(g.recordsLink)&&row&&table.contains(row)){
      const cells=[...row.children].filter(x=>x.tagName==='TD');
      if(cells.length!==10||!/^(.+?) ID: [A-Za-z0-9_-]+$/.test(name(cells[0]))||!cells[9].contains(e))throw Error('governance detail row identity missing');
      const links=[...cells[9].querySelectorAll('a.'+g.recordsLink)].filter(x=>visible(x)&&name(x)==='查看详情');if(links.length!==1||links[0]!==e)throw Error('governance detail ambiguous');
      return {kind:'navigation',scope:'governance-row-readonly-detail'};
    }
    const li=e.closest('li.governance_merchant-pager-item'),pager=e.closest('.governance_merchant-pager');
    if(li&&pager&&root.contains(pager)&&li===e){
      if(li.classList.contains('governance_merchant-pager-item-disabled')||li.classList.contains('governance_merchant-pager-item-checked'))throw Error('governance records pager unavailable');
      if(/^[1-9][0-9]{0,2}$/.test(n)||(n===''&&li.querySelector('.governance_merchant-icon-right')))return {kind:'navigation',scope:'governance-records-pagination'};
    }
    return null;
  }
  function governanceLegacyLayoutRule(e){
    if(name(e)!=='回到旧版')return null;
    const root=governanceRoot(e),u=new URL(location.href);
    const exactClass=(n,c)=>!!n&&String(n.getAttribute('class')||'').trim().split(/\s+/).sort().join(' ')===c.split(' ').sort().join(' ');
    if(location.pathname!==P.governanceCenter.path||u.origin!==P.origin||u.searchParams.getAll('groupid').length!==1||!/^\d+$/.test(u.searchParams.get('groupid')||'')||e.tagName!=='BUTTON'||role(e)!=='button'||e.children.length||e.closest('form')||e.closest('[role=dialog],dialog')||e.closest('a')||!root)throw Error('unreviewed legacy layout control');
    const roots=[...document.querySelectorAll('#governanceRoot')].filter(visible),actions=e.parentElement,header=actions?.parentElement,container=header?.parentElement;
    const classes='governance_merchant-btn governance_merchant-btn-size-md governance_merchant-btn-type-text governance_merchant-btn-shape-angle governance_merchant-can-input-grouped backButton-cbYsPY';
    if(roots.length!==1||roots[0]!==root||!exactClass(e,classes)||!exactClass(actions,'actions-lq_eBp')||!exactClass(header,'header-EaBIRz')||!exactClass(container,'container-a3IjFk')||container.parentElement!==root)throw Error('unreviewed legacy layout ancestry');
    const titles=[...header.querySelectorAll('p.title-N66Jpb')].filter(visible),buttons=[...root.querySelectorAll('button.backButton-cbYsPY')].filter(visible);
    if(titles.length!==1||titles[0].parentElement!==header||titles[0].children.length||name(titles[0])!=='违规中心'||buttons.length!==1||buttons[0]!==e)throw Error('unreviewed legacy layout ambiguity');
    return {kind:'navigation',scope:'governance-center-legacy-layout-only-v1'};
  }
  function governanceAnalysisTabRule(e){
    if(name(e)!=='违规分析')return null;
    const root=governanceRoot(e),u=new URL(location.href),has=(n,c)=>!!n&&n.classList.contains(c);
    if(location.pathname!==P.governanceCenter.path||u.origin!==P.origin||u.searchParams.getAll('groupid').length!==1||!/^\d+$/.test(u.searchParams.get('groupid')||'')||e.tagName!=='DIV'||e.closest('form')||e.closest('[role=dialog],dialog')||e.closest('a')||!root)throw Error('unreviewed analysis tab scope');
    const roots=[...document.querySelectorAll('#governanceRoot')].filter(visible),inner=e.parentElement,outer=inner?.parentElement;
    const exact=(n,c)=>!!n&&String(n.getAttribute('class')||'').trim().split(/\s+/).sort().join(' ')===c.split(' ').sort().join(' ');
    if(roots.length!==1||roots[0]!==root||!exact(inner,'governance_merchant-tab-bar-items-inner')||!exact(outer,'governance_merchant-tab-bar-items-container')||!root.contains(inner)||![3,4].includes(inner.children.length)||inner.children[0]!==e)throw Error('unreviewed analysis tab pair');
    const inert=n=>!n.disabled&&!n.isContentEditable&&!['tabindex','contenteditable','href','onclick','onkeydown','onpointerdown'].some(k=>n.getAttribute(k)!==null);
    if(inner.children.length===4){const spacer=inner.children[2];if(spacer.tagName!=='SPAN'||role(spacer)!=='generic'||!exact(spacer,'governance_merchant-tab-bar-item-span')||name(spacer)!==''||spacer.children.length||!inert(spacer))throw Error('analysis tab spacer unreviewed');}
    const line=inner.children[inner.children.length-1];if(!inert(line)||line.tagName!=='DIV'||role(line)!=='generic'||!exact(line,'governance_merchant-tab-bar-items-inner-line')||name(line)!==''||line.children.length)throw Error('analysis tab indicator unreviewed');
    const prevent=inner.children[1],base='governance_merchant-tab-bar-item governance_merchant-tab-bar-item-type-basic';
    if(!exact(e,base)||!exact(prevent,base+' governance_merchant-tab-bar-item-active')||name(prevent)!=='违规预防'||!visible(prevent))throw Error('analysis tab selection unreviewed');
    for(const [tab,label] of [[e,'违规分析'],[prevent,'违规预防']]){
      if(tab.tagName!=='DIV'||role(tab)!=='generic'||tab.children.length!==1||tab.children[0].tagName!=='SPAN'||!exact(tab.children[0],'governance_merchant-tab-bar-item-label')||tab.children[0].children.length||name(tab.children[0])!==label)throw Error('analysis tab label unreviewed');
    }
    return {kind:'navigation',scope:'governance-center-analysis-display-tab-v1'};
  }
  function governanceCompactRecordsRule(e){
    if(name(e)!=='违规记录'||!e.classList.contains('compactLabel-aFEjMF'))return null;
    const root=governanceRoot(e),u=new URL(location.href),exact=(n,c)=>!!n&&String(n.getAttribute('class')||'').trim().split(/\s+/).sort().join(' ')===c.split(' ').sort().join(' ');
    const item=e.parentElement,list=item?.parentElement,tools=list?.parentElement;
    if(location.pathname!==P.governanceCenter.path||u.origin!==P.origin||u.searchParams.getAll('groupid').length!==1||!/^\d+$/.test(u.searchParams.get('groupid')||'')||!root||e.tagName!=='P'||role(e)!=='generic'||e.children.length||!exact(e,'compactLabel-aFEjMF')||!exact(item,'compactItem-TpyZAq')||!exact(list,'compactList-kThnsC')||!exact(tools,'todoSummary-xpJGcr compact-Gcf1ET boardSuccess-tXR2Eq')||!root.contains(tools)||!/^违规记录 新增[0-9]+$/.test(name(item))||e.closest('form')||e.closest('[role=dialog],dialog')||e.closest('a'))throw Error('unreviewed compact records entry');
    const roots=[...document.querySelectorAll('#governanceRoot')].filter(visible),labels=[...root.querySelectorAll('p.compactLabel-aFEjMF')].filter(x=>visible(x)&&name(x)==='违规记录');
    if(roots.length!==1||roots[0]!==root||labels.length!==1||labels[0]!==e)throw Error('compact records entry ambiguous');
    return {kind:'navigation',scope:'governance-center-compact-record-entry-v1'};
  }
  function governanceRule(e){
    const compact=governanceCompactRecordsRule(e);if(compact)return compact;
    const analysisTab=governanceAnalysisTabRule(e);if(analysisTab)return analysisTab;
    const legacy=governanceLegacyLayoutRule(e);if(legacy)return legacy;
    const g=P.governanceCenter,root=governanceRoot(e);if(!root)return null;
    const n=name(e),cls=String(e.getAttribute('class')||'').split(/\s+/),has=(x,c)=>!!x&&String(x.getAttribute('class')||'').split(/\s+/).includes(c);
    if(/去处理|整改|申诉|删除|缴费|考试/.test(n))throw Error('governance business action forbidden');
    if(governanceDate(e))return {kind:'filter',scope:'governance-datepicker-open-only'};
    const record=governanceRecordsRule(e,root);if(record)return record;
    const panel=e.closest('.'+g.topList),title=panel?[...panel.querySelectorAll('.'+g.topTitle)].filter(visible):[];
    const panelVerified=panel&&root.contains(panel)&&title.length===1&&normalize(title[0].innerText)==='违规原因 Top10';
    if(n==='全部'&&e.tagName==='SPAN'&&cls.includes(g.viewAll)&&panelVerified){
      const targets=[...panel.querySelectorAll('.'+g.viewAll)].filter(x=>visible(x)&&name(x)==='全部');
      if(targets.length!==1||targets[0]!==e)throw Error('governance all-reasons ambiguous');
      return {kind:'navigation',scope:'governance-center-all-reasons'};
    }
    const tools=e.closest('.'+g.tools),item=e.closest('.'+g.toolItem);
    if(n==='违规记录'&&e.tagName==='P'&&cls.includes(g.toolLabel)&&tools&&item&&root.contains(tools)&&tools.contains(item)&&item.contains(e)){
      const targets=[...tools.querySelectorAll('.'+g.toolLabel)].filter(x=>visible(x)&&name(x)==='违规记录');
      if(!normalize(tools.innerText).startsWith('常用工具 ')||!/^违规记录 新增[0-9]+$/.test(normalize(item.innerText))||targets.length!==1||targets[0]!==e)throw Error('governance record entry ambiguous');
      return {kind:'navigation',scope:'governance-center-record-entry'};
    }
    const pager=e.closest('.'+g.pagination),li=e.closest('li.'+g.pagerItem);
    if(panelVerified&&pager&&li&&panel.contains(pager)&&pager.contains(li)&&li.contains(e)){
      const numeric=/^[1-9][0-9]{0,2}$/.test(n)&&['LI','SPAN'].includes(e.tagName);
      const arrow=n===''&&((e.tagName==='SPAN'&&has(e,'governance_merchant-icon-right'))||(e===li&&li.querySelector('.governance_merchant-icon-right')));
      if(numeric||arrow){
        if(has(li,g.pagerDisabled)||has(li,g.pagerChecked))throw Error('governance pager disabled or already selected');
        return {kind:'navigation',scope:'governance-center-top-reasons-pagination'};
      }
    }
    return null;
  }
  function governanceStopLossReturnRule(e){
    if(location.pathname!=='/p/govern_fulfillment_v2/violation_stop_lose_notice')return null;
    if(e.tagName!=='BUTTON'||name(e)!=='查看其他处置'||!e.classList.contains('btn-WHUasg')||!e.classList.contains('govern_fulfillment_v2-btn'))return null;
    const roots=[...document.querySelectorAll('#root')].filter(visible),root=e.closest('#root'),url=new URL(location.href);
    if(roots.length!==1||roots[0]!==root||url.searchParams.getAll('groupid').length!==1||!/^\d+$/.test(url.searchParams.get('groupid')||'')||url.searchParams.get('EnterFrom')!=='home_violation_center'||!/^ST[a-f0-9]{24}$/.test(url.searchParams.get('TaskID')||''))throw Error('stop loss return scope unreviewed');
    const titles=[...root.querySelectorAll('h1.title-AOxZNO')].filter(x=>visible(x)&&name(x)==='止损通知书');
    const targets=[...root.querySelectorAll('button.btn-WHUasg')].filter(x=>visible(x)&&name(x)==='查看其他处置');
    if(titles.length!==1||targets.length!==1||targets[0]!==e)throw Error('stop loss return control not unique');
    return {kind:'navigation',scope:'governance-stop-loss-readonly-return-v1'};
  }
  function publicReviewText(e){
    const cls=(x,c)=>String(x?.getAttribute('class')||'').split(/\s+/).includes(c);
    if(location.pathname!=='/p/life_comment/management'||e.tagName!=='DIV'||!cls(e,'text-Hl9jZe')||!visible(e))return null;
    const card=e.closest('.commentItem-jrXo5p');if(!card||card.tagName!=='DIV'||!visible(card))return null;
    const children=[...e.children];
    if(children.length){
      if(children.length!==1||children[0].tagName.toLowerCase()!=='svg'||children[0].getAttribute('role')!=='presentation'||children[0].getAttribute('class')!=='icon-K1rG1b')return null;
      for(const c of [children[0],...children[0].querySelectorAll('*')])if(!['svg','g','path'].includes(c.tagName.toLowerCase())||String(c.textContent||'').trim()||excluded(c))return null;
    }
    const value=e.innerText;if(typeof value!=='string'||value.length>16000)return null;
    return {method:'visible-innerText-v1',value,complete:true};
  }
  function publicNoticeFrame(e){
    if(location.pathname!=='/p/governance/violation_list'||e.tagName!=='IFRAME'||e.getAttribute('class')!=='iframe-TNKSmG'||!visible(e))return null;
    const selector='.governance_merchant-drawer-dialog.governance_merchant-drawer-dialog-show.notice-drawer-vBipFK';
    const drawer=e.closest(selector),drawers=[...document.querySelectorAll(selector)].filter(visible);
    if(!drawer||drawers.length!==1||drawers[0]!==drawer||[...drawer.querySelectorAll('iframe.iframe-TNKSmG')].filter(visible).length!==1)return null;
    const out={schema:'public-notice-frame-metadata-v1',document_available:false,query_and_fragment_excluded:true,frame_input_enabled:false};
    try{const src=new URL(e.getAttribute('src')||'',location.href);if(src.protocol==='https:'){out.source_origin=src.origin;out.source_path=src.pathname.slice(0,400);out.source_same_origin=src.origin===location.origin;}}
    catch{}
    try{const doc=e.contentDocument;if(doc){const url=new URL(doc.URL);if(url.origin===location.origin){out.document_available=true;out.document_origin=url.origin;out.document_path=url.pathname.slice(0,400);out.ready_state=doc.readyState;}}}
    catch{}
    return out;
  }
  function assertNoticeFrameNoControls(doc){
    // Reject before reading ancestor names, which can include omitted controls
    // through innerText or aria-labelledby. Never inspect control values.
    if(doc.querySelectorAll('input,textarea,select,[contenteditable]').length)throw Error('public notice frame contains unreviewed form controls');
  }
  function node(e) {
    const attributes={};
    for(const key of ['id','class','role','aria-label','aria-pressed','aria-selected','aria-checked','aria-expanded','aria-disabled','datetime','data-review-id','data-comment-id','data-notice-id','data-rating']){const value=e.getAttribute(key);if(value!==null)attributes[key]=String(value).slice(0,P.maxText);}
    if(['INPUT','TEXTAREA'].includes(e.tagName)&&(P.filterPlaceholders.includes(e.getAttribute('placeholder'))||['评价时间','评价类型','评价来源','评价状态'].includes(name(e))))attributes.value=e.value||'';
    if(governanceDate(e)){const value=String(e.value||'');if(value.length<=100&&/^(?:[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}\s*[~～]\s*[0-9]{4}[-/][0-9]{2}[-/][0-9]{2})?$/.test(value))attributes.value=value;}
    const publicText=publicReviewText(e);
    const frame=publicNoticeFrame(e);
    return {...(publicText?{public_visible_text:publicText}:{}),...(frame?{public_frame:frame}:{}),attributes,role:role(e), name:name(e).slice(0,P.maxText), tag:e.tagName.toLowerCase(), selector:selector(e), disabled:!!e.disabled || e.getAttribute('aria-disabled')==='true', placeholder:e.getAttribute('placeholder') || undefined};
  }
  function one(q) {
    const es=resolve(q);
    if(es.length!==1) throw Error(`ambiguous-or-missing: ${es.length} visible matches; inspect and scope selector, never guess`);
    return es[0];
  }
  function complaintDrawerCloseRule(e,action){
    if(location.pathname!=='/p/life_comment/management'||e.tagName!=='SPAN'||name(e)!==''||e.getAttribute('class')!=='byted-drawer-close-icon')return null;
    const selector='.byted-drawer-dialog.byted-drawer-dialog-show.drawer-container-oSzIEl';
    const drawer=e.closest(selector),drawers=[...document.querySelectorAll(selector)].filter(visible);
    if(action!=='complaint-read'||!drawer||drawer.tagName!=='DIV'||drawers.length!==1||drawers[0]!==drawer)throw Error('complaint result drawer not unique');
    const titles=[...drawer.querySelectorAll('.byted-drawer-content-header .byted-drawer-content-inner-wrapper')].filter(x=>visible(x)&&name(x)==='投诉评价');
    const closes=[...drawer.querySelectorAll('span.byted-drawer-close-icon')].filter(visible);
    const icons=[...e.querySelectorAll('span.byted-icon-close-drawer')].filter(visible);
    const content=normalize(drawer.innerText);
    if(titles.length!==1||closes.length!==1||closes[0]!==e||icons.length!==1||!content.includes('顾客评价')||!content.includes('举报信息'))throw Error('unreviewed complaint result drawer structure');
    return {kind:'complaint-read',scope:'observed-complaint-result-drawer-close'};
  }
  function governanceDrawerCloseRule(e,action){
    if(location.pathname!=='/p/governance/violation_list'||e.tagName!=='SPAN'||name(e)!==''||e.getAttribute('class')!=='governance_merchant-drawer-close-icon')return null;
    const selector='.governance_merchant-drawer-dialog.governance_merchant-drawer-dialog-show.notice-drawer-OIp9e3';
    const drawer=e.closest(selector),drawers=[...document.querySelectorAll(selector)].filter(visible);
    if(action!=='dismiss'||!drawer||drawers.length!==1||drawers[0]!==drawer)throw Error('governance notice drawer not unique');
    const titles=[...drawer.querySelectorAll('h1.title-UTzrUd')].filter(x=>visible(x)&&name(x)==='违规通知书');
    const labels=[...drawer.querySelectorAll('span.label-CPZ6GC')].filter(x=>visible(x)&&name(x)==='罚单编号');
    const closes=[...drawer.querySelectorAll('span.governance_merchant-drawer-close-icon')].filter(visible);
    const icons=[...e.querySelectorAll('span.governance_merchant-icon.governance_merchant-icon-close')].filter(visible);
    if(titles.length!==1||labels.length!==1||closes.length!==1||closes[0]!==e||icons.length!==1||e.children.length!==1||e.children[0]!==icons[0])throw Error('governance notice close structure unreviewed');
    const pair=labels[0].parentElement,parts=pair&&[...pair.children];
    if(!pair.classList.contains('item-dOecJQ')||parts.length!==2||parts[0]!==labels[0]||parts[1].tagName!=='SPAN'||!parts[1].classList.contains('value-IrgzTE')||!visible(parts[1])||!/^[A-Za-z0-9_-]+$/.test(name(parts[1])))throw Error('governance notice identity missing');
    return {kind:'dismiss',scope:'governance-observed-notice-drawer-close-v1'};
  }
  function governanceFrameDrawerCloseRule(e,action){
    if(location.pathname!=='/p/governance/violation_list'||e.tagName!=='SPAN'||name(e)!==''||e.getAttribute('class')!=='governance_merchant-drawer-close-icon')return null;
    const selector='.governance_merchant-drawer-dialog.governance_merchant-drawer-dialog-show.notice-drawer-vBipFK';
    const drawer=e.closest(selector);
    if(!drawer)return null;
    const shown=[...document.querySelectorAll('.governance_merchant-drawer-dialog.governance_merchant-drawer-dialog-show')].filter(visible);
    if(action!=='dismiss'||shown.length!==1||shown[0]!==drawer||e.parentElement!==drawer)throw Error('governance frame drawer owner ambiguous');
    const frames=[...drawer.querySelectorAll('iframe.iframe-TNKSmG')].filter(visible);
    if(frames.length!==1)throw Error('governance frame drawer iframe ambiguous');
    const f=frames[0],meta=publicNoticeFrame(f);
    if(!meta||!meta.document_available||!meta.source_same_origin||meta.source_path!=='/h5/governance/violation_talent_notice'||meta.document_path!==meta.source_path||meta.ready_state!=='complete')throw Error('governance frame drawer document unreviewed');
    const doc=f.contentDocument;
    assertNoticeFrameNoControls(doc);
    const titles=[...doc.querySelectorAll('.by-header__title_overhide')].filter(x=>visible(x)&&['生活服务违规通知','锚点使用建议'].includes(name(x)));
    const labels=[...doc.querySelectorAll('div')].filter(x=>visible(x)&&!x.children.length&&name(x)==='违规ID：');
    const closes=[...drawer.querySelectorAll('span.governance_merchant-drawer-close-icon')].filter(visible),icons=[...e.querySelectorAll('span.governance_merchant-icon.governance_merchant-icon-close')].filter(visible);
    if(titles.length!==1||closes.length!==1||closes[0]!==e||icons.length!==1||e.children.length!==1||e.children[0]!==icons[0])throw Error('governance frame drawer structure unreviewed');
    if(name(titles[0])==='锚点使用建议'){
      const u=new URL(location.href),task=u.searchParams.getAll('TaskID');
      if(task.length!==1||!/^CF[A-Za-z0-9_-]{1,96}$/.test(task[0])||u.searchParams.get('drawerForV2')!=='MerchantCID')throw Error('anchor frame task ambiguous');
      const card=doc.getElementById('violation_'+task[0]);
      const leaves=[...doc.querySelectorAll('div,span')].filter(x=>visible(x)&&!x.children.length);
      const literal='您的视频中挂载了抖音生活服务的经营类锚点，但实际视频内容未对锚点下的抖音生活服务相关商品、服务、环境进行展示、营销或种草。该情况不属于违规，不会影响您的视频流量和账号。';
      if(!card||!visible(card)||!name(card).includes('温馨提醒：锚点类型选择有误')||leaves.filter(x=>name(x)===literal).length!==1||labels.length!==0)throw Error('anchor frame advisory identity missing');
      return {kind:'dismiss',scope:'governance-observed-same-origin-anchor-advice-close-v1'};
    }
    if(labels.length!==1)throw Error('governance frame notice identity ambiguous');
    const pair=labels[0].parentElement,parts=pair&&[...pair.children];
    if(!pair||parts.length!==2||parts[0]!==labels[0]||parts[1].tagName!=='DIV'||!visible(parts[1])||parts[1].children.length||!/^[A-Za-z0-9_-]+$/.test(name(parts[1])))throw Error('governance frame drawer notice identity missing');
    return {kind:'dismiss',scope:'governance-observed-same-origin-notice-frame-close-v1'};
  }
  function commentToolboxRule(e,action){
    if(e.id!=='CommentToolView_select')return null;
    const exact=(node,tag,classes)=>node&&node.tagName===tag&&node.getAttribute('class')===classes&&visible(node)&&!node.disabled&&node.getAttribute('aria-disabled')!=='true';
    const roots=[...document.querySelectorAll('#CommentToolView_select')].filter(visible);
    if(location.pathname!=='/p/life_comment/management'||action!=='navigation'||e.tagName!=='DIV'||roots.length!==1||roots[0]!==e||e.closest('form')||e.closest('a')||name(e)!=='工具箱')throw Error('unreviewed comment toolbox owner');
    const item=e.children.length===1?e.children[0]:null;
    const info=item&&item.children.length===1?item.children[0]:null;
    const children=info?[...info.children]:[];
    if(!exact(item,'DIV','toolViewItem-AAil1V tool-KL4xzH')||!exact(info,'DIV','info-EzAm3S')||children.length!==2||!exact(children[0],'IMG','icon-NqMTEO')||children[0].children.length||name(children[0])!==''||!exact(children[1],'DIV','title-x_oc4C')||children[1].children.length||name(children[1])!=='工具箱'||name(item)!=='工具箱'||name(info)!=='工具箱')throw Error('unreviewed comment toolbox structure');
    return {kind:'navigation',scope:'observed-comment-toolbox-list-v1'};
  }
  function commentStatusOpenRule(e,action){
    if(e.tagName!=='INPUT'||name(e)!=='评价状态')return null;
    const exact=(n,tag,classes)=>n&&n.tagName===tag&&n.getAttribute('class')===classes&&visible(n)&&!n.disabled&&n.getAttribute('aria-disabled')!=='true';
    const label=e.parentElement,wrapper=label?.parentElement,trigger=wrapper?.parentElement,select=trigger?.parentElement;
    const inputs=[...document.querySelectorAll('input.byted-input.byted-input-size-md')].filter(x=>visible(x)&&name(x)==='评价状态');
    if(location.pathname!=='/p/life_comment/management'||action!=='filter'||inputs.length!==1||inputs[0]!==e||e.closest('form')||e.closest('a')||!exact(e,'INPUT','byted-input byted-input-size-md')||e.getAttribute('placeholder')!=='请选择'||e.value!=='全部'||e.children.length)throw Error('unreviewed comment status input');
    if(!exact(label,'LABEL','byted-input-inner__wrapper byted-input-inner__wrapper-border byted-input-inner__wrapper-size-md byted-input-inner__wrapper-add-prefix byted-input-inner__wrapper-add-suffix')||!exact(wrapper,'SPAN','byted-input-wrapper byted-input-wrapper-size-md')||!exact(trigger,'SPAN','byted-popper-trigger byted-popper-trigger-click byted-select-input')||!exact(select,'SPAN','byted-select byted-select-size-md byted-select-single byted-can-input-grouped')||[wrapper,trigger,select].some(x=>x.children.length!==1)||label.children.length!==3||label.children[1]!==e)throw Error('unreviewed comment status ancestry');
    const prefix=label.children[0],suffix=label.children[2],arrow=suffix.children[0];
    if(!exact(prefix,'SPAN','byted-input-prefix byted-input-prefix-divider')||prefix.children.length||name(prefix)!=='评价状态'||!exact(suffix,'SPAN','byted-input-suffix')||suffix.children.length!==1||!exact(arrow,'SPAN','byted-icon byted-icon-down byted-select-arrow')||arrow.children.length!==1)throw Error('unreviewed comment status label');
    let icon=arrow.children[0];for(const tag of ['svg','g','g','polyline']){if(!icon||icon.tagName.toLowerCase()!==tag||!visible(icon)||name(icon)!==''||icon.children.length!==(tag==='polyline'?0:1))throw Error('unreviewed comment status icon');icon=icon.children[0];}
    return {kind:'filter',scope:'observed-comment-status-open-only-v1'};
  }
  function normalReviewPagerRule(e,action){
    const pager=e.closest('.pagination-GXvAPk');
    if(!pager)return null;
    const exact=(x,tag,cl)=>x&&x.tagName===tag&&x.getAttribute('class')===cl&&visible(x)&&!x.disabled&&x.getAttribute('aria-disabled')!=='true';
    const lists=[...document.querySelectorAll('.commentList-hkujq4.isPC-WBFQKh.commentList-C8RoYO')].filter(visible),list=pager.parentElement,group=e.parentElement;
    const gid=new URL(location.href).searchParams.getAll('groupid');
    if(location.pathname!=='/p/life_comment/management'||gid.length!==1||!/^\d+$/.test(gid[0])||action!=='navigation'||lists.length!==1||lists[0]!==list||!exact(list,'DIV','commentList-hkujq4 isPC-WBFQKh commentList-C8RoYO')||!exact(pager,'DIV','pagination-GXvAPk')||list.children[list.children.length-1]!==pager||pager.children.length!==2||!exact(group,'DIV','buttonGroup-GDbp9Y')||pager.children[1]!==group||group.children.length!==3||![group.children[0],group.children[2]].includes(e)||e.closest('form')||e.closest('a'))throw Error('unreviewed normal review pager owner');
    const total=pager.children[0],current=group.children[1],match=/^([1-9]\d*)\/([1-9]\d*)$/.exec(name(current));
    if(!exact(total,'DIV','text-bjyZFG')||total.children.length||!/^共[1-9]\d*条记录$/.test(name(total))||!exact(current,'DIV','text-bjyZFG')||current.children.length||!match)throw Error('unreviewed normal review pager labels');
    const page=Number(match[1]),pages=Number(match[2]),records=Number(name(total).match(/\d+/)[0]);
    if(!Number.isSafeInteger(records)||pages!==Math.ceil(records/10)||page>pages)throw Error('unreviewed normal review pager count');
    const head=list.children[0],middle=[...list.children].slice(1,-1);
    const terminalText='折叠评价是根据规则计算对用户帮助不大的评价，不计入全部评价数量，消费后无图文的纯星级评价仍加入评分计算，若有其他疑问咨询下方客服，或查看规则';
    const folds=middle.filter(x=>String(x.getAttribute('class')||'').split(/\s+/).includes('foldTitleContainer-DwIByI'));
    const terminal=folds.length>0;
    if(!exact(head,'DIV','header-sQid1u commentListHeader-jKdTh_'))throw Error('unreviewed normal review pager list');
    if(terminal){
      // The same-job reviewed terminal profile is validated by the caller.
      // At the bridge, enforce only a real unique direct fold boundary and
      // arithmetic normal-prefix coverage; no company/page/count literals.
      const foldIndex=middle.indexOf(folds[0]),visibleCards=Math.min(10,records-(page-1)*10);
      if(e!==group.children[0]||page<=1||folds.length!==1||middle.length!==visibleCards+1||foldIndex<1||foldIndex>10||!exact(folds[0],'DIV','foldTitleContainer-DwIByI isPC-qcMKrG')||name(folds[0])!==terminalText||middle.slice(0,foldIndex).some(x=>!exact(x,'DIV','commentItem-jrXo5p'))||middle.slice(foldIndex+1).some(x=>!exact(x,'DIV','commentItem-jrXo5p')))throw Error('unreviewed terminal normal previous only');
      const anchors=[...folds[0].querySelectorAll('span')].filter(x=>visible(x)&&!x.children.length&&x.getAttribute('class')==='link-FfL1As'&&name(x)==='查看规则');
      if(anchors.length!==1)throw Error('unreviewed terminal normal boundary');
    }else if(middle.length<1||middle.length>10||middle.some(x=>!exact(x,'DIV','commentItem-jrXo5p')))throw Error('unreviewed normal review pager list');
    const counts=[...head.querySelectorAll('div')].filter(x=>visible(x)&&!x.children.length&&/^已筛选[1-9]\d*条$/.test(name(x)));
    const negative=[...document.querySelectorAll('.option-YmRyn3.isSelected-ov8pOi')].filter(x=>visible(x)&&name(x)==='中差评（1-3心）');
    if(counts.length!==1||negative.length!==1)throw Error('unreviewed normal review pager filters');
    if(terminal){const normalCount=Number(name(counts[0]).match(/\d+/)[0]),foldIndex=middle.indexOf(folds[0]);if(!Number.isSafeInteger(normalCount)||normalCount>=records||page!==Math.ceil(normalCount/10)||foldIndex!==normalCount-(page-1)*10)throw Error('unreviewed terminal normal count');}
    const fields=new Map();
    for(const input of document.querySelectorAll('input.byted-input.byted-input-size-md')){if(!visible(input))continue;const label=name(input);if(!['评价时间','评价类型','评价来源','评价状态'].includes(label))continue;if(fields.has(label))throw Error('ambiguous normal review filter');fields.set(label,input.value);}
    if(fields.size!==4||!/^\d{4}-\d{2}-\d{2} ~ \d{4}-\d{2}-\d{2}$/.test(fields.get('评价时间'))||['评价类型','评价来源','评价状态'].some(k=>fields.get(k)!=='全部'))throw Error('unreviewed normal review pager filter values');
    for(const [i,button] of [[0,group.children[0]],[2,group.children[2]]]){
      const disabled=(i===0?page===1:page===pages),cl='button-j4VxiA'+(disabled?' isDisabled-unTBS6':'');
      if(!exact(button,'DIV',cl)||name(button)!==''||button.children.length!==1)throw Error('unreviewed normal review pager button');
      let icon=button.children[0];for(const tag of ['svg','g','path']){if(!icon||icon.tagName.toLowerCase()!==tag||!visible(icon)||name(icon)!==''||icon.children.length!==(tag==='path'?0:1)||(tag==='svg'&&(icon.getAttribute('class')!=='icon-v6i0WU'||icon.getAttribute('role')!=='presentation')))throw Error('unreviewed normal review pager icon');icon=icon.children[0];}
      if(button===e&&disabled)throw Error('normal review pager disabled');
    }
    return {kind:'navigation',scope:terminal?'observed-normal-terminal-previous-v1':'observed-normal-review-adjacent-pager-v1'};
  }
  function exportRecordsPagerRule(e){
    if(!/^\/p\/fulfillsettle\/export_records\/[0-9]+$/.test(location.pathname))return null;
    const cs=n=>new Set(String(n.getAttribute('class')||'').split(/\s+/)),has=(n,c)=>cs(n).has(c);
    if(e.tagName!=='LI'||!has(e,'byted-pager-item'))return null;
    const u=new URL(location.href),g=u.searchParams.getAll('groupid');
    if(u.origin!==P.origin||g.length!==1||!/^\d+$/.test(g[0]))throw Error('export pager group scope');
    const one=(a,why)=>{if(a.length!==1)throw Error(why);return a[0];};
    const active=Array.from(document.querySelectorAll('.byted-tab-bar-item-active')).filter(n=>name(n)==='门店评价');one(active,'export pager active review type');
    const table=one(Array.from(document.querySelectorAll('.byted-table-container-row')).filter(n=>has(n,'byted-table-container')),'export pager one table');
    const pager=one(Array.from(table.querySelectorAll('.byted-pager')),'export pager unique scope');
    if(!pager.contains(e))return null;
    if(!visible(table)||!visible(pager)||e.closest('form')||e.closest('a')||e.disabled||e.getAttribute('aria-disabled')==='true'||has(e,'byted-pager-item-disabled')||has(e,'byted-pager-item-checked'))throw Error('export pager disabled or foreign control');
    const head=one(Array.from(table.querySelectorAll('.byted-table-head')),'export pager head');
    if(JSON.stringify(Array.from(head.querySelectorAll('.byted-table-cell-head')).map(name))!==JSON.stringify(['报表名称','报表类型','开始生成时间','状态','','操作']))throw Error('export pager headers');
    const body=one(Array.from(table.querySelectorAll('.byted-table-body')),'export pager body');
    const count=one(Array.from(pager.querySelectorAll('.byted-pager-record')),'export pager count'),m=/^共\s*([0-9]+)\s*条记录$/.exec(name(count));
    if(!m||+m[1]>30||+m[1]<0)throw Error('export pager retention bound');
    const total=+m[1],pages=Math.max(1,Math.ceil(total/10)),group=one(Array.from(pager.children).filter(n=>has(n,'byted-pager-item-group')),'export pager group'),items=Array.from(group.children),numbers=items.slice(1,-1);
    if(items.length!==pages+2||items.some(n=>n.tagName!=='LI'||!has(n,'byted-pager-item'))||numbers.some((n,i)=>name(n)!==String(i+1)))throw Error('export pager contiguous pages');
    const selected=one(numbers.filter(n=>has(n,'byted-pager-item-checked')),'export pager current'),current=+name(selected);
    if(has(items[0],'byted-pager-item-disabled')!==(current===1)||has(items.at(-1),'byted-pager-item-disabled')!==(current===pages)||name(items[0])!==''||name(items.at(-1))!==''||items[0].querySelectorAll('.byted-icon-left').length!==1||items.at(-1).querySelectorAll('.byted-icon-right').length!==1)throw Error('export pager arrows');
    const rows=Array.from(body.children);
    if(rows.length!==Math.min(10,Math.max(0,total-(current-1)*10))||rows.some(n=>n.tagName!=='DIV'||!has(n,'byted-table-row')||!has(n,'byted-table-column')))throw Error('export pager page size');
    if(e===items.at(-1)&&current<pages||e===numbers[0]&&current!==1)return {kind:'navigation',scope:'review-export-baseline-pager-v1'};
    throw Error('export pager only semantic next or return first');
  }
  function companyCapability(cap) {
    const keys=['kind','config','request','entry_id','company','provider','tabId','windowId','sourceGroupid','sourceIdentity','key','expires_at'];
    if(cap?.sourceEntry)keys.push('sourceEntry');
    if(!cap||Object.keys(cap).sort().join(',')!==keys.sort().join(',')||cap.kind!=='approved-exact-company-capability-v2'||typeof cap.company!=='string'||!cap.company||cap.company.trim()!==cap.company||/[\r\n]/.test(cap.company)||!/^服务商[0-9]+$/.test(cap.provider)||!Number.isSafeInteger(cap.tabId)||!Number.isSafeInteger(cap.windowId)||!/^\d+$/.test(cap.sourceGroupid)||!Number.isFinite(Date.parse(cap.expires_at))||Date.now()>Date.parse(cap.expires_at))throw Error('approved company capability required');
    const u=new URL(location.href),g=u.searchParams.getAll('groupid');
    const login=!!cap.sourceEntry;
    if(u.origin!==P.origin||u.hash||(login?(u.pathname!=='/p/login'||u.search!=='') : (!['/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management'].includes(u.pathname)||g.length!==1||g[0]!==cap.sourceGroupid)))throw Error('company capability source scope changed');
    if(login){const x=cap.sourceEntry;if(Object.keys(x).sort().join(',')!=='authority,kind'||!['original-job-login-company-picker-v2','verified-config-login-company-picker-v2'].includes(x.kind)||!x.authority||Object.keys(x.authority).sort().join(',')!=='path,sha256'||!x.authority.path.startsWith('/')||!/^([a-f0-9]{64})$/.test(x.authority.sha256))throw Error('company login original job authority required');companyPickerRoot(cap);}
    for(const r of[cap.config,cap.request])if(!r||Object.keys(r).sort().join(',')!=='path,sha256'||typeof r.path!=='string'||!r.path.startsWith('/')||!/^([a-f0-9]{64})$/.test(r.sha256))throw Error('company capability ref invalid');
    if(login)return cap.company; // The login page never establishes business identity.
    const identity=cap.sourceIdentity,cards=Array.from(document.querySelectorAll('[class*="UserCard-index-module__outer--"]')).filter(visible);
    if(cards.length!==1)throw Error('company current identity card not unique');
    const text=normalize(cards[0].innerText),providers=[...new Set(text.match(/服务商[0-9]+/g)||[])],accounts=[...new Set([...text.matchAll(/账户ID\s*[：:]?\s*([0-9]{8,})/g)].map(x=>x[1]))],managers=[...new Set([...text.matchAll(/我的客户经理\s*[：:]?\s*(.+?)(?=\s*(?:切换公司|退出登录)|$)/g)].map(x=>x[1].trim()))];
    if(!identity||Object.keys(identity).sort().join(',')!=='account_id,manager,provider'||identity.provider!==cap.provider||text.length>=800||providers.length!==1||providers[0]!==identity.provider||accounts.length!==1||accounts[0]!==identity.account_id||managers.length!==1||managers[0]!==identity.manager)throw Error('company current full identity changed');
    return cap.company;
  }
  function companyPickerRoot(cap) {
    if(!cap?.sourceEntry)return null;
    const prefix='src-pages-Login-components-LoginFlowCard-index-module__';
    const roots=[...document.querySelectorAll('[class*="'+prefix+'container--"]')].filter(visible);
    if(roots.length!==1)throw Error('company login picker unique');
    const root=roots[0],titles=[...root.querySelectorAll('p[class*="'+prefix+'title--"]')].filter(x=>visible(x)&&name(x)==='选择你的公司');
    const fields=[...root.querySelectorAll('input[placeholder="搜索商户"]')].filter(visible),lists=[...root.querySelectorAll('.card__list_582b9')].filter(visible);
    if(titles.length!==1||fields.length!==1||lists.length!==1||fields[0].disabled||fields[0].readOnly||root.querySelector('iframe,form'))throw Error('company login picker structure');
    return root;
  }
  function companySearchField(e,cap) {
    companyCapability(cap);
    const prefix='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__';
    const roots=cap.sourceEntry?[companyPickerRoot(cap)]:[...document.querySelectorAll('[class*="'+prefix+'login-modal--"]')].filter(visible);
    if(roots.length!==1||roots[0].querySelector('iframe,form'))throw Error('company search unique picker');
    const fields=[...roots[0].querySelectorAll('input[placeholder="搜索商户"]')].filter(visible);
    if(fields.length!==1||fields[0]!==e||e.disabled||e.readOnly)throw Error('company search exact picker field');
  }
  function companyDiscoveryRule(e,action,cap) {
    if(action!=='company')return null;
    const company=companyCapability(cap);
    if(name(e)!==company)throw Error('company exact authorized name required');
    const fail=()=>{throw Error('unreviewed configured company row');};
    const prefix='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__';
    const classes=x=>String(x?.getAttribute('class')||'').split(/\s+/);
    const u=new URL(location.href),gid=u.searchParams.getAll('groupid');
    if(action!=='company'||u.origin!==P.origin||(!cap.sourceEntry&&!['/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management'].includes(u.pathname))||(!cap.sourceEntry&&(gid.length!==1||!/^\d+$/.test(gid[0])))||e.tagName!=='DIV'||role(e)!=='generic'||e.children.length!==0||e.getAttribute('class')!=='name_4a8f8'||e.closest('form')||e.closest('a'))fail();
    const loginRoot=companyPickerRoot(cap);
    const modal=loginRoot||e.closest('[class*="'+prefix+'login-modal--"]');
    const roots=loginRoot?[loginRoot]:Array.from(document.querySelectorAll('[class*="'+prefix+'login-modal--"]')).filter(visible);
    if(!modal||modal.querySelector('iframe,form')||roots.length!==1||roots[0]!==modal||(!loginRoot&&(!classes(modal).includes('life-core-modal-show')||!classes(modal).includes('life-core-modal')))||!visible(modal))fail();
    const fields=Array.from(modal.querySelectorAll('input[placeholder="搜索商户"]')).filter(visible);
    const matches=Array.from(modal.querySelectorAll('.name_4a8f8')).filter(x=>visible(x)&&name(x)===company);
    const titles=Array.from(modal.querySelectorAll('[class*="'+prefix+'title--"]')).filter(x=>visible(x)&&name(x)==='切换公司');
    const row=e.closest('.box-account-item_4a8f8'),list=e.closest('.card__list_582b9');
    if(loginRoot&&(!modal.contains(e)||!list||!list.contains(e)))fail();
    if(fields.length!==1||fields[0].tagName!=='INPUT'||fields[0].value!==company||fields[0].disabled||fields[0].readOnly||matches.length!==1||matches[0]!==e||(!loginRoot&&titles.length!==1)||!row||!list||!list.contains(row)||!modal.contains(list)||e.parentElement?.getAttribute('class')!=='main_4a8f8'||e.parentElement.parentElement!==row)fail();
    return {kind:'company',scope:'configured-exact-company-row-v2'};
  }

  // Candidate only: the bridge must first verify the matching backup.
  function retainedExportDeleteRule(e,action,scope){
    if(action!=='backed-up-export-delete')return null;
    if(location.pathname!=='/p/fulfillsettle/export_records/20101'||!scope||typeof scope!=='object')throw Error('retention scope required');
    const u=new URL(location.href);
    if(u.searchParams.getAll('groupid').length!==1||u.searchParams.get('groupid')!==scope.groupid||!/^\d+$/.test(scope.groupid||''))throw Error('retention company mismatch');
    const row=e.closest('.byted-table-column.byted-table-row');
    if(!row||!visible(row)||name(row)!==scope.recordText||e.tagName!=='SPAN'||name(e)!=='删除'||e.closest('form,a'))throw Error('retention exact row required');
    const rows=[...document.querySelectorAll('.byted-table-column.byted-table-row')].filter(x=>visible(x)&&name(x)===scope.recordText);
    const controls=[...row.querySelectorAll('span')].filter(x=>visible(x)&&name(x)==='删除'&&!x.disabled);
    if(rows.length!==1||controls.length!==1||controls[0]!==e)throw Error('retention row or control ambiguous');
    return {kind:'backed-up-export-delete'};
  }

  function retainedExportConfirmRule(e,action,scope){
    if(action!=='backed-up-export-confirm')return null;
    if(location.pathname!=='/p/fulfillsettle/export_records/20101'||!scope||typeof scope!=='object')throw Error('retention confirmation scope required');
    const u=new URL(location.href);
    if(u.searchParams.getAll('groupid').length!==1||u.searchParams.get('groupid')!==scope.groupid||!/^\d+$/.test(scope.groupid||''))throw Error('retention confirmation company mismatch');
    const rows=[...document.querySelectorAll('.byted-table-column.byted-table-row')].filter(x=>visible(x)&&name(x)===scope.recordText);
    const modals=[...document.querySelectorAll('.byted-modal.byted-modal-show')].filter(visible);
    const modal=e.closest('.byted-modal.byted-modal-show');
    if(rows.length!==1||modals.length!==1||modals[0]!==modal||name(modal)!=='确认删除提醒 删除后不可恢复，确定要删除吗？ 确认删除 取消'||e.tagName!=='BUTTON'||name(e)!=='确认删除'||e.closest('form,a'))throw Error('retention confirmation exact modal required');
    const buttons=[...modal.querySelectorAll('button')].filter(x=>visible(x)&&name(x)==='确认删除'&&!x.disabled);
    if(buttons.length!==1||buttons[0]!==e)throw Error('retention confirmation ambiguous');
    return {kind:'backed-up-export-confirm'};
  }

  function assertSafe(e, action, companyCap, retentionScope) {
    if (!visible(e) || e.disabled || e.getAttribute('aria-disabled')==='true') throw Error('not visible or enabled');
    const n=name(e), r=role(e);
    const readComplaint=location.pathname==='/p/life_comment/management' && ((['查看投诉结果','投诉审核中'].includes(n)&&action==='complaint-read')||(n==='投诉'&&action==='complaint-draft')); 
    if(n==='投诉审核中'){
      const classes=String(e.getAttribute('class')||'').split(/\s+/),card=e.closest('.commentItem-jrXo5p');
      if(action!=='complaint-read'||location.pathname!=='/p/life_comment/management'||e.tagName!=='DIV'||e.children.length!==0||!classes.includes('button-vhqEd7')||!classes.includes('isHighlight-DoxxP4')||!card||!visible(card))throw Error('unreviewed complaint pending read entry');
    }
    const configuredCompany=action==='company'?companyDiscoveryRule(e,action,companyCap):null;
    const retention=retainedExportDeleteRule(e,action,retentionScope)||retainedExportConfirmRule(e,action,retentionScope);
    if(blocked.test(n)&&!readComplaint&&!configuredCompany&&!retention) throw Error('forbidden business write control');
    const href=e.closest('a')?.getAttribute('href');
    if(href && (/^(javascript|data):/i.test(href) || new URL(href,location.href).origin!==P.origin)) throw Error('external or executable navigation forbidden');
    const frameClose=governanceFrameDrawerCloseRule(e,action);
    const drawerClose=frameClose||complaintDrawerCloseRule(e,action)||governanceDrawerCloseRule(e,action);
    const governance=governanceStopLossReturnRule(e)||governanceCalendarRule(e)||governanceRule(e);
    if(e.closest('form') && (e.type==='submit' || e.tagName==='BUTTON' && !e.getAttribute('type')) && !(action==='filter'&&governance?.scope==='governance-records-query')) throw Error('form submission forbidden');
    if(governanceRoot(e)&&!governance)throw Error('governance action not reviewed');
    let rule=retention||configuredCompany||exportRecordsPagerRule(e)||normalReviewPagerRule(e,action)||commentStatusOpenRule(e,action)||commentToolboxRule(e,action)||drawerClose||governance||P.clicks.find(x=>x.name===n && (!x.role || x.role===r));
    if(/^全部评价\s+\d+$/.test(n)) rule={kind:'navigation'};
    if(/^([1-9]|[12][0-9]|3[01])$/.test(n) && e.closest(P.dateCellSelector)) rule={kind:'filter'};
    if(r==='textbox' && P.filterPlaceholders.includes(e.getAttribute('placeholder'))) rule={kind:'filter'};
    if(!rule) throw Error('not in offline reviewed click allowlist');
    if(action && rule.kind!==action) throw Error('action kind does not match reviewed policy');
    if(n==='切换'){
      // Reviewed HeaderV3 merchant switch only. No generic page switch button.
      const userPrefix='src-components-HeaderV3-components-UserCard-index-module__outer--';
      const switchPrefix='src-components-HeaderV3-components-UserCard-components-SwitchCard-index-module__switch-card--';
      const buttonPrefix='src-components-HeaderV3-components-UserCard-components-SwitchCard-index-module__switch-card-button--';
      const hasClass=(el,prefix)=>!!el&&String(el.getAttribute('class')||'').split(/\s+/).some(token=>token.startsWith(prefix));
      const card=e.closest('[class*="'+userPrefix+'"]'),switchCard=e.closest('[class*="'+switchPrefix+'"]');
      const cards=[...document.querySelectorAll('[class*="'+userPrefix+'"]')].filter(visible);
      const text=normalize(card?.innerText),switchText=normalize(switchCard?.innerText);
      const merchant=switchText.match(/^商户 (服务商[0-9]+) 切换$/);
      const providers=[...new Set(text.match(/服务商[0-9]+/g)||[])];
      const accounts=[...new Set([...text.matchAll(/账户ID\s*[：:]?\s*([0-9]{8,})\s*复制/g)].map(x=>x[1]))];
      const managers=[...text.matchAll(/我的客户经理\s*[：:]?\s*(.+?)(?=\s*退出登录)/g)].map(x=>x[1].trim());
      const buttons=switchCard?[...switchCard.querySelectorAll('button')].filter(x=>visible(x)&&name(x)==='切换'):[];
      if(action!=='navigation'||r!=='button'||e.tagName!=='BUTTON'||!hasClass(e,buttonPrefix)||!hasClass(card,userPrefix)||!hasClass(switchCard,switchPrefix)||!visible(card)||!visible(switchCard)||!card.contains(switchCard)||cards.length!==1||cards[0]!==card||buttons.length!==1||buttons[0]!==e||!merchant||providers.length!==1||providers[0]!==merchant[1]||accounts.length!==1||managers.length!==1||!managers[0]||managers[0].length>100||text.length>=800)throw Error('unreviewed merchant-switch structure forbidden');
    }
    if(rule.kind==='onboarding-dismiss'){
      const modal=e.closest('[class*="src-pages-HomeV3-components-Guide-index-module__guide-modal--"]');
      const painted=modal&&visible(modal)&&[modal,e].every(x=>Number(getComputedStyle(x).opacity??1)===1);
      if(action!=='onboarding-dismiss'||!painted||!['新来客 新生意','抖音来客全新升级!','导航升级','首页升级'].every(t=>normalize(modal.innerText||'').includes(t)))throw Error('unreviewed onboarding modal forbidden');
    }
    if(rule.kind==='company-confirm') {
      companyCapability(companyCap);
      if(companyCap.sourceEntry)throw Error('company login no invented confirmation');
      const searchFields=Array.from(document.querySelectorAll('input[placeholder="搜索商户"]')).filter(visible);
      if(searchFields.length!==1||searchFields[0].value!==companyCap.company)throw Error('company confirm exact current search required');
      // Generic Confirm is only allowed inside the inspected switch-company dialog.
      // The real modal renders as a plain portal <div> (no role=dialog / .byted-modal), so anchor on
      // the structural signature instead: nearest ancestor that both shows 切换公司 and owns the
      // 搜索商户 input. Same safety intent, no dependency on a class name the site does not use.
      const isDialogRoot=x=>{
        try{
          return normalize(x.innerText || '').includes('切换公司') && !!x.querySelector('input[placeholder="搜索商户"]');
        }catch(_){return false;}
      };
      let modal=e.closest('[role=dialog],.byted-modal');
      if(!isDialogRoot(modal)){
        modal=null;
        for(let p=e.parentElement,n=0;p&&n<20;p=p.parentElement,n++){ if(isDialogRoot(p)){modal=p;break;} }
      }
      if(!modal) throw Error('Confirm outside switch-company dialog forbidden');
    }
    return rule;
  }
  // Semantic DOM events only: no coordinates, hit-testing, private properties or handlers.
  function hoverSeq(e) {
    const fire=(el,type,enter)=>{
      if(typeof el.dispatchEvent!=='function'||typeof MouseEvent==='undefined')return;
      el.dispatchEvent(new MouseEvent(type,{bubbles:!enter,cancelable:true,composed:true}));
    };
    const ancestors=[];for(let p=e.parentElement;p&&p!==document.body;p=p.parentElement)ancestors.unshift(p);
    for(const el of [...ancestors,e]){fire(el,'mouseenter',true);fire(el,'mouseover',false);}
  }
 function accountHoverExit(c){
  const need=(v,code)=>{if(!v)throw Error(code)},has=(e,p)=>String(e?.getAttribute('class')||'').split(/\s+/).some(x=>x.startsWith(p));
  need(Object.keys(c).sort().join(',')==='channel,groupid,kind,locator,op,tabId,value','account-dismiss-fields-invalid');
  need(c.op==='hover'&&c.kind==='account-hover-exit'&&Number.isSafeInteger(c.tabId)&&c.tabId>0&&/^\d+$/.test(c.groupid)&&new URL(location.href).searchParams.getAll('groupid').length===1&&new URL(location.href).searchParams.get('groupid')===c.groupid&&location.pathname==='/p/life_comment/management','account-dismiss-scope-mismatch');
  const id=c.value;need(id&&Object.keys(id).sort().join(',')==='account_id,manager,provider'&&/^服务商\d+$/.test(id.provider)&&/^\d{8,}$/.test(id.account_id)&&typeof id.manager==='string'&&id.manager.length>0&&id.manager.length<100,'account-dismiss-identity-invalid');
  need(c.locator&&Object.keys(c.locator).sort().join(',')==='by,value'&&c.locator.by==='selector','account-dismiss-exact-selector-required');
  const trigger=one(c.locator),version=has(trigger,'src-components-HeaderV2-components-Profile-index-module__title--')?'V2':has(trigger,'src-components-HeaderV3-components-Profile-index-module__title--')?'V3':null;
  need(visible(trigger)&&trigger.tagName==='DIV'&&version&&normalize(trigger.innerText)===id.provider,'account-dismiss-trigger-unreviewed');
  const prefix='src-components-Header'+version+'-components-',wrapper=trigger.closest('[class*="'+prefix+'Profile-index-module__wrap-profile--"]');need(wrapper&&visible(wrapper),'account-dismiss-wrapper-unverified');
  const cards=[...document.querySelectorAll('[class*="'+prefix+'UserCard-index-module__outer--"]')].filter(visible);need(cards.length===1&&wrapper.contains(cards[0]),'account-dismiss-card-not-unique');const card=cards[0],text=normalize(card.innerText);
  need(text.length<800&&['账户ID','手机号','我的客户经理'].every(x=>text.includes(x)),'account-dismiss-card-fields-missing');
  const providers=[...new Set(text.match(/服务商\d+/g)||[])],accounts=[...new Set([...text.matchAll(/账户ID\s*[：:]?\s*([0-9]{8,})\s*复制/g)].map(m=>m[1]))],manager=text.match(version==='V2'?/我的客户经理\s*(.+?)\s*切换公司\s*退出登录$/:/我的客户经理\s*[：:]?\s*(.+?)\s*退出登录$/);
  const buttons=[...card.querySelectorAll('button')].filter(visible);
  need(providers.length===1&&providers[0]===id.provider&&accounts.length===1&&accounts[0]===id.account_id&&manager&&manager[1]===id.manager&&buttons.length===2&&normalize(buttons[0].innerText)===(version==='V2'?'切换公司':'切换')&&normalize(buttons[1].innerText)==='退出登录','account-dismiss-current-identity-or-controls-mismatch');
  if(version==='V3'){
    const switchPrefix=prefix+'UserCard-components-SwitchCard-index-module__switch-card--',buttonPrefix=prefix+'UserCard-components-SwitchCard-index-module__switch-card-button--';
    const switches=[...card.querySelectorAll('[class*="'+switchPrefix+'"]')].filter(visible);
    need(switches.length===1&&card.contains(switches[0])&&normalize(switches[0].innerText)==='商户 '+id.provider+' 切换','account-dismiss-merchant-switch-unverified');
    const controls=[...switches[0].querySelectorAll('button')].filter(visible);
    need(controls.length===1&&controls[0]===buttons[0]&&buttons[0].tagName==='BUTTON'&&has(buttons[0],buttonPrefix),'account-dismiss-merchant-switch-controls-unverified');
  }
  need(![...document.querySelectorAll('[role="dialog"],.byted-modal,.byted-modal-wrap,.byted-drawer-dialog-show')].some(visible)&&![...document.querySelectorAll('input[placeholder="搜索商户"]')].some(visible),'account-dismiss-dialog-or-company-switch-open');
  need(document.body&&!wrapper.contains(document.body),'account-dismiss-related-target-not-outside');
  const fire=(el,type,bubbles)=>el.dispatchEvent(new MouseEvent(type,{bubbles,cancelable:true,composed:true,relatedTarget:document.body}));
  // React derives onMouseLeave from normal bubbling mouseout + relatedTarget.
  // Native mouseleave listeners are notified on the observed card/wrapper only.
  fire(card,'mouseout',true);fire(card,'mouseleave',false);fire(wrapper,'mouseleave',false);
  return {action:'account-hover-exit-events-dispatched',event_sequence:['card:mouseout','card:mouseleave','wrapper:mouseleave'],related_target:'document.body',trusted_event_fabrication:false,business_clicks:false,closure_verified:false,requires_readonly_tree_recheck:true};
 }
  function readTree(locator){
        const root=locator?one(locator):document.body,opacityMemo=new WeakMap(),invisibleErrorBranches=new WeakSet();
        // innerText includes opacity-zero descendants. Prune only this exact
        // invisible error and ancestors containing NOTHING but its same text,
        // otherwise aggregate wrapper names would invent an orphan error leaf.
        if(location.pathname==='/p/life_comment/management') {
          const messages=Array.from(document.querySelectorAll('.life-core-message-content'));
          if(messages.length>64)throw Error('system-error-toast-count-unverified');
          for(const message of messages) {
            if(normalize(message.innerText)!=='系统错误，请稍后再试'||opacityVisible(message,opacityMemo,getComputedStyle(message)))continue;
            for(let n=message;n&&n!==document.body;n=n.parentElement) {
              if(normalize(n.innerText)!=='系统错误，请稍后再试')break;
              invisibleErrorBranches.add(n);
            }
          }
        }
        let count=0, truncated=false;
        function walk(e,depth) {
          if(invisibleErrorBranches.has(e)||!visibleInRead(e,opacityMemo)) return null;
          if(count++>=P.maxNodes) {truncated=true;return null;}
          const out=node(e); out.depth=depth;
          out.children=Array.from(e.children).map(c=>walk(c,depth+1)).filter(Boolean);
          if(out.public_frame?.document_available===true&&out.public_frame.source_same_origin===true&&out.public_frame.source_path==='/h5/governance/violation_talent_notice'&&out.public_frame.document_path==='/h5/governance/violation_talent_notice'&&out.public_frame.ready_state==='complete'){
            const doc=e.contentDocument,frameBody=doc?.body;
            if(frameBody){
              assertNoticeFrameNoControls(doc);
              const frameSelector=out.selector;
              function frameWalk(element,d){
                if(!visibleInRead(element,opacityMemo)||['INPUT','TEXTAREA'].includes(element.tagName))return null;
                if(count++>=P.maxNodes){truncated=true;return null;}
                const n=node(element);n.depth=d;n.selector='readonly-frame:'+frameSelector+' :: '+selector(element);
                n.children=Array.from(element.children).map(c=>frameWalk(c,d+1)).filter(Boolean);return n;
              }
              const frameRoot=frameWalk(frameBody,0),url=new URL(doc.URL);
              if(e.contentDocument!==doc||doc.readyState!=='complete'||url.origin!==location.origin||url.pathname!=='/h5/governance/violation_talent_notice')throw Error('public notice frame document changed during read');
              out.public_frame_dom={kind:'same-origin public notice DOM (read-only)',url:url.origin+url.pathname,frame_selector:frameSelector,input_enabled:false,root:frameRoot};
            }
          }
          return out;
        }
        return {kind:'DOM-derived semantic tree (not native AX)',url:location.origin+location.pathname,root:walk(root,0),truncated};
  }
  const listener=(m,s,respond)=>{
    if(s.id!==chrome.runtime.id || m?.channel!=='local-dom-export-v1') return;
    try {
      if(location.origin!==P.origin) throw Error('site not allowed');
      const risk=Array.from(document.querySelectorAll('[role=dialog],.byted-modal')).filter(visible).some(e=>/安全验证|滑块验证|风险验证|账号异常|扫码登录/.test(e.innerText));
      if(risk) throw Error('risk-or-login-prompt: stop and hand off');
      let result;
      if(m.op==='dom-region-proof'){
        globalThis.__localRegionProof.proof(m,one,readTree).then(result=>respond({ok:true,result})).catch(e=>respond({ok:false,error:String(e.message||e)}));return true;
      }
      if(m.op==='review-viewport-proof'){
        globalThis.__localReviewProof.proof(m,one,readTree).then(result=>respond({ok:true,result})).catch(e=>respond({ok:false,error:String(e.message||e)}));return true;
      }
      if(m.op==='viewport-proof'){
        globalThis.__localViewportProof.proof(m,one,readTree).then(result=>respond({ok:true,result})).catch(e=>respond({ok:false,error:String(e.message||e)}));return true;
      }
      if(m.op==='ping') result={version:VERSION,content_build:BUILD,company_selection_policy:COMPANY_POLICY,governance_compact_records_policy:'observed-compact-record-entry-v1',governance_analysis_tab_policy:'observed-analysis-tab-v1',governance_center_layout_policy:'observed-return-legacy-v1',governance_query_policy:'observed-dom-20261021-v1',governance_calendar_policy:'date-item-div-v3-single',governance_detail_policy:'notice-drawer-close-v1',governance_frame_detail_policy:'same-origin-notice-frame-v1',governance_stop_loss_policy:'public-notice-return-v1',governance_rate_stop_loss_policy:'observed-arrow-no-effect-disabled-v1',safety:'DOM-only',url:location.origin+location.pathname,title:document.title};
      else if(m.op==='tree') {
        result=readTree(m.locator);
      } else if(m.op==='find') result=resolve(m.locator).slice(0,100).map(node);
      else if(m.op==='click') {
        const e=one(m.locator);const rule=assertSafe(e,m.kind,m.companyCapability,m.value);
        e.click();
        result={clicked:node(e),kind:rule.kind,version:VERSION};
      }
      else if(m.op==='hover'&&m.kind==='account-hover-exit') {result=accountHoverExit(m);}
      else if(m.op==='hover') {
        // 只展开/浮现，不点击：用于 hover 触发的下拉与子菜单（如导出菜单的「导出评价」）。
        const e=one(m.locator);const rule=assertSafe(e,m.kind,m.companyCapability,m.value);
        hoverSeq(e);
        result={hovered:node(e),kind:rule.kind};
      }
      else if(m.op==='scroll') {
        const e=one(m.locator);e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});result={scrolled:node(e),version:VERSION};
      }
      else if(m.op==='filter') {
        const e=one(m.locator);
        if(governanceDate(e))throw Error('governance date picker open-only; observe calendar first');
        if(!P.filterPlaceholders.includes(e.getAttribute('placeholder')) || !['INPUT','TEXTAREA'].includes(e.tagName)) throw Error('only reviewed search/date filter inputs can be filled');
        if(e.readOnly || e.disabled) throw Error('readonly input: use calendar DOM cells');
        const value=String(m.value || '');
        if(value.length>100 || /[\r\n]/.test(value)) throw Error('invalid filter value');
        if(e.getAttribute('placeholder')==='搜索商户'){companySearchField(e,m.companyCapability);if(m.companyCapability.company!==value)throw Error('company filter must equal approved exact name');}
        if(e.getAttribute('placeholder')!=='搜索商户' && !/^\d{4}-\d{2}-\d{2}( ~ \d{4}-\d{2}-\d{2})?$/.test(value)) throw Error('invalid date');
        const setter=Object.getOwnPropertyDescriptor(e.tagName==='INPUT'?HTMLInputElement.prototype:HTMLTextAreaElement.prototype,'value').set;
        setter.call(e,value);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));result={filtered:node(e)};
      } else throw Error('unsupported operation');
      respond({ok:true,result});
    } catch(e) {respond({ok:false,error:String(e.message || e)});}
  };
  chrome.runtime.onMessage.addListener(listener);
  globalThis.__localDomExportController={version:VERSION,build:BUILD,company_policy:COMPANY_POLICY,revision:REVISION,listener};
})();

