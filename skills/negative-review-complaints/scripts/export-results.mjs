/* JSON event ledger -> reproducible XLSX; no browser or messaging calls. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const [input,output,previewDir,previewScope]=process.argv.slice(2);
if(!input||!output)throw Error('usage: export-results.mjs state.json output.xlsx [preview-directory]');
const state=JSON.parse(await fs.readFile(input,'utf8'));
const tasks=Object.values(state.tasks).sort((a,b)=>a.review.date.localeCompare(b.review.date)||a.id.localeCompare(b.id));
const labels={pending:'待处理',draft_ready:'草稿完成，未提交',existing_pending:'已投诉，待复查',resolved:'已复查，结果已记录',blocked:'阻塞，待核实'};
const resultLabels={pending:'平台处理中',accepted:'投诉通过',rejected:'投诉未通过',unknown:'结果未知'};
// Never interpret review text, names, draft text or paths as spreadsheet formulas.
const literal=v=>typeof v==='string' && /^[=+@-]/.test(v)?"'"+v:v;
const excelDate=v=>v?new Date(v.slice(0,10)+'T00:00:00Z'):null;
const clockDate=v=>v?new Date(Date.parse(v)+8*3600*1000):null;
const wb=Workbook.create();
let tableCounter=0;
const summary=wb.worksheets.add('处理汇总');summary.showGridLines=false;
function sheet(name,headers,rows,widths){
  const s=wb.worksheets.add(name);s.showGridLines=false;
  const n=Math.max(1,rows.length+1),m=headers.length;
  const whole=s.getRangeByIndexes(0,0,n,m);whole.values=[headers,...rows].map(r=>r.map(literal));
  whole.format.font={name:'Arial',size:10};whole.format.verticalAlignment='center';whole.format.rowHeight=28;
  s.getRangeByIndexes(0,0,1,m).format={fill:'#24364B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center'};
  widths.forEach((w,c)=>s.getRangeByIndexes(0,c,n,1).format.columnWidth=w);
  if(rows.length){const t=s.tables.add(s.getRangeByIndexes(0,0,n,m),true,'Table'+(++tableCounter));t.showFilterButton=true;}
  s.freezePanes.freezeRows(1);
  return s;
}
const withBody=tasks.some(t=>t.body_provenance);
const bodyColumns=t=>withBody?[t.body_provenance?.body_kind||'',t.body_provenance?.image_count??'',t.body_provenance?'DOM无用户正文；导出占位-':'']:[];
const detailRows=tasks.map(t=>[t.id,state.company,excelDate(t.review.date),t.review.store,t.review.customer,t.review.stars,
  t.review.text,t.review.product,t.analysis?.category||'',t.analysis?.suspected_bulk?'疑似批量，身份未确认':'',
  labels[t.status],t.analysis?.reason||t.block_reason||'',t.analysis?.draft||'',
  t.screenshot?.path||'',t.wecom?(state.mode==='fixture'||t.screenshot?.image_scope==='derived-dom-review-region'?'评价区域图：测试群客户端已显示':'历史整窗已显示；待区域图更正'):'未确认',
  t.result?resultLabels[t.result.status]:'未读取',t.result?.visible_text||'',clockDate(t.result?.observed_at),
  t.history?.count??'',t.history?.evidence.path||'',t.latest_snapshot.path,clockDate(t.updated_at),...bodyColumns(t)]);
const details=sheet('逐条处理结果',['评价编号','公司','评价日期','门店','顾客','星级','评价原文','商品','判断类型','批量线索','处理状态','判断依据或阻塞原因','投诉草稿','截图路径','企微核对发送','平台结果','结果原文','复查时间','历史参考条数','历史证据路径','页面证据路径','记录更新时间',...(withBody?['正文形态','评价图片数','正文来源']:[])],detailRows,[25,30,14,34,16,9,64,42,16,28,25,60,76,45,26,20,60,29,18,45,45,29,...(withBody?[24,12,40]:[])]);
if(tasks.length){
  details.getRangeByIndexes(1,2,tasks.length,1).setNumberFormat('yyyy-mm-dd');
  for(const c of [17,21])details.getRangeByIndexes(1,c,tasks.length,1).setNumberFormat('yyyy-mm-dd hh:mm:ss');
  for(const c of [6,7,11,12,16])details.getRangeByIndexes(1,c,tasks.length,1).format.wrapText=true;
  details.getRangeByIndexes(1,0,tasks.length,22).format.autofitRows();
  details.getRangeByIndexes(1,10,tasks.length,1).conditionalFormats.add('containsText',{text:'阻塞',format:{fill:'#FDE7E7',font:{color:'#9C2525'}}});
}
const judgments=tasks.flatMap(t=>Object.entries(t.analysis?.type_assessments||{}).map(([type,a])=>[
  t.id,t.review.store,type,a.match?'符合':'不符合',a.reason,
  (a.evidence||[]).flatMap(e=>(e.quotes||[]).map(q=>`${e.review_key}：${q}`)).join('\n'),
  t.analysis.category,t.analysis.platform_category||t.analysis.platform_category_evidence?.category_label||'',
  t.analysis.primary_selection_reason||'',t.analysis.classification_policy_version||'',
  t.analysis.evidence?.path||''
]));
const judgmentsSheet=sheet('分类判断依据',['评价编号','门店','判断类型','判断结果','逐项理由','原文证据','主选类型','平台选项','主选理由','校验版本','分析证据路径'],judgments,[28,34,18,14,65,75,18,18,55,25,60]);
if(judgments.length){judgmentsSheet.getRangeByIndexes(1,0,judgments.length,11).format.wrapText=true;judgmentsSheet.getRangeByIndexes(1,0,judgments.length,11).format.autofitRows();}
summary.getRange('A2:B2').values=[['差评投诉处理结果',state.mode==='fixture'?'模拟验收数据':'仅草稿，不提交']];
summary.getRange('A2:B2').format.font={name:'Arial',size:14,bold:true};
const summaryRows=[['公司',state.company],['记录时间（北京时间）',clockDate(state.updated_at)],['数据已覆盖至',state.covered_through?excelDate(state.covered_through):'尚未完成'],['下次起始日',excelDate(state.next_start)],['实际完成日',state.last_completed_on?excelDate(state.last_completed_on):'尚未完成'],['累计评价条数',tasks.length],...Object.entries(labels).map(([k,v])=>[v,tasks.filter(t=>t.status===k).length]),['平台提交功能','关闭'],['说明','草稿完成不等于平台投诉完成；未结案评价持续列入复查。']];
summary.getRangeByIndexes(3,0,summaryRows.length,2).values=summaryRows;
summary.getRangeByIndexes(3,0,summaryRows.length,2).format.font={name:'Arial',size:10};
summary.getRange('A1:A18').format.columnWidth=32;summary.getRange('B1:B18').format.columnWidth=90;
summary.getRange('A4:B17').format.rowHeight=28;
summary.getRange('B5').setNumberFormat('yyyy-mm-dd hh:mm:ss');
summary.getRange('B6:B8').setNumberFormat('yyyy-mm-dd');
const batchRows=Object.values(state.batches).map(b=>[excelDate(b.start),excelDate(b.end_exclusive),b.filtered_count,b.excluded_folded,b.closed_at?clockDate(b.closed_at):'未完成',b.snapshot.path]);
const batches=sheet('日期进度',['起始日（含）','截止日（不含）','平台筛选条数','输入排除折叠行数','草稿批次完成时间','页面证据路径'],batchRows,[19,19,18,18,32,80]);
if(batchRows.length){batches.getRangeByIndexes(1,0,batchRows.length,2).setNumberFormat('yyyy-mm-dd');batches.getRangeByIndexes(1,4,batchRows.length,1).setNumberFormat('yyyy-mm-dd hh:mm:ss');}
const actionLabels={'empty-backend-amended':'空账本采集连接迁移','empty-start-amended':'空账本补做起始日提前','initialized':'初始化待办日期','scope-captured':'核验平台筛选范围','screenshot':'登记评价截图','wecom-job-prepared':'登记核对发送任务','test-group-ui-confirmed':'测试群客户端已显示','wecom-stopped':'核对发送停点','other-history-reviewed':'查阅历史其他投诉','draft-ready-not-submitted':'草稿完成，未提交','platform-result-read':'读取平台投诉结果','blocked':'记录阻塞','draft-batch-completed':'完成本批草稿处理','operation-stopped':'操作停止'};
const eventRows=state.events.map(e=>{const t=e.record;return [clockDate(e.at),e.id||'',actionLabels[e.type]||e.type,t?labels[t.status]:'',t?.analysis?.category||'',t?.analysis?.reason||e.reason||'',t?.analysis?.draft||'',t?.result?resultLabels[t.result.status]:'',t?.result?.visible_text||'',t?.screenshot?.path||''];});
const events=sheet('处理记录',['记录时间','评价编号','动作','当时状态','判断类型','依据或停点','当时草稿','当时平台结果','结果原文','截图路径'],eventRows,[30,25,35,27,17,60,76,20,60,45]);
if(eventRows.length){events.getRangeByIndexes(1,0,eventRows.length,1).setNumberFormat('yyyy-mm-dd hh:mm:ss');events.getRangeByIndexes(1,5,eventRows.length,4).format.wrapText=true;events.getRangeByIndexes(1,0,eventRows.length,10).format.autofitRows();}
wb.recalculate();
// Bound inspection; no review text or personal information printed to stdout.
await wb.inspect({kind:'region',sheetId:'处理汇总',range:'A4:B17',maxChars:2000,tableMaxRows:14,tableMaxCols:2});
await fs.mkdir(path.dirname(output),{recursive:true});
const pending=output+'.pending.xlsx';
try{await (await SpreadsheetFile.exportXlsx(wb)).save(pending);await fs.rename(pending,output);}
finally{await fs.rm(pending,{force:true});}
if(previewDir){
  await fs.mkdir(previewDir,{recursive:true});
  const previews=previewScope==='classification-only'?[['分类判断依据',`C1:H${Math.min(judgments.length+1,6)}`]]:[['处理汇总','A2:B17'],['逐条处理结果',`A1:K${Math.min(tasks.length+1,5)}`],['日期进度',`A1:F${Math.min(batchRows.length+1,5)}`],['处理记录',`A1:E${Math.min(eventRows.length+1,5)}`]];
  for(const [name,range] of previews){
    const image=await wb.render({sheetName:name,range,scale:1.25,format:'png'});
    await fs.writeFile(path.join(previewDir,name+'.png'),new Uint8Array(await image.arrayBuffer()));
  }
}
console.log(JSON.stringify({path:output,rows:tasks.length,mode:state.mode,submission_enabled:false}));
