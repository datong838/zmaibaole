"""Pure functions over reviewed, visible DOM trees; no browser or site requests."""
import re
from urllib.parse import urlsplit, parse_qs

VERSION='dom-only-20261103-12'

def nodes(tree):
    if tree.get('truncated') is not False or not isinstance(tree.get('root'),dict):
        raise ValueError('complete-untruncated-tree-required')
    stack=[tree['root']]
    while stack:
        n=stack.pop(); yield n
        stack.extend(reversed(n.get('children',[])))

def leaves(tree):
    return [n for n in nodes(tree) if not n.get('children') and n.get('name')]

def unique(items,code='semantic-locator-not-unique'):
    if len(items)!=1: raise ValueError(code)
    return items[0]

def context(tabs,tab_id,group_id=None,record=False):
    tab=unique([t for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==tab_id],'explicit-tab-not-unique')
    u=urlsplit(tab.get('url',''))
    if not tab.get('allowed') or u.scheme!='https' or u.netloc!='life.douyin.com':raise ValueError('tab-origin-unverified')
    groups=parse_qs(u.query).get('groupid',[])
    if len(groups)!=1 or (group_id is not None and groups!=[str(group_id)]):raise ValueError('source-company-mismatch')
    if record and '/export_records/' not in u.path:raise ValueError('record-context-unverified')
    return dict(tab,groupid=groups[0])

def identity(tree,baseline=None):
    cards=[n for n in nodes(tree) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
    if any(len(n.get('name',''))>=800 for n in (cards if cards else leaves(tree))):raise ValueError('identity-text-may-be-truncated')
    text=unique(cards,'identity-card-unverified')['name'] if cards else '\n'.join(n['name'] for n in leaves(tree))
    provider=unique(sorted(set(re.findall(r'服务商\d+',text))),'identity-provider-unverified')
    account=unique(sorted(set(re.findall(r'账户ID\s*[：:]?\s*(\d{8,})',text))),'identity-account-unverified')
    manager=unique(sorted(set(re.findall(r'我的客户经理\s*[：:]?\s*([^\n]+?)(?=\s*(?:切换公司|退出登录)|$)',text))),'identity-manager-unverified').strip()
    result={'provider':provider,'account_id':account,'manager':manager}
    if baseline and result!=baseline:raise ValueError('account-changed')
    return result

def exact(tree,name,role=None):
    candidates=[n for n in nodes(tree) if n.get('name')==name and (role is None or n.get('role')==role)]
    # Same-name ancestors do not create separate semantic targets. Match bridge.find.
    candidates=[n for n in candidates if not any(c.get('name')==name for c in n.get('children',[]))]
    target=unique(candidates)
    if target.get('disabled') or not target.get('selector'):raise ValueError('element-not-ready')
    return target

def all_reviews(tree):
    names=sorted(set(n['name'] for n in leaves(tree) if re.fullmatch(r'全部评价\s+\d+',n['name'])))
    return exact(tree,unique(names,'all-reviews-unverified'))

def company_switch(tree):
    account=identity(tree)
    card=unique([n for n in nodes(tree) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')],'identity-card-unverified')
    scope={'truncated':False,'root':card}
    old=[n for n in nodes(scope) if n.get('role')=='button' and n.get('name')=='切换公司']
    if old:return exact(scope,'切换公司','button')
    switch=unique([n for n in nodes(scope) if 'SwitchCard-index-module__switch-card--' in n.get('attributes',{}).get('class','') and n.get('name')=='商户 '+account['provider']+' 切换'],'merchant-switch-card-unverified')
    button=exact({'truncated':False,'root':switch},'切换','button')
    if 'SwitchCard-index-module__switch-card-button--' not in button.get('attributes',{}).get('class',''):raise ValueError('merchant-switch-button-unverified')
    return button

def calendar_day(tree,iso):
    year,month,day=map(int,iso.split('-')); month_label=f'{year}年{month}月'
    found=[]
    def visit(n,ancestors):
        if n.get('name')==str(day) and not any(c.get('name')==str(day) for c in n.get('children',[])):
            date_col=next((p for p in reversed(ancestors+[n]) if {'byted-date-col','byted-date-date'}<=set(p.get('attributes',{}).get('class','').split())),None)
            if date_col:
                for p in reversed(ancestors):
                    months=re.findall(r'\d{4}年\d{1,2}月',p.get('name',''))
                    if months:
                        if months==[month_label] and not ({'byted-date-grid-prev','byted-date-grid-next'}&(set(date_col.get('attributes',{}).get('class','').split())|set(n.get('attributes',{}).get('class','').split()))) and not date_col.get('disabled') and 'disabled' not in date_col.get('attributes',{}).get('class',''): found.append(n)
                        break
        for c in n.get('children',[]):visit(c,ancestors+[n])
    list(nodes(tree)) # validate completeness first
    visit(tree['root'],[])
    return unique(found,'calendar-day-or-month-unverified')

def records(tree):
    result=[]
    for n in nodes(tree):
        classes=n.get('attributes',{}).get('class','').split()
        if 'byted-table-row' not in classes:continue
        text=n.get('name','')
        stamp=re.findall(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',text)
        if len(stamp)!=1:raise ValueError('record-timestamp-unverified')
        result.append({'text':text,'generated_at':stamp[0],'state':'success' if '生成成功' in text else 'failed' if re.search('生成失败|导出失败',text) else 'pending','selector':n['selector']})
    return result

def review_filter_fields(tree):
    out={}
    for label in ('评价时间','评价类型','评价来源','评价状态'):
        out[label]=unique([n for n in nodes(tree) if n.get('role')=='textbox' and n.get('name')==label],'review-filter-unverified:'+label)
    return out

def verified_review_filter(tree,date_range):
    fields=review_filter_fields(tree)
    expected=date_range['start']+' ~ '+date_range['end']
    if fields['评价时间'].get('attributes',{}).get('value')!=expected:raise ValueError('filter-date-unverified')
    for label in ('评价类型','评价来源','评价状态'):
        if fields[label].get('attributes',{}).get('value')!='全部':raise ValueError('nondefault-review-filter:'+label)
    counts=set()
    for n in nodes(tree):
        m=re.fullmatch(r'(?:评价\s*)?已筛选\s*(\d+)\s*条',n.get('name',''))
        if m:counts.add(int(m[1]))
    return {'date_range':date_range,'page_filtered':unique(sorted(counts),'page-count-unverified')}

def record_tabs(tabs,group_id):
    out=[]
    for window in tabs:
        for tab in window.get('tabs',[]):
            u=urlsplit(tab.get('url',''))
            if tab.get('allowed') and u.scheme=='https' and u.netloc=='life.douyin.com' and '/export_records/' in u.path and parse_qs(u.query).get('groupid')==[str(group_id)]:out.append(tab)
    return out

def export_tag(date_range):return '门店评价_全部门店_'+date_range['start'].replace('-','_')+'-'+date_range['end'].replace('-','_')

def generated_record(tree,date_range,baseline):
    tag=export_tag(date_range)
    candidates=[]
    for row in records(tree):
        if tag not in row['text']:continue
        # Use the date-name and exact timestamp as identity, independent of status text.
        if any(tag in old['text'] and old['generated_at']==row['generated_at'] for old in baseline):continue
        candidates.append(row)
    if len(candidates)>1:raise ValueError('generated-record-ambiguous')
    return candidates[0] if candidates else None


def all_store_scope(tree):
    scope=unique([n for n in nodes(tree) if n.get('attributes',{}).get('id')=='CommentPoi_select'],'store-scope-unverified')
    if scope.get('name')!='按省市 全部门店':raise ValueError('nondefault-store-scope')
    return True

def export_range_input(tree):
    return unique([n for n in nodes(tree) if n.get('role')=='textbox' and n.get('placeholder')=='请选择日期范围，不选则为近一年'],'export-range-input-unverified')


def complete_record_list(tree):
    unique([n for n in nodes(tree) if n.get('name')=='门店评价' and 'byted-tab-bar-item-active' in n.get('attributes',{}).get('class','').split()],'record-type-not-active')
    counts=[]
    for n in nodes(tree):
        if 'byted-pager-record' in n.get('attributes',{}).get('class','').split():
            match=re.fullmatch(r'共\s*(\d+)\s*条记录',n.get('name',''))
            if not match:raise ValueError('record-pager-unverified')
            counts.append(int(match[1]))
    total=unique(counts,'record-pager-not-unique');rows=records(tree)
    if total!=len(rows):raise ValueError('record-pagination-incomplete')
    return rows


def submitted_export_record(tree,date_range,baseline,submitted_at):
    """Reviewed first page after one submission. Never claims full-list coverage.

    Baseline collection still uses complete_record_list. Only ten-row page-one
    overflow is supported here; hidden pages cannot establish a new baseline.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    def need(ok,code):
        if not ok:raise ValueError(code)
    def classes(n):return set(n.get('attributes',{}).get('class','').split())
    ns=list(nodes(tree));u=urlsplit(tree.get('url',''));need(u.scheme=='https' and u.netloc=='life.douyin.com' and re.fullmatch(r'/p/fulfillsettle/export_records/[0-9]+',u.path) is not None,'record-page-route-unverified')
    unique([n for n in ns if n.get('name')=='门店评价' and 'byted-tab-bar-item-active' in classes(n)],'record-type-not-active')
    table=unique([n for n in ns if {'byted-table-container','byted-table-container-row'}<=classes(n)],'record-page-table-not-unique');scope={'truncated':False,'root':table};scoped=list(nodes(scope))
    body=unique([n for n in scoped if 'byted-table-body' in classes(n)],'record-page-body-not-unique');head=unique([n for n in scoped if 'byted-table-head' in classes(n)],'record-page-head-not-unique')
    heads=[n.get('name','') for n in nodes({'truncated':False,'root':head}) if 'byted-table-cell-head' in classes(n)];need(heads==['报表名称','报表类型','开始生成时间','状态','','操作'],'record-page-headers-unreviewed')
    pager=unique([n for n in scoped if 'byted-pager' in classes(n)],'record-page-pager-not-unique');pns=list(nodes({'truncated':False,'root':pager}));count=unique([n for n in pns if 'byted-pager-record' in classes(n)],'record-pager-not-unique');m=re.fullmatch(r'共\s*([0-9]+)\s*条记录',count.get('name',''));need(m is not None,'record-pager-unverified');total=int(m.group(1))
    items=[n for n in pns if n.get('tag')=='li' and 'byted-pager-item' in classes(n)];selected=unique([n for n in items if 'byted-pager-item-checked' in classes(n)],'record-page-selected-not-unique');need(selected.get('name')=='1','record-page-not-first')
    numbers=[int(n['name']) for n in items if re.fullmatch(r'[1-9][0-9]*',n.get('name',''))];need(numbers==list(range(1,max(1,(total+9)//10)+1)),'record-page-count-size-unverified')
    arrows=[n for n in items if not re.fullmatch(r'[1-9][0-9]*',n.get('name',''))];need(len(arrows)==2 and 'byted-pager-item-disabled' in classes(arrows[0]) and any('byted-icon-left' in classes(n) for n in nodes({'truncated':False,'root':arrows[0]})) and any('byted-icon-right' in classes(n) for n in nodes({'truncated':False,'root':arrows[1]})),'record-page-navigation-unverified')
    need(('byted-pager-item-disabled' in classes(arrows[1]))==(total<=10),'record-page-next-state-conflict')
    rownodes=body.get('children',[]);need(all(n.get('tag')=='div' and {'byted-table-column','byted-table-row'}<=classes(n) for n in rownodes),'record-page-direct-rows-unreviewed')
    rows=records({'truncated':False,'root':body});need(len(rows)==len(rownodes)==min(total,10),'record-page-size-incomplete');need(len(records(tree))==len(rows),'record-page-foreign-rows')
    filenames=[]
    for node,row in zip(rownodes,rows):
        visible=unique(node.get('children',[]),'record-row-visible-not-unique');need('byted-table-column-visible' in classes(visible),'record-row-visible-unreviewed');scroll=unique(visible.get('children',[]),'record-row-scroller-not-unique');need('byted-table-column-scroller' in classes(scroll),'record-row-scroller-unreviewed');cells=scroll.get('children',[])
        need(len(cells)==6 and all('byted-table-cell-body' in classes(n) for n in cells),'record-row-six-fields-required');name=cells[0].get('name','');need(re.fullmatch(r'门店评价_全部门店_[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{4}_[0-9]{2}_[0-9]{2}',name) is not None and cells[1].get('name')=='门店评价' and cells[2].get('name')==row['generated_at'],'record-row-name-type-time-unverified')
        need(node.get('name')==' '.join(n.get('name','') for n in cells if n.get('name','')),'record-row-summary-fields-conflict');filenames.append(name)
    def row_id(row):
        name=row.get('text','').split(' ',1)[0];need(re.fullmatch(r'门店评价_全部门店_[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{4}_[0-9]{2}_[0-9]{2}',name) is not None,'record-baseline-name-unverified');datetime.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S');return name,row['generated_at']
    need(isinstance(baseline,list),'record-complete-baseline-required');old=[row_id(r) for r in baseline];ids=[row_id(r) for r in rows];need(len(set(old))==len(old) and len(set(ids))==len(ids),'record-identity-duplicate')
    if len([i for i in ids if i[0]==export_tag(date_range) and i not in old])>1:raise ValueError('generated-record-ambiguous')
    need([x[1] for x in old]==sorted([x[1] for x in old],reverse=True) and [x[1] for x in ids]==sorted([x[1] for x in ids],reverse=True),'record-newest-first-order-unverified')
    need(total in (len(old),len(old)+1),'record-total-not-one-submission');new=[i for i in ids if i not in old];need(len(new)<=1 and total==len(old)+len(new),'record-unexpected-new-records')
    need([i for i in ids if i in old]==old[:len(ids)-len(new)],'record-baseline-prefix-changed')
    candidates=[row for row,name,ident in zip(rows,filenames,ids) if name==export_tag(date_range) and ident not in old]
    need(len(candidates)<=1,'generated-record-ambiguous');row=candidates[0] if candidates else None
    if row:
        need(row['generated_at'] not in [item[1] for item in old],'record-new-target-timestamp-already-in-baseline')
        need(ids[0]==row_id(row),'record-new-target-not-first');start=datetime.fromisoformat(submitted_at);need(start.utcoffset() is not None,'export-intent-timezone-required');generated=datetime.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Shanghai'));need(generated>=start.astimezone(ZoneInfo('Asia/Shanghai')).replace(microsecond=0),'generated-record-predates-export-intent')
    return {'row':row,'page':{'schema':'submitted-export-first-page-v1','table_selector':table['selector'],'body_selector':body['selector'],'pager_selector':pager['selector'],'total':total,'page':1,'page_size':10,'page_size_basis':'reviewed-ten-row-first-page-template','visible_rows':len(rows),'all_pages_read':total==len(rows),'baseline_complete_count':len(old),'target_scope':'unique-new-exact-filename-and-timestamp-on-first-page'}}


def verified_export_dialog(tree,date_range,require_dates=True):
    modal=unique([n for n in nodes(tree) if 'byted-modal' in n.get('attributes',{}).get('class','').split() and n.get('name','').startswith('请选择要导出的评价范围')],'export-dialog-unverified')
    if not re.search(r'所属门店\s+按省市\s+全部门店',modal.get('name','')):raise ValueError('export-store-scope-unverified')
    scope={'truncated':False,'root':modal};field=export_range_input(scope)
    if require_dates and field.get('attributes',{}).get('value')!=date_range['start']+' ~ '+date_range['end']:raise ValueError('export-range-mismatch')
    return modal,field

def export_calendar_day(tree,date_range,iso):
    """Resolve only within the verified export dialog, never the page picker."""
    modal,_=verified_export_dialog(tree,date_range,require_dates=False)
    return calendar_day({'truncated':False,'root':modal},iso)

def bound_generated_record(tree,date_range,baseline,bound):
    """B92: resolve a provably pre-existing artifact bound by a verified
    identity reconcile. Same page-parse discipline as
    submitted_export_record (it is re-run first and must hold), then the row
    is located by exact identity (filename + generated_at) instead of the
    submission window. The bound row must be the unique exact-range success
    row on the page and must exist in the reviewed baseline: the reconcile
    that wrote `bound` proved the submission created nothing (zero
    post-baseline records), so the artifact identity is the platform record
    itself, never a replayed submission."""
    def need(ok,code):
        if not ok:raise ValueError(code)
    def classes(n):return set(n.get('attributes',{}).get('class','').split())
    need(isinstance(bound,dict) and bound.get('bound_by')=='export-artifact-identity-recovery-v1','bound-record-unbound')
    proof=submitted_export_record(tree,date_range,baseline,bound['submitted_at'])
    if proof['row'] is not None:return proof  # a real post-submission record appeared; normal path wins
    ns=list(nodes(tree))
    table=unique([n for n in ns if {'byted-table-container','byted-table-container-row'}<=classes(n)],'record-page-table-not-unique')
    scoped=list(nodes({'truncated':False,'root':table}))
    body=unique([n for n in scoped if 'byted-table-body' in classes(n)],'record-page-body-not-unique')
    rows=records({'truncated':False,'root':body})
    tag=export_tag(date_range)
    from datetime import datetime as _dt
    def row_id(r):
        name=r.get('text','').split(' ',1)[0];_dt.strptime(r['generated_at'],'%Y-%m-%d %H:%M:%S');return name,r['generated_at']
    matching=[r for r in rows if row_id(r)==(tag,bound['generated_at'])]
    need(len(matching)==1,'bound-record-not-unique-on-page')
    row=matching[0];need(row['state']=='success','bound-record-not-success')
    from zoneinfo import ZoneInfo as _Z
    old={( _dt.strptime(r['generated_at'],'%Y-%m-%d %H:%M:%S'),r['text'].split(' ',1)[0]) for r in baseline}
    need(( _dt.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S'),tag) in old,'bound-record-not-in-reviewed-baseline')
    need(_dt.fromisoformat(bound['submitted_at']).astimezone(_Z('Asia/Shanghai')).date()>=_dt.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S').date(),'bound-record-not-same-day')
    return {'row':row,'page':proof['page']}
