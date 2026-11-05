"""TEMP-only pinned profiles and original operation guards. No UI/capture."""
import contextlib,hashlib,io,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
R=Path(__file__).resolve().parents[3];sys.path[:0]=[str(R/'skills/violation-notifier/scripts'),str(R/'skills/chrome-dom-export/scripts')]
import region_frame_capture as r
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.profile=self.write('profile.json',{});self.source={'path':str(self.root/'source.json'),'sha256':'a'*64};self.obs={'path':str(self.root/'obs.json'),'sha256':'b'*64};self.out=self.root/'out';self.kw=dict(pid=55,mode='anchor',chain_id='synthetic-chain',key='synthetic-key',outdir=self.out);self.request=Mock(side_effect=AssertionError('no request allowed'))
 def write(self,name,obj):
  path=self.root/name;path.write_text(json.dumps(obj));return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 def cap(self,**extra):return r.capture(self.source,self.obs,self.profile,request=self.request,**self.kw,**extra)
 def operation(self,revision,state='unknown'):
  folder=self.root/'.native-region-frame-state';folder.mkdir(exist_ok=True);operation={'source':self.source,'observation':self.obs,'profile':self.profile,**self.kw,'outdir':str(self.out),'revision':revision,'replaces':None};operation.pop('chain_id');(folder/(r.fc.fingerprint([self.source['sha256'],self.kw['chain_id']])+'.json')).write_text(json.dumps({'scope':{'source_sha256':self.source['sha256'],'profile_sha256':self.profile['sha256'],'chain_id':self.kw['chain_id']},'frames':[{'state':state,'operation':operation}]}))
 def test_default_plain_and_rectification_from_pinned_profile(self):
  self.assertEqual(r.capture_revision(self.profile),'region-v1');self.profile=self.write('profile.json',{'projection_contract':r.business.gp.RECTIFICATION_CONTRACT});self.assertEqual(r.capture_revision(self.profile),'rectification-v3')
 def test_explicit_valid_preserved_without_reading_profile(self):
  for value in ('r1','rectification-v3','A'*40):
   with patch.object(r.sr,'document',side_effect=AssertionError('explicit resolver must not read')):self.assertEqual(r.capture_revision({},value),value)
 def test_invalid_explicit_is_first_guard_zero_profile_read_or_request(self):
  for bad in ('','x'*41,'bad revision','../x',True,7):
   with patch.object(r.sr,'document',side_effect=AssertionError('no profile read')),patch.object(r.fc,'page_inputs',side_effect=AssertionError('no source parse')):
    with self.assertRaisesRegex(ValueError,'explicit-revision-required'):self.cap(revision=bad)
  self.request.assert_not_called();self.assertFalse(self.out.exists())
 def test_unknown_projection_refuses_before_request(self):
  self.profile=self.write('profile.json',{'projection_contract':'unreviewed'})
  with patch.object(r.fc,'page_inputs',side_effect=AssertionError('must reject first')):
   with self.assertRaisesRegex(ValueError,'projection-unreviewed'):self.cap()
  self.request.assert_not_called()
 def test_changed_pinned_profile_rejected(self):
  Path(self.profile['path']).write_text('{"projection_contract":null}')
  with self.assertRaises(ValueError):r.capture_revision(self.profile)
 def test_default_never_changes_old_operation_revision_or_bypasses_unknown(self):
  self.operation('r1')
  with patch.object(r.fc,'page_inputs',return_value={}):
   with self.assertRaisesRegex(ValueError,'original-operation-required'):self.cap()
   with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.cap(revision='r1')
  self.request.assert_not_called()
 def test_default_matching_unknown_still_no_recapture(self):
  self.operation('region-v1')
  with patch.object(r.fc,'page_inputs',return_value={}):
   with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.cap()
  self.request.assert_not_called()
 def test_cli_revision_optional_and_explicit_preserved(self):
  argv=['capture']
  vals={'source':self.source['path'],'source-sha256':'a'*64,'observation':self.obs['path'],'observation-sha256':'b'*64,'profile':self.profile['path'],'profile-sha256':self.profile['sha256'],'pid':'55','mode':'anchor','chain-id':'synthetic-chain','key':'synthetic-key','outdir':str(self.out)}
  for k,v in vals.items():argv+=['--'+k,v]
  for suffix,expected in (([],None),(['--revision','r1'],'r1')):
   with patch.object(sys,'argv',['region_frame_capture.py']+argv+suffix),patch.object(r,'capture',return_value={'ok':True}) as cap,contextlib.redirect_stdout(io.StringIO()):r.main()
   self.assertEqual(cap.call_args.kwargs['revision'],expected)
if __name__=='__main__':unittest.main()
