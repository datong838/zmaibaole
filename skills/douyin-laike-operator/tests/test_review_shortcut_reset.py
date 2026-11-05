"""Portable synthetic reviewed shortcut and durable-phase tests; no bridge/UI."""
import sys,copy,json,unittest,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/douyin-laike-operator/scripts').is_dir());sys.path[:0]=[str(R/'skills/douyin-laike-operator/scripts'),str(R/'skills/chrome-dom-export/scripts')]
P=R/'skills/douyin-laike-operator/scripts/bridge-workflow.py';spec=importlib.util.spec_from_file_location('shortcut_reset_reviewed_workflow',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
LABELS=('好评（4-5心）','中差评（1-3心）','未回复','已回复','抖音消费','非抖音消费');URL='https://life.douyin.com/p/life_comment/management'
def tree(selected=True):
 children=[]
 for i,label in enumerate(LABELS):
  if i in (2,4):children.append({'tag':'div','role':'generic','name':'','attributes':{'class':'divider-t1NIxB'},'selector':'#root > div > .divider'+str(i),'children':[],'disabled':False})
  children.append({'tag':'div','role':'generic','name':label,'attributes':{'class':'option-YmRyn3'+(' isSelected-ov8pOi' if selected and i==1 else '')},'selector':'#root > div > .option'+str(i),'children':[],'disabled':False})
 return {'truncated':False,'url':URL,'root':{'tag':'div','name':' '.join(LABELS),'role':'generic','selector':'#root > div','attributes':{'class':'otherSelectGroup-PCCUqW'},'children':children}}
class Shortcuts(unittest.TestCase):
 def workflow(self,t):
  w=m.Workflow.__new__(m.Workflow);w.s={'state':'running','phase':'verifyFilter','revision':1,'calls':[],'tab_id':11,'initial_groupid':'17','date_range':{'start':'2026-10-19','end':'2026-10-19'},'checkpoints':[]};w.job={'groupid':'17','action':'acquire'};w.current={'url':URL+'?groupid=17','windowId':12,'groupid':'17'};w.tree=t;w.tick_snapshot=lambda:({'ping':{'version':m.VERSION,'safety':'DOM-only'},'tree':w.tree,'after':[]},[],w.current);w.source_context=lambda _:w.current;w.remember_tree=lambda x:x;w.save=lambda:None;w.settle_review_filter=lambda x,_:x;w.input=[]
  def call(cmd):w.input.append(cmd);return {'clicked':copy.deepcopy(w.tree['root']['children'][1]),'kind':'filter','version':m.VERSION}
  w.call=call;return w
 def guards(self):return patch.multiple(m,all_store_scope=lambda _:None,verified_review_filter=lambda *_:{'page_filtered':1})
 def test_saved_public_scope_fixture(self):
  v=json.loads((Path(__file__).parent/'fixtures/observed-shortcut-scope.json').read_text());self.assertEqual(m.review_shortcut_reset_target(v)['name'],LABELS[1])
 def test_default_path_remains_one_read_zero_input(self):
  w=self.workflow(tree(False))
  with self.guards():w.tick()
  self.assertEqual(w.s['phase'],'openExportMenu');self.assertEqual(w.input,[])
 def test_selected_negative_exact_scope_only(self):
  t=tree();self.assertEqual(m.review_shortcut_reset_target(t)['name'],LABELS[1]);self.assertIsNone(m.review_shortcut_reset_target(tree(False)))
  for mutation in ('duplicate','parent','divider','disabled','children','route'):
   v=copy.deepcopy(t)
   if mutation=='duplicate':v['root']['children'].append(copy.deepcopy(v['root']['children'][1]))
   elif mutation=='parent':v['root']['attributes']['class']='unknown'
   elif mutation=='divider':v['root']['children'][2]['attributes']['class']='unknown'
   elif mutation=='disabled':v['root']['children'][1]['disabled']=True
   elif mutation=='children':v['root']['children'][1]['children']=[{'name':'nested'}]
   else:v['url']='https://life.douyin.com/p/home'
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):m.review_shortcut_reset_target(v)
 def test_nonnegative_or_multiple_selection_rejected(self):
  for selected in (False,True):
   v=tree(selected);v['root']['children'][0]['attributes']['class']+=' isSelected-ov8pOi'
   with self.assertRaisesRegex(ValueError,'nondefault-review-shortcut'):m.review_shortcut_reset_target(v)
 def test_normal_phase_sequence_only_one_toggle_and_fresh_defaults(self):
  w=self.workflow(tree())
  with self.guards(),patch('review_filter_loading.validate_filter_values') as dates:
   w.tick();self.assertEqual(w.s['phase'],'clearReviewNegativeShortcut');self.assertEqual(w.input,[])
   w.tick();self.assertEqual(w.s['phase'],'verifyClearedReviewShortcut');self.assertEqual(len(w.input),1);self.assertEqual(w.s['calls'][0]['state'],'confirmed')
   w.tree=tree(False);w.tick();self.assertEqual(w.s['phase'],'verifyFilter');w.tick();self.assertEqual(w.s['phase'],'openExportMenu');self.assertEqual(len(w.input),1);self.assertGreaterEqual(dates.call_count,3)
 def test_unknown_written_before_transport_and_never_replayed(self):
  w=self.workflow(tree());w.s['phase']='clearReviewNegativeShortcut'
  def failed(cmd):self.assertEqual(w.s['calls'][0]['state'],'unknown');w.input.append(cmd);raise ValueError('lost reply')
  w.call=failed
  with self.guards(),patch('review_filter_loading.validate_filter_values'):
   with self.assertRaisesRegex(ValueError,'lost reply'):w.tick()
   w.tree=tree(False)
   with self.assertRaisesRegex(ValueError,'unknown-do-not-replay'):w.tick()
  self.assertEqual(len(w.input),1);self.assertEqual(w.s['calls'][0]['state'],'unknown')
 def test_confirmed_call_before_phase_commit_is_not_replayed(self):
  w=self.workflow(tree());w.s['phase']='clearReviewNegativeShortcut';originalgo=w.go;w.go=lambda _:(_ for _ in ()).throw(ValueError('crash after confirmed'))
  with self.guards(),patch('review_filter_loading.validate_filter_values'):
   with self.assertRaisesRegex(ValueError,'crash after confirmed'):w.tick()
   self.assertEqual(w.s['calls'][0]['state'],'confirmed');w.go=originalgo;w.tree=tree(False);w.tick();self.assertEqual(w.s['phase'],'verifyClearedReviewShortcut');self.assertEqual(len(w.input),1)
 def test_post_toggle_still_selected_is_readonly_hold(self):
  w=self.workflow(tree());w.s['phase']='verifyClearedReviewShortcut'
  with self.guards(),patch('review_filter_loading.validate_filter_values'),self.assertRaisesRegex(ValueError,'clear-not-observed-readonly'):w.tick()
  self.assertEqual(w.input,[])
 def test_date_or_company_change_refuses_before_input(self):
  w=self.workflow(tree());w.s['phase']='clearReviewNegativeShortcut'
  with self.guards(),patch('review_filter_loading.validate_filter_values',side_effect=ValueError('filter-date-unverified')),self.assertRaisesRegex(ValueError,'filter-date-unverified'):w.tick()
  self.assertEqual(w.input,[]);w.current['groupid']='18'
  with self.guards(),self.assertRaisesRegex(ValueError,'source-company-mismatch'):w.tick()
  self.assertEqual(w.input,[])
if __name__=='__main__':unittest.main()
