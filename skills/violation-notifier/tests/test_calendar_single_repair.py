"""Effective start-date selection recovery; exact actual evidence, no live requests."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_calendar_target_repair as f
m=f.m
class SingleRepairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'query.json';self.original=json.loads((Path(__file__).parent/'fixtures/confirmed-div-start-single-journal.json').read_text());self.path.write_text(json.dumps(self.original,ensure_ascii=False));self.sha=m.nav.digest(self.path);self.r=object.__new__(m.Runner);self.r.file=self.path;self.r.s=copy.deepcopy(self.original);self.r.tab=self.original['tab_id'];self.r.version=self.original['approved_version'];self.r.job={};self.r.plan=m.g.QueryPlan('2026-10-16','2026-10-20');self.r.calendar_policy_ready=False;self.tree=m.nav.read_pinned(self.original['last_observation']['path'],self.original['last_observation']['sha256'])['tree'];self.reads=0
 def observe(self):self.reads+=1;self.r.calendar_policy_ready=True;return self.tree
 def repair(self):
  with patch.object(m.nav,'scope'),patch.object(self.r,'observe',side_effect=self.observe):return self.r.reconcile_selected_single_start(self.sha,self.original['last_observation']['sha256'])
 def test_actual_16_single_verified_continues_end_and_preserves_old_repair_calls(self):
  s=self.repair();self.assertEqual(s['phase'],'select-end');self.assertEqual(s['calls'],self.original['calls']);self.assertEqual(s['calendar_target_repair'],self.original['calendar_target_repair']);self.assertFalse(s.get('settling_exhausted'));self.assertEqual(m.nav.digest(s['selected_single_start_repair']['original_journal']['path']),self.sha);self.assertEqual(self.reads,1)
 def test_fresh_range_or_input_change_refuses_no_reclick(self):
  self.tree=copy.deepcopy(self.tree);m.g.date_input(self.tree)['attributes']['value']='2026/10/16 ～ 2026/10/19'
  with self.assertRaisesRegex(ValueError,'fresh-selection-or-date-changed'):self.repair()
  self.assertEqual(self.r.s['calls'],self.original['calls'])
 def test_repeat_refuses_before_read(self):
  self.repair();self.sha=m.nav.digest(self.path)
  with self.assertRaisesRegex(ValueError,'already-recorded'):self.repair()
  self.assertEqual(self.reads,1)
 def test_wrong_start_confirmed_target_or_unknown_refuses(self):
  for kind in ('wrong','unknown'):
   self.r.s=copy.deepcopy(self.original)
   if kind=='wrong':self.r.s['calls'][-1]['command']['locator']['value']='#other'
   else:self.r.s['calls'][-1]['state']='unknown'
   with self.assertRaises(ValueError):self.repair()
   self.assertEqual(self.reads,0)
 def test_actual_single_start_is_parseable_and_end_targets_19_not_16(self):
  views=m.g.calendar(self.tree);self.assertTrue(any('2026-10-16' in v['cells'] for v in views));target=self.r.plan.next(self.tree,{'phase':'select-end'});self.assertEqual(target['selected_date'],'2026-10-19');self.assertNotEqual(target['command'],{k:v for k,v in self.original['calls'][-1]['command'].items() if k!='tabId'})
if __name__=='__main__':unittest.main()
