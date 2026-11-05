"""Pure actual-page replay and synthetic prefix memo; never runs browser APIs."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d
import verification_session as cache
CALLS=[]
def checked(s,m,v,*,require_complete=True):CALLS.append(require_complete);return [{'complete':require_complete}]
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class IntegrationTests(unittest.TestCase):
 def test_actual_two_pages_index_and_original_parser_are_equal(self):
  q=json.loads((BASE/'records-range-query-v9.json').read_text());job=json.loads((BASE/'navigation-job.json').read_text())
  with cache.validation_scope() as session:
   for page in q['pages']:
    plain=json.loads(Path(page['observation']['path']).read_text());pinned=d.document(page['observation'])
    self.assertEqual(d.g.records_page(plain['tree'],start=job['start'],end_exclusive=job['end_exclusive']),d.g.records_page(pinned['tree'],start=job['start'],end_exclusive=job['end_exclusive']))
    self.assertEqual(list(d.g.walk(plain['tree']['root'])),list(d.g.walk(pinned['tree']['root'])))
   self.assertEqual(len(session.indexes),2)
 def test_pinned_prefix_memo_flags_code_changes_and_mutable_live_bypass(self):
  with tempfile.TemporaryDirectory() as folder,cache.validation_scope() as session:
   def pin(name,value):
    p=Path(folder)/name;p.write_text(json.dumps(value));return d.document(d.ref(p))
   state=pin('state.json',{'phase':'complete'});manifest=pin('manifest.json',{});v={'job':pin('job.json',{}),'query':pin('query.json',{})};calls=CALLS;calls.clear()
   with patch.object(d,'_verify_completed_uncached',checked):
    self.assertEqual(d.verify_completed(state,manifest,v),[{'complete':True}]);d.verify_completed(state,manifest,v);self.assertEqual(calls,[True]);d.verify_completed(state,manifest,v,require_complete=False);self.assertEqual(calls,[True,False])
    d.verify_completed(copy.deepcopy(state),manifest,v);self.assertEqual(len(calls),3)
    old=d.g.HEADERS;d.g.HEADERS=old+['changed']
    try:d.verify_completed(state,manifest,v);self.assertEqual(len(calls),4)
    finally:d.g.HEADERS=old
 def test_actual_pinned_dependency_changed_rejects_before_reuse(self):
  with tempfile.TemporaryDirectory() as folder,cache.validation_scope() as session:
   p=Path(folder)/'raw.json';p.write_text('{"truncated":false,"root":{"tag":"div","children":[]}}');ref=d.ref(p);raw=d.document(ref);self.assertEqual(len(d.g.nodes(raw)),1);p.write_text('{}')
   with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):d.document(ref)
if __name__=='__main__':unittest.main()
