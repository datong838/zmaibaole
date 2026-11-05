"""Fresh staged same-round lease selection; never releases ownership to unrelated work."""
FLOWS=('daily-comment-stats','negative-review-complaints','violation-notifier')
CONTRACT='three-flow-collection-ready-v1'
def need(ok,error):
 if not ok:raise ValueError(error)
def next_collection_task(original,tasks):
 need(original['state']=='collection-ready'and original['payload'].get('collection_contract')==CONTRACT,'staged-original-ready-task')
 index=FLOWS.index(original['flow']);same=[t for t in tasks if t['plan_id']==original['plan_id']and t['day']==original['day']]
 need(len(same)==3 and {t['flow']for t in same}==set(FLOWS)and all(t['payload'].get('collection_contract')==CONTRACT for t in same),'staged-exact-three-original-tasks')
 need(all(t['state']=='collection-ready'for t in same if FLOWS.index(t['flow'])<=index),'staged-prior-ready-required')
 if index==2:return None # retain third original owner; batch delivery is separate.
 target=next(t for t in same if t['flow']==FLOWS[index+1]);need(target['state']=='queued'and target['attempt']==0 and not target.get('active_attempt')and not target.get('context'),'staged-successor-fresh-only');return target

def delivery_context(original,tasks):
 """Pin the three harvested natural exits before reusing the final task key.
 This is queue staging only; the worker still deep-validates every ready report.
 """
 import copy
 from pathlib import Path
 from .common import ref,pinned
 need(original['flow']==FLOWS[-1]and next_collection_task(original,tasks)is None,'staged-final-original-task')
 need(original['context'].get('stage')!='unified-delivery','staged-no-restage-delivery')
 packets=[]
 for flow in FLOWS:
  task=next(t for t in tasks if t['plan_id']==original['plan_id']and t['day']==original['day']and t['flow']==flow)
  context=task['context'];folder=Path(task['active_attempt']);need(folder.is_absolute()and str(folder.resolve())==str(folder)and folder.name==task['id']+'-'+str(task['attempt']),'staged-original-attempt-path')
  exit_ref=ref(folder/'exit.json');ended=pinned(exit_ref);response=pinned(ended['response']);request=pinned(ended['request'])
  need(ended.get('returncode')==0 and ended.get('attempt_id')==folder.name and request.get('attempt_id')==folder.name and response.get('attempt_id')==folder.name and response.get('task_id')==task['id']and response.get('outcome')=='collection-ready','staged-natural-ready-exit')
  need(request['task']['id']==task['id']and all(request['task'][k]==task[k]for k in('plan_id','day','flow','outer'))and context.get('collection_ready_attempt')==str(folder)and context.get('collection_ready_receipt')==response.get('collection_ready')and response.get('collection_ready'),'staged-harvested-ready-context')
  expected={**response['context'],'collection_ready_receipt':response['collection_ready'],'collection_ready_attempt':str(folder)}
  need(context==expected,'staged-ready-context-drift')
  packets.append({'id':task['id'],'flow':flow,'attempt_path':str(folder),'exit':exit_ref,'context':copy.deepcopy(context),'outer':copy.deepcopy(task['outer'])})
 return {**copy.deepcopy(original['context']),'stage':'unified-delivery','delivery_ready_tasks':packets}
