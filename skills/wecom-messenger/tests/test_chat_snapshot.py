"""Fake AX graphs only. No native process or UI access."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import chat_snapshot as c
import messenger as m
import ui
from test_sender import fixture,MockNative
class FakeAX:
    def __init__(self,messages=('sent message',),extra_conversations=3000):
        self.root=1;self.pid=123;self.by_path={};self.data={};self.children={};self.reads=[];self.refs={};self.n=1
        snap=fixture(messages=messages)
        # Menus and an unrelated recent table are huge, but must not be scanned.
        recent=snap['tree']['children'][0]['children'][0]['children'][4]['children'][0]
        recent['children']=[{'role':'AXRow','children':[],'AXValue':'irrelevant'} for _ in range(extra_conversations)]
        snap['tree']['children'].insert(0,{'role':'AXMenuBar','children':[{'role':'AXMenuItem','children':[]} for _ in range(3000)]})
        def store(node):
            eid=self.n;self.n+=1;self.data[eid]={**node};self.refs[id(node)]=eid;self.children[eid]=[store(ch) for ch in node.get('children',[])];return eid
        self.root=store(snap['tree']);self.window=self.children[self.root][1]
        self.tables=[e for e,d in self.data.items() if d['role']=='AXTable'];self.recent=self.tables[0];self.transcript=self.tables[1]
        self.composer=next(e for e,d in self.data.items() if d['role']=='AXTextArea' and 'AXValue' in d.get('settable',[]));self.changed=False
    def get(self,e,key):self.reads.append((e,key));return self.data[e].get('role') if key=='AXRole' else self.data[e].get(key)
    def value(self,e,key):return self.window if key=='AXMainWindow' else None
    def same_element(self,a,b):return a==b
    def scoped_array(self,e,key,required=False):
        self.reads.append((e,key))
        if key=='AXWindows':return [self.window]
        if key=='AXRows':return [ch for ch in self.children[e] if self.data[ch]['role']=='AXRow']
        if key=='AXChildren':return list(self.children[e])
        return None
    def scoped_settable(self,e,key):return key in self.data[e].get('settable',[])
class ChatSnapshotTests(unittest.TestCase):
    def test_large_unrelated_menu_and_recent_list_are_excluded_complete_transcript_kept(self):
        n=FakeAX(messages=tuple('message '+str(i) for i in range(100)))
        snapshot=c.capture(n);self.assertFalse(snapshot['truncated'],snapshot['truncation_reason']);ctx=ui.context(snapshot)
        self.assertEqual(snapshot['transcript_rows'],100);self.assertEqual(ui.message_count(ctx,'message 99'),1)
        self.assertLess(snapshot['discovery_node_count'],30);self.assertNotIn((n.recent,'AXChildren'),n.reads)
        self.assertNotIn('irrelevant',json.dumps(snapshot));self.assertTrue(snapshot['transcript_complete'])
    def test_same_complete_chat_uses_public_batch_to_stay_within_original_deadline(self):
        now=[0.0];n=FakeAX(messages=tuple('message '+str(i) for i in range(100)));get=n.get
        def slow_get(e,key):now[0]+=.03;return get(e,key)
        n.get=slow_get;failed=c.capture(n,clock=lambda:now[0]);self.assertEqual(failed['truncation_reason'],'deadline')
        now[0]=0;calls=[]
        def batch(e,keys):
            now[0]+=.03;calls.append(tuple(keys));return {key:n.data[e].get('role') if key=='AXRole' else n.data[e].get(key) for key in keys}
        n.node_attributes=batch;n._attribute_batches={'stale':True};snap=c.capture(n,clock=lambda:now[0]);self.assertFalse(snap['truncated'],snap['truncation_reason']);self.assertEqual(snap['transcript_rows'],100);self.assertEqual(ui.message_count(ui.context(snap),'message 99'),1);self.assertEqual(n._attribute_batches,{});self.assertTrue(all(keys==('AXRole',)+c.FIELDS for keys in calls));self.assertLess(now[0],55)
    def test_incomplete_or_failed_batch_never_looks_like_empty_composer(self):
        for failure in ('missing','failed','role-changed'):
            n=FakeAX()
            def batch(e,keys):
                result={key:n.data[e].get('role') if key=='AXRole' else n.data[e].get(key) for key in keys}
                if e==n.composer:
                    if failure=='failed':raise RuntimeError('batch-input-value-unreadable')
                    if failure=='missing':result.pop('AXValue')
                    else:result['AXRole']='AXGroup'
                return result
            n.node_attributes=batch;snap=c.capture(n);self.assertTrue(snap['truncated']);self.assertFalse(snap['transcript_complete'])
            with self.assertRaises(ui.UIError):ui.context(snap)
    def test_budget_deadline_depth_and_child_error_fail_closed(self):
        for kwargs in ({'max_nodes':10},{'max_depth':2},{'timeout':-1}):
            with self.subTest(kwargs=kwargs):
                snapshot=c.capture(FakeAX(),**kwargs);self.assertTrue(snapshot['truncated']);self.assertTrue(snapshot['truncation_reason'])
                with self.assertRaises(ui.UIError):ui.context(snapshot)
        n=FakeAX();original=n.scoped_array
        def broken(e,key,required=False):
            if e==n.transcript and key=='AXChildren':raise RuntimeError('AXChildren-error')
            return original(e,key,required)
        n.scoped_array=broken;snapshot=c.capture(n);self.assertEqual(snapshot['truncation_reason'],'AXChildren-error')
    def test_declared_rows_and_public_row_collection_must_match(self):
        n=FakeAX();n.data[n.transcript]['AXRowCount']=2
        self.assertEqual(c.capture(n)['truncation_reason'],'transcript-row-count-mismatch')
        n=FakeAX();original=n.scoped_array
        n.scoped_array=lambda e,k,required=False:[] if e==n.transcript and k=='AXRows' else original(e,k,required)
        self.assertEqual(c.capture(n)['truncation_reason'],'transcript-row-set-mismatch')
    def test_transcript_append_or_header_change_during_capture_is_unknown(self):
        n=FakeAX();original=n.scoped_array;reads=0
        def changed(e,key,required=False):
            nonlocal reads
            value=original(e,key,required)
            if e==n.transcript and key=='AXChildren':
                reads+=1
                if reads>2:return value+value
            return value
        n.scoped_array=changed;self.assertEqual(c.capture(n)['truncation_reason'],'transcript-changed-during-read')
    def test_exact_header_mismatch_never_confirms_another_recipient(self):
        n=FakeAX();snap=c.capture(n);ctx=ui.context(snap)
        with self.assertRaises(ui.UIError):ui.verify(ctx,{'target':'其他群','kind':'group'})
    def test_verify_sent_uses_targeted_read_only_path_and_never_replays_return(self):
        class Directed(MockNative):
            def __init__(self):super().__init__();self.directed=0
            def tree(self):raise AssertionError('full tree must not run during verify-sent')
            def chat_tree(self):self.directed+=1;return c.capture(FakeAX(messages=('自动化测试消息',)))
            def key(self,*args,**kwargs):raise AssertionError('must not repeat Return')
            def set_text(self,*args):raise AssertionError('must not write')
            def focus(self,*args):raise AssertionError('must not focus')
        with tempfile.TemporaryDirectory() as directory:
            path,state=m.prepare('read-only-test','group','测试群请忽略',text='自动化测试消息',directory=directory)
            state.update(phase='verify-sent',status='unknown',send_intent_at='already-sent',pid=123,baseline=0);m.atomic(path,state)
            n=Directed();result=m.advance(path,lambda:n);self.assertEqual(result['status'],'complete');self.assertEqual(n.directed,1);self.assertTrue(result['last_read']['transcript_complete'])
    def test_enabled_image_button_survives_scoped_projection(self):
        import images
        from test_images import image_snapshot
        n=FakeAX(messages=(),extra_conversations=0);row=images.transcript_rows(ui.context(image_snapshot(with_image=True)))[-1]
        def store(node):
            eid=n.n;n.n+=1;n.data[eid]={**node};n.children[eid]=[store(ch) for ch in node.get('children',[])];return eid
        n.children[n.transcript]=[store(row)];snap=c.capture(n);self.assertFalse(snap['truncated']);last=images.transcript_rows(ui.context(snap))[-1];self.assertTrue(images.image_row(last))
        button=next(x for x in ui.nodes(last) if x['role']=='AXButton');self.assertIs(button['AXEnabled'],True);button['AXEnabled']=False;self.assertFalse(images.image_row(last))
    def test_recorded_post_return_row_confirms_readonly_without_weakening_prefix(self):
        import images
        root=Path(__file__).resolve().parents[3];evidence=root/'work/live-acceptance/complaints/live-profile/lumos-wecom-post-return.ax.json';job=root/'runtime/wecom-messenger/08ca25002cd0ab2f6cadeab6.json'
        if not evidence.exists() or not job.exists():self.skipTest('local live receipt unavailable')
        snapshot=json.loads(evidence.read_text());state=json.loads(job.read_text());before_bytes=job.read_bytes()
        def project(node):return {'role':node['role'],'path':node['path'],'children':[project(ch) for ch in node.get('children',[])],**{k:node[k] for k in c.FIELDS if k in node},**({'settable':node['settable']} if node.get('settable') else {})}
        snapshot['tree']=project(snapshot['tree']);snapshot.update(read_scope='current-chat-readonly',transcript_complete=True)
        images.verify_image(state,ui.context(snapshot),m.event,m.finish);self.assertEqual(state['status'],'complete');self.assertEqual(job.read_bytes(),before_bytes)
    def test_incomplete_targeted_read_remains_unknown_with_diagnostics(self):
        class Directed(MockNative):
            def chat_tree(self):return c.capture(FakeAX(),max_nodes=2)
            def tree(self):raise AssertionError('no fallback')
            def key(self,*args,**kwargs):raise AssertionError('no resend')
        with tempfile.TemporaryDirectory() as directory:
            path,state=m.prepare('read-only-unknown','group','测试群请忽略',text='message',directory=directory)
            state.update(phase='verify-sent',status='unknown',send_intent_at='already-sent',pid=123,baseline=0);m.atomic(path,state)
            for _ in range(2):result=m.advance(path,Directed)
            self.assertEqual(result['status'],'unknown');self.assertEqual(result['phase'],'verify-sent');self.assertEqual(result['error'],'ui-tree-incomplete');self.assertEqual(result['last_read']['truncation_reason'],'node-limit')
if __name__=='__main__':unittest.main()
