// ============================================================================
// extension-self-refresh · A 方案：content.js 自刷新片段
// 用法：整段替换 content.js 顶部的 IIFE 开头（放在原 install guard 之前）。
// 每次修改 content.js 后，把 SELF_VERSION 的版本号 +1，否则自刷新不会触发。
// ============================================================================
(() => {
  const SELF_VERSION='v1';   // TODO: 每次改本文件 +1
  try{
    // Self-refresh (no user action, no ports): when this file is re-injected into a page whose
    // message listener was registered by an OLDER version (install guard already set, version
    // marker stale), reload the page once so the newest code goes live. After the reload, the fresh
    // manifest injection registers this version and refreshes the marker, so later re-injections
    // see a matching version and never loop. Equivalent to Cmd+R: same URL, same session cookie.
    // ONE-SHOT per version (sessionStorage survives reloads): if the extension itself was never
    // reloaded after loading, the manifest content_scripts injection still uses the OLD snapshot
    // and re-registers the old guard on every reload — without the one-shot that loops forever.
    // The permanent fix for that case is reloading the extension once (chrome://extensions ↺).
    if(globalThis.__localDomExportInstalled && globalThis.__lde_version!==SELF_VERSION){
      let fired=false;
      try{ fired=sessionStorage.getItem('__lde_self_reload')===SELF_VERSION; }catch(_){}
      if(!fired){
        try{ sessionStorage.setItem('__lde_self_reload',SELF_VERSION); }catch(_){}
        globalThis.__lde_version=SELF_VERSION; location.reload(); return;
      }
    }
    globalThis.__lde_version=SELF_VERSION;
  }catch(_){}
  if (globalThis.__localDomExportInstalled) return;   // ← 原 install guard 原样保留
  globalThis.__localDomExportInstalled = true;
  const P = globalThis.DOM_EXPORT_POLICY;
  // …以下为原 content.js 主体，不动…
})();

// ============================================================================
// B 方案：worker.js execute() 内增加 reload op（配合桥接层放行）
// ============================================================================
//   if(cmd.op==='reload') {
//     // Reload the allowed tab so freshly edited content scripts are re-injected cleanly
//     // (same as the user pressing Cmd+R: same URL, same session cookie, no ports, no login impact).
//     await target(cmd.tabId);
//     await chrome.tabs.reload(cmd.tabId);
//     return {reloaded:true};
//   }

// ============================================================================
// C 方案：control.js 打开即重载扩展（用户点一次工具栏图标，worker 即新代码）
// ============================================================================
// document.getElementById('identity').textContent='Extension ID: '+chrome.runtime.id;
// document.getElementById('status').textContent='正在重载扩展以加载最新代码（约 2 秒）…';
// setTimeout(()=>{
//   try{ chrome.runtime.reload(); }
//   catch(e){ document.getElementById('status').textContent='重载失败: '+e.message+' — 请改用 chrome://extensions 上的刷新按钮'; }
// },2000);
