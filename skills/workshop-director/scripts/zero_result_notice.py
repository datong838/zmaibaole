"""Zero-result business notices. Existing sender owns all UI and UNKNOWN policy.
No CLI, implicit recipient, generic text, historical backfill or retry authority.
"""
import hashlib,json,os,subprocess,sys
from datetime import date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
import delivery_targets
TARGET=delivery_targets.target('daily-comment-stats')
FLOWS={'daily-comment-stats':('评价日报','评价0条，采集与核验完成。'),'negative-review-complaints':('差评投诉流程','本次筛选范围内中差评0条，核验完成。'),'violation-notifier':('违规巡查','违规0条，违规分析与违规记录列表均已核对。')}
def need(ok,error):
 if not ok:raise ValueError(error)
def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def ref(path):
 p=Path(path);need(p.is_absolute()and p.resolve()==p and not any(x.is_symlink()for x in (p,*p.parents))and p.is_file(),'zero-notice-reference');return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(reference):
 p=Path(reference['path']);need(set(reference)=={'path','sha256'}and p.is_absolute()and p.resolve()==p and not any(x.is_symlink()for x in (p,*p.parents))and p.is_file(),'zero-notice-reference');data=p.read_bytes();need(hashlib.sha256(data).hexdigest()==reference['sha256'],'zero-notice-reference-drift');return data
def immutable(path,data):
 path=Path(path);need(path.is_absolute()and path.resolve()==path and not any(p.is_symlink()for p in (path,*path.parents)),'zero-notice-path');path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(path.read_bytes()==data,'zero-notice-immutable-conflict')
 else:
  with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 return ref(path)
def qualify(flow,company,start,end_exclusive,sources):
 need(flow in FLOWS and type(company)is str and company and date.fromisoformat(start)<date.fromisoformat(end_exclusive)and sources,'zero-notice-scope');end=(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat()
 for reference in sources:
  s=json.loads(raw(reference));need(s.get('company')==company,'zero-notice-company')
  if flow=='daily-comment-stats':
   need(s.get('flow')==flow and s.get('status')=='zero_rows'and s.get('zero_rows')is True and type(s.get('row_count'))is int and s['row_count']==s.get('page_filtered')==0 and s.get('attribution_verified')is True and s.get('mismatch')is False and not s.get('warnings')and s['date_range']['start']==start and s['date_range']['end']==end,'zero-notice-daily-not-zero')
  else:
   need(s.get('start')==start and s.get('end_exclusive')==end_exclusive,'zero-notice-date')
   if flow=='negative-review-complaints':need(s.get('rows')==[]and s.get('account_verified')is True and s.get('all_pages_read')is True,'zero-notice-complaint-not-zero')
   else:need(s.get('analysis',{}).get('total')==s.get('records',{}).get('total')==0 and type(s['records']['total'])is int and type(s['analysis']['total'])is int and s['records']['rows']==s['analysis']['rows']==[],'zero-notice-violation-not-zero')
 return end

def prepare(folder,flow,company,start,end_exclusive,work_order,sources,*,module_ref):
 end=qualify(flow,company,start,end_exclusive,sources);raw(work_order);raw(module_ref)
 title,summary=FLOWS[flow];text=f'【{title}】\n公司：{company}\n日期：{start}～{end}\n{summary}'
 binding={'flow':flow,'company':company,'start':start,'end_exclusive':end_exclusive,'work_order':work_order,'sources':sources,'zero_module_ref':module_ref}
 key=('daily-comments:'+company+':'+start+':'+end+':zero-result')if flow=='daily-comment-stats'else flow+':zero-result:'+digest({k:v for k,v in binding.items()if k not in ('sources','zero_module_ref')})[:32]
 payload=Path(folder)/'zero-result.txt';r=immutable(payload,text.encode())
 return {'part':'zero-result','type':'text','key':key,'kind':'group','target':TARGET,'scope':'test','text_file':r['path'],'text_sha256':r['sha256'],'zero_result_binding':binding}
def job(order):
 binding=order['zero_result_binding'];raw(binding['zero_module_ref']);end=qualify(binding['flow'],binding['company'],binding['start'],binding['end_exclusive'],binding['sources']);raw(binding['work_order']);title,summary=FLOWS[binding['flow']];text=f'【{title}】\n公司：{binding["company"]}\n日期：{binding["start"]}～{end}\n{summary}'
 key=('daily-comments:'+binding['company']+':'+binding['start']+':'+end+':zero-result')if binding['flow']=='daily-comment-stats'else binding['flow']+':zero-result:'+digest({k:v for k,v in binding.items()if k not in ('sources','zero_module_ref')})[:32]
 need(order=={'part':'zero-result','type':'text','key':key,'kind':'group','target':TARGET,'scope':'test','text_file':order['text_file'],'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'zero_result_binding':binding}and raw({'path':order['text_file'],'sha256':order['text_sha256']})==text.encode(),'zero-notice-order-drift')
 return {'version':'1.0.0','key':key,'kind':'group','target':TARGET,'scope':'test','type':'text','text':text}
def sender_path(key):return ROOT/'runtime/wecom-messenger'/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json')
def client(order,receipt=None):
 expected=job(order);path=sender_path(order['key']);r=ref(path)
 if receipt is not None:need(r==receipt,'zero-notice-client-drift')
 s=json.loads(raw(r));need(s.get('job')==expected and s.get('fingerprint')==digest(expected),'zero-notice-client-binding')
 need(s.get('status')=='complete'and s.get('phase')=='done'and s.get('sent')is True and s.get('ui_confirmed')is True and not s.get('error')and s.get('send_intent_at')and any(e.get('stage')=='send-intent'for e in s.get('events',[]))and any(e.get('stage')=='ui-confirmed'and e.get('recipient')==TARGET and e.get('recipient_kind')=='group'for e in s.get('events',[])),'zero-notice-client-unconfirmed')
 return r
def send(folder,order,*,invoke=None):
 invoke=invoke or subprocess.run;expected=job(order);folder=Path(folder);path=sender_path(order['key']);intent=folder/'notice-intent.json';run=folder/'notice-run-intent.json';result=folder/'notice-result.json';binding={'kind':'zero-result-notice-send-intent-v1','order':order,'sender_path':str(path)}
 if not intent.exists():need(not path.exists()and not run.exists()and not result.exists(),'zero-notice-unowned-sender')
 immutable(intent,encode(binding))
 if run.exists():
  ri=json.loads(raw(ref(run)));need(set(ri)=={'kind','intent','sender','sender_path'}and ri['kind']=='zero-result-notice-run-intent-v1'and ri['intent']==ref(intent)and ri['sender_path']==str(path)and ri['sender']['path']==str(folder/'sender-prepared.json'),'zero-notice-run-binding');prepared=json.loads(raw(ri['sender']));need(prepared.get('job')==expected and prepared.get('fingerprint')==digest(expected)and prepared.get('phase')=='locate'and prepared.get('events')==[],'zero-notice-run-binding')
 if result.exists():
  value=json.loads(raw(ref(result)));need(run.exists()and set(value)=={'kind','intent','client'}and value['kind']=='zero-result-notice-confirmed-v1'and value.get('intent')==ref(intent),'zero-notice-result-binding');return client(order,value['client'])
 if path.exists():
  state=json.loads(raw(ref(path)));need(state.get('job')==expected and state.get('fingerprint')==digest(expected),'zero-notice-client-binding')
  if state.get('status')=='complete':
   need(run.exists(),'zero-notice-unowned-completion');r=client(order);immutable(result,encode({'kind':'zero-result-notice-confirmed-v1','intent':ref(intent),'client':r}));return r
 need(not run.exists(),'zero-notice-unknown-no-replay')
 if not path.exists():
  p=invoke([sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'prepare','--key',order['key'],'--kind','group','--target',TARGET,'--scope','test','--text-file',order['text_file']],capture_output=True,text=True,timeout=30);need(p.returncode==0,'zero-notice-prepare-failed')
 state=json.loads(raw(ref(path)));need(state.get('job')==expected and state.get('fingerprint')==digest(expected)and state.get('status')=='running'and state.get('phase')=='locate'and state.get('events')==[]and state.get('sent')is False and state.get('ui_confirmed')is False and not state.get('error'),'zero-notice-unknown-no-replay')
 prepared=immutable(folder/'sender-prepared.json',raw(ref(path)));payload=encode({'kind':'zero-result-notice-run-intent-v1','intent':ref(intent),'sender':prepared,'sender_path':str(path)})
 # Exclusive claim: only the creator may invoke run, never an idempotent opener.
 with run.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
 p=invoke([sys.executable,str(ROOT/'skills/wecom-messenger/scripts/messenger.py'),'run','--job',str(path)],capture_output=True,text=True,timeout=360)
 immutable(folder/'notice-run-exit.json',encode({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
 r=client(order);immutable(result,encode({'kind':'zero-result-notice-confirmed-v1','intent':ref(intent),'client':r}));return r
