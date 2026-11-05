#!/usr/bin/env python3
"""Portable append-only public history entry observations, never appeal cases/UI."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,fcntl,hashlib,json,os,re
from datetime import datetime,date
from pathlib import Path
from urllib.parse import urlsplit
import case_memory as memory_api
DOMAIN=memory_api.KIND
KIND='negative-review-appeal-history-coverage-observation-v1'
AUDIT='public-appeal-history-entry-scope-audit-v1'
FILES=('source-tree.json','review-settled-tree.json','toolbox-open-reply.json','toolbox-hover-reply.json','toolbox-hover-tree.json','all-rating-reply.json','all-rating-tree.json','status-options-open-reply.json','status-options-tree.json')
def _load_known():
 path = Path(os.environ.get('ZMAIBAOLE_APPEAL_IDENTITIES', str(Path(__file__).resolve().parents[1] / 'config/appeal-history-identities.json')))
 if not path.exists(): return {}
 data = json.loads(path.read_text(encoding='utf-8'))
 if not isinstance(data, dict): raise ValueError('appeal-history-identity-config-invalid')
 result = {}
 for gid, value in data.items():
  if not str(gid).isdigit() or not isinstance(value, list) or len(value) != 4 or not all(isinstance(x, str) and x.strip() for x in value): raise ValueError('appeal-history-identity-config-invalid')
  result[str(gid)] = tuple(value)
 return result
KNOWN=_load_known()
HINT='已归档案例数不是全月总量；评价时间不是投诉时间，评价状态是可见性；已查菜单未见独立申诉历史入口，成功移除/隐藏及更早评价的本月申诉尚未证明覆盖。'
def need(ok,reason):memory_api.need(ok,'appeal-coverage-'+reason)
def nodes(n):
 yield n
 for child in n.get('children',[]):yield from nodes(child)
def facts(audit,docs):
 need(audit.get('kind')==AUDIT and audit.get('domain')==DOMAIN,'domain-kind')
 gid=str(audit.get('groupid'));need(gid in KNOWN and audit.get('company')==KNOWN[gid][0],'company-binding')
 need(set(audit.get('evidence',{}))==set(FILES) and set(docs)==set(FILES),'nine-evidence-required')
 need(type(audit.get('tab_id')) is int and type(audit.get('window_id')) is int,'tab-window-required')
 for flag in ('independent_complaint_history_entry_observed','complaint_date_query_observed','complaint_success_retention_proved','complete_company_month_history_proved','case_memory_changed','business_cursor_changed'):
  need(audit.get(flag) is False,'unproved-completeness-or-mutation')
 need(audit.get('company_all_history_proven',False) is False and audit.get('case_count_is_company_total',False) is False,'unproved-completeness-or-total')
 need(audit.get('new_case_originals_read')==0 and audit.get('normal_review_history_is_not_all_appeal_history') is True and audit.get('unread_or_removed_history_count') is None,'case-count-is-not-total')
 date.fromisoformat(audit['requested_range']['start']);date.fromisoformat(audit['requested_range']['end_exclusive']);memory_api.timestamp(audit['observed_at'])
 need(audit['requested_range']['start']<audit['requested_range']['end_exclusive'],'range-invalid')
 trees={}
 for filename,raw in docs.items():
  need(raw.get('ok') is True and raw.get('error') is None,'source-not-confirmed')
  result=raw.get('result',{})
  if filename.endswith('tree.json'):
   u=urlsplit(result.get('url',''));expected='/p/governance/violation_list' if filename=='source-tree.json' else '/p/life_comment/management'
   need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path==expected and not u.query and not u.fragment and result.get('truncated') is False,'source-origin-or-completeness')
   ns=list(nodes(result['root']));heads=[n for n in ns if n.get('tag')=='header'];need(len(heads)==1 and all(x in heads[0].get('name','') for x in ('服务商7576493388812273702',KNOWN[gid][1],KNOWN[gid][2])),'source-identity')
   trees[filename]=ns
  else:
   action=result.get('hovered') if filename=='toolbox-hover-reply.json' else result.get('clicked');need(isinstance(action,dict) and action.get('disabled') is False,'action-receipt-required')
   if filename.startswith('toolbox-'):need(result.get('kind')=='navigation' and action.get('name')=='工具箱' and action.get('selector')=='#CommentToolView_select','toolbox-receipt')
   elif filename=='all-rating-reply.json':need(result.get('kind')=='navigation' and re.fullmatch(r'全部评价\s+[0-9]+',action.get('name','')),'review-navigation-receipt')
   else:need(result.get('kind')=='filter' and action.get('name')=='评价状态' and action.get('tag')=='input' and action.get('attributes',{}).get('value')=='全部','status-open-receipt')
 tools=[n['name'] for n in trees['toolbox-hover-tree.json'] if n.get('attributes',{}).get('class')=='title-OGQFa1' and not n.get('children')]
 need(tools==['报名免费试','下载到店码','评价规则']==audit.get('toolbox_items'),'toolbox-items-changed')
 final=trees['status-options-tree.json'];opts=[n for n in final if n.get('attributes',{}).get('class')=='byted-list-item-inner-wrapper byted-select-option-inner-wrapper' and not n.get('children')]
 need([n['name'] for n in opts]==['全部','对顾客可见','对顾客折叠'] and [{'text':n['name'],'selector':n['selector']} for n in opts]==audit.get('evaluation_status_options'),'status-is-visibility')
 dates=[n for n in final if n.get('tag')=='input' and n.get('name')=='评价时间'];need(len(dates)==1 and audit.get('date_field',{}).get('text')=='评价时间' and audit['date_field'].get('selector')==dates[0]['selector'],'review-time-not-complaint-time')
 need('Shanghai equivalent public entry not yet inspected' in audit.get('missing_capabilities',[]),'unchecked-company-required')
 return {'company':audit['company'],'groupid':gid,'observed_at':audit['observed_at'],'requested_range':audit['requested_range'],'date_field':'review_time','status_field':'customer_visibility','menus_checked':audit['searched_public_locations'],'independent_history_entry_observed':False,'company_all_history_proven':False,'case_count_is_company_total':False,'unchecked_companies':['上海老芗汇餐饮管理有限公司'],'limitations':audit['missing_capabilities'],'hint':HINT}
def _read_unlocked(memory):
 root=Path(memory).resolve();p=root/'history-coverage.jsonl'
 if not p.exists():return []
 need(not p.is_symlink(),'log-symlink');raw=p.read_bytes();need(not raw or raw.endswith(b'\n'),'damaged-tail');out=[];seen=set()
 for line in raw.splitlines():
  r=json.loads(line);need(r.get('kind')==KIND and r.get('domain')==DOMAIN,'domain-kind');audit=memory_api._local(root,r['audit_ref']);docs={k:memory_api._local(root,v) for k,v in r['evidence_refs'].items()}
  need(all(r['evidence_refs'][k]['sha256']==audit['evidence'][k]['sha256'] for k in FILES),'source-ref-mismatch');f=facts(audit,docs)
  need(all(r.get(k)==v for k,v in f.items()) and r['observation_id']==r['audit_ref']['sha256'] and r['observation_id'] not in seen,'record-facts-changed');seen.add(r['observation_id']);out.append(r)
 return out
def read_records(memory=memory_api.DEFAULT_MEMORY):
 root=Path(memory).resolve();lock=root/'.coverage.append.lock'
 if not lock.exists():return _read_unlocked(root)
 need(not lock.is_symlink(),'lock-symlink')
 with lock.open('rb') as handle:
  fcntl.flock(handle,fcntl.LOCK_SH);return _read_unlocked(root)

def import_audit(path,sha256,*,memory=memory_api.DEFAULT_MEMORY):
 root=Path(memory).resolve();audit_ref={'path':str(Path(path).resolve()),'sha256':sha256};raw=memory_api._raw_ref(audit_ref);audit=json.loads(raw);need(audit.get('kind')==AUDIT and audit.get('domain')==DOMAIN,'domain-kind');need(set(audit.get('evidence',{}))==set(FILES),'nine-evidence-required')
 payloads={k:memory_api._raw_ref(v) for k,v in audit['evidence'].items()};f=facts(audit,{k:json.loads(v) for k,v in payloads.items()})
 root.mkdir(parents=True,exist_ok=True);lock=root/'.coverage.append.lock';need(not lock.is_symlink(),'lock-symlink')
 with lock.open('a+b') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX);prior=_read_unlocked(root)
  if any(r['observation_id']==sha256 for r in prior):return {'appended':False,'observation_id':sha256}
  owned={}
  for key,data in {'audit':raw,**payloads}.items():
   sha=memory_api.sha(data);p=root/'evidence'/(sha+'.json');p.parent.mkdir(exist_ok=True);memory_api._write_exclusive(p,data);owned[key]={'path':'evidence/'+sha+'.json','sha256':sha}
  record={'kind':KIND,'domain':DOMAIN,'schema_version':1,'observation_id':sha256,**f,'audit_ref':owned.pop('audit'),'evidence_refs':owned,'original_audit_ref':audit_ref,'imported_at':datetime.now(memory_api.ZONE).isoformat()}
  log=root/'history-coverage.jsonl';need(not log.is_symlink(),'log-symlink')
  try:fd=os.open(log,os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_EXCL,0o600)
  except FileExistsError:fd=os.open(log,os.O_WRONLY|os.O_APPEND)
  with os.fdopen(fd,'ab') as out:out.write(memory_api.canonical(record)+b'\n');out.flush();os.fsync(out.fileno())
  directory=os.open(root,os.O_RDONLY)
  try:os.fsync(directory)
  finally:os.close(directory)
  return {'appended':True,'record':record}
def summary(*,memory=memory_api.DEFAULT_MEMORY,company=None,groupid=None,as_of=None):
 cutoff=as_of or datetime.now(memory_api.ZONE)
 need(isinstance(cutoff,date),'as-of-invalid')
 def available(r):
  at=memory_api.timestamp(r['observed_at'])
  if isinstance(cutoff,datetime):
   point=cutoff.replace(tzinfo=memory_api.ZONE) if cutoff.tzinfo is None else cutoff.astimezone(memory_api.ZONE)
   return at<=point
  return at.date()<=cutoff
 rows=[r for r in read_records(memory) if available(r)]
 if company is not None:rows=[r for r in rows if (r['company']==company and r['groupid']==str(groupid)) or company in r['unchecked_companies']]
 return {'domain':DOMAIN,'kind':'appeal-history-coverage-summary-v1','scope_audit_count':len(rows),'company_all_history_proven':False,'case_count_is_company_total':False,'hint':HINT,'audits':[{k:r[k] for k in ('company','groupid','observed_at','date_field','status_field','unchecked_companies','audit_ref')} for r in rows]}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--memory',default=str(memory_api.DEFAULT_MEMORY));ap.add_argument('--document');a=ap.parse_args();result=import_audit(a.audit,a.sha256,memory=a.memory)
 if a.document and result['appended']:result['document']=memory_api.render_document(a.document,memory=a.memory)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
