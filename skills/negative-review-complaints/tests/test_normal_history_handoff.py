import sys,json,unittest,importlib.util,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_case_journey as j
spec=importlib.util.spec_from_file_location('candidate_history_handoff',Path(__file__).resolve().parents[1]/'scripts/history_workspace.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class HandoffTests(unittest.TestCase):
 def setUp(self):
  self.source={'path':'/synthetic/source.json','sha256':'a'*64};self.m={'root':'/synthetic/history','review_key':'123:r','inputs':{'source':self.source,'profile':{'path':'/synthetic/profile.json','sha256':'b'*64}}};self.state={'tasks':{'123:r':{'action':'查看投诉结果','latest_snapshot':self.source}}}
 def run_case(self,profile,route):
  with patch.object(h.workflow,'read',return_value=self.m),patch.object(h,'load',return_value=self.state),patch.object(h.runner,'document',return_value=profile),patch.object(h.runner,'tick',return_value={'state':'opened'}) as tick,patch.object(j,'ensure_for_result',return_value=route) as ensure:
   out=h.run('/synthetic/inspection.json',steps=1,request=lambda c:self.fail('fixture must not request'));return out,tick.call_count,ensure.call_count
 def test_new_profile_requires_complete_case_journey_before_existing_reader(self):
  out,ticks,routes=self.run_case({'contract':j.p.CONTRACT},{'state':'complete'});self.assertEqual((out['state'],ticks,routes),('opened',1,1))
 def test_unknown_route_returns_original_outcome_without_opening_complaint(self):
  out,ticks,routes=self.run_case({'contract':j.p.CONTRACT},{'state':'unknown','error':'original adjacent intent unresolved'});self.assertEqual((out['state'],ticks,routes),('unknown',0,1))
 def test_legacy_profile_uses_original_reader_no_new_route(self):
  out,ticks,routes=self.run_case({'text_schema':'public-visible-text-v2'},{'state':'unknown'});self.assertEqual((out['state'],ticks,routes),('opened',1,0))
if __name__=='__main__':unittest.main()
