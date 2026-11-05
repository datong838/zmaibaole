// Isolated proposed policy, mock public DOM only. Never loads Chrome.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'../extension');let listener,id=0;
function matches(e,s){if(s.startsWith('#'))return e.id===s.slice(1);let bits=s.split('.'),tag=bits.shift();return (!tag||e.tagName===tag.toUpperCase())&&bits.every(c=>e.cls.split(' ').includes(c));}
function all(e){return e.children.flatMap(x=>[x,...all(x)]);}
function el(text='',tag='DIV',cls='',children=[]){const e={id:'e'+(++id),tagName:tag,innerText:text,textContent:text,cls,children,nodeType:1,parentElement:null,disabled:false,type:'text',value:'2026/09/21 ~ 2026/10/21',attrs:{},getAttribute(k){return k==='class'?this.cls:k==='id'?this.id:this.attrs[k]??null;},hasAttribute(k){return this.getAttribute(k)!==null;},getClientRects(){return [1];},contains(x){return x===this||all(this).includes(x);},closest(s){for(let p=this;p;p=p.parentElement)if(matches(p,s))return p;return null;},querySelectorAll(s){return all(this).filter(x=>matches(x,s));},querySelector(s){return this.querySelectorAll(s)[0]||null;},click(){this.clicks=(this.clicks||0)+1;}};children.forEach(x=>x.parentElement=e);return e;}
let root,document={querySelectorAll(s){return [root,...all(root)].filter(e=>matches(e,s));}};
const context={document,chrome:{runtime:{id:'test',onMessage:{addListener(f){listener=f;}}}},location:{origin:'https://life.douyin.com',pathname:'/p/governance/home_violation_center',href:'https://life.douyin.com/p/governance/home_violation_center'},CSS:{escape:s=>s},getComputedStyle:()=>({visibility:'visible'}),URL,Event:class{}};
vm.createContext(context);for(const f of ['policy.js','content.js'])vm.runInContext(fs.readFileSync(path.join(dir,f),'utf8'),context);
function fixture(){const date=el('','INPUT','governance_merchant-input');date.attrs.placeholder='开始日期 ～ 结束日期';const title=el('违规原因 Top10','SPAN','title-KYD1nB'),whole=el('全部','SPAN','viewAllText-W89JWE'),record=el('违规记录','P','todoLabel-I3rSqB'),p1=el('1','LI','governance_merchant-pager-item governance_merchant-pager-item-checked'),p2=el('2','LI','governance_merchant-pager-item'),arrow=el('','SPAN','governance_merchant-icon-right');const next=el('','LI','governance_merchant-pager-item',[arrow]);const panel=el('违规原因 Top10 全部','DIV','topList-DDjs8Y',[title,whole,el('','DIV','pagination-D3lzMl',[p1,p2,next])]);const item=el('违规记录 新增21','DIV','todoItem-SQ0SNc',[record]);root=el('','DIV','',[el('','DIV','governance_merchant-date-picker governance_merchant-date-picker-range',[date]),panel,el('常用工具 违规记录 新增21','DIV','todoSummary-xpJGcr',[item])]);root.id='governanceRoot';document.body=root;return {date,title,whole,record,p1,p2,next,arrow,item,panel};}
function run(e,kind='navigation',op='click'){let r;listener({channel:'local-dom-export-v1',op,kind,locator:{by:'selector',value:'#'+e.id},value:'2026-10-16 ~ 2026-10-20'},{id:'test'},x=>r=x);return r;}
let f=fixture();assert.equal(run(f.date,'filter').ok,true);assert.equal(f.date.clicks,1);assert.match(run(f.date,'filter','filter').error,/open-only/);
for(const key of ['whole','record','p2','arrow']){f=fixture();let r=run(f[key]);assert.equal(r.ok,true,key+':'+r.error);}
for(const key of ['p1','next']){f=fixture();if(key==='next')f.next.cls+=' governance_merchant-pager-item-disabled';let r=run(f[key]);assert.equal(r.ok,false,key);}
f=fixture();f.item.innerText='整改 新增21';assert.equal(run(f.record).ok,false);
f=fixture();f.title.innerText='其他分析';assert.equal(run(f.whole).ok,false);
f=fixture();f.record.cls='other';assert.equal(run(f.record).ok,false);
f=fixture();f.date.attrs.placeholder='other';assert.equal(run(f.date,'filter').ok,false);
f=fixture();f.date.parentElement.cls='other';assert.equal(run(f.date,'filter').ok,false);
f=fixture();context.location.pathname='/p/life_comment/management';assert.equal(run(f.record).ok,false);context.location.pathname='/p/governance/home_violation_center';
for(const name of ['去处理','整改','申诉','删除','投诉','16','查看详情']){f=fixture();const x=el(name,'BUTTON');x.parentElement=root;root.children.push(x);assert.equal(run(x).ok,false,name);assert.equal(x.clicks,undefined);}
console.log('Governance proposal: scoped observed entries and conservative unknown-action rejection passed (mock only).');
