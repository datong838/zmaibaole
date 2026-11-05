"""Synthetic pure-validation cache safety. No live evidence/UI/network.
Run with unittest discover; only temporary files and synthetic PNG pixels.
"""
import unittest,tempfile,json,hashlib,types
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import registration_validation as nm

class RegistrationNodeMemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.image=self.root/'raw.png';self.image.write_bytes(b'original pixels')
        self.source=self.put('source.json',{'scope':'same-company'})
        self.code=[1]
    def tearDown(self):self.tmp.cleanup()
    def put(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));return {'path':str(p),'sha256':nm.digest(p)}
    def session(self,**kw):return nm.Session(lambda:self.code[0],**kw)
    def metadata(self,**extra):return {'capture_backend':'test','pinned_inputs':{},**extra}
    def call(self,s,ref,fn,allow=False,m=None):
        m=m or json.loads(Path(ref['path']).read_text())
        return s.node(ref,str(self.image),self.source,allow,m,fn)
    def test_shared_dag_94_to_12_semantic_computations(self):
        sr=types.SimpleNamespace();r=types.SimpleNamespace(sr=sr);counts=[0]
        def document(ref):
            data=Path(ref['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('original-ref-changed')
            return json.loads(data)
        sr.document=document
        r._selection_prefix=lambda selection,source,profile:None
        def validate(image,m,*,source,allow_preview=False):
            counts[0]+=1;Path(image).read_bytes();sr.document(source)
            for ref in m['prior']:
                child=sr.document(ref);r.validate_frame(image,child,source=source)
            if m.get('preview'):
                child=sr.document(m['preview']);r.validate_frame(image,child,source=source,allow_preview=True)
            return {'ids':m['ids'],'pixels':nm.digest(image)}
        r.validate_frame=validate
        finals=[]
        for i in range(6):
            prior=[] if i in (0,1,4) else list(finals)
            preview=self.put('preview%d.json'%i,self.metadata(prior=prior,ids=[i]))
            finals.append(self.put('final%d.json'%i,self.metadata(prior=prior,ids=[i],preview=preview)))
        old=validate(str(self.image),document(finals[-1]),source=self.source,allow_preview=True)
        baseline=counts[0];self.assertEqual(baseline,94);counts[0]=0;s=self.session()
        with nm.installed(r,s),s.transaction():
            result=r.validate_frame(str(self.image),sr.document(finals[-1]),source=self.source,allow_preview=True)
        self.assertEqual(old,result);self.assertEqual(counts[0],12);self.assertGreater(s.stats['hits'],0)
        self.assertIs(r.validate_frame,validate)
    def test_same_path_raw_pixel_change_rejects_hit_and_terminal(self):
        ref=self.put('m.json',self.metadata());s=self.session()
        with self.assertRaisesRegex(ValueError,'dependency-changed'):
            with s.transaction():
                self.call(s,ref,lambda:self.image.read_bytes().hex())
                with s.pause():self.image.write_bytes(b'changed pixels')
                self.call(s,ref,lambda:'must-not-compute')
        s=self.session()
        with self.assertRaisesRegex(ValueError,'dependency-changed'):
            with s.transaction():
                self.call(s,ref,lambda:self.image.read_bytes().hex())
                with s.pause():self.image.write_bytes(b'changed again')
    def test_nested_hit_propagates_dependencies_to_outer(self):
        a=self.put('a.json',self.metadata());b=self.put('b.json',self.metadata());s=self.session()
        with self.assertRaisesRegex(ValueError,'dependency-changed'):
            with s.transaction():
                self.call(s,b,lambda:self.image.read_bytes().hex())
                self.call(s,a,lambda:self.call(s,b,lambda:'no'))
                with s.pause():self.image.write_bytes(b'external change')
                self.call(s,a,lambda:'no')
    def test_current_guard_rechecked_on_hit_and_terminal(self):
        ref=self.put('m.json',self.metadata());current=[True];calls=[0];s=self.session()
        def guard(*args):
            calls[0]+=1
            if not current[0]:raise ValueError('canonical-unknown')
        def compute():s.guard(guard,({'scope':'same'},));return {'ok':True}
        with self.assertRaisesRegex(ValueError,'canonical-unknown'):
            with s.transaction():
                self.call(s,ref,compute);current[0]=False;self.call(s,ref,compute)
        self.assertGreater(calls[0],1)
    def test_code_change_no_hit(self):
        ref=self.put('m.json',self.metadata());s=self.session()
        with self.assertRaisesRegex(ValueError,'code-graph-changed'):
            with s.transaction():
                self.call(s,ref,lambda:1);self.code[0]=2;self.call(s,ref,lambda:2)
    def test_mode_source_image_are_distinct_keys(self):
        ref=self.put('m.json',self.metadata());m=json.loads(Path(ref['path']).read_text());s=self.session();calls=[0]
        def compute():calls[0]+=1;return calls[0]
        with s.transaction():
            self.call(s,ref,compute);self.call(s,ref,compute,True)
            s.node(ref,str(self.image),{'different':'source'},False,m,compute)
            s.node(ref,str(self.root/'other.png'),self.source,False,m,compute)
        self.assertEqual(calls[0],4)
    def test_failure_not_cached_cap_bypass_and_result_not_mutable_shared(self):
        ref=self.put('m.json',self.metadata());s=self.session(max_bytes=0);calls=[0]
        def compute():calls[0]+=1;return {'items':[]}
        with s.transaction():self.call(s,ref,compute);self.call(s,ref,compute)
        self.assertEqual(calls[0],2);self.assertFalse(s.entries)
        s=self.session()
        with s.transaction():
            with self.assertRaisesRegex(ValueError,'failure'):self.call(s,ref,lambda:(_ for _ in ()).throw(ValueError('failure')))
            result=self.call(s,ref,compute);result['items'].append('mutated')
            self.assertEqual(self.call(s,ref,compute),{'items':[]})
    def test_cycle_rejected(self):
        ref=self.put('m.json',self.metadata());s=self.session()
        with self.assertRaisesRegex(ValueError,'registration-cycle'):
            with s.transaction():self.call(s,ref,lambda:self.call(s,ref,lambda:1))
    def test_mutated_unpublished_metadata_cannot_hit(self):
        ref=self.put('m.json',self.metadata());s=self.session();m=json.loads(Path(ref['path']).read_text());m['changed']=True
        with self.assertRaisesRegex(ValueError,'metadata-mutated'):
            with s.transaction():self.call(s,ref,lambda:1,m=m)
    def test_pillow_pixel_reader_is_transitive_dependency(self):
        from PIL import Image
        png=self.root/'actual.png';Image.new('RGBA',(2,2),(1,2,3,255)).save(png)
        ref=self.put('m.json',self.metadata());s=self.session()
        def pixels():
            with Image.open(png) as image:return image.convert('RGBA').tobytes().hex()
        with self.assertRaisesRegex(ValueError,'dependency-changed'):
            with s.transaction():
                self.call(s,ref,pixels)
                with s.pause():Image.new('RGBA',(2,2),(4,5,6,255)).save(png)
                self.call(s,ref,pixels)
    def test_reviewed_graph_source_and_loaded_constant_change(self):
        import importlib.util
        path=Path(__file__).resolve().parents[3]/'skills/violation-notifier/scripts/verification_session.py'
        spec=importlib.util.spec_from_file_location('candidate_graph_signer',path);signer=importlib.util.module_from_spec(spec);spec.loader.exec_module(signer)
        module=types.ModuleType('fixed_graph');module.__file__=str(self.root/'code.py');Path(module.__file__).write_text('REQUIRED = 1')
        exec('REQUIRED=1\ndef verify(): return REQUIRED',module.__dict__)
        token=nm.reviewed_graph_token([module],signer.code_signature,[])
        module.REQUIRED=2
        self.assertNotEqual(token,nm.reviewed_graph_token([module],signer.code_signature,[]))
        module.REQUIRED=1;Path(module.__file__).write_text('REQUIRED = 2')
        self.assertNotEqual(token,nm.reviewed_graph_token([module],signer.code_signature,[]))
    def test_fixed_default_function_code_defaults_and_binding_signed(self):
        import sys,importlib.util
        path=Path(__file__).resolve().parents[3]/'skills/violation-notifier/scripts/verification_session.py'
        spec=importlib.util.spec_from_file_location('default_graph_signer',path);signer=importlib.util.module_from_spec(spec);spec.loader.exec_module(signer)
        module=types.ModuleType('fixed_default_graph');module.__file__=str(self.root/'default_code.py');Path(module.__file__).write_text('fixed test graph')
        exec('def request(timeout=50): return timeout\ndef other(timeout=51): return timeout+1\nclass Native: pass\ndef invoke(request=request,native_factory=Native): return request()',module.__dict__)
        def token():return nm.reviewed_graph_token([module],signer.code_signature,[])
        baseline=token();module.invoke.__defaults__=(module.other,module.Native);self.assertNotEqual(baseline,token())
        module.invoke.__defaults__=(module.request,module.Native);module.request.__defaults__=(60,);self.assertNotEqual(baseline,token())
        module.request.__defaults__=(50,);module.request.__code__=module.other.__code__;self.assertNotEqual(baseline,token())
        module.invoke.__defaults__=(lambda:1,module.Native)
        with self.assertRaisesRegex(ValueError,'default-function-not-fixed'):token()
        def factory():
            captured=[]
            def request():return captured
            return request
        closure=factory();closure.__module__=module.__name__;module.request=closure;module.invoke.__defaults__=(closure,module.Native)
        with self.assertRaisesRegex(ValueError,'default-function-closure'):token()
        exec('def request(value=None): return value',module.__dict__);module.request.__defaults__=(module.request,);module.invoke.__defaults__=(module.request,module.Native)
        with self.assertRaisesRegex(ValueError,'default-function-cycle'):token()
    def test_observed_inline_default_and_stdlib_changes_are_signed(self):
        import sys,importlib,subprocess
        root=Path(__file__).resolve().parents[3]
        sys.path.insert(0,str(root/'skills/chrome-dom-export/scripts'));sys.path.insert(0,str(root/'skills/violation-notifier/scripts'))
        identity=importlib.import_module('chrome_process_identity');signer=importlib.import_module('verification_session')
        def token():return nm.reviewed_graph_token([identity],signer.code_signature,[])
        baseline=token();original=dict(subprocess.run.__kwdefaults__)
        try:
            subprocess.run.__kwdefaults__={**original,'check':True};self.assertNotEqual(baseline,token())
        finally:subprocess.run.__kwdefaults__=original
        fn=identity.verify.__kwdefaults__['resolve_fn'];old=fn.__code__
        try:
            fn.__code__=(lambda p:p).__code__
            with self.assertRaisesRegex(ValueError,'default-function-not-fixed'):token()
        finally:fn.__code__=old
        self.assertEqual(baseline,token())
    def test_auth_consumed_at_entry_and_exception_does_not_retain(self):
        r=types.SimpleNamespace(sr=types.SimpleNamespace());r._selection_prefix=lambda *args:None
        r.sr.document=lambda ref:json.loads(Path(ref['path']).read_text())
        s=self.session(max_bytes=100000);checks=[]
        def validate(image,m,*,source,allow_preview=False):
            checks.append(s.retained)
            if m.get('fail'):raise ValueError('original-validator-failure')
            return {'ok':True}
        r.validate_frame=validate;ref=self.put('auth.json',self.metadata())
        with nm.installed(r,s),s.transaction():
            doc=r.sr.document(ref);r.validate_frame(str(self.image),doc,source=self.source)
            self.assertEqual(checks[0],0)
            before=s.retained
            # Exact bytes copied into an unpublished object do not authorize a node hit.
            r.validate_frame(str(self.image),dict(doc),source=self.source)
            self.assertEqual(s.stats['unpublished_computations'],1)
            failed=dict(doc);failed['fail']=True
            with self.assertRaisesRegex(ValueError,'original-validator-failure'):r.validate_frame(str(self.image),failed,source=self.source)
            self.assertEqual(s.retained,before)
        s=self.session()
        with nm.installed(r,s),s.transaction():
            doc=r.sr.document(ref);doc['modified']=True
            with self.assertRaisesRegex(ValueError,'metadata-mutated'):r.validate_frame(str(self.image),doc,source=self.source)
            self.assertEqual(s.retained,0);self.assertFalse(s.entries)
    def test_reader_writes_fd_and_process_rejected(self):
        import subprocess
        with self.assertRaisesRegex(ValueError,'write-forbidden'):
            with self.session().transaction():self.image.write_bytes(b'no')
        fd=__import__('os').open(str(self.image),__import__('os').O_RDONLY)
        try:
            with self.assertRaisesRegex(ValueError,'untracked-file-descriptor'):
                with self.session().transaction():open(fd,'rb',closefd=False)
        finally:__import__('os').close(fd)
        with self.assertRaisesRegex(ValueError,'not-pure-validation'):
            with self.session().transaction():subprocess.run(['/usr/bin/true'])
if __name__=='__main__':unittest.main()
