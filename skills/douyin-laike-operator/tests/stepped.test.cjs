const assert=require('node:assert/strict'),path=require('node:path'),{pathToFileURL}=require('node:url');
(async()=>{
  const {createSteppedOperator}=await import(pathToFileURL(path.join(__dirname,'../scripts/stepped-runtime.mjs')).href);
  let calls=[];let active=false;
  function call(name,value){assert.ok(active,'Host call escaped an active step');calls.push(name);return Promise.resolve(value);}
  const identity={provider:'服务商123',account_id:'987654321',manager:'测试经理'};
  const fake={id:'tab',url:()=>call('url','https://life.douyin.com/p/life_comment/management?groupid=123'),playwright:{
    domSnapshot:()=>call('snapshot','评价管理'),getByRole:()=>({isVisible:()=>call('menuVisible',true)}),evaluate:()=>call('accountDOM',identity)
  }};
  const task=await createSteppedOperator({},fake,{action:'acquire',company:'测试公司',groupid:'123',date_range:{start:'2026-10-16',end:'2026-10-18'}});
  let status=await task.start('account');assert.equal(calls.length,0);
  let steps=0;
  while(status.state==='running'||status.pending){
    const before=calls.length;active=true;status=await task.step();active=false;
    assert.ok(calls.length-before<=1,'More than one UI call per tool step');assert.ok(++steps<30);
  }
  assert.equal(status.state,'complete');assert.deepEqual(status.result.identity,identity);assert.equal(calls.length,4);
  await assert.rejects(()=>task.start('arbitraryClick'),/not-allowed/);
  // The same composed method surfaces a host failure instead of scheduling another write.
  fake.playwright.evaluate=()=>{assert.ok(active);calls.push('error');throw Error('account-changed');};
  status=await task.start('account');
  while(status.state==='running'||status.pending){active=true;status=await task.step();active=false;}
  assert.equal(status.state,'failed');assert.match(status.error,/account-changed/);assert.equal(status.error_code,'account-changed');await assert.rejects(()=>task.start('account'),/previous-step-failed/);
  console.log('Stepped runtime: zero background UI calls, at most one UI request per step, real role composition and host-error propagation passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
