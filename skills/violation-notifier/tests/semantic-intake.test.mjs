import assert from 'node:assert/strict';
import {intakeViolationTrees} from '../scripts/semantic-intake.mjs';
const job={account_verified:true,identity:{provider:'服务商测试',account_id:'123456',manager:'测试经理'},company:'测试公司',groupid:'123',start:'2026-10-17',end_exclusive:'2026-10-20'};
const profile={status:'live-validated',revision:'mock-only',identity:{provider:'#provider',account_id:'#account',manager:'#manager'}};
for(const section of ['analysis','records'])profile[section]={root:'#rows',row:{role:'row'},dateInput:'#dates',scope:'#scope',total:'#total',currentPage:'#page',next:'#next',otherFilters:{all:{locator:'#filter',expected:'全部'}},allReasons:'#reasons',unreadOnly:'#unread',violationType:{role:'type'},objectTypes:{role:'objects'},count:{role:'count'},idAttribute:'data-notice-id',subject:{role:'subject'}};
profile.detail={noticeId:'#id',subject:'#subject',date:'#date',actions:'#actions'};
for(const key of ['reason','object_type','object_name','effectiveness_status','rectification_status','public_recommendation'])profile.detail[key]='#'+key;
const leaf=(selector,name,attributes={})=>({selector,name,attributes,children:[]});
function envelope(children){return {source:'local-dom-bridge',tab_id:1,tab:{id:1,url:'https://life.douyin.com/p/governance?groupid=123'},observed_at:'2026-10-20T10:00:00+08:00',tree:{kind:'DOM-derived semantic tree (not native AX)',url:'https://life.douyin.com/p/governance',truncated:false,root:{selector:'body',children:[leaf('#provider',job.identity.provider),leaf('#account',job.identity.account_id),leaf('#manager',job.identity.manager),...children]}}};}
function page(rows,total,index,last){return envelope([leaf('#dates','2026/10/17 ~ 2026/10/19'),leaf('#scope','全部',{'aria-selected':'true'}),leaf('#total','全部 '+total),leaf('#page',String(index)),{...leaf('#next','下一页'),disabled:last},leaf('#filter','全部'),leaf('#reasons','全部',{'aria-selected':'true'}),leaf('#unread','只看未读',{'aria-checked':'false'}),{selector:'#rows',children:rows}]);}
const analysisRow=(type,count)=>({role:'row',children:[{role:'type',name:type,children:[]},{role:'objects',name:'门店、商品',children:[]},{role:'count',name:String(count),children:[]}]});
const recordRow=id=>({role:'row',attributes:{'data-notice-id':id},children:[{role:'subject',name:'测试门店'+id,children:[]}]});
function detail(id){return envelope([leaf('#id',id),leaf('#subject','测试门店'+id),leaf('#date','2天前',{datetime:'2026-10-18T10:00:00+08:00'}),leaf('#actions','下架商品；扣分'),...Object.entries({reason:'商品信息待完善',object_type:'商品',object_name:'测试商品',effectiveness_status:'已生效',rectification_status:'平台未显示',public_recommendation:'请核对商品展示内容'}).map(([k,v])=>leaf('#'+k,v))]);}
function fixture(){return {source:'local-dom-bridge',analysis:[page([analysisRow('资质待完善',1)],2,1,false),page([analysisRow('内容待优化',1)],2,2,true)],records:[page([recordRow('n1')],2,1,false),page([recordRow('n2')],2,2,true)],details:[detail('n1'),detail('n2')]};}
let checks=0;
function blocked(mut,regex,p=profile){const x=fixture();mut(x);const r=intakeViolationTrees(x,job,p);assert.equal(r.ok,false);assert.match(r.gaps[0],regex);checks++;}
let r=intakeViolationTrees(fixture(),job,profile);assert.equal(r.ok,true,JSON.stringify(r));assert.equal(r.live_accepted,false);assert.equal(r.capture.source,'local-dom-bridge');assert.deepEqual(r.capture.records.rows[0].actions,['下架商品','扣分']);checks++;
blocked(x=>{},/awaiting-live/,{...profile,status:'awaiting-live-validation'});
blocked(x=>x.analysis.pop(),/pagination-incomplete/);
blocked(x=>x.records[0].tree.truncated=true,/tree-incomplete/);
blocked(x=>x.records[1].tab.url='https://life.douyin.com/p/governance?groupid=999',/company-origin/);
blocked(x=>x.records[0].tree.root.children[0].name='不同服务商',/identity-tree-mismatch/);
blocked(x=>x.records[0].tree.root.children[3].name='2026/09/20 ~ 2026/10/20',/date-filter/);
blocked(x=>x.records[0].tree.root.children[10].attributes['aria-checked']='true',/unread-filter/);
blocked(x=>x.analysis[0].tree.root.children[9].attributes['aria-selected']='false',/all-reasons/);
blocked(x=>x.analysis[1].tree.root.children[6].name='1',/page-order/);
blocked(x=>x.analysis[1].tree.root.children[11].children[0].children[0].name='资质待完善',/duplicate-row/);
blocked(x=>x.records[1].tree.root.children[11].children[0].attributes['data-notice-id']='n1',/duplicate-row/);
blocked(x=>x.details.pop(),/details-incomplete/);
blocked(x=>x.details[0].tree.root.children[4].name='别的主体',/subject-mismatch/);
blocked(x=>delete x.details[0].tree.root.children[5].attributes.datetime,/absolute-date/);
blocked(x=>x.details[0].tree.root.children.at(-1).name='',/field-missing/);
blocked(x=>x.details[0].tree.root.children[7].name='商品信息…',/truncated/);
blocked(x=>x.details[0].tree.root.children[3].name='n999',/not-in-records/);
blocked(x=>x.details[1].observed_at='2026-10-21T10:00:00+08:00',/days-inconsistent/);
blocked(x=>x.records[0].source='codex-existing-extension',/source-mismatch/);
blocked(x=>x.details[0].tree.root.children.at(-1).name='长'.repeat(800),/may-be-truncated/);
const empty={source:'local-dom-bridge',analysis:[page([],0,1,true)],records:[page([],0,1,true)],details:[]};r=intakeViolationTrees(empty,job,profile);assert.equal(r.ok,true,JSON.stringify(r));assert.equal(r.capture.records.total,0);checks++;
console.log(`${checks} violation semantic tree mock checks passed; no live acceptance`);
