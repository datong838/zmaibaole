const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../extension/content.js'),'utf8');
const fn=source.slice(source.indexOf('  function normalReviewPagerRule('),source.indexOf('  function assertSafe('));
function fixture(){
 const el=(tag,cl,name='')=>({tagName:tag,children:[],parentElement:null,disabled:false,hidden:false,name,getAttribute(k){return k==='class'?this.cl:k==='role'?this.role:null},cl,
 closest(q){if(q==='.pagination-GXvAPk'){for(let n=this;n;n=n.parentElement)if(n.cl==='pagination-GXvAPk')return n;return null;}return null;},querySelectorAll(){return this.desc||[];}});
 const set=(p,cs)=>{p.children=cs;for(const c of cs)c.parentElement=p;};
 const root=el('DIV','commentList-hkujq4 isPC-WBFQKh commentList-C8RoYO'),head=el('DIV','header-sQid1u commentListHeader-jKdTh_'),count=el('DIV','','已筛选44条');head.desc=[count];
 const pager=el('DIV','pagination-GXvAPk'),total=el('DIV','text-bjyZFG','共54条记录'),group=el('DIV','buttonGroup-GDbp9Y'),current=el('DIV','text-bjyZFG','1/6');
 const button=disabled=>{const b=el('DIV','button-j4VxiA'+(disabled?' isDisabled-unTBS6':'')),svg=el('svg','icon-v6i0WU'),g=el('g',''),p=el('path','');svg.role='presentation';set(b,[svg]);set(svg,[g]);set(g,[p]);return b;};
 const prev=button(true),next=button(false);set(group,[prev,current,next]);set(pager,[total,group]);set(root,[head,...Array.from({length:10},()=>el('DIV','commentItem-jrXo5p')),pager]);
 const negative=el('DIV','option-YmRyn3 isSelected-ov8pOi','中差评（1-3心）'),inputs=['评价时间','评价类型','评价来源','评价状态'].map(name=>Object.assign(el('INPUT','byted-input byted-input-size-md',name),{value:name==='评价时间'?'2026-09-21 ~ 2026-10-20':'全部'}));
 const ctx={URL,location:{pathname:'/p/life_comment/management',href:'https://life.douyin.com/p/life_comment/management?groupid=123'},visible:e=>!e.hidden,name:e=>e.name,document:{querySelectorAll(q){if(q.startsWith('.commentList'))return this.lists;if(q.startsWith('.option'))return [negative];if(q.startsWith('input.'))return inputs;return []},lists:[root]}};
 vm.createContext(ctx);vm.runInContext(fn+'\nglobalThis.run=normalReviewPagerRule;',ctx);return {ctx,root,pager,group,prev,next,current,total,head,count,inputs,negative,el,run:(e=next,kind='navigation')=>ctx.run(e,kind)};
}
test('actual observed page1 shape approves only semantic next, preserves 44 vs54',()=>{const f=fixture();assert.equal(f.run().scope,'observed-normal-review-adjacent-pager-v1');assert.equal(f.count.name,'已筛选44条');assert.equal(f.total.name,'共54条记录');assert.throws(()=>f.run(f.prev),/disabled/);});
test('adjacent previous works on synthetic page2 but arbitrary descendant/numeric target never does',()=>{const f=fixture();f.current.name='2/6';f.prev.cl='button-j4VxiA';assert.equal(f.run(f.prev).kind,'navigation');assert.throws(()=>f.run(f.current));assert.throws(()=>f.run(f.next.children[0]));assert.equal(f.run(f.el('DIV','','2')),null);});
test('wrong scope, duplicate list, malformed pager, filters, hidden and foreign ownership refuse',()=>{
 for(const mutate of [f=>f.ctx.location.pathname='/p/other',f=>f.ctx.location.href+='&groupid=456',f=>f.ctx.document.lists.push(f.root),f=>f.pager.parentElement=f.el('DIV','other'),f=>f.current.name='1/1',f=>f.total.name='共55条记录X',f=>f.inputs[0].value='2026-10-21',f=>f.inputs[1].value='其他',f=>f.negative.name='好评（4-5心）',f=>f.next.hidden=true,f=>f.next.children[0].role='button',f=>f.root.children.splice(2,0,f.el('DIV','foldTitleContainer-DwIByI','折叠'))]){const f=fixture();mutate(f);assert.throws(()=>f.run());}
 const f=fixture();assert.throws(()=>f.run(f.next,'complaint-read'));
});
test('single versioned build and narrow guard wired, generic navigation list untouched',()=>{assert.match(source,/const BUILD='normal-review-adjacent-pager-v1'/);assert.match(source,/let rule=normalReviewPagerRule\(e,action\)\|\|commentStatusOpenRule/);assert.equal((source.match(/const BUILD=/g)||[]).length,1);});
