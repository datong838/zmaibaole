/* Same immutable data builds XLSX + every row of both table images. No browser. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const [input,outdir]=process.argv.slice(2);if(!input||!outdir)throw Error('usage: build-report.mjs build-input.json outdir');
const data=JSON.parse(await fs.readFile(input,'utf8'));
if(!data.total)throw Error('zero-no-report');
if(data.records.length!==data.total||data.analysis.reduce((n,r)=>n+r.count,0)!==data.total)throw Error('report-count-mismatch');
const literal=v=>typeof v==='string'&&v!=='-'&&/^[=+@-]/.test(v)?"'"+v:v;
// Remaining duration is a raw observation, not the stable customer status.
function rectificationLabel(value){const match=typeof value==='string'&&/^待整改 ((?:0|[1-9][0-9]*))天((?:[01][0-9]|2[0-3])):([0-5][0-9]):([0-5][0-9])$/.exec(value);return match&&match[0]===value?'待整改':value;}
const excelDate=v=>new Date(v+'T00:00:00Z');
const dateEnd=new Date(Date.parse(data.end_exclusive+'T00:00:00Z')-86400000).toISOString().slice(0,10);
const summaryHeaders=['起始日期（含）','结束日期（含）','违规类型','违规对象类型','总数'];
const summaryRows=data.analysis.map(r=>[excelDate(data.start),excelDate(dateEnd),r.violation_type,r.object_types.join('、'),r.count]);
const hasStages=data.records.some(r=>r.disposal_stage_text);
const detailHeaders=['违规日期','处置主体（门店/公司原名）','违规原因','违规对象','处置方式','生效状态','整改状态','通知书ID',...(hasStages?['处置分项状态']:[])];
const detailRows=data.records.map(r=>[excelDate(r.date),r.subject,r.reason,r.object_name,r.table_disposal||r.actions.join('；'),r.table_effectiveness_status||r.effectiveness_status,rectificationLabel(r.rectification_status),r.notice_id,...(hasStages?[r.disposal_stage_text||'']:[])]);
const detailWidths=[19,42,48,42,42,16,20,27,...(hasStages?[60]:[])];
const title=`${data.company} ${data.start}至${dateEnd}${data.mode==='fixture'?'（模拟验收）':''}`;
function fill(wb,name,headers,rows,widths){
  const sheet=wb.worksheets.add(name);sheet.showGridLines=false;
  sheet.getRange('A1').values=[[title]];sheet.getRange('A1').format.font={name:'Arial',size:12,bold:true};
  const n=rows.length+1,m=headers.length;
  sheet.getRangeByIndexes(2,0,n,m).values=[headers,...rows].map(row=>row.map(literal));
  const all=sheet.getRangeByIndexes(2,0,n,m);all.format.font={name:'Arial',size:11};all.format.wrapText=true;all.format.verticalAlignment='center';
  sheet.getRangeByIndexes(2,0,1,m).format={fill:'#25384D',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',rowHeight:36,wrapText:true};
  widths.forEach((w,i)=>sheet.getRangeByIndexes(0,i,n+3,1).format.columnWidth=w);
  const heights=[];
  rows.forEach((row,index)=>{
    let lines=1;
    for(let i=0;i<row.length;i++)if(typeof row[i]==='string'){
      if(row[i].length>4000)throw Error('oversize-text-needs-layout-review');
      const size=Math.max(4,Math.floor(widths[i]/2));
      lines=Math.max(lines,row[i].split('\n').reduce((sum,s)=>sum+Math.max(1,Math.ceil(s.length/size)),0));
    }
    const height=Math.max(42,lines*16+16);heights.push(height);
    sheet.getRangeByIndexes(index+3,0,1,m).format.rowHeight=height;
  });
  sheet.freezePanes.freezeRows(3);
  const idColumn=headers.indexOf('通知书ID');
  if(idColumn>=0&&rows.length)sheet.getRangeByIndexes(3,idColumn,rows.length,1).setNumberFormat('@');
  return {sheet,heights};
}
const wb=Workbook.create();
const summary=fill(wb,'违规类型汇总',summaryHeaders,summaryRows,[20,20,40,32,12]);
summary.sheet.getRangeByIndexes(3,0,summaryRows.length,2).setNumberFormat('yyyy-mm-dd');
const totalRow=summaryRows.length+4;
summary.sheet.getRange('D'+totalRow).values=[['合计']];
summary.sheet.getRange('E'+totalRow).formulas=[['=SUM(E4:E'+(totalRow-1)+')']];
const detail=fill(wb,'违规记录表',detailHeaders,detailRows,detailWidths);
detail.sheet.getRangeByIndexes(3,0,detailRows.length,1).setNumberFormat('yyyy-mm-dd');
wb.recalculate();
await wb.inspect({kind:'region',sheetId:'违规类型汇总',range:'D'+totalRow+':E'+totalRow,maxChars:500,tableMaxRows:1,tableMaxCols:2});
if(summary.sheet.getRange('E'+totalRow).values[0][0]!==data.total)throw Error('xlsx-total-formula-mismatch');
await fs.mkdir(outdir,{recursive:true});
const files=[];
async function add(kind,file,coverage){const bytes=await fs.readFile(file);files.push({kind,path:path.resolve(file),sha256:crypto.createHash('sha256').update(bytes).digest('hex'),...coverage});}
const xlsx=path.join(outdir,'违规汇总.xlsx');const pending=xlsx+'.pending.xlsx';
try{await(await SpreadsheetFile.exportXlsx(wb)).save(pending);await fs.rename(pending,xlsx);}finally{await fs.rm(pending,{force:true});}
await add('workbook',xlsx);
// For large tables, repeat the headers on complete-row image pages. Never shrink/crop rows.
for(const [kind,name,headers,rows,widths,heights,dateCols] of [
  ['analysis_image','违规类型汇总',summaryHeaders,summaryRows,[20,20,40,32,12],summary.heights,2],
  ['records_image','违规记录表',detailHeaders,detailRows,detailWidths,detail.heights,1]
]){
  let start=0,page=1;
  while(start<rows.length){
    let end=start,pixels=0;
    while(end<rows.length&&(pixels+heights[end]<=1000||end===start)){pixels+=heights[end];end++;}
    const imageBook=Workbook.create();
    // Explicit visible label prevents the renderer from coercing an 18-digit string
    // to a number. The exported workbook retains the exact original ID.
    const imageRows=rows.slice(start,end).map(row=>row.map((value,i)=>headers[i]==='通知书ID'?'ID：'+value:value));
    const view=fill(imageBook,name,headers,imageRows,widths);
    view.sheet.getRangeByIndexes(3,0,end-start,dateCols).setNumberFormat('yyyy-mm-dd');
    let finalRow=end-start+3;
    if(kind==='analysis_image'&&end===rows.length){finalRow++;view.sheet.getRange('D'+finalRow).values=[['合计']];view.sheet.getRange('E'+finalRow).values=[[data.total]];}
    const range='A1:'+String.fromCharCode(64+headers.length)+finalRow;
    const image=await imageBook.render({sheetName:name,range,scale:1.25,format:'png'});
    const file=path.join(outdir,name+'-完整表格-'+String(page).padStart(2,'0')+'.png');
    await fs.writeFile(file,new Uint8Array(await image.arrayBuffer()));
    await add(kind,file,{first_row:start+1,last_row:end,row_count:end-start,total_rows:rows.length,headers_repeated:true});
    start=end;page++;
  }
}
await fs.writeFile(path.join(outdir,'artifacts.json'),JSON.stringify({version:1,source_sha256:data.source.sha256,files},null,2));
console.log(JSON.stringify({ok:true,files:files.length,records:data.total,mode:data.mode}));
