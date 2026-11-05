// Independent security regression; static 0019 replay only, no Chrome/UI.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
let listener,body;
function self(e,s){
 if(s.includes(','))return s.split(',').some(q=>self(e,q));
 if(s==='[contenteditable]')return Object.hasOwn(e.attrs,'contenteditable');
 if(s.includes('['))return false;
 if(s.startsWith('#'))return e.id===s.slice(1);
 const bits=s.split('.'),tag=bits.shift();return (!tag||e.tagName===tag.toUpperCase())&&bits.every(c=>e.classList.contains(c));
}
function match(e,s){const parts=s.split(' ');if(!self(e,parts.pop()))return false;while(parts.length){const part=parts.pop();let p=e.parentElement;while(p&&!self(p,part))p=p.parentElement;if(!p)return false;e=p;}return true;}
function flatten(e){return e.children.flatMap(x=>[x,...flatten(x)]);}
function build(n,parent=null){
 const attrs={...n.attributes};if(n.placeholder)attrs.placeholder=n.placeholder;
 const e={nodeType:1,tagName:(n.tag||'div').toUpperCase(),innerText:n.name||'',textContent:n.name||'',attrs,id:attrs.id||'',type:'text',disabled:!!n.disabled,value:attrs.value||'',originalSelector:n.selector,parentElement:parent,children:[],
 getAttribute(k){return this.attrs[k]??null;},hasAttribute(k){return k in this.attrs;},getClientRects(){return [1]},closest(s){for(let p=this;p;p=p.parentElement)if(match(p,s))return p;return null},contains(x){return x===this||flatten(this).includes(x)},querySelectorAll(s){return flatten(this).filter(x=>match(x,s))},querySelector(s){return this.querySelectorAll(s)[0]||null},click(){this.clickCount=(this.clickCount||0)+1;}};
 e.classList={contains:c=>String(e.attrs.class||'').split(/\s+/).includes(c)};
 if(e.tagName==='INPUT')e.labels=[{textContent:n.name||n.placeholder||''}];if(e.tagName==='BUTTON')e.type='submit';
 e.children=(n.children||[]).map(c=>build(c,e));return e;
}
const document={querySelectorAll(s){return [body,...flatten(body)].filter(e=>e.originalSelector===s||match(e,s));},getElementById(id){return [body,...flatten(body)].find(e=>e.id===id)}};
const ctx={document,chrome:{runtime:{id:'test',onMessage:{addListener(f){listener=f;}}}},location:{origin:'https://life.douyin.com',pathname:'/p/governance/violation_list',href:'https://life.douyin.com/p/governance/violation_list'},CSS:{escape:s=>s},getComputedStyle:()=>({visibility:'visible'}),URL,Event:class{}};
vm.createContext(ctx);for(const f of ['policy.js','content.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension',f),'utf8'),ctx);
const source=path.resolve(process.cwd(),'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0019.json');
const tree=JSON.parse(fs.readFileSync(source)).tree;
function walk(n){return [n,...(n.children||[]).flatMap(walk)];}
const original=walk(tree.root).find(n=>n.public_frame_dom);assert.ok(original);
function setup(){
 body=build(tree.root);document.body=body;
 const frame=flatten(body).find(e=>e.tagName==='IFRAME'&&e.attrs.class==='iframe-TNKSmG');
 const doc={URL:original.public_frame_dom.url,readyState:'complete'};doc.body=build(original.public_frame_dom.root);
 doc.querySelectorAll=s=>[doc.body,...flatten(doc.body)].filter(e=>match(e,s));doc.getElementById=id=>[doc.body,...flatten(doc.body)].find(e=>e.id===id);
 for(const e of [doc.body,...flatten(doc.body)])e.ownerDocument=doc;
 frame.attrs.src=doc.URL;frame.contentDocument=doc;
 const close=frame.closest('.notice-drawer-vBipFK').querySelector('span.governance_merchant-drawer-close-icon');
 return {frame,doc,close};
}
function call(op,target,kind){let reply;listener({channel:'local-dom-export-v1',op,kind,locator:{by:'selector',value:target.originalSelector}},{id:'test'},r=>reply=r);return reply;}
let x=setup();let reply=call('tree',x.frame);assert.equal(reply.ok,true,reply.error);assert.ok(reply.result.root.public_frame_dom);assert.equal(call('click',x.close,'dismiss').ok,true);
const SECRET='REVIEW_ONLY_SYNTHETIC_SENSITIVE_TEXT';let cases=0;
for(const mode of ['ancestor-innerText','aria-labelledby','input','select','contenteditable']){
 x=setup();let reads=0;
 const tag=mode==='input'?'input':mode==='select'?'select':mode==='contenteditable'?'div':'textarea';
 const attrs=mode==='contenteditable'?{contenteditable:'false'}:{id:'synthetic-draft'};
 const control=build({tag,name:'',attributes:attrs,children:[]},x.doc.body);control.ownerDocument=x.doc;x.doc.body.children.push(control);
 Object.defineProperty(control,'value',{get(){reads++;return SECRET;}});
 Object.defineProperty(control,'textContent',{get(){reads++;return SECRET;}});
 if(mode==='ancestor-innerText')Object.defineProperty(x.doc.body,'innerText',{get(){reads++;return SECRET;}});
 if(mode==='aria-labelledby')x.doc.body.attrs['aria-labelledby']='synthetic-draft';
 reply=call('tree',x.frame);assert.equal(reply.ok,false,mode+' frame tree must fail closed');assert.match(reply.error,/controls|editable|input/i);assert.equal(JSON.stringify(reply).includes(SECRET),false);assert.equal(reply.result,undefined);assert.equal(reads,0,mode+' must reject before any body/control naming/value access');
 reply=call('click',x.close,'dismiss');assert.equal(reply.ok,false,mode+' close must reject before frame naming');assert.match(reply.error,/controls|editable|input/i);assert.equal(JSON.stringify(reply).includes(SECRET),false);assert.equal(x.close.clickCount,undefined);assert.equal(reads,0);cases++;
}
console.log(JSON.stringify({security_regression:'public-notice-frame-no-controls',cases,tree_and_close_rejected_before_sensitive_reads:true,synthetic_only:true,no_live_access:true}));
