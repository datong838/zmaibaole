"""Staged batch item transport. No completion/cursor authority from sender flags.
Only explicit original sealed orders, configured recipient, exclusive per-item run claim.
The three ready providers and final ledger transaction are separate mandatory gates.

B133/W133: the produced-output recipient is configured per workflow
(skills/workshop-director/config/delivery-targets.json, resolved through
delivery_targets and gated by the messenger policy allowlist). Newly derived
items take their flow's configured group; an order sealed by a producer keeps
its own recorded recipient verbatim, so historical evidence never drifts.
"""
import hashlib,json,os,sqlite3,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from collection_ready import raw,ref,doc,immutable,encode,need
import delivery_targets
CONTRACT='three-flow-collection-ready-v1'
ROOT=Path(__file__).resolve().parents[3]
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def sender_job(item):
 need(type(item)is dict and item.get('kind')=='group'and item.get('target')in delivery_targets.allowed() and item.get('scope')=='test'and type(item.get('key'))is str and 0<len(item['key'])<=160,'batch-fixed-recipient-key')
 value={'version':'1.0.0','key':item['key'],'kind':'group','target':item['target'],'scope':'test','type':item['type']}
 payload=raw(item['payload'])
 if item['type']=='text':value['text']=payload.decode('utf-8');need(bool(value['text'].strip())and '\0'not in value['text']and len(value['text'])<=10000,'batch-text')
 else:
  need(item['type']=='file'and 0<len(payload)<=20*1024*1024,'batch-file')
  value.update(file=item['payload']['path'],file_sha256=item['payload']['sha256'],file_name=Path(item['payload']['path']).name)
 return value
def sender_path(item,directory):return Path(directory)/(hashlib.sha256(item['key'].encode()).hexdigest()[:24]+'.json')
def confirmed(item,directory,receipt=None):
 job=sender_job(item);path=sender_path(item,directory);r=ref(path)
 if receipt is not None:need(r==receipt,'batch-client-ref-drift')
 state=doc(r);need(state.get('job')==job and state.get('fingerprint')==digest(job),'batch-client-payload')
 if state.get('text_parts'):
  import importlib.util
  spec=importlib.util.spec_from_file_location('_delivery_text_parts',ROOT/'skills/wecom-messenger/scripts/text_parts.py');parts_module=importlib.util.module_from_spec(spec)
  previous=list(__import__('sys').path)
  try:
   __import__('sys').path.insert(0,str(ROOT/'skills/wecom-messenger/scripts'));spec.loader.exec_module(parts_module);parts_module.validate_completed(state)
  finally:__import__('sys').path[:]=previous
 need(state.get('status')=='complete'and state.get('phase')=='done'and state.get('sent')is True and state.get('ui_confirmed')is True and not state.get('error')and state.get('send_intent_at')and any(e.get('stage')=='send-intent'for e in state.get('events',[]))and any(e.get('stage')=='ui-confirmed'and e.get('recipient')==job['target'] and e.get('recipient_kind')=='group'for e in state.get('events',[])),'batch-client-unconfirmed')
 return r
def _transport_plan(plan):
 need(plan.get('kind')=='three-flow-unified-client-batch-v1'and plan.get('collection_contract')=='three-flow-collection-ready-v1'and plan.get('items')and len({i['key']for i in plan['items']})==len(plan['items']),'batch-plan')
 need(set(plan['ready_reports'])=={'daily-comment-stats','negative-review-complaints','violation-notifier'},'batch-three-ready-barrier')
 for r in plan['ready_reports'].values():raw(r)
 configured=set(delivery_targets.all().values())
 need(len(configured)==1,'batch-single-configured-group')
 for item in plan['items']:
  need(item.get('target')in configured,'batch-current-configured-recipient')
  sender_job(item)
 return plan

DEDUP_DB=ROOT/'runtime/workshop-director/delivery-dedup.sqlite3'
DEDUP_SCHEMA=('create table if not exists delivered(dedup_key text primary key,scope_digest text not null,'
 'company text not null,day text not null,stream text not null,item_key text not null,'
 'content_sha256 text not null,recipient_group_id text not null,round_key text not null,'
 'first_seen_at text not null,attempts integer not null,receipt_path text,receipt_sha256 text,confirmed_at text)')
def _stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def dedup_scope(plan):
 need(type(plan.get('scope'))is list and bool(plan['scope']),'delivery-dedup-scope')
 return hashlib.sha256(json.dumps(plan['scope'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def dedup_key(plan,item,recipient=None):
 # Only immutable delivery facts enter the key: the sealed scope
 # (company/group/start/end), the exact bytes handed to the sender, the
 # recipient. Round, dispatch and item-key identity are excluded on purpose -
 # an identical resend must land on the same key or the ledger proves nothing.
 # stream/part cannot be used: item['key'] embeds digest(round_key) (:237/:251)
 # and derive's output is immutable (check_plan rederives it byte for byte).
 # docs/统一交付发送防重测绘-E1a.md:4 holds the full argument.
 payload=item.get('payload')
 need(type(payload)is dict and type(payload.get('sha256'))is str and len(payload['sha256'])==64,'delivery-dedup-facts')
 if recipient is None:recipient=item['target']
 return hashlib.sha256(('\0'.join(['v1',dedup_scope(plan),payload['sha256'],recipient])).encode()).hexdigest()
def dedup_audit(plan,item):
 # Audit columns only: no key ingredient, so a wrong guess cannot change a decision.
 one=plan['scope'][0];single=len(plan['scope'])==1;key=str(item.get('key')or'-')
 return {'company':str(one[0])if single else'-','day':(str(one[2])+'~'+str(one[3]))if single else'-','stream':(key.split(':')[0]or'-'),'item_key':key}
def _dedup_open():
 try:
  DEDUP_DB.parent.mkdir(parents=True,exist_ok=True)
  db=sqlite3.connect(str(DEDUP_DB),timeout=10,isolation_level=None)
  db.execute('pragma journal_mode=wal');db.execute('pragma synchronous=full');db.execute('pragma busy_timeout=10000');db.execute(DEDUP_SCHEMA)
  return db
 except Exception as error:raise ValueError('delivery-dedup-unavailable: '+type(error).__name__+': '+str(error))
def dedup_claim(plan,item,recipient=None):
 """One row per delivered byte-payload. The primary key is the whole arbiter:
 two concurrent processes can only ever get rowcount 1 once."""
 recipient=item['target'] if recipient is None else recipient
 value=item['payload']['sha256'];audit=dedup_audit(plan,item);key=dedup_key(plan,item,recipient);db=_dedup_open()
 try:
  db.execute('begin immediate')
  cursor=db.execute('insert or ignore into delivered(dedup_key,scope_digest,company,day,stream,item_key,content_sha256,recipient_group_id,round_key,first_seen_at,attempts)values(?,?,?,?,?,?,?,?,?,?,1)',(key,dedup_scope(plan),audit['company'],audit['day'],audit['stream'],audit['item_key'],value,recipient,str(plan.get('round_key')or'-'),_stamp()))
  if cursor.rowcount==1:db.execute('commit');return key
  row=db.execute('select receipt_path from delivered where dedup_key=?',(key,)).fetchone()
  if row[0]:db.execute('commit');raise ValueError('delivery-dedup-already-confirmed: '+str(row[0]))
  # Occupied but never confirmed: the previous attempt died mid-send. Resuming
  # is the only allowed path, and it stays one row, so no second send can start.
  db.execute('update delivered set attempts=attempts+1,round_key=? where dedup_key=?',(str(plan.get('round_key')or'-'),key));db.execute('commit');return key
 except ValueError:
  try:db.execute('rollback')
  except Exception:pass
  raise
 except Exception as error:
  try:db.execute('rollback')
  except Exception:pass
  raise ValueError('delivery-dedup-unavailable: '+type(error).__name__+': '+str(error))
 finally:db.close()
def dedup_confirm(key,receipt):
 db=_dedup_open()
 try:
  db.execute('begin immediate')
  cursor=db.execute('update delivered set receipt_path=?,receipt_sha256=?,confirmed_at=? where dedup_key=?',(receipt['path'],receipt['sha256'],_stamp(),key))
  need(cursor.rowcount==1,'delivery-dedup-confirm-missing-row');db.execute('commit')
 except ValueError:raise
 except Exception as error:raise ValueError('delivery-dedup-unavailable: '+type(error).__name__+': '+str(error))
 finally:db.close()
def _send_item(plan_ref,index,folder,*,sender_directory,invoke=None,checked_plan=None):
 """An interrupted or unknown run is read-only rechecked, never invoked again.
 invoke is a subprocess seam for TEMP tests, not an authority provider.
 """
 invoke=invoke or subprocess.run;plan=checked_plan if checked_plan is not None else check_plan(plan_ref);need(type(index)is int and 0<=index<len(plan['items']),'batch-item-index');item=plan['items'][index];job=sender_job(item)
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);intent=folder/'item-intent.json';run=folder/'item-run-intent.json';result=folder/'item-result.json';path=sender_path(item,sender_directory)
 try:dedup=dedup_claim(plan,item)
 except ValueError as error:
  if not str(error).startswith('delivery-dedup-already-confirmed: ') or not item.get('preconfirmed_client'):raise
  receipt=confirmed(item,sender_directory,item['preconfirmed_client'])
  need(receipt['path']==str(error).split(': ',1)[1],'batch-dedup-prior-client-mismatch');dedup=dedup_key(plan,item)

 binding={'kind':'unified-item-intent-v1','batch':plan_ref,'index':index,'item':item,'sender_path':str(path)}
 if item.get('preconfirmed_client'):
  need(not run.exists(),'batch-prior-client-never-run')
  receipt=confirmed(item,sender_directory,item['preconfirmed_client']);need(doc(receipt)==doc(item['prior_client_evidence']),'batch-prior-client-evidence-drift')
  immutable(intent,encode(binding));immutable(result,encode({'kind':'unified-item-prior-confirmed-v1','intent':ref(intent),'client':receipt}));dedup_confirm(dedup,receipt);return receipt
 if not intent.exists():need(not any(p.exists()for p in(path,run,result)),'batch-unowned-sender-or-result')
 immutable(intent,encode(binding));intent_ref=ref(intent)
 # Terminal result must be checked before prepare, claim or input.
 if result.exists():
  value=doc(ref(result));need(set(value)=={'kind','intent','client'}and value['kind']=='unified-item-confirmed-v1'and value['intent']==intent_ref and run.exists(),'batch-terminal-conflict');_check_run(run,intent_ref,path,job,folder);receipt=confirmed(item,sender_directory,value['client']);dedup_confirm(dedup,receipt);return receipt
 if run.exists():
  _check_run(run,intent_ref,path,job,folder)
  state=doc(ref(path))
  if state.get('status')=='unknown' and state.get('phase') in ('image-verify-sent','verify-sent') and state.get('send_intent_at'):
   # These two native phases only inspect the current chat; neither can send.
   argv=[sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'step','--job',str(path)]
   p=invoke(argv,capture_output=True,text=True,timeout=90)
   immutable(folder/('readonly-reconcile-'+__import__('uuid').uuid4().hex+'.json'),encode({'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
   state=doc(ref(path))
  # The original sender owns the pre-send safety decision. A natural failure
  # before any paste/send may resume once, on the same key; UNKNOWN stays HOLD.
  recovery=folder/'preinput-resume-intent.json'
  read_race=(state.get('phase')=='locate'and state.get('error')=='ui-tree-incomplete'and state.get('last_read',{}).get('truncation_reason')=='single-attribute-unavailable:AXRole:-25201')
  if state.get('status')=='failed'and ((state.get('phase')=='stage'and state.get('error')=='composer-guard-incomplete')or read_race)and not recovery.exists():
   need(state.get('job')==job and state.get('fingerprint')==digest(job),'batch-resume-job-drift')
   need(not any(v for k,v in state.items()if any(w in k.lower()for w in('intent','paste','choice','return'))),'batch-resume-input-present')
   need(not any(any(w in str(e.get('stage','')).lower()for w in('intent','paste','choice','return','confirmed'))for e in state.get('events',[]))and not any(state.get(k)for k in('sent','ui_confirmed','delivery_confirmed','automated_send','user_sent','image_proof')),'batch-resume-send-present')
   old_exit=doc(ref(folder/'run-exit.json'));argv=[sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'run','--job',str(path)]
   need(old_exit['argv']==argv and old_exit['returncode']==2 and not old_exit['stderr'],'batch-resume-natural-failure-required')
   immutable(folder/'preinput-sender-before.json',raw(ref(path)))
   immutable(recovery,encode({'kind':'unified-preinput-resume-intent-v1','intent':intent_ref,'sender':ref(path),'natural_exit':ref(folder/'run-exit.json')}))
   resume=[sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'resume','--job',str(path)]
   p=invoke(resume,capture_output=True,text=True,timeout=60);immutable(folder/'preinput-resume-exit.json',encode({'argv':resume,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}));need(p.returncode==0,'batch-preinput-resume-failed')
   immutable(folder/'preinput-rerun-intent.json',encode({'recovery':ref(recovery),'sender':ref(path),'argv':argv}))
   p=invoke(argv,capture_output=True,text=True,timeout=360);immutable(folder/'preinput-rerun-exit.json',encode({'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
  receipt=confirmed(item,sender_directory) # absent/unknown/failed => HOLD, no run
  immutable(result,encode({'kind':'unified-item-confirmed-v1','intent':intent_ref,'client':receipt}));dedup_confirm(dedup,receipt);return receipt
 need(not path.exists(),'batch-unowned-prepared-sender')
 argv=[sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'prepare','--key',item['key'],'--kind','group','--target',job['target'],'--scope','test','--directory',str(sender_directory),'--file'if item['type']=='file'else'--text-file',item['payload']['path']]
 p=invoke(argv,capture_output=True,text=True,timeout=30);immutable(folder/'prepare-exit.json',encode({'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}));need(p.returncode==0,'batch-prepare-failed')
 state=doc(ref(path));need(state.get('job')==job and state.get('fingerprint')==digest(job)and state.get('status')=='running'and state.get('phase')=='locate'and state.get('events')==[]and state.get('sent')is False and state.get('ui_confirmed')is False,'batch-prepared-state')
 prepared=immutable(folder/'sender-before.json',raw(ref(path)));claim=encode({'kind':'unified-item-run-intent-v1','intent':intent_ref,'sender_path':str(path),'prepared':prepared})
 # Only this exclusive creator gets permission to invoke the original sender key.
 with run.open('xb')as stream:stream.write(claim);stream.flush();os.fsync(stream.fileno())
 argv=[sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'run','--job',str(path)];p=invoke(argv,capture_output=True,text=True,timeout=360)
 immutable(folder/'run-exit.json',encode({'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
 receipt=confirmed(item,sender_directory);immutable(result,encode({'kind':'unified-item-confirmed-v1','intent':intent_ref,'client':receipt}));dedup_confirm(dedup,receipt);return receipt

def _check_run(run,intent_ref,path,job,folder):
 value=doc(ref(run));need(set(value)=={'kind','intent','sender_path','prepared'}and value['kind']=='unified-item-run-intent-v1'and value['intent']==intent_ref and value['sender_path']==str(path)and value['prepared']['path']==str(folder/'sender-before.json'),'batch-run-binding')
 before=doc(value['prepared']);need(before.get('job')==job and before.get('fingerprint')==digest(job)and before.get('status')=='running'and before.get('phase')=='locate'and before.get('events')==[],'batch-run-original-prepared')
def _all_transport_clients(plan_ref,folder,*,sender_directory):
 plan=_transport_plan(doc(plan_ref));clients=[]
 for index,item in enumerate(plan['items']):
  base=Path(folder)/str(index).zfill(4);value=doc(ref(base/'item-result.json'));need(value.get('kind')==('unified-item-prior-confirmed-v1'if item.get('preconfirmed_client')else'unified-item-confirmed-v1')and value.get('intent')==ref(base/'item-intent.json'),'batch-item-result-binding')
  binding=doc(value['intent']);need(binding=={'kind':'unified-item-intent-v1','batch':plan_ref,'index':index,'item':item,'sender_path':str(sender_path(item,sender_directory))},'batch-item-intent-binding');need(not(base/'item-run-intent.json').exists(),'batch-prior-client-never-run')if item.get('preconfirmed_client')else _check_run(base/'item-run-intent.json',value['intent'],sender_path(item,sender_directory),sender_job(item),base)
  if item.get('preconfirmed_client'):need(value['client']==item['preconfirmed_client']and doc(value['client'])==doc(item['prior_client_evidence']),'batch-prior-client-evidence-drift')
  clients.append(confirmed(item,sender_directory,value['client']))
 return {'kind':'three-flow-all-client-confirmed-v1','batch':plan_ref,'clients':clients,'cursor_advanced':False,'workflow_completed':False}



def _current_ready_facts(ready_reports):
    """Consume only the three explicitly selected current producer results."""
    flows={'daily-comment-stats','negative-review-complaints','violation-notifier'}
    need(set(ready_reports)==flows,'batch-three-ready-barrier')
    reports={};days=set();scopes=[]
    for flow,reference in ready_reports.items():
        report=doc(reference);order=doc(report['order'])
        need(report.get('workflow')==order.get('workflow')==flow,'batch-ready-workflow')
        need(report.get('collection_contract')==order.get('collection_contract')==CONTRACT,'batch-ready-contract')
        need(report.get('collection_ready')is True and report.get('fixture')is not True and report.get('complete')is False and report.get('delivery_complete')is False and report.get('cursor_advanced')is False,'batch-ready-stage')
        need(report['day']==order['day'] and report['scope_sha256']==order['scope_sha256'],'batch-ready-scope')
        kinds={'daily-comment-stats':'daily-director-collection-ready-report-v1','negative-review-complaints':'complaint-director-collection-ready-report-v1','violation-notifier':'violation-director-collection-ready-report-v1'}
        need(report.get('kind')==kinds[flow] and report['dispatch_id']==order['dispatch_id'],'batch-current-producer-result')
        days.add(report['day']);reports[flow]=(report,order)
    need(len(days)==1,'batch-ready-day-mismatch')
    report,order=reports['daily-comment-stats'];ready=doc(report['ready'])
    need(ready.get('kind')=='daily-collection-ready-v1' and ready.get('collection_ready')is True and ready.get('delivery_complete')is False and ready.get('cursor_advanced')is False and ready.get('sender_invoked')is False,'batch-daily-ready-stage')
    daily={'report':report,'ready':ready,'order':order}
    roles={flow:{**report,'order_document':order} for flow,(report,order) in reports.items() if flow!='daily-comment-stats'}
    scopes=[{(c['company'],str(c['groupid']),c['start'],c['end_exclusive']) for c in daily['ready']['companies']}]+[{(c['company'],str(c['groupid']),c['start'],c['end_exclusive']) for c in role['companies']} for role in roles.values()]
    need(bool(scopes[0]) and all({(c[0],c[1],c[3])for c in scope}=={(c[0],c[1],c[3])for c in scopes[0]} for scope in scopes),'batch-same-company-end-required')
    for flow,role in roles.items():
        expected={(c['company'],str(c['groupid']),c['start'],c['end_exclusive'])for c in role['order_document']['companies']if not c.get('skipped')}
        actual={(c['company'],str(c['groupid']),c['start'],c['end_exclusive'])for c in role['companies']}
        need(expected==actual,'batch-role-original-company-ranges')
    return daily,roles

def check_plan(plan_ref,*,_details=False):
    value=_transport_plan(doc(plan_ref))
    daily,roles=_current_ready_facts(value['ready_reports'])
    scope={(c['company'],str(c['groupid']),c['start'],c['end_exclusive']) for c in daily['ready']['companies']}
    need({(c[0],str(c[1]),c[2],c[3]) for c in value['scope']}==scope,'batch-plan-current-scope')
    expected={flow:[[c['company'],str(c['groupid']),c['start'],c['end_exclusive']]for c in (daily['ready']['companies']if flow=='daily-comment-stats'else roles[flow]['companies'])]for flow in value['ready_reports']}
    need(value.get('flow_scopes')==expected,'batch-plan-original-flow-scopes')
    return (value,{'daily':daily,'roles':roles}) if _details else value

def send_item(plan_ref,index,folder,*,sender_directory,invoke=None):
    # Validate the sealed current plan and keep recipient/dedup checks.
    need(Path(sender_directory)==ROOT/'runtime/wecom-messenger','batch-canonical-sender-directory')
    value=check_plan(plan_ref)
    return _send_item(plan_ref,index,folder,sender_directory=sender_directory,invoke=invoke,checked_plan=value)

def _daily_zero_order(notice,company,start,end,receipt,module_ref,*,write):
    """Sealing may create text; proof reads never invoke a writing producer."""
    last=notice.qualify('daily-comment-stats',company,start,end,[receipt]);raw(receipt);raw(module_ref)
    title,summary=notice.FLOWS['daily-comment-stats'];text=f'【{title}】\n公司：{company}\n日期：{start}～{last}\n{summary}'
    payload=Path(receipt['path']).parent/'test-notifications/zero-result.txt';expected={'path':str(payload),'sha256':hashlib.sha256(text.encode()).hexdigest()}
    if write:need(immutable(payload,text.encode())==expected,'batch-zero-text-write')
    else:need(raw(expected)==text.encode(),'batch-zero-text-drift')
    native={'part':'zero-result','type':'text','key':'daily-comments:'+company+':'+start+':'+last+':zero-result','kind':'group','target':notice.TARGET,'scope':'test','text_file':str(payload),'text_sha256':expected['sha256'],'zero_result_binding':{'flow':'daily-comment-stats','company':company,'start':start,'end_exclusive':end,'work_order':receipt,'sources':[receipt],'zero_module_ref':module_ref}}
    notice.job(native) # Original public content/identity/key consumer, no writes.
    return native

def daily_review_facts(company):
    """Same verified daily content branch used by the three-ready barrier."""
    import unified_review_format as render_update
    from datetime import date,timedelta
    name,start,end=(company[k]for k in('company','start','end_exclusive'));last=(date.fromisoformat(end)-timedelta(days=1)).isoformat();stats=company['statistics']
    if company.get('source_kind')=='daily-visible-dom-source-v1':
        need(company.get('download_verified')is False and company.get('source_is_authoritative_export')is False,'batch-dom-source-authority')
        facts=render_update.build(company['source']['path'],name,start,last,stats[0]['path']if stats else None,dom_source=company['dom_source'])
    else:facts=render_update.build(company['source']['path'],name,start,last,stats[0]['path']if stats else None)
    need(facts['rows']==company['row_count'],'batch-xlsx-count-drift');return facts

def derive(ready_reports,round_key,folder,*,write=False,_return_facts=False,accepted_request=None):
    import daily_orchestration,collection_ready,notification_backlog,unified_review_format as render_update
    from datetime import date,timedelta
    need(type(round_key)is str and bool(round_key)and set(ready_reports)=={'daily-comment-stats','negative-review-complaints','violation-notifier'},'batch-three-ready-barrier')
    daily,roles=_current_ready_facts(ready_reports)
    if accepted_request is not None:
        request=doc(accepted_request)
        need(round_key==request['task']['plan_id']+':'+request['task']['day'],'batch-current-round-key')
    scopes=[{(c['company'],c['groupid'],c['start'],c['end_exclusive'])for c in daily['ready']['companies']}]+[{(c['company'],c['groupid'],c['start'],c['end_exclusive'])for c in v['companies']}for v in roles.values()]
    need(bool(scopes[0])and all({(c[0],str(c[1]),c[3])for c in scope}=={(c[0],str(c[1]),c[3])for c in scopes[0]}for scope in scopes),'batch-same-company-end-required')
    need(len({daily['report']['day'],*[v['day']for v in roles.values()]})==1,'batch-ready-day-mismatch')
    folder=Path(folder);items=[]
    need(Path(render_update.__file__)==ROOT/'skills/workshop-director/scripts/unified_review_format.py','batch-fixed-review-formatter-origin')
    def text_items(key,text,heading,target):
        parts=notification_backlog.pn.chunks(text)
        for index,body in enumerate(parts,1):
            message=(('【%s %d/%d】\n'%(heading,index,len(parts)))if index>1 else'')+body;itemkey=key+':%03d'%index;path=folder/'texts'/(hashlib.sha256(itemkey.encode()).hexdigest()+'.txt');payload={'path':str(path),'sha256':hashlib.sha256(message.encode()).hexdigest()}
            if write:need(immutable(path,message.encode())==payload,'batch-text-write')
            else:need(raw(payload)==message.encode(),'batch-text-not-derived')
            items.append({'key':itemkey,'kind':'group','target':target,'scope':'test','type':'text','payload':payload})
    def item(order):
        need(order.get('kind')=='group'and order.get('target')in delivery_targets.allowed() and order.get('scope')=='test','batch-recipient')
        kind=order.get('type','file'if order.get('file')else None);need(kind in('text','file'),'batch-original-order-type');name='file'if kind=='file'else'text_file';payload=ref(Path(order[name]))if 'file_sha256'not in order and kind=='file'else{'path':order[name],'sha256':order['file_sha256']if kind=='file'else order['text_sha256']};raw(payload)
        return {'key':order['key'],'kind':'group','target':order['target'],'scope':'test','type':kind,'payload':payload}
    for company in daily['ready']['companies']:
        name,gid,start,end=(company[k]for k in('company','groupid','start','end_exclusive'));last=(date.fromisoformat(end)-timedelta(days=1)).isoformat()
        violation=next(c for c in roles['violation-notifier']['companies']if c['company']==name)
        need(type(violation['count'])is int and violation['count']>=0,'batch-verified-violation-count')
        # Source XLSX is authoritative even when zero; no HTML count substituted.
        stats=company['statistics'];facts=daily_review_facts(company)
        mapping=next(c for c in notification_backlog.batch_mapping(doc(daily['ready']['batch']))[0]if c['company']==name)
        violation_state=roles['violation-notifier'];violation_ledger=doc(next(x['archive']for x in violation_state['ledgers']if x['company']==name));violation_engine=doc(violation_state['engine_archive']);ci=next(i for i,c in enumerate(violation_state['order_document']['companies'])if c['company']==name);violation_batch=violation_ledger['batches'][violation_engine['companies'][ci]['artifacts']['batch']];source_ref=violation['source'];source=doc(source_ref);copydoc=doc(violation_batch['copy_evidence'])if violation['count']else None
        import execution_timing as timing
        profile=timing.company_delivery_profile(daily['order'].get('active_company_policy'),name,gid,mapping['wecom_group'])
        brand=profile['brand']if profile else(notification_backlog.pn.BRANDS.get(name)or mapping['wecom_group'])
        text=render_update.render(facts,brand,mapping['wecom_group'],'online',violation_summary=render_update.violation_brief(source,source_ref['sha256'],copydoc))
        key='unified-review:'+digest({'round_key':round_key,'company':name,'groupid':gid,'start':start,'end_exclusive':end})[:48];text_items(key,text,'评价日报｜'+name+'｜'+start+'～'+last,delivery_targets.target('daily-comment-stats'))
        if company['row_count']:
            for part,artifacts in(('detail',company['detail']),('stats',company['statistics'])):
                need(len(artifacts)==1,'batch-daily-exact-artifact');artifact=artifacts[0];payload={'path':artifact['path'],'sha256':artifact['sha256']};raw(payload)
                items.append({'key':'daily-comments:'+name+':'+start+':'+last+':'+part,'kind':'group','target':delivery_targets.target('daily-comment-stats'),'scope':'test','type':'file','payload':payload})
        else:
            notice=notification_backlog._zero_notice_module();native=_daily_zero_order(notice,name,start,end,company['receipt'],notification_backlog._ZERO_NOTICE_MODULE,write=write);items.append(item(native))
    for flow,value in roles.items():
        manifest=doc(value['delivery_plan'])
        if flow=='negative-review-complaints':
            role_engine=doc(value['engine_archive'])
            for c,cs in zip(value['order_document']['companies'],role_engine['companies']):
                if c['skipped']:continue
                ledger=doc(next(x['archive']for x in value['ledgers']if x['company']==c['company']));keys=list(dict.fromkeys(key for unit in cs['artifacts']['completed_units']for key in unit.get('keys',[])));new_count=next(x['count']for x in value['companies']if x['company']==c['company']);text=render_update.complaint_summary(c['company'],c['start'],c['end_exclusive'],new_count,ledger,keys)
                if text:text_items('unified-complaint:'+digest({'round_key':round_key,**{k:c[k]for k in('company','groupid','start','end_exclusive')}})[:48],text,'差评投诉流程｜'+c['company']+'｜'+c['start']+'～'+(date.fromisoformat(c['end_exclusive'])-timedelta(days=1)).isoformat(),delivery_targets.target('negative-review-complaints'))
        for order in manifest['orders']:
            native=order['order']if flow=='negative-review-complaints'else order
            if flow=='negative-review-complaints'and order.get('image_sha256'):native={**native,'type':'file','file_sha256':order['image_sha256']}
            if flow=='negative-review-complaints'and order.get('collection_workbook'):
                import current_complaint_workbook
                ci=next(i for i,c in enumerate(value['order_document']['companies'])if c['company']==order['company']);ledger=doc(next(x['archive']for x in value['ledgers']if x['company']==order['company']))
                native=current_complaint_workbook.delivery_order(native,value['order_document']['companies'][ci],role_engine['companies'][ci],ledger)
            value_item=item(native)
            if flow=='negative-review-complaints'and not order.get('zero_result')and not order.get('collection_workbook'):
                ledger=doc(next(x['archive']for x in value['ledgers']if x['company']==order['company']));task=ledger['tasks'][order['review_key']]
                if task.get('wecom'):
                    prior=confirmed(value_item,ROOT/'runtime/wecom-messenger');need(doc(prior)==doc(task['wecom']),'batch-original-prior-client-changed');value_item.update(preconfirmed_client=prior,prior_client_evidence=task['wecom'])
            items.append(value_item)
    # A completed company may already have delivered these exact original items.
    # Consult only each current business key; never scan sender history.
    for current_item in items:
        path=sender_path(current_item,ROOT/'runtime/wecom-messenger')
        if path.exists():
            prior=confirmed(current_item,ROOT/'runtime/wecom-messenger')
            current_item.update(preconfirmed_client=prior,prior_client_evidence=prior)
    value={'kind':'three-flow-unified-client-batch-v1','collection_contract':'three-flow-collection-ready-v1','round_key':round_key,'ready_reports':ready_reports,'scope':[list(s)for s in sorted(scopes[0])],'flow_scopes':{flow:[[c['company'],str(c['groupid']),c['start'],c['end_exclusive']]for c in (daily['ready']['companies']if flow=='daily-comment-stats'else roles[flow]['companies'])]for flow in ready_reports},'items':items}
    if accepted_request is not None:value['accepted_request']=accepted_request
    _transport_plan(value)
    if write:return immutable(folder/'batch.json',encode(value))
    return (value,{'daily':daily,'roles':roles})if _return_facts else value


def all_clients(plan_ref,folder,*,sender_directory):
    need(Path(sender_directory)==ROOT/'runtime/wecom-messenger','batch-canonical-sender-directory')
    check_plan(plan_ref)
    return _all_transport_clients(plan_ref,folder,sender_directory=sender_directory)

def seal_clients(plan_ref,folder,*,sender_directory):
    value=all_clients(plan_ref,folder,sender_directory=sender_directory)
    return immutable(Path(plan_ref['path']).parent/'all-clients-confirmed.json',encode(value))
def verify_client_proof(proof_ref,folder,*,sender_directory,_details=False):
    value=doc(proof_ref);need(set(value)=={'kind','batch','clients','cursor_advanced','workflow_completed'}and value['kind']=='three-flow-all-client-confirmed-v1'and proof_ref['path']==str(Path(value['batch']['path']).parent/'all-clients-confirmed.json'),'batch-client-proof-origin')
    need(Path(sender_directory)==ROOT/'runtime/wecom-messenger','batch-canonical-sender-directory')
    plan,inputs=check_plan(value['batch'],_details=True)
    need(value==_all_transport_clients(value['batch'],folder,sender_directory=sender_directory),'batch-client-proof-not-derived')
    return (plan,inputs,value)if _details else plan


def _close_accepted_complaint(workflow,ledger,batch,completed_at,day):
    b=ledger['batches'][batch];workflow.verify_evidence(b['snapshot'])
    for key in b['ids']:
        task=ledger['tasks'][key]
        need(task['status']in workflow.READY and task.get('screenshot')and task.get('wecom'),'batch-accepted-complaint-not-ready')
        for evidence in (task['latest_snapshot'],task['screenshot'],task['wecom']):workflow.verify_evidence(evidence)
        if task.get('result'):workflow.verify_evidence(task['result']['evidence'])
        if task.get('analysis'):workflow.verify_evidence(task['analysis']['evidence'])
        need(task['action']not in ('查看投诉结果','投诉审核中')or task.get('result'),'batch-accepted-complaint-result-required')
    return workflow._close_collected_batch_value(ledger,batch,completed_at=completed_at,completed_on=day)

def _complete_accepted_violation(workflow,ledger,batch,zero,completed_at,day,source_ref=None):
    b=ledger['batches'][batch];workflow.verify(b['source'])
    if not b['total']:
        need(zero is not None,'batch-accepted-zero-notice-required');native=zero['order'];binding=native['zero_result_binding']
        need(binding['flow']=='violation-notifier'and binding['company']==ledger['company']and binding['start']==b['start']and binding['end_exclusive']==b['end_exclusive'],'batch-accepted-zero-scope')
        if binding['sources']!=[b['source']]:
            # Match the existing collection seal/send adoption of a verified
            # zero recapture; preserve the sealed ledger source and fingerprint.
            need(source_ref is not None and binding['sources']==[source_ref],'batch-accepted-zero-source')
            source=doc(source_ref)
            need(b['status']=='zero_verified'and b['input_fingerprint']==workflow.fingerprint(doc(b['source']))and workflow.zero_recapture_aligned(ledger,b,source),'batch-accepted-zero-adoption')
        _zero_client(native,zero['client']);b['zero_result_notification']=zero
    return workflow._complete_collected_value(ledger,batch,zero_notice=zero,completed_at=completed_at,completed_on=day)

def _completion_workflow(flow):
    import importlib.util
    need(flow in ('negative-review-complaints','violation-notifier'),'batch-fixed-completion-workflow')
    path=ROOT/'skills'/flow/'scripts/workflow.py'
    need(path.resolve()==path and not path.is_symlink(),'batch-completion-workflow-origin')
    name='_batch_completion_'+flow.replace('-','_');old=sys.path[:]
    try:
        sys.path[:0]=[str(path.parent)]
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    finally:sys.path[:]=old

def _zero_client(order,receipt):
    import notification_backlog
    need(order['zero_result_binding']['zero_module_ref']==notification_backlog._ZERO_NOTICE_MODULE,'batch-zero-client-module')
    notification_backlog._zero_notice_module().client(order,receipt)

def completion_values(client_proof_ref,delivery_folder,*,sender_directory,completed_at):
    """Derive exact three-workflow ledger values; no runtime writes.
    All item clients are independently checked BEFORE deriving any cursor value.
    Archived ready ledgers, not already-mutated canonical files, are the basis.
    """
    import copy,ds_progress,collection_ready
    from datetime import datetime
    from zoneinfo import ZoneInfo
    at=datetime.fromisoformat(completed_at);need(at.utcoffset()is not None,'batch-completion-aware-time');day=at.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()
    plan,inputs,client_proof=verify_client_proof(client_proof_ref,delivery_folder,sender_directory=sender_directory,_details=True)
    clients={item['key']:r for item,r in zip(plan['items'],client_proof['clients'])};commits=[]
    daily=inputs['daily']['ready'];before=doc(daily['progress_before']);after=ds_progress._commit_collection_facts(before,daily,client_proof_ref,completed_at=completed_at)
    commits.append({'workflow':'daily-comment-stats','target':daily['original_progress'],'before_archive':daily['progress_before'],'after':after})
    for flow,value in inputs['roles'].items():
        parent=doc(value['parent_archive']);engine=doc(value['engine_archive']);order=value['order_document'];manifest=doc(value['delivery_plan'])
        w=_completion_workflow(flow)
        for c,cs in zip(order['companies'],engine['companies']):
            if c['skipped']:continue
            before=next(x for x in value['ledgers']if x['company']==c['company']);ledger=copy.deepcopy(doc(before['archive']));root=Path(c['root'])
            need(before['original']['path']==str(root/'state.json'),'batch-canonical-ledger-target')
            if flow=='negative-review-complaints':
                selected=[x for x in manifest['orders']if x['company']==c['company']]
                for item in selected:
                    if item.get('collection_workbook'):continue
                    native=item['order'];receipt=clients[native['key']]
                    if item.get('zero_result'):
                        _zero_client(native,receipt)
                        ledger['batches'][c['start']+'_'+c['end_exclusive']]['zero_result_notification']={'order':native,'client':receipt}
                        continue
                    key=item['review_key'];need(w._collected_send_order(root,ledger,key)==native,'batch-original-complaint-send-order');state=doc(receipt);need(state['job']['file_sha256']==ledger['tasks'][key]['screenshot']['sha256'],'batch-complaint-client-image')
                    ledger['tasks'][key]['wecom']=receipt;ledger['tasks'][key]['send_attempt']={'order':native,'job_path':receipt['path']}
                ledger=_close_accepted_complaint(w,ledger,c['start']+'_'+c['end_exclusive'],completed_at,day)
                ledger['xlsx_dirty']=True
            else:
                a=cs['artifacts'];batch=a['batch'];b=ledger['batches'][batch];selected=next(x for x in manifest['companies']if x['company']==c['company'])['orders'];zero=None
                for native in selected:
                    receipt=clients[native['key']]
                    if not b['total']:zero={'order':native,'client':receipt};continue
                    b['send_jobs'][native['part']]={'order':native,'job_path':receipt['path'],'confirmed':True,'receipt':receipt,'confirmation':w.SENT_LABEL}
                ledger=_complete_accepted_violation(w,ledger,batch,zero,completed_at,day,a['source'])
            ledger.setdefault('events',[]).append({'at':completed_at,'type':'unified-client-batch-completed','client_proof':client_proof_ref,'collection_ready_report':plan['ready_reports'][flow],'not_platform_submission':True});ledger['updated_at']=completed_at
            commits.append({'workflow':flow,'target':before['original'],'before_archive':before['archive'],'after':ledger})
    need(len({x['target']['path']for x in commits})==len(commits),'batch-duplicate-ledger-target')
    return commits

_policy_original_derive=derive
def derive(*args,**kwargs):
    import execution_timing as timing
    from ds_common import dom_command
    with dom_command():return _policy_original_derive(*args,**kwargs)

