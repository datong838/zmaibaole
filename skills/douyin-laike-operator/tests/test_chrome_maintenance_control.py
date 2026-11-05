"""Only fake native/UI objects; no process discovery or Chrome interaction."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('chrome_maintenance_test',Path(__file__).resolve().parents[1]/'scripts/chrome-maintenance-control.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class FakeNative:
    def __init__(self,world,out):self.pid=55;self.world=world;self.out=out
    def observe(self):
        self.world['reads']+=1
        return {'pid':55,'frontmost':self.world.get('frontmost',True),'main_window_verified':True,'same_window':self.world.get('same_window',True),'web_areas_count':self.world.get('areas',1),'blank_url':'chrome://newtab/' if self.world.get('blank') else None,'blank_verified':self.world.get('blank',False),'toolbar_targets':self.world.get('targets',1),'business_page_content_read':False}
    def new_tab(self):
        assert json.loads(self.out.read_text())['phase']=='cmd-t-intent';self.world['cmd_t']+=1
        if self.world.get('fail_key'):raise RuntimeError('unknown key result')
        self.world['blank']=not self.world.get('bad_blank')
    def open_control(self):
        assert json.loads(self.out.read_text())['phase']=='toolbar-intent';self.world['presses']+=1
        if self.world.get('fail_press'):raise RuntimeError('unknown press result')
    def close(self):self.world['closed']+=1
class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)/'maintenance.json';self.world={'reads':0,'cmd_t':0,'presses':0,'closed':0};self.factories=0
    def factory(self,expected_pid):self.assertEqual(expected_pid,55);self.factories+=1;return FakeNative(self.world,self.out)
    def run_once(self):return m.run(55,self.out,self.factory)
    def test_cmd_t_then_verified_blank_then_exact_toolbar_once(self):
        result=self.run_once();self.assertEqual(result['state'],'complete');self.assertFalse(result['control_page_verified']);self.assertEqual(self.world['cmd_t'],1);self.assertEqual(self.world['presses'],1)
        before=dict(self.world);self.assertTrue(self.run_once()['already_recorded']);self.assertEqual(self.world,before);self.assertEqual(self.factories,1)
    def test_unknown_key_and_toolbar_never_replay(self):
        for failure in ('fail_key','fail_press'):
            with self.subTest(failure=failure):
                self.out.unlink(missing_ok=True);self.world[failure]=True
                with self.assertRaisesRegex(RuntimeError,'unknown'):self.run_once()
                before=dict(self.world);result=self.run_once();self.assertEqual(result['state'],'unknown');self.assertEqual(self.world,before)
                self.world[failure]=False
    def test_blank_main_toolbar_ambiguity_never_presses(self):
        for bad in ({'bad_blank':True},{'same_window':False},{'areas':2},{'targets':2},{'frontmost':False}):
            with self.subTest(bad=bad):
                self.out.unlink(missing_ok=True);self.world={'reads':0,'cmd_t':0,'presses':0,'closed':0,**bad}
                with patch.object(m.time,'monotonic',side_effect=[0,3]),self.assertRaises(RuntimeError):self.run_once()
                self.assertEqual(self.world['presses'],0)
                if 'frontmost' in bad:self.assertEqual(self.world['cmd_t'],0)
    def test_existing_intent_different_pid_refuses_without_factory(self):
        self.run_once();count=self.factories
        with self.assertRaisesRegex(RuntimeError,'scope-conflict'):m.run(99,self.out,self.factory)
        self.assertEqual(self.factories,count)
    def pending_blank(self):
        self.out.write_text(json.dumps({'mode':'open-maintenance-control','expected_pid':55,'state':'unknown','phase':'verify-blank','cmd_t_returned':True,'error':'maintenance-active-tab-not-blank'}))
        return hashlib.sha256(self.out.read_bytes()).hexdigest()
    def test_original_verified_blank_resumes_only_unattempted_toolbar(self):
        original=self.pending_blank();self.world['blank']=True
        result=m.resume_verified_blank(55,self.out,original,self.factory)
        self.assertEqual(result['state'],'complete');self.assertEqual(self.world['cmd_t'],0);self.assertEqual(self.world['presses'],1)
        self.assertEqual(result['blank_recovery']['original_intent_sha256'],original)
        count=self.factories
        with self.assertRaisesRegex(RuntimeError,'original-intent-changed'):m.resume_verified_blank(55,self.out,original,self.factory)
        self.assertEqual(self.factories,count)
    def test_unknown_toolbar_recovery_cannot_press_twice(self):
        original=self.pending_blank();self.world.update(blank=True,fail_press=True)
        with self.assertRaisesRegex(RuntimeError,'unknown press'):m.resume_verified_blank(55,self.out,original,self.factory)
        current=hashlib.sha256(self.out.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError,'not-unattempted'):m.resume_verified_blank(55,self.out,current,self.factory)
        self.assertEqual(self.world['presses'],1);self.assertEqual(self.world['cmd_t'],0)
    def test_recovery_bad_current_blank_or_changed_original_performs_no_input(self):
        for bad in ({'blank':False},{'blank':True,'areas':2},{'blank':True,'targets':2},{'blank':True,'frontmost':False}):
            with self.subTest(bad=bad):
                original=self.pending_blank();before=self.out.read_bytes();self.world.update({'blank':True,'areas':1,'targets':1,'frontmost':True,**bad})
                with self.assertRaisesRegex(RuntimeError,'current-blank-unverified'):m.resume_verified_blank(55,self.out,original,self.factory)
                self.assertEqual(self.out.read_bytes(),before);self.assertEqual(self.world['presses'],0);self.assertEqual(self.world['cmd_t'],0)
        original=self.pending_blank();count=self.factories
        with self.assertRaisesRegex(RuntimeError,'original-intent-changed'):m.resume_verified_blank(55,self.out,'0'*64,self.factory)
        self.assertEqual(self.factories,count)
    def test_observe_never_walks_or_reads_business_webarea_content(self):
        native=object.__new__(m.MaintenanceInspector);native.root=1;native.pid=55;native.cf=SimpleNamespace(CFEqual=lambda a,b:a==b)
        attrs={1:{'AXFrontmost':True},2:{'AXRole':'AXWindow','AXSubrole':'AXStandardWindow','AXMain':True},3:{'AXRole':'AXWebArea','AXURL':'https://life.douyin.com/private?token=not-logged'}};reads=[]
        def get(e,key):
            reads.append((e,key))
            if e==3:self.assertIn(key,('AXRole','AXURL'))
            return attrs.get(e,{}).get(key)
        def array(e,key):
            self.assertNotEqual(e,3,'must not read WebArea children')
            return [2] if e==1 else [3] if e==2 else []
        native.get=get;native.array=array;native.value=lambda e,key:2
        proof=native.observe();self.assertFalse(proof['blank_verified']);self.assertIsNone(proof['blank_url']);self.assertNotIn('life.douyin.com',json.dumps(proof))
        attrs[3]['AXURL']='chrome://new-tab-page/';self.assertTrue(native.observe()['blank_verified'])
if __name__=='__main__':unittest.main()
