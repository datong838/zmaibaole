import copy,importlib.util,json,sys,tempfile,unittest,struct,zlib
from pathlib import Path
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS))
sp=importlib.util.spec_from_file_location('viewport_verified_capture_test',SCRIPTS/'verified_capture.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def png():
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff'))+chunk(b'IEND',b'')
class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.src=self.root/'source.json';self.obs=self.root/'observation.json';self.out=self.root/'fixture.png';self.calls=[]
        source={'source':'local-dom-bridge','account_verified':True,'company':'fixture','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-20','records':{'rows':[{'notice_id':'notice-1'}]}}
        self.src.write_text(json.dumps(source));self.elements=[{'key':'date','kind':'date-filter','selector':'#date','notice_id':None}];ns=[{'selector':'#date','role':'textbox','attributes':{'value':'2026-10-16 ~ 2026-10-19'},'name':'日期','children':[]}]
        for i,h in enumerate(['违规原因','处置主体','违规对象','处置生效状态','处置方式']):
            ns.append({'selector':'#h'+str(i),'role':'columnheader','name':h,'children':[]});self.elements.append({'key':'h'+str(i),'kind':'header','selector':'#h'+str(i),'notice_id':None})
        ns.append({'selector':'#r','role':'row','name':'ID:notice-1 主体 处置方式','children':[]});self.elements.append({'key':'r','kind':'row','selector':'#r','notice_id':'notice-1'})
        self.observation={'source':'local-dom-bridge','tab_id':5,'tab':{'tabId':5,'windowId':3,'url':'https://life.douyin.com/p/records?groupid=123'},'tree':{'kind':'DOM-derived semantic tree (not native AX)','url':'https://life.douyin.com/p/records','root':{'children':ns},'truncated':False}}
        self.obs.write_text(json.dumps(self.observation));self.source_sha=m.sha(self.src);self.observation_sha=m.sha(self.obs)
    def command(self):return m.command_from_inputs(self.src,self.source_sha,self.obs,self.observation_sha,self.elements)
    def proof(self,cmd):
        return {'safety_version':'dom-only-20261021-11','source_sha256':cmd['source_sha256'],'dom_sha256':cmd['dom_sha256'],'scope':{k:cmd[k] for k in ('tabId','windowId','groupid')},'url':self.observation['tab']['url'],'epoch':7,'viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'all_fully_visible':True,'elements':[{**{k:e[k] for k in ('key','kind','notice_id','locator')},'text':e['expected_text'],**{k:True for k in ('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent','fully_visible')}} for e in cmd['elements']]}
    def request(self,cmd):self.calls.append(cmd);return {'ok':True,'result':self.proof(cmd)}
    def fake_capture(self,command,out,request):
        out.write_bytes(png());m.atomic(out.with_suffix('.json'),{'capture':{'before':{'url':self.observation['tab']['url']}}});self.calls.append(command);return {'ok':True}
    def run_capture(self):
        with patch.object(m,'write_capture',self.fake_capture):return m.capture(self.src,self.source_sha,self.obs,self.observation_sha,self.elements,'fixture-key-123',self.out,self.request)
    def test_mechanically_generates_registration_only_after_two_equal_proofs(self):
        result=self.run_capture();metadata=json.loads(Path(result['metadata']).read_text());self.assertTrue(metadata['filters_visible']);self.assertTrue(metadata['date_filter_visible']);self.assertEqual(metadata['visible_filter_kinds'],['date-filter']);self.assertEqual(metadata['required_scope_filters'],['date-filter']);self.assertTrue(metadata['list_headers_visible']);self.assertEqual(metadata['notice_ids'],['notice-1']);self.assertEqual(metadata['source_sha256'],self.source_sha);self.assertEqual(metadata['sha256'],m.sha(self.out));self.assertEqual([c['op'] for c in self.calls],['viewport-proof','capture-visible','viewport-proof'])
    def test_changed_epoch_after_screenshot_no_registration_no_replay(self):
        original=self.request
        def changed(cmd):
            response=original(cmd)
            if len(self.calls)>1:response['result']['epoch']+=1
            return response
        self.request=changed
        with self.assertRaisesRegex(ValueError,'changed-during'):self.run_capture()
        self.assertFalse(self.out.with_suffix('.registration.json').exists());count=len(self.calls)
        with self.assertRaisesRegex(ValueError,'no-replay'):self.run_capture()
        self.assertEqual(len(self.calls),count)
    def test_clipped_or_partial_row_no_screenshot(self):
        original=self.request
        def clipped(cmd):
            r=original(cmd);r['result']['elements'][-1]['text_unclipped']=False;return r
        self.request=clipped
        with self.assertRaisesRegex(ValueError,'incomplete-row'):self.run_capture()
        self.assertFalse(self.out.exists())
    def test_source_or_observation_hash_changed_no_api(self):
        self.src.write_text('{}')
        with self.assertRaisesRegex(ValueError,'pinned-file'):self.run_capture()
        self.assertFalse(self.calls)
    def test_required_header_missing_and_fake_flags_rejected(self):
        self.elements.pop(2)
        with self.assertRaisesRegex(ValueError,'headers-missing'):self.command()
        self.setUp();self.elements[0]['filters_visible']=True
        with self.assertRaisesRegex(ValueError,'unknown-fields'):self.command()
    def test_unknown_id_partial_date_truncated_row_rejected(self):
        for kind in ('id','date','truncated'):
            old=copy.deepcopy(self.observation);elements=copy.deepcopy(self.elements)
            if kind=='id':self.elements[-1]['notice_id']='not-source'
            elif kind=='date':self.observation['tree']['root']['children'][0]['attributes']['value']='全部'
            else:self.observation['tree']['root']['children'][-1]['name']='a'*800
            self.obs.write_text(json.dumps(self.observation));self.observation_sha=m.sha(self.obs)
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.command()
            self.observation=old;self.elements=elements
    def test_id_only_span_cannot_register_full_record_row(self):
        self.observation['tree']['root']['children'][-1]['role']='generic'
        self.obs.write_text(json.dumps(self.observation));self.observation_sha=m.sha(self.obs)
        with self.assertRaisesRegex(ValueError,'explicit-semantic-row'):self.command()
    def test_bridge_schema_rejects_coordinates_and_arbitrary_script(self):
        cmd=self.command();m.bridge.validate_command(cmd)
        for field in ('x','y','script','url','debugger'):
            with self.subTest(field=field),self.assertRaises(ValueError):m.bridge.validate_command({**cmd,field:1})
if __name__=='__main__':unittest.main()
