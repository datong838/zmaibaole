/* Public entry point: createWorkflow(browser, tab, job), then one tick per host call.
 * The fixed state machine owns sequencing, durable intents and task selection.
 * Local filesystem IO only; browser requests use stepped-runtime's public API.
 */
import fs from 'node:fs';
import path from 'node:path';
import {createHash, randomUUID} from 'node:crypto';
import {createSteppedOperator} from './stepped-runtime.mjs';

const VERSION=1;
const range=job=>({start:job.date_range?.start,end:job.date_range?.end});
const tag=job=>`门店评价_全部门店_${job.date_range.start.replace(/-/g,'_')}-${job.date_range.end.replace(/-/g,'_')}`;
const fingerprint=job=>createHash('sha256').update(JSON.stringify([VERSION,job.work_order_id,job.action,job.company,String(job.groupid),range(job),job.source_dir])).digest('hex');
function atomic(file,value){
  fs.mkdirSync(path.dirname(file),{recursive:true});const temp=file+'.'+randomUUID()+'.tmp';
  try{const fd=fs.openSync(temp,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(value,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}fs.renameSync(temp,file);}finally{if(fs.existsSync(temp))fs.unlinkSync(temp);}
}
function code(error){
  const s=String(error);if(/Debugger unattached|disconnected|connection-unavailable|could not read requirements/i.test(s))return 'connection-unavailable';
  return s.replace(/^Error: /,'').split(':')[0];
}
function validate(job){
  if(!['acquire','return-company'].includes(job.action)||!job.company||!/^\d+$/.test(String(job.groupid))||!job.work_order_id||!path.isAbsolute(job.workflow_path||''))throw Error('work-order-invalid');
  if(job.action==='acquire'){
    for(const key of ['start','end']){
      const value=job.date_range?.[key];
      if(!/^\d{4}-\d{2}-\d{2}$/.test(value||'')||!Number.isFinite(Date.parse(value))||new Date(value).toISOString().slice(0,10)!==value)throw Error('work-order-date-invalid');
    }
    if(job.date_range.start>job.date_range.end)throw Error('work-order-date-invalid');
  }
}
function checkpoint(s,event){s.checkpoints.push({...event,event_id:randomUUID(),at:new Date().toISOString()});}
function identityKey(i){return ['provider','account_id','manager'].map(k=>i?.[k]||'').join('\u0000');}

// One transition after a completed method. No host IO, no model-selected methods.
export function transition(s,job,result){
  const go=p=>{s.phase=p;};
  switch(s.phase){
    case 'account':
      if(!result?.identity||['provider','account_id','manager'].some(k=>!result.identity[k]))throw Error('identity-unverified');
      if(s.identity&&identityKey(s.identity)!==identityKey(result.identity))throw Error('account-changed');
      if(job.identity_baseline&&identityKey(job.identity_baseline)!==identityKey(result.identity))throw Error('account-changed');
      s.identity=result.identity;checkpoint(s,result);go('context');break;
    case 'context':go(String(result.groupid)===String(job.groupid)?'verifySwitch':'openSwitch');break;
    case 'openSwitch':go('searchCompany');break;
    case 'searchCompany':go('chooseCompany');break;
    case 'chooseCompany':go('confirmSwitch');break;
    case 'confirmSwitch':go('verifySwitch');break;
    case 'verifySwitch':
      if(String(result.groupid)!==String(job.groupid))throw Error('source-company-mismatch');
      if(identityKey(s.identity)!==identityKey(result.identity))throw Error('account-changed');
      checkpoint(s,result);
      if(job.action==='return-company'){
        s.result={verified:true,company:job.company,groupid:String(job.groupid),identity:s.identity};s.state='complete';go('done');
      }else if(s.recoverPhase){go(s.recoverPhase);delete s.recoverPhase;}
      else go('openReviews');
      break;
    case 'openReviews':checkpoint(s,{stage:'navigation',groupid:String(job.groupid)});go('openPageCalendar');break;
    case 'openPageCalendar':go('pageStart');break;
    case 'pageStart':go('pageEnd');break;
    case 'pageEnd':go('verifyFilter');break;
    case 'verifyFilter':s.pageFiltered=result.page_filtered;checkpoint(s,result);go('baselineTabs');break;
    case 'baselineTabs':
    case 'recordTabs':{
      const items=result,phase=s.phase;
      if(!Array.isArray(items))throw Error('record-tab-unverified');
      if(!items.length){
        if(s.openedRecords)throw Error('record-tab-missing');
        s.afterOpen=phase;go('recordsMenu');break;
      }
      let selected=items.filter(t=>String(t.id)===String(job.record_tab_id||s.recordTabId||''));
      if(!selected.length&&items.length===1)selected=items;
      if(phase==='recordTabs'&&selected.length!==1){
        const newlyOpened=items.filter(t=>!(s.baselineTabIds||[]).includes(String(t.id)));
        if(newlyOpened.length===1)selected=newlyOpened;
      }
      if(selected.length!==1)throw Error('record-tab-ambiguous');
      s.recordTabId=selected[0].id;s.baselineTabIds=items.map(t=>String(t.id));s.afterUse=phase==='baselineTabs'?'baselineRecords':'pollRecords';go('useRecordTab');break;
    }
    case 'recordsMenu':go('openRecordMenu');break;
    case 'openRecordMenu':s.openedRecords=true;go(s.afterOpen);break;
    case 'useRecordTab':go(s.afterUse);break;
    case 'baselineRecords':s.baseline=result;s.openedRecords=false;go('openExportMenu');break;
    case 'openExportMenu':go('openExportDialog');break;
    case 'openExportDialog':go('exportRange');break;
    case 'exportRange':go(result.correct?'prepareSubmit':'openExportCalendar');break;
    case 'openExportCalendar':go('exportStart');break;
    case 'exportStart':go('exportEnd');break;
    case 'exportEnd':go('checkExportRange');break;
    case 'checkExportRange':if(!result.correct)throw Error('export-range-mismatch');go('prepareSubmit');break;
    case 'prepareSubmit':
      if(s.exportPending)throw Error('export-outcome-unknown');
      if(s.attempts>=3)throw Error('export-retries-exhausted');
      s.attempts++;s.exportPending=true;checkpoint(s,result);s.submittedAt=Date.now();go('submit');break;
    case 'submit':checkpoint(s,result);go('recordTabs');break;
    case 'pollRecords':{
      const same=result.filter(r=>r.text.includes(tag(job))&&!s.baseline.some(old=>old.generated_at===r.generated_at&&old.text.includes(tag(job))));
      if(same.length>1)throw Error('generated-record-ambiguous');
      if(same.length===1&&same[0].state==='success'){
        if(!same[0].generated_at)throw Error('generated-record-unverified');
        s.generatedAt=same[0].generated_at;go('verifyRecord');break;
      }
      if(same.length===1&&same[0].state==='failed'){
        checkpoint(s,{stage:'export-failed',platform_status:'failed',record_reference:same[0].text});
        s.exportPending=false;
        if(s.attempts>=3)throw Error('export-retries-exhausted');
        s.baseline=result;s.resetOperator=true;go('openExportMenu');break;
      }
      if(Date.now()-s.submittedAt>600000)throw Error('export-outcome-unknown');
      s.pollCount=(s.pollCount||0)+1;s.notBefore=Date.now()+Math.min(30000,5000*s.pollCount);break;
    }
    case 'verifyRecord':checkpoint(s,result);go('prepareDownload');break;
    case 'prepareDownload':go('armDownload');break;
    case 'armDownload':checkpoint(s,result);s.downloadPending=true;go('clickDownload');break;
    case 'clickDownload':go('downloadResult');break;
    case 'downloadResult':
      if(!result.source)throw Error('download-path-missing');
      checkpoint(s,{stage:'download-complete',source:result.source,generated_at:s.generatedAt});
      s.result=result;s.downloadPending=false;s.state='complete';go('done');break;
    default:throw Error('workflow-phase-invalid');
  }
  // Arguments are computed by code; neither UI text nor callers choose actions.
  return s;
}
function methodFor(s,job){
  if(['pageStart','exportStart'].includes(s.phase))return ['calendarDate',job.date_range.start];
  if(['pageEnd','exportEnd'].includes(s.phase))return ['calendarDate',job.date_range.end];
  if(['baselineTabs','recordTabs'].includes(s.phase))return ['recordTabs'];
  if(['baselineRecords','pollRecords'].includes(s.phase))return ['listRecords'];
  if(s.phase==='recordsMenu')return ['openExportMenu'];
  if(s.phase==='checkExportRange')return ['exportRange'];
  if(s.phase==='useRecordTab')return ['useRecordTab',s.recordTabId];
  if(s.phase==='verifyRecord')return ['verifyRecord',s.generatedAt];
  if(['submit','clickDownload'].includes(s.phase))return [s.phase,true];
  return [s.phase];
}
// Explicit supervisor re-dispatch after a transport fault. Preserve all intents;
// refresh identity before any business step and never repeat an uncertain download.
export function recoverConnection(s,job){
  const request=job.recovery_request;
  if(!request||request.kind!=='connection-recovery'||typeof request.id!=='string'||!request.id)return false;
  if(s.state!=='failed'||s.error_code!=='connection-unavailable'||s.lastRecoveryRequestId===request.id)return false;
  if(s.downloadPending)throw Error('download-outcome-unknown: reconcile existing download before recovery');
  s.recoveryHistory=s.recoveryHistory||[];
  s.recoveryHistory.push({id:request.id,at:new Date().toISOString(),phase:s.phase,error:s.error});
  s.lastRecoveryRequestId=request.id;s.state='running';s.phase='account';
  s.recoverPhase=s.exportPending?'recordTabs':null;
  delete s.error;delete s.error_code;delete s.notBefore;
  return true;
}
export async function createWorkflow(browser,tab,job){
  validate(job);job=JSON.parse(JSON.stringify(job));const file=job.workflow_path,fp=fingerprint(job);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  let s;
  if(fs.existsSync(file)){
    s=JSON.parse(fs.readFileSync(file,'utf8'));
    if(s.version!==VERSION)throw Error('workflow-version-mismatch');
    if(s.fingerprint!==fp)throw Error('work-order-conflict');
    recoverConnection(s,job);
    // An event waiter cannot survive a kernel reset. Never click a second time.
    if(s.state==='running'){
      if(s.downloadPending){s.state='failed';s.error_code='download-outcome-unknown';}
      else{
        if(s.phase==='submit')s.phase='recordTabs';
        s.recoverPhase=s.exportPending?'recordTabs':null;s.phase='account';
      }
    }
  }else{
    if(job.resume?.export_pending||job.resume?.checkpoints?.some(e=>e.stage==='export-intent'))throw Error('legacy-export-outcome-unknown');
    s={version:VERSION,work_order_id:job.work_order_id,fingerprint:fp,company:job.company,groupid:String(job.groupid),date_range:range(job),phase:'account',state:'running',checkpoints:[],attempts:0,revision:0};
  }
  let controller=null,busy=false,loadedRevision=s.revision;
  function persist(){s.revision++;s.updated_at=new Date().toISOString();atomic(file,s);loadedRevision=s.revision;}
  // Do not overwrite a different worker's journal during construction.
  // Initial/recovery state is committed under the same exclusive lock as tick.
  let recoveryPending=true;
  function resumeJob(){return {...job,identity_baseline:s.identity||job.identity_baseline,resume:{export_pending:s.exportPending,checkpoints:s.checkpoints}};}
  function status(){return {state:s.state,phase:s.phase,error_code:s.error_code||null,error:s.error||null,next_poll_at:s.notBefore||null,journal:file,result_file:s.state==='complete'?file:null,result:s.state==='complete'?s.result:null,ui:controller?.status()||null};}
  async function tick(){
    if(busy)throw Error('workflow-busy');busy=true;let lockfd;
    try{
      lockfd=fs.openSync(file+'.lock','wx',0o600);
      if(fs.existsSync(file)&&JSON.parse(fs.readFileSync(file,'utf8')).revision!==loadedRevision)throw Error('workflow-concurrent-change');
      if(recoveryPending){persist();recoveryPending=false;}
      if(s.state!=='running')return status();
      if(s.notBefore&&Date.now()<s.notBefore)return status();delete s.notBefore;
      if(!controller)controller=await createSteppedOperator(browser,tab,resumeJob());
      let current=controller.status();
      if(current.state==='running'||current.pending)current=await controller.step();
      else{
        const [method,...args]=methodFor(s,job);current=await controller.start(method,...args);
      }
      if(current.state==='failed')throw Error(current.error_code+': '+current.error);
      if(current.state==='complete'&&!current.pending){
        transition(s,job,current.result);persist();
        if(s.resetOperator){
          delete s.resetOperator;controller=null;s.recoverPhase=s.phase;s.phase='account';persist();
        }
      }
      return status();
    }catch(error){
      if(lockfd===undefined||/workflow-concurrent-change/.test(String(error)))throw error;
      s.state='failed';s.error=String(error);s.error_code=code(error);persist();return status();
    }finally{
      if(lockfd!==undefined){fs.closeSync(lockfd);fs.unlinkSync(file+'.lock');}busy=false;
    }
  }
  return Object.freeze({tick,status});
}
export default createWorkflow;
