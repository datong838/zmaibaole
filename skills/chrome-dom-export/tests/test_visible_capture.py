import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import visible_capture as v
import ax_capture_grant as g
import bridge
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg=='

class VisibleCaptureTests(unittest.TestCase):
 def test_grant_and_png_use_current_bridge_release(self):
  self.assertEqual(g.SAFETY,v.SAFETY)
  self.assertEqual(g.SAFETY,bridge.SAFETY_VERSION)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.cmd={'op':'capture-visible','tabId':7,'windowId':1,'groupid':'123','captureKey':'fixture-capture-1'}
  self.scope={'tabId':7,'windowId':1,'groupid':'123','url':'https://life.douyin.com/p/governance?groupid=123','title':'抖音来客'}
  self.result={'before':self.scope,'after':copy.deepcopy(self.scope),'captureKey':'fixture-capture-1','safety_version':v.SAFETY,'capture_method':'chrome.tabs.captureVisibleTab','viewport_only':True,'pixel_actions_used':False,'imageDataUrl':'data:image/png;base64,'+PNG}
 def test_capture_writes_png_hash_and_never_base64_metadata(self):
  calls=[];out=self.root/'capture.png'
  def request(cmd):
   calls.append(cmd);intent=json.loads(out.with_suffix('.json').read_text());self.assertEqual(intent['state'],'intent')
   return {'ok':True,'result':copy.deepcopy(self.result)}
  result=v.write_capture(self.cmd,out,request);self.assertTrue(result['ok']);self.assertTrue(out.is_file())
  metadata=out.with_suffix('.json').read_text();self.assertNotIn('base64',metadata);self.assertNotIn(PNG,metadata)
  second=v.write_capture(self.cmd,out,request);self.assertTrue(second['result']['reused']);self.assertEqual(len(calls),1)
 def test_unknown_never_calls_again(self):
  calls=[];out=self.root/'capture.png'
  def request(cmd):calls.append(cmd);return {'ok':False,'error':'activeTab permission missing'}
  with self.assertRaisesRegex(ValueError,'capture-failed'):v.write_capture(self.cmd,out,request)
  with self.assertRaisesRegex(ValueError,'no-replay'):v.write_capture(self.cmd,out,request)
  self.assertEqual(len(calls),1);self.assertFalse(out.exists())
 def test_scope_origin_and_payload_fail_closed(self):
  for index,change in enumerate(({'after':{**self.scope,'tabId':99}},{'safety_version':'old'},{'imageDataUrl':'data:image/jpeg;base64,'+PNG},{'imageDataUrl':'data:image/png;base64,invalid'})):
   with self.subTest(change=list(change)),self.assertRaises(ValueError):
    v.write_capture(self.cmd,self.root/(str(index)+'.png'),lambda cmd:{'ok':True,'result':{**self.result,**change}})
 def test_capture_command_schema_has_no_urls_or_coordinates(self):
  bridge.validate_command(self.cmd)
  for change in ({'x':1},{'url':'https://life.douyin.com'},{'windowId':True},{'groupid':'x'},{'captureKey':'x'}):
   with self.subTest(change=change),self.assertRaises(ValueError):bridge.validate_command({**self.cmd,**change})
 def test_generic_cli_request_refuses_image_payload(self):
  with patch.object(sys,'argv',['bridge.py','request',json.dumps(self.cmd)]),patch.object(bridge,'request') as request:
   with self.assertRaisesRegex(ValueError,'never print image base64'):bridge.main()
  request.assert_not_called()

class ActionGrantTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.scope={'tabId':7,'windowId':1,'groupid':'123'};self.observed=0;self.pressed=0;self.path=self.root/'action.json'
  test=self
  class Native:
   def __init__(self,pid):self.pid=pid
   def tree(self,title):return {'role':'AXWindow','children':[{'role':'AXWebArea','children':[{'role':'AXButton','AXTitle':g.LABEL,'AXEnabled':True,'actions':['AXPress'],'path':[1]}]},{'role':'AXToolbar','path':[2],'children':[{'role':'AXPopUpButton','AXTitle':g.LABEL,'AXEnabled':True,'actions':['AXPress'],'path':[2,0]}]}]}
   def press(self,node,title):
    self_intent=json.loads(test.path.read_text());test.assertEqual(self_intent['state'],'unknown');test.assertEqual(node['path'],[2,0]);test.pressed+=1
   def close(self):pass
  self.native=Native
 def request(self,command):
  self.observed+=1;scope={**self.scope,'url':'https://life.douyin.com/p/governance?groupid=123','title':'抖音来客'}
  grant={'nonce':'new-invocation','invokedAt':datetime.now(timezone.utc).isoformat(),'via':'chrome.action.onClicked'} if self.pressed else None
  return {'ok':True,'result':{'scope':scope,'safety_version':g.SAFETY,'extensionId':'a'*32,'invocationObserved':bool(grant),'grant':grant}}
 def test_one_native_action_is_not_falsely_claimed_capture_permission(self):
  result=g.invoke(self.scope,55,self.path,'a'*32,self.request,self.native)
  self.assertEqual(self.pressed,1);self.assertEqual(result['state'],'action-invocation-observed-permission-unproven');self.assertFalse(result['permission_granted'])
  g.invoke(self.scope,55,self.path,'a'*32,self.request,self.native);self.assertEqual(self.pressed,1)
 def test_no_observed_browser_invocation_no_repeat_or_fake_authorization(self):
  def request(command):
   r=self.request(command);r['result'].update(invocationObserved=False,grant=None);return r
  with patch.object(g.time,'sleep'),self.assertRaisesRegex(ValueError,'invocation-not-observed'):g.invoke(self.scope,55,self.path,'a'*32,request,self.native)
  self.assertEqual(self.pressed,1);g.invoke(self.scope,55,self.path,'a'*32,request,self.native);self.assertEqual(self.pressed,1)
 def test_delayed_action_delivery_only_reads_status_again(self):
  def request(command):
   r=self.request(command)
   if self.pressed and self.observed==3:r['result'].update(invocationObserved=False,grant=None)
   return r
  with patch.object(g.time,'sleep'):
   result=g.invoke(self.scope,55,self.path,'a'*32,request,self.native)
  self.assertEqual(self.pressed,1);self.assertEqual(result['state'],'action-invocation-observed-permission-unproven')
 def test_native_press_rechecks_live_toolbar_parent_and_main_window(self):
  from types import SimpleNamespace
  native=g.NativeAction.__new__(g.NativeAction);native.root='root';native.window='window';native.nodes={(2,):'toolbar',(2,0):'button'};native.refs=[]
  roles={'toolbar':'AXToolbar','button':'AXPopUpButton','dialog':'AXDialog','window':'AXWindow','root':'AXApplication'};parent=['toolbar'];pressed=[]
  def get(e,key):
   if key=='AXRole':return roles[e]
   if e=='root' and key=='AXFrontmost':return True
   if e=='window' and key=='AXMain':return True
   if e=='window' and key=='AXTitle':return '抖音来客'
   if e=='button' and key=='AXEnabled':return True
   if e=='button' and key=='AXTitle':return g.LABEL
   return None
  def raw(e,key):
   if e=='root' and key=='AXMainWindow':return 'window'
   if key=='AXParent':return parent[0] if e=='button' else 'window' if e in ('toolbar','dialog') else 'root' if e=='window' else None
   return None
  native.get=get;native.raw=raw;native.string=lambda s:s
  native.cf=SimpleNamespace(CFEqual=lambda a,b:a==b,CFRelease=lambda a:None)
  native.ax=SimpleNamespace(AXUIElementPerformAction=lambda *a:pressed.append(a) or 0)
  node={'path':[2,0],'toolbar_path':[2],'role':'AXPopUpButton'}
  native.press(node,'抖音来客');self.assertEqual(len(pressed),1)
  parent[0]='dialog'
  with self.assertRaisesRegex(ValueError,'left-reviewed-toolbar'):native.press(node,'抖音来客')
  self.assertEqual(len(pressed),1)
 def test_only_page_button_cannot_be_used_as_extension_action(self):
  tree={'role':'AXWindow','children':[{'role':'AXWebArea','children':[{'role':'AXButton','AXTitle':g.LABEL,'AXEnabled':True,'actions':['AXPress']}]}]}
  with self.assertRaisesRegex(ValueError,'not-unique-or-not-visible'):g.target(tree)

class PngIntegrityTests(unittest.TestCase):
 def test_truncation_crc_and_missing_image_data_refused(self):
  import base64
  raw=base64.b64decode(PNG)
  self.assertEqual(v.validate_png(raw),(1,1))
  for body in (raw[:33],raw[:-1],raw[:45]+bytes([raw[45]^1])+raw[46:]):
   with self.subTest(length=len(body)),self.assertRaises(ValueError):v.validate_png(body)
 def test_ordinary_outer_dialog_button_is_not_toolbar_action(self):
  tree={'role':'AXWindow','children':[{'role':'AXDialog','children':[{'role':'AXButton','AXTitle':g.LABEL,'AXEnabled':True,'actions':['AXPress'],'path':[1]}]}]}
  with self.assertRaisesRegex(ValueError,'in-toolbar'):g.target(tree)
if __name__=='__main__':unittest.main()
