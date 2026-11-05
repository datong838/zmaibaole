import unittest,json,sys,hashlib,tempfile,copy,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/violation-notifier/scripts')]
import screenshot_identity as si,governance_projection as gp,frame_capture as fc
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
def ref(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
class ScreenshotIdentityV2(unittest.TestCase):
 def setUp(self):
  self.src=ref(BASE/'complete-governance-source.json');self.profile=ref(BASE/'records-five-business-cells-profile-v1.json');self.obs=ref(next((BASE/'.records-region-navigation').glob('*/evidence/0027.json')));self.chain='yantai-20261016-20-business-cells-v1';self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.a=si.create(self.src,self.profile,self.obs,chain_id=self.chain,pid=86614);self.path=Path(self.tmp.name)/'anchor.json';self.path.write_text(json.dumps(self.a,ensure_ascii=False));self.ar=ref(self.path)
  v=json.loads((BASE/'screenshot-observations/045-governance-identity-bounded-readonly-raw.json').read_text());tree=next(c['reply']['result'] for c in v['calls'] if c['command']['op']=='tree');tabs=[c['reply']['result'] for c in v['calls'] if c['command']['op']=='tabs'][-1];tab=next(t for w in tabs for t in w['tabs'] if t['tabId']==995698279);self.raw={'source':'local-dom-bridge','observed_at':'2026-10-22T03:00:00+00:00','tab_id':tab['tabId'],'tab':tab,'tree':tree}
 def test_actual0027_anchor_actual045_hidden_card_current_and_v2_page(self):
  self.assertEqual(si.validate(self.ar,self.src,self.profile),self.a);cur=si.current(self.ar,self.src,self.profile,self.raw);self.assertIsNone(cur['visible_full_identity']);self.assertEqual(cur['public_provider'],self.a['identity']['provider'])
  p=Path(self.tmp.name)/'current.json';p.write_text(json.dumps(self.raw));inputs=fc.page_inputs(self.src,ref(p),self.profile,screenshot_anchor=self.ar);self.assertTrue(all(e['key'].startswith('notice-five-business-cells-v2:') for e in inputs['command']['elements']));self.assertEqual(inputs['command']['dom_sha256'],gp.digest(self.raw['tree'],self.a['groupid'],actual_url=self.raw['tab']['url']))
 def test_wrong_gid_duplicate_blank_gid_path_window_provider_rejected(self):
  for mode in ('gid','duplicate','blank','path','window','provider'):
   raw=copy.deepcopy(self.raw)
   if mode=='gid':raw['tab']['url']=raw['tab']['url'].replace(self.a['groupid'],'1764303851132943')
   elif mode=='duplicate':raw['tab']['url']+='&groupid='+self.a['groupid']
   elif mode=='blank':raw['tab']['url']+='&groupid='
   elif mode=='path':raw['tab']['url']=raw['tab']['url'].replace('/violation_list','/home_violation_center')
   elif mode=='window':raw['tab']['windowId']+=1
   else:next(n for n in gp.walk(raw['tree']['root']) if 'Profile-index-module__title--' in n.get('attributes',{}).get('class',''))['name']='服务商999999999999'
   with self.assertRaises(ValueError,msg=mode):si.current(self.ar,self.src,self.profile,raw)
 def test_full_visible_identity_mismatch_rejected(self):
  raw=json.loads(Path(self.obs['path']).read_text());self.assertEqual(si.current(self.ar,self.src,self.profile,raw)['visible_full_identity'],self.a['identity']);card=next(n for n in gp.walk(raw['tree']['root']) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class',''));card['name']=card['name'].replace('曾庆洋','其他经理')
  with self.assertRaises(ValueError):si.current(self.ar,self.src,self.profile,raw)
 def test_anchor_tamper_scope_and_source_rejected(self):
  for k,value in (('native_pid',123),('chain_id','wrong-chain'),('identity',{})):
   a=copy.deepcopy(self.a);a[k]=value;self.path.write_text(json.dumps(a))
   with self.assertRaises((ValueError,KeyError)):si.validate(ref(self.path),self.src,self.profile,chain_id=self.chain,pid=86614)
 def test_actual045_python_js_v2_projection_byte_equivalence(self):
  node='/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
  js="const fs=require('fs'),vm=require('vm');const x=JSON.parse(fs.readFileSync(0,'utf8')),c={document:{documentElement:{}},MutationObserver:class{observe(){}},addEventListener(){},URL};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.__localViewportProof.governanceProjection(x.tree,x.gid,x.url).value));"
  result=subprocess.check_output([node,'-e',js,str(ROOT/'skills/chrome-dom-export/extension/viewport-proof.js')],input=json.dumps({'tree':self.raw['tree'],'gid':self.a['groupid'],'url':self.raw['tab']['url']}).encode())
  self.assertEqual(result.decode(),gp.canonical(gp.project(self.raw['tree'],self.a['groupid'],actual_url=self.raw['tab']['url'])['value']))
 def test_old_projection_requires_card_and_original_hash_unchanged(self):
  old=json.loads(Path(self.obs['path']).read_text());self.assertEqual(gp.digest(old['tree'],self.a['groupid']),'9fb0cfda4918c9150beff4ee1a8e9fb7d7aea11de1b29fcb4de0ef244c6ea71c')
  with self.assertRaises(ValueError):gp.digest(self.raw['tree'],self.a['groupid'])
if __name__=='__main__':unittest.main()
