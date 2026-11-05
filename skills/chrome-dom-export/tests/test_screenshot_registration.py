"""Real v6 local producer + mocked public bridge; no actual screen/browser calls."""
import base64,copy,json,sys,tempfile,unittest,struct,zlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS))
import verified_capture as vc
import screenshot_registration as v

def png():
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff'))+chunk(b'IEND',b'')
class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.src=self.root/'source.json';self.obs=self.root/'observation.json';self.out=self.root/'fixture.png'
        self.url='https://life.douyin.com/p/governance/violation_list?groupid=123'
        self.source={'source':'local-dom-bridge','account_verified':True,'company':'fixture','groupid':'123','url':self.url,'start':'2026-10-16','end_exclusive':'2026-10-20','records':{'rows':[{'notice_id':'notice-1'}]}}
        vc.atomic(self.src,self.source);self.spec=[{'key':'d','kind':'date-filter','selector':'#d','notice_id':None}];ns=[{'selector':'#d','role':'textbox','attributes':{'value':'2026-10-16 ~ 2026-10-19'},'name':'日期','children':[]}]
        for i,h in enumerate(['违规原因','处置主体','违规对象','处置生效状态','处置方式']):
            selector='#h'+str(i);ns.append({'selector':selector,'role':'columnheader','name':h,'children':[]});self.spec.append({'key':'h'+str(i),'kind':'header','selector':selector,'notice_id':None})
        ns.append({'selector':'#r','role':'row','name':'ID:notice-1 主体 处置方式','children':[]});self.spec.append({'key':'r','kind':'row','selector':'#r','notice_id':'notice-1'})
        self.observation={'source':'local-dom-bridge','tab_id':5,'tab':{'tabId':5,'windowId':3,'url':self.url},'tree':{'kind':'DOM-derived semantic tree (not native AX)','url':self.url.split('?')[0],'root':{'children':ns},'truncated':False}}
        vc.atomic(self.obs,self.observation);self.source_ref={'path':str(self.src),'sha256':vc.sha(self.src)};self.scope={'tabId':5,'windowId':3,'groupid':'123','url':self.url,'title':'抖音来客'}
        vc.capture(self.src,vc.sha(self.src),self.obs,vc.sha(self.obs),self.spec,'mock-capture-key-v6',self.out,self.request)
        self.registration=self.out.with_suffix('.registration.json');self.meta=json.loads(self.registration.read_text())
    def request(self,cmd):
        if cmd['op']=='viewport-proof':
            result={'source':'local-dom-bridge','method':'public-DOM-semantic-viewport-proof','safety_version':'dom-only-20261021-11','source_sha256':cmd['source_sha256'],'dom_sha256':cmd['dom_sha256'],'scope':{k:cmd[k] for k in ('tabId','windowId','groupid')},'url':self.url,'epoch':7,'viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'all_fully_visible':True,'elements':[{**{k:e[k] for k in ('key','kind','notice_id','locator')},'text':e['expected_text'],**{k:True for k in ('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent','fully_visible')}} for e in cmd['elements']]}
        else:
            self.assertEqual(cmd['op'],'capture-visible');now=datetime.now(timezone.utc);result={'before':self.scope,'after':self.scope,'grant':{'scope':self.scope,'nonce':'fixture-owned-grant','via':'chrome.action.onClicked','safety_version':'dom-only-20261021-11','invokedAt':(now-timedelta(seconds=1)).isoformat()},'observedAt':now.isoformat(),'captureKey':cmd['captureKey'],'viewport_only':True,'safety_version':'dom-only-20261021-11','capture_method':'chrome.tabs.captureVisibleTab','pixel_actions_used':False,'imageDataUrl':'data:image/png;base64,'+base64.b64encode(png()).decode()}
        return {'ok':True,'result':result}
    def validate(self,m=None,**kw):
        args={'source':self.source_ref,'company':'fixture','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-20','notice_ids':['notice-1']};args.update(kw)
        return v.validate_violation_registration(self.out,m or self.meta,**args)
    def mutate_capture(self,fn):
        ref=self.meta['capture_metadata'];p=Path(ref['path']);doc=json.loads(p.read_text());fn(doc);vc.atomic(p,doc);ref['sha256']=vc.sha(p)
    def test_real_local_producer_output_validates_without_browser(self):
        result=self.validate();self.assertEqual(result['notice_ids'],['notice-1']);self.assertEqual(len(result['references']),4);self.assertTrue(result['viewport_only'])
    def test_historical_v6_complete_chain_still_validates(self):
        for proof in self.meta['public_dom_proof'].values():proof['safety_version']='dom-only-20261021-6'
        def old(capture):
            capture['capture']['safety_version']='dom-only-20261021-6';capture['capture']['grant']['safety_version']='dom-only-20261021-6'
        self.mutate_capture(old);self.assertEqual(self.validate()['version'],'dom-only-20261021-6')
    def test_historical_v7_complete_chain_validates_and_mixed_grant_is_rejected(self):
        for proof in self.meta['public_dom_proof'].values():proof['safety_version']='dom-only-20261021-7'
        def old(capture):
            capture['capture']['safety_version']='dom-only-20261021-7';capture['capture']['grant']['safety_version']='dom-only-20261021-7'
        self.mutate_capture(old);self.assertEqual(self.validate()['version'],'dom-only-20261021-7')
        self.mutate_capture(lambda d:d['capture']['grant'].update(safety_version='dom-only-20261021-8'))
        with self.assertRaisesRegex(ValueError,'grant-unbound'):self.validate()
    def test_handwritten_true_fields_alone_rejected(self):
        fake={k:self.meta[k] for k in ('source','source_sha256','sha256','filters_visible','list_headers_visible','notice_ids')}
        with self.assertRaisesRegex(ValueError,'pinned-source-required'):self.validate(fake)
    def test_before_after_hash_epoch_mismatch_or_clipped_row_rejected(self):
        for kind in ('epoch','hash','clipped','extra-coordinates'):
            changed=copy.deepcopy(self.meta)
            if kind=='epoch':changed['public_dom_proof']['after']['epoch']+=1
            else:
                for proof in changed['public_dom_proof'].values():
                    if kind=='hash':proof['dom_sha256']='f'*64
                    elif kind=='clipped':proof['elements'][-1]['text_unclipped']=False
                    else:proof['elements'][-1]['left']=30
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.validate(changed)
    def test_unknown_or_omitted_coverage_id_rejected(self):
        for ids in (['other'],[],['notice-1','notice-1']):
            changed=copy.deepcopy(self.meta);changed['notice_ids']=ids
            with self.subTest(ids=ids),self.assertRaisesRegex(ValueError,'row-coverage'):self.validate(changed)
    def test_batch_company_dates_or_source_set_conflict_rejected(self):
        for fields in ({'company':'other'},{'groupid':'999'},{'start':'2026-10-17'},{'end_exclusive':'2026-10-21'},{'notice_ids':['different']}):
            with self.subTest(fields=fields),self.assertRaises(ValueError):self.validate(**fields)
    def test_capture_journal_changed_without_new_hash_rejected(self):
        Path(self.meta['capture_metadata']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'reference-changed'):self.validate()
    def test_capture_pending_wrong_window_version_method_and_key_rejected_even_rehashed(self):
        original=Path(self.meta['capture_metadata']['path']).read_bytes()
        changes=[lambda d:d.update(state='unknown'),lambda d:d['capture']['before'].update(windowId=99),lambda d:d['capture'].update(safety_version='dom-only-20261021-5'),lambda d:d['capture'].update(capture_method='made-up'),lambda d:d['command'].update(captureKey='other-key')]
        for mutate in changes:
            Path(self.meta['capture_metadata']['path']).write_bytes(original);self.meta['capture_metadata']['sha256']=vc.sha(self.meta['capture_metadata']['path']);self.mutate_capture(mutate)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):self.validate()
    def test_missing_five_headers_or_forged_semantic_selector_rejected(self):
        for kind in ('missing','selector','row-role'):
            changed=copy.deepcopy(self.meta)
            if kind=='missing':changed['pinned_inputs']['command']['elements'].pop(2)
            elif kind=='selector':changed['pinned_inputs']['command']['elements'][-1]['locator']['value']='#made-up'
            else:
                self.observation['tree']['root']['children'][-1]['role']='generic';vc.atomic(self.obs,self.observation);changed['pinned_inputs']['observation_sha256']=vc.sha(self.obs)
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.validate(changed)
    def test_original_observation_or_png_tamper_rejected(self):
        self.obs.write_text('{}')
        with self.assertRaisesRegex(ValueError,'reference-changed'):self.validate()
    def test_declared_date_flags_cannot_override_real_date(self):
        changed=copy.deepcopy(self.meta);changed['date_filter_visible']=False
        with self.assertRaisesRegex(ValueError,'derived-filter-flags'):self.validate(changed)
    def test_grant_or_capture_timeline_unbound_rejected(self):
        self.mutate_capture(lambda d:d['capture']['grant'].update(via='control-page-button'))
        with self.assertRaisesRegex(ValueError,'grant-unbound'):self.validate()
if __name__=='__main__':unittest.main()
