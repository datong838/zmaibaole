"""Actual saved public DOM; JS/Python canonical projection byte parity, no UI."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import governance_projection as p
BASE=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
MODULE=Path(__file__).resolve().parents[1]/'extension/viewport-proof.js'
class ProjectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((BASE/'records-range-query-v9.json').read_text());cls.tree=json.loads(Path(cls.q['pages'][0]['observation']['path']).read_text())['tree']
 def test_actual_four_five_only_countdown_change_projection_equal(self):
  folder=BASE/'.records-region-navigation/7bb6a631114b5351e9d54b7370e2af2a8d4a38e63676a74c98fabee0a4118d2d/evidence';a=json.loads((folder/'0004.json').read_text())['tree'];b=json.loads((folder/'0005.json').read_text())['tree'];self.assertNotEqual(p.canonical(a),p.canonical(b));self.assertEqual(p.digest(a,'1767942028615694'),p.digest(b,'1767942028615694'))
 def test_JS_Python_identical_projection_both_actual_pages(self):
  script="""const fs=require('fs'),vm=require('vm'),crypto=require('crypto');const input=JSON.parse(fs.readFileSync(0,'utf8'));const c={document:{documentElement:{}},MutationObserver:class{observe(){}},addEventListener(){}};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);const value=c.__localViewportProof.governanceProjection(input.tree,input.groupid).value;process.stdout.write(JSON.stringify({value,sha:crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex')}));"""
  for page in self.q['pages']:
   tree=json.loads(Path(page['observation']['path']).read_text())['tree'];result=json.loads(subprocess.check_output([str(NODE),'-e',script,str(MODULE)],input=json.dumps({'tree':tree,'groupid':'1767942028615694'},ensure_ascii=False).encode()));self.assertEqual(result['value'],p.project(tree,'1767942028615694')['value']);self.assertEqual(result['sha'],p.digest(tree,'1767942028615694'))
 def test_change_business_tuple_or_source_scope_changes_hash(self):
  original=p.digest(self.tree,'1767942028615694')
  for idx in range(7):
   tree=copy.deepcopy(self.tree);row=next(n for n in p.walk(tree['root']) if n.get('tag')=='tr' and len(n.get('children',[]))==10 and n['children'][0].get('tag')=='td');row['children'][idx]['name']+=' changed';self.assertNotEqual(p.digest(tree,'1767942028615694'),original)
  self.assertNotEqual(p.digest(self.tree,'123456'),original)
 def test_profile_gated_command_and_registration_explicit_projection_metadata(self):
  directory=Path(__file__).resolve().parents[2]/'violation-notifier/scripts';sys.path.insert(0,str(directory))
  import prepare_records_profile as derived
  import frame_capture as fc
  import screenshot_registration as sr
  import tempfile
  source=derived.d.ref(BASE/'complete-governance-source.json');job=derived.d.ref(BASE/'navigation-job.json');query=derived.d.ref(BASE/'records-range-query-v9.json');profile=derived.derive(source,job,query,full_source_check=False)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'profile.json';derived.d.exclusive(path,profile);inputs=fc.page_inputs(source,self.q['pages'][0]['observation'],derived.d.ref(path));cmd=inputs['command'];self.assertTrue(all(e['key'].startswith(p.SCHEMA+':') for e in cmd['elements']));self.assertEqual(cmd['dom_sha256'],p.digest(self.tree,'1767942028615694'))
   proof={'source':'local-dom-bridge','method':'public-DOM-semantic-viewport-proof','source_sha256':source['sha256'],'dom_sha256':cmd['dom_sha256'],'epoch':0,'url':inputs['url'],'viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'all_fully_visible':True,'scope':{k:cmd[k] for k in ('tabId','windowId','groupid')},'safety_version':'dom-only-20261021-11','hash_contract':p.SCHEMA,'hash_scope':'versioned-public-DOM-projection','diagnostic_build':'viewport-notice-business-cells-v3','elements':[{**{k:e[k] for k in ('key','kind','notice_id','locator')},'text':e['expected_text'],**dict.fromkeys(('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent','fully_visible'),True),'containment_diagnostic':{'purpose':'readonly-containment-diagnostic-only','scope':'target-and-descendants','reasons':[],'reason_count':0,'truncated':False},'possible_overlay_diagnostic':{'purpose':'readonly-overlay-diagnostic-only','candidates':[],'candidate_count':0,'truncated':False}} for e in cmd['elements']]}
   sr.validate_public_proof(proof,cmd,inputs['url'])
   coordinates=copy.deepcopy(proof);coordinates['pixel_coordinates_returned']=True
   with self.assertRaisesRegex(ValueError,'proof-safety-mismatch'):sr.validate_public_proof(coordinates,cmd,inputs['url'])
   coordinates['pixel_coordinates_returned']=False;coordinates['elements'][0]['containment_diagnostic']['coordinate_space']='CSS-viewport-diagnostic-only'
   with self.assertRaisesRegex(ValueError,'containment-diagnostic-fields-invalid'):sr.validate_public_proof(coordinates,cmd,inputs['url'])
   bad=copy.deepcopy(proof);bad['hash_scope']='whole-tree'
   with self.assertRaises(ValueError):sr.validate_public_proof(bad,cmd,inputs['url'])
 def test_unknown_timer_shape_or_missing_headers_reject(self):
  for mode in ('shape','headers'):
   tree=copy.deepcopy(self.tree);ns=list(p.walk(tree['root']))
   if mode=='shape':next(n for n in ns if p.TIME.fullmatch(n.get('name','')) and n.get('tag')=='span')['name']='0天01:02:03';# parent aggregate deliberately unchanged
   else:next(n for n in ns if n.get('tag')=='th')['name']='unreviewed'
   with self.assertRaises(ValueError):p.project(tree,'1767942028615694')
if __name__=='__main__':unittest.main()
