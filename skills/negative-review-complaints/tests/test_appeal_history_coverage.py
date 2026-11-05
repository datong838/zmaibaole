"""Offline copies of observed discovery evidence; never modify live case library/UI."""
import copy,hashlib,json,shutil,sys,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import appeal_history_coverage as coverage
import case_memory as memory
PROJECT=Path(__file__).resolve().parents[3]
AUDIT=PROJECT/'work/live-acceptance/complaints/month-history-20260921-20261021/public-history-discovery-v1/scope-audit.json'
class CoverageTests(unittest.TestCase):
 def setUp(self):
  if not AUDIT.is_file():self.skipTest('actual observed scope audit unavailable')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.library=self.root/'memory';self.audit=json.loads(AUDIT.read_bytes());self.docs={}
  for name,ref in self.audit['evidence'].items():
   data=Path(ref['path']).read_bytes();p=self.root/name;p.write_bytes(data);self.docs[name]=p;ref.update(path=str(p),sha256=hashlib.sha256(data).hexdigest())
  self.path=self.root/'audit.json'
 def save(self):
  self.path.write_text(json.dumps(self.audit,ensure_ascii=False));return hashlib.sha256(self.path.read_bytes()).hexdigest()
 def ingest(self):return coverage.import_audit(self.path,self.save(),memory=self.library)
 def state(self):
  return {'mode':'draft-only','company':self.audit['company'],'groupid':self.audit['groupid'],'next_start':'2026-09-21','tasks':{'new':{'status':'pending','review':{'date':'2026-10-20','customer':'fixture'},'screenshot':None,'latest_snapshot':{'sha256':'x'},'history':None}},'batches':{}}
 def test_actual_nine_evidence_portable_no_case_created_or_library_read_writes(self):
  result=self.ingest();self.assertTrue(result['appended']);self.assertFalse((self.library/'complaint-cases.jsonl').exists());self.assertFalse(self.ingest()['appended'])
  self.assertEqual(len(coverage.read_records(self.library)),1)
  for p in self.docs.values():p.unlink()
  self.path.unlink();rows=coverage.read_records(self.library);self.assertEqual(rows[0]['date_field'],'review_time');self.assertEqual(rows[0]['status_field'],'customer_visibility');self.assertFalse(rows[0]['company_all_history_proven'])
  before={str(p):p.stat().st_mtime_ns for p in self.library.rglob('*') if p.is_file()};coverage.summary(memory=self.library);self.assertEqual(before,{str(p):p.stat().st_mtime_ns for p in self.library.rglob('*') if p.is_file()})
 def test_hash_mismatch_wrong_domain_or_false_full_coverage_is_rejected(self):
  sha=self.save()
  with self.assertRaisesRegex(ValueError,'hash-mismatch'):coverage.import_audit(self.path,'0'*64,memory=self.library)
  for key,value in [('domain','violation'),('complete_company_month_history_proved',True),('new_case_originals_read',5),('company_all_history_proven',True),('case_count_is_company_total',True)]:
   old=copy.deepcopy(self.audit);self.audit[key]=value
   with self.assertRaises(ValueError):self.ingest()
   self.audit=old
  self.assertFalse((self.library/'history-coverage.jsonl').exists())
 def test_modified_source_origin_or_identity_even_with_new_hash_rejected(self):
  for change in ('origin','identity'):
   p=self.docs['all-rating-tree.json'];original=p.read_bytes();data=json.loads(original)
   if change=='origin':data['result']['url']='https://example.com/p/life_comment/management'
   else:
    def walk(n):
     yield n
     for c in n.get('children',[]):yield from walk(c)
    next(n for n in walk(data['result']['root']) if n.get('tag')=='header')['name']='wrong identity'
   p.write_text(json.dumps(data,ensure_ascii=False));self.audit['evidence'][p.name]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
   with self.assertRaisesRegex(ValueError,'source-origin|source-identity'):self.ingest()
   p.write_bytes(original);self.audit['evidence'][p.name]['sha256']=hashlib.sha256(original).hexdigest()
 def test_append_is_concurrent_idempotent_and_preserves_prior_observation(self):
  sha=self.save()
  with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda _:coverage.import_audit(self.path,sha,memory=self.library),range(3)))
  self.assertEqual(sum(r['appended'] for r in results),1);before=(self.library/'history-coverage.jsonl').read_bytes()
  self.audit['observed_at']='2026-10-21T23:59:00+08:00';self.ingest();self.assertTrue((self.library/'history-coverage.jsonl').read_bytes().startswith(before));self.assertEqual(len(coverage.read_records(self.library)),2)
 def test_tamper_or_damaged_tail_refuses_without_repair(self):
  self.ingest();log=self.library/'history-coverage.jsonl';before=log.read_bytes();log.write_bytes(before+b'{')
  with self.assertRaisesRegex(ValueError,'damaged-tail'):self.ingest()
  self.assertEqual(log.read_bytes(),before+b'{');log.write_bytes(before)
  record=coverage.read_records(self.library)[0];(self.library/record['audit_ref']['path']).write_text('{}')
  with self.assertRaisesRegex(ValueError,'evidence-hash'):coverage.read_records(self.library)
 def test_plan_and_analysis_autoload_coverage_without_changing_business_range(self):
  import workflow
  self.ingest();state=self.state();before=copy.deepcopy(state);original=memory.load_for_workflow
  with patch.object(memory,'load_for_workflow',side_effect=lambda s,key=None,**kw:original(s,key,memory=self.library,**kw)):
   plan=workflow.plan(state,'2026-10-21');order=workflow.analysis_order(state,'new')
  for output in (plan,order):
   info=output['appeal_case_memory']['history_scope_coverage'];self.assertEqual(info['scope_audit_count'],1);self.assertFalse(info['case_count_is_company_total']);self.assertFalse(info['company_all_history_proven'])
  self.assertEqual(state,before);self.assertEqual((plan['start'],plan['end_exclusive']),('2026-09-21','2026-10-21'))
  shanghai={**state,'company':'上海老芗汇餐饮管理有限公司','groupid':'1764303851132943'};self.assertEqual(original(shanghai,memory=self.library)['history_scope_coverage']['audits'][0]['unchecked_companies'],['上海老芗汇餐饮管理有限公司'])
 def test_document_adds_only_short_coverage_note_and_original_source_link(self):
  self.ingest();out=self.root/'refs'/'memory.md';memory.render_document(out,memory=self.library);text=out.read_text();self.assertIn('历史查询覆盖观察',text);self.assertIn('已归档案例数不是公司全月总量',text);self.assertIn('原始范围审计',text);self.assertIn('../memory/evidence/',text);self.assertFalse((self.library/'complaint-cases.jsonl').exists())
if __name__=='__main__':unittest.main()
