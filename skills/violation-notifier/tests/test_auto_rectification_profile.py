"""Offline orchestration tests; saved public shape, synthetic refs, TEMP outputs.
Original full derive is mocked only at its existing source-validation boundary.
"""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path[:0]=[str(R/'skills/violation-notifier/scripts'),str(R/'skills/chrome-dom-export/scripts')]
s=importlib.util.spec_from_file_location('auto_profile_candidate',R/'skills/violation-notifier/scripts/prepare_records_profile.py');p=importlib.util.module_from_spec(s);sys.modules[s.name]=p;s.loader.exec_module(p)
RAW=json.loads((R/'skills/chrome-dom-export/tests/fixtures/rectification-projection/0000.json').read_text())
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)/'profile.json';self.source={'path':'/synthetic/source.json','sha256':'a'*64};self.job={'path':'/synthetic/job.json','sha256':'b'*64};self.query={'path':'/synthetic/query.json','sha256':'c'*64};self.raw=copy.deepcopy(RAW);self.rawref={'path':'/synthetic/observation.json','sha256':'d'*64};self.query_doc={'pages':[{'observation':self.rawref}]};self.calls=[]
  def document(ref):
   if ref==self.query:return self.query_doc
   if ref==self.rawref:return self.raw
   raise AssertionError(ref)
  def derive(source,job,query,**kwargs):
   self.assertEqual((source,job,query),(self.source,self.job,self.query));self.assertNotIn('full_source_check',kwargs);self.calls.append(kwargs.copy())
   result={'status':'DOM-derived-ready','derivation':{'source':source,'job':job,'query':query,'pages':[{}],'scope':{'total':4}}}
   result.update({k:v for k,v in kwargs.items() if v is not None});return result
  self.addCleanup(patch.stopall);patch.object(p.d,'document',side_effect=document).start();patch.object(p,'derive',side_effect=derive).start()
 def run_prepare(self,**kw):return p._prepare_uncached(self.source,self.job,self.query,self.out,**kw)
 def pending_cell(self):return next(n for n in p.g.walk(self.raw['tree']['root']) if n.get('tag')=='td' and n.get('name','').startswith('待整改'))
 def test_new_output_auto_selects_both_and_retains_raw(self):
  before=copy.deepcopy(self.raw);self.run_prepare();doc=json.loads(self.out.read_text());self.assertEqual((doc['evidence_contract'],doc['projection_contract']),(p.BUSINESS,p.PROJECTION));self.assertEqual(before,self.raw);self.assertEqual(len(self.calls),1)
 def test_existing_legacy_bytes_return_unchanged_even_with_pending(self):
  legacy=p.derive(self.source,self.job,self.query,evidence_contract=None,projection_contract=None);self.out.write_text(json.dumps(legacy,indent=3)+'\n');before=self.out.read_bytes();self.calls.clear()
  with patch.object(p,'automatic_projection',side_effect=AssertionError('old output must not auto select')):self.run_prepare()
  self.assertEqual(before,self.out.read_bytes());self.assertEqual(self.calls,[{'evidence_contract':None,'projection_contract':None}])
 def test_existing_new_output_idempotent(self):
  self.run_prepare();before=self.out.read_bytes();self.run_prepare();self.assertEqual(before,self.out.read_bytes())
 def test_unknown_pending_shape_fail_no_output(self):
  self.pending_cell()['children'][0]['attributes']['class']+=' unknown'
  with self.assertRaises(ValueError):self.run_prepare()
  self.assertFalse(self.out.exists());self.assertFalse(self.calls)
 def test_no_pending_retains_default_and_explicit_still_supported(self):
  c=self.pending_cell();c['name']='无需整改';c['children']=[];self.run_prepare();doc=json.loads(self.out.read_text());self.assertNotIn('evidence_contract',doc);self.assertNotIn('projection_contract',doc)
  self.out.unlink();self.run_prepare(projection_contract=p.PROJECTION);doc=json.loads(self.out.read_text());self.assertEqual(doc['projection_contract'],p.PROJECTION);self.assertEqual(doc['evidence_contract'],p.BUSINESS)
 def test_existing_input_or_explicit_contract_conflict_rejects(self):
  self.run_prepare();before=self.out.read_bytes()
  with self.assertRaises(ValueError):p._prepare_uncached(self.source,{'path':'/other','sha256':'e'*64},self.query,self.out)
  with self.assertRaises(ValueError):self.run_prepare(projection_contract='unknown')
  self.assertEqual(before,self.out.read_bytes())
 def test_nav_capture_generation_same_query_same_flag(self):
  self.run_prepare();first=json.loads(self.out.read_text());self.out=Path(self.tmp.name)/'capture.json';self.run_prepare(evidence_contract=p.BUSINESS);self.assertEqual(first,json.loads(self.out.read_text()))
 def test_invalid_clock_and_duplicate_span_never_fall_back(self):
  for mode in ('clock','duplicate'):
   self.raw=copy.deepcopy(RAW);cell=self.pending_cell();leaf=cell['children'][0]['children'][1]['children'][0]
   if mode=='clock':leaf['name']='5天25:00:00'
   else:cell['children'][0]['children'][1]['children'].append(copy.deepcopy(leaf))
   with self.assertRaises(ValueError):self.run_prepare()
   self.assertFalse(self.out.exists())
if __name__=='__main__':unittest.main()
