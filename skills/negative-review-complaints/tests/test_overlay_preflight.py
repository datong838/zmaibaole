"""Synthetic DOM/request doubles. No live source, bridge or native invocation."""
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('overlay_candidate',Path(__file__).resolve().parents[1]/'scripts/account_overlay_preflight.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.calls=[];self.card_shown=True;self.blocked=True;self.hover_mode='success';self.identity={'provider':'服务商123456789','account_id':'123456789012','manager':'synthetic'};self.scope={'tabId':10,'windowId':20,'groupid':'123'};self.url='https://life.douyin.com/p/life_comment/management?groupid=123';self.base={**self.scope,'reviews':[{'card':'#review','review_key':'123:review'}]};self.build=h.content_identity();self.manifest={'capture_key':'same-capture-key','review_keys':['123:review']}
  source={'groupid':'123','identity':self.identity};job={'identity':self.identity};tab={**{k:self.scope[k] for k in ('tabId','windowId')},'url':self.url,'active':True,'allowed':True,'title':'抖音来客'};self.tab=tab
  for k,v in [('source',source),('job',job),('profile',{}),('envelope',{}),('page',{'tab':tab})]:self.manifest[k]=self.write(self.root/(k+'.json'),v)
  self.mref=self.write(self.root/'manifest.json',self.manifest)
  patches=[patch.object(h,'RUNTIME',self.root/'.account-hover-preflight'),patch.object(h.rc,'command_from_inputs',return_value=copy.deepcopy(self.base)),patch.object(h.rc.normal,'context',side_effect=lambda p,g:(p['tab'],p['tree'])),patch.object(h.rc.normal,'navigation_probe',return_value={}),patch.object(h.rc.normal,'public_identity',side_effect=lambda t,i: h.need(t.get('identity')==i,'identity-mismatch')),patch.object(h.region,'checked',side_effect=lambda r,c:h.need(r.get('ok') is True and r.get('result',{}).get('scope')==self.scope,'proof-invalid') or r['result'])]
  for p in patches:p.start();self.addCleanup(p.stop)
 def write(self,p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v));return h.ref(p)
 def node(self,name='',cl='',selector='',children=()):return {'name':name,'tag':'div','selector':selector,'attributes':{'class':cl},'children':list(children)}
 def tree(self):
  trigger=self.node(self.identity['provider'],'src-components-HeaderV2-components-Profile-index-module__title--fixture','#trigger');self.card=self.node('', 'src-components-HeaderV2-components-UserCard-index-module__outer--fixture','#card',[self.node(x) for x in ['账户ID','我的客户经理','切换公司','退出登录']]);wrap=self.node('', 'src-components-HeaderV2-components-Profile-index-module__wrap-profile--fixture','#wrapper',[trigger]+([self.card] if self.card_shown else []));return {'kind':'DOM-derived semantic tree (not native AX)','truncated':False,'url':'https://life.douyin.com/p/life_comment/management','identity':self.identity,'root':self.node(children=[wrap])}
 def response(self):return {'ok':True,'result':{'action':'account-hover-exit-events-dispatched','event_sequence':['card:mouseout','card:mouseleave','wrapper:mouseleave'],'related_target':'document.body','trusted_event_fabrication':False,'business_clicks':False,'closure_verified':False,'requires_readonly_tree_recheck':True}}
 def request(self,c):
  self.calls.append(copy.deepcopy(c));op=c['op']
  if op=='tabs':return {'ok':True,'result':[{'windowId':20,'focused':True,'tabs':[self.tab]}]}
  if op=='ping':return {'ok':True,'result':{'version':self.build['version'],'content_build':self.build['build'],'safety':'DOM-only'}}
  if op=='tree':return {'ok':True,'result':self.tree()}
  if op=='find':return {'ok':True,'result':[copy.deepcopy(self.card)]}
  if op=='dom-region-proof':
   if self.card_shown and self.blocked:return {'ok':False,'error':'region-painted-external-overlap:'+json.dumps({'tag':'DIV','class':self.card['attributes']['class'],'selector':'html > body > div'})}
   return {'ok':True,'result':{'scope':self.scope}}
  if op=='hover':
   journal=next((self.root/'.account-hover-preflight').glob('*.json'));saved=json.loads(journal.read_text());self.assertEqual(saved['state'],'unknown');self.assertEqual(saved['command'],c)
   if self.hover_mode=='unknown':self.card_shown=False;raise RuntimeError('timeout-unknown')
   self.card_shown=False
   if self.hover_mode=='bad-reply':return {'ok':True,'result':{'closure_verified':True}}
   return self.response()
  raise AssertionError(c)
 def ensure(self,**kw):return h.ensure(self.mref,self.request,**kw)
 def hovers(self):return [c for c in self.calls if c['op']=='hover']
 def journal(self):return json.loads(next((self.root/'.account-hover-preflight').glob('*.json')).read_text())
 def test_one_exit_persistent_intent_exact_command_and_fresh_close(self):
  out=self.ensure();self.assertTrue(out['ready']);self.assertEqual(len(self.hovers()),1);self.assertEqual(out['capture_key'],'same-capture-key');self.assertTrue(self.journal()['closure_verified']);self.assertTrue(any(c['op']=='dom-region-proof' for c in self.calls));self.ensure();self.assertEqual(len(self.hovers()),1)
 def test_absent_or_present_not_blocking_zero_input(self):
  self.card_shown=False;self.ensure();self.assertEqual(self.hovers(),[])
  self.card_shown=True;self.blocked=False;self.ensure();self.assertEqual(self.hovers(),[]);self.assertFalse(self.journal()['closure_verified'])
 def test_unknown_then_readonly_effect_reconcile_never_replay(self):
  self.hover_mode='unknown'
  with self.assertRaisesRegex(RuntimeError,'unknown'):self.ensure()
  self.assertEqual(self.journal()['state'],'unknown');self.ensure();self.assertEqual(len(self.hovers()),1);self.assertTrue(self.journal()['closure_verified'])
 def test_bad_reply_raw_is_saved_before_validation(self):
  self.hover_mode='bad-reply'
  with self.assertRaisesRegex(ValueError,'reply-unreviewed'):self.ensure()
  saved=self.journal();raw=h.document(saved['reply']);self.assertEqual(raw['response']['result'],{'closure_verified':True});self.assertEqual(len(self.hovers()),1)
 def test_other_blocker_or_bad_identity_never_hover(self):
  original=self.request
  def bad(c):
   r=original(c)
   if c['op']=='dom-region-proof':r={'ok':False,'error':'region-painted-external-overlap:'+json.dumps({'tag':'DIV','class':'other-popup','selector':'#other'})}
   return r
  with self.assertRaisesRegex(ValueError,'not-usercard'):h.ensure(self.mref,bad)
  with patch.object(h.rc.normal,'public_identity',side_effect=ValueError('identity')):
   with self.assertRaises(ValueError):self.ensure()
  self.assertEqual(self.hovers(),[])
 def test_unknown_capture_blocks_all_requests(self):
  self.write(self.root/'.review-region-state'/'original.json',{'state':'unknown'})
  with self.assertRaisesRegex(ValueError,'capture-intent'):self.ensure()
  self.assertEqual(self.calls,[])
 def test_same_source_unknown_cannot_use_other_key(self):
  self.hover_mode='unknown'
  with self.assertRaises(RuntimeError):self.ensure()
  self.card_shown=True;self.scope['windowId']=21
  with self.assertRaises(ValueError):self.ensure()
  self.assertEqual(len(self.hovers()),1)
 def test_existing_confirmed_intent_adopt_is_readonly(self):
  before=self.write(self.root/'manual-before.json',{'ok':True,'result':self.tree()});trigger=self.tree()['root']['children'][0]['children'][0];cmd=h.command(self.scope,self.identity,trigger);adopt=self.write(self.root/'manual-intent.json',{'state':'confirmed','command':cmd,'reply':self.response(),'source_sha256':self.manifest['source']['sha256'],'before':before});self.card_shown=False
  out=self.ensure(adopt=adopt);self.assertTrue(out['adopted']);self.assertEqual(self.hovers(),[]);self.ensure(adopt=adopt);self.assertEqual(self.hovers(),[])
 def test_wrong_adoption_and_ping_or_window_refused(self):
  self.card_shown=False;adopt=self.write(self.root/'invalid-adopt.json',{'state':'unknown'})
  with self.assertRaises(ValueError):self.ensure(adopt=adopt)
  original=self.request
  def badping(c):
   r=original(c)
   if c['op']=='ping':r['result']['content_build']='wrong'
   return r
  with self.assertRaisesRegex(ValueError,'not-loaded'):h.ensure(self.mref,badping)
  self.assertEqual(self.hovers(),[])
 def test_dialog_and_foreign_find_refuse_before_hover(self):
  original=self.request
  def otherfind(c):
   r=original(c)
   if c['op']=='find':r['result'][0]['selector']='#other-node'
   return r
  with self.assertRaisesRegex(ValueError,'not-same'):h.ensure(self.mref,otherfind)
  original_tree=self.tree
  def dialogtree():
   t=original_tree();t['root']['children'].append({'role':'dialog','children':[]});return t
  with patch.object(self,'tree',dialogtree),self.assertRaisesRegex(ValueError,'dialog-present'):self.ensure()
  self.assertEqual(self.hovers(),[])
 def test_completed_once_reappeared_card_holds_no_second_hover(self):
  self.ensure();self.card_shown=True
  with self.assertRaisesRegex(ValueError,'no-replay'):self.ensure()
  self.assertEqual(len(self.hovers()),1)
 def test_original_intent_and_missing_command_cannot_be_reinterpreted(self):
  self.hover_mode='unknown'
  with self.assertRaises(RuntimeError):self.ensure()
  path=next((self.root/'.account-hover-preflight').glob('*.json'));state=json.loads(path.read_text());state.pop('command');self.write(path,state)
  with self.assertRaisesRegex(ValueError,'command-missing'):self.ensure()
  self.assertEqual(len(self.hovers()),1)
 def test_source_lock_and_capturekey_remain_original(self):
  directory=self.root/'.account-hover-preflight';directory.mkdir()
  with (directory/'.source.lock').open('a') as lock:
   h.fcntl.flock(lock,h.fcntl.LOCK_EX|h.fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):self.ensure()
  self.assertEqual(self.calls,[]);self.assertEqual(h.document(self.mref)['capture_key'],'same-capture-key')
 def test_same_source_copy_cannot_create_another_hover_journal(self):
  self.hover_mode='unknown'
  with self.assertRaises(RuntimeError):self.ensure()
  copied=dict(self.manifest);copied['source']=self.write(self.root/'copy-source.json',h.document(self.manifest['source']));copied_manifest=self.write(self.root/'copy-manifest.json',copied)
  with self.assertRaisesRegex(ValueError,'binding-required'):h.ensure(copied_manifest,self.request)
  self.assertEqual(len(self.hovers()),1)
 def test_different_scope_or_source_midread_stops(self):
  original=self.request
  def changed(c):
   r=original(c)
   if c['op']=='tree':Path(self.manifest['source']['path']).write_text('{}')
   return r
  with self.assertRaisesRegex(ValueError,'input-reference'):h.ensure(self.mref,changed)
  self.assertEqual(self.hovers(),[])
if __name__=='__main__':unittest.main()
