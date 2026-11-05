# extension-self-refresh — 解压 Chrome 扩展的自主热更新技能

## 触发场景
- 在开发/维护**解压加载（unpacked）的 Chrome 扩展**时，改了 `content.js` / `worker.js` / `policy.js` / `control.js`，但**浏览器里跑的还是旧代码**。
- Chrome 的「文件改动自动重载扩展」监听**失灵或不触发**（本机实测：Edit 工具的原子写、touch、append、甚至 manifest 版本号升级都无法触发自动重载）。
- 目标：**不依赖用户手动点 `chrome://extensions` 的 ↺**，让代码更新尽量自主生效；只在绝对必要时才请用户点一次。

## 先理解三个底层事实（本技能的全部基础）
1. **`chrome.scripting.executeScript({files:[...]})` 每次从磁盘现读**——所以 worker 每次调 `executeScript` 注入的都是最新 content.js。
2. **manifest 声明的 `content_scripts` 注入用的是扩展加载时的快照**——扩展不重载，页面每次刷新注入的都是**旧代码**。
3. **install guard + 先注册先响应**：content.js 顶部的 `if(globalThis.__xxxInstalled) return;` 让重注入的新 listener 无法接管；`chrome.runtime.onMessage` 多个 listener 时**先注册的先响应**，后注册的永远轮不到。

→ 推论：光靠 executeScript 重注入，新代码**跑得到但接不了消息**；页面重载又会把旧快照的 guard 重新设上。这就是「改了代码不生效」的根本原因。

## 三段式方案（按优先级）

### A. content.js 自刷新（版本标记 + 一次性 reload）
在 content.js 的 install guard **之前**插入（完整可抄代码见 `references/content-self-refresh.snippet.js`）：

```js
(() => {
  const SELF_VERSION='v1';              // 每次改 content.js 必须 +1
  try{
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
  if (globalThis.__localDomExportInstalled) return;   // 原 guard 不动
  globalThis.__localDomExportInstalled = true;
  …
```

- 生效路径：worker 下次 op → executeScript 从磁盘注入新版 → 检测到「guard 在、版本过期」→ `location.reload()` → 新页面 manifest 注入同版本 → 版本匹配 → 稳定。**等价于自动 Cmd+R，不碰登录态、不开端口。**
- **一次性闸门（sessionStorage）是必须的**：见下方「大坑」。
- mock 测试环境没有 `location.reload`/`sessionStorage`，全部包了 try/catch + typeof 守卫，测试不受影响。

### B. worker.js 加 `reload` op（页面自主刷新）
worker 的 `execute()` 里加：
```js
if(cmd.op==='reload'){ await target(cmd.tabId); await chrome.tabs.reload(cmd.tabId); return {reloaded:true}; }
```
同时在桥接层（如 bridge.py 的 `OPS` 白名单和 tabId 校验列表）放行 `reload`。注意：**改完 bridge.py 必须重启 serve 进程**（运行中的进程持有旧白名单）。

### C. control.js 打开即重载（worker 自主更新）
把扩展控制页改成打开 2 秒后 `chrome.runtime.reload()`——用户点一次工具栏扩展图标，worker 就是新代码。注意：**扩展页面是否从磁盘现读取决于 Chrome 行为，不确定时以 `chrome://extensions` ↺ 为准**（本机实测 `open -a "Google Chrome" "chrome-extension://…"` 会因 scheme 未注册而失败）。

## 大坑：旧快照导致的无限重载循环（本机实测踩中）
- 现象：部署自刷新后页面开始**周期性整页重载**，ping 在 OK/unavailable 之间振荡。
- 根因：扩展自加载后从未重载 → manifest 注入用**旧快照**（如 v1）→ 每轮重载后旧代码重新设下 guard（**不设版本标记**）→ 磁盘新版检测到「guard 在、版本过期」→ 又 reload → **死循环**。
- 修复：A 方案的一次性 sessionStorage 闸门（每个版本每标签页会话最多触发一次）。循环会停，页面稳定在旧代码。
- **根本解**：重载扩展一次（`chrome://extensions` ↺）→ 快照更新为当前磁盘版本 → 版本标记由新 manifest 注入设置 → 自刷新逻辑永久进入「版本匹配、不触发」的静默状态。

## 验证清单（每次改完按序过）
1. `node --check extension/content.js && node --check extension/worker.js`；Python 侧 `ast.parse`。
2. 跑该扩展自带的离线测试（content/worker mock + python unittest），**一个都不能挂**（mock 无 window/MouseEvent/sessionStorage/getBoundingClientRect，全靠 typeof 守卫）。
3. 发一个无害 op（如 ping）触发自刷新 → 等页面重载完成（重载中会报 `content script unavailable` / `Receiving end does not exist`，属预期）→ 再 ping 确认恢复。
4. 连续 ping 2-3 次（间隔 ≥25s）确认**不再振荡**（循环已止）。
5. 行为验证：用改动的功能做一次真机操作确认新代码生效。

## 红线（与 control-existing-chrome 一致）
- 不开 `--remote-debugging-port`、不用 CDP/调试会话（商户站点风控会顶号清登录态）。
- 不读 cookie、不碰 Chrome Cookies 库。
- 页面重载只用 `location.reload()` / `chrome.tabs.reload()`（等价 Cmd+R，同 URL 同会话 cookie）。
- 不重启日常 Chrome、不 pkill Chrome 进程。
- 点击仍走 policy 白名单闸门，禁词/角色/kind 校验不因热更新而绕过。

## 相关文件
- `references/content-self-refresh.snippet.js` — A 方案完整片段（含注释）
- 实战样例：`zmaibaole/skills/chrome-dom-export/extension/content.js`（SELF_VERSION 当前 v5，含祖先链拟人点击）
