import importlib.util,math,os,signal,subprocess,sys,time
from datetime import date,datetime,timedelta
from pathlib import Path
from .common import *
from .store import Store
# Keep ordinary child handles until natural exit; never kill on scheduler close.
CHILDREN={}
OUTER_CLOCK_CONTRACT='system-clock-gettime-CLOCK_MONOTONIC-v1'
def system_monotonic():
    need(hasattr(time,'clock_gettime') and hasattr(time,'CLOCK_MONOTONIC'),'scheduler-system-monotonic-unavailable')
    value=time.clock_gettime(time.CLOCK_MONOTONIC)
    need(type(value) in (int,float) and math.isfinite(value) and value>=0,'scheduler-system-monotonic-invalid')
    return value
def start_outer():
    # A shared kernel clock, independent of Python 3.9/macOS process origins.
    start=system_monotonic()
    return {'started_at':now(),'start_monotonic':start,'boot':boot(),'clock_contract':OUTER_CLOCK_CONTRACT}
def finish_outer(original,context,parent_pass):
    outer=dict(original);ended=now();elapsed=None;end=None
    comparable=outer.get('clock_contract')==OUTER_CLOCK_CONTRACT and not context.get('reboot_continuation')
    reason='typed-reboot-continuation-permanently-noncomparable' if context.get('reboot_continuation') else 'legacy-or-unknown-clock-contract-no-cross-process-proof'
    if comparable:
        comparable=outer.get('boot')==boot();reason='boot-changed'
        if comparable:
            start=outer.get('start_monotonic');end=system_monotonic()
            comparable=type(start) in (int,float) and math.isfinite(start) and 0<=start<=end;reason='invalid-or-reversed-system-clock'
            if comparable:elapsed=end-start;reason=None
    else:
        # Audit only: never translate an old process-relative origin or restart it.
        outer['unverifiable_original_clock']=dict(original)
    wall_elapsed=None
    try:
        value=(timestamp(ended)-timestamp(outer['started_at'])).total_seconds()
        if math.isfinite(value) and value>=0:wall_elapsed=value
    except (KeyError,TypeError,ValueError,OverflowError):pass
    measured=bool(comparable and context.get('offer'))
    outer.update(ended_at=ended,end_monotonic=end if comparable else None,elapsed_seconds=elapsed,clock_comparable=comparable,elapsed_unverified_reason=reason,wall_elapsed_seconds_auxiliary=wall_elapsed,wall_elapsed_acceptance_eligible=False,full_workflow_measured=measured,acceptance_pass=bool(measured and parent_pass and 0<=elapsed<=30),end_boundary='after-original-parent-source-client-and-coordinator-completion-deep-verification',same_day_completed_reuse=not bool(context.get('offer')))
    return outer
def reap():
    for pid,process in list(CHILDREN.items()):
        if process.poll() is not None:CHILDREN.pop(pid,None)
CONFIG_POINTER_KIND='standalone-workshop-active-config-v1'
CONFIG_MUTABLE_FIELDS={'worker_argv','local_semantic_workers'}
def config_snapshot(path):
    path=Path(path)
    need(path.is_absolute() and path==path.resolve() and not any(p.is_symlink() for p in (path,*path.parents)) and path.is_file(),'active-config-canonical-file-required')
    raw=path.read_bytes()
    return json.loads(raw),{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
def load_active_config(root):
    root=Path(root);base,base_ref=config_snapshot(root/'config.json');pointer=root/'active_config.json'
    need(not pointer.is_symlink(),'active-config-pointer-symlink-forbidden')
    if not pointer.exists():return base,base_ref,base_ref
    grant,_=config_snapshot(pointer)
    need(type(grant) is dict and set(grant)=={'kind','base_config','config'} and grant['kind']==CONFIG_POINTER_KIND and grant['base_config']==base_ref,'active-config-pointer-base-binding')
    reference=grant['config']
    need(type(reference) is dict and set(reference)=={'path','sha256'} and re.fullmatch('[a-f0-9]{64}',str(reference.get('sha256',''))) is not None,'active-config-version-reference')
    expected=root/'config_versions'/(reference['sha256']+'.json')
    need(reference['path']==str(expected),'active-config-fixed-version-path-required')
    current,current_ref=config_snapshot(expected);need(current_ref==reference,'active-config-version-hash-changed')
    need(type(base) is dict and type(current) is dict and {k:v for k,v in current.items() if k not in CONFIG_MUTABLE_FIELDS}=={k:v for k,v in base.items() if k not in CONFIG_MUTABLE_FIELDS},'active-config-base-fields-changed')
    argv=current.get('worker_argv');need(argv is None or (type(argv) is list and bool(argv) and all(type(v) is str and bool(v) for v in argv)),'active-config-worker-argv-invalid')
    need('local_semantic_workers' not in current or type(current['local_semantic_workers']) is dict,'active-config-semantic-workers-invalid')
    return current,current_ref,base_ref

CALENDAR_MODE='cn-workdays'
CALENDAR_SOURCE=Path(__file__).resolve().parents[3]/'skills/daily-comment-stats/scripts/ds_calendar.py'
CALENDAR_DATA=CALENDAR_SOURCE.parent.parent/'config/holidays.json'
def workday_calendar():
    need(CALENDAR_SOURCE.is_file() and CALENDAR_SOURCE.resolve()==CALENDAR_SOURCE and not CALENDAR_SOURCE.is_symlink(),'scheduler-calendar-source-required')
    need(CALENDAR_DATA.is_file() and CALENDAR_DATA.resolve()==CALENDAR_DATA and not CALENDAR_DATA.is_symlink(),'scheduler-calendar-file-required')
    raw=CALENDAR_DATA.read_bytes();document=json.loads(raw);need(type(document)is dict,'scheduler-calendar-object-required');need(type(document.get('holidays'))is dict and type(document.get('workdays'))is dict,'scheduler-calendar-day-maps-invalid');spec=importlib.util.spec_from_file_location('workshop_fixed_ds_calendar',CALENDAR_SOURCE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    config,holidays,workdays=module.load_calendar(CALENDAR_DATA)
    need(type(config)is dict and type(config.get('covered_years'))is list and config['covered_years'] and all(type(y)is int and 1<=y<=9999 for y in config['covered_years']) and len(set(config['covered_years']))==len(config['covered_years']),'scheduler-calendar-covered-years-invalid')
    need(type(config.get('holidays',{}))is dict and type(config.get('workdays',{}))is dict and all(type(v)is str and date.fromisoformat(v).isoformat()==v for v in holidays|workdays),'scheduler-calendar-date-format-invalid')
    need(CALENDAR_DATA.read_bytes()==raw,'scheduler-calendar-changed-during-load')
    return module,config,holidays,workdays,{'path':str(CALENDAR_DATA),'sha256':hashlib.sha256(raw).hexdigest()}

class Engine:
    def __init__(self,root,verifier=None):
        self.config,self.active_config_ref,self.base_config_ref=load_active_config(Path(root).resolve());self.s=Store(root);self.root=self.s.root;self.verifier=verifier
    def close(self):reap();self.s.close()
    def add_plan(self,plan_id,*,at=None,start=None,daily_at=None,workflow=None,priority=50,task_id=None,initial_state='active',calendar_mode=None,collection_contract=None):
        need(initial_state in ('active','paused'),'plan-initial-state-invalid');need(calendar_mode is None or calendar_mode==CALENDAR_MODE and bool(daily_at) and not at,'plan-calendar-mode-invalid')
        need(bool(at)!=bool(daily_at),'choose-at-or-daily-at');flows=list(FLOWS) if not workflow else [workflow];need(all(f in FLOWS for f in flows),'unknown-workflow')
        if at:timestamp(at);need(not start,'oneoff-start-not-allowed')
        else:
            date.fromisoformat(start);datetime.strptime(daily_at,'%H:%M')
        need(collection_contract in(None,'three-flow-collection-ready-v1')and(not collection_contract or workflow is None),'collection-contract-requires-three-flows')
        payload={'at':at,'start':start,'daily_at':daily_at,'flows':flows,'priority':priority,'task_id':task_id}
        if collection_contract:payload['collection_contract']=collection_contract
        if calendar_mode is not None:payload['calendar_mode']=calendar_mode
        with self.s.transaction():
            old=self.s.db.execute('SELECT payload FROM plans WHERE id=?',(plan_id,)).fetchone()
            if old:need(json.loads(old[0])==payload,'plan-id-payload-conflict')
            else:self.s.db.execute('INSERT INTO plans VALUES(?,?,?)',(plan_id,json.dumps(payload,sort_keys=True),initial_state));self.s.event('plan-added',plan=plan_id)
        return plan_id
    def set_plan(self,key,state):
        need(state in ('active','paused','cancelled'),'plan-state-invalid')
        with self.s.transaction():
            row=self.s.db.execute('SELECT state FROM plans WHERE id=?',(key,)).fetchone();need(row is not None,'plan-not-found');need(row[0]!='cancelled' or state=='cancelled','cancelled-plan-immutable')
            self.s.db.execute('UPDATE plans SET state=? WHERE id=?',(state,key));self.s.event('plan-'+state,plan=key)
            if state=='cancelled':
                owner=self.s.get('resource_owner');need(not owner or self.s.task(owner)['plan_id']!=key,'active-plan-cancel-forbidden-pause-instead')
                self.s.db.execute("UPDATE tasks SET state='cancelled' WHERE plan_id=? AND state='queued'",(key,))
    def calendar_holds(self):
        return {p['id']:value for p in self.s.plans() if p.get('calendar_mode')==CALENDAR_MODE and (value:=self.s.get('calendar-hold:'+p['id']))}
    def calendar_hold(self,plan,error=None):
        key='calendar-hold:'+plan['id'];old=self.s.get(key)
        if error is None:
            if old:self.s.set(key,None);self.s.event('plan-calendar-resumed',plan=plan['id'])
            return
        try:material={'path':str(CALENDAR_DATA),'sha256':hashlib.sha256(CALENDAR_DATA.read_bytes()).hexdigest()}
        except OSError:material={'path':str(CALENDAR_DATA),'absent':True}
        fingerprint=digest({'error':str(error),'calendar':material})
        if not old or old.get('fingerprint')!=fingerprint:
            value={'kind':'workshop-plan-calendar-hold-v1','plan_id':plan['id'],'fingerprint':fingerprint,'error':str(error),'calendar':material,'at':now()};self.s.set(key,value);self.s.event('plan-calendar-held',plan=plan['id'],hold=value)
    def materialize(self,at):
        calendar=None;calendar_error=None
        for p in self.s.plans():
            if p['state']!='active':continue
            if p['at']:points=[timestamp(p['at'])]
            else:
                first=date.fromisoformat(p['start']);last=at.astimezone(ZONE).date();need((last-first).days<=3660,'missed-run-range-too-large')
                points=[datetime.fromisoformat((first+timedelta(days=i)).isoformat()+'T'+p['daily_at']+':00').replace(tzinfo=ZONE) for i in range(max(0,(last-first).days+1))]
            if p.get('calendar_mode')==CALENDAR_MODE:
                due=[point for point in points if point<=at]
                if not due:continue
                try:
                    if calendar is None and calendar_error is None:
                        try:calendar=workday_calendar()
                        except Exception as error:calendar_error=error
                    if calendar_error is not None:raise calendar_error
                    module,config,holidays,workdays,_=calendar
                    need(all(point.year in config['covered_years']for point in due),'scheduler-calendar-year-uncovered')
                    points=[point for point in due if module.is_workday(point.date(),holidays,workdays)]
                    self.calendar_hold(p)
                except Exception as error:self.calendar_hold(p,error);continue
            for point in points:
                if point>at:continue
                day=point.astimezone(ZONE).date().isoformat()
                # A once-off requested role still goes through the SAME original
                # coordinator. Missing prior roles are explicit queue dependencies.
                wanted=p['flows'];flows=list(FLOWS[:max(FLOWS.index(f) for f in wanted)+1])
                for flow in flows:
                    key=p.get('task_id') if p.get('task_id') and flow==wanted[-1] else 'task-'+digest([p['id'],day,flow])[:24]
                    payload={'day':day,'workflow':flow,'plan_id':p['id'],'requested':flow in wanted,'original_business_keys_only':True}
                    if p.get('collection_contract'):payload['collection_contract']=p['collection_contract']
                    old=self.s.db.execute('SELECT payload FROM tasks WHERE id=?',(key,)).fetchone()
                    if old:need(json.loads(old[0])==payload,'task-id-payload-conflict');continue
                    self.s.db.execute('INSERT INTO tasks(id,plan_id,day,flow,due,rank,payload,state,context) VALUES(?,?,?,?,?,?,?,?,?)',(key,p['id'],day,flow,point.isoformat(),p['priority']*10+FLOWS.index(flow),json.dumps(payload,sort_keys=True),'queued','{}'));self.s.event('task-enqueued',key)
    def harvest(self,task):
        folder=Path(task['active_attempt']);exitfile=folder/'exit.json';started=folder/'started.json'
        if exitfile.exists():
            x=read(exitfile);request=pinned(x['request']);need(request['task']['id']==task['id'] and request['attempt_id']==folder.name,'exit-original-attempt-required');need(x['attempt_id']==folder.name,'exit-attempt-conflict')
            if x['returncode']!=0:
                self.s.update(task['id'],state='failed',error='worker-exit:'+str(x['returncode']));self.s.event('worker-failed',task['id'],receipt=ref(exitfile));return
            response=pinned(x['response']);need(response.get('kind')=='workshop-worker-result-v1' and response.get('task_id')==task['id'] and response.get('attempt_id')==folder.name,'worker-result-binding')
            outcome=response.get('outcome');need(outcome in ('continue','waiting','complete','failed','collection-ready','batch-complete'),'worker-outcome-invalid');context=response.get('context',task['context'])
            need(task.get('payload',{}).get('collection_contract')!='three-flow-collection-ready-v1'or outcome!='complete','staged-legacy-completion-forbidden')
            if outcome=='complete':
                if self.verifier:self.verifier(task,response,self.config)
                else:
                    from .adapters import verify_completion
                    verify_completion(task,response,self.config)
                outer=task['outer']
                # The scheduler boundary includes issuance, handoff waits, every
                # subprocess start/exit, deep verification and scheduler delay.
                parent_pass=False
                if response.get('completion'):
                    parent_pass=pinned(response['completion']['report']).get('performance',{}).get('acceptance_pass') is True
                outer=finish_outer(outer,context,parent_pass)
                self.s.update(task['id'],state='complete',context=context,error=None,outer=outer);self.s.set('resource_owner',None)
            elif outcome=='batch-complete':
                from .adapters import verify_unified_completion
                verify_unified_completion(task,response,self.config)
                originals=task['context']['delivery_ready_tasks'];need(len(originals)==3,'delivery-three-scheduler-tasks')
                for original in originals:
                    row=self.s.task(original['id']);need(row['plan_id']==task['plan_id']and row['day']==task['day']and row['flow']==original['flow']and row['outer']==original['outer'],'delivery-scheduler-original-scope')
                    if row['id']!=task['id']:need(row['state']=='collection-ready'and row['active_attempt']==original['attempt_path']and row['context']==original['context'],'delivery-scheduler-ready-drift')
                for original in originals:
                    row=self.s.task(original['id']);closed_context={**row['context'],'unified_delivery_completion':response['unified_completion']}
                    self.s.update(row['id'],state='complete',context=closed_context,error=None,outer=finish_outer(row['outer'],closed_context,False))
                    self.s.event('unified-client-complete',row['id'],receipt=ref(exitfile),completion=response['unified_completion'])
                self.s.set('resource_owner',None)
            elif outcome=='collection-ready':
                from .adapters import verify_collection_ready
                verify_collection_ready(task,response,self.config)
                self.s.update(task['id'],state='collection-ready',context={**context,'collection_ready_receipt':response['collection_ready'],'collection_ready_attempt':str(folder)},error=None)
            elif outcome=='waiting':self.s.update(task['id'],state='waiting',context={**context,'handoff':response['handoff']},error=None)
            elif outcome=='continue':self.s.update(task['id'],state='queued',context=context,error=None)
            else:self.s.update(task['id'],state='failed',context=context,error=response.get('error','worker-held'))
            self.s.event('worker-'+outcome,task['id'],receipt=ref(exitfile));return
        if not started.exists() and (folder/'spawn.json').exists():
            spawned=read(folder/'spawn.json')
            if same_process(spawned.get('process')):self.s.update(task['id'],state='running');return
        if started.exists():
            process=read(started)['process']
            if same_process(process):self.s.update(task['id'],state='running');return
        # Never infer not-dispatched from dead/missing PID or stale timestamps.
        self.s.update(task['id'],state='unknown',error='missing-original-exit-receipt-no-blind-spawn');self.s.event('unknown-process-outcome',task['id'])
    def defer_download(self,proof_ref):
        from . import deferred_download_handoff as deferred
        return deferred.start(self,proof_ref)
    def tick(self,at=None):
        from . import deferred_download_handoff as deferred
        deferred_progress=deferred.advance(self)
        if deferred_progress:return deferred_progress
        from . import quiescent_lease_handoff as handoff
        handoff_progress=handoff.advance(self)
        if handoff_progress and handoff_progress.get('action')=='environment-restoration-continue':return handoff_progress
        reap();at=at or datetime.now(ZONE)
        with lock(self.root/'scheduler.lock'):
            with self.s.transaction():
                binding=handoff.admission(self)
                download_deferral=deferred.admission(self)
                self.materialize(at);owner=self.s.get('resource_owner')
                if owner:
                    task=self.s.task(owner)
                    if task['state'] in ('dispatching','running'):
                        try:self.harvest(task)
                        except Exception as e:self.s.update(owner,state='unknown',error='receipt-verification:'+str(e));self.s.event('receipt-rejected',owner,error=str(e))
                    task=self.s.task(owner)
                    if task['state'] in ('waiting','failed','unknown'):return {'action':'blocked','task':owner,'state':task['state']}
                    if task['state']=='collection-ready':
                        deferred_result=deferred.collection_transition(self,task)
                        if deferred_result:return deferred_result
                        from .staged_delivery import next_collection_task
                        next_task=next_collection_task(task,self.s.tasks())
                        if next_task is None:
                            from .staged_delivery import delivery_context
                            context=delivery_context(task,self.s.tasks())
                            self.s.update(owner,state='queued',context=context,error=None)
                            self.s.event('collection-batch-staged',owner,ready_exits=[v['exit']for v in context['delivery_ready_tasks']],original_attempt=task['active_attempt'])
                            return {'action':'delivery-staged','task':owner,'business_complete':False}
                        self.s.set('resource_owner',next_task['id']);self.s.event('collection-lease-transferred',next_task['id'],previous_task=owner,original_ready_attempt=task['active_attempt']);owner=next_task['id'];task=next_task
                    if task['state']=='complete':owner=None
                    elif task['state']!='queued':return {'action':'wait-original-process','task':owner}
                held_plans=self.calendar_holds();tasks=self.s.tasks()
                # due is the task's earliest start, not just an ordering key:
                # a queued task is claimable only once its due instant has
                # passed. Existing enqueues always carry a past due, so this
                # gate changes nothing retroactively - it only stops a queue
                # that drains early from pulling a deferred day forward.
                eligible=[t for t in tasks if t['state']=='queued' and datetime.fromisoformat(t['due'])<=at and t['plan_id']not in held_plans and handoff.eligible(binding,t) and next(p for p in self.s.plans() if p['id']==t['plan_id'])['state']=='active']
                task=self.s.task(owner) if owner else (eligible[0] if eligible else None)
                if task and next(p for p in self.s.plans() if p['id']==task['plan_id'])['state']!='active':return {'action':'plan-paused-original-resource-retained','task':task['id']}
                if task and task['plan_id']in held_plans:return {'action':'calendar-held-original-resource-retained','task':task['id'],'plan':task['plan_id']}
                if not task:return {'action':'calendar-plan-held','plans':list(held_plans)} if held_plans else {'action':'idle'}
                need(handoff.eligible(binding,task),'handoff-selected-task-outside-stage')
                # All earlier business roles/days must finish, independent of plans.
                prior=[t for t in tasks if t['state'] not in ('complete','cancelled') and not(binding and t['id']==binding['old_task'] and t['state']=='parked' and binding['phase']=='new-first-two') and (t['day'],FLOWS.index(t['flow']))<(task['day'],FLOWS.index(task['flow']))]
                if task.get('payload',{}).get('collection_contract')=='three-flow-collection-ready-v1':
                    prior=[t for t in prior if not(t['state']=='collection-ready'and t['plan_id']==task['plan_id']and t['day']==task['day']and t.get('payload',{}).get('collection_contract')==task['payload']['collection_contract'])]
                if download_deferral:prior=[t for t in prior if t['id']!=download_deferral['daily']['id']]
                if prior:return {'action':'wait-prior-workflow','task':prior[0]['id']}
                need(pinned(self.active_config_ref)==self.config and ref(self.root/'config.json')==self.base_config_ref,'active-config-changed-after-load')
                task=handoff.bind_new_scope(self,binding,task)
                index=task['attempt']+1;folder=self.root/'attempts'/(task['id']+'-'+str(index));folder.mkdir(parents=True,exist_ok=True)
                outer=task['outer'] or start_outer()
                request={'kind':'workshop-worker-request-v1','attempt_id':folder.name,'task':{**task,'outer':outer},'context':task['context'],'config':self.config,'config_ref':self.active_config_ref,'root':str(self.root)}
                request_ref=immutable(folder/'request.json',request);intent={'kind':'local-dispatch-intent-v1','attempt_id':folder.name,'task_id':task['id'],'request':request_ref,'at':now(),'outer':outer}
                immutable(folder/'intent.json',intent);self.s.update(task['id'],state='dispatching',attempt=index,active_attempt=str(folder),outer=outer);self.s.set('resource_owner',task['id']);self.s.event('dispatch-intent',task['id'],intent=ref(folder/'intent.json'))
            # The committed intent is deliberately before Popen. A crash here is
            # unknown forever until an explicit bound external reconciliation.
            argv=[sys.executable,'-m','workshop_director.worker','--attempt',str(folder)]
            env=os.environ.copy();env['PYTHONPATH']=str(Path(__file__).resolve().parent.parent)
            try:
                with (folder/'runner.log').open('ab') as output:proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
                CHILDREN[proc.pid]=proc
                immutable(folder/'spawn.json',{'attempt_id':folder.name,'pid':proc.pid,'process':identity(proc.pid),'argv':argv,'at':now()})
            except Exception as e:
                with self.s.transaction():self.s.update(task['id'],state='unknown',error='spawn-outcome-unknown:'+str(e))
                return {'action':'unknown','task':task['id']}
            return {'action':'spawned','task':task['id'],'pid':proc.pid,'attempt_id':folder.name}
    def accept(self,key,response_ref):
        with lock(self.root/'scheduler.lock'),self.s.transaction():
            task=self.s.task(key);need(task['state']=='waiting','task-not-waiting');request=task['context']['handoff'];value=pinned(response_ref)
            need(value.get('request')==request and value.get('task_id')==key,'handoff-response-binding');need(value.get('kind')=='workshop-handoff-response-v1','handoff-response-kind')
            self.s.update(key,state='queued',context={**task['context'],'response':response_ref});self.s.event('handoff-accepted',key,response=response_ref)
    def repair(self,key,proof_ref,unknown=False):
        proof=pinned(proof_ref)
        with lock(self.root/'scheduler.lock'),self.s.transaction():
            task=self.s.task(key);need(task['state'] in ('failed','unknown'),'task-not-repairable')
            need(proof.get('kind')=='workshop-repair-v1' and proof.get('task_id')==key and proof.get('attempt_id')==Path(task['active_attempt']).name,'repair-scope')
            need(all(proof.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_order_keys_preserved')),'repair-quiescence-and-order-required')
            if task['state']=='unknown':
                need(unknown and proof.get('outcome')=='original-receipt-reconciled','unknown-requires-original-exit-reconciliation')
                # An absent receipt can never authorize a replacement child.
                need((Path(task['active_attempt'])/'exit.json').is_file(),'unknown-original-exit-receipt-required');self.harvest(task);return
            need(proof.get('outcome')=='repaired-existing-order','repair-outcome');need(not same_process(read(Path(task['active_attempt'])/'started.json')['process']),'original-process-still-alive')
            if proof.get('reboot_continuation'):
                import sys
                sys.path.insert(0,str(Path(self.config['project'])/'skills/violation-notifier/scripts'))
                import violation_reboot_continuation as reboot
                value=reboot.verify(proof['reboot_continuation'],live_boot=boot())
                need(value['task_id']==key and value['attempt_id']==Path(task['active_attempt']).name and value['original']['outer']==task['outer'],'repair-reboot-original-task')
                self.s.update(key,context={**task['context'],'reboot_continuation':proof['reboot_continuation']},state='queued',error=None)
                self.s.event('explicit-retry-original-task',key,repair=proof_ref,reboot_continuation=proof['reboot_continuation'],clock_comparable=False)
            else:self.s.update(key,state='queued',error=None);self.s.event('explicit-retry-original-task',key,repair=proof_ref)
    def cancel_task(self,key):
        with lock(self.root/'scheduler.lock'),self.s.transaction():
            task=self.s.task(key)
            if task['state']=='failed':
                # A terminal bootstrap failure with no business lease can be
                # discarded without repairing or replaying its coordinator call.
                need(not task['context'],'cannot-cancel-failed-business-context')
                folder=Path(task['active_attempt']);ended=read(folder/'exit.json');response=pinned(ended['response'])
                need(response.get('outcome')=='failed' and response.get('task_id')==key and not response.get('context'),'cancel-failed-bootstrap-receipt')
                need(not same_process(read(folder/'started.json')['process'])and not same_process(read(folder/'child-process.json')['process']),'cannot-cancel-live-bootstrap')
                state=read(Path(self.config['coordinator_root'])/'state.json')
                need(state.get('delivery_complete')is True and state['day']<task['day'],'cancel-bootstrap-previous-delivery-required')
                if self.s.get('resource_owner')==key:self.s.set('resource_owner',None)
            else:need(task['state']=='queued' and self.s.get('resource_owner')!=key,'cannot-cancel-active-or-unknown-task')
            self.s.update(key,state='cancelled');self.s.event('task-cancelled',key)
