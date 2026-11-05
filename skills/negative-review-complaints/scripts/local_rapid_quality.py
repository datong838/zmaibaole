"""Pinned local CPU OCR runtime. No business/UI action or network inference."""
import argparse,hashlib,json,math,os,signal,subprocess,sys,time
from pathlib import Path
KIND='local-rapidocr-native-cell-observations-v1'
ENGINE={'rapidocr':'3.10.0','onnxruntime':'1.19.2','provider':'CPUExecutionProvider','text_score':.5}
def need(value,message):
 if not value:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':str(Path(path)),'sha256':sha(path)}
def raw(reference):
 p=Path(reference['path']);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),'Rapid-canonical-reference');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==reference['sha256'],'Rapid-reference-changed');return b
def child(root,name):
 p=Path(name);need(not p.is_absolute()and '..'not in p.parts and str(p)==name,'Rapid-relative-path');return root/p
def manifest(reference):
 m=json.loads(raw(reference));root=Path(reference['path']).parent;need(m['kind']=='offline-RapidOCR-CPU-wheelhouse-v1'and m['engine']==ENGINE and sha(__file__)==m['runner_sha256'],'Rapid-runtime-generation');return m,root
def verify(reference,full=False):
 m,root=manifest(reference)
 if full:
  for item in m['wheels']:need(sha(child(root,item['file']))==item['sha256'],'Rapid-wheel-changed')
 env=root/'.venv';need((env/'pyvenv.cfg').is_file(),'Rapid-runtime-not-built');need(not any((env/'lib/python3.9/site-packages').rglob('*.pyc')),'Rapid-untracked-bytecode-cache')
 for item in m['installed_files']if full else m['runtime_files']:
  p=child(env/'lib/python3.9/site-packages',item['file']);need(p.is_file()and not p.is_symlink()and sha(p)==item['sha256'],'Rapid-installed-dependency-changed:'+item['file'])
 need(sha(root/'.venv/bin/python')==m['python']['sha256'],'Rapid-runtime-python-changed');return m,root
def prepare(reference):
 m,root=manifest(reference);python=m['python']['base_entry'];need(sha(python)==m['python']['sha256'],'Rapid-build-python-changed')
 for item in m['wheels']:need(sha(child(root,item['file']))==item['sha256'],'Rapid-wheel-changed')
 env=root/'.venv'
 if not env.exists():
  subprocess.run([python,'-I','-B','-m','venv',str(env)],check=True,timeout=60)
  clean=os.environ.copy();clean.update({'PIP_CONFIG_FILE':'/dev/null','PIP_NO_INDEX':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_NO_CACHE_DIR':'1','PYTHONDONTWRITEBYTECODE':'1'})
  subprocess.run([str(env/'bin/python'),'-I','-B','-m','pip','install','--no-index','--no-deps','--no-compile',*[str(child(root,r['file']))for r in m['wheels']]],env=clean,check=True,timeout=120)
  for cache in (env/'lib/python3.9/site-packages').rglob('*.pyc'):cache.unlink()
 verify(reference,full=True);return {'kind':'offline-RapidOCR-runtime-ready-v1','manifest':reference,'python':str(env/'bin/python')}
def process(reference,image_ref,plan_ref):
 started=time.perf_counter();m,root=verify(reference);need(str(Path(sys.executable).absolute())==str(root/'.venv/bin/python'),'Rapid-private-interpreter-required');raw(image_ref);plan=json.loads(raw(plan_ref));need(set(plan)=={'cells'}and type(plan['cells'])is list and 1<=len(plan['cells'])<=5,'Rapid-bounded-cells');events=[]
 def deny(event,args):
  if event in ('socket.__new__','socket.connect','socket.connect_ex','socket.getaddrinfo'):
   events.append(event);raise PermissionError('Rapid-offline-network-denied')
 sys.addaudithook(deny)
 import socket
 try:socket.socket();raise ValueError('Rapid-network-guard-failed')
 except PermissionError:pass
 selftest=list(events);events.clear();t=time.perf_counter()
 import rapidocr,numpy as np
 from rapidocr import RapidOCR
 from PIL import Image
 imported=time.perf_counter()-t;import_events=list(events);events.clear()
 import importlib.metadata as md
 need({k:md.version(k)for k in ('rapidocr','onnxruntime')}=={k:ENGINE[k]for k in ('rapidocr','onnxruntime')},'Rapid-package-version')
 folder=Path(rapidocr.__file__).resolve().parent
 params={'Global.model_root_dir':str(folder/'models'),'Det.model_path':str(folder/'models/PP-OCRv6_det_small.onnx'),'Cls.model_path':str(folder/'models/ch_ppocr_mobile_v2.0_cls_mobile.onnx'),'Rec.model_path':str(folder/'models/PP-OCRv6_rec_small.onnx'),'EngineConfig.onnxruntime.use_cuda':False,'EngineConfig.onnxruntime.use_dml':False,'EngineConfig.onnxruntime.use_cann':False,'EngineConfig.onnxruntime.use_coreml':False,'EngineConfig.onnxruntime.intra_op_num_threads':2,'EngineConfig.onnxruntime.inter_op_num_threads':1,'Global.text_score':.5}
 t=time.perf_counter();engine=RapidOCR(params=params);engine._load_det_model();engine._load_cls_model();engine._load_rec_model();loaded=time.perf_counter()-t;providers={k:getattr(engine,k).session.session.get_providers()for k in ('text_det','text_cls','text_rec')};need(all(v==['CPUExecutionProvider']for v in providers.values()),'Rapid-CPU-only');image=Image.open(image_ref['path']);cells=[];total=0;keys=[]
 for item in plan['cells']:
  need(set(item)=={'key','box'}and type(item['key'])is str and item['key']not in keys,'Rapid-cell-keys-no-queries');keys.append(item['key']);b=item['box'];need(len(b)==4 and all(type(v)is int for v in b)and 0<=b[0]<b[2]<=image.width and 0<=b[1]<b[3]<=image.height,'Rapid-original-pixel-box');t=time.perf_counter();result=engine(image.crop(b));seconds=time.perf_counter()-t;total+=seconds;rows=[]
  if result.boxes is not None:
   for box,text,score in zip(result.boxes,result.txts,result.scores):rows.append({'box':np.asarray(box).tolist(),'text':str(text),'confidence':float(score)})
  cells.append({'key':item['key'],'box':b,'observations':rows,'ranges':[],'coordinate_system':'top-left-pixel-quadrilateral','seconds':seconds})
 need(not events,'Rapid-post-import-network-attempt');raw(image_ref);raw(plan_ref)
 return {'kind':KIND,'engine':ENGINE,'elapsed_seconds':total,'cells':cells,'provenance':{'runtime':reference,'runner':ref(Path(__file__).resolve()),'image':image_ref,'plan':plan_ref,'providers':providers,'import_seconds':imported,'cold_model_load_seconds':loaded,'total_seconds':time.perf_counter()-started,'socket_guard_selftest':selftest,'blocked_import_capability_probe':import_events,'post_import_network_attempts':events,'expected_text_supplied':False,'transform':'CG-equivalent-original-pixel-integer-crop/Pillow'}}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','verify','ocr']);p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha',required=True);p.add_argument('--image');p.add_argument('--image-sha');p.add_argument('--plan');p.add_argument('--plan-sha');a=p.parse_args();reference={'path':str(Path(a.manifest).absolute()),'sha256':a.manifest_sha};signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('Rapid-runtime-bounded-timeout')));signal.alarm(240 if a.action=='prepare'else 120)
 if a.action=='prepare':value=prepare(reference)
 elif a.action=='verify':verify(reference,full=True);value={'kind':'offline-RapidOCR-runtime-verified-v1','manifest':reference}
 else:need(all((a.image,a.image_sha,a.plan,a.plan_sha)),'Rapid-image-plan-refs-required');value=process(reference,{'path':a.image,'sha256':a.image_sha},{'path':a.plan,'sha256':a.plan_sha})
 print(json.dumps(value,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
