// Dependency-free semantic control tests in a mock DOM, not a live Chrome claim.
const vm=require('node:vm'), fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'../extension');
let listener, elements=[], merchantCard=null;
function element(text,tag='DIV',attrs={}) {
  return {tagName:tag,innerText:text,textContent:text,id:'',nodeType:1,children:[],parentElement:null,disabled:false,
    getAttribute(k){return attrs[k] ?? null;},hasAttribute(k){return k in attrs;},getClientRects(){return [1];},
    closest(s){if(s==='.commentItem-jrXo5p')return attrs.normalCard||null;if(s.includes('UserCard-index-module__outer--'))return attrs.userCard||null;if(s.includes('SwitchCard-index-module__switch-card--'))return attrs.switchCard||null;if(s.includes('Guide-index-module__guide-modal--'))return attrs.guide||null;if(s.includes('form'))return null;if(s.includes('byted-date-col'))return attrs.dateCell?this:null;if(s.includes('role=dialog'))return attrs.modal || null;return null;},
    click(){this.clicked=true;this.clickCount=(this.clickCount||0)+1;}};
}
const document={body:element('body','BODY'),querySelectorAll(s){if(s.includes('UserCard-index-module__outer--'))return merchantCard?[merchantCard]:[];return elements;},getElementById(){return null;}};
const context={document,chrome:{runtime:{id:'test',onMessage:{addListener(fn){listener=fn;}}}},location:{origin:'https://life.douyin.com',pathname:'/p/life_comment/management',href:'https://life.douyin.com/p/life_comment/management'},CSS:{escape:s=>s},getComputedStyle:()=>({visibility:'visible'}),URL,Event:class{}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(dir,'policy.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(dir,'content.js'),'utf8'),context);
function run(op,locator,kind){let result;listener({channel:'local-dom-export-v1',op,locator,kind},{id:'test'},r=>result=r);return result;}
let e=element('导出评价');elements=[e];assert.equal(run('click',{by:'text',value:'导出评价'},'export').ok,true);assert.equal(e.clicked,true);assert.equal(e.clickCount,1);
e=element('投诉');elements=[e];assert.equal(run('click',{by:'text',value:'投诉'}).ok,false);assert.equal(e.clicked,undefined);
e=element('投诉');elements=[e];assert.equal(run('click',{by:'text',value:'投诉'},'complaint-draft').ok,true);
e=element('提交');elements=[e];assert.equal(run('click',{by:'text',value:'提交'},'complaint-draft').ok,false);
e=element('回复');elements=[e];assert.equal(run('click',{by:'selector',value:'button'}).ok,false);
elements=[element('下载'),element('下载')];assert.match(run('click',{by:'text',value:'下载'}).error,/ambiguous/);
elements=[element('任意修改')];assert.match(run('click',{by:'text',value:'任意修改'}).error,/allowlist/);
elements=[element('确认','BUTTON')];assert.match(run('click',{by:'role',value:'button',name:'确认'}).error,/switch-company/);
e=element('16','DIV',{dateCell:true});elements=[e];assert.equal(run('click',{by:'text',value:'16'},'filter').ok,true);
elements=[element('16')];assert.equal(run('click',{by:'text',value:'16'},'filter').ok,false);
elements=[element('导出评价')];assert.equal(run('click',{by:'text',value:'导出评价'},'download').ok,false);
assert.equal(run('html',{by:'selector',value:'body'}).ok,false);assert.equal(run('react-click').ok,false);
assert.equal(run('ping').result.version,'dom-only-20261021-11');
assert.equal(run('cookies').ok,false);assert.equal(run('evaluate').ok,false);
console.log('Semantic control safety cases passed (mock DOM).');

const guide=element('新来客 新生意 抖音来客全新升级! 导航升级 首页升级');
e=element('立即体验','BUTTON',{guide});elements=[e];assert.equal(run('click',{by:'role',value:'button',name:'立即体验'},'onboarding-dismiss').ok,true);assert.equal(e.clickCount,1);
for(const attrs of [{},{guide:element('立即体验')},{guide:element('新来客 新生意 抖音来客全新升级! 导航升级')}]){e=element('立即体验','BUTTON',attrs);elements=[e];assert.equal(run('click',{by:'text',value:'立即体验'},'onboarding-dismiss').ok,false);assert.equal(e.clicked,undefined);}
e=element('立即体验','BUTTON',{guide});elements=[e];assert.equal(run('click',{by:'text',value:'立即体验'}).ok,false);
e=element('立即体验','DIV',{guide});elements=[e];assert.equal(run('click',{by:'text',value:'立即体验'},'onboarding-dismiss').ok,false);

// Observed HeaderV3 merchant switch. Full identity and exact ancestry are mandatory.
function merchantFixture(change={}){
 const provider='服务商123456789';
 const card=element(change.cardText||`${provider} 代运营中 商户 ${provider} 切换 服务类型 总户代运营 账户ID 987654321 复制 我的客户经理 陈方圆 退出登录`,'DIV',{'class':'src-components-HeaderV3-components-UserCard-index-module__outer--fixture'});
 const sw=element(change.switchText||`商户 ${provider} 切换`,'DIV',{'class':change.switchClass||'src-components-HeaderV3-components-UserCard-components-SwitchCard-index-module__switch-card--fixture'});
 const button=element('切换',change.tag||'BUTTON',{'class':change.buttonClass||'life-core-btn src-components-HeaderV3-components-UserCard-components-SwitchCard-index-module__switch-card-button--fixture',userCard:change.noCard?null:card,switchCard:change.noSwitch?null:sw});
 sw.querySelectorAll=()=>change.twoButtons?[button,element('切换','BUTTON')]:[button];card.contains=x=>x===sw;merchantCard=card;elements=[button];return button;
}
e=merchantFixture();{const outcome=run('click',{by:'role',value:'button',name:'切换'},'navigation');assert.equal(outcome.ok,true,outcome.error);}assert.equal(e.clickCount,1);
for(const change of [{noCard:true},{noSwitch:true},{buttonClass:'unrelated'},{switchClass:'unrelated'},{switchText:'商户 服务商999 切换'},{cardText:'服务商123456789 账户ID 987654321 复制 我的客户经理 陈方圆'}, {cardText:'服务商123456789 我的客户经理 陈方圆 退出登录'}, {cardText:'服务商123456789 账户ID 123456789 复制 我的客户经理 退出登录'}, {twoButtons:true},{tag:'DIV'}]){
 e=merchantFixture(change);assert.equal(run('click',{by:'text',value:'切换'},'navigation').ok,false,JSON.stringify(change));assert.equal(e.clicked,undefined);
}
e=merchantFixture();assert.equal(run('click',{by:'text',value:'切换'}).ok,false);assert.equal(e.clicked,undefined);
merchantCard=null;e=element('切换','BUTTON');elements=[e];assert.equal(run('click',{by:'text',value:'切换'},'navigation').ok,false);assert.equal(e.clicked,undefined);
console.log('Narrow merchant-switch ancestry/identity tests passed (mock public DOM).');

// Observed normal-card pending complaint is read-only, never a submit path.
const normalCard=element('模拟评价','DIV',{'class':'commentItem-jrXo5p'});
e=element('投诉审核中','DIV',{'class':'button-vhqEd7 isHighlight-DoxxP4',normalCard});elements=[e];assert.equal(run('click',{by:'text',value:'投诉审核中'},'complaint-read').ok,true);assert.equal(e.clickCount,1);
for(const attrs of [{},{'class':'button-vhqEd7',normalCard},{'class':'button-vhqEd7 isHighlight-DoxxP4'}]){e=element('投诉审核中','DIV',attrs);elements=[e];assert.equal(run('click',{by:'text',value:'投诉审核中'},'complaint-read').ok,false);assert.equal(e.clickCount,undefined);}
e=element('投诉审核中','DIV',{'class':'button-vhqEd7 isHighlight-DoxxP4',normalCard});elements=[e];assert.equal(run('click',{by:'text',value:'投诉审核中'},'complaint-draft').ok,false);assert.equal(e.clickCount,undefined);
