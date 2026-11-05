#!/usr/bin/env python3
"""Supervisor issue telemetry only: never executes work or alters an E2E clock."""
import argparse,json,math,re
from pathlib import Path
import execution_timing as t
KIND='supervisor-rehearsal-issues-v1'
CATEGORIES=('model-wait','code-repair','webpage-wait')
NEXT={'open':{'repair-start','failed'},'repair-start':{'resume','failed'},'resume':{'verified','failed'}}
def check_ref(ref):
 t.need(type(ref) is dict and set(ref)=={'path','sha256'} and Path(ref['path']).is_absolute() and re.fullmatch('[a-f0-9]{64}',ref['sha256']) is not None,'issue-reference-invalid')
 p=Path(ref['path']);t.need(p.is_file() and not p.is_symlink() and t.ref(p)==ref,'issue-reference-changed');return p

def check_binding(binding):
 t.need(type(binding) is dict and set(binding)=={'workflow','round_id','anchor','previous_round'} and binding['workflow'] in t.FLOWS and re.fullmatch('[A-Za-z0-9_-]{1,100}',binding['round_id']) is not None,'issue-round-binding-invalid')
 check_ref(binding['anchor'])
 if binding['previous_round']:
  previous=json.loads(check_ref(binding['previous_round']).read_bytes());old=previous['binding']
  t.need(previous['kind']==KIND and old['workflow']==binding['workflow'] and old['round_id']!=binding['round_id'] and previous['issues'] and all(x['events'][-1]['step'] in ('verified','failed') for x in previous['issues'].values()),'issue-previous-round-invalid')

def validate(state,clock,now):
 t.need(state.get('kind')==KIND and state.get('clock')==t.MONOTONIC_CLOCK,'issue-original-ledger-required')
 t.need(state['binding_sha256']==t.digest(state['binding']),'issue-binding-changed');check_binding(state['binding'])
 t.need(clock.boot()==state['boot'] and t.finite(now) and now>=state['recorded_monotonic'],'issue-boot-or-monotonic-changed')
 for issue in state['issues'].values():
  t.need(type(issue['stop_refs']) is list and issue['stop_refs'],'issue-stop-reference-required')
  for ref in issue['stop_refs']:check_ref(ref)
  last=state['recorded_monotonic'];previous=None
  for event in issue['events']:
   t.need(event['step']=='open' if previous is None else event['step'] in NEXT.get(previous,set()),'issue-transition-corrupt');previous=event['step']
   if event['monotonic'] is None:t.need(event['step']=='open' and issue['historical'] and event['at'] is None,'issue-missing-clock-invalid')
   else:t.need(t.finite(event['monotonic']) and last<=event['monotonic']<=now,'issue-monotonic-invalid');last=event['monotonic']
   t.need(event['category'] in CATEGORIES if event['step'] not in ('verified','failed') else event['category'] is None,'issue-category-invalid')
   if event['evidence']:check_ref(event['evidence'])

def view(state,now):
 out={**state['binding'],'clock':state['clock'],'boot':state['boot'],'measurement_only':True,'e2e_clock_modified':False,'issues':{}}
 for key,issue in state['issues'].items():
  events=issue['events'];by={x['step']:x for x in events};terminal=events[-1]['step'] in ('verified','failed');cost={x:0 for x in CATEGORIES}
  for a,b in zip(events,events[1:]+([] if terminal else [{'monotonic':now}])):
   if a['monotonic'] is not None:cost[a['category']]+=b['monotonic']-a['monotonic']
  def duration(a,b):return by[b]['monotonic']-by[a]['monotonic'] if a in by and b in by and by[a]['monotonic'] is not None else None
  out['issues'][key]={'stop_refs':issue['stop_refs'],'state':events[-1]['step'],'result':events[-1]['step'] if terminal else None,'discovery_to_resume_seconds':duration('open','resume'),'repair_seconds':duration('repair-start','resume') if 'resume' in by else duration('repair-start',events[-1]['step']) if terminal else None,'verification_seconds':duration('resume',events[-1]['step']) if terminal else None,'discovery_to_terminal_seconds':duration('open',events[-1]['step']) if terminal else None,'category_seconds':cost,'events':events,'historical_onset_unknown':issue['historical']}
 return out

def apply(path,step,issue_id,*,binding=None,category=None,evidence=None,historical=False,clock=None):
 clock=clock or t.Clock();now=clock.monotonic();wall=t.stamp(clock)
 t.need(not historical or step=='open','issue-historical-onset-only')
 t.need(re.fullmatch('[A-Za-z0-9_-]{1,100}',issue_id) is not None and step in ('open','repair-start','resume','verified','failed'),'issue-command-invalid')
 t.need(category in CATEGORIES if step not in ('verified','failed') else category is None,'issue-category-required')
 if step in ('verified','failed'):t.need(evidence is not None,'issue-verification-evidence-required')
 if evidence:check_ref(evidence)
 if step=='open':
  t.need(type(binding) is dict and set(binding)=={'workflow','round_id','anchor','stop_refs','previous_round'} and type(binding['stop_refs']) is list and binding['stop_refs'],'issue-binding-invalid')
  round_binding={k:v for k,v in binding.items() if k!='stop_refs'};check_binding(round_binding)
  for ref in binding['stop_refs']:check_ref(ref)
  refs=[binding['anchor'],*binding['stop_refs']]+([binding['previous_round']] if binding['previous_round'] else [])
  t.need(str(Path(path).resolve()) not in [r['path'] for r in refs],'issue-ledger-aliases-evidence')
 t.need(not Path(path).is_symlink() and (not Path(path).exists() or json.loads(Path(path).read_bytes()).get('kind')==KIND),'issue-original-ledger-required')
 with t.locked(path) as ledger:
  if ledger.exists():state=json.loads(ledger.read_bytes());validate(state,clock,now)
  else:
   t.need(step=='open','issue-open-required');state={'kind':KIND,'binding':round_binding,'binding_sha256':t.digest(round_binding),'clock':t.MONOTONIC_CLOCK,'boot':clock.boot(),'recorded_monotonic':now,'recorded_at':wall,'issues':{}}
  if step=='open':t.need(state['binding']==round_binding,'issue-round-binding-conflict')
  found=state['issues'].get(issue_id)
  payload={'step':step,'category':category,'evidence':evidence}
  if found:
   same=[x for x in found['events'] if x['step']==step]
   if same:
    t.need(all(same[0][k]==v for k,v in payload.items()) and (step!='open' or historical==found['historical'] and binding['stop_refs']==found['stop_refs']),'issue-repeat-conflict');return view(state,now)
   t.need(step in NEXT.get(found['events'][-1]['step'],set()),'issue-transition-invalid')
  else:
   t.need(step=='open','issue-open-required');found={'stop_refs':binding['stop_refs'],'historical':historical,'events':[]};state['issues'][issue_id]=found
  found['events'].append({**payload,'monotonic':None if step=='open' and historical else now,'at':None if step=='open' and historical else wall,'recorded_at':wall})
  validate(state,clock,now);t.save(ledger,state);return view(state,now)

def main(argv=None,*,clock=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('step',choices=('open','repair-start','resume','verified','failed','status'));parser.add_argument('--ledger',required=True);parser.add_argument('--issue',required=True);parser.add_argument('--workflow',choices=t.FLOWS);parser.add_argument('--round',dest='round_id');parser.add_argument('--anchor');parser.add_argument('--stop-ref',action='append',default=[]);parser.add_argument('--previous-round');parser.add_argument('--historical',action='store_true');parser.add_argument('--category',choices=CATEGORIES);parser.add_argument('--evidence');a=parser.parse_args(argv);clock=clock or t.Clock()
 try:
  if a.step=='status':
   t.need(not Path(a.ledger).is_symlink() and json.loads(Path(a.ledger).read_bytes()).get('kind')==KIND,'issue-original-ledger-required')
   with t.locked(a.ledger) as ledger:state=json.loads(ledger.read_bytes());now=clock.monotonic();validate(state,clock,now);result=view(state,now)
  else:
   t.need(a.step=='open' or not(a.workflow or a.round_id or a.anchor or a.stop_ref or a.previous_round or a.historical),'issue-open-fields-only')
   binding={'workflow':a.workflow,'round_id':a.round_id,'anchor':t.ref(a.anchor),'stop_refs':[t.ref(p) for p in a.stop_ref],'previous_round':t.ref(a.previous_round) if a.previous_round else None} if a.step=='open' else None
   category=a.category or {'open':'model-wait','repair-start':'code-repair','resume':'webpage-wait'}.get(a.step)
   result=apply(a.ledger,a.step,a.issue,binding=binding,category=category,evidence=t.ref(a.evidence) if a.evidence else None,historical=a.historical,clock=clock)
  print(json.dumps(result,ensure_ascii=False));return 0
 except (ValueError,OSError,KeyError,TypeError,t.subprocess.SubprocessError) as error:print(json.dumps({'ok':False,'error':str(error),'measurement_only':True}));return 2
if __name__=='__main__':raise SystemExit(main())
