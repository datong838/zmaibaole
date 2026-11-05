"""Offline loopback integration tests. Does not open/control Chrome."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('bridge',Path(__file__).resolve().parents[1]/'scripts/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.config={'cliToken':'test-cli','bridgeToken':'test-extension','extensionId':'a'*32}
        self.server=b.make_server(self.config,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def post(self,path,data,token='test-cli',origin=None):
        h={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
        if origin: h['Origin']=origin
        req=Request(self.base+path,data=json.dumps(data).encode(),headers=h,method='POST')
        try:
            with urlopen(req,timeout=4) as r: return r.status,json.load(r)
        except HTTPError as e: return e.code,json.load(e)
    def test_auth_and_origin(self):
        self.assertEqual(self.post('/v1/status',{},'wrong')[0],401)
        self.assertEqual(self.post('/v1/status',{},origin='https://life.douyin.com')[0],403)
        self.assertEqual(self.post('/bridge/poll',{},'test-cli')[0],401)
        self.assertEqual(self.post('/bridge/poll',{},'test-extension',origin='https://evil.test')[0],403)
        self.assertEqual(self.post('/bridge/poll',{'extensionId':'a'*32},'test-extension','chrome-extension://'+'a'*32)[0],200)
    def test_protocol_and_no_replay(self):
        result={}
        t=threading.Thread(target=lambda:result.update(reply=self.post('/v1/request',{'command':{'op':'tree','tabId':7},'timeout':3})))
        t.start()
        # Synchronize directly on queue, avoiding timing assumptions.
        import time
        until=time.monotonic()+1
        while not self.server.jobs.queue and time.monotonic()<until: time.sleep(.01)
        origin='chrome-extension://'+'a'*32
        _,reply=self.post('/bridge/poll',{'extensionId':'a'*32},'test-extension',origin)
        job=reply['job'];self.assertEqual(job['command']['tabId'],7)
        self.assertIsNone(self.post('/bridge/poll',{'extensionId':'a'*32},'test-extension',origin)[1]['job'])
        self.assertEqual(self.post('/bridge/result',{'id':job['id'],'ok':True,'result':{'tree':'fixture'}},'test-extension',origin)[0],200)
        t.join();self.assertTrue(result['reply'][1]['ok'])
        self.assertEqual(self.post('/bridge/result',{'id':job['id'],'ok':True},'test-extension',origin)[0],409)
    def test_denied_commands(self):
        for c in [{'op':'react-click','tabId':7},{'op':'html','tabId':7},{'op':'reload','tabId':7},{'op':'evaluate'},{'op':'cookies'},{'op':'click','tabId':7,'x':1,'y':2},{'op':'click','tabId':7,'locator':{'by':'coordinate','value':'1,2'}},{'op':'tree','tabId':True}]:
            with self.assertRaises(ValueError): b.validate_command(c)
    def test_narrow_records_reload_schema_and_stable_key(self):
        good={'op':'reload-records','tabId':7,'groupid':'123456789','reloadKey':'work-order-record-refresh-1'}
        self.assertEqual(b.validate_command(good),good)
        for change in ({'tabId':True},{'groupid':123},{'groupid':'123&bad=1'},{'reloadKey':'new'},{'url':'https://life.douyin.com/'},{'locator':{'by':'text','value':'刷新'}}):
            with self.subTest(change=change),self.assertRaises(ValueError):b.validate_command({**good,**change})
        with self.assertRaises(ValueError):b.validate_command({'op':'tabs','reloadKey':'work-order-1'})
    def test_old_extension_cannot_reload_record_page(self):
        code,body=self.post('/v1/request',{'command':{'op':'reload-records','tabId':7,'groupid':'123','reloadKey':'work-order-refresh-1'}})
        self.assertEqual(code,400);self.assertIn('reviewed-extension-version-required',body['error']);self.assertFalse(self.server.jobs.queue)
    def test_account_hover_exit_exact_schema_without_general_group_bypass(self):
        good={'op':'hover','kind':'account-hover-exit','tabId':7,'groupid':'123','locator':{'by':'selector','value':'#observed-profile'},'value':{'provider':'服务商123','account_id':'12345678','manager':'测试'}}
        self.assertEqual(b.validate_command(good),good)
        for change in ({'kind':'navigation'},{'groupid':123},{'locator':{'by':'text','value':'退出登录'}},{'value':{'provider':'服务商123'}},{'windowId':1}):
            with self.subTest(change=change),self.assertRaises(ValueError):b.validate_command({**good,**change})
    def test_long_poll_wakes_for_next_serial_command(self):
        import time
        jobs=b.Jobs();reply={}
        t=threading.Thread(target=lambda:reply.update(job=jobs.poll(wait_seconds=1)))
        t.start();time.sleep(.03)
        job=jobs.add({'op':'tabs'},2);t.join(timeout=.5)
        self.assertFalse(t.is_alive());self.assertEqual(reply['job']['id'],job['id'])
        start=time.monotonic();self.assertIsNone(jobs.poll(wait_seconds=1))
        self.assertLess(time.monotonic()-start,.2)
    def test_expired_not_delivered(self):
        job=self.server.jobs.add({'op':'tabs'},0)
        self.assertIsNone(self.server.jobs.poll())
        self.server.jobs.expire(job)
    def test_old_extension_cannot_mutate(self):
        code,body=self.post('/v1/request',{'command':{'op':'click','tabId':7,'locator':{'by':'text','value':'导出'}}})
        self.assertEqual(code,400);self.assertIn('reviewed-extension-version-required',body['error'])
        self.assertFalse(self.server.jobs.queue)
        origin='chrome-extension://'+'a'*32
        self.post('/bridge/poll',{'extensionId':'a'*32,'safety_version':b.SAFETY_VERSION},'test-extension',origin)
        self.assertTrue(self.post('/v1/status',{})[1]['reviewedExtensionReady'])
    def test_manifest(self):
        manifest=json.loads((Path(__file__).resolve().parents[1]/'extension/manifest.json').read_text())
        self.assertEqual(set(manifest['permissions']),{'tabs','scripting','downloads','alarms','storage','activeTab'})
        self.assertEqual(set(manifest['host_permissions']),{'https://life.douyin.com/*','http://127.0.0.1/*'})
        self.assertEqual(manifest['content_scripts'][0]['world'],'ISOLATED')

if __name__=='__main__': unittest.main()
