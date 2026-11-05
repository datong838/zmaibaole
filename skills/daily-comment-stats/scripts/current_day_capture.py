"""Capture one exact day from the current original task; no export or history scan."""
import fcntl,json,os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/douyin-laike-operator/scripts')]
import bridge
from dom_evidence import nodes,identity,context,review_filter_fields,calendar_day,verified_review_filter,all_store_scope
from readonly_tick_snapshot import decode
TASK='task-bf6cef9c81d1add49b37d998'
DIRECTORY=ROOT/'runtime/standalone-workshop-director'
STATE=DIRECTORY/'current-day-capture.json'
def write(value):
 p=STATE.with_suffix('.tmp')
 with p.open('w') as f:json.dump(value,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
 p.replace(STATE)
def select_day(tree,day):
 try:return calendar_day(tree,day)
 except ValueError as error:
  if str(error)!='calendar-day-or-month-unverified':raise
 # The picker displays adjacent-month days. Resolve their absolute month
 # from the visible panel title and the explicit grid-next/grid-prev class.
 import re
 year,month,number=map(int,day.split('-'));wanted=year*12+month-1;found=[]
 def visit(n,parents):
  classes=set(n.get('attributes',{}).get('class','').split())
  if n.get('name')==str(number) and not n.get('children'):
   col=next((x for x in reversed(parents+[n]) if {'byted-date-col','byted-date-date'}<=set(x.get('attributes',{}).get('class','').split())),None)
   if col and not col.get('disabled'):
    cellclasses=classes|set(col.get('attributes',{}).get('class','').split())
    if 'disabled' not in ' '.join(cellclasses):
     offset=1 if 'byted-date-grid-next'in cellclasses else -1 if 'byted-date-grid-prev'in cellclasses else 0
     if offset:
      for parent in reversed(parents):
       matches=re.findall(r'(\d{4})年(\d{1,2})月',parent.get('name',''))
       if matches:
        if len(matches)==1 and int(matches[0][0])*12+int(matches[0][1])-1+offset==wanted:found.append(n)
        break
  for child in n.get('children',[]):visit(child,parents+[n])
 visit(tree['root'],[])
 if len(found)!=1:raise ValueError('adjacent-calendar-day-ambiguous')
 return found[0]
def step(day):
 from datetime import date
 with sqlite3.connect('file:'+str(DIRECTORY/'queue.sqlite3')+'?mode=ro',uri=True) as db:
  row=db.execute('select day,state,context from tasks where id=?',(TASK,)).fetchone()
  assert row and row[0]=='2026-11-03' and row[1]=='failed','original-task-not-quiescent'
  assert db.execute("select count(*) from tasks where state in ('running','dispatching','unknown')").fetchone()[0]==0,'worker-active'
 job=json.loads(Path(json.loads(row[2])['operator']['work_order']['path']).read_bytes())
 assert date.fromisoformat(job['date_range']['start'])<=date.fromisoformat(day)<=date.fromisoformat(job['date_range']['end']),'outside-original-range'
 current=json.loads(STATE.read_bytes()) if STATE.exists() else {'task':TASK,'day':day,'step':'open','status':'ready'}
 assert current['task']==TASK,'current-capture-owner-conflict'
 assert current['status']!='unknown','current-click-unknown-no-replay'
 captures=current.setdefault('captures',{})
 if current['status']=='captured':
  captures.setdefault(current['day'],{'scope':current['scope'],'filtered':current['filtered']})
 if day in captures:
  write(current);print(json.dumps({'day':day,'status':'already-captured'}));return
 if current['day']!=day:
  assert current['status']=='captured','current-day-incomplete'
  current={'task':TASK,'day':day,'step':'open','status':'ready','captures':captures}
  write(current)
 journal=json.loads(Path(job['workflow_path']).read_bytes())
 tab=journal['tab_id'];tabs=bridge.request({'op':'tabs'});assert tabs.get('ok'),'tabs-failed'
 windows=[w for w in tabs['result'] if any(t.get('tabId')==tab for t in w.get('tabs',[]))];assert len(windows)==1,'window-ambiguous';window=windows[0]['windowId']
 raw=bridge.request({'op':'readonly-scope','tabId':tab,'windowId':window});assert raw.get('ok'),'scope-failed';v=decode(raw['result'],tab,window)
 for side in ('before','after'):context(v[side],tab,str(job['groupid']))
 tree=v['tree'];identity(tree,job['identity_baseline']);all_store_scope(tree)
 stage=current['step'];target=None
 if stage=='open':target=review_filter_fields(tree)['评价时间'];next_stage='start'
 elif stage=='start':target=select_day(tree,day);next_stage='end'
 elif stage=='end':target=select_day(tree,day);next_stage='dismiss'
 elif stage=='dismiss':
  choices=[n for n in nodes(tree) if n.get('name')=='评价管理' and n.get('selector')=='#root > div > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1)'];assert len(choices)==1,'dismiss-target-ambiguous';target=choices[0];next_stage='read'
 elif stage=='read':
  result=verified_review_filter(tree,{'start':day,'end':day})
  captures[day]={'scope':raw,'filtered':result['page_filtered']}
  current.update(status='captured',scope=raw,filtered=result['page_filtered']);write(current);print(json.dumps({'day':day,'status':'captured','filtered':result['page_filtered']}));return
 else:raise ValueError('unknown-stage')
 command={'op':'click','tabId':tab,'kind':'navigation' if stage=='dismiss' else 'filter','locator':{'by':'selector','value':target['selector']}}
 current.update(status='unknown',command=command);write(current)
 reply=bridge.request(command)
 if not reply.get('ok'):raise ValueError('click-outcome-unknown-no-replay')
 current.update(status='ready',step=next_stage,reply=reply);write(current);print(json.dumps({'day':day,'next_step':next_stage}))
if __name__=='__main__':
 import contextlib
 with contextlib.ExitStack() as stack:
  for name in ('runtime/workshop-director/browser-wecom.resource.lock','runtime/standalone-workshop-director/scheduler.lock','runtime/workshop-director/.lock'):
   f=stack.enter_context((ROOT/name).open('a'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  step(sys.argv[1])
