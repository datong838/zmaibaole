import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'scripts/dismiss_account_overlay.py';spec=importlib.util.spec_from_file_location('dismiss_account_overlay',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestDismiss(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/'source.json';self.ident={'provider':'服务商123456789','account_id':'123456789','manager':'某某'};self.source.write_text(json.dumps({'groupid':'12345','identity':self.ident}));self.digest=hashlib.sha256(self.source.read_bytes()).hexdigest();self.out=self.root/'intent.json';self.esc=0
  self.tree={'truncated':False,'root':{'tag':'body','children':[{'name':'服务商123456789 账户ID 123456789 我的客户经理 某某 退出登录','attributes':{'class':'UserCard-index-module__outer--test'},'children':[{'name':x} for x in ('账户ID','我的客户经理','切换公司','退出登录')]}]}}
  self.tabs=[{'windowId':2,'focused':True,'tabs':[{'tabId':1,'windowId':2,'active':True,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=12345','title':'抖音来客'}]}]
 def native(self,pid):
  outer=self
  class N:
   def foreground(self):pass
   def guard(self,title):assert title=='抖音来客'
   def escape(self):outer.esc+=1
  return N()
 def request(self,c):
  if c['op']=='tabs':return {'ok':True,'result':self.tabs}
  if c['op']=='tree':return {'ok':True,'result':self.tree if self.esc==0 or getattr(self,'stuck',False) else {'truncated':False,'root':{'tag':'body'}}}
  return {'ok':True,'result':{}}
 def run_it(self):return m.run(self.source,self.digest,1,42,self.out,self.request,self.native)
 def test_once_and_complete_reuse(self):
  self.assertEqual(self.run_it()['result'],'dismissed');self.assertEqual(self.esc,1);self.run_it();self.assertEqual(self.esc,1)
 def test_still_present_is_unknown_no_replay(self):
  self.stuck=True
  with self.assertRaisesRegex(ValueError,'still-present'):self.run_it()
  with self.assertRaisesRegex(ValueError,'unknown-no-replay'):self.run_it()
  self.assertEqual(self.esc,1)
 def test_other_dialog_never_escape(self):
  self.tree['root']['children'].append({'role':'dialog'})
  with self.assertRaisesRegex(ValueError,'other-dialog'):self.run_it()
  self.assertEqual(self.esc,0)
 def test_identity_change_never_escape(self):
  self.ident['account_id']='777777777';self.source.write_text(json.dumps({'groupid':'12345','identity':self.ident}));self.digest=hashlib.sha256(self.source.read_bytes()).hexdigest()
  with self.assertRaisesRegex(ValueError,'account-changed'):self.run_it()
  self.assertEqual(self.esc,0)
 def test_absent_no_key(self):
  self.tree={'truncated':False,'root':{'tag':'body'}};self.assertEqual(self.run_it()['result'],'already-absent');self.assertEqual(self.esc,0)
 def test_wrong_focus_never_escape(self):
  self.tabs[0]['focused']=False
  with self.assertRaisesRegex(ValueError,'focused-tab'):self.run_it()
  self.assertEqual(self.esc,0)
