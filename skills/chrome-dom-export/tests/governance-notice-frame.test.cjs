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

const src=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0017.json');
const tree=JSON.parse(fs.readFileSync(src)).tree;body=build(tree.root);document.body=body;ctx.location.pathname=new URL(tree.url).pathname;ctx.location.href=tree.url;
const frame=flatten(body).find(e=>e.tagName==='IFRAME'&&e.attrs.class==='iframe-TNKSmG');assert.ok(frame);
function read(){let r;listener({channel:'local-dom-export-v1',op:'tree',locator:{by:'selector',value:frame.originalSelector}},{id:'test'},v=>r=v);assert.equal(r.ok,true,r.error);return r.result.root;}
frame.attrs.src='https://life.douyin.com/mock-notice?secret=not-exported#fragment';frame.contentDocument={URL:frame.attrs.src,readyState:'complete'};
let n=read();assert.equal(n.public_frame.document_available,true);assert.equal(n.public_frame.source_path,'/mock-notice');assert.equal(n.public_frame.document_path,'/mock-notice');assert.equal(JSON.stringify(n).includes('not-exported'),false);assert.equal(n.public_frame.frame_input_enabled,false);

const doc={URL:'https://life.douyin.com/h5/governance/violation_talent_notice?private=omitted',readyState:'complete',getElementById(){return null;},querySelectorAll(s){return [this.body,...flatten(this.body)].filter(e=>match(e,s));}};
doc.body=build({tag:'body',name:'通知公开正文',attributes:{},children:[{tag:'h1',name:'通知公开正文',attributes:{},children:[]},{tag:'span',name:'公开建议',attributes:{},children:[]}]});
for(const e of [doc.body,...flatten(doc.body)])e.ownerDocument=doc;
frame.attrs.src=doc.URL;frame.contentDocument=doc;n=read();assert.equal(n.public_frame_dom.input_enabled,false);assert.equal(n.public_frame_dom.url,'https://life.douyin.com/h5/governance/violation_talent_notice');assert.equal(n.public_frame_dom.root.name,'通知公开正文');assert.ok(n.public_frame_dom.root.selector.startsWith('readonly-frame:'));assert.equal(flatten(n.public_frame_dom.root).some(e=>e.tag==='input'),false);assert.equal(JSON.stringify(n.public_frame_dom).includes('private=omitted'),false);
frame.attrs.src='https://life.douyin.com/unreviewed';assert.equal(read().public_frame_dom,undefined);

frame.attrs.src='https://external.invalid/notice?token=private';frame.contentDocument=null;n=read();assert.equal(n.public_frame.source_same_origin,false);assert.equal(n.public_frame.document_available,false);assert.equal(JSON.stringify(n).includes('private'),false);
frame.attrs.class='unreviewed-frame';assert.equal(read().public_frame,undefined);
console.log('Known same-origin notice path DOM is read-only; query/fragment and form inputs omitted, foreign/unreviewed frames never traversed.');
