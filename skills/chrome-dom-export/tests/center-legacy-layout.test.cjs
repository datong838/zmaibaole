// Synthetic DOM rule + actual content BUILD replacement, no Chrome.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const dir=__dirname,rootdir=path.resolve(dir,'../../..');
const current=fs.readFileSync(path.join(rootdir,'skills/chrome-dom-export/extension/content.js'),'utf8');
const currentBuild=current.match(/const BUILD='([^']+)'/)[1];
const strictRule=current.slice(current.indexOf('  function governanceLegacyLayoutRule(e){'),current.indexOf('  function governanceRule(e){'));
// Synthetic previous BUILD only: verifies listener replacement, not an old live policy.
const previous=current.replace("const BUILD='"+currentBuild+"'","const BUILD='synthetic-previous-build'");
function fixture(){
 const n=(tag,text,cls)=>({tagName:tag,_name:text,children:[],getAttribute(k){return k==='class'?cls:null;},closest(s){return this.blocked||null;}});
 const root=n('DIV','',''),container=n('DIV','','container-a3IjFk'),header=n('DIV','','header-EaBIRz'),actions=n('DIV','','actions-lq_eBp'),title=n('P','违规中心','title-N66Jpb'),button=n('BUTTON','回到旧版','governance_merchant-btn governance_merchant-btn-size-md governance_merchant-btn-type-text governance_merchant-btn-shape-angle governance_merchant-can-input-grouped backButton-cbYsPY');
 container.parentElement=root;header.parentElement=container;actions.parentElement=header;title.parentElement=header;button.parentElement=actions;header.querySelectorAll=()=>[title];root.querySelectorAll=()=>[button];
 const c={URL,location:{href:'https://life.douyin.com/p/governance/home_violation_center?groupid=123',pathname:'/p/governance/home_violation_center'},P:{origin:'https://life.douyin.com',governanceCenter:{path:'/p/governance/home_violation_center'}},governanceRoot:()=>root,name:e=>e._name,role:e=>e.tagName==='BUTTON'?'button':'generic',visible:()=>true,document:{querySelectorAll:()=>[root]}};
 vm.createContext(c);vm.runInContext(strictRule,c);return {c,root,button,title,header};
}
let f=fixture();assert.equal(f.c.governanceLegacyLayoutRule(f.button).kind,'navigation');
for(const mode of ['path','group','class','title','duplicate','form','children']){
 f=fixture();if(mode==='path')f.c.location.pathname='/p/other';if(mode==='group')f.c.location.href+='&groupid=456';if(mode==='class')f.button.getAttribute=()=> 'unreviewed';if(mode==='title')f.title._name='商户设置';if(mode==='duplicate')f.root.querySelectorAll=()=>[f.button,f.button];if(mode==='form')f.button.blocked={};if(mode==='children')f.button.children=[{}];assert.throws(()=>f.c.governanceLegacyLayoutRule(f.button),undefined,mode);
}
let active,added=0,removed=0;
const c={chrome:{runtime:{id:'synthetic',onMessage:{addListener(fn){active=fn;added++;},removeListener(fn){assert.equal(fn,active);removed++;}}}},location:{origin:'https://life.douyin.com',pathname:'/p/governance/home_violation_center',href:'https://life.douyin.com/p/governance/home_violation_center?groupid=123'},document:{title:'synthetic',querySelectorAll:()=>[]},URL};
vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(rootdir,'skills/chrome-dom-export/extension/policy.js'),'utf8'),c);vm.runInContext(previous,c);vm.runInContext(current,c);assert.equal(removed,1);assert.equal(added,2);
let reply;active({channel:'local-dom-export-v1',op:'ping'},{id:'synthetic'},r=>reply=r);assert.equal(reply.result.version,'dom-only-20261021-11');assert.equal(reply.result.content_build,currentBuild);assert.equal(reply.result.governance_center_layout_policy,'observed-return-legacy-v1');vm.runInContext(current,c);assert.equal(added,2);console.log(JSON.stringify({passed:9,scope:'synthetic strict rule negatives and same-wire new BUILD listener replacement'}));
