// Public DOM snapshots replayed in a fake DOM, no Chrome access.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
// Resolve independent of invocation cwd; files are local real observations, never current collection.
const evidence=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/profile-discovery-evidence');
let listener,body;
function self(e,s){if(s.includes(','))return s.split(',').some(q=>self(e,q));if(s.includes('['))return false;if(s.startsWith('#'))return e.id===s.slice(1);const bits=s.split('.'),tag=bits.shift();return (!tag||e.tagName===tag.toUpperCase())&&bits.every(c=>e.classList.contains(c));}
function match(e,s){const parts=s.split(' ');if(!self(e,parts.pop()))return false;while(parts.length){const part=parts.pop();let p=e.parentElement;while(p&&!self(p,part))p=p.parentElement;if(!p)return false;e=p;}return true;}
function flatten(e){return e.children.flatMap(x=>[x,...flatten(x)]);}
function build(n,parent=null){const attrs={...n.attributes};if(n.placeholder)attrs.placeholder=n.placeholder;const e={nodeType:1,tagName:(n.tag||'div').toUpperCase(),innerText:n.name||'',textContent:n.name||'',attrs,id:attrs.id||'',type:'text',disabled:!!n.disabled,value:attrs.value||'',originalSelector:n.selector,parentElement:parent,children:[],getAttribute(k){return this.attrs[k]??null;},hasAttribute(k){return k in this.attrs;},getClientRects(){return [1]},closest(s){for(let p=this;p;p=p.parentElement)if(match(p,s))return p;return null},contains(x){return x===this||flatten(this).includes(x)},querySelectorAll(s){return flatten(this).filter(x=>match(x,s))},querySelector(s){return this.querySelectorAll(s)[0]||null},click(){this.clickCount=(this.clickCount||0)+1;}};e.classList={contains:c=>String(e.attrs.class||'').split(/\s+/).includes(c)};if(e.tagName==='INPUT')e.labels=[{textContent:n.name||n.placeholder||''}];if(e.tagName==='BUTTON')e.type='submit';e.children=(n.children||[]).map(c=>build(c,e));return e;}
const document={querySelectorAll(s){return [body,...flatten(body)].filter(e=>e.originalSelector===s||match(e,s));},getElementById(id){return [body,...flatten(body)].find(e=>e.id===id)}};
const ctx={document,chrome:{runtime:{id:'test',onMessage:{addListener(f){listener=f;}}}},location:{origin:'https://life.douyin.com',pathname:'',href:''},CSS:{escape:s=>s},getComputedStyle:()=>({visibility:'visible'}),URL,Event:class{}};vm.createContext(ctx);for(const f of ['policy.js','content.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension',f),'utf8'),ctx);
function run(e,kind){let r;listener({channel:'local-dom-export-v1',op:'click',kind,locator:{by:'selector',value:e.originalSelector}},{id:'test'},v=>r=v);return r;}


const source=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0042.json');
const raw=JSON.parse(fs.readFileSync(source));
function setup(){body=build(raw.tree.root);document.body=body;ctx.location.href=raw.tab.url;ctx.location.pathname=new URL(ctx.location.href).pathname;return flatten(body).find(e=>e.tagName==='BUTTON'&&e.innerText==='查看其他处置');}
let target=setup();assert(target);assert.equal(run(target,'dismiss').ok,false);assert.equal(target.clickCount,undefined);let reply=run(target,'navigation');assert.equal(reply.ok,true,reply.error);assert.equal(target.clickCount,1);
target=setup();ctx.location.href=ctx.location.href.replace(/TaskID=[^&]+/,'TaskID=unreviewed');assert.equal(run(target,'navigation').ok,false);
target=setup();ctx.location.href+='&groupid=1';assert.equal(run(target,'navigation').ok,false);
target=setup();flatten(body).find(e=>e.tagName==='H1'&&e.classList.contains('title-AOxZNO')).innerText='其他';assert.equal(run(target,'navigation').ok,false);
target=setup();const clone=build({tag:'button',name:'查看其他处置',attributes:{class:'btn-WHUasg govern_fulfillment_v2-btn'},selector:'#other'},target.parentElement);target.parentElement.children.push(clone);assert.equal(run(target,'navigation').ok,false);
target=setup();const other=flatten(body).find(e=>e.tagName==='BUTTON'&&e.innerText==='意见反馈');assert(other);assert.equal(run(other,'navigation').ok,false);assert.equal(other.clickCount,undefined);
console.log('Actual 0042 public stop-loss return only: route, title, task, company, unique control and navigation kind enforced; feedback denied.');
