"""Portable actual public-card/base fixture, synthetic identity mutations.
Full validate_base executes; no source lookup, bridge, UI or native capture.
"""
import ast,copy,importlib.util,json,re,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;R=H.parents[2];sys.path[:0]=[str(R/'skills/violation-notifier/scripts'),str(R/'skills/chrome-dom-export/scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
b=load('candidate_visible_card',R/'skills/chrome-dom-export/scripts/business_cells_capture.py')
class Tests(unittest.TestCase):
 def setUp(self):
  v=json.loads((H/'fixtures/visible-card/base.json').read_text());self.inputs=v['inputs'];self.proof=v['proof'];self.expected=self.inputs['screenshot_identity']['identity']
 def card(self):return self.proof['public_identity']['visible_card']
 def test_actual_complete_visible_card_full_base_passes(self):
  import screenshot_identity as identity
  with identity.api() as (d,_):
   original=d.nav.identity
   with patch.object(d.nav,'identity',wraps=original) as call:
    self.assertIs(b.validate_base(self.proof,self.inputs),self.proof);self.assertEqual(call.call_count,1);self.assertIs(call.call_args.args[0]['truncated'],False);self.assertEqual(call.call_args.args[1],self.expected)
 def test_missing_manager_still_rejected(self):
  self.card()['name']=re.sub(r'我的客户经理.*?(?=切换公司|退出登录|$)','',self.card()['name'])
  with self.assertRaises(ValueError):b.validate_base(self.proof,self.inputs)
 def test_wrong_account_still_rejected(self):
  self.card()['name']=self.card()['name'].replace(self.expected['account_id'],'9999999999999999')
  with self.assertRaisesRegex(ValueError,'account-changed'):b.validate_base(self.proof,self.inputs)
 def test_wrong_provider_inside_card_still_rejected(self):
  self.card()['name']=self.card()['name'].replace(self.expected['provider'],'服务商9999999999999999')
  with self.assertRaisesRegex(ValueError,'account-changed'):b.validate_base(self.proof,self.inputs)
 def test_wrong_manager_or_public_provider_rejected(self):
  self.card()['name']=self.card()['name'].replace(self.expected['manager'],'错误经理')
  with self.assertRaises(ValueError):b.validate_base(self.proof,self.inputs)
  self.setUp();self.proof['public_identity']['provider']='服务商9999999999999999'
  with self.assertRaisesRegex(ValueError,'business-public-identity-changed'):b.validate_base(self.proof,self.inputs)
 def test_absent_card_path_unchanged(self):
  self.proof['public_identity']['visible_card']=None;self.assertIs(b.validate_base(self.proof,self.inputs),self.proof)
if __name__=='__main__':unittest.main()
