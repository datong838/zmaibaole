import assert from 'node:assert/strict';
import {intakeReviewTree} from '../scripts/semantic-intake.mjs';
const leaf=(selector,name,attributes={})=>({selector,name,attributes,children:[]});
const job={account_verified:true,identity:{provider:'p',account_id:'a',manager:'m'},company:'fixture',groupid:'123',start:'2026-10-19',end:'2026-10-19',end_exclusive:'2026-10-20'};
const profile={status:'live-validated',revision:'mock-only',root:'#normal',row:{role:'row',attributes:{class:'review'}},filteredCount:'#count',idAttribute:'data-review-id',store:{role:'store'},customer:{role:'customer'},text:{role:'review-text'},date:{role:'date'},stars:{role:'stars'},action:{role:'action'},activeNegative:'#negative',dateInput:'#date',foldBoundary:'#fold',otherFilters:{评价类型:'#type',评价来源:'#source',评价状态:'#status'}};
function fixture(){
 const row={selector:'#r',role:'row',attributes:{class:'review','data-review-id':'r1'},children:[
 {...leaf('#store','商店'),role:'store'},{...leaf('#customer','顾客'),role:'customer'},{...leaf('#text','口味一般'),role:'review-text'},
 {...leaf('#day','1天前',{datetime:'2026-10-19T10:00:00+08:00'}),role:'date'},
 {...leaf('#stars','❤❤❤',{ 'data-rating':'3'}),role:'stars'}, {...leaf('#action','查看投诉结果'),role:'action'}]};
 return {source:'local-dom-bridge',tab_id:1,tab:{id:1,url:'https://life.douyin.com/p/life_comment/management?groupid=123'},observed_at:'2026-10-20T10:00:00+08:00',tree:{kind:'DOM-derived semantic tree (not native AX)',url:'https://life.douyin.com/p/life_comment/management',truncated:false,root:{selector:'body',children:[
 leaf('#negative','中差评（1-3心）',{'aria-selected':'true'}),leaf('#date','2026-10-19 ~ 2026-10-19'),leaf('#count','评价 已筛选1条'),
 leaf('#type','全部'),leaf('#source','全部'),leaf('#status','全部'),{selector:'#normal',children:[row]},
 {selector:'#fold',get name(){throw Error('folded-content-read');},get children(){throw Error('folded-subtree-read');}}]}}};
}
let checks=0;
function blocked(mut,code,p=profile){const x=fixture();mut(x);const r=intakeReviewTree(x,job,p);assert.equal(r.ok,false);assert.match(r.gaps[0],code);checks++;}
const r=intakeReviewTree(fixture(),job,profile);assert.equal(r.ok,true);assert.equal(r.live_accepted,false);assert.equal(r.capture.source,'local-dom-bridge');assert.equal(r.capture.rows[0].stars,3);checks++;
blocked(x=>x.tree.truncated=true,/tree-incomplete/);
blocked(x=>x.tab.url='https://life.douyin.com/?groupid=999',/company-origin/);
blocked(x=>x.tab.id=2,/tab-observation/);
blocked(x=>x.source='codex-existing-extension',/backend-source/);
blocked(x=>{},/awaiting-live/,{...profile,status:'awaiting-live-validation'});
blocked(x=>x.tree.root.children[2].name='评价 已筛选2条',/pagination/);
blocked(x=>x.tree.root.children[0].attributes['aria-selected']='false',/filter-not-active/);
blocked(x=>x.tree.root.children[1].name='2026-10-18 ~ 2026-10-19',/date-filter/);
blocked(x=>delete x.tree.root.children[6].children[0].attributes['data-review-id'],/stable-review/);
blocked(x=>delete x.tree.root.children[6].children[0].children[3].attributes.datetime,/absolute-review/);
blocked(x=>delete x.tree.root.children[6].children[0].children[4].attributes['data-rating'],/negative-stars/);
blocked(x=>x.tree.root.children[6].children[0].children[5].name='提交',/unknown-complaint/);
blocked(x=>x.tree.root.children[3].name='部分',/other-filter/);
blocked(x=>x.tree.root.children.pop(),/fold-boundary/);
blocked(x=>x.tree.root.children[6].children[0].children[2].name='长'.repeat(800),/may-be-truncated/);
const noFold=fixture();noFold.tree.root.children.pop();assert.equal(intakeReviewTree(noFold,job,{...profile,foldBoundary:null,normalRootIsExclusive:true}).ok,true);checks++;
const empty=fixture();empty.tree.root.children[2].name='已筛选0条';empty.tree.root.children[6].children=[];assert.equal(intakeReviewTree(empty,job,profile).capture.rows.length,0);checks++;
console.log(`${checks} pure semantic tree mock checks passed; no live acceptance`);
