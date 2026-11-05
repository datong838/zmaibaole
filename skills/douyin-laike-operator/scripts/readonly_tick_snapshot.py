"""Decode the deployed fixed four-read operation. No cache, action or fallback."""
import math
from urllib.parse import urlsplit

def decode(result,tab_id,window_id):
    def need(value,error):
        if not value:raise ValueError(error)
    fields={'schema','scope','commands','before','ping','tree','after','timing'}
    need(type(result) is dict and set(result)==fields and result['schema']=='readonly-scope-v1' and result['scope']=={'tabId':tab_id,'windowId':window_id},'readonly-scope-envelope-invalid')
    commands=[{'op':'tabs'},{'op':'ping','tabId':tab_id},{'op':'tree','tabId':tab_id},{'op':'tabs'}]
    need(result['commands']==commands,'readonly-scope-command-sequence-invalid')
    numeric=lambda v:type(v) in (int,float) and math.isfinite(v) and v>=0
    timing=result['timing']
    need(type(timing) is dict and set(timing)=={'clock','steps','elapsed_ms'} and timing['clock']=='worker-performance-now' and numeric(timing['elapsed_ms']) and type(timing['steps']) is list and len(timing['steps'])==4,'readonly-scope-timing-invalid')
    for row,command in zip(timing['steps'],commands):
        need(type(row) is dict and set(row)=={'op','elapsed_ms'} and row['op']==command['op'] and numeric(row['elapsed_ms']),'readonly-scope-timing-invalid')
    need(sum(row['elapsed_ms'] for row in timing['steps'])<=timing['elapsed_ms']+1e-6,'readonly-scope-timing-invalid')
    for key in ('before','after'):
        tabs=result[key];need(type(tabs) is list,'readonly-scope-tabs-invalid')
        matches=[(w,t) for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==tab_id]
        need(len(matches)==1,'readonly-scope-tab-not-unique')
        w,t=matches[0]
        need(w.get('windowId')==window_id and t.get('windowId')==window_id,'readonly-scope-window-changed')
        u=urlsplit(t.get('url',''));need(t.get('allowed') is True and u.scheme=='https' and u.netloc=='life.douyin.com','readonly-scope-site-denied')
    return result
