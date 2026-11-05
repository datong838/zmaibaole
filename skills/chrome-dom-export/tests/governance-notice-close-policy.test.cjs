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
function load(kind){const tree=JSON.parse(fs.readFileSync(path.join(evidence,'001-'+kind+'.json'))).tree;body=build(tree.root);document.body=body;ctx.location.pathname=new URL(tree.url).pathname;ctx.location.href=tree.url;return [body,...flatten(body)];}
function run(e,kind){let r;listener({channel:'local-dom-export-v1',op:'click',kind,locator:{by:'selector',value:e.originalSelector}},{id:'test'},v=>r=v);return r;}

const source=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/first-detail-probe-v9-evidence/0002.json');
function detail(){const tree=JSON.parse(fs.readFileSync(source)).tree;body=build(tree.root);document.body=body;ctx.location.pathname=new URL(tree.url).pathname;ctx.location.href=tree.url;return [body,...flatten(body)];}
let ns=detail(),drawer=ns.find(e=>e.classList.contains('notice-drawer-OIp9e3')&&e.classList.contains('governance_merchant-drawer-dialog-show'));
assert.ok(drawer);let close=drawer.querySelector('span.governance_merchant-drawer-close-icon');
assert.equal(run(close,'navigation').ok,false);let reply=run(close,'dismiss');assert.equal(reply.ok,true,reply.error);assert.equal(close.clickCount,1);
assert.equal(run(close.children[0],'dismiss').ok,false);assert.equal(close.children[0].clickCount,undefined);
const title=drawer.querySelector('h1.title-UTzrUd');title.innerText='整改确认';assert.equal(run(close,'dismiss').ok,false);title.innerText='违规通知书';
const label=drawer.querySelectorAll('span.label-CPZ6GC').find(e=>e.innerText==='罚单编号'),value=label.parentElement.children[1];value.innerText='unknown notice';assert.equal(run(close,'dismiss').ok,false);
ns=detail();drawer=ns.find(e=>e.classList.contains('notice-drawer-OIp9e3')&&e.classList.contains('governance_merchant-drawer-dialog-show'));close=drawer.querySelector('span.governance_merchant-drawer-close-icon');
const other=ns.find(e=>e!==drawer&&e.classList.contains('governance_merchant-drawer-dialog'));assert.ok(other);other.attrs.class+=' governance_merchant-drawer-dialog-show notice-drawer-OIp9e3';assert.equal(run(close,'dismiss').ok,false);
ns=detail();drawer=ns.find(e=>e.classList.contains('notice-drawer-OIp9e3')&&e.classList.contains('governance_merchant-drawer-dialog-show'));close=drawer.querySelector('span.governance_merchant-drawer-close-icon');ctx.location.pathname='/p/life_comment/management';assert.equal(run(close,'dismiss').ok,false);
console.log('Actual public notice drawer: unique exact close only; wrong kind, child icon, identity, duplicate drawer and route denied. No live actions.');
