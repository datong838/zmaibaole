"""Synthetic assembly tests only; actual DOM parser tests live in their own modules."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_capture as c
REAL_SCOPE=c.scope
import test_center_reconciliation as center_fixtures
class CaptureTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);pages,records=center_fixtures.CenterTests().synthetic();self.pages=pages
  self.job={'company':'模拟公司','groupid':'123','identity':{'provider':'模拟服务商','account_id':'123','manager':'模拟经理'},'start':'2026-10-16','end_exclusive':'2026-10-21'}
  self.qrows=[];self.facts=[];self.entries=[]
  def raw(name,path,tree=None):
   p=self.root/name;p.write_text(json.dumps({'source':'local-dom-bridge','tab_id':1,'tab':{'tabId':1,'windowId':2,'url':'https://life.douyin.com'+path+'?groupid=123'},'observed_at':'2026-10-21T09:00:00+08:00','tree':tree or {}},ensure_ascii=False));return c.detail.ref(p)
  self.recordref=raw('records.json',c.g.RECORDS)
  for r in records:
   row={'notice_id':r['notice_id'],'violation_date':r['date'],'store_name':'模拟门店','reason':r['reason'],'disposal':'警告','effective_status':'已生效','rectification_status':'-'};self.qrows.append(row);facts={'schema':'governance-notice-detail-v1','source_notice_row':row,'notice_id':row['notice_id'],'object_type':r['object_type'],'object_name':'模拟对象','disposals':['警告'],'effective_statuses':['已生效'],'public_recommendation':'模拟建议，非真实数据','public_recommendation_section':'如何避免再次违规','public_recommendation_selector':'#mock-advice'};self.facts.append(facts);self.entries.append({'notice_id':row['notice_id'],**{k:self.recordref for k in ('normal_before','detail_observation','before_close','normal_after')}})
  self.refs={k:self.recordref for k in ('job','query','detail_manifest','detail_state')};self.refs['center_pages']=[raw('center'+str(p['page'])+'.json',c.g.CENTER,{'mock_center_page':p}) for p in pages];self.m={'kind':'governance-capture-manifest-v1','profile_revision':c.PROFILE,'inputs':self.refs};self.v={'job':self.job,'query':{'rows':self.qrows,'pages':[{'observation':self.recordref}]},'detail_manifest':{'tab_id':1},'detail_state':{'details':self.entries},'facts':self.facts}
  self.patches=[patch.object(c,'inputs',return_value=self.v),patch.object(c,'scope',side_effect=lambda *a,**k:__import__('datetime').datetime.fromisoformat(a[0]['observed_at'])),patch.object(c.center,'center_page',side_effect=lambda tree,**kw:tree['mock_center_page'])]
  for p in self.patches:p.start();self.addCleanup(p.stop)
 def test_synthetic_full_two_page_records_distribution_reconciles_all_twelve(self):
  out=c.assemble(self.m);self.assertEqual(out['records']['total'],16);self.assertEqual(len(out['analysis']['rows']),12);self.assertFalse(out['analysis']['top10_is_complete_distribution']);self.assertEqual(out['records']['rows'][0]['actions'],['警告']);self.assertEqual(out['records']['rows'][0]['rectification_status'],'-');self.assertEqual(out['records']['rows'][0]['subject'],'模拟门店')
 def test_incomplete_center_detail_or_duplicate_notice_refuses(self):
  for kind in ('center','detail','duplicate'):
   with self.subTest(kind=kind):
    m=copy.deepcopy(self.m);v=copy.deepcopy(self.v)
    if kind=='center':m['inputs']['center_pages']=m['inputs']['center_pages'][:1]
    elif kind=='detail':v['detail_state']['details'].pop()
    else:v['query']['rows'][1]['notice_id']=v['query']['rows'][0]['notice_id'];v['facts'][1]['notice_id']=v['query']['rows'][0]['notice_id'];v['facts'][1]['source_notice_row']=v['query']['rows'][1];v['detail_state']['details'][1]['notice_id']=v['query']['rows'][0]['notice_id']
    with patch.object(c,'inputs',return_value=v),self.assertRaises(ValueError):c.assemble(m)
 def test_literal_difference_yields_real_refs_report_without_payload(self):
  self.facts[0]['effective_statuses']=['已豁免']
  with self.assertRaises(c.MappingRequired) as e:c.assemble(self.m)
  report=e.exception.report;self.assertFalse(report['capture_generated']);item=report['mismatches'][0];self.assertEqual(item['table']['effective_status'],'已生效');self.assertEqual(item['detail']['effective_statuses'],['已豁免']);self.assertEqual(item['detail_observation'],self.recordref)
 def test_mechanical_verifier_rebuilds_and_refuses_tamper_and_raw_changes(self):
  manifest=self.root/'manifest.json';manifest.write_text(json.dumps(self.m));out=self.root/'capture.json';c.build(manifest,out);raw=out.read_bytes();self.assertEqual(c.validate(out)['records']['total'],16)
  p=json.loads(raw);p['records']['rows'][0]['actions']=['调整展示'];out.write_text(json.dumps(p))
  with self.assertRaisesRegex(ValueError,'derived-payload'):c.validate(out)
  out.write_bytes(raw);Path(self.recordref['path']).write_text('{}')
  with self.assertRaises(ValueError):c.validate(out)
 def test_multi_paragraph_advice_keeps_all_exact_selector_refs(self):
  fact=self.facts[0];fact.pop('public_recommendation_selector');fact['public_recommendation_selectors']=['#first','#second'];fact['public_recommendation']='模拟第一段\n模拟第二段';out=c.assemble(self.m);self.assertEqual(out['records']['rows'][0]['public_recommendation_basis']['selectors'],['#first','#second'])
 def test_actual_first_detail_scope_binding_and_changed_window_or_dates_reject(self):
  base=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司';raw=json.loads((base/'first-detail-probe-v9-evidence/0002.json').read_text());job=json.loads((base/'navigation-job.json').read_text());REAL_SCOPE(raw,job,raw['tab_id'],raw['tab']['windowId'],c.g.RECORDS)
  with self.assertRaisesRegex(ValueError,'window-changed'):REAL_SCOPE(raw,job,raw['tab_id'],999,c.g.RECORDS)
  changed=copy.deepcopy(raw);c.g.date_input(changed['tree'])['attributes']['value']='2026/10/01 ～ 2026/10/20'
  with self.assertRaises(ValueError):REAL_SCOPE(changed,job,raw['tab_id'],raw['tab']['windowId'],c.g.RECORDS)
 def test_old_backend_cannot_claim_a_local_manifest(self):
  import workflow as w
  p=self.root/'wrong-backend.json';p.write_text(json.dumps({'capture_manifest':{},'analysis':{},'records':{},'start':'2026-10-16','end_exclusive':'2026-10-21','source':'codex-existing-extension'}));state={'mode':'live','browser_backend':'codex-existing-extension'}
  with patch.object(w,'check_source',return_value=self.job['identity']),self.assertRaisesRegex(ValueError,'backend-mismatch'):w.ingest(self.root,state,p,'2026-10-21')
 def test_workflow_live_local_requires_assembler_not_just_capture_booleans(self):
  import workflow as w
  p=self.root/'unverified.json';p.write_text(json.dumps({'analysis':{},'records':{},'start':'2026-10-16','end_exclusive':'2026-10-21'}));state={'mode':'live','browser_backend':'local-dom-bridge'}
  with patch.object(w,'check_source',return_value=self.job['identity']),self.assertRaisesRegex(ValueError,'manifest-reference-required'):w.ingest(self.root,state,p,'2026-10-21')
if __name__=='__main__':unittest.main()
