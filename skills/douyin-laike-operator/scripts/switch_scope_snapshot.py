"""Opt-in fixed four-read adapter. Existing collectors/reconcile remain unchanged."""
import math
from pathlib import Path
import switch_read_recovery as recovery

def collect(job,state,invoke,directory):
    """Persist four original JSONs, then use the original switch verifier verbatim.
    directory must be a new isolated attempt; a failed scope never invokes fallback.
    """
    scope=recovery.contract(job,state)
    command={'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']}
    out=Path(directory);out.mkdir(parents=True,exist_ok=False)
    raw=invoke(command);transport=recovery.immutable(out/'transport.json',recovery.encoded(raw))
    recovery.need(type(raw) is dict and raw.get('ok') is True,'readonly-scope-transport-failed')
    result=raw.get('result');fields={'schema','scope','commands','before','ping','tree','after','timing'}
    recovery.need(type(result) is dict and set(result)==fields and result['schema']=='readonly-scope-v1' and result['scope']=={'tabId':scope['tab_id'],'windowId':scope['window_id']},'readonly-scope-envelope-invalid')
    commands=[{'op':'tabs'},{'op':'ping','tabId':scope['tab_id']},{'op':'tree','tabId':scope['tab_id']},{'op':'tabs'}]
    recovery.need(result['commands']==commands,'readonly-scope-command-sequence-invalid')
    timing=result['timing'];numeric=lambda v:type(v) in (int,float) and math.isfinite(v) and v>=0
    recovery.need(type(timing) is dict and set(timing)=={'clock','steps','elapsed_ms'} and timing['clock']=='worker-performance-now' and numeric(timing['elapsed_ms']) and type(timing['steps']) is list and len(timing['steps'])==4,'readonly-scope-timing-invalid')
    for row,cmd in zip(timing['steps'],commands):
        recovery.need(type(row) is dict and set(row)=={'op','elapsed_ms'} and row['op']==cmd['op'] and numeric(row['elapsed_ms']),'readonly-scope-timing-invalid')
    recovery.need(sum(x['elapsed_ms'] for x in timing['steps'])<=timing['elapsed_ms']+1e-6,'readonly-scope-timing-invalid')
    refs={key:recovery.immutable(out/(key+'.json'),recovery.encoded(result[key])) for key in ('before','ping','tree','after')}
    timing_ref=recovery.immutable(out/'worker-timing.json',recovery.encoded(timing))
    sample={'kind':'company-switch-readonly-sample-v1','at':recovery.now(),'commands':commands,**{key:result[key] for key in refs}}
    sample_ref=recovery.immutable(out/'sample.json',recovery.encoded(sample))
    # No identity/race/version shortcut: same exact validator and exception codes.
    facts=recovery.verify_sample(job,state,sample)
    return {'sample':sample_ref,'refs':refs,'transport':transport,'worker_timing':timing_ref,'facts':facts,'ui_used':False,'new_mutations':0}
