"""Bounded durable baseline navigation. Page-two template awaits live review.
No export/download or guessed URL. All observations are immutable local evidence.
"""
import copy,hashlib,json,os,re,time,uuid
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs,urlsplit
import dom_evidence as d
import readonly_tick_snapshot

def need(ok,code):
 if not ok:raise ValueError(code)
def classes(n):return set(n.get('attributes',{}).get('class','').split())
def ns(n):return list(d.nodes({'truncated':False,'root':n}))
def checksum(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(row):return row['text'].split(' ',1)[0],row['generated_at']
def parse(tree):
 nodes=list(d.nodes(tree));u=urlsplit(tree.get('url',''));need(u.scheme=='https' and u.netloc=='life.douyin.com' and re.fullmatch(r'/p/fulfillsettle/export_records/[0-9]+',u.path),'baseline-record-route')
 d.unique([n for n in nodes if n.get('name')=='门店评价' and 'byted-tab-bar-item-active' in classes(n)],'baseline-active-review-tab')
 table=d.unique([n for n in nodes if {'byted-table-container','byted-table-container-row'}<=classes(n)],'baseline-one-table');scope=ns(table)
 body=d.unique([n for n in scope if 'byted-table-body' in classes(n)]);head=d.unique([n for n in scope if 'byted-table-head' in classes(n)])
 need([n.get('name','') for n in ns(head) if 'byted-table-cell-head' in classes(n)]==['报表名称','报表类型','开始生成时间','状态','','操作'],'baseline-six-headers')
 pager=d.unique([n for n in scope if 'byted-pager' in classes(n)]);pn=ns(pager);count=d.unique([n for n in pn if 'byted-pager-record' in classes(n)]);m=re.fullmatch(r'共\s*([0-9]+)\s*条记录',count.get('name',''));need(m,'baseline-total');total=int(m[1]);need(0<=total<=30,'baseline-retention-bound')
 group=d.unique([n for n in pager.get('children',[]) if 'byted-pager-item-group' in classes(n)]);items=group.get('children',[]);pages=max(1,(total+9)//10)
 need(len(items)==pages+2 and all(n.get('tag')=='li' and 'byted-pager-item' in classes(n) for n in items),'baseline-pager-shape')
 numeric=items[1:-1];need([n.get('name') for n in numeric]==[str(i) for i in range(1,pages+1)],'baseline-contiguous-pages')
 selected=d.unique([n for n in numeric if 'byted-pager-item-checked' in classes(n)]);page=int(selected['name'])
 for node,side,disabled in ((items[0],'left',page==1),(items[-1],'right',page==pages)):
  need(node.get('name','')=='' and any('byted-icon-'+side in classes(n) for n in ns(node)) and ('byted-pager-item-disabled' in classes(node))==disabled,'baseline-pager-arrow-state')
 rownodes=body.get('children',[]);rows=d.records({'truncated':False,'root':body});need(len(rows)==len(rownodes)==min(10,max(0,total-10*(page-1))) and len(d.records(tree))==len(rows),'baseline-page-size-or-foreign-rows')
 for n,row in zip(rownodes,rows):
  need(n.get('tag')=='div' and {'byted-table-column','byted-table-row'}<=classes(n),'baseline-row-shape');v=d.unique(n.get('children',[]));need('byted-table-column-visible' in classes(v),'baseline-visible-wrapper');s=d.unique(v.get('children',[]));need('byted-table-column-scroller' in classes(s),'baseline-scroller-wrapper');cells=s.get('children',[])
  need(len(cells)==6 and all('byted-table-cell-body' in classes(c) for c in cells),'baseline-six-cells');need(re.fullmatch(r'门店评价_全部门店_\d{4}_\d{2}_\d{2}-\d{4}_\d{2}_\d{2}',cells[0].get('name','')) and cells[1].get('name')=='门店评价' and cells[2].get('name')==row['generated_at'] and n.get('name')==' '.join(c.get('name','') for c in cells if c.get('name','')),'baseline-row-values');datetime.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S')
 ids=[identity(r) for r in rows];need(len(set(ids))==len(ids) and [i[1] for i in ids]==sorted([i[1] for i in ids],reverse=True),'baseline-page-order-or-duplicates')
 need(all(isinstance(n.get('selector'),str) and bool(n['selector']) for n in (table,pager,items[-1],numeric[0])),'baseline-observed-selector-required')
 return dict(schema='export-baseline-page-v1',total=total,page=page,pages=pages,rows=rows,table=table['selector'],pager=pager['selector'],next=items[-1]['selector'],first=numeric[0]['selector'])
def combine(pages):
 need(bool(pages),'baseline-pages-empty');first=pages[0];need(len(pages)==first['pages'],'baseline-missing-pages')
 for i,p in enumerate(pages):need(p['page']==i+1 and all(p[k]==first[k] for k in ('total','pages','table','pager')),'baseline-page-scope-or-sequence')
 rows=[r for p in pages for r in p['rows']];ids=[identity(r) for r in rows]
 need(len(rows)==first['total'] and len(set(ids))==len(ids) and [i[1] for i in ids]==sorted([i[1] for i in ids],reverse=True),'baseline-complete-order-or-duplicate');return rows


def is_initial_loading(tree):
 """Recognize the observed mounted record microapp + empty root + shell progress.
 Never ready/zero; unrelated blank pages and unknown tab types remain rejected.
 """
 nodes=list(d.nodes(tree));root=tree.get('root',{})
 if tree.get('url')!='https://life.douyin.com/p/fulfillsettle/export_records/20101' or len(nodes)!=32 or root.get('tag')!='body' or root.get('name')!='' or root.get('attributes')!={'class':'core-new-layout'}:return False
 if any(n.get('tag')not in('body','div','section','main','aside') or n.get('role')not in('generic','region','main','complementary')or n.get('name','')not in('','scrollable content')for n in nodes):return False
 def one_id(identifier):
  matches=[n for n in nodes if n.get('attributes',{}).get('id')==identifier]
  return matches[0]if len(matches)==1 else None
 content=one_id('root');sub=one_id('submodule');skeleton=one_id('skeleton-container')
 if content is None or sub is None or skeleton is None or content.get('selector')!='#root' or content.get('attributes')!={'id':'root','class':'fulfillsettle-body'}:return False
 kids=content.get('children',[])
 if len(kids)!=1 or kids[0].get('attributes')!={'class':'fulfillsettle_scope'}or kids[0].get('children')!=[]:return False
 apps=sub.get('children',[])
 if len(apps)!=1 or not re.fullmatch(r'garfish_app_for_merchant_fulfillsettle_pc_[A-Za-z0-9_]+',apps[0].get('attributes',{}).get('id',''))or not any(n is content for n in ns(apps[0])):return False
 node=skeleton
 for index,label in enumerate(('HomeSkeleton','life-core-progress life-core-progress-shape-line life-core-progress-size-xs','life-core-progress-wrap','life-core-progress-outer','life-core-progress-inner','life-core-progress-bg')):
  kids=node.get('children',[])
  if len(kids)!=1:return False
  node=kids[0];attributes=node.get('attributes',{})
  if node.get('tag')!='div'or node.get('name')!=''or set(attributes)!={'class'}:return False
  if index==0:
   if not re.fullmatch(r'src-components-HomeSkeleton-index-module__home-skeleton-container--[A-Za-z0-9_-]+',attributes['class']):return False
  elif attributes['class']!=label:return False
 return node.get('children')==[]

# A freshly opened record tab rebuilds its frame while the first read arrives;
# Chrome answers "Frame with ID 0 was removed." instead of a snapshot. The
# whitelist is the same transport family Workflow.call already retries, so the
# two judgements cannot drift apart; a closed tab, a denied site or a changed
# route is not in it and stays fatal on the first reply.
FRAME_TRANSIENT=re.compile(r'(?:Could not establish connection\. Receiving end does not exist\.|Frame with [Ii][Dd] \d+ was removed\.?|No frame with [Ii][Dd] \d+ in tab \d+\.?|Frame has been detached\.?)')
FRAME_RETRY_LIMIT=3
FRAME_RETRY_BUDGET=600.0

def observe(w,window_id):
 s=w.s;directory=w.file.parent/'bridge-evidence';directory.mkdir(exist_ok=True);command={'op':'readonly-scope','tabId':s['record_tab_id'],'windowId':window_id};deadline=time.monotonic()+FRAME_RETRY_BUDGET;reply=None
 for attempt in range(FRAME_RETRY_LIMIT):
  if attempt:
   delay=.25*(2**(attempt-1));need(time.monotonic()+delay<=deadline,'baseline-frame-retry-budget-exhausted');time.sleep(delay)
  reply=w.invoke(command);token=uuid.uuid4().hex;replypath=directory/('baseline-'+token+'-reply.json')
  with replypath.open('x')as out:json.dump(reply,out,ensure_ascii=False);out.flush();os.fsync(out.fileno())
  s.setdefault('baseline_transport_observations',[]).append({'command':command,'reply':{'path':str(replypath),'sha256':checksum(replypath)}})
  if attempt:s['baseline_frame_transient_retries']=s.get('baseline_frame_transient_retries',0)+1
  w.save()
  if type(reply)is dict and reply.get('ok')is True:break
  error=str(reply.get('error',''))if type(reply)is dict else ''
  need(attempt<FRAME_RETRY_LIMIT-1 and bool(FRAME_TRANSIENT.fullmatch(error)),'baseline-readonly-transport-unverified')
 need(type(reply)is dict and reply.get('ok')is True,'baseline-readonly-transport-unverified');snapshot=reply.get('result');need(type(snapshot)is dict and type(snapshot.get('tree'))is dict,'readonly-scope-envelope-invalid')
 t=snapshot['tree'];path=directory/('baseline-'+token+'.json');scopepath=directory/('baseline-'+token+'-scope.json')
 for p,value in ((path,t),(scopepath,snapshot)):
  with p.open('x')as out:json.dump(value,out,ensure_ascii=False);out.flush();os.fsync(out.fileno())
 reference=dict(path=str(path),sha256=checksum(path));scope_ref=dict(path=str(scopepath),sha256=checksum(scopepath));s.setdefault('baseline_read_observations',[]).append(reference);s.setdefault('baseline_read_scopes',[]).append({'tree':reference,'scope':scope_ref});w.save()
 readonly_tick_snapshot.decode(snapshot,s['record_tab_id'],window_id);before=d.context(snapshot['before'],s['record_tab_id'],w.job['groupid'],record=True);after=d.context(snapshot['after'],s['record_tab_id'],w.job['groupid'],record=True);keys=('tabId','windowId','url','groupid')
 need(type(after.get('windowId'))is int and type(after.get('tabId'))is int,'baseline-explicit-tab-window-required');need(all(before.get(k)==after.get(k)for k in keys),'baseline-tab-context-changed');need(t.get('url')==urlsplit(after['url'])._replace(query='',fragment='').geturl(),'baseline-tree-route')
 binding={k:after[k]for k in keys};binding.update(fingerprint=s['fingerprint'],date_range=s['date_range']);return t,reference,binding

def _calls_safe(w):
 if not w.s.get('company_search_explicit_recovery'):return all(c.get('state')=='confirmed'for c in w.s.get('calls',[]))
 validator=getattr(w,'calls_progression_safe',None);need(callable(validator),'baseline-typed-progression-required');return validator()

def settle_initial(w,t,reference,binding,window_id,state):
 s=w.s;calls=copy.deepcopy(s['calls']);loading=s.get('baseline_initial_loading')
 if loading is None and not is_initial_loading(t):return t,reference
 if loading is None:loading={'schema':'export-baseline-initial-loading-v1','binding':binding,'observations':[],'ready':False};s['baseline_initial_loading']=loading
 need(loading['schema']=='export-baseline-initial-loading-v1'and loading['binding']==binding and not state['pages']and state['pending']is None,'baseline-initial-loading-state')
 for old in loading['observations']:need(checksum(old['path'])==old['sha256'],'baseline-initial-loading-evidence-changed')
 while True:
  need(len(loading['observations'])<2000,'baseline-initial-loading-exhausted-readonly');loading['observations'].append(reference);w.save()
  if not is_initial_loading(t):loading['ready']=True;loading['ready_tree']=reference;w.save();return t,reference
  need(len(loading['observations'])<2000,'baseline-initial-loading-exhausted-readonly');time.sleep(min(.25*2**(len(loading['observations'])-1),2.0));need(s['calls']==calls and _calls_safe(w),'baseline-initial-loading-calls-changed');t,reference,current=observe(w,window_id);need(current==binding,'baseline-initial-loading-scope-changed')

def advance(w):
 """Called only after fresh source date/store verification, under workflow lock."""
 s=w.s;need(not s.get('exportPending') and not s.get('downloadPending') and not s.get('submitted_at'),'baseline-before-export-only')
 need(_calls_safe(w),'baseline-unknown-intent-hold')
 # A saved window is only a routing hint; both scope tab lists are fresh.
 loading=s.get('baseline_initial_loading');need(not loading or loading.get('ready')is True or len(loading.get('observations',[]))<2000,'baseline-initial-loading-exhausted-readonly')
 binding=s.get('baseline_pagination',{}).get('binding',{})
 window_id=binding.get('windowId')
 if window_id is None:
  discovery=d.context(w.call({'op':'tabs'}),s['record_tab_id'],w.job['groupid'],record=True)
  window_id=discovery.get('windowId')
 need(type(window_id) is int,'baseline-explicit-tab-window-required')
 t,ref,binding=observe(w,window_id)
 state=s.setdefault('baseline_pagination',dict(schema='export-baseline-collection-v1',binding=binding,pages=[],pending=None));need(state['binding']==binding,'baseline-binding-conflict')
 if not state['pages']and state['pending']is None and not s.get('baseline_records'):
  t,ref=settle_initial(w,t,ref,binding,window_id,state)
 old=[]
 for entry in state['pages']:
  need(checksum(entry['observation']['path'])==entry['observation']['sha256'],'baseline-observation-changed');p=parse(json.loads(Path(entry['observation']['path']).read_text()));need(p==entry['page'],'baseline-page-evidence-conflict');old.append(p)
 page=parse(t);pending=state.get('pending')
 if pending:
  call=d.unique([c for c in s['calls'] if c['key']==pending['key']]);need(call['state']=='confirmed' and call['command']==pending['command'],'baseline-pager-unknown-or-conflict')
  if page['page']!=pending['target']:
   need(page['page']==pending['source'],'baseline-unexpected-current-page');state['settle_reads']=state.get('settle_reads',0)+1;need(state['settle_reads']<=2000,'baseline-pager-settle-exhausted');s['waiting_for']='baseline-confirmed-pager-awaiting-readonly-settle';w.save();return False
  state['pending']=None;state['settle_reads']=0;s.pop('waiting_for',None)
  if pending['target']==1:
   need(old and page==old[0],'baseline-return-first-page-changed');s['baseline_records']=combine(old);s['baseline_record_observation']=ref;s['baseline_complete_proof']=dict(schema='export-baseline-complete-v1',pages=state['pages'],returned_first=ref,total=len(s['baseline_records']),all_pages_read=True);s['record_url']=binding['url'];w.save();return True
 need(page['page']==len(old)+1,'baseline-page-not-next');state['pages'].append(dict(page=page,observation=ref));old.append(page)
 if page['page']==page['pages']:
  rows=combine(old)
  if page['page']==1:
   s['baseline_records']=rows;s['baseline_record_observation']=ref;s['record_url']=binding['url'];s['baseline_complete_proof']=dict(schema='export-baseline-complete-v1',pages=state['pages'],returned_first=ref,total=len(rows),all_pages_read=True);w.save();return True
  target=1;selector=page['first']
 else:target=page['page']+1;selector=page['next']
 command=dict(op='click',tabId=s['record_tab_id'],kind='navigation',locator=dict(by='selector',value=selector));key='baseline-page:'+str(page['page'])+'->'+str(target)
 state['pending']=dict(key=key,command=command,source=page['page'],target=target);w.save();w.once(command,intent_key=key);return False

INITIAL_RECOVERY_KIND='verified-preexport-baseline-initial-skeleton-recovery-v1'
def _pinned(reference):
 p=Path(reference['path']);need(p.is_absolute()and p.resolve()==p and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'baseline-recovery-canonical-ref');need(checksum(p)==reference['sha256'],'baseline-recovery-pin');return json.loads(p.read_bytes())
def record_url_initialization(previous,current):
 if previous==current:return True
 before,after=urlsplit(previous),urlsplit(current);old=parse_qs(before.query,keep_blank_values=True);new=parse_qs(after.query,keep_blank_values=True)
 return (before.scheme==after.scheme=='https'and before.netloc==after.netloc=='life.douyin.com'and before.path==after.path=='/p/fulfillsettle/export_records/20101'and not before.fragment and not after.fragment and set(old)=={'groupid'}and len(old['groupid'])==1 and old['groupid'][0].isdigit()and new=={**old,'life_biz_view_id':['22'],'life_account_biz_ids':['']})
def plan_initial_loading_recovery(job_ref,original_ref,source_scope_ref):
 job=_pinned(job_ref);s=_pinned(original_ref);need(job['work_order_path']==job_ref['path']and job['workflow_path']==original_ref['path']and s['work_order_id']==job['work_order_id']and s['company']==job['company']and str(s['groupid'])==str(job['groupid'])and s['date_range']=={k:job['date_range'][k]for k in('start','end')},'baseline-recovery-original-job')
 need(s['state']=='running'and s['phase']=='recordsProfileRequired'and s['last_error']['code']==s['last_error']['message']=='baseline-active-review-tab'and all(c['state']=='confirmed'for c in s['calls'])and not any(s.get(k)for k in('exportPending','downloadPending','submitted_at','baseline_records','result','baseline_initial_loading','baseline_initial_loading_recovery')),'baseline-recovery-preexport-only')
 last=s['calls'][-1];command=last['command'];clicked=last['result']['clicked'];need(last['phase']=='openRecordMenu'and command['op']=='click'and command['kind']==last['result']['kind']=='export'and command['tabId']==s['tab_id']and command['locator']=={'by':'selector','value':clicked['selector']}and clicked['name']=='评价导出记录'and last['result']['version']==d.VERSION,'baseline-recovery-original-confirmed-open')
 directory=Path(original_ref['path']).parent/'bridge-evidence';need(Path(source_scope_ref['path']).parent==directory and re.fullmatch(str(s['revision']).zfill(4)+r'-recordsProfileRequired-scope-[a-f0-9]{32}\.json',Path(source_scope_ref['path']).name),'baseline-recovery-source-companion');value=_pinned(source_scope_ref);readonly_tick_snapshot.decode(value,s['tab_id'],s['baseline_pagination']['binding']['windowId']);source=d.context(value['before'],s['tab_id'],job['groupid']);after=d.context(value['after'],s['tab_id'],job['groupid']);need(source==after and value['tree']==_pinned(s['last_tree']),'baseline-recovery-source-context');d.identity(value['tree'],job['identity_baseline']);d.all_store_scope(value['tree']);need(d.verified_review_filter(value['tree'],s['date_range'])['page_filtered']==s['page_filtered'],'baseline-recovery-source-filter')
 binding=s['baseline_pagination']['binding'];need(s['baseline_pagination']['pages']==[]and s['baseline_pagination']['pending']is None and binding['fingerprint']==s['fingerprint']and binding['date_range']==s['date_range']and binding['tabId']==s['record_tab_id']and binding['groupid']==str(job['groupid']),'baseline-recovery-empty-pagination')
 for side in('before','after'):
  record=d.context(value[side],s['record_tab_id'],job['groupid'],record=True);need(all(record[k]==binding[k]for k in('tabId','windowId','groupid'))and record_url_initialization(record['url'],binding['url']),'baseline-recovery-record-routing')
 observations=s.get('baseline_read_observations');need(type(observations)is list and len(observations)==1,'baseline-recovery-one-consumed');tree_ref=observations[0];need(Path(tree_ref['path']).parent==directory and re.fullmatch(r'baseline-[a-f0-9]{32}\.json',Path(tree_ref['path']).name)and is_initial_loading(_pinned(tree_ref)),'baseline-recovery-original-skeleton')
 return {'kind':INITIAL_RECOVERY_KIND,'job':job_ref,'original':original_ref,'source_scope':source_scope_ref,'record_tree':tree_ref,'binding':copy.deepcopy(binding),'original_calls':copy.deepcopy(s['calls']),'observations_consumed':1,'max_total_observations':3,'remaining_observations':2,'UI_used':False,'new_inputs':0}
def initial_loading_transform(original,plan,proof_ref):
 need(plan['kind']==INITIAL_RECOVERY_KIND and original['calls']==plan['original_calls']and original['last_error']['code']=='baseline-active-review-tab'and 'baseline_initial_loading'not in original and 'baseline_initial_loading_recovery'not in original,'baseline-recovery-transform-frontier');new=copy.deepcopy(original);new.pop('last_error');new['baseline_initial_loading']={'schema':'export-baseline-initial-loading-v1','binding':copy.deepcopy(plan['binding']),'observations':[copy.deepcopy(plan['record_tree'])],'ready':False};new['baseline_initial_loading_recovery']=copy.deepcopy(proof_ref);return new
