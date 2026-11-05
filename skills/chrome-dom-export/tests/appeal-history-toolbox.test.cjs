const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function fixture(change={}){
 let listener;
 function element(tag,cls,text='',id=''){
  const n={tagName:tag,id,nodeType:1,children:[],parentElement:null,disabled:false,hidden:false,innerText:text,textContent:text,
   getAttribute(k){return k==='class'?cls:k==='aria-disabled'?(this.ariaDisabled||null):null},hasAttribute(){return false},getClientRects(){return this.hidden?[]:[1]},
   closest(q){if(q==='form')return this.form||null;if(q==='a')return this.link||null;return null},click(){this.count=(this.count||0)+1}};return n;
 }
 const root=element('DIV',null,'工具箱','CommentToolView_select'),item=element('DIV','toolViewItem-AAil1V tool-KL4xzH','工具箱'),info=element('DIV','info-EzAm3S','工具箱'),img=element('IMG','icon-NqMTEO'),title=element('DIV','title-x_oc4C','工具箱');
 for(const [p,cs] of [[root,[item]],[item,[info]],[info,[img,title]]]){p.children=cs;for(const c of cs)c.parentElement=p;}
 const nodes={root,item,info,img,title,element};if(change.mutate)change.mutate(nodes);
 const context={URL,CSS:{escape:s=>s},Event:class{},getComputedStyle:()=>({visibility:'visible'}),location:{origin:'https://life.douyin.com',href:'https://life.douyin.com'+(change.path||'/p/life_comment/management'),pathname:change.path||'/p/life_comment/management'},document:{body:element('BODY',null),getElementById:()=>null,querySelectorAll(q){return q==='#CommentToolView_select'?(change.duplicate?[root,element('DIV',null,'工具箱','CommentToolView_select')]:[root]):[]}},chrome:{runtime:{id:'test',onMessage:{addListener(f){listener=f}}}}};
 vm.createContext(context);for(const f of ['policy.js','content.js'])vm.runInContext(fs.readFileSync(__dirname+'/../extension/'+f,'utf8'),context);
 return {...nodes,run(kind='navigation',target='#CommentToolView_select'){let result;listener({channel:'local-dom-export-v1',op:'click',kind,locator:{by:'selector',value:target}},{id:'test'},r=>result=r);return result;}};
}
test('only observed unique toolbox root opens one read-only tool list',()=>{const f=fixture(),r=f.run();assert.equal(r.ok,true,r.error);assert.equal(f.root.count,1);assert.equal(r.result.kind,'navigation')});
test('different path, kind, duplicate, pseudo root and disabled are refused',()=>{
 for(const change of [{path:'/p/governance/violation_list'},{duplicate:true},{mutate:f=>f.root.id='fake'},{mutate:f=>f.root.tagName='BUTTON'},{mutate:f=>f.root.disabled=true},{mutate:f=>f.root.ariaDisabled='true'},{mutate:f=>f.root.hidden=true}]){const f=fixture(change);assert.equal(f.run().ok,false,JSON.stringify(change));assert.equal(f.root.count,undefined)}
 const f=fixture();assert.equal(f.run('complaint-draft').ok,false);assert.equal(f.root.count,undefined);
});
test('unknown child, altered exact classes, child disabled, form and anchor are refused',()=>{
 for(const mutate of [f=>f.root.children.push(f.element('DIV',null,'任意')),f=>f.item.children=[],f=>f.info.children.push(f.element('BUTTON',null,'提交')),f=>f.title.children=[f.element('INPUT',null)],f=>f.title.innerText='投诉历史',f=>f.item.getAttribute=()=> 'toolViewItem-AAil1V other',f=>f.img.disabled=true,f=>f.img.innerText='未审查操作',f=>f.root.form={},f=>f.root.link={}]){const f=fixture({mutate});assert.equal(f.run().ok,false);assert.equal(f.root.count,undefined)}
});
