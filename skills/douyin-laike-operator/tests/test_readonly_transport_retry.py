import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
s=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(s))
spec=importlib.util.spec_from_file_location('readonly_transport_workflow',s/'bridge-workflow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RetryTest(unittest.TestCase):
    def invoke(self,op,answers):
        w=m.Workflow.__new__(m.Workflow);self.calls=[]
        def request(c):self.calls.append(c);return answers.pop(0)
        w.invoke=request;return w.call({'op':op})
    @patch.object(m.time,'sleep')
    def test_transient_read_only_listener_loss_retries(self,sleep):
        error={'ok':False,'error':'Could not establish connection. Receiving end does not exist.'}
        self.assertEqual(self.invoke('tree',[error,error,{'ok':True,'result':{'root':'new-company'}}]),{'root':'new-company'})
        self.assertEqual(len(self.calls),3);self.assertEqual([a.args[0] for a in sleep.call_args_list],[1,2])
    @patch.object(m.time,'sleep')
    def test_mutation_or_unreviewed_error_never_retries(self,sleep):
        for op,error in [('click','Could not establish connection. Receiving end does not exist.'),('activate','Frame with id 0 was removed.'),('tree','not in offline reviewed click allowlist'),('tree','request timed out')]:
            with self.subTest(op=op,error=error),self.assertRaises(RuntimeError):self.invoke(op,[{'ok':False,'error':error}])
            self.assertEqual(len(self.calls),1)
        sleep.assert_not_called()
    @patch.object(m.time,'sleep')
    def test_read_only_retries_are_bounded(self,sleep):
        with self.assertRaises(RuntimeError):self.invoke('tree',[{'ok':False,'error':'No frame with id 0 in tab 123.'}]*3)
        self.assertEqual(len(self.calls),3)
if __name__=='__main__':unittest.main()
