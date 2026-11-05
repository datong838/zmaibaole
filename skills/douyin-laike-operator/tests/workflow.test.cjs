const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {pathToFileURL}=require('node:url');
(async()=>{
 const {createWorkflow,transition}=await import(pathToFileURL(path.join(__dirname,'../scripts/workflow-runtime.mjs')).href);
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'laike-workflow-'));
 const identity={provider:'服务商123',account_id:'987654321',manager:'测试经理'};
 const dates={start:'2026-10-16',end:'2026-10-18'},groupid='123';
 const tag='门店评价_全部门店_2026_10_16-2026_10_18';
 function job(name='run'){return {action:'acquire',company:'测试公司',groupid,date_range:dates,source_dir:root,work_order_id:name,workflow_path:path.join(root,name+'.json')};}
 function host(work,options={}){
  let calls=0,submitted=0,downloads=0,resolveDownload,active=false;
  const recordUrl='https://life.douyin.com/p/export_records/20101?groupid=123';
  function call(value){assert.ok(active,'UI request outside tick');calls++;return Promise.resolve(value);}
  function locator(kind,name){return {
   count:()=>call(1),isVisible:()=>call(true),isEnabled:()=>call(true),
   getByText:(text)=>locator('text',text),getByRole:(role,opt)=>locator(role,opt?.name),filter:()=>locator(kind,name),
   evaluate:(fn)=>call(kind==='placeholder'?`${dates.start} ~ ${dates.end}`:'全部'),
   evaluateAll:(fn)=>{
    const body=String(fn);
    if(body.includes('generated_at'))return call(submitted?[{text:tag+'\n2026-10-20 18:00:0'+submitted+'\n'+(submitted<=(options.failCount||0)?'生成失败':'生成成功'),generated_at:'2026-10-20 18:00:0'+submitted,state:submitted<=(options.failCount||0)?'failed':'success'}]:[]);
    if(body.includes('function path'))return call(['#calendar-day']);
    return call([{value:`${dates.start} ~ ${dates.end}`}]);
   },
   click:()=>{
    // Both irreversible intents must already be on disk BEFORE click.
    if(kind==='button'&&name==='导出'){const s=JSON.parse(fs.readFileSync(work.workflow_path));assert.equal(s.phase,'submit');assert.ok(s.checkpoints.some(e=>e.stage==='export-intent'));submitted++;}
    if(name==='下载'){const s=JSON.parse(fs.readFileSync(work.workflow_path));assert.ok(s.checkpoints.some(e=>e.stage==='download-intent'));downloads++;resolveDownload({path:()=>call('/tmp/fake-fixture.xlsx')});}
    return call(null);
   },fill:()=>call(null)
  };}
  function tab(records){return {id:records?'record':'main',url:()=>call(records?recordUrl:'https://life.douyin.com/p/life_comment/management?groupid=123'),playwright:{
   domSnapshot:()=>call('评价管理 已筛选 2 条'),evaluate:()=>call(identity),
   getByRole:(r,o)=>locator(r,o?.name),getByText:t=>locator('text',t),getByPlaceholder:t=>locator('placeholder',t),locator:t=>locator('selector',t),
   waitForEvent:()=>{call(null);return new Promise(resolve=>{resolveDownload=resolve;});}
  }};}
  const main=tab(false),records=tab(true);
  const browser={tabs:{list:()=>call([{id:'record',url:recordUrl}]),get:()=>call(records)}};
  return {browser,main,get submitted(){return submitted;},get downloads(){return downloads;},
   async tick(op){const before=calls;active=true;try{const s=await op.tick();assert.ok(calls-before<=1,'More than one UI call per tick');return s;}finally{active=false;}}};
 }
 try{
  const work=job(),h=host(work),op=await createWorkflow(h.browser,h.main,work);
  assert.deepEqual(Object.keys(op).sort(),['status','tick']); // No caller-selected business actions.
  let result;
  for(let n=0;n<600;n++){result=await h.tick(op);if(result.state!=='running')break;}
  assert.equal(result.state,'complete',JSON.stringify(result));assert.equal(h.submitted,1);assert.equal(h.downloads,1);
  const saved=JSON.parse(fs.readFileSync(work.workflow_path));assert.equal(saved.phase,'done');assert.equal(saved.result.page_filtered,2);
  assert.deepEqual(saved.checkpoints.map(e=>e.stage),['identity','switch','navigation','filter','export-intent','export-submitted','export-generated','download-intent','download-complete']);
  await h.tick(op);assert.equal(h.submitted,1);assert.equal(h.downloads,1);
  const restored=await createWorkflow(h.browser,h.main,work);assert.equal((await h.tick(restored)).state,'complete');assert.equal(h.submitted,1);
  // Kernel loss immediately before/during submit: reconcile records, never submit again.
  const recovering=job('recover');const interrupted={...saved,work_order_id:'recover',phase:'submit',state:'running',exportPending:true,checkpoints:saved.checkpoints.slice(0,5)};
  // Fingerprint changes with work-order ID, so create a legitimate fresh journal first.
  const rh=host(recovering),initial=await createWorkflow(rh.browser,rh.main,recovering);await rh.tick(initial);
  const fresh=JSON.parse(fs.readFileSync(recovering.workflow_path));Object.assign(fresh,interrupted,{fingerprint:fresh.fingerprint,revision:fresh.revision,downloadPending:false});fs.writeFileSync(recovering.workflow_path,JSON.stringify(fresh));
  const recovery=await createWorkflow(rh.browser,rh.main,recovering);
  for(let n=0;n<90;n++){await rh.tick(recovery);if(recovery.status().phase==='pollRecords')break;}
  assert.equal(rh.submitted,0);assert.equal(recovery.status().phase,'pollRecords');
  // Download intent survives a reset as UNKNOWN, never silently clears.
  fresh.downloadPending=true;fresh.phase='clickDownload';fs.writeFileSync(recovering.workflow_path,JSON.stringify(fresh));
  const uncertain=await createWorkflow(rh.browser,rh.main,recovering);assert.equal((await rh.tick(uncertain)).error_code,'download-outcome-unknown');assert.equal(rh.downloads,0);
  // Exclusive writer and revision checks prevent two loaded workers replaying work.
  const cj=job('concurrency'),ch=host(cj),a=await createWorkflow(ch.browser,ch.main,cj),b=await createWorkflow(ch.browser,ch.main,cj);
  await ch.tick(a);await assert.rejects(()=>ch.tick(b),/concurrent-change/);
  fs.writeFileSync(cj.workflow_path+'.lock','locked');await assert.rejects(()=>ch.tick(a),/EEXIST/);fs.unlinkSync(cj.workflow_path+'.lock');
  // Task attribution is based on baseline difference and refuses ambiguity.
  const s={phase:'pollRecords',baseline:[],submittedAt:Date.now(),checkpoints:[],attempts:1};
  assert.throws(()=>transition(s,work,[{text:tag,generated_at:'x',state:'success'},{text:tag,generated_at:'y',state:'success'}]),/ambiguous/);
  const failure={phase:'pollRecords',baseline:[],submittedAt:Date.now(),checkpoints:[],attempts:3};
  assert.throws(()=>transition(failure,work,[{text:tag,generated_at:'x',state:'failed'}]),/retries-exhausted/);
  const rj={...job('return'),action:'return-company'},rhost=host(rj),rop=await createWorkflow(rhost.browser,rhost.main,rj);
  for(let n=0;n<100;n++){result=await rhost.tick(rop);if(result.state!=='running')break;}
  assert.equal(result.result.verified,true);assert.equal(rhost.submitted,0);
  const retryJob=job('retry'),retryHost=host(retryJob,{failCount:2}),retryOp=await createWorkflow(retryHost.browser,retryHost.main,retryJob);
  for(let n=0;n<1200;n++){result=await retryHost.tick(retryOp);if(result.state!=='running')break;}
  assert.equal(result.state,'complete',JSON.stringify(result));assert.equal(retryHost.submitted,3);assert.equal(retryHost.downloads,1);
  const exhaustJob=job('exhaust'),exhaustHost=host(exhaustJob,{failCount:9}),exhaustOp=await createWorkflow(exhaustHost.browser,exhaustHost.main,exhaustJob);
  for(let n=0;n<1200;n++){result=await exhaustHost.tick(exhaustOp);if(result.state!=='running')break;}
  assert.equal(result.state,'failed');assert.equal(exhaustHost.submitted,3);assert.equal(exhaustHost.downloads,0);
  console.log('Fixed workflow: complete acquisition, durable pre-click intents, no duplicate after resume, ambiguity/retry cap, return-company, locks, and <=1 UI call per tick passed (synthetic host).');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
