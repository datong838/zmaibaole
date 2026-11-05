"""Failed staging recovery on original job, fake Native only, no paste/Return."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
import messenger as m
import ui
import files
from test_sender import MockNative
class StageResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);file=self.root/'test.txt';file.write_text('fixture')
        self.path,self.state=m.prepare('same-stage-key','group','测试群请忽略',file=file,directory=self.root/'jobs');self.native=MockNative()
        m.advance(self.path,lambda:self.native);m.advance(self.path,lambda:self.native)
        self.state=json.loads(self.path.read_text());self.assertEqual(self.state['phase'],'stage');self.state.update(status='failed',error='ui-tree-incomplete');m.atomic(self.path,self.state)
    def test_safe_stage_resume_keeps_original_job_and_only_reads(self):
        original_job=copy.deepcopy(self.state['job']);result=m.resume_before_send(self.path,lambda:self.native)
        self.assertEqual(result['status'],'running');self.assertEqual(result['phase'],'locate');self.assertEqual(result['job'],original_job);self.assertEqual(result['fingerprint'],self.state['fingerprint']);self.assertEqual(self.native.keys,[]);self.assertEqual(self.native.draft,'')
    def test_any_send_paste_return_choice_marker_or_event_refuses_before_native(self):
        original=copy.deepcopy(self.state)
        markers=['send_intent_at','paste_empty_composer_verified','owned_image_paste','image_return_intent_at','original_file_choice_intent_at','automated_send','user_sent','image_proof']
        variants=[{k:True} for k in markers]+[{'events':original['events']+[{'stage':e}]} for e in ['send-intent','file-pasted','file-confirm-intent','image-return-intent','original-file-choice-intent']]
        for fields in variants:
            m.atomic(self.path,{**original,**fields})
            with self.subTest(fields=fields),self.assertRaisesRegex(m.SendError,'resume-not-safe'):m.resume_before_send(self.path,lambda:(_ for _ in ()).throw(AssertionError('must not instantiate Native')))
    def test_wrong_recipient_pid_or_nonempty_composer_does_not_resume(self):
        for field,value in [('target','方景堂'),('draft','owned? unknown draft')]:
            m.atomic(self.path,self.state);setattr(self.native,field,value)
            with self.subTest(field=field),self.assertRaises(RuntimeError):m.resume_before_send(self.path,lambda:self.native)
            setattr(self.native,field,'测试群请忽略' if field=='target' else '')
        bad={**self.state,'pid':999};m.atomic(self.path,bad)
        with self.assertRaisesRegex(m.SendError,'resume-context'):m.resume_before_send(self.path,lambda:self.native)
        self.assertEqual(self.native.keys,[])
    def test_changed_payload_and_incomplete_snapshot_cannot_resume(self):
        bad=copy.deepcopy(self.state);bad['job']['file_name']='changed';m.atomic(self.path,bad)
        with self.assertRaises(RuntimeError):m.resume_before_send(self.path,lambda:self.native)
        m.atomic(self.path,self.state);original=self.native.tree
        self.native.tree=lambda:{**original(),'truncated':True,'truncation_reason':'deadline'}
        with self.assertRaises(ui.UIError):m.resume_before_send(self.path,lambda:self.native)
    def test_failed_inner_file_tree_reports_actual_latest_diagnostics(self):
        self.state.update(status='running');m.atomic(self.path,self.state)
        class Tracked(MockNative):
            def tree(self):
                self.last_snapshot_metadata={'read_scope':'application-windows-complete','node_count':10,'truncated':False,'truncation_reason':None};return super().tree()
        native=Tracked()
        def failed(n,*args):
            n.last_snapshot_metadata={'read_scope':'application-windows-complete','node_count':499,'truncated':True,'truncation_reason':'deadline'}
            raise ui.UIError('ui-tree-incomplete')
        with patch.object(files,'stage_file',failed):result=m.advance(self.path,lambda:native)
        self.assertEqual(result['status'],'failed');self.assertEqual(result['last_read']['node_count'],499);self.assertEqual(result['last_read']['truncation_reason'],'deadline');self.assertFalse(result.get('send_intent_at'));self.assertEqual(native.keys,[])
if __name__=='__main__':unittest.main()
