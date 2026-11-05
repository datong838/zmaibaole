"""Temporary-only switch-read journal fixture; never imports a UI driver."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
OP=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(OP))
import switch_read_recovery as m
assert Path(m.__file__).resolve()==OP/'switch_read_recovery.py'
class RecoveryFixture(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name).resolve();self.file=self.p/'workflow.json';self.jobpath=self.p/'work-order.json'
  self.ident={'provider':'服务商123456789','account_id':'12345678901','manager':'甲'};self.other={**self.ident,'account_id':'22345678901','manager':'乙'}
  self.job={'action':'acquire','work_order_id':'abc','company':'目标公司','groupid':'222','date_range':{'start':'2026-10-21','end':'2026-10-21'},'source_dir':str(self.p/'export'),'workflow_path':str(self.file),'work_order_path':str(self.jobpath),'identity_contract':'merchant-v2','provider_baseline':self.ident['provider'],'known_company_identities':{'111':self.ident,'222':self.other},'identity_baseline':self.other}
  calls=[]
  for i,phase,label,kind in ((1,'chooseCompany','目标公司','company'),(2,'confirmSwitch','确认','company-confirm')):
   calls.append({'key':str(i)+':'+phase,'phase':phase,'state':'confirmed','at':'2026-10-22T10:00:00+00:00','command':{'op':'click','tabId':9,'kind':kind,'locator':{'by':'selector','value':'#'+phase}},'result':{'clicked':{'selector':'#'+phase,'name':label,'disabled':phase=='confirmSwitch'}}})
  calls.insert(0,{'key':'focus','phase':'account','state':'confirmed','command':{'op':'activate','tabId':9},'result':{'windowId':8}})
  old=self.p/'0005-verifySwitch.json';old.write_text(json.dumps({'truncated':False,'url':'https://life.douyin.com/p/home','root':{'name':'old','children':[]}}))
  self.s={'version':1,'backend':'local-dom-bridge','work_order_id':'abc','fingerprint':m.fingerprint(self.job),'company':self.job['company'],'groupid':'222','date_range':self.job['date_range'],'state':'running','phase':'verifySwitch','revision':5,'tab_id':9,'initial_groupid':'111','entry_groupid':'111','entry_identity':self.ident,'provider_baseline':self.ident['provider'],'identity_contract':'merchant-v2','calls':calls,'checkpoints':[],'last_tree':m.ref(old),'last_error':{'code':'tab-context-changed-during-read','message':'tab-context-changed-during-read','at':'2026-10-22T10:00:01+00:00'}}
  self.file.write_bytes(m.encoded(self.s));self.jobpath.write_bytes(m.encoded(self.job));self.original=self.file.read_bytes();self.original_sha=m.sha(self.original);self.seen=[]

 def tabs(self,gid='222',host='life.douyin.com'):
  return [{'windowId':8,'focused':True,'tabs':[{'tabId':9,'windowId':8,'active':True,'allowed':True,'url':'https://'+host+'/p/home?groupid='+gid}]}]

 def tree(self):
  return {'url':'https://life.douyin.com/p/home','truncated':False,'root':{'children':[{'tag':'span','name':'目标公司','attributes':{'class':'AccountInfo-module__companyName--xxx'},'children':[]},{'name':self.ident['provider'],'attributes':{'class':'Profile-index-module__title--xxx'},'children':[]}]}}

 def invoke(self,cmd):
  self.seen.append(cmd)
  if cmd['op']=='tabs':return self.tabs()
  if cmd['op']=='tree':return self.tree()
  if cmd['op']=='ping':return {'version':'dom-only-20261021-11','safety':'DOM-only'}
  raise AssertionError('MUTATION '+str(cmd))

 def runrepair(self,invoke=None):return m.reconcile(self.jobpath,self.original_sha,invoke or self.invoke)

