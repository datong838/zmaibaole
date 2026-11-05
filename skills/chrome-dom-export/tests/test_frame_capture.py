"""Synthetic pages/proofs through actual local v7 producer; zero UI/network."""
import base64,copy,json,sys,tempfile,unittest,struct,zlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import frame_capture as f

def png():
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff'))+chunk(b'IEND',b'')
def node(selector,name='',role='generic',attributes=None,children=None):return {'selector':selector,'name':name,'role':role,'attributes':attributes or {},'children':children or []}
class FrameTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source_path=self.root/'source.json';self.profile_path=self.root/'profile.json';self.chain_id='fixture-chain-123';self.meta_paths=[]
        self.identity={'provider':'服务商123456789','account_id':'987654321','manager':'fixture经理'}
        self.source={'source':'local-dom-bridge','profile_revision':'mock-only-1','account_verified':True,'identity':self.identity,'company':'fixture','groupid':'123','url':'https://life.douyin.com/p/governance/violation_list?groupid=123','start':'2026-10-16','end_exclusive':'2026-10-20','records':{'total':3,'scope':'全部','all_pages_read':True,'filters_verified':True,'unread_only':False,'rows':[{'notice_id':'notice-'+str(i),'subject':'主体'+str(i)} for i in range(1,4)]}}
        self.profile={'status':'live-validated','revision':'mock-only-1','identity':{k:'#'+k for k in self.identity},'records':{'root':'#rows','row':{'attributes':{'data-kind':'record-row'}},'idAttribute':'data-notice-id','subject':{'attributes':{'data-field':'subject'}},'dateInput':'#date','scope':'#all','unreadOnly':'#unread','otherFilters':{'等级':{'locator':'#level','expected':'全部'}},'total':'#total','currentPage':'#page','next':'#next'},'screenshot':{'headers':{name:'#h'+str(i) for i,name in enumerate(f.HEADERS)}}}
        f.atomic(self.source_path,self.source);f.atomic(self.profile_path,self.profile);self.source_ref=self.ref(self.source_path);self.profile_ref=self.ref(self.profile_path);self.active_page=1;self.mode='anchor';self.sequence=0;self.proof_fault=None;self.calls=[]
    def ref(self,path):return {'path':str(Path(path).resolve()),'sha256':f.sha(path)}
    def observation(self,page):
        rows=[]
        for i in ([1,2] if page==1 else [3]):rows.append(node('#row'+str(i),'ID:notice-'+str(i)+' 主体'+str(i),'row',{'data-notice-id':'notice-'+str(i),'data-kind':'record-row'},[node('#subject'+str(i),'主体'+str(i),attributes={'data-field':'subject'})]))
        children=[*[node('#'+k,v) for k,v in self.identity.items()],node('#date','日期','textbox',{'value':'2026-10-16 ~ 2026-10-19'}),node('#all','全部',attributes={'aria-selected':'true'}),node('#unread','只看未读',attributes={'aria-checked':'false'}),node('#level','全部'),node('#total','全部3'),node('#page',str(page)),{**node('#next','下一页'),'disabled':page==2},*[node('#h'+str(i),name,'columnheader') for i,name in enumerate(f.HEADERS)],node('#rows',children=rows)]
        return {'source':'local-dom-bridge','observed_at':datetime.now(timezone.utc).isoformat(),'tab_id':5,'tab':{'tabId':5,'windowId':3,'url':self.source['url']+'&page='+str(page)},'tree':{'kind':'DOM-derived semantic tree (not native AX)','url':self.source['url'].split('?')[0],'truncated':False,'root':node('body',children=children)}}
    def request(self,cmd):
        self.calls.append(cmd)
        if cmd['op']=='viewport-proof':
            es=[]
            for e in cmd['elements']:
                visible=(e['kind']!='row' if self.mode=='anchor' else e['kind']=='row' and (e['notice_id']=='notice-2' if self.active_page==1 else e['notice_id']=='notice-3'))
                es.append({**{k:e[k] for k in ('key','kind','locator','notice_id')},'text':e['expected_text'],'rendered':True,'viewport_contained':visible,'text_unclipped':True,'unsupported_css_absent':True,'possible_overlay_absent':True,'fully_visible':visible})
            result={'source':'local-dom-bridge','method':'public-DOM-semantic-viewport-proof','source_sha256':cmd['source_sha256'],'dom_sha256':cmd['dom_sha256'],'scope':{k:cmd[k] for k in ('tabId','windowId','groupid')},'url':self.source['url']+'&page='+str(self.active_page),'epoch':self.sequence,'safety_version':'dom-only-20261021-11','viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'elements':es,'all_fully_visible':all(e['fully_visible'] for e in es)}
            if self.mode=='anchor' and self.active_page==1:
                row=result['elements'][-2];row.update(viewport_contained=True,fully_visible=True)
            if self.proof_fault:self.proof_fault(result)
        else:
            self.assertEqual(cmd['op'],'capture-visible');now=datetime.now(timezone.utc);scope={**{k:cmd[k] for k in ('tabId','windowId','groupid')},'url':self.source['url']+'&page='+str(self.active_page),'title':'fixture'}
            result={'before':scope,'after':scope,'grant':{'scope':scope,'nonce':'fixture-grant-page'+str(self.active_page),'via':'chrome.action.onClicked','safety_version':'dom-only-20261021-11','invokedAt':(now-timedelta(seconds=1)).isoformat()},'observedAt':now.isoformat(),'captureKey':cmd['captureKey'],'viewport_only':True,'safety_version':'dom-only-20261021-11','capture_method':'chrome.tabs.captureVisibleTab','pixel_actions_used':False,'imageDataUrl':'data:image/png;base64,'+base64.b64encode(png()).decode()}
        return {'ok':True,'result':result}
    def frame(self,page,mode,alter=None):
        self.active_page=page;self.mode=mode;self.sequence+=1;obs=self.observation(page)
        if alter:alter(obs)
        path=self.root/f'obs-{self.sequence}.json';f.atomic(path,obs);out=self.root/f'frame-{self.sequence}.png'
        result=f.capture(self.source_ref,self.ref(path),self.profile_ref,mode=mode,chain_id=self.chain_id,key='fixture-capture-'+str(self.sequence),out=out,request=self.request);self.meta_paths.append(result['metadata']);return result
    def all_frames(self):
        for page,mode in [(1,'anchor'),(1,'rows'),(2,'anchor'),(2,'rows')]:self.frame(page,mode)
        result=f.assemble(self.source_ref,list(reversed(self.meta_paths)),self.root/'manifest.json');return json.loads(Path(result['path']).read_text())
    def validate(self,manifest):return f.validate_chain(manifest,source=self.source_ref,company='fixture',groupid='123',start='2026-10-16',end_exclusive='2026-10-20',notice_ids=['notice-1','notice-2','notice-3'])
    def test_anchor_and_row_frames_keep_visibility_false_and_cover_all_pages(self):
        manifest=self.all_frames();checked=self.validate(manifest);self.assertEqual(checked['notice_ids'],['notice-1','notice-2','notice-3'])
        for path in self.meta_paths:
            m=json.loads(Path(path).read_text())
            if m['frame_mode']=='rows':self.assertFalse(m['filters_visible']);self.assertFalse(m['date_filter_visible']);self.assertFalse(m['list_headers_visible']);self.assertTrue(m['notice_ids'])
        self.assertEqual([e['page'] for e in checked['entries']],[1,1,2,2])
    def rewrite_frame_version(self,manifest,index,version):
        entry=manifest['frames'][index];path=Path(entry['metadata']['path']);meta=json.loads(path.read_text())
        for proof in meta['public_dom_proof'].values():proof['safety_version']=version
        ref=meta['capture_metadata'];capture=json.loads(Path(ref['path']).read_text());capture['capture']['safety_version']=version;capture['capture']['grant']['safety_version']=version;f.atomic(Path(ref['path']),capture);ref['sha256']=f.sha(ref['path']);f.atomic(path,meta);entry['metadata']['sha256']=f.sha(path)
    def test_historical_frame_chains_6_and_7_are_accepted_but_mixing_is_rejected(self):
        manifest=self.all_frames()
        for version in ('dom-only-20261021-7','dom-only-20261021-6'):
            for index in range(len(manifest['frames'])):self.rewrite_frame_version(manifest,index,version)
            self.assertEqual(self.validate(manifest)['notice_ids'],['notice-1','notice-2','notice-3'])
        self.rewrite_frame_version(manifest,1,'dom-only-20261021-11')
        with self.assertRaisesRegex(ValueError,'safety-version-changed'):self.validate(manifest)
    def test_row_frame_cannot_use_strict_api_or_forge_visible_date(self):
        result=self.frame(1,'rows');m=json.loads(Path(result['metadata']).read_text());m['date_filter_visible']=True
        with self.assertRaisesRegex(ValueError,'derived-visibility'):f.validate_frame(result['image'],m,source=self.source_ref)
        from screenshot_registration import validate_capture_chain
        with self.assertRaises(ValueError):validate_capture_chain(result['image'],json.loads(Path(result['metadata']).read_text()),source_sha256=self.source_ref['sha256'],groupid='123',expected_command=m['pinned_inputs']['command'],expected_url=m['public_dom_proof']['before']['url'])
    def test_missing_page_anchor_incomplete_coverage_or_reused_key_denied(self):
        manifest=self.all_frames()
        for kind in ('anchor','coverage','key'):
            changed=copy.deepcopy(manifest)
            if kind=='anchor':changed['frames'].pop(2)
            elif kind=='coverage':changed['frames'].pop(3)
            else:changed['frames'].insert(1,copy.deepcopy(changed['frames'][0]))
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.validate(changed)
    def test_old_anchor_cannot_cross_page_source_or_chain(self):
        manifest=self.all_frames()
        for kind in ('page','source','chain'):
            changed=copy.deepcopy(manifest)
            if kind=='page':changed['frames']=[*changed['frames'][:2],copy.deepcopy(changed['frames'][0]),changed['frames'][3]]
            elif kind=='source':changed['source_sha256']='a'*64
            else:changed['chain_id']='another-chain-123'
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.validate(changed)
    def test_unreviewed_generic_rows_unknown_profile_and_virtualized_date_hold(self):
        for kind in ('generic','profile','date'):
            if kind=='profile':self.profile['status']='awaiting-live-validation';f.atomic(self.profile_path,self.profile);self.profile_ref=self.ref(self.profile_path);alter=None
            else:
                self.profile['status']='live-validated';f.atomic(self.profile_path,self.profile);self.profile_ref=self.ref(self.profile_path)
                def alter(obs):
                    if kind=='generic':obs['tree']['root']['children'][-1]['children'][0]['role']='generic'
                    else:obs['tree']['root']['children']=[n for n in obs['tree']['root']['children'] if n['selector']!='#date']
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.frame(1,'anchor',alter)
    def test_foreign_profile_revision_rejected_even_when_marked_accepted(self):
        self.profile['revision']='another-accepted-revision';f.atomic(self.profile_path,self.profile);self.profile_ref=self.ref(self.profile_path)
        with self.assertRaisesRegex(ValueError,'source-profile-revision'):self.frame(1,'anchor')
        self.assertFalse(self.calls)
    def test_actual_filter_unread_page_or_scope_changed_cannot_capture(self):
        for selector,change in [('#unread',{'attributes':{'aria-checked':'true'}}),('#level',{'name':'仅严重'}),('#total',{'name':'全部4'}),('#page',{'name':'0'})]:
            def alter(obs):
                next(n for n in obs['tree']['root']['children'] if n['selector']==selector).update(change)
            with self.subTest(selector=selector),self.assertRaises(ValueError):self.frame(1,'anchor',alter)
        self.assertFalse(any(c['op']=='capture-visible' for c in self.calls))
    def test_tall_wide_clipped_row_not_counted_and_unknown_not_replayed(self):
        self.proof_fault=lambda p:[e.update(viewport_contained=False,fully_visible=False) for e in p['elements'] if e['kind']=='row']
        with self.assertRaisesRegex(ValueError,'required-content'):self.frame(1,'rows')
        self.assertFalse(any(c['op']=='capture-visible' for c in self.calls))
        before=len(self.calls);self.proof_fault=None
        with self.assertRaisesRegex(ValueError,'prior-unknown-no-new-key'):self.frame(1,'rows')
        self.assertEqual(len(self.calls),before)
    def test_declared_page_and_source_cannot_override_actual_dom(self):
        result=self.frame(1,'anchor');meta=json.loads(Path(result['metadata']).read_text())
        for kind in ('page','source'):
            changed=copy.deepcopy(meta)
            if kind=='page':changed['page_scope']['page']=2
            else:changed['pinned_inputs']['source_sha256']='f'*64
            with self.subTest(kind=kind),self.assertRaises(ValueError):f.validate_frame(result['image'],changed,source=self.source_ref)
    def test_readonly_reconcile_uses_original_saved_complete_frame_without_ui(self):
        self.frame(1,'rows');journal=next((self.root/'.frame-capture-state').glob('*.json'));data=json.loads(journal.read_text());data['frames'][0]['state']='unknown';f.atomic(journal,data);calls=len(self.calls)
        result=f.reconcile(self.source_ref,self.profile_ref,self.chain_id);self.assertEqual(result['state'],'complete');self.assertFalse(result['new_capture']);self.assertEqual(len(self.calls),calls)
        data=json.loads(journal.read_text());self.assertTrue(data['frames'][0]['reconciled_without_capture'])
    def test_new_frame_intent_never_captures_again_after_unknown(self):
        self.frame(1,'rows');path=self.root/'obs-1.json';before=len(self.calls)
        with self.assertRaisesRegex(ValueError,'no-replay'):f.capture(self.source_ref,self.ref(path),self.profile_ref,mode='rows',chain_id=self.chain_id,key='fixture-capture-1',out=self.root/'frame-1.png',request=self.request)
        self.assertEqual(len(self.calls),before)
if __name__=='__main__':unittest.main()
