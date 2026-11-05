import assert from 'node:assert/strict';
import {validateProfile,inspectReviews,openComplaint} from '../scripts/browser-review.mjs';
assert.throws(()=>validateProfile({status:'awaiting-live-validation'}),/awaiting-live/);
const profile={status:'live-validated',revision:'fixture'};
for(const k of ['root','row','filteredCount','foldBoundary','idAttribute','store','customer','text','date','stars','action','activeNegative','dateInput'])profile[k]='[data-'+k+']';
const job={account_verified:true,identity:{provider:'test',account_id:'123456789',manager:'test'},company:'测试',groupid:'123',start:'2026-10-19',end:'2026-10-19',end_exclusive:'2026-10-20'};
let clicked=0;
function mock({url='https://life.douyin.com/?groupid=123',snapshot='评价管理',rows=[{review_id:'r1',action:'查看投诉结果'}]}={}){
  const target={getByText(label){assert.equal(label,rows[0].action);return this;},async count(){return 1;},async isVisible(){return true;},async click(){clicked++;}};
  return {async url(){return url;},playwright:{async domSnapshot(){return snapshot;},async evaluate(){if(/请完成验证/.test(snapshot))throw Error('connection-risk-stop');return {rows};},locator(){return target;}}};
}
const noFold={...profile,foldBoundary:null,normalRootIsExclusive:true};validateProfile(noFold);
assert.throws(()=>validateProfile({...noFold,normalRootIsExclusive:false}),/boundary-unverified/);
await assert.rejects(()=>inspectReviews(mock({url:'https://example.com/'}),job,profile),/company-origin/);
await assert.rejects(()=>inspectReviews(mock({snapshot:'请完成验证'}),job,profile),/risk-stop/);
await assert.rejects(()=>openComplaint(mock(),job,profile,'other'),/not-in-current-filter/);
assert.equal(clicked,0);
const opened=await openComplaint(mock(),job,profile,'r1');
assert.equal(opened.opened,'查看投诉结果');assert.equal(opened.submission_enabled,false);assert.equal(clicked,1);
await assert.rejects(()=>openComplaint(mock({rows:[{review_id:'r1',action:'提交'}]}),job,profile,'r1'),/unreviewed/);
assert.equal(clicked,1);
console.log('browser adapter boundary tests passed (mock only)');
