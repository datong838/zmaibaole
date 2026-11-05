"""Exact staged-delivery cursor transaction. No browser, sender or task setter.
Public application requires the original delivery worker and all common locks.
"""
import contextlib,copy,fcntl,hashlib,json,os,sqlite3,tempfile
from pathlib import Path
from datetime import datetime,timezone
from collection_ready import need,ref,raw,doc,immutable,encode,regular
import unified_delivery as delivery
ROOT=Path(__file__).resolve().parents[3]
def _hash(b):return hashlib.sha256(b).hexdigest()
def _atomic(path,data,mode):
    regular(path);fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path);fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def _prefix(commits):
    states=[]
    for c in commits:
        p=regular(c['target']['path']);need(p.stat().st_mode&0o777==c['mode'],'delivery-ledger-mode-drift');current=ref(p)
        if current==c['target']:states.append('before')
        elif current=={'path':str(p),'sha256':c['after']['sha256']}:states.append('after')
        else:raise ValueError('delivery-ledger-foreign-pair')
        need(c['target']['sha256']==c['before_archive']['sha256'],'delivery-before-archive');raw(c['before_archive']);raw(c['after'])
    need(states==sorted(states,key=lambda x:0 if x=='after'else 1),'delivery-nonprefix-commit')
    return states

def _apply(intent_ref,folder,guard,*,checkpoint=None):
    """Shared exact CAS core, also exercised on synthetic TEMP files.
    Caller has already rederived this exact intent using completion_values.
    """
    value=doc(intent_ref);folder=Path(folder);commits=value['commits'];states=_prefix(commits);result=folder/'result.json'
    expected={'kind':'unified-cursor-commit-v1','intent':intent_ref,'batch':value['batch'],'client_proof':value['client_proof'],'after':[{'path':c['target']['path'],'sha256':c['after']['sha256']}for c in commits],'completed_at':value['completed_at']}
    for index,(commit,state)in enumerate(zip(commits,states)):
        receipt=folder/('commit-%04d.json'%index)
        expected_receipt={'kind':'unified-ledger-CAS-v1','intent':intent_ref,'index':index,'before':commit['target'],'after':{'path':commit['target']['path'],'sha256':commit['after']['sha256']}}
        if receipt.exists():need(doc(ref(receipt))==expected_receipt and state=='after','delivery-commit-receipt-conflict')
    # A terminal artifact can never be discovered only after advancing ledgers.
    if result.exists():
        need(doc(ref(result))==expected and all(s=='after'for s in states)and all((folder/('commit-%04d.json'%i)).exists()for i in range(len(commits))),'delivery-terminal-conflict');guard.check();return ref(result)
    guard.check()
    for index,(commit,state)in enumerate(zip(commits,states)):
        guard.check();_prefix(commits)
        if state=='before':
            need(ref(commit['target']['path'])==commit['target'],'delivery-CAS-conflict');_atomic(Path(commit['target']['path']),raw(commit['after']),commit['mode'])
            if checkpoint:checkpoint('after-CAS',index)
        need(ref(commit['target']['path'])=={'path':commit['target']['path'],'sha256':commit['after']['sha256']},'delivery-CAS-readback')
        receipt={'kind':'unified-ledger-CAS-v1','intent':intent_ref,'index':index,'before':commit['target'],'after':{'path':commit['target']['path'],'sha256':commit['after']['sha256']}}
        guard.check();immutable(folder/('commit-%04d.json'%index),encode(receipt))
    guard.check();need(all(s=='after'for s in _prefix(commits)),'delivery-incomplete-CAS');return immutable(result,encode(expected))

DAILY_READY_PARENT={'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/daily-parent-executions/2a41903c76e070450c340ec338aeb7065923c3d476d2ee347519091a180c6f64/state.json', 'sha256': 'e3776058f3df90e39e7e1bc2fff0962b351adf3fac3e5364cc5b9ea5053983c0'}
DAILY_READY_ORIGINAL=[{'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/daily_execution_launcher.py', 'sha256': '36c5c48c63025a177b42fc5ee68f8085c75c7903b4dfa827900b00b188ad5869'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/daily_timed_run.py', 'sha256': '158c1f25014bd45d1f0db71db7dc09ae2b01cfdc71d15e8691f3dbb2d2fd8839'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', 'sha256': 'e688a0e00cf70a558ce93b773787bfc62a79a1f9517de7c19488d715cd29d35d'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/daily_dispatch_order.py', 'sha256': 'a640751fbf4a38c3cb9eac06320f70ed61eec6e7c0b955dc3961327e1095b802'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/notification_backlog.py', 'sha256': '7c432dcb46a443d8d19ea24596cc2c5fa256439cc572511b4562e236bd5580eb'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/flow.py', 'sha256': '873f8f73987850f072586a4c03079d292b3ad96d5abfca8a1bc5e90e8ade2914'}]
DAILY_READY_CURRENT=[{'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/daily_execution_launcher.py', 'sha256': 'a5cce1a8a70f3d3b869f42244d590f8b442a8108e688750ae8adc9e1a57c3fe3'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/daily_timed_run.py', 'sha256': '948080fa43124fe4e154ae7da02aabea8abc3b1cfc87abcfb56b27b2d09fc21e'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', 'sha256': 'b18f998ba339d25ec278bd1ea4a09749f4c0280f76caacce7cfa9fd7b803e592'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/daily_dispatch_order.py', 'sha256': 'a640751fbf4a38c3cb9eac06320f70ed61eec6e7c0b955dc3961327e1095b802'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/notification_backlog.py', 'sha256': '9a4c8c6fa95df9cc69bef40a16d9dc2757542ac083c02eb8819ed36eaf3f9023'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/flow.py', 'sha256': 'e4a877106194bf17a818af9433387f484e37dc944d65dff490adf0228c23f881'}]

def ready_source_refs(report,flow):
    """Original producer source identities, read as accepted historical data.
    The only consumer below checks the unchanged actual worker supervisor.
    Natural ready receipts and all live worker/ledger guards remain separate.
    """
    need(flow in ('daily-comment-stats','negative-review-complaints','violation-notifier'),'delivery-fixed-ready-source-flow')
    parent=doc(report.get('parent_archive')or report['parent']);original=parent['code_refs']
    need(len({r['path']for r in original})==len(original),'delivery-original-source-duplicates')
    return original


class WorkerGuard:
    """Existing scheduler/resource lease + exact natural ready-attempt receipts.
    OS identity is PID/start/boot only; no argv or environment is read.
    """
    def __init__(self,request_ref):
        self.reference=request_ref;self.request=doc(request_ref);r=self.request;self.root=Path(r['root']);self.coordinator=Path(r['config']['coordinator_root']);self.context=r['context'];self.task=r['task'];self.handles=[];self.baseline=None;self.mutable_targets=set()
        need(self.root==ROOT/'runtime/standalone-workshop-director'and self.coordinator==ROOT/'runtime/workshop-director'and r.get('kind')=='workshop-worker-request-v1'and self.task['flow']=='violation-notifier'and self.task['payload'].get('collection_contract')==delivery.CONTRACT,'delivery-fixed-worker-roots-contract')
        need(self.context.get('stage')=='unified-delivery'and request_ref['path']==str(self.root/'attempts'/r['attempt_id']/'request.json')and self.task['id']+'-'+str(self.task['attempt']+1)==r['attempt_id'],'delivery-original-worker-request')
        need(r['config'].get('project')==str(ROOT)and doc(r['config_ref'])==r['config'],'delivery-worker-config-ref')
    def queue(self):
        connection=sqlite3.connect((self.root/'queue.sqlite3').as_uri()+'?mode=ro',uri=True);connection.row_factory=sqlite3.Row;connection.execute('BEGIN')
        try:return {name:[dict(row)for row in connection.execute('SELECT * FROM '+name+' ORDER BY '+('key'if name=='meta'else'id'))]for name in('tasks','plans','meta')}
        finally:connection.rollback();connection.close()
    @contextlib.contextmanager
    def locked(self,targets):
        from workshop_director.common import lock
        resource=self.coordinator/'browser-wecom.resource.lock';text=os.environ.get('WORKSHOP_STAGED_RESOURCE_FD','');need(text.isdigit(),'delivery-inherited-resource-fd-required');descriptor=int(text);stat=os.fstat(descriptor);need((stat.st_dev,stat.st_ino)==(resource.stat().st_dev,resource.stat().st_ino),'delivery-inherited-resource-inode')
        # A separate open description must observe the already-held resource.
        with resource.open('a')as probe:
            try:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:
                fcntl.flock(probe,fcntl.LOCK_UN);raise ValueError('delivery-inherited-resource-not-held')
        paths=[self.root/'scheduler.lock',self.coordinator/'.lock']
        paths+=sorted({Path(t).parent/('.workflow.lock'if Path(t).name=='progress.json'else'.lock')for t in targets},key=str)
        protected,ledgers=self.ready_protected()
        need(not targets or set(targets)=={r['path']for r in ledgers},'delivery-exact-ledger-mutable-partition')
        self.mutable_targets=set(targets)
        with contextlib.ExitStack()as stack:
            inherited=stack.enter_context(os.fdopen(os.dup(descriptor),'a'));self.handles=[{'file':inherited,'path':resource}]+[{'file':stack.enter_context(lock(p,blocking=(p==self.root/'scheduler.lock'))),'path':p}for p in paths]
            try:self.check();yield self
            finally:self.handles=[];self.baseline=None;self.mutable_targets=set()
    def ready_protected(self):
        protected=[];ledgers=[]
        for original in self.context['delivery_ready_tasks']:
            report=doc(original['context']['collection_ready_receipt']['report'])
            if original['flow']=='daily-comment-stats':
                need(report.get('kind')=='daily-director-collection-ready-report-v1','delivery-current-daily-reader-required')
                protected.extend([report['order'],report['ready']]);ready=doc(report['ready']);ledgers.append(ready['original_progress'])
            else:
                protected.extend([report['original_parent'],report['original_engine']]);ledgers.extend(x['original']for x in report['ledgers'])
        return protected,ledgers
    def check(self):
        need(bool(self.handles)and all(not h['file'].closed and os.fstat(h['file'].fileno()).st_ino==h['path'].stat().st_ino for h in self.handles),'delivery-original-locks-required')
        protected,ledgers=self.ready_protected()
        for reference in protected+ledgers:
            if reference['path']not in self.mutable_targets:raw(reference)
        need(doc(self.reference)==self.request and doc(self.request['config_ref'])==self.request['config'],'delivery-request-config-drift');q=self.queue();rows=q['tasks'];t=next(x for x in rows if x['id']==self.task['id']);context=json.loads(t['context']);payload=json.loads(t['payload']);outer=json.loads(t['outer'])
        need(t['state']in('dispatching','running')and t['active_attempt']==str(Path(self.reference['path']).parent)and t['attempt']==self.task['attempt']+1 and t['plan_id']==self.task['plan_id']and t['day']==self.task['day']and payload==self.task['payload']and context==self.context and outer==self.task['outer']and not t['error'],'delivery-current-worker-task-drift')
        need(json.loads(next(x['value']for x in q['meta']if x['key']=='resource_owner'))==t['id'],'delivery-original-owner-required')
        from workshop_director.common import same_process
        current=doc(ref(Path(self.reference['path']).parent/'started.json'));child=doc(ref(Path(self.reference['path']).parent/'child-process.json'));need(current['process']['pid']==os.getppid()and same_process(current['process'])and child['process']['pid']==child['pid']==os.getpid()and same_process(child['process'])and current['request']==self.reference and current['attempt_id']==child['attempt_id']==self.request['attempt_id'],'delivery-original-live-worker-parent')
        binding=current['resource_binding'];resource=self.coordinator/'browser-wecom.resource.lock';stat=os.fstat(self.handles[0]['file'].fileno());need(binding==child['resource_binding']and set(binding)=={'kind','path','device','inode','fd','supervisor_source'}and binding['kind']=='staged-inherited-resource-lock-v1'and binding['path']==str(resource)and(binding['device'],binding['inode'])==(stat.st_dev,stat.st_ino)and binding['fd']==int(os.environ['WORKSHOP_STAGED_RESOURCE_FD']),'delivery-original-resource-binding');raw(binding['supervisor_source'])
        ready=self.context['delivery_ready_tasks'];need(len(ready)==3 and {x['flow']for x in ready}=={'daily-comment-stats','negative-review-complaints','violation-notifier'},'delivery-three-original-ready-tasks')
        for original in ready:
            row=next(x for x in rows if x['id']==original['id']);need(row['plan_id']==t['plan_id']and row['day']==t['day']and row['flow']==original['flow'],'delivery-ready-task-scope')
            if row['id']!=t['id']:need(row['state']=='collection-ready'and row['active_attempt']==original['attempt_path']and json.loads(row['context'])==original['context'],'delivery-ready-task-drift')
            exit_ref=ref(Path(original['attempt_path'])/'exit.json');need(exit_ref==original['exit'],'delivery-original-exit-drift');ended=doc(exit_ref);response=doc(ended['response']);old_request=doc(ended['request']);need(ended['returncode']==0 and response['outcome']=='collection-ready'and response['task_id']==row['id']and response['attempt_id']==Path(original['attempt_path']).name and response['collection_ready']==original['context']['collection_ready_receipt']and old_request['task']['id']==row['id']and all(old_request['task'][k]==row[k]for k in('plan_id','day','flow'))and old_request['attempt_id']==Path(original['attempt_path']).name and old_request['task']['outer']==original['outer'],'delivery-original-natural-ready-exit')
            started=doc(ref(Path(original['attempt_path'])/'started.json'));need(not same_process(started['process']),'delivery-ready-worker-still-live')
        coordinator=doc(ref(self.coordinator/'state.json'));expected_reports={x['flow']:x['context']['collection_ready_receipt']['report']for x in ready}
        need(coordinator.get('day')==t['day']and coordinator.get('phase')=='ready'and coordinator.get('index')==3 and coordinator.get('collection_contract')==delivery.CONTRACT and coordinator.get('collection_ready_reports')==expected_reports,'delivery-coordinator-three-ready-drift')
        if self.baseline is not None:need(self.coordinator_ref==ref(self.coordinator/'state.json'),'delivery-coordinator-drift')
        else:self.coordinator_ref=ref(self.coordinator/'state.json')
        need(binding['supervisor_source']['path']==str(ROOT/'packages/workshop-director/workshop_director/worker.py'),'delivery-current-supervisor-source-required')
        need(not any(x['id']!=t['id']and x['state']in('dispatching','running','unknown')for x in rows),'delivery-other-live-or-unknown-task')
        if self.baseline is None:self.baseline=q
        else:need(q==self.baseline,'delivery-queue-plan-lease-drift')

def reentry_request(current_ref,original_ref):
    """Bind the current retry to the same immutable transaction and last exit.
    No predecessor-chain traversal and no authority to invoke a sender.
    """
    current=doc(current_ref);original=doc(original_ref)
    if current_ref==original_ref:return original_ref
    from workshop_director.common import same_process
    task=current['task'];other=original['task']
    need(all(task[k]==other[k]for k in('id','plan_id','day','flow','payload','outer'))and current['context']==original['context']and current['config_ref']==original['config_ref']and current['root']==original['root'],'delivery-reentry-original-key-context')
    path=Path(task['active_attempt'])
    need(path.parent==Path(current['root'])/'attempts'and path.name==task['id']+'-'+str(task['attempt']),'delivery-reentry-current-predecessor')
    ended=doc(ref(path/'exit.json'));prior=doc(ended['request'])
    need(ended['request']['path']==str(path/'request.json')and ended.get('attempt_id')==path.name and prior['task']['id']==task['id']and prior['attempt_id']==path.name and prior['task']['attempt']+1==task['attempt'],'delivery-reentry-current-exit-binding')
    failed=type(ended.get('returncode'))is int and ended['returncode']!=0
    if ended.get('response'):failed=failed or doc(ended['response']).get('outcome')=='failed'
    need(failed and not same_process(doc(ref(path/'started.json'))['process']),'delivery-reentry-natural-failed-exit')
    need(other['attempt']<task['attempt'],'delivery-reentry-attempt-decrease')
    return original_ref


def apply(request_ref,client_proof_ref,delivery_folder):
    """No CLI; only the original final delivery worker may call this function."""
    guard=WorkerGuard(request_ref);proof=doc(client_proof_ref);batch=doc(proof['batch']);folder=Path(proof['batch']['path']).parent/'completion';intent=folder/'intent.json';sender_directory=ROOT/'runtime/wecom-messenger'
    need(batch['round_key']==guard.task['plan_id']+':'+guard.task['day'],'delivery-original-round-key')
    completed_at=doc(ref(intent))['completed_at']if intent.exists()else datetime.now(timezone.utc).isoformat()
    values=delivery.completion_values(client_proof_ref,delivery_folder,sender_directory=sender_directory,completed_at=completed_at)
    with guard.locked([v['target']['path']for v in values]):
        # Re-read the complete client/source qualification after taking locks.
        need(values==delivery.completion_values(client_proof_ref,delivery_folder,sender_directory=sender_directory,completed_at=completed_at),'delivery-facts-raced-before-lock')
        commits=[]
        for index,value in enumerate(values):
            original=value['target'];before=value['before_archive'];need(raw(before)and original['sha256']==before['sha256'],'delivery-before-archive-binding');target=regular(original['path']);after_bytes=encode(value['after']);after_hash=_hash(after_bytes)
            if not intent.exists():need(ref(target)==original,'delivery-unowned-after-bytes')
            before_ref=immutable(folder/('before-%04d.json'%index),raw(before));after_ref=immutable(folder/('after-%04d.json'%index),after_bytes);commits.append({'workflow':value['workflow'],'target':original,'before_archive':before_ref,'after':after_ref,'mode':target.stat().st_mode&0o777})
        original_request=doc(ref(intent))['request']if intent.exists()else request_ref
        reentry_request(request_ref,original_request)
        payload={'kind':'three-flow-ledger-commit-intent-v1','batch':proof['batch'],'client_proof':client_proof_ref,'request':original_request,'completed_at':completed_at,'commits':commits}
        guard.check();intent_ref=immutable(intent,encode(payload));return _apply(intent_ref,folder,guard)


def completion_facts(result_ref,delivery_folder,*,current=False):
    """Read-only typed completion facts. Historical after bytes are immutable;
    initial coordinator/task admission additionally checks canonical after files.
    No status flag or string can manufacture this proof.
    """
    result=doc(result_ref);intent_ref=result['intent'];intent=doc(intent_ref);folder=Path(intent_ref['path']).parent
    need(result_ref['path']==str(folder/'result.json')and intent_ref['path']==str(Path(result['batch']['path']).parent/'completion/intent.json')and intent['kind']=='three-flow-ledger-commit-intent-v1','delivery-result-canonical-origin')
    request=doc(intent['request']);task=request['task'];need(request['context'].get('stage')=='unified-delivery'and task['payload'].get('collection_contract')==delivery.CONTRACT and task['flow']=='violation-notifier','delivery-original-final-worker')
    values=delivery.completion_values(intent['client_proof'],delivery_folder,sender_directory=ROOT/'runtime/wecom-messenger',completed_at=intent['completed_at']);commits=intent['commits'];need(len(values)==len(commits),'delivery-completion-target-count')
    for index,(value,commit)in enumerate(zip(values,commits)):
        need(commit['workflow']==value['workflow']and commit['target']==value['target']and raw(commit['before_archive'])==raw(value['before_archive'])and commit['before_archive']['path']==str(folder/('before-%04d.json'%index))and commit['after']['path']==str(folder/('after-%04d.json'%index))and raw(commit['after'])==encode(value['after']),'delivery-completion-transform-changed')
        receipt=doc(ref(folder/('commit-%04d.json'%index)));need(receipt=={'kind':'unified-ledger-CAS-v1','intent':intent_ref,'index':index,'before':commit['target'],'after':{'path':commit['target']['path'],'sha256':commit['after']['sha256']}},'delivery-completion-CAS-receipt')
        if current:need(ref(commit['target']['path'])==receipt['after']and Path(commit['target']['path']).stat().st_mode&0o777==commit['mode'],'delivery-completion-current-ledger-drift')
    expected={'kind':'unified-cursor-commit-v1','intent':intent_ref,'batch':intent['batch'],'client_proof':intent['client_proof'],'after':[{'path':c['target']['path'],'sha256':c['after']['sha256']}for c in commits],'completed_at':intent['completed_at']}
    need(result==expected and doc(intent['client_proof'])['batch']==result['batch'],'delivery-completion-result-binding')
    return {'result':result_ref,'request':intent['request'],'task':task,'batch':intent['batch'],'client_proof':intent['client_proof'],'commits':commits,'completed_at':intent['completed_at'],'cursor_committed':True,'client_confirmed':True}

def report_values(result_ref,delivery_folder,*,current=False):
    """Three truthful completion reports; collection parents remain collection-ready.
    The cursor transaction and every client, never parent status booleans, prove
    completion. No legacy completion receipt is manufactured or rewritten.
    """
    facts=completion_facts(result_ref,delivery_folder,current=current);batch=doc(facts['batch']);proof=doc(facts['client_proof']);result=doc(result_ref);reports={}
    need(len(proof['clients'])==len(batch['items']),'delivery-report-all-clients')
    for flow,ready_ref in batch['ready_reports'].items():
        ready=doc(ready_ref);need(ready.get('workflow')==flow and ready.get('collection_ready')is True and ready.get('complete')is False and ready.get('fixture')is not True,'delivery-report-original-ready')
        refs=[ready_ref,facts['batch'],facts['client_proof'],result_ref,*proof['clients'],*[c['before_archive']for c in facts['commits']],*[c['after']for c in facts['commits']]]
        for reference in refs:raw(reference)
        reports[flow]={'kind':'staged-unified-director-completion-v1','collection_contract':delivery.CONTRACT,'workflow':flow,'day':ready['day'],'dispatch_id':ready['dispatch_id'],'live':True,'fixture':False,'complete':True,'delivery_complete':True,'cursor_advanced':True,'test_target':delivery.delivery_targets.target(flow),'production_sent':False,'complaint_submitted':False,'completed_at':facts['completed_at'],'collection_report':ready_ref,'collection_parent_status':'collection-ready','source_client_proof':{'kind':'three-flow-delivery-source-client-proof-v1','batch':facts['batch'],'all_clients':facts['client_proof'],'cursor_commit':result_ref},'evidence':refs}
    need(set(reports)=={'daily-comment-stats','negative-review-complaints','violation-notifier'}and len({r['day']for r in reports.values()})==1,'delivery-report-exact-three')
    return reports

def seal_reports(result_ref,delivery_folder):
    values=report_values(result_ref,delivery_folder,current=True);base=Path(result_ref['path']).parent/'reports';reports={flow:immutable(base/(flow+'.json'),encode(value))for flow,value in values.items()}
    return immutable(base/'reports.json',encode({'kind':'three-flow-client-completion-reports-v1','cursor_commit':result_ref,'reports':reports}))

def verify_reports(bundle_ref,delivery_folder,*,current=False):
    bundle=doc(bundle_ref);need(set(bundle)=={'kind','cursor_commit','reports'}and bundle['kind']=='three-flow-client-completion-reports-v1'and bundle_ref['path']==str(Path(bundle['cursor_commit']['path']).parent/'reports/reports.json'),'delivery-report-bundle-origin');values=report_values(bundle['cursor_commit'],delivery_folder,current=current)
    need(set(bundle['reports'])==set(values),'delivery-report-bundle-flows')
    for flow,value in values.items():
        report=bundle['reports'][flow];need(report['path']==str(Path(bundle_ref['path']).parent/(flow+'.json'))and doc(report)==value,'delivery-report-not-derived')
    return values

def verify_report_value(value):
    need(value.get('kind')=='staged-unified-director-completion-v1','delivery-report-kind');result_ref=value['source_client_proof']['cursor_commit'];folder=Path(doc(result_ref)['batch']['path']).parent/'items';expected=report_values(result_ref,folder)
    need(value==expected[value['workflow']],'delivery-report-value-not-derived');return value
