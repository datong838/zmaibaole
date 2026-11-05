import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import messenger as m
import ui

def fixture(name='测试群请忽略',kind='group',draft='',messages=()):
    def n(role,children=(),**kwargs):return {'role':role,'children':list(children),**kwargs}
    headers=[n('AXButton',AXHelp='添加群成员')]
    if kind=='group':headers += [n('AXTextField',AXValue=name),n('AXButton',AXHelp='聊天信息')]
    else:headers += [n('AXStaticText',AXValue=name)]
    transcript=n('AXTable',[n('AXRow',[n('AXCell',[n('AXTextArea',AXValue=t)])]) for t in messages])
    composer=n('AXTextArea',AXValue=draft,settable=['AXValue','AXFocused'])
    recent=n('AXScrollArea',[n('AXTable',[n('AXRow',[n('AXCell',[n('AXStaticText',AXValue='测试群请忽略')])],settable=['AXSelected']),n('AXRow',[n('AXCell',[n('AXStaticText',AXValue='方景堂')])],settable=['AXSelected'])])])
    shell=n('AXSplitGroup',headers+[n('AXTextField',settable=['AXValue']),recent,n('AXSplitGroup',[n('AXScrollArea',[transcript]),n('AXScrollArea',[composer])])])
    root=n('AXApplication',[n('AXWindow',[shell],AXSubrole='AXStandardWindow',AXTitle='企业微信')])
    def paths(node,path):
        node['path']=path
        for i,c in enumerate(node['children']):paths(c,path+[i])
    paths(root,[])
    return {'ok':True,'pid':123,'tree':root,'truncated':False}

class MockNative:
    def __init__(self):self.draft='';self.messages=[];self.sends=0;self.target='测试群请忽略';self.kind='group';self.keys=[];self.fail_key=False
    def tree(self):return fixture(self.target,self.kind,self.draft,self.messages)
    def set_text(self,node,text):self.draft=text
    def focus(self,node):pass
    def flag(self,*args):pass
    def key(self,*args,**kwargs):
        self.keys.append(args)
        if self.fail_key:raise m.AXError('event-result-unknown')
        self.sends+=1;self.messages.append(self.draft);self.draft=''
    def close(self):pass

class SenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def prepare(self,**args):return m.prepare('test-1',args.pop('kind','group'),args.pop('target','测试群请忽略'),text='自动化测试消息',directory=self.root,**args)
    def test_production_and_other_targets_rejected(self):
        for kind,target in [('group','生产群'),('person','其他人')]:
            with self.assertRaises(m.SendError):self.prepare(kind=kind,target=target)
        with self.assertRaises(m.SendError):self.prepare(scope='production')
    def test_person_exact_authorization(self):
        p,s=self.prepare(kind='person',target='方景堂');self.assertEqual(s['job']['kind'],'person')
    def test_type_or_name_mismatch_blocks(self):
        job={'kind':'person','target':'测试群请忽略'}
        with self.assertRaises(ui.UIError):ui.verify(ui.context(fixture()),job)
    def test_complete_once_and_idempotent(self):
        path,state=self.prepare();native=MockNative()
        for _ in range(7):state=m.advance(path,lambda:native)
        self.assertEqual(state['status'],'complete');self.assertEqual(native.sends,1)
        again,_=self.prepare();self.assertEqual(path,again)
        m.advance(path,lambda:native);self.assertEqual(native.sends,1)
        self.assertTrue(state['ui_confirmed']);self.assertFalse(state['delivery_confirmed'])
    def test_durable_intent_before_send(self):
        path,state=self.prepare();native=MockNative();original=native.key
        def key(*args,**kwargs):
            saved=json.loads(path.read_text());self.assertEqual(saved['phase'],'verify-sent');self.assertEqual(saved['status'],'unknown')
            original(*args,**kwargs)
        native.key=key
        for _ in range(5):state=m.advance(path,lambda:native)
        self.assertEqual(state['status'],'complete')
    def test_unknown_send_never_replayed(self):
        path,state=self.prepare();native=MockNative();native.fail_key=True
        for _ in range(10):state=m.advance(path,lambda:native)
        self.assertEqual(len(native.keys),1);self.assertEqual(state['status'],'unknown')
    def test_existing_draft_never_overwritten(self):
        path,state=self.prepare();native=MockNative();native.draft='用户的草稿'
        for _ in range(3):state=m.advance(path,lambda:native)
        self.assertEqual(state['status'],'failed');self.assertEqual(native.draft,'用户的草稿');self.assertEqual(native.sends,0)
    def test_changed_draft_blocks_send(self):
        path,state=self.prepare();native=MockNative()
        for _ in range(3):m.advance(path,lambda:native)
        native.draft='被用户修改'
        state=m.advance(path,lambda:native);self.assertEqual(state['status'],'failed');self.assertEqual(native.sends,0)
    def test_changed_job_or_reused_key_rejected(self):
        path,state=self.prepare()
        with self.assertRaises(m.SendError):self.prepare(target='方景堂',kind='person')
        state['job']['text']='改过了';m.atomic(path,state)
        with self.assertRaises(m.SendError):m.advance(path,MockNative)
    def test_process_change_blocks_send(self):
        path,state=self.prepare();native=MockNative();m.advance(path,lambda:native)
        state=json.loads(path.read_text());state['pid']=999;m.atomic(path,state)
        state=m.advance(path,lambda:native);self.assertEqual(state['status'],'failed');self.assertEqual(native.sends,0)
    def test_file_hash_and_empty_file_guards(self):
        file=self.root/'test.txt';file.write_text('仅测试')
        path,state=m.prepare('f','group','测试群请忽略',file=file,directory=self.root)
        file.write_text('changed')
        with self.assertRaises(m.SendError):m.advance(path,MockNative)
        file.write_bytes(b'')
        with self.assertRaises(m.SendError):m.prepare('f2','group','测试群请忽略',file=file,directory=self.root)
    def test_failed_bubble_cannot_be_reported_successful(self):
        snap=fixture(messages=['test'])
        ctx=ui.context(snap)
        row=next(n for n in ui.nodes(ctx['transcript']) if n['role']=='AXRow')
        row['children'].append({'role':'AXButton','AXHelp':'重新发送','path':row['path']+[1],'children':[]})
        with self.assertRaisesRegex(ui.UIError,'client-send-failed'):ui.message_count(ctx,'test')
    def test_final_newline_trim_is_not_a_failed_send(self):
        ctx=ui.context(fixture(messages=['完整正文\n第二行']))
        self.assertEqual(ui.message_count(ctx,'完整正文\n第二行\n'),1)
        self.assertEqual(ui.message_count(ctx,'完整正文'),0)
    def test_truncated_tree_refused(self):
        snap=fixture();snap['truncated']=True
        with self.assertRaises(ui.UIError):ui.context(snap)



class FileFlowTest(unittest.TestCase):
    setUp=SenderTest.setUp
    tearDown=SenderTest.tearDown
    def test_file_paste_path_confirmation_and_once_only(self):
        from contextlib import contextmanager
        from unittest.mock import patch
        source=self.root/'仅测试.xlsx';source.write_bytes(b'fixture')
        path,state=m.prepare('file','group','测试群请忽略',file=source,directory=self.root)
        native=MockNative();native.attachment=None;native.pastes=0
        base_tree=native.tree
        def tree():
            snap=base_tree()
            if native.attachment:
                c=ui.context(snap)['composer']
                c['children']=[{'role':'AXUnknown','AXSubrole':'AXTextAttachment','AXURL':native.attachment,'path':c['path']+[0],'children':[]}]
            return snap
        native.tree=tree
        def key(code,*args,**kwargs):
            if code==53:return
            saved=json.loads(path.read_text());self.assertTrue(saved.get('send_intent_at'))
            if code==9:
                native.pastes+=1;native.attachment=source.as_uri();native.draft='\ufffc'
            elif code==36:
                self.assertEqual(saved['phase'],'verify-sent');native.sends+=1;native.messages.append(source.name);native.draft='';native.attachment=None
        native.key=key
        @contextmanager
        def clipboard(_):yield {'restored':True,'concurrent_change':False}
        with patch('files.file_url',clipboard),patch('files.time.sleep'):
            for _ in range(9):state=m.advance(path,lambda:native)
        self.assertEqual(state['status'],'complete',state);self.assertEqual(native.pastes,1);self.assertEqual(native.sends,1)
        self.assertTrue(any(e.get('clipboard_restored') for e in state['events']))
    def test_same_filename_different_path_blocks(self):
        from files import advance_file
        source=self.root/'x.xlsx';source.write_bytes(b'fixture')
        snap=fixture(draft='\ufffc');composer=ui.context(snap)['composer']
        composer['children']=[{'role':'AXUnknown','AXSubrole':'AXTextAttachment','AXURL':'file:///another/x.xlsx','path':composer['path']+[0],'children':[]}]
        state={'job':{'target':'测试群请忽略','kind':'group','file':str(source),'file_name':'x.xlsx'},'phase':'file-confirm','baseline':0}
        native=MockNative()
        with self.assertRaisesRegex(ui.UIError,'attachment-path-unverified'):
            advance_file(native,state,snap,self.root/'state.json',m.atomic,m.event,m.finish)
        self.assertEqual(native.keys,[])
    def test_resume_forbidden_after_send_intent(self):
        path,state=m.prepare('resume','group','测试群请忽略',text='test',directory=self.root)
        state.update(status='failed',phase='verify',send_intent_at=m.now());m.atomic(path,state)
        with self.assertRaisesRegex(m.SendError,'resume-not-safe'):m.resume_before_send(path,MockNative)
    def test_safe_resume_does_not_send_or_erase(self):
        path,state=m.prepare('resume','group','测试群请忽略',text='test',directory=self.root)
        state.update(status='failed',phase='verify',pid=123);m.atomic(path,state)
        native=MockNative();state=m.resume_before_send(path,lambda:native)
        self.assertEqual(state['phase'],'locate');self.assertEqual(native.sends,0);self.assertEqual(native.draft,'')

    def test_original_spreadsheet_choice_once_and_durable(self):
        from files import advance_file
        path=self.root/'choice.json';snap=fixture()
        sheet={'role':'AXSheet','path':[0,4],'children':[
            {'role':'AXTextArea','AXValue':'发送到聊天','path':[0,4,0],'children':[]},
            {'role':'AXStaticText','AXValue':'x.xlsx','path':[0,4,1],'children':[]},
            {'role':'AXButton','AXTitle':'转为在线表格','AXEnabled':True,'path':[0,4,2],'children':[]},
            {'role':'AXButton','AXTitle':'使用原文件','AXEnabled':True,'path':[0,4,3],'children':[]}]}
        snap['tree']['children'][0]['children'].append(sheet)
        state={'job':{'target':'测试群请忽略','kind':'group','file_name':'x.xlsx'},'phase':'file-confirm','baseline':0,
               'send_intent_at':m.now(),'events':[{'stage':'file-pasted'}]}
        pressed=[];native=MockNative()
        def press(button):
            saved=json.loads(path.read_text());self.assertTrue(saved['original_file_choice_intent_at'])
            self.assertEqual(button['AXTitle'],'使用原文件');pressed.append(button)
        native.press=press
        advance_file(native,state,snap,path,m.atomic,m.event,m.finish)
        self.assertEqual(len(pressed),1);self.assertEqual(state['phase'],'file-confirm')
        with self.assertRaisesRegex(ui.UIError,'unknown-no-replay'):advance_file(native,state,snap,path,m.atomic,m.event,m.finish)
        self.assertEqual(len(pressed),1)
    def test_original_spreadsheet_choice_wrong_filename_never_clicked(self):
        from files import advance_file
        snap=fixture();sheet={'role':'AXSheet','path':[0,4],'children':[]}
        for i,text in enumerate(['发送到聊天','other.xlsx','转为在线表格','使用原文件']):
            sheet['children'].append({'role':'AXButton' if i>1 else 'AXStaticText','AXValue':text,'AXEnabled':True,'path':[0,4,i],'children':[]})
        snap['tree']['children'][0]['children'].append(sheet)
        state={'job':{'target':'测试群请忽略','kind':'group','file_name':'x.xlsx'},'phase':'file-confirm','baseline':0,
               'send_intent_at':m.now(),'events':[{'stage':'file-pasted'}]}
        with self.assertRaisesRegex(ui.UIError,'filename-mismatch'):advance_file(MockNative(),state,snap,self.root/'x.json',m.atomic,m.event,m.finish)

if __name__=='__main__':unittest.main()
