"""Pure chain-order tests with actual seven static bindings; no UI/asset rewrite.
Per-frame validation is isolated here; production still fully validates it first.
"""
import sys,json,copy,hashlib,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import region_frame_capture as r
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class EpochDomains(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=BASE/'screenshot-observations/060-assemble-region-chain-cli.json';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='65c00ce9f93d30ed156717ef38e658703595d3e3e484a77831fa57028431f66d';argv=json.loads(raw)['argv'];cls.source={'path':argv[argv.index('--source')+1],'sha256':argv[argv.index('--source-sha256')+1]};cls.paths=argv[argv.index('--frames')+1:];cls.originals=[json.loads(Path(p).read_text()) for p in cls.paths];cls.native=[r.sr.document(m['capture_metadata']) for m in cls.originals];cls.src=r.sr.document(cls.source)
 def setUp(self):
  self.meta=copy.deepcopy(self.originals);self.times=[n['captured_at'] for n in self.native];self.manifest={'capture_backend':r.BACKEND,'visibility_policy':r.business.CONTRACT,'source_sha256':self.source['sha256'],'chain_id':self.meta[0]['chain_id'],'frames':[{'image':m['image']['path'],'metadata':r.ref(p)} for p,m in zip(self.paths,self.meta)]}
 def base(self,i):return self.meta[i]['public_dom_proof']['before']['base_proof']
 def check(self):
  realdoc=r.sr.document
  def document(ref):
   if ref['path'] in self.paths:return self.meta[self.paths.index(ref['path'])]
   return realdoc(ref)
  def frame(image,m,**kwargs):
   i=self.meta.index(m);n=self.native[i];return {'version':m['public_dom_proof']['before']['safety_version'],'observed_at':self.times[i],'capture_scope':n['before']['scope'],'window_scope':n['before']['window'],'references':[],'notice_ids':m['notice_ids']}
  with patch.object(r.sr,'document',side_effect=document),patch.object(r,'validate_frame',side_effect=frame):return r.validate_chain(self.manifest,source=self.source,company=self.src['company'],groupid=self.src['groupid'],start=self.src['start'],end_exclusive=self.src['end_exclusive'],notice_ids=[x['notice_id'] for x in self.src['records']['rows']])
 def test_actual_seven_static_epoch_bindings_pass_with_explicit_domains(self):
  result=self.check();trace=result['epoch_domain_sequence'];self.assertEqual([x['epoch'] for x in trace],[3090,4908,0,51,684,684,0]);self.assertEqual(len(set(x['namespace'] for x in trace)),4);self.assertEqual(len(result['notice_ids']),16)
 def test_same_build_regression_rejects(self):
  self.base(1)['epoch']=100
  with self.assertRaisesRegex(ValueError,'time-or-dom-epoch-reset'):self.check()
 def test_intervening_different_build_does_not_forget_maximum(self):
  self.base(3)['diagnostic_build']=self.base(0)['diagnostic_build'];self.base(3)['epoch']=100
  with self.assertRaisesRegex(ValueError,'time-or-dom-epoch-reset'):self.check()
 def test_cross_build_timestamp_still_global_monotonic(self):
  self.times[2]='2000-01-01T00:00:00+00:00'
  with self.assertRaisesRegex(ValueError,'time-or-dom-epoch-reset'):self.check()
 def test_missing_or_unknown_business_build_cannot_create_reset_domain(self):
  for value in (None,'arbitrary-new-instance'):
   self.setUp()
   if value is None:self.base(2).pop('diagnostic_build')
   else:self.base(2)['diagnostic_build']=value
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'epoch-build-unverified'):self.check()
 def test_region_build_never_owns_viewport_counter(self):
  self.base(2)['diagnostic_build']=self.base(1)['diagnostic_build'];self.meta[2]['public_dom_proof']['before']['region_build']='brand-new-region-build'
  with self.assertRaisesRegex(ValueError,'time-or-dom-epoch-reset'):self.check()
 def test_generic_legacy_missing_or_changed_build_cannot_reset_same_page(self):
  self.manifest['visibility_policy']=r.POLICY
  for m in self.meta:m['visibility_policy']=r.POLICY
  self.base(2).pop('diagnostic_build')
  with self.assertRaisesRegex(ValueError,'time-or-dom-epoch-reset'):self.check()
 def test_new_page_anchor_resets_only_its_page_counter_not_time(self):
  self.base(4)['epoch']=0;self.base(5)['epoch']=0;self.assertEqual(len(self.check()['entries']),7)
if __name__=='__main__':unittest.main()
