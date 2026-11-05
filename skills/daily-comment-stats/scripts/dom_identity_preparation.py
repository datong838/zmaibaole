"""Idempotent identity-card display preparation, under the collector's same lock.
Library seam only: observe/hover are fixed caller transport functions, not data
callbacks or dynamic command names accepted from a user/CLI. No workflow tick.
"""
import fcntl,hashlib,json,os,re,sys,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
import dom_evidence as d
from readonly_tick_snapshot import decode
RESOURCE=ROOT/'runtime/workshop-director/browser-wecom.resource.lock'
KIND='daily-dom-identity-preparation-v1'
def need(v,e):
 if not v:raise ValueError(e)
def ref(p):
 p=Path(p);need(p.is_file()and p.is_absolute()and p.resolve()==p and not any(x.is_symlink()for x in(p,*p.parents)),'identity-preparation-canonical-file');return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def doc(r):
 need(ref(r['path'])==r,'identity-preparation-reference-changed');return json.loads(Path(r['path']).read_bytes())
def put(path,value):
 with path.open('x')as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 fd=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return ref(path)
def stamp():return {'wall_at':datetime.now(timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns()}
def checked_scope(job,reference,expected_url=None):
 scope=decode(doc(reference),job['tab_id'],job['window_id']);before=d.context(scope['before'],job['tab_id'],job['groupid']);after=d.context(scope['after'],job['tab_id'],job['groupid']);u=urlsplit(before['url']);need(before['url']==after['url']and before['windowId']==after['windowId']==job['window_id']and u.scheme=='https'and u.netloc=='life.douyin.com'and u.path=='/p/life_comment/management'and not u.fragment,'identity-preparation-route-changed');need(expected_url is None or before['url']==expected_url,'identity-preparation-continuity-lost');tree=scope['tree'];need(tree['url']=='https://life.douyin.com/p/life_comment/management'and scope['ping'].get('version')==d.VERSION and scope['ping'].get('safety')=='DOM-only','identity-preparation-version');ns=list(d.nodes(tree));need(not any(n.get('role')=='dialog'and re.search('安全验证|滑块验证|风险验证|账号异常|扫码登录',n.get('name',''))for n in ns),'identity-preparation-risk');need(not any(n.get('name')=='系统错误，请稍后再试'and 'life-core-message-content'in n.get('attributes',{}).get('class','').split()for n in ns),'identity-preparation-system-error');d.all_store_scope(tree);d.verified_review_filter(tree,job['date_range'])
 cards=[n for n in ns if 'UserCard-index-module__outer--'in n.get('attributes',{}).get('class','')]
 if cards:
  need(len(cards)==1,'identity-preparation-duplicate-card');d.identity(tree,job['identity']);return {'ready':True,'url':before['url'],'scope':reference,'identity':job['identity']}
 # Only an absent complete card may trigger display. A malformed/wrong card
 # above is a conflict, never repaired by choosing a different merchant.
 triggers=[n for n in ns if 'Profile-index-module__title--'in n.get('attributes',{}).get('class','')];trigger=d.unique(triggers,'account-trigger-unverified');need(trigger.get('name')==job['identity']['provider']and trigger.get('selector')and not trigger.get('disabled'),'account-trigger-disabled-or-provider-changed');return {'ready':False,'url':before['url'],'scope':reference,'command':{'op':'hover','tabId':job['tab_id'],'locator':{'by':'selector','value':trigger['selector']},'kind':'navigation'}}
def code_refs():return [ref(Path(__file__).absolute()),ref(Path(d.__file__).absolute()),ref(Path(sys.modules[decode.__module__].__file__).absolute())]
def prepare_identity(job,root,*,observe,hover,guard,resource_fd):
 """At most 3 fresh scopes/2 idempotent hovers in one continuous caller lock.
 Missing card after the finite burst returns pending. A later ordinary program
 invocation starts a new display epoch, rather than permanently exhausting a
 business-input key; it always starts with fresh scope and never replays input.
 """
 need(all(callable(x)for x in(observe,hover,guard)),'identity-preparation-fixed-callers-required');stat=os.fstat(resource_fd);need(RESOURCE.is_file()and not RESOURCE.is_symlink()and (stat.st_dev,stat.st_ino)==(RESOURCE.stat().st_dev,RESOURCE.stat().st_ino),'identity-preparation-original-resource-fd');fcntl.flock(resource_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 root=Path(root);need(root==Path(job['original_job']['path']).parent/'dom-identity-preparation','identity-preparation-original-output');need(root.resolve()==root and not any(x.is_symlink()for x in(root,*root.parents)),'identity-preparation-canonical-output');before=guard();code=code_refs();root.mkdir(exist_ok=True);indices=[int(x.name)for x in root.iterdir()if x.is_dir()and re.fullmatch(r'\d{4}',x.name)];folder=root/f'{max(indices,default=-1)+1:04d}';folder.mkdir();intent=put(folder/'intent.json',{'kind':KIND,'job':job,'guard':before,'code_refs':code,'started':stamp(),'environment_only':True,'business_inputs':0});samples=[];hovers=[];url=None
 for index in range(3):
  need(guard()==before,'identity-preparation-original-guard-drift');read_intent=put(folder/f'{index:02d}-read-intent.json',{'command':{'op':'readonly-scope','tabId':job['tab_id'],'windowId':job['window_id']},'at':stamp()});sample=observe(index,folder);facts=checked_scope(job,sample['scope'],url);url=facts['url'];samples.append({'intent':read_intent,'observed':sample,'checked':facts,'at':stamp()});put(folder/f'{index:02d}-read-result.json',samples[-1])
  if facts['ready']:
   need(guard()==before and code_refs()==code,'identity-preparation-original-guard-drift');receipt=put(folder/'complete.json',{'kind':KIND,'intent':intent,'samples':samples,'hovers':hovers,'final_scope':sample['scope'],'full_identity':job['identity'],'completed':stamp(),'business_inputs':0,'environment_hover_attempts':len(hovers),'guard_after':before,'code_refs':code,'capture_authority':False});return {'state':'ready','scope':sample['scope'],'preparation':receipt,'same_resource_fd':resource_fd}
  if index==2:break
  need(guard()==before,'identity-preparation-original-guard-drift');command=facts['command'];hover_intent=put(folder/f'{index:02d}-hover-intent.json',{'kind':'idempotent-provider-display-only-v1','command':command,'scope':sample['scope'],'at':stamp(),'business_inputs':0})
  # A hover reply is a dispatch observation, never full-identity success.
  # Even an unknown hover effect is followed by fresh scope; no business input
  # is retried. If still absent the next bounded hover is a new fresh display.
  reply=hover(command,index,folder);hovers.append({'intent':hover_intent,'reply':reply,'at':stamp()});put(folder/f'{index:02d}-hover-result.json',hovers[-1])
 pending=put(folder/'pending.json',{'kind':KIND,'intent':intent,'samples':samples,'hovers':hovers,'at':stamp(),'reason':'full-identity-card-not-visible-after-bounded-display','business_inputs':0});return {'state':'pending','preparation':pending,'same_resource_fd':resource_fd}
def prepare_and_consume(job,root,*,observe,hover,guard,resource_fd,consume):
 """One normal program call: final full-identity scope -> consumer, same FD.
 The fixed collector supplies consume; no CLI accepts or imports caller code.
 """
 need(callable(consume),'identity-preparation-fixed-consumer-required');result=prepare_identity(job,root,observe=observe,hover=hover,guard=guard,resource_fd=resource_fd)
 if result['state']!='ready':return result
 need(guard()==doc(doc(result['preparation'])['intent'])['guard'],'identity-preparation-preconsume-guard-drift');result['consumed']=consume(result['scope'],result['preparation']);return result
