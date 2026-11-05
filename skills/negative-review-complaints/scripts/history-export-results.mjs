/* Independent history-state XLSX export. No daily cursor, browser or messaging. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const forbidden=['next_start','initial_start','covered_through','last_completed_on','batches'];
const label={accepted:'投诉通过',rejected:'投诉未通过',pending:'平台处理中',unknown:'结果未知'};
// Untrusted cells are always literal strings, including leading whitespace/control.
export const literal=v=>typeof v==='string' && /^[\s\u0000-\u001f]*[=+@-]/u.test(v)?"'"+v:v;
const text=v=>v==null?'':String(v);
const date=v=>{need(/^\d{4}-\d{2}-\d{2}$/.test(v)&&!Number.isNaN(Date.parse(v+'T00:00:00Z')),'invalid-review-date');return new Date(v+'T00:00:00Z');};
function clock(v){if(!v)return null;const t=Date.parse(v);need(Number.isFinite(t),'invalid-observation-time');return new Date(t+8*3600000);}
const complaintTime=v=>{if(!v)return null;need(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(v),'invalid-complaint-time');const t=new Date(v.replace(' ','T')+'Z');need(Number.isFinite(t.getTime()),'invalid-complaint-time');return t;};
export function data(state){
  need(state.workspace_kind==='negative-review-appeal-history-only-v1'&&state.domain==='negative-review-appeal-cases'&&state.mode==='draft-only','history-state-required');
  need(!forbidden.some(k=>k in state),'daily-progress-not-history');
  need(typeof state.company==='string'&&state.company&&/^\d+$/.test(state.groupid),'company-group-required');
  const scope=state.history_range;date(scope.start);date(scope.end_exclusive);need(scope.start<scope.end_exclusive,'invalid-half-open-range');
  const tasks=Object.values(state.tasks),ids=new Set(),skipped=new Set();let normal=0;
  for(const s of Object.values(state.sources)){
    need(scope.start<=s.start&&s.start<s.end_exclusive&&s.end_exclusive<=scope.end_exclusive,'source-range-outside-history');
    need(Array.isArray(s.existing_ids)&&Array.isArray(s.skipped_uncomplained_ids)&&Number.isInteger(s.normal_count)&&s.normal_count===s.existing_ids.length+s.skipped_uncomplained_ids.length,'source-count-mismatch');
    for(const [values,set] of [[s.existing_ids,ids],[s.skipped_uncomplained_ids,skipped]])for(const id of values){need(!ids.has(id)&&!skipped.has(id),'duplicate-source-id');set.add(id);}
    normal+=s.normal_count;
  }
  need(ids.size===tasks.length&&tasks.every(t=>ids.has(t.id)&&state.tasks[t.id]===t),'task-source-id-mismatch');
  tasks.sort((a,b)=>a.review.date.localeCompare(b.review.date)||a.id.localeCompare(b.id));
  const rows=[];let read=0,waiting=0,histories=0;
  for(const t of tasks){
    const r=t.review;need(['查看投诉结果','投诉审核中'].includes(t.action)&&scope.start<=r.date&&r.date<scope.end_exclusive,'history-task-action-or-date');
    need(typeof r.text==='string'&&typeof r.store==='string'&&typeof r.customer==='string'&&Number.isFinite(r.stars),'review-fields-required');
    const result=t.result;need(!result||label[result.status],'unknown-current-result-status');
    if(result)read++;if(!result||['pending','unknown'].includes(result.status))waiting++;
    const original=result?.original_complaint||{};
    const base=[state.company,t.id,date(r.date),r.store,r.customer,r.stars,r.text,r.product||''];
    const evidence=[result?.evidence?.path||'',t.completed_operation?.path||'',t.latest_snapshot?.path||''];
    rows.push([...base,'当前申诉',result?'已读取':'未读取',original['投诉类型']||'',original['投诉理由']||'',complaintTime(original['投诉时间']),result?label[result.status]:'未读取',result?.platform_status||'',result?.visible_text||'',clock(result?.observed_at),...evidence,t.body_provenance?.body_kind||'',t.body_provenance?.image_count??null]);
    need(!result?.complaint_history||Array.isArray(result.complaint_history),'complaint-history-array-required');
    for(const h of result?.complaint_history||[]){
      need(h&&typeof h.original_complaint==='object','history-form-required');const f=h.original_complaint;histories++;
      rows.push([...base,'历史申诉','已读取表单',f['投诉类型']||'',f['投诉理由']||'',complaintTime(f['投诉时间']),'结果未知','历史表单不证明独立结果','',clock(result.observed_at),...evidence,t.body_provenance?.body_kind||'',t.body_provenance?.image_count??null]);
    }
  }
  return {scope,rows,normal_count:normal,existing_ids:ids.size,skipped_count:skipped.size,results_read:read,unread:tasks.length-read,recheck:waiting,history_rows:histories};
}
export async function exportHistory(statePath,out,previewDir){
  statePath=path.resolve(statePath);out=path.resolve(out);need(statePath!==out&&out.endsWith('.xlsx'),'xlsx-output-required');
  const bytes=await fs.readFile(statePath),stateSha=sha(bytes),state=JSON.parse(bytes),d=data(state),wb=Workbook.create();
  const summary=wb.worksheets.add('历史复查汇总');summary.showGridLines=false;
  summary.getRange('A2').values=[['历史投诉复查结果']];summary.getRange('A2').format.font={name:'Arial',size:14,bold:true};
  const metrics=[['公司',state.company],['平台公司编号',state.groupid],['评价日期起始（含）',date(d.scope.start)],['评价日期截止（不含）',date(d.scope.end_exclusive)],['正常筛选评价数',d.normal_count],['已投诉或审核中评价数',d.existing_ids],['未投诉跳过数',d.skipped_count],['已读取当前结果数',d.results_read],['尚未读取结果数',d.unread],['待复查数（含未读和处理中/未知）',d.recheck],['历史申诉表单行数',d.history_rows],['范围说明','仅当前正常筛选中的既有投诉；不含折叠区、未显示或已移除评价。'],['历史结果说明','历史申诉表单与当前申诉分列；未核验独立结果记为未知。'],['来源状态路径',statePath],['来源状态 SHA256',stateSha]];
  summary.getRangeByIndexes(3,0,metrics.length,2).values=metrics.map(r=>r.map(literal));
  const sr=summary.getRangeByIndexes(3,0,metrics.length,2);sr.format.font={name:'Arial',size:10};sr.format.rowHeight=27;sr.format.verticalAlignment='center';
  summary.getRange('A4:A18').format.columnWidth=44;summary.getRange('B4:B18').format.columnWidth=104;summary.getRange('B6:B7').setNumberFormat('yyyy-mm-dd');summary.getRange('B8:B14').setNumberFormat('#,##0');summary.getRange('B15:B18').format.wrapText=true;summary.getRange('A15:B18').format.autofitRows();
  const headers=['公司','评价编号','评价日期','门店','顾客','星级','评价原文','商品','申诉记录类别','读取状态','投诉类型','原投诉理由','原投诉时间（北京时间）','独立结果','平台当前状态或备注','结果原文','本次读取时间（北京时间）','结果证据路径','操作证据路径','评价来源路径','正文形态','评价图片数'];
  const detail=wb.worksheets.add('逐条申诉结果');detail.showGridLines=false;
  const range=detail.getRangeByIndexes(0,0,d.rows.length+1,headers.length);range.values=[headers,...d.rows].map(r=>r.map(literal));range.format.font={name:'Arial',size:10};range.format.rowHeight=28;range.format.verticalAlignment='center';
  detail.getRangeByIndexes(0,0,1,headers.length).format={fill:'#24364B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:34,wrapText:true,horizontalAlignment:'center'};
  [30,34,14,36,18,8,64,40,15,16,18,76,26,20,30,76,29,55,55,55,24,12].forEach((w,i)=>detail.getRangeByIndexes(0,i,d.rows.length+1,1).format.columnWidth=w);
  if(d.rows.length){
    detail.getRangeByIndexes(1,2,d.rows.length,1).setNumberFormat('yyyy-mm-dd');for(const i of [12,16])detail.getRangeByIndexes(1,i,d.rows.length,1).setNumberFormat('yyyy-mm-dd hh:mm:ss');
    for(const i of [6,7,11,15])detail.getRangeByIndexes(1,i,d.rows.length,1).format.wrapText=true;
    detail.getRangeByIndexes(1,0,d.rows.length,headers.length).format.autofitRows();detail.tables.add(range,true,'HistoryResults').showFilterButton=true;
  }
  detail.freezePanes.freezeRows(1);detail.freezePanes.freezeColumns(2);wb.recalculate();
  await wb.inspect({kind:'region',sheetId:'历史复查汇总',range:'A4:B14',maxChars:1500,tableMaxRows:11,tableMaxCols:2});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:1000});
  if(previewDir){
    previewDir=path.resolve(previewDir);await fs.mkdir(previewDir,{recursive:true});
    for(const [sheetName,region,name] of [['历史复查汇总','A2:B16','summary'],['逐条申诉结果',`C1:N${Math.min(d.rows.length+1,6)}`,'details'],['逐条申诉结果',`M1:Q${Math.min(d.rows.length+1,6)}`,'results']]){
      const image=await wb.render({sheetName,range:region,scale:1,format:'png'});await fs.writeFile(path.join(previewDir,name+'.png'),new Uint8Array(await image.arrayBuffer()));
    }
  }
  await fs.mkdir(path.dirname(out),{recursive:true});const pending=path.join(path.dirname(out),'.'+path.basename(out)+'.'+crypto.randomUUID()+'.pending.xlsx');
  try{await(await SpreadsheetFile.exportXlsx(wb)).save(pending);need(sha(await fs.readFile(statePath))===stateSha,'state-changed-during-export');const h=await fs.open(pending,'r');try{await h.sync();}finally{await h.close();}await fs.rename(pending,out);const dir=await fs.open(path.dirname(out),'r');try{await dir.sync();}finally{await dir.close();}}
  finally{await fs.rm(pending,{force:true});}
  return {path:out,sha256:sha(await fs.readFile(out)),state:{path:statePath,sha256:stateSha},company:state.company,range:d.scope,normal_count:d.normal_count,existing_ids:d.existing_ids,skipped_count:d.skipped_count,results_read:d.results_read,recheck:d.recheck,rows:d.rows.length,current_rows:d.existing_ids,history_rows:d.history_rows,data_sha256:sha(JSON.stringify(d)),formula_scan_completed:!!errors,submission_enabled:false,business_cursor_updated:false};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  try{const args={};const tokens=process.argv.slice(2);need(tokens.length%2===0,'expected-key-value-args');for(let i=0;i<tokens.length;i+=2){need(['--state','--out','--preview-dir'].includes(tokens[i])&&!args[tokens[i]],'unknown-or-duplicate-option');args[tokens[i]]=tokens[i+1];}need(args['--state']&&args['--out'],'usage: history-export-results.mjs --state ABS_STATE --out ABS_XLSX [--preview-dir ABS_DIR]');console.log(JSON.stringify(await exportHistory(args['--state'],args['--out'],args['--preview-dir'])));}
  catch(e){console.error(JSON.stringify({ok:false,error:e.message}));process.exitCode=1;}
}
