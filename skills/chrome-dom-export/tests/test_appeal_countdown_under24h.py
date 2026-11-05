"""Actual0027 deterministic countdown projection regression; no UI."""
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import governance_projection as gp
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/.records-region-navigation/7bb6a631114b5351e9d54b7370e2af2a8d4a38e63676a74c98fabee0a4118d2d/evidence'
GID='1767942028615694'
def cell(tree):return next(n['children'][7] for n in gp.walk(tree['root']) if n.get('tag')=='tr' and len(n.get('children',[]))==10 and n['children'][7].get('name')=='待申诉 23:48:48')
def change(root,old,new):
 for n in gp.walk(root):
  if old in n.get('name',''):n['name']=n['name'].replace(old,new)
class Under24h(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=BASE/'0027.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='05b7793846d3064c825cfeedad0b42a90f2f87e8efd5c3ae12eaf1f90de62158';cls.tree=json.loads(p.read_text())['tree'];spec=importlib.util.spec_from_file_location('old_governance_projection',ROOT/'work/live-acceptance/violations/appeal-countdown-under24h-v8/governance_projection-v7-baseline.py');cls.old=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.old)
 def test_actual_hour_tick_changed_previous_SHA_now_normalizes_exact_four_nodes(self):
  t=copy.deepcopy(self.tree);before=gp.project(t,GID);old=self.old.digest(t,GID);self.assertEqual(old,'19dc92747ec8afb232f5a68a355724f7afc84567dfa6e9991912b5e8bbc7e11d');change(cell(t),'23:48:48','23:48:47');self.assertNotEqual(old,self.old.digest(t,GID));self.assertEqual(before['value'],gp.project(t,GID)['value']);self.assertEqual(len(before['timers']),len(self.old.project(self.tree,GID)['timers'])+1)
 def test_only_valid_24h_range_and_original_eighth_cell_shape(self):
  before=gp.digest(self.tree,GID)
  for value in ('00:00:00','23:59:59'):
   t=copy.deepcopy(self.tree);change(cell(t),'23:48:48',value);self.assertEqual(gp.digest(t,GID),before)
  for value in ('24:00:00','23:60:00','23:59:60','1:02:03','x23:48:48'):
   t=copy.deepcopy(self.tree);change(cell(t),'23:48:48',value);self.assertNotEqual(gp.digest(t,GID),before)
  t=copy.deepcopy(self.tree);cell(t)['children'][0]['attributes']['class']='unknown'
  with self.assertRaises(ValueError):gp.project(t,GID)
 def test_hover_status_other_column_and_identity_change_remain_strict(self):
  before=gp.digest(self.tree,GID)
  for mode in ('hover','other-column','status','identity'):
   t=copy.deepcopy(self.tree);rows=[n for n in gp.walk(t['root']) if n.get('tag')=='tr' and len(n.get('children',[]))==10]
   if mode=='hover':rows[-1]['children'][0]['attributes']['class']+=' governance_merchant-Table-Cell_hover'
   if mode=='other-column':rows[5]['children'][6]['name']='23:48:47'
   if mode=='status':rows[5]['children'][3]['name']+=' changed'
   if mode=='identity':next(n for n in gp.walk(t['root']) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class',''))['name']+=' changed'
   self.assertNotEqual(gp.digest(t,GID),before)
 def test_old_approved_inputs_and_day_format_remain_byte_identical(self):
  for name in ('0016.json','0019.json','0024.json','0026.json'):
   t=json.loads((BASE/name).read_text())['tree'];self.assertEqual(gp.canonical(gp.project(t,GID)['value']),self.old.canonical(self.old.project(t,GID)['value']))
 def test_current_JS_matches_Python_current_exact_projection(self):
  node='/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node';script="""const fs=require('node:fs'),vm=require('node:vm'),c={MutationObserver:class{observe(){}},document:{documentElement:{}},addEventListener(){}};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);const x=JSON.parse(fs.readFileSync(process.argv[2]));console.log(JSON.stringify(c.__localViewportProof.governanceProjection(x.tree,process.argv[3]).value));""";actual=subprocess.check_output([node,'-e',script,str(ROOT/'skills/chrome-dom-export/extension/viewport-proof.js'),str(BASE/'0027.json'),GID],text=True).rstrip('\n');self.assertEqual(actual,gp.canonical(gp.project(self.tree,GID)['value']))
if __name__=='__main__':unittest.main()
