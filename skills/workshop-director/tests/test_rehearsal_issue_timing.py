"""TDD: temporary supervisor ledger, frozen refs, fake same-boot system clock."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import rehearsal_issue_timing as m
class Clock:
 def __init__(self):self.n=100.;self.boot_id='boot-A';self.offset=0
 def monotonic(self):return self.n
 def wall(self):return datetime(2026,10,23,tzinfo=timezone.utc)+timedelta(seconds=self.n+self.offset)
 def boot(self):return self.boot_id
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);self.ledger=self.p/'supervisor-issue.json';self.clock=Clock();self.anchor=self.p/'ticket.json';self.anchor.write_text('{"dispatch":"original"}');self.stop=self.p/'stop.json';self.stop.write_text('{"phase":"held"}');self.e2e=self.p/'original-e2e.json';self.e2e.write_text('{"start_monotonic":1,"status":"running"}');self.original=self.e2e.read_bytes();self.proof=self.p/'verified.json';self.proof.write_text('{"ok":true}');self.binding={'workflow':'violation-notifier','round_id':'round-1','anchor':m.t.ref(self.anchor),'stop_refs':[m.t.ref(self.stop)],'previous_round':None}
 def apply(self,step,**kw):return m.apply(self.ledger,step,'issue-1',clock=self.clock,**kw)
 def open(self,**kw):return self.apply('open',binding=self.binding,category='model-wait',**kw)
 def finish(self):
  self.open();self.clock.n=110;self.apply('repair-start',category='code-repair');self.clock.n=125;self.apply('resume',category='webpage-wait');self.clock.n=130;return self.apply('verified',evidence=m.t.ref(self.proof))
 def test_dual_clock_categories_and_e2e_never_reset_or_discounted(self):
  self.open();self.clock.n=110;self.clock.offset=-1000;self.apply('repair-start',category='code-repair');self.clock.n=125;self.apply('resume',category='webpage-wait');self.clock.n=130;r=self.apply('verified',evidence=m.t.ref(self.proof));v=r['issues']['issue-1'];self.assertEqual(v['discovery_to_resume_seconds'],25);self.assertEqual(v['repair_seconds'],15);self.assertEqual(v['verification_seconds'],5);self.assertEqual(v['category_seconds'],{'model-wait':10,'code-repair':15,'webpage-wait':5});self.assertEqual(v['result'],'verified');self.assertEqual(self.e2e.read_bytes(),self.original);self.assertLess(v['events'][1]['at'],v['events'][0]['at'])
 def test_repeated_commands_idempotent_and_conflicts_cannot_restart(self):
  self.open();raw=self.ledger.read_bytes();self.clock.n=105;self.open();self.assertEqual(raw,self.ledger.read_bytes());self.apply('repair-start',category='code-repair');raw=self.ledger.read_bytes();self.clock.n=106;self.apply('repair-start',category='code-repair');self.assertEqual(raw,self.ledger.read_bytes())
  with self.assertRaises(ValueError):self.apply('repair-start',category='model-wait')
 def test_boundaries_and_terminal_failure_preserved(self):
  self.open()
  for step in ('resume','verified'):
   with self.assertRaises(ValueError):self.apply(step,evidence=m.t.ref(self.proof))
  self.apply('failed',evidence=m.t.ref(self.proof));raw=self.ledger.read_bytes()
  with self.assertRaises(ValueError):self.apply('repair-start',category='code-repair')
  self.apply('failed',evidence=m.t.ref(self.proof));self.assertEqual(raw,self.ledger.read_bytes())
 def test_boot_changed_or_monotonic_backwards_rejected_without_write(self):
  self.open();raw=self.ledger.read_bytes();self.clock.boot_id='boot-B'
  with self.assertRaises(ValueError):self.apply('repair-start',category='code-repair')
  self.clock.boot_id='boot-A';self.clock.n=99
  with self.assertRaises(ValueError):self.apply('repair-start',category='code-repair')
  self.assertEqual(raw,self.ledger.read_bytes())
 def test_ref_change_and_output_alias_refused(self):
  self.open();raw=self.ledger.read_bytes();self.stop.write_text('changed')
  with self.assertRaises(ValueError):self.apply('repair-start',category='code-repair')
  self.assertEqual(raw,self.ledger.read_bytes())
  with self.assertRaises(ValueError):m.apply(self.anchor,'open','issue-1',binding=self.binding,category='model-wait',clock=self.clock)
 def test_unknown_historical_onset_stays_null(self):
  self.open(historical=True)
  with self.assertRaises(ValueError):self.apply('repair-start',category='code-repair',historical=True)
  self.clock.n=110;self.apply('repair-start',category='code-repair');self.clock.n=120;self.apply('resume',category='webpage-wait');self.clock.n=125;r=self.apply('verified',evidence=m.t.ref(self.proof));v=r['issues']['issue-1'];self.assertIsNone(v['discovery_to_resume_seconds']);self.assertIsNone(v['events'][0]['at']);self.assertIsNone(v['events'][0]['monotonic']);self.assertEqual(v['repair_seconds'],10);self.assertEqual(v['category_seconds']['model-wait'],0)
 def test_next_round_distinct_and_links_original_failure_without_overwrite(self):
  self.open();self.apply('failed',evidence=m.t.ref(self.proof));old=self.ledger.read_bytes();binding={**self.binding,'round_id':'round-2','previous_round':m.t.ref(self.ledger)};next_file=self.p/'round-2.json';r=m.apply(next_file,'open','issue-next',binding=binding,category='model-wait',clock=self.clock);self.assertEqual(r['round_id'],'round-2');self.assertEqual(self.ledger.read_bytes(),old)
  with self.assertRaises(ValueError):m.apply(self.p/'duplicate.json','open','x',binding={**binding,'round_id':'round-1'},category='model-wait',clock=self.clock)
 def test_distinct_issues_bind_their_own_stop_refs_within_same_round(self):
  self.open();second=self.p/'second-stop.json';second.write_text('{"phase":"new-stop"}');binding={**self.binding,'stop_refs':[m.t.ref(second)]};r=m.apply(self.ledger,'open','issue-2',binding=binding,category='webpage-wait',clock=self.clock);self.assertEqual(r['issues']['issue-2']['stop_refs'],binding['stop_refs']);self.assertEqual(r['issues']['issue-1']['stop_refs'],self.binding['stop_refs'])
 def test_failed_repair_keeps_measured_duration_and_no_resume_claim(self):
  self.open();self.clock.n=110;self.apply('repair-start',category='code-repair');self.clock.n=117;r=self.apply('failed',evidence=m.t.ref(self.proof));v=r['issues']['issue-1'];self.assertEqual(v['repair_seconds'],7);self.assertIsNone(v['discovery_to_resume_seconds']);self.assertEqual(v['discovery_to_terminal_seconds'],17)
 def test_existing_e2e_file_cannot_be_overwritten_as_issue_ledger(self):
  with self.assertRaises(ValueError):m.apply(self.e2e,'open','issue-1',binding=self.binding,category='model-wait',clock=self.clock)
  self.assertEqual(self.e2e.read_bytes(),self.original);self.assertFalse(self.e2e.with_name(self.e2e.name+'.lock').exists())
 def test_cli_only_writes_supervisor_ledger_and_requires_bound_evidence(self):
  args=['open','--ledger',str(self.ledger),'--issue','issue-1','--workflow','violation-notifier','--round','round-1','--anchor',str(self.anchor),'--stop-ref',str(self.stop)];self.assertEqual(m.main(args,clock=self.clock),0);self.assertEqual(self.e2e.read_bytes(),self.original)
  with self.assertRaises(ValueError):self.apply('failed')
if __name__=='__main__':unittest.main()
