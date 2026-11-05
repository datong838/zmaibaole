import importlib.util,tempfile,json,hashlib,unittest,copy
from pathlib import Path
from datetime import datetime,timezone
s=importlib.util.spec_from_file_location('r',str(Path(__file__).resolve().parents[1]/'scripts/resume_focus_preflight.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Test(unittest.TestCase):
 def fixture(self,d):
  def write(name,val):
   p=d/name;p.write_text(json.dumps(val));return r.ref(p)
  job=write('job.json',{'groupid':'123'});page=write('page.json',{'tab':{'tabId':7}});source=write('source.json',{});bm=write('manifest.json',{'root':str(d),'source':source});op=write('op.json',{'state':'preflight','reads':0,'error':r.ERROR,'manifest':{'root':str(d),'review_key':'x','inputs':{'source':source,'page':page,'job':job}}});b=write('batch.json',{'manifest':bm,'state':'hold','completed':[],'current_key':'x','journey':{'state':'complete'},'error':r.ERROR});tabs=write('tabs.json',{'ok':True,'result':[{'windowId':8,'focused':True,'tabs':[{'tabId':7,'windowId':8,'active':True,'url':'https://life.douyin.com/p?groupid=123'}]}]});native=write('native.json',{'frontmost':True});f=write('focus.json',{'kind':'existing-tab-focus-observation-v1','tab_id':7,'active':True,'window_focused':True,'chrome_frontmost':True,'business_actions':False,'browser_restarted':False,'observed_at':datetime.now(timezone.utc).isoformat(),'tabs':tabs,'native':native});return b,op,f
 def test_success_idempotence_and_preserved_original(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);b,o,f=self.fixture(d);before=Path(o['path']).read_bytes();self.assertEqual(r.resume(b,o,f)['state'],'running');self.assertTrue(r.resume(b,o,f)['idempotent']);self.assertEqual(before,Path(o['path']).read_bytes());self.assertTrue((d/('focus-hold-'+b['sha256']+'.json')).exists())
 def test_reject_unsafe_or_changed_case(self):
  for update in ({'reads':1},{'state':'opened'},{'open_command':{}},{'error':'unknown'}):
   with tempfile.TemporaryDirectory() as t:
    d=Path(t);b,o,f=self.fixture(d);op=json.loads(Path(o['path']).read_text());op.update(update);Path(o['path']).write_text(json.dumps(op));o=r.ref(Path(o['path']));original=Path(b['path']).read_bytes()
    with self.assertRaises(ValueError):r.resume(b,o,f)
    self.assertEqual(original,Path(b['path']).read_bytes())
 def test_reject_unfocused_or_stale(self):
  for update in ({'window_focused':False},{'observed_at':'2020-01-01T00:00:00Z'},{'browser_restarted':True}):
   with tempfile.TemporaryDirectory() as t:
    d=Path(t);b,o,f=self.fixture(d);v=json.loads(Path(f['path']).read_text());v.update(update);Path(f['path']).write_text(json.dumps(v));f=r.ref(Path(f['path']))
    with self.assertRaises(ValueError):r.resume(b,o,f)
if __name__=='__main__':unittest.main()
