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

const source=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0019.json');
const tree=JSON.parse(fs.readFileSync(source)).tree;
function walk(n){return [n,...(n.children||[]).flatMap(walk)]}
const original=walk(tree.root).find(n=>n.public_frame_dom);
function setup(){body=build(tree.root);document.body=body;ctx.location.pathname=new URL(tree.url).pathname;ctx.location.href=tree.url;
 const frame=flatten(body).find(e=>e.tagName==='IFRAME'&&e.attrs.class==='iframe-TNKSmG'),doc={URL:original.public_frame_dom.url,readyState:'complete'};
 doc.body=build(original.public_frame_dom.root);doc.querySelectorAll=s=>[doc.body,...flatten(doc.body)].filter(e=>match(e,s));doc.getElementById=id=>[doc.body,...flatten(doc.body)].find(e=>e.id===id);
 for(const n of [doc.body,...flatten(doc.body)])n.ownerDocument=doc;
 frame.attrs.src=doc.URL;frame.contentDocument=doc;
 const drawer=frame.closest('.notice-drawer-vBipFK'),close=drawer.querySelector('span.governance_merchant-drawer-close-icon');return {frame,doc,drawer,close};}
let x=setup();assert.equal(run(x.close,'navigation').ok,false);let r=run(x.close,'dismiss');assert.equal(r.ok,true,r.error);assert.equal(x.close.clickCount,1);assert.equal(run(x.close.children[0],'dismiss').ok,false);
x=setup();x.frame.attrs.src='https://external.invalid/unreviewed';assert.equal(run(x.close,'dismiss').ok,false);assert.equal(x.close.clickCount,undefined);
x=setup();const label=x.doc.querySelectorAll('div').find(e=>e.innerText==='违规ID：'&&!e.children.length);label.parentElement.children[1].innerText='not a notice';assert.equal(run(x.close,'dismiss').ok,false);
x=setup();x.doc.querySelectorAll('.by-header__title_overhide.overflow-VUGAYn')[0].innerText='其他';assert.equal(run(x.close,'dismiss').ok,false);
x=setup();x.frame.contentDocument=null;assert.equal(run(x.close,'dismiss').ok,false);
console.log('Actual same-origin notice frame outer close only; wrong input, title, ID, foreign or unavailable document denied. No iframe actions.');
