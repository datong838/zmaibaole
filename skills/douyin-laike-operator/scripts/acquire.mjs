/* Existing Codex Chrome API only. Declarations for cua_repl, NOT a standalone driver.
 * No debugger/ports, cookies, page storage, React internals or coordinate actions.
 * Each public method is one resumable operator step. Read DOM between mutations.
 */
var douyinLaikeOperator = {
  normalize(s) { return String(s||'').normalize('NFKC').replace(/[^\p{L}\p{N}]/gu,'').toLowerCase(); },
  matchCompany(target,names) {
    const norm=s=>this.normalize(s), variants=s=>{const n=norm(s);return [n,n.replace(/(?:集团有限公司|股份有限公司|有限责任公司|有限公司)$/,'')].filter(Boolean);};
    let exact=names.filter(n=>norm(n)===norm(target));
    if(!exact.length)exact=names.filter(n=>variants(n).some(x=>variants(target).includes(x)));
    if(exact.length===1)return exact[0];
    if(exact.length>1)throw Error('company-ambiguous');
    const included=names.filter(n=>variants(n).some(x=>variants(target).some(y=>x.includes(y)||y.includes(x))));
    if(included.length===1)return included[0];
    throw Error(included.length?'company-ambiguous':'company-not-found');
  },
  async create(browser,tab,job) {
    if(job.action!=='acquire' && job.action!=='return-company')throw Error('work-order-invalid');
    if(!/^\d+$/.test(String(job.groupid)) || !job.company)throw Error('work-order-invalid');
    const op=Object.create(this);op.browser=browser;op.tab=tab;op.job=job;op.stages=[];
    op.submitted=!!job.resume?.export_pending;op.downloadPromise=null;
    const checkpoints=job.resume?.checkpoints||[];
    const filter=checkpoints.filter(c=>c.stage==='filter').pop(),record=checkpoints.filter(c=>c.stage==='export-generated').pop();
    if(filter)op.pageFiltered=filter.page_filtered;
    if(record)op.generatedAt=record.generated_at;
    op.downloadUncertain=checkpoints.some(c=>c.stage==='download-intent')&&!checkpoints.some(c=>c.stage==='download-complete');
    return op;
  },
  async observe(tab=this.tab) {
    const url=new URL(await tab.url());
    if(url.origin!=='https://life.douyin.com')throw Error('origin-not-allowed');
    if(this.contextVerified && url.searchParams.get('groupid')!==String(this.job.groupid))throw Error('source-company-mismatch');
    const snapshot=await tab.playwright.domSnapshot();
    if(/安全验证|滑块验证|扫码登录|账号异常|风险验证|请完成验证/.test(snapshot))throw Error('risk-prompt');
    return {url:url.href,groupid:url.searchParams.get('groupid'),snapshot};
  },
  async unique(locator) {
    if(await locator.count()!==1)throw Error('locator-ambiguous-or-missing');
    if(!await locator.isVisible() || !await locator.isEnabled())throw Error('element-not-ready');
    return locator;
  },
  async clickText(text,tab=this.tab) {
    if(/回复|投诉|发送|发布|删除|支付|购买|退出登录|保存设置/.test(text))throw Error('business-write-forbidden');
    if(!['导出','导出评价','评价导出记录'].includes(text) && text!==this.companyChoice)throw Error('unreviewed-control');
    const target=await this.unique(tab.playwright.getByText(text,{exact:true}));
    await target.click({timeoutMs:5000});return this.observe(tab);
  },
  async account() {
    await this.observe();
    const menu=this.tab.playwright.getByRole('button',{name:'切换公司',exact:true});
    if(!await menu.isVisible()){
      const trigger=await this.unique(this.tab.playwright.getByText(/^服务商\d+$/));
      await trigger.click({timeoutMs:5000});await this.observe();
    }
    const identity=await this.tab.playwright.evaluate(()=>{
      const text=document.body.innerText;
      return {provider:(text.match(/服务商\d+/)||[])[0]||'',account_id:(text.match(/账户ID\s*(\d{8,})/)||[])[1]||'',manager:(text.match(/我的客户经理\s*([^\n]+)/)||[])[1]?.trim()||''};
    });
    if(Object.values(identity).some(v=>!v))throw Error('identity-unverified');
    if(this.job.identity_baseline && JSON.stringify(identity)!==JSON.stringify(this.job.identity_baseline)){
      const keys=['provider','account_id','manager'];
      if(keys.some(k=>identity[k]!==this.job.identity_baseline[k]))throw Error('account-changed');
    }
    if(this.identityBefore && ['provider','account_id','manager'].some(k=>identity[k]!==this.identityBefore[k]))throw Error('account-changed');
    if(!this.identityBefore)this.identityBefore={...identity};
    this.identity=identity;return {stage:'identity',identity};
  },
  async openSwitch() {
    await this.account();
    const button=await this.unique(this.tab.playwright.getByRole('button',{name:'切换公司',exact:true}));
    await button.click({timeoutMs:5000});return this.observe();
  },
  async searchCompany() {
    await this.observe();
    const input=await this.unique(this.tab.playwright.getByPlaceholder('搜索商户',{exact:true}));
    await input.fill(this.job.company,{timeoutMs:5000});return this.observe();
  },
  async chooseCompany() {
    await this.observe();
    const names=await this.tab.playwright.getByPlaceholder('搜索商户',{exact:true}).evaluate((input,{company})=>{
      const modal=input.closest('[role=dialog],.byted-modal,.arco-modal');
      if(!modal)throw Error('company-dialog-structure-unknown');
      return Array.from(modal.querySelectorAll('div,span,p')).filter(e=>e.getClientRects().length && !e.children.length)
        .map(e=>(e.innerText||'').trim()).filter(s=>s.length>=4 && (s.endsWith('公司') || s===company));
    },{company:this.job.company});
    const selected=this.matchCompany(this.job.company,[...new Set(names)]);
    this.companyChoice=selected;
    return this.clickText(selected);
  },
  async confirmSwitch() {
    await this.observe();
    const input=this.tab.playwright.getByPlaceholder('搜索商户',{exact:true});
    if(await input.isVisible()){
      const confirm=await this.unique(this.tab.playwright.getByRole('button',{name:'确认',exact:true}));
      await confirm.click({timeoutMs:5000});
    }
    return this.observe();
  },
  async verifySwitch() {
    const current=await this.observe();
    if(current.groupid!==String(this.job.groupid))throw Error('source-company-mismatch');
    const account=await this.account();
    if(this.identityBefore && ['provider','account_id','manager'].some(k=>account.identity[k]!==this.identityBefore[k]))throw Error('account-changed');
    this.identityVerified=true;this.contextVerified=true;
    return {stage:'switch',company:this.job.company,groupid:current.groupid,identity:account.identity};
  },
  async openReviews() {
    const current=await this.observe();
    if(current.groupid!==String(this.job.groupid))throw Error('source-company-mismatch');
    const all=this.tab.playwright.getByText(/^全部评价\s*\d+$/);
    if(!await all.isVisible()){
      const nav=await this.unique(this.tab.playwright.getByRole('complementary').getByText('评价管理',{exact:true}));
      await nav.click({timeoutMs:5000});await this.observe();
    }
    // Also closes account overlay by a reviewed main heading click if present.
    const heading=this.tab.playwright.getByRole('main').getByText('评价管理',{exact:true});
    if(await heading.count()===1)await heading.click({timeoutMs:5000});
    await this.observe();
    await (await this.unique(all)).click({timeoutMs:5000});return this.observe();
  },
  async context(){return this.observe();},
  async openPageCalendar() {
    await this.observe();
    await (await this.unique(this.tab.playwright.getByRole('textbox',{name:'评价时间',exact:true}))).click({timeoutMs:5000});
    return this.observe();
  },
  async calendarDate(iso) {
    const day=String(Number(iso.slice(8,10))), month=iso.slice(0,4)+'年'+Number(iso.slice(5,7))+'月';
    const matches=await this.tab.playwright.getByText(day,{exact:true}).evaluateAll((elements,{month})=>{
      function path(e){const out=[];while(e&&e!==document.body){if(e.id){out.unshift('#'+CSS.escape(e.id));break;}const same=Array.from(e.parentElement?.children||[]).filter(c=>c.tagName===e.tagName);out.unshift(e.tagName.toLowerCase()+`:nth-of-type(${same.indexOf(e)+1})`);e=e.parentElement;}return out.join(' > ');}
      return elements.filter(e=>{
        if(!e.getClientRects().length || !e.closest('.byted-date-col'))return false;
        let p=e.parentElement;
        while(p && p!==document.body){const months=(p.innerText||'').match(/\d{4}年\d{1,2}月/g)||[];if(months.length)return months.length===1&&months[0]===month;p=p.parentElement;}
        return false;
      }).map(path);
    },{month});
    if(matches.length!==1)throw Error('calendar-date-not-unique-or-month-not-visible: inspect month DOM; no positional fallback');
    await this.tab.playwright.locator(matches[0]).click({timeoutMs:5000});return this.observe();
  },
  async verifyFilter() {
    if(!this.identityVerified || !this.contextVerified)throw Error('identity-unverified');
    const current=await this.observe();
    const inputs=await this.tab.playwright.getByRole('textbox').evaluateAll(es=>es.map(e=>({label:e.getAttribute('aria-label')||'',placeholder:e.getAttribute('placeholder'),value:e.value||''})));
    const start=this.job.date_range.start,end=this.job.date_range.end;
    if(!inputs.some(i=>i.value===`${start} ~ ${end}`))throw Error('filter-date-unverified');
    const filtered=[...current.snapshot.matchAll(/已筛选\s*(\d+)\s*条/g)].map(m=>Number(m[1]));
    if(filtered.length!==1)throw Error('page-count-unverified');
    // Existing non-date filters must remain 全部. Unexpected state is handed back.
    for(const name of ['评价类型','评价来源','评价状态']){
      const box=this.tab.playwright.getByRole('textbox',{name,exact:true});
      if(await box.count()!==1 || await box.evaluate(e=>e.value)!=='全部')throw Error('nondefault-filter: '+name);
    }
    this.pageFiltered=filtered[0];
    return {stage:'filter',groupid:current.groupid,date_range:{start,end},page_filtered:filtered[0],pagination_count:Number((current.snapshot.match(/共\s*(\d+)\s*条记录/)||[])[1])||null};
  },
  async openExportMenu(){return this.clickText('导出');},
  async openExportDialog(){return this.clickText('导出评价');},
  async exportRange() {
    await this.observe();
    const input=await this.unique(this.tab.playwright.getByPlaceholder('请选择日期范围，不选则为近一年',{exact:true}));
    const value=await input.evaluate(e=>e.value);
    const desired=this.job.date_range.start+' ~ '+this.job.date_range.end;
    return {value,desired,correct:value===desired};
  },
  async openExportCalendar() {
    const input=await this.unique(this.tab.playwright.getByPlaceholder('请选择日期范围，不选则为近一年',{exact:true}));
    await input.click({timeoutMs:5000});return this.observe();
  },
  async prepareSubmit() {
    if(this.submitted)throw Error('export-outcome-unknown: inspect existing task, do not resubmit');
    if(!this.identityVerified || !this.contextVerified)throw Error('identity-unverified');
    if(this.pageFiltered===undefined)throw Error('page-count-unverified');
    if(!(await this.exportRange()).correct)throw Error('export-range-mismatch');
    this.submitIntent={stage:'export-intent',company:this.job.company,groupid:String(this.job.groupid),date_range:{start:this.job.date_range.start,end:this.job.date_range.end},at:new Date().toISOString()};
    return this.submitIntent; // Caller must persist using flow.py checkpoint BEFORE submit().
  },
  async submit(intentRecorded) {
    if(intentRecorded!==true || !this.submitIntent || this.submitted)throw Error('export-intent-not-recorded-or-already-submitted');
    if(!this.identityVerified || !this.contextVerified)throw Error('identity-unverified');
    if(!(await this.exportRange()).correct)throw Error('export-range-mismatch');
    this.submitted=true;
    const button=await this.unique(this.tab.playwright.getByRole('button',{name:'导出',exact:true}));
    await button.click({timeoutMs:5000});
    return {stage:'export-submitted',...this.submitIntent,stage:'export-submitted'};
  },
  async recordTabs() {
    const tabs=await this.browser.tabs.list();
    return tabs.filter(t=>{try{const u=new URL(t.url);return u.origin==='https://life.douyin.com'&&u.pathname.includes('/export_records/')&&u.searchParams.get('groupid')===String(this.job.groupid);}catch{return false;}});
  },
  async openRecordMenu(){return this.clickText('评价导出记录');},
  async useRecordTab(tabId) {
    // tabId must come from recordTabs(); no guessed URL navigation.
    const allowed=await this.recordTabs();if(!allowed.some(t=>t.id===tabId))throw Error('record-tab-not-observed');
    this.records=await this.browser.tabs.get(tabId);return this.observe(this.records);
  },
  async listRecords() {
    await this.observe(this.records);
    return this.records.playwright.locator('.byted-table-row').evaluateAll(rows=>rows.map(row=>({
      text:row.innerText,
      generated_at:(row.innerText.match(/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/)||[])[0]?.replace(/\s+/g,' ')||null,
      state:row.innerText.includes('生成成功')?'success':/生成失败|导出失败/.test(row.innerText)?'failed':'pending'
    })));
  },
  async verifyRecord(generatedAt) {
    const records=await this.listRecords(),tag=`门店评价_全部门店_${this.job.date_range.start.replace(/-/g,'_')}-${this.job.date_range.end.replace(/-/g,'_')}`;
    const matching=records.filter(r=>r.generated_at===generatedAt && r.text.includes(tag));
    if(matching.length!==1 || matching[0].state!=='success')throw Error('generated-record-unverified');
    this.generatedAt=generatedAt;return {stage:'export-generated',groupid:String(this.job.groupid),record_name:tag,generated_at:generatedAt,record_url:await this.records.url()};
  },
  async armDownload() {
    if(this.downloadUncertain)throw Error('download-outcome-unknown: reconcile local downloads before another click');
    if(!this.generatedAt || !this.downloadTarget || this.downloadPromise)throw Error('download-record-unverified-or-already-armed');
    this.downloadPromise=this.records.playwright.waitForEvent('download',{timeoutMs:120000}).then(download=>({ok:true,download}),error=>({ok:false,error:String(error)}));
    return {stage:'download-intent',groupid:String(this.job.groupid),generated_at:this.generatedAt};
  },
  async clickDownload(intentRecorded) {
    if(!this.downloadPromise || !this.downloadTarget || intentRecorded!==true || this.downloadClicked)throw Error('download-not-armed-or-duplicate');
    this.downloadClicked=true;await this.downloadTarget.click({timeoutMs:5000});return {clicked:true,generated_at:this.generatedAt};
  },
  async prepareDownload() {
    if(!this.generatedAt)throw Error('download-record-unverified');
    await this.observe(this.records);
    const row=this.records.playwright.locator('.byted-table-row').filter({has:this.records.playwright.getByText(this.generatedAt,{exact:true})});
    this.downloadTarget=await this.unique(row.getByText('下载',{exact:true}));
    return {ready:true,generated_at:this.generatedAt};
  },
  async downloadResult() {
    if(!this.downloadPromise || !this.downloadClicked)throw Error('download-not-started');
    const event=await this.downloadPromise;if(!event.ok)throw Error('download-unverified: '+event.error);
    const source=await event.download.path({timeoutMs:30000});
    if(!source)throw Error('download-path-missing');
    return {company:this.job.company,groupid:String(this.job.groupid),source,
      date_range:{start:this.job.date_range.start,end:this.job.date_range.end},page_filtered:this.pageFiltered,
      identity:this.identity,identity_before:this.identityBefore,account_verified:this.identityVerified===true,
      generated_at:this.generatedAt,record_url:await this.records.url(),download_verified:false,
      note:'Run role_cli.py finalize to verify/copy the actual local XLSX and produce the handoff receipt.'};
  }
};
export default douyinLaikeOperator;
