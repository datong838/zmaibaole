"""One explicit repair for a read-only SCK initialization crash, never business writes."""
import hashlib,json,os
from pathlib import Path
from visible_capture import require,sha,stamp
FAILURE='sck-helper-response-invalid:Assertion failed: (did_initialize), function CGS_REQUIRE_INIT, file CGInitialization.c, line 44.\n'
def load(path):return json.loads(Path(path).read_text())
def ref(path):return {'path':str(Path(path).resolve()),'sha256':sha(path)}
def pinned(r):require(set(r)=={'path','sha256'} and Path(r['path']).is_absolute() and sha(r['path'])==r['sha256'],'native-repair-pinned-file-changed');return Path(r['path'])
def report(r):
    value=load(pinned(r));require(value.get('kind')=='sck-initialization-repair-v1' and value.get('status')=='compiled' and value.get('failure')=='CGS_REQUIRE_INIT did_initialize' and value.get('root_authorization')=='retry-readonly-pre-output-once','native-repair-report-not-authorized')
    source=pinned(value['swift_source']);helper=pinned(value['helper']);require(source.name=='window-capture.swift' and os.access(helper,os.X_OK),'native-repair-reviewed-helper-required');return value

def eligible(source_state,native_meta,manifest,outdir,backend,pid,report_ref):
    r=report(report_ref);require(backend=='screen-capture-kit','native-repair-only-sck')
    require(ref(source_state)==r['source_state'] and ref(native_meta)==r['native_metadata'],'native-repair-original-journals-conflict')
    old=load(source_state);m=load(native_meta);outdir=Path(outdir).resolve()
    require(old.get('state')=='unknown' and old.get('backend')==backend and old.get('manifest')==manifest and old.get('outdir')==str(outdir),'native-repair-original-order-conflict')
    require(m.get('state')=='unknown' and m.get('backend')==backend and m.get('error')==FAILURE and m.get('command',{}).get('pid')==pid and m['command'].get('captureKey')==manifest['capture_key'],'native-repair-not-initialization-crash')
    require(not old.get('repair_intent') and not m.get('repair_intent') and not (outdir/'native-pre-output-repair.json').exists(),'native-repair-once-only')
    require(not any(outdir.glob('*.png')) and not (outdir/'registration.json').exists() and not m.get('png') and not old.get('registration'),'native-repair-output-already-exists')
    return old,m

def prepare(source_state,native_meta,manifest,outdir,backend,pid,report_ref,fresh_preflight):
    old,m=eligible(source_state,native_meta,manifest,outdir,backend,pid,report_ref)
    require(fresh_preflight['scope']==m['before']['scope'] and fresh_preflight['window']==m['before']['window'] and fresh_preflight['pid']==pid and fresh_preflight['executable']==m['before']['executable'],'native-repair-current-window-changed')
    outdir=Path(outdir).resolve();history=outdir/'native-repair-history';history.mkdir(exist_ok=True)
    refs={}
    for key,path in [('source_state',source_state),('native_metadata',native_meta)]:
        raw=Path(path).read_bytes();target=history/(key+'-'+hashlib.sha256(raw).hexdigest()+'.json')
        with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        refs[key]=ref(target)
    intent={'kind':'sck-initialization-retry-once-v1','state':'issued-unknown','report':report_ref,'original':refs,'outdir':str(outdir),'manifest':manifest,'native_command':m['command'],'original_capture_api_issued':'unknown','reason':'Explicitly authorized retry of read-only screenshot after repaired initialization crash; no sendable PNG exists.','intent_at':stamp()}
    path=outdir/'native-pre-output-repair.json'
    with path.open('x') as f:json.dump(intent,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    return ref(path)

def consume(r,command,out,old):
    intent=load(pinned(r));report(intent['report']);require(intent.get('kind')=='sck-initialization-retry-once-v1' and intent.get('state')=='issued-unknown' and intent.get('native_command')==command and intent.get('original_capture_api_issued')=='unknown' and intent.get('outdir')==str(Path(out).resolve().parent),'native-repair-intent-invalid')
    original=load(pinned(intent['original']['native_metadata']));require(original==old and old.get('error')==FAILURE and old.get('state')=='unknown' and not old.get('repair_intent'),'native-repair-original-native-changed')
    require(not Path(out).exists() and not (Path(out).parent/'registration.json').exists() and not old.get('png'),'native-repair-output-already-exists')
    source=load(pinned(intent['original']['source_state']));require(source.get('state')=='unknown' and source.get('manifest')==intent['manifest'] and source.get('backend')=='screen-capture-kit','native-repair-original-source-changed')
    return intent
