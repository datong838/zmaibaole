import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import images
import messenger as m
import ui
from test_sender import fixture,MockNative

def image_snapshot(draft='',with_image=False,extra=False):
    snap=fixture(draft=draft,messages=['existing text'])
    ctx=ui.context(snap)
    if draft:
        c=ctx['composer'];c['children']=[{'role':'AXUnknown','AXSubrole':'AXTextAttachment','path':c['path']+[0],'children':[]}]
    if with_image:
        table=ctx['transcript'];p=table['path']+[len(table['children'])]
        row={'role':'AXRow','path':p,'children':[{'role':'AXCell','path':p+[0],'children':[
            {'role':'AXStaticText','AXValue':'00:20','path':p+[0,0],'children':[]},
            {'role':'AXButton','AXEnabled':True,'path':p+[0,1],'children':[]}]}]}
        table['children'].append(row)
        if extra:table['children'].append(copy.deepcopy(row))
    return snap

class ImageSenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        source=self.root/'fixture.png';source.write_bytes(b'fixture-image')
        self.path,self.state=m.prepare('image','group','测试群请忽略',file=source,directory=self.root)
        self.state.update(phase='file-confirm',status='unknown',pid=123,baseline=0,paste_empty_composer_verified=True,send_intent_at=m.now(),
                          events=[{'stage':'send-intent','sha256':self.state['job']['file_sha256']},{'stage':'file-pasted'}])
        self.native=MockNative();self.native.tree=lambda:image_snapshot('\ufffc');self.native.attachment_attributed=lambda node:123
        self.proof={'width':120,'height':80,'rgba_sha256':'pixels','source_sha256':self.state['job']['file_sha256'],
                    'rtf_sha256':'rtf','method':'public-AXRTFForRange-exact-decoded-pixels'}
        images.bind_owned_paste(self.state,ui.context(self.native.tree()),{'file_url_verified':True,'types':['public.file-url'],'change_count':7},m.event)
        self.proof=self.state['owned_image_paste']
    def confirm(self):
        images.confirm_image(self.native,self.state,ui.context(self.native.tree()),self.path,m.atomic,m.event)
    def test_transient_layout_reads_wait_for_exact_original_proof_without_rebase(self):
        changed=image_snapshot('\ufffc');ui.context(changed)['composer']['children'][0]['role']='AXImage'
        original=copy.deepcopy(self.state['owned_image_paste']);calls=[]
        self.native.tree=lambda:(calls.append(1) or image_snapshot('\ufffc'))
        with patch('images.time.sleep'):images.confirm_image(self.native,self.state,ui.context(changed),self.path,m.atomic,m.event)
        self.assertEqual(self.state['owned_image_paste'],original);self.assertEqual(self.native.keys,[(36,13)]);self.assertGreaterEqual(len(calls),2)
    def test_persistent_layout_difference_never_changes_original_baseline_or_sends(self):
        changed=image_snapshot('\ufffc',with_image=True);self.native.tree=lambda:changed;original=copy.deepcopy(self.state['owned_image_paste'])
        with patch('images.time.sleep'),self.assertRaisesRegex(ui.UIError,'draft-or-transcript-changed'):images.confirm_image(self.native,self.state,ui.context(changed),self.path,m.atomic,m.event)
        self.assertEqual(self.state['owned_image_paste'],original);self.assertEqual(self.native.keys,[])
    def test_exact_proof_durable_before_one_return(self):
        def key(code,*args):
            saved=json.loads(self.path.read_text());self.assertEqual(code,36)
            self.assertEqual(saved['phase'],'image-verify-sent');self.assertEqual(saved['image_proof'],self.proof)
            self.native.keys.append(code)
        self.native.key=key;self.confirm();self.assertEqual(self.native.keys,[36])
        with self.assertRaisesRegex(ui.UIError,'no-replay'):self.confirm()
        self.assertEqual(self.native.keys,[36])
    def test_owned_exact_image_and_new_row_complete(self):
        self.confirm();images.verify_image(self.state,ui.context(image_snapshot(with_image=True)),m.event,m.finish)
        self.assertEqual(self.state['status'],'complete');self.assertTrue(self.state['ui_confirmed'])
        self.assertFalse(self.state['delivery_confirmed']);self.assertFalse(self.state['user_sent'])
    def test_wrong_image_identity_never_sends(self):
        self.state['owned_image_paste']['source_sha256']='wrong'
        with self.assertRaisesRegex(ui.UIError,'proof-corrupt'):
            images.confirm_image(self.native,self.state,ui.context(self.native.tree()),self.path,m.atomic,m.event)
        self.assertFalse(self.native.keys)
    def test_unknown_return_not_replayed_through_state_machine(self):
        def key(*args):self.native.keys.append(args);raise m.AXError('unknown-key-outcome')
        self.native.key=key;m.atomic(self.path,self.state)
        first=m.advance(self.path,lambda:self.native)
        self.assertEqual(first['phase'],'image-verify-sent')
        for _ in range(3):m.advance(self.path,lambda:self.native)
        self.assertEqual(len(self.native.keys),1)
    def test_extra_rows_or_changed_prefix_rejected(self):
        self.confirm()
        with self.assertRaisesRegex(ui.UIError,'difference-ambiguous'):
            images.verify_image(self.state,ui.context(image_snapshot(with_image=True,extra=True)),m.event,m.finish)
        snap=image_snapshot(with_image=True);ctx=ui.context(snap)
        next(n for n in ui.nodes(ctx['transcript']) if n.get('AXValue')=='existing text')['AXValue']='changed'
        with self.assertRaisesRegex(ui.UIError,'difference-ambiguous'):images.verify_image(self.state,ctx,m.event,m.finish)
    def test_failure_or_nonimage_bubble_rejected(self):
        self.confirm();ctx=ui.context(image_snapshot(with_image=True));row=images.transcript_rows(ctx)[-1]
        button=next(n for n in ui.nodes(row) if n['role']=='AXButton');button['AXHelp']='重新发送'
        with self.assertRaisesRegex(ui.UIError,'new-row-not-verified'):images.verify_image(self.state,ctx,m.event,m.finish)
    def test_child_reordering_is_not_changed_message_content(self):
        snap=image_snapshot(with_image=True);row=images.transcript_rows(ui.context(snap))[-1];before=images.row_signature(row)
        row['children'][0]['children'].reverse();self.assertEqual(before,images.row_signature(row))
        row['children'][0]['children'][0]['AXHelp']='发送失败';self.assertNotEqual(before,images.row_signature(row))
    def test_empty_static_placeholders_do_not_change_old_message(self):
        row=images.transcript_rows(ui.context(image_snapshot(with_image=True)))[-1];before=images.row_signature(row)
        row['children'][0]['children'].append({'role':'AXStaticText','children':[]})
        self.assertEqual(before,images.row_signature(row))
        row['children'][0]['children'][-1]['AXValue']='发送失败';self.assertNotEqual(before,images.row_signature(row))
    def test_user_sent_old_job_without_proof_cannot_be_robot_receipt(self):
        with self.assertRaisesRegex(ui.UIError,'proof-missing'):
            images.verify_image(self.state,ui.context(image_snapshot(with_image=True)),m.event,m.finish)
    def test_old_unbound_attachment_never_sent(self):
        self.state.pop('owned_image_paste')
        with self.assertRaisesRegex(ui.UIError,'proof-missing'):self.confirm()
        self.assertFalse(self.native.keys)
    def test_process_session_change_never_sends(self):
        with patch('images.OWNERSHIP_SESSION','new-process'):
            with self.assertRaisesRegex(ui.UIError,'session-ended'):self.confirm()
        self.assertFalse(self.native.keys)
    def test_missing_own_clipboard_type_never_binds(self):
        with self.assertRaisesRegex(ui.UIError,'clipboard-proof-missing'):
            images.bind_owned_paste(self.state,ui.context(self.native.tree()),{'change_count':7,'types':[]},m.event)
    def test_complete_own_paste_chain_return_and_passive_receipt(self):
        from contextlib import contextmanager
        source=self.root/'new.png';source.write_bytes(b'controlled-new-image')
        path,state=m.prepare('controlled-image','group','测试群请忽略',file=source,directory=self.root)
        native=MockNative();native.pastes=0;native.image_sent=False
        native.tree=lambda:image_snapshot(native.draft,with_image=native.image_sent)
        def key(code,*args,**kwargs):
            if code==53:return
            saved=json.loads(path.read_text())
            if code==9:
                self.assertTrue(saved['paste_empty_composer_verified']);native.draft='\ufffc';native.pastes+=1
            elif code==36:
                self.assertEqual(saved['phase'],'image-verify-sent');self.assertTrue(saved['image_proof']['clipboard']['file_url_verified'])
                native.sends+=1;native.draft='';native.image_sent=True
        native.key=key
        @contextmanager
        def clipboard(_):
            yield {'assert_owned':lambda:{'change_count':22,'types':['public.file-url'],'file_url_verified':True},'restored':True,'concurrent_change':False}
        with patch('files.file_url',clipboard),patch('files.time.sleep'):
            for _ in range(10):state=m.advance(path,lambda:native)
        self.assertEqual(state['status'],'complete',state);self.assertEqual(native.pastes,1);self.assertEqual(native.sends,1)
    def test_wrong_target_cannot_focus_or_send(self):
        self.state['job']['target']='other'
        with self.assertRaisesRegex(ui.UIError,'recipient-mismatch'):self.confirm()
        self.assertFalse(self.native.keys)

if __name__=='__main__':unittest.main()
