"""Saved actual public DOM replay plus explicitly synthetic mutations. No UI."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SCRIPTS=ROOT/'skills/chrome-dom-export/scripts'
sys.path[:0]=[str(SCRIPTS),str(ROOT/'skills/violation-notifier/scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
p=load('governance_projection',SCRIPTS/'governance_projection.py')
b=load('production_business',SCRIPTS/'business_cells_capture.py')
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
GID='1767942028615694';CONTRACT=p.RECTIFICATION_CONTRACT
JS="""const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),input=JSON.parse(fs.readFileSync(0,'utf8'));const c={document:{documentElement:{}},MutationObserver:class{observe(){}},addEventListener(){},URL};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);let out=input.map(x=>{try{const value=c.__localViewportProof.governanceProjection(x.tree,x.gid,x.url||null,x.contract||null).value;return {value,sha:crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex')}}catch(e){return {error:String(e)}}});process.stdout.write(JSON.stringify(out));"""
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.raws=[json.loads((HERE/'fixtures/rectification-projection'/f'{x}.json').read_text()) for x in ('0000','0016')]
 def tree(self):return copy.deepcopy(self.raws[0]['tree'])
 def row(self,t):return next(n for n in p.walk(t['root']) if n.get('tag')=='tr' and len(n.get('children',[]))==10 and n['children'][0].get('tag')=='td' and n['children'][6].get('name','').startswith('待整改'))
 def test_legacy_actual_values_and_full_projection_unchanged(self):
  hashes=[['4a02fedbd0674345f1981e19529955bcf7cc952bf855736278a89630682fb2c7','2623f5d7754abe15a4710b577cbfcf52980c22805efc05759b8090948bd103ee'],['0c12ae5c7431f28b0f5f244b2c749714c0f1a361f0832684033053abcd75ccc7','a9a5a3f1b380c1c3a28ebc9dbcec25d5adbecd28c79d3ffda1cf0a8afd1b7c5f']]
  for i,raw in enumerate(self.raws):
   for j,url in enumerate((None,raw['tab']['url'])):self.assertEqual(p.digest(raw['tree'],GID,actual_url=url),hashes[i][j])
 def test_optin_actual_equal_and_raw_untouched(self):
  before=copy.deepcopy(self.raws);self.assertEqual(p.digest(self.raws[0]['tree'],GID,projection_contract=CONTRACT),p.digest(self.raws[1]['tree'],GID,projection_contract=CONTRACT));self.assertEqual(before,self.raws)
 def test_js_python_actual_both_contracts_and_provider(self):
  inputs=[dict(tree=r['tree'],gid=GID,contract=c,url=u) for r in self.raws for c in (None,CONTRACT) for u in (None,r['tab']['url'])]
  out=json.loads(subprocess.check_output([str(NODE),'-e',JS,str(SCRIPTS.parent/'extension/viewport-proof.js')],input=json.dumps(inputs,ensure_ascii=False).encode()))
  for x,y in zip(inputs,out):self.assertEqual(y['value'],p.project(x['tree'],GID,actual_url=x['url'],projection_contract=x['contract'])['value']);self.assertEqual(y['sha'],p.digest(x['tree'],GID,actual_url=x['url'],projection_contract=x['contract']))
 def test_all_other_business_fields_and_selector_strict(self):
  original=p.digest(self.tree(),GID,projection_contract=CONTRACT)
  for i in (0,1,2,3,4,5,8,9):
   t=self.tree();self.row(t)['children'][i]['name']+=' changed';self.assertNotEqual(original,p.digest(t,GID,projection_contract=CONTRACT))
  t=self.tree();self.row(t)['children'][6]['selector']+=' changed';self.assertNotEqual(original,p.digest(t,GID,projection_contract=CONTRACT))
 def test_status_not_masked(self):
  t=self.tree();cell=self.row(t)['children'][6]
  for n in p.walk(cell):n['name']=n.get('name','').replace('待整改','整改完成')
  self.assertNotEqual(p.digest(self.tree(),GID,projection_contract=CONTRACT),p.digest(t,GID,projection_contract=CONTRACT))
 def test_unknown_wrapper_duplicate_span_bad_clock_and_forged_label_reject_both(self):
  trees=[]
  for mode in ('wrapper','duplicate','hour','minute','second','label','interactive'):
   t=self.tree();cell=self.row(t)['children'][6];w=cell['children'][0];label,value=w['children'];leaf=value['children'][0]
   if mode=='wrapper':w['attributes']['class']+=' unknown'
   elif mode=='duplicate':value['children'].append(copy.deepcopy(leaf))
   elif mode=='label':label['name']='待整改伪'
   elif mode=='interactive':leaf['attributes']['tabindex']='0'
   else:
    bad={'hour':'5天24:00:00','minute':'5天12:60:00','second':'5天12:00:60'}[mode];oldv=leaf['name']
    for n in p.walk(cell):n['name']=n.get('name','').replace(oldv,bad)
   trees.append(t)
   with self.assertRaises(ValueError):p.project(t,GID,projection_contract=CONTRACT)
  out=json.loads(subprocess.check_output([str(NODE),'-e',JS,str(SCRIPTS.parent/'extension/viewport-proof.js')],input=json.dumps([dict(tree=t,gid=GID,contract=CONTRACT) for t in trees],ensure_ascii=False).encode()));self.assertTrue(all('error' in x for x in out))
 def test_namespace_strict(self):
  for manual in (False,True):
   ns=b.command_namespace(manual,CONTRACT);self.assertEqual(b.command_projection({'elements':[{'key':ns+':date'},{'key':ns+':row'}]}),CONTRACT)
   for keys in ((ns+':date',b.command_namespace(manual)+':row'),(ns.replace('v3','v99')+':row',)):
    with self.assertRaises(ValueError):b.command_projection({'elements':[{'key':k} for k in keys]})
  with self.assertRaises(ValueError):p.project(self.tree(),GID,projection_contract='unknown')
 def test_profile_consumer_propagates_optin(self):
  fc=ast.parse((SCRIPTS/'frame_capture.py').read_text());calls=[n for n in ast.walk(fc) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('make_command','spec')]
  self.assertTrue(calls);self.assertTrue(all(any(k.arg=='projection_contract' for k in n.keywords) for n in calls))
 def test_profile_explicit_flag_rejects_unknown_before_read(self):
  derived=load('candidate_derived',ROOT/'skills/violation-notifier/scripts/prepare_records_profile.py')
  for contract,evidence in (('unknown',derived.BUSINESS),(CONTRACT,None)):
   with self.assertRaisesRegex(ValueError,'projection-contract-unreviewed'):derived.derive({}, {}, {},projection_contract=contract,evidence_contract=evidence)
if __name__=='__main__':unittest.main()
