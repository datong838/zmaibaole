"""Complaint-side chain binding mocks; shared validator owns PNG/DOM tests."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import workflow as w
import test_workflow as fixtures

class ComplaintReviewRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.WorkflowTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.capture();self.root=self.f.root;self.s=self.f.s;self.key=self.f.key;self.t=self.s['tasks'][self.key]
        self.s.update(mode='draft-only',browser_backend='local-dom-bridge')
        source=self.f.payload();source['source']='local-dom-bridge';source['rows']=source['rows'][:1]
        self.source=self.f.json('source.json',source);self.t['latest_snapshot']=w.evidence(self.root,self.source)
        self.png=self.root/'mock-not-a-live-capture.png';self.png.write_bytes(b'\x89PNG\r\n\x1a\nmock')
        self.reg=self.f.json('registration.json',{'source':{'path':str(self.source),'sha256':w.digest(self.source)},'review_keys':[self.key]})
        self.meta={'review_key':self.key,'snapshot_sha256':self.t['latest_snapshot']['sha256'],'source':'local-dom-bridge','sha256':w.digest(self.png),'registration':{'path':str(self.reg),'sha256':w.digest(self.reg)}}
        self.checked={'ok':True,'review_keys':[self.key],'image':{'path':str(self.png),'sha256':w.digest(self.png),'width':1,'height':1},'text_complete_in_image':{self.key:False},'occlusion_verified':False,'image_scope':'derived-dom-review-region','whole_window':False,'region_derived':True,'capture_backend':'screen-capture-kit-dom-region'}
    def attach(self):return w.attach_screenshot(self.root,self.s,self.key,self.png,self.f.json('metadata.json',self.meta))
    def test_live_chain_required_without_boolean_claims_and_test_order_revalidates(self):
        calls=[]
        with patch.object(w,'review_validator',return_value=lambda p,**binding:(calls.append(p) or copy.deepcopy(self.checked))):
            self.attach();order=w.send_order(self.root,self.s,self.key)
        self.assertEqual(len(calls),2);self.assertEqual(order['target'],'测试群请忽略');self.assertEqual(order['scope'],'test');self.assertIn('registration',self.t['screenshot'])
    def test_legacy_true_flags_never_replace_live_registration(self):
        self.meta.pop('registration');self.meta.update(filters_visible=True,review_visible=True)
        with self.assertRaisesRegex(ValueError,'registration-reference'):self.attach()
    def test_wrong_canonical_snapshot_or_merchant_refused_before_validator(self):
        original=copy.deepcopy(self.meta)
        for field,value in [('review_key','123:wrong'),('snapshot_sha256','0'*64)]:
            self.meta=copy.deepcopy(original);self.meta[field]=value
            with self.assertRaisesRegex(ValueError,'scope-mismatch'):self.attach()
        self.meta=original;source=json.loads(self.source.read_text());source['identity']={'different':True};self.source.write_text(json.dumps(source));new=w.evidence(self.root,self.source);self.t['latest_snapshot']=new;self.meta['snapshot_sha256']=new['sha256'];self.reg.write_text(json.dumps({'source':{'path':str(self.source),'sha256':w.digest(self.source)},'review_keys':[self.key]}));self.meta['registration']['sha256']=w.digest(self.reg)
        with self.assertRaisesRegex(ValueError,'merchant-mismatch'):self.attach()
    def test_validator_key_image_and_limitations_are_enforced(self):
        for mutate in [lambda c:c.update(review_keys=['other']),lambda c:c['image'].update(sha256='0'*64),lambda c:c.update(occlusion_verified=True),lambda c:c.update(text_complete_in_image={})]:
            checked=copy.deepcopy(self.checked);mutate(checked)
            with patch.object(w,'review_validator',return_value=lambda p,**binding:checked):
                with self.assertRaises(ValueError):self.attach()
    def test_changed_raw_ref_blocks_future_send_and_never_mints_new_key(self):
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):self.attach();original=w.send_order(self.root,self.s,self.key)
        self.reg.write_text(self.reg.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'evidence-changed'):w.send_order(self.root,self.s,self.key)
        self.assertEqual(original['target'],'测试群请忽略');self.assertIsNone(self.t['wecom'])
    def test_send_test_holds_original_unknown_file_confirmation_without_run(self):
        from types import SimpleNamespace
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):
            self.attach();order=w.send_order(self.root,self.s,self.key);job=self.f.json('sender-original.json',{'status':'unknown','phase':'file-confirm','send_intent_at':'owned'})
            calls=[]
            def command(argv,**kwargs):calls.append(argv);return SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(job)}))
            with patch.object(w.subprocess,'run',side_effect=command):
                with self.assertRaisesRegex(ValueError,'unknown-hold'):w.send_test(self.root,self.s,self.key)
            self.assertEqual(len(calls),1);self.assertIn('prepare',calls[0]);self.assertEqual(w.send_order(self.root,self.s,self.key),order)
    def test_new_sender_normal_chain_runs_once_then_original_job_is_attached(self):
        from types import SimpleNamespace
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):
            self.attach();order=w.send_order(self.root,self.s,self.key);job=self.f.json('sender-original.json',{'status':'running','phase':'locate'})
            calls=[]
            def command(argv,**kwargs):
                calls.append(argv)
                if 'run' in argv:
                    import hashlib
                    request={'key':order['key'],'kind':'group','target':order['target'],'scope':'test','file_sha256':self.t['screenshot']['sha256']}
                    state={'job':request,'fingerprint':hashlib.sha256(json.dumps(request,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'complete','phase':'done','ui_confirmed':True};w.atomic(job,state)
                return SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(job)}))
            with patch.object(w.subprocess,'run',side_effect=command):w.send_test(self.root,self.s,self.key)
            self.assertEqual([x[2] for x in calls],['prepare','run']);self.assertTrue(self.t['wecom']);self.assertEqual(self.t['send_attempt']['order']['key'],order['key'])
    def test_registration_cli_adapter_derives_wrapper_without_model_flags(self):
        value=json.loads(self.reg.read_text());value['image']=self.checked['image'];w.atomic(self.reg,value)
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):
            w.register_review_screenshot(self.root,self.s,self.key,self.reg);order=w.send_order(self.root,self.s,self.key)
        self.assertEqual(order['target'],'测试群请忽略');metadata=w.read(self.t['screenshot']['metadata']['path']);self.assertNotIn('filters_visible',metadata);self.assertEqual(metadata['snapshot_sha256'],self.t['latest_snapshot']['sha256'])
    def test_sender_timeout_preserves_original_job_without_second_send(self):
        from types import SimpleNamespace
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):
            self.attach();order=w.send_order(self.root,self.s,self.key)
            job=self.f.json('sender-timeout.json',{'status':'running','phase':'locate'})
            calls=[]
            def command(argv,**kwargs):
                calls.append(argv)
                if 'run' in argv:
                    self.assertEqual(kwargs['timeout'],360)
                    raise w.subprocess.TimeoutExpired(argv,360)
                return SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(job)}))
            with patch.object(w.subprocess,'run',side_effect=command):
                with self.assertRaisesRegex(ValueError,'wecom-timeout: inspect same job'):w.send_test(self.root,self.s,self.key)
            self.assertEqual([x[2] for x in calls],['prepare','run'])
            self.assertEqual(self.t['send_attempt']['job_path'],str(job))
            self.assertEqual(w.send_order(self.root,self.s,self.key),order)
            self.assertEqual(w.read(job),{'status':'running','phase':'locate'})
    def original_complete_send(self):
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.checked):
            self.attach();order=w.send_order(self.root,self.s,self.key)
        request={'key':order['key'],'kind':'group','target':'测试群请忽略','scope':'test','file_sha256':self.t['screenshot']['sha256']}
        job={'job':request,'fingerprint':w.hashlib.sha256(json.dumps(request,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'complete','phase':'done','ui_confirmed':True}
        self.sender=self.f.json('complete-original.json',job);self.t['wecom']=w.evidence(self.root,self.sender);self.t['send_attempt']={'order':order,'job_path':str(self.sender)}
        self.t['screenshot'].pop('image_scope') # Honest prior whole-window legacy state.
        self.old=copy.deepcopy(self.t);self.old_job_hash=w.digest(self.sender)
        self.newpng=self.root/'new-region.png';self.newpng.write_bytes(b'\x89PNG\r\n\x1a\nDIFFERENT-MOCK')
        self.newreg=self.f.json('new-region-registration.json',{'source':{'path':str(self.source),'sha256':w.digest(self.source)},'review_keys':[self.key],'image':{'path':str(self.newpng),'sha256':w.digest(self.newpng)}})
        self.newchecked=copy.deepcopy(self.checked);self.newchecked['image'].update(path=str(self.newpng),sha256=w.digest(self.newpng))
    def test_whole_window_cannot_be_registered_or_sent_as_final(self):
        checked=copy.deepcopy(self.checked);checked.update(image_scope='whole-window',whole_window=True,region_derived=False)
        with patch.object(w,'review_validator',return_value=lambda p,**binding:checked):
            with self.assertRaisesRegex(ValueError,'region-screenshot-required'):self.attach()
        self.original_complete_send()
        with patch.object(w,'review_validator',return_value=lambda p,**binding:checked):
            with self.assertRaisesRegex(ValueError,'region-screenshot-required'):w.send_order(self.root,self.s,self.key)
        self.t['status']='resolved'
        self.assertEqual(w.next_action(self.s,self.key),'correct-to-region-screenshot')
        self.assertIn(self.key,w.plan(self.s,'2026-10-21')['next_actions'])
        batch=next(iter(self.s['batches']))
        with self.assertRaisesRegex(ValueError,'unfinished'):w.close_batch(self.root,self.s,batch)
        self.s['batches'][batch]['closed_at']='historical-completion'
        with self.assertRaisesRegex(ValueError,'unfinished'):w.close_batch(self.root,self.s,batch)
    def test_confirmed_whole_window_correction_preserves_history_and_stable_new_key(self):
        self.original_complete_send()
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.newchecked):
            w.revise_review_screenshot(self.root,self.s,self.key,self.newreg,'user-requested-region-only')
            order=w.send_order(self.root,self.s,self.key)
            self.assertNotEqual(order['key'],self.old['send_attempt']['order']['key'])
            self.assertEqual(self.t['screenshot_revisions'][0]['previous'],{k:self.old[k] for k in ('screenshot','wecom','send_attempt')})
            self.assertEqual(w.digest(self.sender),self.old_job_hash)
            self.assertIsNone(self.t['wecom']);self.assertEqual(self.t['screenshot']['image_scope'],'derived-dom-review-region')
            # Repeating the SAME correction cannot clear a new unknown send.
            self.t['send_attempt']={'order':order,'job_path':'same-new-unknown-job'}
            w.revise_review_screenshot(self.root,self.s,self.key,self.newreg,'user-requested-region-only')
            self.assertEqual(self.t['send_attempt']['job_path'],'same-new-unknown-job');self.assertEqual(len(self.t['screenshot_revisions']),1)
    def test_unknown_original_cannot_be_hidden_by_revision(self):
        self.original_complete_send();state=w.read(self.sender);state.update(status='unknown',phase='image-verify-sent');w.atomic(self.sender,state)
        with patch.object(w,'review_validator',return_value=lambda p,**binding:self.newchecked):
            with self.assertRaisesRegex(ValueError,'original-send-not-complete'):w.revise_review_screenshot(self.root,self.s,self.key,self.newreg,'user-requested-region-only')
        self.assertEqual(self.t,self.old);self.assertFalse(self.t.get('screenshot_revisions'))
    def test_reason_and_image_source_are_not_free_form_revision_bypasses(self):
        self.original_complete_send()
        with self.assertRaisesRegex(ValueError,'reason-required'):w.revise_review_screenshot(self.root,self.s,self.key,self.newreg,'retry')
        wrong=copy.deepcopy(self.newchecked);wrong.update(whole_window=True,region_derived=False)
        with patch.object(w,'review_validator',return_value=lambda p,**binding:wrong):
            with self.assertRaisesRegex(ValueError,'region-screenshot-required'):w.revise_review_screenshot(self.root,self.s,self.key,self.newreg,'user-requested-region-only')
        self.assertEqual(self.t,self.old)

class PinnedRealFourRowRegression(unittest.TestCase):
    def test_actual_yantai_current_export_normal_source_rebuilds_same_four_results(self):
        import normal_observation as normal
        base=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/frozen-20261016-20261020/01-yantai'
        if not (base/'authoritative-normal-capture.json').is_file():self.skipTest('local pinned live input absent; no fixture live acceptance')
        load=lambda name:json.loads((base/name).read_text())
        job=load('navigation-job.json');rebuilt=normal.joined(job,load('normal-envelope.json'),load('normal-profile.json'),job['source_receipt'],job['source_receipt_sha256']);actual=load('authoritative-normal-capture.json')
        self.assertEqual(rebuilt,actual);self.assertEqual(actual['filtered_count'],4);self.assertEqual([r['stars'] for r in actual['rows']],[1,1,2,3]);self.assertEqual([r['action'] for r in actual['rows']],['投诉审核中','查看投诉结果','查看投诉结果','查看投诉结果'])
        self.assertTrue(all(r['review_id'].startswith('verified-tuple-sha256:') for r in actual['rows']));self.assertFalse(any(r['section']=='folded' for r in actual['rows']))
        self.assertEqual(load('result-lumos-observation.json')['status'],'rejected')
if __name__=='__main__':unittest.main()
