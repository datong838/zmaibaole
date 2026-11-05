"""Portable observed DOM shape with synthetic TEMP job/identity/open evidence.
No live ledger, work-directory evidence, UI, bridge or clipboard calls.
"""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from stop_loss_business_production_loader import d,stop,recovery as r,FIXTURE
import test_governance_dom as dom
import test_bridge_navigation as nav_fixture

def put(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.encoded(value));return d.ref(path)
class Parser(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
  f=nav_fixture.NavigationTests();f.setUp();self.addCleanup(f.doCleanups);self.job=copy.deepcopy(f.job);plan=copy.deepcopy(f.plan);plan.update(start='2026-10-21',end_exclusive='2026-10-22');pr=put(self.root/'plan.json',plan);self.job.update(start='2026-10-21',end_exclusive='2026-10-22',plan_path=pr['path'],plan_sha256=pr['sha256']);jr=put(self.root/'navigation-job.json',self.job)
  tree=dom.tree();d.g.date_input(tree)['attributes']['value']='2026/10/21 ～ 2026/10/21';tr=d.g.one([n for n in d.g.nodes(tree) if n.get('tag')=='tr' and n.get('children') and n['children'][0].get('tag')=='td'],'synthetic-row');cells=tr['children'];texts=['一般 门店商品缺货 ID: SYNTHETIC123','合成门店 门店ID：1000000000000002','合成商品 商品 ¥19.90 1000000000000001','已结束','门店商品不展示（截至10月21号24点）','2026/10/21','-']
  for cell,text in zip(cells,texts):cell['name']=text
  cells[1]['children'][0]['name']='合成门店';identity=[nav_fixture.leaf(self.job['identity']['provider'],'#provider'),nav_fixture.leaf('账户ID'+self.job['identity']['account_id'],'#account'),nav_fixture.leaf('我的客户经理'+self.job['identity']['manager']+' 切换公司','#manager')];tree['root']['children']+=copy.deepcopy(identity)
  tab={'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+d.g.RECORDS+'?groupid=123'};normal={'source':'local-dom-bridge','observed_at':'2026-10-22T10:00:00+00:00','tab_id':5,'tab':tab,'tree':tree,'not_business_capture':True};br=put(self.root/'before.json',normal);page=d.g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);self.row=page['rows'][0]
  detailroot=json.loads(FIXTURE.read_bytes())['root'];detailtree={'url':'https://life.douyin.com'+stop.PATH,'truncated':False,'root':{'tag':'div','selector':'#synthetic-document','name':'','attributes':{},'children':[detailroot,*copy.deepcopy(identity)]}};url='https://life.douyin.com'+stop.PATH+'?EnterFrom=home_violation_center&TaskID=ST0123456789abcdef01234567&groupid=123&life_account_biz_ids=&life_biz_view_id=22';self.raw={'source':'local-dom-bridge','observed_at':'2026-10-22T10:01:00+00:00','tab_id':5,'tab':{**tab,'url':url},'tree':detailtree,'not_business_capture':True};dr=put(self.root/'detail.json',self.raw)
  command={**d.g.detail_action(tree,self.row['notice_id'],start=self.job['start'],end_exclusive=self.job['end_exclusive']),'tabId':5};target=d.g.one([n for n in d.g.nodes(tree) if n.get('selector')==command['locator']['value']],'synthetic-open-target');self.call={'state':'confirmed','before':br,'command':command,'intent_at':'2026-10-22T10:00:30+00:00','result':{'kind':'navigation','version':d.nav.VERSION,'clicked':copy.deepcopy(target)}}
  query={'fingerprint':d.nav.tag(self.job),'tab_id':5,'approved_version':d.nav.VERSION,'phase':'capture-complete','business_progress_changed':False,'pages':[{**page,'observation':br}],'rows':page['rows']};qr=put(self.root/'records-query.json',query);self.manifest={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':jr,'query':qr},'tab_id':5,'approved_version':d.nav.VERSION};self.v=d.inputs(self.manifest);self.path=self.root/'governance-detail-operations'/d.nav.tag(self.job)/'state.json';self.s={'manifest':self.manifest,'fingerprint':d.nav.tag(self.job),'phase':'read-detail','last_error':r.ERROR,'cursor':0,'details':[],'current':{'notice_id':self.row['notice_id'],'normal_before':br},'calls':[self.call],'observations':[br,dr],'last_observation':dr};put(self.path,self.s)
 def parse(self):return stop.parse(self.raw,self.row,self.call,self.job)
 def test_new_context_keeps_original_table_status_and_excludes_marketing(self):
  facts,command=self.parse();self.assertEqual(facts['disposals'],[self.row['disposal']]);self.assertEqual(facts['effective_statuses'],[]);self.assertFalse(facts['detail_period_observed']);self.assertNotIn('effective_period',facts);self.assertEqual(facts['table_effectiveness_status'],'已结束');self.assertNotIn('开通体验补偿赔券',facts['public_recommendation']);self.assertIn('及时备货',facts['public_recommendation']);self.assertEqual(command['kind'],'navigation');self.assertEqual(facts['store_id'],'1000000000000002')
 def test_exact_route_pair_unknown_duplicate_host_path_fragment_refused(self):
  original=self.raw['tab']['url']
  for url in (original.replace('life_biz_view_id=22','life_biz_view_id=23'),original.replace('life_account_biz_ids=','life_account_biz_ids=x'),original+'&life_biz_view_id=22',original+'&TaskID=ST000000000000000000000000',original+'&other=x',original+'#x',original.replace('life.douyin.com','evil.example'),original.replace(stop.PATH,'/p/home'),original.replace('life_biz_view_id=22','life_biz_view_id='),original.replace('EnterFrom=home_violation_center','EnterFrom=x')):
   self.raw['tab']['url']=url
   with self.subTest(url=url),self.assertRaises(ValueError):self.parse()
 def test_product_store_notice_date_advice_or_open_mismatch_refused(self):
  original=copy.deepcopy(self.raw)
  for mode,cls,text in (('notice','value-Hil7yf','SYNTHETIC123'),('store','value-Hil7yf','合成门店（ID：1000000000000002）'),('product','id_text-muNBHv','1000000000000001'),('date','value-Hil7yf','2026-10-21 22:40'),('advice','content-RvpJDV',None)):
   self.raw=copy.deepcopy(original);node=d.g.one([n for n in d.g.nodes(self.raw['tree']) if n.get('attributes',{}).get('class')==cls and (not n.get('children') if text is None else d.g.text(n)==text)],'synthetic-mutation');node['name']='different'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.parse()
  self.raw=original;self.call['state']='unknown'
  with self.assertRaises(ValueError):self.parse()
 def test_consistent_changed_before_table_status_still_refused(self):
  before=d.document(self.call['before']);node=d.g.one([n for n in d.g.nodes(before['tree']) if n.get('selector')==self.row['cell_selectors']['处置生效状态']],'status');node['name']='已撤销';self.call['before']=put(self.root/'revoked-before.json',before);self.row=copy.deepcopy(self.row);self.row['effective_status']='已撤销'
  with self.assertRaisesRegex(ValueError,'business-context-status'):self.parse()
 def test_typed_original_contract_rejects_unknown_error_extra_call_phase_and_key(self):
  r.inputs(self.s,self.path,self.s['last_observation']['sha256'])
  for mode in ('unknown','error','extra','phase','key'):
   state=copy.deepcopy(self.s)
   if mode=='unknown':state['calls'][0]['state']='unknown'
   elif mode=='error':state['last_error']='different'
   elif mode=='extra':state['calls'].append(copy.deepcopy(state['calls'][0]))
   elif mode=='phase':state['phase']='normal'
   else:state['current']['notice_id']='different'
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.inputs(state,self.path,state['last_observation']['sha256'])
 def test_fresh_numeric_store_id_change_rejected_against_original_pinned_detail(self):
  m,v,facts,command=r.inputs(self.s,self.path,self.s['last_observation']['sha256']);tree=copy.deepcopy(self.raw['tree'])
  for node in d.g.nodes(tree):
   if isinstance(node.get('name'),str):node['name']=node['name'].replace('1000000000000002','1000000000000003')
  cmds=[{'op':'tabs'},{'op':'ping','tabId':5},{'op':'tree','tabId':5},{'op':'tabs'}];values=[[{'tabs':[self.raw['tab']]}],{'version':d.nav.VERSION,'safety':'DOM-only','governance_stop_loss_policy':'public-notice-return-v1'},tree,[{'tabs':[self.raw['tab']]}]];records=[{'command':c,'at':'2026-10-22T10:02:00+00:00','reply':{'ok':True,'result':value}} for c,value in zip(cmds,values)]
  with self.assertRaisesRegex(ValueError,'fresh-facts-changed'):r.verify_reads(records,self.s,m,v,facts,command)

class Recovery(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.path=self.root/'state.json';self.original={'manifest':{},'phase':'read-detail','last_error':r.ERROR,'fingerprint':'synthetic','cursor':0,'details':[],'current':{'notice_id':'notice'},'calls':[{'state':'confirmed'}],'observations':[{'path':'before','sha256':'a'},{'path':'detail','sha256':'b'}],'last_observation':{'path':'detail','sha256':'b'}};self.path.write_bytes(r.encoded(self.original));self.sha=r.sha(self.path.read_bytes());self.calls=[];self.m={'tab_id':5};self.v={'job':{},'query':{'rows':[{'notice_id':'notice'}]}};self.facts={'synthetic':True}
  self.addCleanup(patch.stopall);patch.object(r,'inputs',return_value=(self.m,self.v,self.facts,{})).start();patch.object(r,'verify_reads',side_effect=lambda records,*a: {'source':'synthetic','observed_at':'2026-10-23T10:00:00+00:00','records':records}).start()
 def invoke(self,c):self.calls.append(c);return {'ok':True,'result':{'synthetic':c['op']}}
 def reconcile(self,checkpoint=None):return r.reconcile(self.path,self.sha,'b',self.invoke,checkpoint)
 def test_four_reads_typed_delta_original_preserved_and_no_replay(self):
  before=self.path.read_bytes();result=self.reconcile();current=json.loads(self.path.read_bytes());r.verify_recovered(current,result['proof']);self.assertEqual(current['calls'],self.original['calls']);self.assertNotIn('last_error',current);self.assertEqual(Path(r.read(result['proof'])['original_journal']['path']).read_bytes(),before);self.assertEqual([c['op'] for c in self.calls],['tabs','ping','tree','tabs'])
  with self.assertRaisesRegex(ValueError,'already-recovered'):self.reconcile()
  self.assertEqual(len(self.calls),4)
 def test_failed_read_preserves_original_and_intent_no_second_read(self):
  before=self.path.read_bytes()
  def fail(c):self.calls.append(c);raise TimeoutError('read failed')
  with self.assertRaises(TimeoutError):r.reconcile(self.path,self.sha,'b',fail)
  self.assertEqual(self.path.read_bytes(),before)
  with self.assertRaisesRegex(ValueError,'incomplete-read-intent'):self.reconcile()
  self.assertEqual(len(self.calls),1)
 def test_proof_publish_crash_recommits_offline_and_forgery_rejected(self):
  def stop(_):raise RuntimeError('crash')
  with self.assertRaises(RuntimeError):self.reconcile(stop)
  self.assertEqual(r.sha(self.path.read_bytes()),self.sha);result=self.reconcile();self.assertEqual(len(self.calls),4);current=json.loads(self.path.read_bytes());current['calls'][0]['state']='unknown'
  with self.assertRaises(ValueError):r.verify_continuation(current)
 def test_source_changed_bad_sha_and_lock_zero_reads(self):
  with self.assertRaisesRegex(ValueError,'sha-mismatch'):r.reconcile(self.path,'0'*64,'b',self.invoke)
  self.assertFalse(self.calls)
  with (self.path.parent/'.lock').open('a') as lock:
   r.fcntl.flock(lock,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):self.reconcile()
  self.assertFalse(self.calls)

if __name__=='__main__':unittest.main()
