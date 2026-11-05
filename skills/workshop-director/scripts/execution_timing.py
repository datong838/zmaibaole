#!/usr/bin/env python3
"""Standalone end-to-end telemetry; never executes, cancels or replays work.
Acceptance: fresh start before the first web action through every expected
client-confirmed send. Development/resume/no-data are explicitly separate.
"""
import argparse,fcntl,hashlib,json,math,os,re,subprocess,sys,time,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
FLOWS=('daily-comment-stats','negative-review-complaints','violation-notifier')
SENDER_DIRECTORY=Path(__file__).resolve().parents[3]/'runtime/wecom-messenger'
DYNAMIC_DELIVERY='seal-once-before-first-sender-prepare-v1'
MONOTONIC_CLOCK='system-clock-gettime-CLOCK_MONOTONIC-v1'
TARGET='测试群请忽略';KIND='workflow-execution-timing-v1';LIMIT=30.0
class TimingError(ValueError):pass
def need(ok,reason):
 if not ok:raise TimingError(reason)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def finite(n):return type(n) in (int,float) and math.isfinite(n) and n>=0
def ref(path):
 p=Path(path).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def pinned(r):
 need(type(r) is dict and set(r)=={'path','sha256'} and isinstance(r['path'],str) and Path(r['path']).is_absolute() and re.fullmatch('[0-9a-f]{64}',str(r['sha256'])),'timing-pinned-reference-required')
 p=Path(r['path']);need(p.is_file() and not p.is_symlink(),'timing-evidence-unavailable');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==r['sha256'],'timing-evidence-changed');return json.loads(raw)
def sender_path(key):
 # Same filename rule as WeCom prepare; no messenger import or UI initialization.
 return SENDER_DIRECTORY.resolve()/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json')

def boot_identity():
 if sys.platform=='darwin':
  # kern.boottime is wall-clock-derived and can drift under NTP adjustment.
  # The public boot-session UUID remains stable throughout one kernel session.
  raw=subprocess.run(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],capture_output=True,text=True,check=True,timeout=5).stdout.strip()
  need(re.fullmatch(r'[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}',raw) is not None,'timing-boot-identity-unavailable')
  value=uuid.UUID(raw);need(value.int!=0,'timing-boot-identity-unavailable')
  return 'darwin-kern-bootsessionuuid:'+str(value)
 p=Path('/proc/sys/kernel/random/boot_id');need(p.is_file(),'timing-boot-identity-unavailable');return 'linux-boot-id:'+str(uuid.UUID(p.read_text().strip()))
class Clock:
 def monotonic(self):
  # Python 3.9/macOS time.monotonic has a per-process reference origin. Use
  # the public system CLOCK_MONOTONIC shared by successive CLI processes.
  need(hasattr(time,'clock_gettime') and hasattr(time,'CLOCK_MONOTONIC'),'timing-system-monotonic-unavailable');return time.clock_gettime(time.CLOCK_MONOTONIC)
 def wall(self):return datetime.now(timezone.utc)
 def boot(self):return boot_identity()
def stamp(clock):return clock.wall().isoformat()
def parse_time(s):
 try:t=datetime.fromisoformat(s)
 except (TypeError,ValueError):raise TimingError('timing-aware-timestamp-required')
 need(t.utcoffset() is not None,'timing-aware-timestamp-required');return t
def company_ranges(scope):
 # Derived view only: never rewrite legacy scope bytes or its SHA.
 if 'company_ranges' in scope:return scope['company_ranges']
 return [{**x,'start':scope['start'],'end_exclusive':scope['end_exclusive']} for x in scope['companies']]
def scope_check(scope):
 common={'workflow','companies','start','end_exclusive','test_target'}
 ranged={'workflow','company_ranges','test_target','delivery_contract'}
 need(type(scope) is dict and (set(scope)==common|{'expected_send_keys'} or set(scope)==common|{'delivery_contract'} and scope['delivery_contract']==DYNAMIC_DELIVERY or set(scope)==ranged and scope['delivery_contract']==DYNAMIC_DELIVERY),'timing-scope-schema-invalid')
 need(scope['workflow'] in FLOWS and scope['test_target']==TARGET,'timing-flow-or-test-target-invalid')
 companies=scope.get('company_ranges',scope.get('companies'));fields={'company','groupid','start','end_exclusive'} if 'company_ranges' in scope else {'company','groupid'}
 need(isinstance(companies,list) and companies and all(type(x) is dict and set(x)==fields and isinstance(x['company'],str) and x['company'] and re.fullmatch('[0-9]+',str(x['groupid'])) for x in companies),'timing-company-scope-invalid')
 need(len({str(x['groupid']) for x in companies})==len(companies) and len({x['company'] for x in companies})==len(companies),'timing-company-duplicate')
 from datetime import date
 for x in company_ranges(scope):
  try:need(date.fromisoformat(x['start'])<date.fromisoformat(x['end_exclusive']),'timing-date-range-invalid')
  except (TypeError,ValueError):raise TimingError('timing-date-range-invalid')
 if 'expected_send_keys' in scope:
  keys=scope['expected_send_keys'];need(isinstance(keys,list) and all(type(k) is str and k for k in keys) and len(keys)==len(set(keys)),'timing-expected-send-keys-invalid')
 return scope
@contextmanager
def locked(path):
 path=Path(path).resolve();path.parent.mkdir(parents=True,exist_ok=True)
 with path.with_name(path.name+'.lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);yield path
  fcntl.flock(f,fcntl.LOCK_UN)
def save(path,state):
 tmp=path.with_name(path.name+'.tmp')
 with tmp.open('w') as f:json.dump(state,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def load(path,clock):
 s=json.loads(path.read_text());need(s.get('kind')==KIND,'timing-original-run-required');need(s.get('monotonic_clock')==MONOTONIC_CLOCK,'timing-monotonic-clock-contract-missing');pinned(s['work_order']);scope_check(s['scope']);need(digest(s['scope'])==s['scope_sha256'],'timing-scope-changed');need(clock.boot()==s['boot_identity'],'timing-monotonic-boot-changed');need(finite(s['start_monotonic']) and finite(clock.monotonic()) and clock.monotonic()>=s['start_monotonic'],'timing-monotonic-invalid')
 if s['scope'].get('delivery_contract')==DYNAMIC_DELIVERY:
  delivery=s.get('delivery',{});need(delivery.get('contract')==DYNAMIC_DELIVERY and delivery.get('status') in ('unsealed','sealed'),'timing-dynamic-delivery-state-invalid')
  if delivery['status']=='sealed':
   orders=delivery_orders(delivery['manifest'],s);need(orders==delivery['orders'] and delivery['keys']==[o['key'] for o in orders] and delivery['manifest_sha256']==delivery['manifest']['sha256'],'timing-sealed-delivery-changed')
 return s
def running(s):need(s['status']=='running','timing-run-already-ended')
def view(s,clock):
 end=s.get('end_monotonic',clock.monotonic());elapsed=end-s['start_monotonic']
 return {'run_id':s['run_id'],'workflow':s['scope']['workflow'],'mode':s['mode'],'origin':s['origin'],'status':s['status'],'outcome':s.get('outcome'),'wall_started_at':s['wall_started_at'],'wall_ended_at':s.get('wall_ended_at'),'elapsed_seconds':elapsed,'deadline_seconds':LIMIT,'deadline_exceeded':elapsed>LIMIT,'full_workflow_measured':s.get('full_workflow_measured',False),'acceptance_pass':bool(s.get('acceptance_pass',False)),'end_boundary':s['end_boundary'],'startup_prechecks_included':s['startup_prechecks_included'],'final_timing_ledger_write_in_elapsed':s['final_timing_ledger_write_in_elapsed'],'stage_durations_are_additive':False,'delivery_sealed':s.get('delivery',{}).get('status')=='sealed' if 'delivery' in s else 'expected_send_keys' in s['scope'],'measurement_only_no_cancel_or_replay':True}
def _start(path,run_id,work_order,scope,*,mode='development',origin='fresh',resumed_from=None,clock=None,_entry):
 clock=clock or Clock();entry_monotonic,entry_wall,entry_boot=_entry;need(isinstance(run_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,100}',run_id),'timing-run-id-invalid');need(mode in ('development','acceptance') and origin in ('fresh','resume'),'timing-mode-invalid');scope_check(scope);pinned(work_order)
 need((origin=='resume')==(resumed_from is not None),'timing-resume-reference-required')
 if resumed_from:pinned(resumed_from)
 with locked(path) as p:
  if p.exists():
   s=load(p,clock);need(all(s[k]==v for k,v in {'run_id':run_id,'work_order':work_order,'scope':scope,'mode':mode,'origin':origin,'resumed_from':resumed_from}.items()),'timing-existing-run-conflict');return view(s,clock)
  if origin=='fresh':
   need(all(not sender_path(key).exists() for key in scope.get('expected_send_keys',[])),'timing-fresh-send-job-preexists-use-resume')
  mono=entry_monotonic;need(finite(mono) and clock.boot()==entry_boot,'timing-monotonic-or-boot-invalid');s={'kind':KIND,'monotonic_clock':MONOTONIC_CLOCK,'run_id':run_id,'work_order':work_order,'scope':scope,'scope_sha256':digest(scope),'mode':mode,'origin':origin,'resumed_from':resumed_from,'boot_identity':entry_boot,'start_monotonic':mono,'wall_started_at':entry_wall.isoformat(),'start_boundary':'before-first-webpage-action' if origin=='fresh' else 'resume-reconciliation-start','end_boundary':'all-expected-client-confirmed-and-local-verification-complete-before-final-timing-ledger-write','startup_prechecks_included':True,'final_timing_ledger_write_in_elapsed':False,'status':'running','delivery':{'status':'sealed','contract':'legacy-fixed-keys-v1','keys':scope['expected_send_keys']} if 'expected_send_keys' in scope else {'status':'unsealed','contract':DYNAMIC_DELIVERY},'stages':[],'events':[],'acceptance_pass':False,'full_workflow_measured':False};save(p,s);return view(s,clock)
def start(path,run_id,work_order,scope,*,mode='development',origin='fresh',resumed_from=None,clock=None):
 clock=clock or Clock();entry=(clock.monotonic(),clock.wall(),clock.boot())
 return _start(path,run_id,work_order,scope,mode=mode,origin=origin,resumed_from=resumed_from,clock=clock,_entry=entry)
def start_from_order(path,run_id,work_order,validate_order,*,mode='development',clock=None):
 """Count immutable dispatch validation itself, before role planning/prechecks."""
 clock=clock or Clock();entry=(clock.monotonic(),clock.wall(),clock.boot());path=path() if callable(path) else path;order=validate_order(work_order)
 return _start(path,run_id,work_order,order['scope'],mode=mode,origin=order['origin'],resumed_from=order['resumed_from'],clock=clock,_entry=entry)
def file_reference(path):
 p=Path(path).absolute();need(p.is_file() and not p.is_symlink(),'timing-delivery-payload-unavailable');return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def checked_bytes(r):
 need(type(r) is dict and set(r)=={'path','sha256'} and Path(r['path']).is_absolute(),'timing-delivery-source-ref-invalid');p=Path(r['path']);need(p.is_file() and not p.is_symlink(),'timing-delivery-source-unavailable');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==r['sha256'],'timing-delivery-source-changed');return raw

def normalized_order(order,workflow):
 need(type(order) is dict,'timing-delivery-native-order-required')
 if workflow=='daily-comment-stats':
  args=order.get('prepare_argv');need(isinstance(args,list) and len(args)==13 and args[2]=='prepare' and all(isinstance(x,str) for x in args),'timing-delivery-daily-argv-invalid');pairs=list(zip(args[3::2],args[4::2]));options=dict(pairs);need(len(options)==len(pairs) and set(options) in ({'--key','--kind','--target','--scope','--file'},{'--key','--kind','--target','--scope','--text-file'}),'timing-delivery-daily-options-invalid');o={'key':options['--key'],'kind':options['--kind'],'target':options['--target'],'scope':options['--scope']};typ='file' if '--file' in options else 'text';payload=options.get('--file',options.get('--text-file'));need(order.get('payload')==payload,'timing-delivery-daily-payload-conflict');expected_sha=order.get('sha256')
 else:
  o={k:order.get(k) for k in ('key','kind','target','scope')};typ=order.get('type','file');payload=order.get('file') if typ=='file' else order.get('text_file');expected_sha=order.get('file_sha256') if typ=='file' else order.get('text_sha256')
 need(isinstance(o['key'],str) and o['key'] and o['kind']=='group' and o['target']==TARGET and o['scope']=='test' and typ in ('file','text') and isinstance(payload,str),'timing-delivery-order-scope-invalid');r=file_reference(payload);need(expected_sha is None or expected_sha==r['sha256'],'timing-delivery-native-payload-hash-conflict');o['type']=typ
 if typ=='file':o.update(file=str(Path(payload).absolute()),file_name=Path(payload).name,file_sha256=r['sha256'])
 else:o['text']=checked_bytes(r).decode('utf-8').replace('\r\n','\n').replace('\r','\n')
 return {'key':o['key'],'payload_ref':r,'sender_payload':o}

def delivery_orders(manifest_ref,s):
 m=pinned(manifest_ref);binding(m,s,'workflow-delivery-manifest-v1');fields={'kind','run_id','work_order','scope_sha256','source_refs','source_plans','expected_send_keys'}
 if 'company_ranges' in s['scope']:
  fields.add('company_ranges');need(m.get('company_ranges')==s['scope']['company_ranges'],'timing-delivery-company-ranges-conflict')
  if 'zero_acquisitions' in m:fields.add('zero_acquisitions')
 need(set(m)==fields,'timing-delivery-manifest-schema-invalid');sources=m['source_refs'];plans=m['source_plans'];need(isinstance(sources,list) and sources and isinstance(plans,list) and plans and len({r.get('path') for r in plans})==len(plans),'timing-delivery-source-plans-required')
 for r in sources:checked_bytes(r)
 orders=[];company_names=[];workflow=s['scope']['workflow'];zero_names=[]
 if 'zero_acquisitions' in m:
  need(workflow=='daily-comment-stats' and type(m['zero_acquisitions']) is list,'timing-mixed-zero-contract-invalid')
  for r in m['zero_acquisitions']:
   a=pinned(r);zero_acquisition(a,s);zero_names.append(a.get('company'))
  need(len(zero_names)==len(set(zero_names)),'timing-zero-company-coverage-invalid')
 for r in plans:
  plan=pinned(r)
  if workflow=='daily-comment-stats':
   need(isinstance(plan,dict) and plan.get('workflow')==workflow and plan.get('test_target')==TARGET,'timing-delivery-daily-plan-invalid');native=plan.get('orders');company_names.append(plan.get('company'))
   from datetime import date,timedelta
   matches=[x for x in company_ranges(s['scope']) if x['company']==plan.get('company')];need(len(matches)==1,'timing-delivery-daily-company-coverage-conflict');company=matches[0]
   dates=plan.get('date_range',{});need(type(dates) is dict and dates.get('start')==company['start'] and dates.get('end')==(date.fromisoformat(company['end_exclusive'])-timedelta(days=1)).isoformat() and ('end_exclusive' not in dates or dates['end_exclusive']==company['end_exclusive']),'timing-delivery-daily-range-conflict')
  else:native=plan if isinstance(plan,list) else [plan] if isinstance(plan,dict) and 'key' in plan else None
  need(isinstance(native,list) and native,'timing-delivery-complete-native-plan-required');orders.extend(normalized_order(o,workflow) for o in native)
 if workflow=='daily-comment-stats':need(sorted(company_names+zero_names)==sorted(x['company'] for x in company_ranges(s['scope'])),'timing-delivery-daily-company-coverage-conflict')
 keys=[o['key'] for o in orders];need(keys and len(keys)==len(set(keys)) and isinstance(m['expected_send_keys'],list) and len(m['expected_send_keys'])==len(set(m['expected_send_keys'])) and sorted(keys)==sorted(m['expected_send_keys']),'timing-delivery-complete-key-set-mismatch');need(len({str(sender_path(k)) for k in keys})==len(keys),'timing-delivery-canonical-key-collision');return orders

def seal_delivery(path,manifest_ref,*,clock=None):
 clock=clock or Clock()
 with locked(path) as p:
  s=load(p,clock);running(s);need(s['scope'].get('delivery_contract')==DYNAMIC_DELIVERY,'timing-delivery-legacy-keys-already-fixed')
  if s['delivery'].get('status')=='sealed':
   need(s['delivery']['manifest']==manifest_ref,'timing-delivery-already-sealed-conflict');return view(s,clock)
  need(s['delivery'].get('status')=='unsealed','timing-delivery-state-invalid');need(any(e['kind']=='first-webpage-action-intent' for e in s['events']) or s['origin']=='resume','timing-delivery-must-follow-acquisition-start');orders=delivery_orders(manifest_ref,s)
  # Current three workflows generate order descriptions before messenger.prepare.
  # Seal must be inserted there. Even an unsent pre-created canonical job is not
  # silently adopted into a fresh acceptance run; use explicit resume instead.
  if s['origin']=='fresh':need(all(not sender_path(o['key']).exists() for o in orders),'timing-fresh-delivery-job-preexists-use-resume')
  s['delivery']={'contract':DYNAMIC_DELIVERY,'status':'sealed','manifest':manifest_ref,'manifest_sha256':manifest_ref['sha256'],'orders':orders,'keys':[o['key'] for o in orders],'sealed_at':stamp(clock),'sealed_monotonic':clock.monotonic(),'fresh_canonical_absence_checked':s['origin']=='fresh'};s['events'].append({'kind':'delivery-manifest-sealed','monotonic':clock.monotonic(),'at':stamp(clock),'manifest_sha256':manifest_ref['sha256']});save(p,s);return view(s,clock)

def expected_keys(s):
 if s['scope'].get('delivery_contract')==DYNAMIC_DELIVERY:
  need(s.get('delivery',{}).get('status')=='sealed','timing-delivery-manifest-unsealed');return s['delivery']['keys']
 return s['scope']['expected_send_keys']

def mark_web_action(path,*,clock=None):
 clock=clock or Clock()
 with locked(path) as p:
  s=load(p,clock);running(s);need(not any(e['kind']=='first-webpage-action-intent' for e in s['events']),'timing-first-web-action-already-recorded');s['events'].append({'kind':'first-webpage-action-intent','monotonic':clock.monotonic(),'at':stamp(clock)});save(p,s);return view(s,clock)
def stage(path,stage_id,phase,*,end=False,clock=None):
 clock=clock or Clock();need(isinstance(stage_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,100}',stage_id),'timing-stage-id-invalid');need(phase in ('webpage-acquisition','artifact-generation','test-group-send','client-confirmation'),'timing-stage-phase-invalid')
 with locked(path) as p:
  s=load(p,clock);running(s);found=[x for x in s['stages'] if x['id']==stage_id]
  if end:
   need(len(found)==1 and found[0]['phase']==phase and 'end_monotonic' not in found[0],'timing-stage-end-invalid');found[0].update(end_monotonic=clock.monotonic(),ended_at=stamp(clock),elapsed_seconds=clock.monotonic()-found[0]['start_monotonic'])
  else:
   need(not found,'timing-stage-already-started');s['stages'].append({'id':stage_id,'phase':phase,'start_monotonic':clock.monotonic(),'started_at':stamp(clock)})
  save(p,s);return view(s,clock)
def binding(receipt,s,kind):
 need(receipt.get('kind')==kind and receipt.get('run_id')==s['run_id'] and receipt.get('work_order')==s['work_order'] and receipt.get('scope_sha256')==s['scope_sha256'],'timing-completion-binding-invalid')
def clients(receipt,s,clock):
 binding(receipt,s,'workflow-client-confirmation-v1');keys=expected_keys(s)
 if s['scope'].get('delivery_contract')==DYNAMIC_DELIVERY:need(receipt.get('delivery_manifest_sha256')==s['delivery']['manifest_sha256'],'timing-completion-delivery-hash-mismatch')
 refs=receipt.get('client_jobs');need(isinstance(refs,list) and refs and len({r.get('path') for r in refs})==len(refs),'timing-all-client-jobs-required');actual=[];earliest=parse_time(s['wall_started_at']).replace(microsecond=0)
 for r in refs:
  job=pinned(r);payload=job.get('job',{});need(job.get('status')=='complete' and job.get('sent') is True and job.get('ui_confirmed') is True and not job.get('error') and payload.get('target')==TARGET and payload.get('kind')=='group' and payload.get('scope')=='test','timing-final-client-confirmation-required')
  need(hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==job.get('fingerprint'),'timing-client-job-payload-changed')
  need(any(e.get('stage')=='ui-confirmed' for e in job.get('events',[])),'timing-client-event-required');created=parse_time(job.get('created_at'));completed=parse_time(job.get('completed_at'));need(created<=completed<=clock.wall(),'timing-client-time-invalid')
  if s['origin']=='fresh':need(created>=earliest,'timing-old-send-not-fresh-run')
  need(isinstance(payload.get('key'),str) and Path(r['path']).resolve()==sender_path(payload['key']),'timing-canonical-client-job-required')
  if s['scope'].get('delivery_contract')==DYNAMIC_DELIVERY:
   match=[o for o in s['delivery']['orders'] if o['key']==payload['key']];need(len(match)==1 and all(payload.get(k)==v for k,v in match[0]['sender_payload'].items()),'timing-client-delivery-payload-mismatch')
  actual.append(payload.get('key'))
 need(len(actual)==len(set(actual)) and sorted(actual)==sorted(keys),'timing-expected-client-job-set-mismatch')
 return {'client_jobs':refs,'client_timestamp_resolution_seconds':1,'all_expected_client_confirmed':True}
def zero_acquisition(a,s):
 need(a.get('workflow')==s['scope']['workflow'] and a.get('run_id')==s['run_id'] and a.get('work_order')==s['work_order'] and a.get('scope_sha256')==s['scope_sha256'] and a.get('source')=='local-dom-bridge' and a.get('fixture') is False and a.get('account_verified') is True and a.get('complete') is True and type(a.get('row_count')) is int and a['row_count']==0,'timing-zero-acquisition-invalid')
 refs=a.get('raw_evidence');need(isinstance(refs,list) and refs,'timing-zero-raw-evidence-required')
 for raw in refs:pinned(raw)
 observed=parse_time(a.get('observed_at'))
 if s['origin']=='fresh':need(observed>=parse_time(s['wall_started_at']),'timing-old-zero-acquisition')
 if 'company_ranges' in s['scope']:
  matches=[x for x in company_ranges(s['scope']) if str(x['groupid'])==str(a.get('groupid'))];need(len(matches)==1 and all(a.get(k)==matches[0][k] for k in ('company','start','end_exclusive')),'timing-zero-company-range-invalid')
 return str(a.get('groupid'))
def no_data(receipt,s):
 # Telemetry structural evidence; role validators still replay actual sources.
 binding(receipt,s,'workflow-no-data-completion-v1');need(receipt.get('fixture') is False and receipt.get('live') is True and receipt.get('row_count')==0 and type(receipt.get('row_count')) is int,'timing-real-zero-data-required');acquisitions=receipt.get('acquisitions');need(isinstance(acquisitions,list) and acquisitions,'timing-zero-acquisition-evidence-required')
 seen=[zero_acquisition(pinned(r),s) for r in acquisitions]
 need(sorted(seen)==sorted(str(x['groupid']) for x in company_ranges(s['scope'])),'timing-zero-company-coverage-invalid');return {'acquisitions':acquisitions,'client_send_success':False,'business_source_replay_required_by_workflow':True}
def finish(path,outcome,completion=None,*,reason=None,clock=None):
 clock=clock or Clock();need(outcome in ('client-confirmed','no-data-complete','incomplete'),'timing-outcome-invalid')
 with locked(path) as p:
  s=load(p,clock)
  if s['status']=='complete':need(s['outcome']==outcome and s.get('completion')==completion,'timing-ended-run-conflict');return view(s,clock)
  running(s);detail={}
  if outcome!='incomplete':
   if s['origin']=='fresh':need(any(e['kind']=='first-webpage-action-intent' for e in s['events']),'timing-webpage-boundary-not-measured')
   receipt=pinned(completion);detail=clients(receipt,s,clock) if outcome=='client-confirmed' else no_data(receipt,s)
  else:need(isinstance(reason,str) and reason,'timing-incomplete-reason-required')
  end=clock.monotonic();s.update(status='complete',outcome=outcome,completion=completion,completion_detail=detail,reason=reason,end_monotonic=end,wall_ended_at=stamp(clock),deadline_exceeded=end-s['start_monotonic']>LIMIT,full_workflow_measured=outcome!='incomplete' and s['origin']=='fresh',acceptance_pass=outcome=='client-confirmed' and s['origin']=='fresh' and s['mode']=='acceptance' and end-s['start_monotonic']<=LIMIT);write_start=clock.monotonic();save(p,s);result=view(s,clock);result['final_timing_ledger_write_seconds']=clock.monotonic()-write_start;return result
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='verb',required=True)
 a=sub.add_parser('start');a.add_argument('--run',required=True);a.add_argument('--run-id',required=True);a.add_argument('--work-order',required=True);a.add_argument('--scope',required=True);a.add_argument('--mode',choices=('development','acceptance'),default='development');a.add_argument('--origin',choices=('fresh','resume'),default='fresh');a.add_argument('--resumed-from');a.add_argument('--before-first-webpage-action',action='store_true',required=True)
 for verb in ('web-action-intent','status','finish','stage-start','stage-end','seal-delivery'):
  a=sub.add_parser(verb);a.add_argument('--run',required=True)
  if verb=='seal-delivery':a.add_argument('--manifest',required=True)
  if verb=='finish':a.add_argument('--outcome',choices=('client-confirmed','no-data-complete','incomplete'),required=True);a.add_argument('--completion');a.add_argument('--reason')
  if verb.startswith('stage-'):a.add_argument('--stage-id',required=True);a.add_argument('--phase',required=True)
 a=p.parse_args(argv)
 try:
  if a.verb=='start':result=start(a.run,a.run_id,ref(a.work_order),json.loads(Path(a.scope).read_text()),mode=a.mode,origin=a.origin,resumed_from=ref(a.resumed_from) if a.resumed_from else None)
  elif a.verb=='seal-delivery':result=seal_delivery(a.run,ref(a.manifest))
  elif a.verb=='web-action-intent':result=mark_web_action(a.run)
  elif a.verb=='finish':result=finish(a.run,a.outcome,ref(a.completion) if a.completion else None,reason=a.reason)
  elif a.verb.startswith('stage-'):result=stage(a.run,a.stage_id,a.phase,end=a.verb=='stage-end')
  else:
   clock=Clock()
   with locked(a.run) as path:result=view(load(path,clock),clock)
  print(json.dumps(result,ensure_ascii=False));return 0
 except (TimingError,OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as e:print(json.dumps({'ok':False,'error':str(e),'acceptance_pass':False}));return 2

def configuration_source_material(reference):
    """Resolve installed code directly; never walk historical source releases."""
    project=Path(__file__).absolute().parents[3]
    allowed={str(project/'skills/workshop-director/scripts'/n)for n in('company_configuration.py','execution_timing.py','daily_execution_launcher.py','collection_ready.py')}|{str(project/'skills/negative-review-complaints/scripts'/n)for n in('initial_ledger_recovery.py','review_capture_tab.py','program_review_quality.py')}|{str(project/'skills/douyin-laike-operator/scripts'/n)for n in('bridge-workflow.py','switch_read_recovery.py','export_record_page_recovery.py')}|{str(project/'skills/daily-comment-stats/scripts'/n)for n in('flow.py','notification_backlog.py','daily_timed_run.py','dom_fresh_capture.py')}
    need(type(reference)is dict and set(reference)=={'path','sha256'}and reference['path']in allowed and re.fullmatch('[0-9a-f]{64}',str(reference['sha256'])),'configuration-source-exact-slot')
    current=ref(Path(reference['path']))
    return {'historical':dict(reference),'current':current,'material':current,'dependencies':[]}

if __name__=='__main__':raise SystemExit(main())

# Opt-in company scope; legacy orders keep their original contract.
COMPANY_GROUPS={'烟台一成教育文化咨询有限公司':'1767942028615694','上海老芗汇餐饮管理有限公司':'1764303851132943'}
def company_policy(reference):
    """Public full facts copy; command callers below use the exact indexed row."""
    import copy
    with company_policy_command():return copy.deepcopy(_policy_facts(reference)['value'])if reference is not None else None

def company_names(reference=None):
    p=company_policy(reference);return tuple(c['company']for c in p['active'])if p else tuple(COMPANY_GROUPS)

def offer_company_names(offer):return company_names(offer.get('active_company_policy'))



from contextvars import ContextVar as _PolicyContextVar
from contextlib import ExitStack as _PolicyExitStack
_POLICY_COMMAND=_PolicyContextVar('company_policy_command',default=None)

@contextmanager
def company_policy_command():
    """One bounded command only. No process-global facts or cross-version cache.
    Every lookup checks held-file identity. Full content hashes bracket the
    command; module/config/policy bytes are parsed/loaded once per version.
    """
    existing=_POLICY_COMMAND.get()
    if existing is not None:yield existing['counts'];return
    with _PolicyExitStack()as stack:
        state={'stack':stack,'facts':{},'pins':{},'modules':{},'configs':[],'counts':{'policy_reads':0,'policy_hashes':0,'module_loads':0,'source_hashes':0,'config_parses':0,'config_hashes':0,'business_checks':0,'lookups':0}};token=_POLICY_COMMAND.set(state)
        stack.callback(lambda:state['counts'].update(config_hashes=sum(c.counts['config_hashes']for c in state['configs'])))
        try:
            yield state['counts'];_policy_check(state)
            for pin in state['pins'].values():
                need(hashlib.sha256(pin['path'].read_bytes()).hexdigest()==pin['sha256'],'company-policy-command-exit-drift');state['counts'][pin['counter']]+=1
        finally:_POLICY_COMMAND.reset(token)

def _policy_stamp(path):
    need(path.is_absolute()and path.is_file()and path==path.resolve()and not any(p.is_symlink()for p in(path,*path.parents)),'company-policy-command-canonical');st=path.stat();return(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode)
def _policy_check(state):
    for (source_path,_),module in state['modules'].items():need(getattr(module,'__file__',None)==source_path and Path(source_path)==Path(source_path).resolve(),'company-policy-loaded-module-origin-drift')
    for pin in state['pins'].values():
        st=os.fstat(pin['fd'].fileno());held=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode)
        need(_policy_stamp(pin['path'])==pin['stamp']==held,'company-policy-command-version-drift')
    for item in state['facts'].values():
        if item.get('config')is not None:item['config'].fresh()
def _policy_pin(state,reference,counter):
    path=Path(reference['path']);key=str(path);need(set(reference)=={'path','sha256'},'company-policy-ref-shape')
    if key in state['pins']:
        need(state['pins'][key]['sha256']==reference['sha256'],'company-policy-command-version-change');_policy_check(state);return state['pins'][key]['raw']
    stamp=_policy_stamp(path);fd=state['stack'].enter_context(path.open('rb'));data=fd.read();need(_policy_stamp(path)==stamp and hashlib.sha256(data).hexdigest()==reference['sha256'],'company-policy-ref-changed');state['counts'][counter]+=1;state['pins'][key]={'path':path,'sha256':reference['sha256'],'stamp':stamp,'fd':fd,'raw':data,'counter':counter};_policy_check(state);return data

def _policy_facts(reference):
    state=_POLICY_COMMAND.get();need(state is not None,'company-policy-command-required');need(type(reference)is dict and set(reference)=={'path','sha256'},'company-policy-ref-shape');_policy_check(state)
    key=(reference['path'],reference['sha256'])
    if key in state['facts']:state['counts']['lookups']+=1;return state['facts'][key]
    data=_policy_pin(state,reference,'policy_hashes');state['counts']['policy_reads']+=1;policy=json.loads(data)
    if policy.get('kind')!='active-company-scope-policy-v2':
        need(set(policy)=={'kind','active','retired','reason'}and policy['kind']=='active-company-scope-policy-v1'and policy['reason']=='customer-cooperation-ended-access-unavailable','company-policy-schema');need(policy['active']==[{'company':'上海老芗汇餐饮管理有限公司','groupid':'1764303851132943'}]and policy['retired']==[{'company':'烟台一成教育文化咨询有限公司','groupid':'1767942028615694','disposition':'retired-incomplete-history-preserved'}],'company-policy-exact-authorized-scope');facts={'value':policy,'config':None};state['facts'][key]=facts;return facts
    need(set(policy)=={'kind','configuration','configuration_code','active_ids','retired_ids'},'company-policy-v2-schema')
    path=Path(__file__).resolve().with_name('company_configuration.py')
    import importlib.util
    module_key=(str(path),None)
    if module_key not in state['modules']:
        spec=importlib.util.spec_from_file_location('timing_fixed_configured_companies',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);state['modules'][module_key]=module;state['counts']['module_loads']+=1;state['stack'].enter_context(module.configuration_command())
    module=state['modules'][module_key];config=module.get_config(policy['configuration']);
    if config not in state['configs']:state['configs'].append(config);state['counts']['config_parses']+=1
    active=policy['active_ids'];retired=policy['retired_ids'];need(type(active)is list and bool(active)and type(retired)is list and all(type(x)is str for x in active+retired)and len(set(active+retired))==len(active+retired),'company-policy-v2-partition');rows=[];retired_rows=[]
    for entry in active:rows.append(config.business(entry));state['counts']['business_checks']+=1
    for entry in retired:
        need(entry in config.byid and config.byid[entry]['status']=='retired'and not config.byid[entry]['capabilities'],'company-policy-v2-retired');row=config.byid[entry];retired_rows.append({'company':row['company'],'groupid':row['verified']['groupid']if row['verified']else None,'disposition':'retired-incomplete-history-preserved'})
    need(len({row['provider']for row in rows})==1,'company-policy-v2-single-provider-required');index={(r['company'],r['verified']['groupid']):r for r in rows};need(len(index)==len(rows),'company-policy-v2-duplicate-index');registry={r['verified']['groupid']:r['verified']['identity']for r in rows}
    facts={'value':{**policy,'active':[{'company':r['company'],'groupid':r['verified']['groupid']}for r in rows],'retired':retired_rows,'configured_entries':rows},'config':config,'index':index,'registry':registry,'allowed':sorted(registry)};state['facts'][key]=facts;state['counts']['lookups']+=1;return facts

def _configured_company_policy(policy):
    # Kept private legacy entry; public callers must supply their pinned ref.
    raise TimingError('company-policy-exact-reference-required')

def company_job_fields(reference,company,groupid,*,known=None):
    """Indexed exact target facts; authoritative acquisition remains external."""
    if reference is None:return {}
    import copy
    with company_policy_command():
        facts=_policy_facts(reference);policy=facts['value']
        if policy['kind']!='active-company-scope-policy-v2':return {}
        row=facts['index'].get((company,str(groupid)));need(row is not None,'company-job-target-not-configured');registry=facts['registry']
        if known is not None:
            need(type(known)is dict,'company-job-existing-registry')
            need(str(groupid)not in known or known[str(groupid)]==row['verified']['identity'],'company-job-known-identity-conflict')
        return {'company_configuration_policy':copy.deepcopy(reference),'company_configuration_entry':row['id'],'identity_contract':'merchant-v2','provider_baseline':row['provider'],'identity_baseline':copy.deepcopy(row['verified']['identity']),'known_company_identities':{str(groupid):copy.deepcopy(row['verified']['identity'])},'allowed_groupids':[str(groupid)],'identity_bootstrap':False,'company_configuration_registry':'configured-source-index-v2'}

def company_delivery_profile(reference,company,groupid,mapped_group):
    if reference is None:return None
    import copy
    with company_policy_command():
        facts=_policy_facts(reference);policy=facts['value']
        if policy['kind']!='active-company-scope-policy-v2':return None
        row=facts['index'].get((company,str(groupid)));need(row is not None and row['production_group']==mapped_group,'company-delivery-configured-profile-conflict')
        return {'company':company,'groupid':str(groupid),'brand':row['brand'],'production_group':mapped_group,'policy':copy.deepcopy(reference),'configuration':copy.deepcopy(policy['configuration']),'configuration_code':copy.deepcopy(policy['configuration_code']),'entry_id':row['id']}


def company_run_mapping(reference):
    """Pure v2 run inputs derived only from the fully validated policy index.
    Legacy callers retain their original mapping files. Group is configuration
    metadata, not a verified recipient or permission to send.
    """
    if reference is None:return None
    import copy,csv,io
    with company_policy_command():
        facts=_policy_facts(reference);policy=facts['value']
        if policy['kind']!='active-company-scope-policy-v2':return None
        entries=policy['configured_entries'];rows=[{'seq':i+1,'company':r['company'],'wecom_group':r['production_group']}for i,r in enumerate(entries)]
        stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n');writer.writerow(['公司名称','企业微信群']);writer.writerows((r['company'],r['wecom_group'])for r in rows)
        return {'policy':copy.deepcopy(reference),'configuration':copy.deepcopy(policy['configuration']),'configuration_code':copy.deepcopy(policy['configuration_code']),'companies':{r['company']:{'groupid':r['verified']['groupid']}for r in entries},'mapping':rows,'csv_bytes':stream.getvalue().encode('utf-8'),'identities':{r['company']:{'groupid':r['verified']['groupid']}for r in entries}}


def company_run_target(reference,company):
    """Exact indexed v2 route, without rebuilding the full run CSV per company."""
    if reference is None:return None
    with company_policy_command():
        facts=_policy_facts(reference)
        if facts['value']['kind']!='active-company-scope-policy-v2':return None
        entry=facts['config'].byname.get(company);configured=facts['config'].byid.get(entry,{})
        verified=configured.get('verified')or{};row=facts['index'].get((company,verified.get('groupid')))
        need(row is not None,'company-routing-not-configured')
        return {'company':row['company'],'groupid':row['verified']['groupid'],'production_group':row['production_group'],'brand':row['brand'],'entry_id':row['id']}

_CONFIGURATION_MODULE_SOURCE=ref(Path(__file__).absolute())
_CONFIGURATION_SOURCE_UNCACHED=configuration_source_material
def configuration_source_material(reference):
    state=_POLICY_COMMAND.get()
    if state is None:return _CONFIGURATION_SOURCE_UNCACHED(reference)
    key=json.dumps(reference,sort_keys=True,separators=(',',':'));cache=state.setdefault('source_successors',{})
    counts=state['counts']
    if key not in cache:
        cache[key]=_CONFIGURATION_SOURCE_UNCACHED(reference);counts['source_successor_computes']=counts.get('source_successor_computes',0)+1
    else:counts['source_successor_hits']=counts.get('source_successor_hits',0)+1
    value=cache[key]
    for dependency in [value['material'],value['current'],*value['dependencies']]:_policy_pin(state,dependency,'source_hashes')
    return json.loads(json.dumps(value))


def _configuration_release_doc(reference):
    state=_POLICY_COMMAND.get()
    if state is None:return pinned(reference)
    data=_policy_pin(state,reference,'source_hashes');key=(reference['path'],reference['sha256']);cache=state.setdefault('configuration_release_docs',{})
    if key not in cache:
        cache[key]=json.loads(data);state['counts']['configuration_release_parses']=state['counts'].get('configuration_release_parses',0)+1
    return cache[key]
