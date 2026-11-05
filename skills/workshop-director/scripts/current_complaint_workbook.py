"""Business workbook from this company's explicitly collected review keys only."""
from pathlib import Path
import hashlib,json
from datetime import date,timedelta
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from collection_ready import need,ref

def write(company,state,ledger,folder):
 keys=list(dict.fromkeys(key for unit in state['artifacts']['completed_units']for key in unit.get('keys',[])))
 rows=[];statuses={'draft_ready':'草稿已生成（未提交）','existing_pending':'已复查，平台审核中','resolved':'已复查，结果已记录'}
 for key in keys:
  task=ledger['tasks'][key];review=task['review'];analysis=task.get('analysis')or{};result=task.get('result')or{}
  need(task['status']in statuses,'current-workbook-unprocessed-review')
  rows.append([review['date'],review['store'],review['customer'],review['stars'],review['text'],statuses[task['status']],analysis.get('category',''),analysis.get('reason',''),analysis.get('draft',''),result.get('platform_status')or result.get('status',''),result.get('visible_text','')])
 last=(date.fromisoformat(company['end_exclusive'])-timedelta(days=1)).isoformat()
 summary=[['公司',company['company']],['本期处理范围',company['start']+' ～ '+last],['本期中差评条数',len(keys)],['处理说明','仅生成草稿或复查已有平台结果，未提交新投诉']]
 header=['评价日期','门店','顾客','星级','评价内容','处理状态','判断类型','判断依据','投诉草稿（未提交）','平台结果','平台可见结果原文']
 data={'summary':summary,'headers':header,'rows':rows};digest=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 folder=Path(folder)/digest[:16];folder.mkdir(parents=True,exist_ok=True);path=folder/('本期差评处理结果_'+company['start']+'_'+last+'.xlsx')
 if not path.exists():
  book=Workbook();sheet=book.active;sheet.title='本期汇总'
  for row in summary:sheet.append(row)
  details=book.create_sheet('本期逐条结果');details.append(header)
  for row in rows:details.append(row)
  if not rows:sheet.append(['本期结论','本期中差评0条，核验完成。'])
  for sheet in book:
   sheet.freeze_panes='A2'
   for cell in sheet[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='243B53')
   for row in sheet:
    for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
   for column in sheet.columns:sheet.column_dimensions[column[0].column_letter].width=36
  details.column_dimensions['E'].width=60;details.column_dimensions['I'].width=60;book.save(path)
 # Verify the actual outgoing rows, not a ledger-wide export or its manifest.
 book=load_workbook(path,read_only=True,data_only=True);actual=[list(row)for row in book['本期逐条结果'].iter_rows(values_only=True)];book.close()
 expected=[[None if value==''else value for value in row]for row in rows]
 need(actual==[header]+expected,'current-workbook-business-rows-changed')
 return ref(path),digest

def delivery_order(native,company,state,ledger):
 file,digest=write(company,state,ledger,Path(native['file']).parent/'current-period')
 return {**native,'key':native['key']+':period:'+digest[:12],'file':file['path'],'file_sha256':file['sha256']}
