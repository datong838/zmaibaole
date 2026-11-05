"""Actual original evidence replay only. No live bridge or original journal writes."""
import copy,importlib.util,json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();PROJECT=HERE.parents[3];sys.path.insert(0,str(HERE.parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('calendar_repair_runner',HERE.parents[1]/'scripts/bridge-governance-query.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE=PROJECT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class RepairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.file=Path(self.tmp.name)/'query.json';self.original=json.loads((BASE/'center-analysis-query-v9.json.calendar-target-repair-original-5422dea5c2ad49751595dc9303e880cc2535130c99285e2be80f9cfeb8e77149.json').read_text());self.file.write_text(json.dumps(self.original,ensure_ascii=False));self.r=object.__new__(m.Runner);self.r.file=self.file;self.r.s=copy.deepcopy(self.original);self.r.tab=self.original['tab_id'];self.r.version=self.original['approved_version'];self.r.job={};self.r.plan=m.g.QueryPlan('2026-10-16','2026-10-20');self.r.calendar_policy_ready=False;self.calls=[]
  self.tree=m.nav.read_pinned(self.original['last_observation']['path'],self.original['last_observation']['sha256'])['tree'];self.sha=m.nav.digest(self.file)
 def observe(self):
  self.calls.append('read-only');self.r.calendar_policy_ready=True;return self.tree
 def repair(self):
  with patch.object(m.nav,'scope'),patch.object(self.r,'observe',side_effect=self.observe):return self.r.reconcile_calendar_target(self.sha,self.original['last_observation']['sha256'])
 def test_actual_confirmed_no_effect_target_prepares_child_div_without_click(self):
  s=self.repair();self.assertEqual(s['phase'],'select-start');self.assertEqual(s['calls'],self.original['calls']);self.assertEqual(self.calls,['read-only']);repair=s['calendar_target_repair'];self.assertEqual(m.nav.digest(repair['original_journal']['path']),self.sha);self.assertEqual(repair['corrected_command']['locator']['value'],self.original['calls'][-1]['command']['locator']['value']+' > div');self.assertFalse(s.get('settling_exhausted',False))
 def test_repeat_repair_never_reads_or_clicks_again(self):
  self.repair();self.r.s=json.loads(self.file.read_text());self.sha=m.nav.digest(self.file)
  with self.assertRaisesRegex(ValueError,'already-recorded'):self.repair()
  self.assertEqual(len(self.calls),1)
 def test_changed_original_hash_last_ref_phase_unknown_call_refused_before_observation(self):
  for kind in ('hash','last','phase','unknown'):
   with self.subTest(kind=kind):
    self.r.s=copy.deepcopy(self.original);self.file.write_text(json.dumps(self.original,ensure_ascii=False));self.sha=m.nav.digest(self.file)
    if kind=='hash':self.sha='0'*64
    if kind=='last':self.r.s['last_observation']['sha256']='0'*64
    if kind=='phase':self.r.s['phase']='verify-date'
    if kind=='unknown':self.r.s['calls'][-1]['state']='unknown'
    with self.assertRaises(ValueError):self.repair()
    self.assertEqual(self.calls,[])
 def test_fresh_changed_date_stops_preserving_original_confirmed_call(self):
  self.tree=copy.deepcopy(self.tree);m.g.date_input(self.tree)['attributes']['value']='2026/10/16 ～ 2026/10/21'
  with self.assertRaisesRegex(ValueError,'fresh-date-or-calendar-changed'):self.repair()
  self.assertEqual(self.r.s['calls'],self.original['calls']);self.assertEqual(self.r.s['calendar_target_repair']['state'],'readonly-verification')
 def test_calendar_planner_selects_observed_div_and_ambiguous_child_refuses(self):
  action=m.g.calendar_action(self.tree,'2026-10-16');self.assertTrue(action['action']['locator']['value'].endswith(' > div'))
  t=copy.deepcopy(self.tree);cell=next(n for n in m.g.nodes(t) if n['selector']==self.original['calls'][-1]['command']['locator']['value']);cell['children'].append(copy.deepcopy(cell['children'][0]))
  with self.assertRaisesRegex(ValueError,'item-not-unique'):m.g.calendar_action(t,'2026-10-16')
if __name__=='__main__':unittest.main()
