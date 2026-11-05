/*
 * Run these declarations ONLY inside an already initialized Codex cua_repl.
 * NOT a Node/CLI program. Read current runtime docs before use.
 * These are thin calls to the SAME host API used in the recorded session.
 * They neither create a browser connection nor implement a new browser driver.
 * Do not invoke on a no-debugging site until host backend compliance is established.
 */
var existingChromeUI = {
  async tabs(browser) {
    return await browser.user.openTabs();
  },
  async tree(tab) {
    return await tab.playwright.domSnapshot();
  },
  locator(tab, spec) {
    if (!spec || typeof spec.value !== 'string' || !spec.value.trim()) throw Error('A fresh DOM locator is required');
    if (spec.by === 'text') return tab.playwright.getByText(spec.value, {exact:true});
    if (spec.by === 'role' && typeof spec.name === 'string') return tab.playwright.getByRole(spec.value, {name:spec.name, exact:true});
    if (spec.by === 'selector') return tab.playwright.locator(spec.value);
    throw Error('Only exact text, role+name, or inspected CSS selector is allowed');
  },
  async inspect(tab, spec) {
    const target = this.locator(tab, spec);
    const count = await target.count();
    return {count, text:count===1 ? await target.innerText({timeoutMs:5000}) : null};
  },
  async unique(tab, spec) {
    const target = this.locator(tab, spec);
    const count = await target.count();
    if (count !== 1) throw Error(`Expected one visible reviewed target, found ${count}; inspect DOM and scope, do not guess`);
    if (!await target.isVisible()) throw Error('Target is not visible');
    if (!await target.isEnabled()) throw Error('Target is disabled');
    return target;
  },
  async clickReviewed(tab, spec, context) {
    // context is the calling agent's explicit review, not an authorization source.
    // The agent must still review actual UI, account and the current user request.
    const kinds = ['navigation','filter','company-switch','export','download'];
    if (!context || !kinds.includes(context.kind) || context.reviewed !== true) throw Error('Reviewed read/export context required');
    const target = await this.unique(tab, spec);
    const text = String(await target.innerText({timeoutMs:5000})).replace(/\s+/g,' ').trim();
    if (/回复|投诉|发送|发布|删除|支付|购买|退出登录|修改密码|保存设置/.test(text)) throw Error('Forbidden business write target');
    await target.click({timeoutMs:5000});
    return {clicked:true, kind:context.kind, observedText:text, snapshot:await this.tree(tab)};
  },
  async downloadReviewed(tab, spec, context) {
    // Documented API route; NOT completed in the original live run.
    if (!context || context.kind!=='download' || context.reviewed!==true) throw Error('Review correct generated export record before downloading');
    const target=await this.unique(tab,spec);
    const text=String(await target.innerText({timeoutMs:5000})).trim();
    if (!/^(下载|下载文件|下载评价|下载报表)$/.test(text)) throw Error('Expected an explicitly reviewed download control');
    // Register first so fast downloads are not missed. Observe both promises to
    // avoid unhandled rejection if the click or listener fails. Never retry click.
    const pending=tab.playwright.waitForEvent('download',{timeoutMs:45000});
    const results=await Promise.allSettled([pending,target.click({timeoutMs:5000})]);
    if(results[1].status==='rejected') throw Error('Download click outcome unknown; inspect current UI, do not replay: '+String(results[1].reason));
    if(results[0].status==='rejected') throw Error('No verified download event; inspect platform task, do not replay: '+String(results[0].reason));
    const download=results[0].value;
    const path=await download.path({timeoutMs:45000});
    if(!path) throw Error('Download did not return a filesystem path');
    return {toolReportedPath:path, localFileVerified:false, note:'Agent must verify this path exists locally before claiming delivery.'};
  }
};
