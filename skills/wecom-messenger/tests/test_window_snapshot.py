"""Native.tree public window projection with fake AX, no OS calls."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native import Native,AXError
import ui
class WindowSnapshotTests(unittest.TestCase):
    def fake(self):
        n=object.__new__(Native);n.root=1;n.pid=123;n.refs=[]
        data={1:{'role':'AXApplication'},2:{'role':'AXMenuBar'},3:{'role':'AXWindow','AXTitle':'企业微信','AXSubrole':'AXStandardWindow'},4:{'role':'AXWindow','AXTitle':'file confirmation','AXSubrole':'AXDialog'},5:{'role':'AXSheet'},6:{'role':'AXButton','AXTitle':'使用原文件'},7:{'role':'AXDialog'},8:{'role':'AXButton','AXTitle':'发送'}}
        children={1:[2,3,4,7],2:list(range(100,10000)),3:[5],4:[6],5:[8],6:[],7:[],8:[]};reads=[]
        def get(e,key):
            reads.append((e,key));return data[e].get('role') if key=='AXRole' else data[e].get(key)
        def array(e,key,required=False):
            reads.append((e,key))
            if e==2:raise AssertionError('menu must never be traversed')
            return [3,4] if key=='AXWindows' else children[e]
        n.get=get;n.scoped_array=array;n.same_element=lambda a,b:a==b;n.scoped_settable=lambda *a:False;n.ax=SimpleNamespace(AXUIElementCopyActionNames=lambda *a:1)
        return n,data,children,reads
    def test_all_windows_sheets_dialogs_kept_original_paths_and_menu_not_read(self):
        n,_,_,reads=self.fake();snap=n.tree();self.assertFalse(snap['truncated']);pool=list(ui.nodes(snap['tree']))
        self.assertEqual([r['path'] for r in snap['tree']['children']],[[1],[2],[3]])
        self.assertIn(('AXSheet',[1,0]),[(x['role'],x['path']) for x in pool]);self.assertIn(('AXButton',[2,0]),[(x['role'],x['path']) for x in pool])
        self.assertEqual(snap['read_scope'],'application-windows-complete');self.assertEqual(snap['omitted_nonwindow_roles'],{'AXMenuBar':1});self.assertNotIn((2,'AXChildren'),reads)
        self.assertEqual(n.by_path[(2,0)],6)
    def test_partial_windows_deadline_depth_and_node_limit_remain_incomplete(self):
        for args,reason in [({'timeout':-1},'deadline'),({'max_depth':1},'depth-limit'),({'max_nodes':2},'node-limit')]:
            n,*_=self.fake();snap=n.tree(**args);self.assertTrue(snap['truncated']);self.assertEqual(snap['truncation_reason'],reason)
            with self.assertRaises(ui.UIError):ui.context(snap)
    def test_public_window_absent_from_root_children_is_read_completely(self):
        n,_,children,_=self.fake();children[1]=[2,3]
        snap=n.tree();self.assertFalse(snap['truncated']);pool=list(ui.nodes(snap['tree']));self.assertIn(('AXButton',['AXWindows',1,0]),[(x['role'],x['path']) for x in pool]);self.assertEqual(n.by_path[('AXWindows',1,0)],6)
    def test_auxiliary_public_window_unknown_role_is_not_silently_omitted(self):
        n,data,children,_=self.fake();children[1]=[2,3];data[4]['role']='AXUnknown'
        snap=n.tree();self.assertFalse(snap['truncated'])
        window=snap['tree']['children'][-1]
        self.assertEqual(window['role'],'AXUnknown');self.assertEqual(window['enumerated_by'],'AXWindows')
        self.assertEqual(window['children'][0]['AXTitle'],'使用原文件')
    def test_array_read_failure_is_explicit_and_never_a_complete_snapshot(self):
        n,*_=self.fake();original=n.scoped_array
        def broken(e,key,required=False):
            if e==4 and key=='AXChildren':raise AXError('scoped-required-array-unavailable:AXChildren')
            return original(e,key,required)
        n.scoped_array=broken;snap=n.tree();self.assertTrue(snap['truncated']);self.assertIn('AXChildren',snap['truncation_reason'])
if __name__=='__main__':unittest.main()
