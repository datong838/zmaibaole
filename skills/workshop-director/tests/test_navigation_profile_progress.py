"""Self-contained synthetic TEMP plan/receipt/public DOM; no UI or real ledger."""
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'skills/workshop-director/scripts';NAV=ROOT/'skills/violation-notifier/scripts'
spec=importlib.util.spec_from_file_location('profile_candidate_helper',S/'navigation_profile_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sem=types.ModuleType('profile_candidate_semantic');sem.__file__=str(S/'semantic_progress.py');exec(compile((S/'semantic_progress.py').read_text(),sem.__file__,'exec'),sem.__dict__);sem._navigation_profile_path=S/'navigation_profile_progress.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.path=self.root/'center-navigation.json';self.identity={'provider':'服务商123456789','account_id':'12345678901','manager':'合成经理'}
  self.plan={'company':'合成公司','groupid':'123','start':'2026-10-21','end_exclusive':'2026-10-22','browser_backend':'local-dom-bridge','production_enabled':False,'platform_writes':False,'send_target':'测试群请忽略','has_new_dates':True};pp=self.put('plan.json',self.plan)
  receipt={'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','work_order_id':'synthetic-id','company':'合成公司','groupid':'123','account_verified':True,'identity':self.identity,'identity_before':self.identity};rp=self.put('receipt.json',receipt)
  self.job={'company':'合成公司','groupid':'123','start':'2026-10-21','end_exclusive':'2026-10-22','account_verified':True,'identity':self.identity,'source_work_order_id':'synthetic-id','plan_path':pp['path'],'plan_sha256':pp['sha256'],'identity_receipt':rp['path'],'identity_receipt_sha256':rp['sha256']};self.put('navigation-job.json',self.job);self.fp=hashlib.sha256(json.dumps(self.job,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  self.before=self.observation('/p/home','2026-10-22T10:00:00+00:00');self.final=self.observation('/p/governance/home_violation_center','2026-10-22T10:01:00+00:00');self.br=self.put('navigation-evidence/002-openCenter-123456789abc.json',self.before);self.fr=self.put('navigation-evidence/003-observeCenter-abcdef123456.json',self.final)
  self.state={'version':1,'phase':'profileRequired','waiting_for':'live-violation-analysis-date-and-pagination-profile','profile_accepted':False,'business_progress_changed':False,'production_enabled':False,'platform_writes':False,'zero_verified':False,'fingerprint':self.fp,'company':'合成公司','groupid':'123','start':'2026-10-21','end_exclusive':'2026-10-22','tab_id':5,'identity_verified_at':'2026-10-22T10:00:05+00:00','observations':[self.br,self.fr],'last_tree':self.fr,'calls':[{'key':'2:openCenter','state':'confirmed','intent_at':'2026-10-22T10:00:10+00:00','before':self.br,'command':{'op':'click','kind':'navigation','tabId':5,'locator':{'by':'selector','value':'#center'}},'result':{'clicked':{'name':'违规中心','selector':'#center','disabled':False},'kind':'navigation','version':'dom-only-20261021-11'}}]};self.save()
 def put(self,name,value):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False));return {'path':str(p),'sha256':sha(p)}
 def save(self):self.path.write_text(json.dumps(self.state,ensure_ascii=False))
 def observation(self,route,at):
  leaves=[{'name':self.identity['provider'],'selector':'#provider','children':[]},{'name':'账户ID'+self.identity['account_id'],'selector':'#account','children':[]},{'name':'我的客户经理'+self.identity['manager']+' 切换公司','selector':'#manager','children':[]},{'name':'违规中心','selector':'#center','children':[]}]
  return {'source':'local-dom-bridge','observed_at':at,'company':'合成公司','groupid':'123','tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+route+'?groupid=123'},'tree':{'url':'https://life.douyin.com'+route,'truncated':False,'root':{'children':leaves}},'navigation_fingerprint':self.fp,'plan_sha256':self.job['plan_sha256'],'not_business_capture':True,'name_text_limit':800,'full_field_text_verified':False}
 def verify(self,role='violation_operator'):
  self.save();return m.verify(self.state,self.path,role=role,navigation_directory=NAV)
 def update_final(self,fn):
  fn(self.final);r=self.put('navigation-evidence/003-observeCenter-abcdef123456.json',self.final);self.state['observations'][-1]=r;self.state['last_tree']=r
 def test_complete_boundary_is_pending_zero_tokens_not_date_profile_or_business(self):
  p=self.verify();self.assertFalse(p['business_progress_changed']);self.assertFalse(p['profile_accepted']);self.assertFalse(p['dates_queried']);self.assertFalse(p['completion_claimed']);out=sem.extract(self.state,'violation_operator',self.path);self.assertEqual(out['tokens'],{});self.assertEqual(out['binding'],{'fingerprint':self.fp,'tab_id':5});self.assertEqual(out['profile_review_pending'],p)
 def test_other_role_and_unknown_phase_reject(self):
  with self.assertRaises(ValueError):self.verify('complaint_operator')
  self.state['phase']='profile-required'
  with self.assertRaises(ValueError):self.verify()
 def test_unknown_unconfirmed_error_hold_and_business_flags_reject(self):
  original=copy.deepcopy(self.state)
  for change in ('unknown','unconfirmed','last_error','hold','production_enabled','platform_writes','zero_verified','profile_accepted','business_progress_changed'):
   self.state=copy.deepcopy(original)
   if change in ('unknown','unconfirmed'):self.state['calls'][0]['state']=change
   else:self.state[change]=True
   with self.subTest(change=change),self.assertRaises(ValueError):self.verify()
 def test_bad_final_reference_or_not_last_ref_reject(self):
  self.state['last_tree']={**self.fr,'sha256':'0'*64}
  with self.assertRaises(ValueError):self.verify()
  self.state['last_tree']=self.fr;Path(self.fr['path']).write_text('{}')
  with self.assertRaises(ValueError):self.verify()
 def test_identity_provider_account_manager_and_risk_reject(self):
  original=copy.deepcopy(self.final)
  for i,text in ((0,'服务商999999999'),(1,'账户ID99999999999'),(2,'我的客户经理错误 切换公司')):
   self.final=copy.deepcopy(original);self.update_final(lambda o:o['tree']['root']['children'][i].update(name=text))
   with self.subTest(i=i),self.assertRaises(ValueError):self.verify()
  self.final=copy.deepcopy(original);self.update_final(lambda o:o['tree']['root']['children'].append({'name':'风险验证','children':[]}))
  with self.assertRaises(ValueError):self.verify()
 def test_wrong_route_group_window_company_plan_or_fingerprint_reject(self):
  original=copy.deepcopy(self.final)
  for field in ('route','group','window','company','plan','fingerprint'):
   self.final=copy.deepcopy(original)
   def alter(o):
    if field=='route':o['tab']['url']='https://life.douyin.com/p/home?groupid=123';o['tree']['url']='https://life.douyin.com/p/home'
    elif field=='group':o['tab']['url']=o['tab']['url'].replace('groupid=123','groupid=999')
    elif field=='window':o['tab']['windowId']=9
    elif field=='company':o['company']='其他公司'
    elif field=='plan':o['plan_sha256']='0'*64
    else:o['navigation_fingerprint']='0'*64
   self.update_final(alter)
   with self.subTest(field=field),self.assertRaises(ValueError):self.verify()
 def test_bad_command_reply_or_duplicate_center_call_reject(self):
  original=copy.deepcopy(self.state)
  for field in ('selector','name','version','before','duplicate','input'):
   self.state=copy.deepcopy(original);c=self.state['calls'][0]
   if field=='selector':c['command']['locator']['value']='#other'
   elif field=='name':c['result']['clicked']['name']='其他'
   elif field=='version':c['result']['version']='unknown'
   elif field=='before':c['before']=self.fr
   elif field=='input':c['command']['op']='type'
   else:self.state['calls'].append(copy.deepcopy(c))
   with self.subTest(field=field),self.assertRaises(ValueError):self.verify()
 def test_receipt_and_plan_bytes_changed_reject(self):
  for f in ('receipt.json','plan.json'):
   p=self.root/f;raw=p.read_bytes();p.write_text('{}')
   with self.subTest(f=f),self.assertRaises(ValueError):self.verify()
   p.write_bytes(raw)
 def test_wrong_canonical_name_or_copy_directory_or_symlink_reject(self):
  self.save();other=self.root/'copy.json';other.write_bytes(self.path.read_bytes())
  with self.assertRaises(ValueError):m.verify(self.state,other,role='violation_operator',navigation_directory=NAV)
  copied=self.root/'copied';copied.mkdir();(copied/'center-navigation.json').write_bytes(self.path.read_bytes());(copied/'navigation-job.json').write_bytes((self.root/'navigation-job.json').read_bytes())
  with self.assertRaisesRegex(ValueError,'plan-directory-conflict'):m.verify(self.state,copied/'center-navigation.json',role='violation_operator',navigation_directory=NAV)
  link=self.root/'alias';link.symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(ValueError):m.verify(self.state,link/'center-navigation.json',role='violation_operator',navigation_directory=NAV)
 def test_timestamp_and_truncated_observations_reject(self):
  self.update_final(lambda o:o.update(observed_at='2026-10-22T09:00:00+00:00'))
  with self.assertRaises(ValueError):self.verify()
  self.update_final(lambda o:o.update(observed_at='2026-10-22T10:01:00'))
  with self.assertRaises(ValueError):self.verify()
  self.update_final(lambda o:o.update(observed_at='2026-10-22T10:01:00+00:00'));self.update_final(lambda o:o['tree'].update(truncated=True))
  with self.assertRaises(ValueError):self.verify()
 def test_hover_menu_center_normal_confirmed_chain_is_still_zero_tokens(self):
  account=copy.deepcopy(self.before);account['observed_at']='2026-10-22T09:59:00+00:00';ar=self.put('navigation-evidence/000-account-111111111111.json',account)
  menu=copy.deepcopy(self.before);menu['observed_at']='2026-10-22T09:59:30+00:00';menu['tree']['root']['children'].append({'name':'经营保障','selector':'#menu','children':[]});mr=self.put('navigation-evidence/001-menu-222222222222.json',menu)
  def call(key,op,label,selector,before,at):
   result={'kind':'navigation','hovered' if op=='hover' else 'clicked':{'name':label,'selector':selector}}
   if op=='click':result['version']='dom-only-20261021-11'
   return {'key':key,'state':'confirmed','intent_at':at,'before':before,'command':{'op':op,'kind':'navigation','tabId':5,'locator':{'by':'selector','value':selector}},'result':result}
  self.state['calls']=[call('0:account','hover',self.identity['provider'],'#provider',ar,'2026-10-22T09:59:01+00:00'),call('1:menu','click','经营保障','#menu',mr,'2026-10-22T09:59:31+00:00')]+self.state['calls'];self.state['observations']=[ar,mr]+self.state['observations'];p=self.verify();self.assertEqual(p['original_confirmed_calls'],3);self.assertEqual(sem.extract(self.state,'violation_operator',self.path)['tokens'],{})
 def test_noncommand_intermediate_observation_cannot_cross_window(self):
  raw=copy.deepcopy(self.before);raw['observed_at']='2026-10-22T10:00:30+00:00';raw['tab']['windowId']=99;ref=self.put('navigation-evidence/002-observeCenter-aaaaaaaaaaaa.json',raw);self.state['observations'].insert(1,ref)
  with self.assertRaisesRegex(ValueError,'observation-window-conflict'):self.verify()
 def test_old_center_profile_and_alias_helper_ASTs_unchanged(self):
  import ast
  def bodies(file):return {n.name:ast.dump(n) for n in ast.parse(file.read_text()).body if isinstance(n,ast.FunctionDef)}
  a=bodies(HERE/'fixtures/navigation-profile/semantic_progress.py.before');b=bodies(S/'semantic_progress.py');self.assertEqual({k for k in a if a[k]!=b[k]},{'extract'});self.assertEqual(b['verified_center_profile_pending'],a['verified_center_profile_pending']);self.assertEqual(b['automatic_tokens'],a['automatic_tokens'])
if __name__=='__main__':unittest.main()
