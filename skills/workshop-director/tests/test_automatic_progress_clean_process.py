"""Actual immutable evidence replay in a clean process; no UI or fake verifier."""
import hashlib,json,subprocess,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
JOURNAL=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state.json'

class CleanProcessAutomaticProgressTests(unittest.TestCase):
    def test_actual_complete_sixteen_with_only_workshop_import_path(self):
        if not JOURNAL.is_file():self.skipTest('actual completed sixteen-detail evidence unavailable')
        before=hashlib.sha256(JOURNAL.read_bytes()).hexdigest()
        code=r'''
import hashlib,json,os,sys
from pathlib import Path
# -I -B drops caller PYTHONPATH and bytecode writes. Only add workshop code.
sys.path.insert(0,sys.argv[1])
assert not any('violation-notifier' in p for p in sys.path)
assert not any(n.startswith('governance_') for n in sys.modules)
def readonly(event,args):
    if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):
        raise AssertionError('business/UI/network operation forbidden:'+event)
    if event=='open':
        mode=args[1];flags=args[2]
        if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            raise AssertionError('write forbidden during semantic extraction')
sys.addaudithook(readonly)
import semantic_progress
path=Path(sys.argv[2]);raw=path.read_bytes();state=json.loads(raw)
assert state['phase']=='complete' and len(state['details'])==16
out=semantic_progress.extract(state,'violation_operator',journal_path=path)
assert path.read_bytes()==raw
assert 'governance_stop_loss_production' in sys.modules
assert 'workshop_verified_stop_loss' not in sys.modules
assert not any('violation-notifier' in p for p in sys.path)
print(json.dumps({'schema':out['schema'],'total':len(out['tokens']),'details':len([k for k in out['tokens'] if k.startswith('detail:')]),'automatic':len([k for k in out['tokens'] if k.startswith('automatic:')])}))
'''
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/'skills/workshop-director/scripts'),str(JOURNAL)],capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertEqual(json.loads(result.stdout),{'schema':'dom-navigation-v1','total':21,'details':16,'automatic':5})
        self.assertEqual(hashlib.sha256(JOURNAL.read_bytes()).hexdigest(),before)

if __name__=='__main__':unittest.main()
