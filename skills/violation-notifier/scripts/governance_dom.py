"""Observed governance public DOM parser and deterministic read-only query planner.
No browser execution here. Commands must pass the separately reviewed bridge policy.
No guessed dates, record IDs, zero totals, hidden interfaces or business progress.
"""
import re
import verification_session as verification
from datetime import date,timedelta
from urllib.parse import urlsplit
CENTER='/p/governance/home_violation_center';RECORDS='/p/governance/violation_list'
HEADERS=['违规原因','处置主体','违规对象','处置生效状态','处置方式','违规时间','整改状态','申诉状态','违约金状态','操作']
def need(ok,code):
    if not ok:raise ValueError(code)
def one(items,code):need(len(items)==1,code);return items[0]
def cls(n):return set(n.get('attributes',{}).get('class','').split())
def walk(n):
    session=verification.current();indexed=session.walk_view(n) if session is not None else None
    if indexed is not None:
        yield from indexed;return
    yield n
    for c in n.get('children',[]):yield from walk(c)
def nodes(tree):
    need(tree.get('truncated') is False,'governance-complete-tree-required');session=verification.current();indexed=session.all_nodes(tree['root']) if session is not None else None;return indexed if indexed is not None else list(walk(tree['root']))
def text(n):
    value=n.get('name','');need(len(value)<800,'governance-text-possibly-truncated');return value.strip()
def root(tree,path=None):
    need(tree.get('truncated') is False,'governance-complete-tree-required');session=verification.current();indexed=session.matching(tree['root'],'ids','governanceRoot') if session is not None else None;ns=nodes(tree) if indexed is None else indexed;need(urlsplit(tree['url']).path in (CENTER,RECORDS),'governance-path-unreviewed')
    if path:need(urlsplit(tree['url']).path==path,'governance-wrong-view')
    return one([n for n in ns if n.get('attributes',{}).get('id')=='governanceRoot'],'governance-root-not-unique')
def classnodes(n,c):
    session=verification.current();indexed=session.matching(n,'classes',c) if session is not None else None
    return indexed if indexed is not None else [x for x in walk(n) if c in cls(x)]
def date_input(tree):
    r=root(tree);found=[]
    for box in classnodes(r,'governance_merchant-date-picker-range'):
        for n in walk(box):
            if n.get('tag')=='input' and n.get('role')=='textbox' and (n.get('placeholder')=='开始日期 ～ 结束日期' or text(n)=='违规时间'):found.append(n)
    return one(found,'governance-date-input-not-unique')
def date_value(tree):
    n=date_input(tree);value=n.get('attributes',{}).get('value');need(isinstance(value,str),'governance-date-value-not-exposed');value=re.sub(r'\s*[~～]\s*',' ~ ',value.replace('/','-').strip());return value

def calendar(tree):
    root(tree);panels=[n for n in nodes(tree) if 'governance_merchant-date-picker-popper' in cls(n)];p=one(panels,'governance-visible-calendar-not-unique');views=classnodes(p,'governance_merchant-date-view');need(len(views)==2,'governance-two-month-views-required');out=[]
    for view in views:
        title=one(classnodes(view,'governance_merchant-date-title'),'governance-month-title-not-unique');m=re.fullmatch(r'(\d{4})年(\d{1,2})月',text(title));need(m,'governance-month-title-invalid');year,month=map(int,m.groups());date(year,month,1)
        positions=cls(view)&{'governance_merchant-date-position-start','governance_merchant-date-position-end'};need(len(positions)==1,'governance-calendar-side-invalid');cells={}
        for cell in classnodes(view,'governance_merchant-date-col'):
            if 'governance_merchant-date-grid-in' not in cls(cell) or 'governance_merchant-date-disabled' in cls(cell):continue
            need(cell.get('tag')=='span' and re.fullmatch(r'[1-9]|[12][0-9]|3[01]',text(cell)) is not None,'governance-calendar-cell-invalid')
            children=cell.get('children',[]);need(len(children)==1,'governance-calendar-date-item-not-unique');item=children[0]
            base={'governance_merchant-date-date','governance_merchant-date-item','governance_merchant-date-grid-in'};states={'governance_merchant-date-selected','governance_merchant-date-today','governance_merchant-date-state-start','governance_merchant-date-state-end','governance_merchant-date-state-in','governance_merchant-date-state-single'}
            need(item.get('tag')=='div' and not item.get('children') and text(item)==text(cell) and not item.get('disabled') and base<=cls(item)<=base|states,'governance-calendar-date-item-invalid')
            d=date(year,month,int(text(cell))).isoformat();need(d not in cells,'governance-duplicate-day');cells[d]=item
        controls={}
        for direction in ('prev','next'):
            cs=classnodes(view,'governance_merchant-date-nav-'+direction)
            icon='governance_merchant-icon-'+('left' if direction=='prev' else 'right')
            candidates=[n for n in cs if classnodes(n,icon)]
            if candidates:controls[direction]=one(candidates,'governance-month-navigation-ambiguous')
        out.append({'year':year,'month':month,'side':next(iter(positions)),'cells':cells,'controls':controls})
    need({v['side'] for v in out}=={'governance_merchant-date-position-start','governance_merchant-date-position-end'},'governance-calendar-sides-conflict');return out

def click(n,kind='filter'):need(n.get('selector') and not n.get('disabled'),'governance-target-not-ready');return {'op':'click','locator':{'by':'selector','value':n['selector']},'kind':kind}
def calendar_action(tree,target):
    target=date.fromisoformat(target);views=calendar(tree);key=target.isoformat();candidates=[v['cells'][key] for v in views if key in v['cells']]
    if candidates:return {'action':click(one(candidates,'governance-target-date-ambiguous')),'selects_date':key,'month_navigation':False}
    months=[v['year']*12+v['month'] for v in views];wanted=target.year*12+target.month
    need(wanted<min(months) or wanted>max(months),'governance-target-date-disabled-or-missing');direction='prev' if wanted<min(months) else 'next';side='start' if direction=='prev' else 'end';view=one([v for v in views if v['side'].endswith(side)],'governance-calendar-side-missing');need(direction in view['controls'],'governance-month-control-missing');return {'action':click(view['controls'][direction]),'selects_date':None,'month_navigation':True,'expected_month_delta':-1 if direction=='prev' else 1}

def records_zero_page(tree,table,heads,*,start,end_exclusive,require_date):
    """Observed empty table, not an inferred zero from an unnumbered tab."""
    r=root(tree,RECORDS);ns=list(walk(r))
    need(require_date and start and end_exclusive,'governance-zero-date-binding-required')
    expected=start+' ~ '+(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat();need(date_value(tree)==expected,'governance-record-date-filter-mismatch')
    tab=one([n for n in ns if n.get('tag')=='div' and 'governance_merchant-tab-bar-item' in cls(n) and text(n)=='全部'],'governance-zero-all-tab-not-unique')
    need(cls(tab)=={'governance_merchant-tab-bar-item','governance_merchant-tab-bar-item-active','governance_merchant-tab-bar-item-type-text'} and len(tab.get('children',[]))==1,'governance-zero-all-tab-not-selected')
    label=tab['children'][0];need(label.get('tag')=='span' and cls(label)=={'governance_merchant-tab-bar-item-label'} and text(label)=='全部' and not label.get('children'),'governance-zero-all-label-invalid')
    need(not any('governance_merchant-tab-bar-item' in cls(n) and re.fullmatch(r'全部\s*\d+',text(n)) for n in ns),'governance-zero-numbered-total-conflict')
    manage=one([n for n in ns if n.get('tag')=='div' and 'governance_merchant-tab-bar-item' in cls(n) and text(n)=='违规记录管理'],'governance-zero-management-tab-missing');need('governance_merchant-tab-bar-item-active' in cls(manage),'governance-zero-management-tab-inactive')
    unread=one([n for n in ns if n.get('tag')=='label' and text(n)=='只看未读' and 'governance_merchant-checkbox' in cls(n)],'governance-unread-filter-missing');need(len(classnodes(unread,'governance_merchant-checkbox-icon-uncheck'))==1 and not classnodes(unread,'governance_merchant-checkbox-icon-check'),'governance-unread-filter-enabled')
    body=one([n for n in table.get('children',[]) if n.get('tag')=='tbody' and n.get('role')=='rowgroup' and cls(n)=={'governance_merchant-Table-Body'}],'governance-zero-tbody-not-unique')
    need(not body.get('children') and not text(body) and not any(n.get('tag')=='td' for n in ns),'governance-zero-table-not-empty')
    header=one([n for n in table.get('children',[]) if n.get('tag')=='thead'],'governance-zero-thead-not-unique');need(len(header.get('children',[]))==1 and header['children'][0].get('children')==heads,'governance-zero-header-structure-invalid')
    cols=one([n for n in table.get('children',[]) if n.get('tag')=='colgroup' and cls(n)=={'governance_merchant-Table-ColGroup'}],'governance-zero-colgroup-invalid');need(len(cols.get('children',[]))==10 and all(n.get('tag')=='col' and cls(n)=={'governance_merchant-Table-Col'} and not n.get('children') and not text(n) for n in cols['children']),'governance-zero-columns-invalid')
    need(len(table.get('children',[]))==3 and not classnodes(r,'governance_merchant-pager') and not classnodes(r,'governance_merchant-pager-item'),'governance-zero-pagination-conflict')
    container=one([n for n in ns if table in n.get('children',[])],'governance-zero-table-container-not-unique');need(cls(container)=={'governance_merchant-Table-Container','governance_merchant-Table-Container_scrollable'},'governance-zero-table-container-invalid')
    empty=one([n for n in container.get('children',[]) if cls(n)=={'governance_merchant-Table-Empty'}],'governance-zero-empty-sibling-missing');current=empty
    outer=one(current.get('children',[]),'governance-zero-empty-structure-invalid')
    if cls(outer)=={'governance_merchant-empty','governance_merchant-empty-size-normal','governance_merchant-empty-untyped'}:
        inner=one(outer.get('children',[]),'governance-zero-empty-structure-invalid');need(cls(inner)=={'governance_merchant-empty-inner-children'},'governance-zero-empty-structure-invalid')
        view=one(inner.get('children',[]),'governance-zero-empty-structure-invalid');need(cls(view)=={'emptyView-cEpWy_'},'governance-zero-empty-structure-invalid')
        children=view.get('children',[])
        need(len(children)==2 and cls(children[0])=={'emptyImageWrapper-m5qqw6'} and not text(children[0]) and len(children[0].get('children',[]))==1 and children[0]['children'][0].get('tag')=='svg' and children[1].get('tag')=='div' and cls(children[1])=={'emptyText-g7632x'} and not children[1].get('children') and text(children[1])=='暂无数据','governance-zero-empty-literal-invalid')
    else:
        for expected_class in ('governance_merchant-empty','governance_merchant-empty-inner'):
            need(len(current.get('children',[]))==1,'governance-zero-empty-structure-invalid');current=current['children'][0];need(current.get('tag')=='div' and cls(current)=={expected_class},'governance-zero-empty-structure-invalid')
        children=current.get('children',[]);need(len(children)==2 and children[0].get('tag')=='svg' and not text(children[0]) and children[1].get('tag')=='p' and not children[1].get('children') and text(children[1])=='暂无数据','governance-zero-empty-literal-invalid')
    need(len([n for n in ns if not n.get('children') and text(n)=='暂无数据'])==1 and not any(n.get('role')=='progressbar' or n.get('attributes',{}).get('aria-busy')=='true' for n in ns),'governance-zero-empty-or-busy-conflict')
    return {'page':1,'total':0,'rows':[],'next':{'disabled':True,'command':None},'unread':False,'all_scope':True,'headers':[{'name':text(h),'selector':h['selector']} for h in heads],'date_selector':date_input(tree)['selector'],'query_verified':True,'empty_result':{'schema':'governance-records-explicit-empty-v1','all_selector':tab['selector'],'empty_selector':children[1]['selector'],'tbody_selector':body['selector'],'pagination_observed':False,'logical_single_result':True}}

def records_counts_pending(tree):
    """The records list has mounted without its counts, so it has no result yet (B43).

    The list renders its tabs twice: bare names over an empty tbody first, then the counted
    tabs (全部N / 待整改N) together with the queried rows and the pager. A bare 全部 over an
    empty tbody is therefore not evidence of an empty result -- reading it as the explicit
    zero page is exactly what turned a page that had not rendered into a fatal date-binding
    error. Only the counted tab proves the query has come back, so until it appears the
    caller must read again. A genuinely zero day never settles past this state and is left
    to the supervisor instead of being claimed as empty.
    """
    if urlsplit(tree.get('url') or '').path!=RECORDS:return False
    r=root(tree,RECORDS);ns=list(walk(r))
    if any('governance_merchant-tab-bar-item' in cls(n) and re.fullmatch(r'全部\s*\d+',text(n)) for n in ns):return False
    if not any(n.get('tag')=='div' and 'governance_merchant-tab-bar-item' in cls(n) and text(n)=='全部' for n in ns):return False
    table=one([n for n in ns if n.get('tag')=='table' and 'governance_merchant-Table-Implement' in cls(n)],'governance-table-not-unique')
    body=one([n for n in table.get('children',[]) if n.get('tag')=='tbody' and n.get('role')=='rowgroup' and cls(n)=={'governance_merchant-Table-Body'}],'governance-zero-tbody-not-unique')
    return not body.get('children') and not text(body) and not classnodes(r,'governance_merchant-pager')

def records_page(tree,*,start=None,end_exclusive=None,require_date=True):
    r=root(tree,RECORDS);ns=list(walk(r));table=one([n for n in ns if n.get('tag')=='table' and 'governance_merchant-Table-Implement' in cls(n)],'governance-table-not-unique');heads=[n for n in walk(table) if n.get('tag')=='th' and n.get('role')=='columnheader'];need([text(h) for h in heads]==HEADERS,'governance-record-headers-changed')
    if any(n.get('tag')=='div' and 'governance_merchant-tab-bar-item' in cls(n) and text(n)=='全部' for n in ns):
        return records_zero_page(tree,table,heads,start=start,end_exclusive=end_exclusive,require_date=require_date)
    tabs=[n for n in ns if 'governance_merchant-tab-bar-item' in cls(n) and re.fullmatch(r'全部\s*\d+',text(n))];tab=one(tabs,'governance-all-tab-not-unique');need('governance_merchant-tab-bar-item-active' in cls(tab),'governance-all-tab-not-selected');total=int(re.search(r'\d+',text(tab)).group())
    unread=one([n for n in ns if n.get('tag')=='label' and text(n)=='只看未读' and 'governance_merchant-checkbox' in cls(n)],'governance-unread-filter-missing');need(len(classnodes(unread,'governance_merchant-checkbox-icon-uncheck'))==1 and not classnodes(unread,'governance_merchant-checkbox-icon-check'),'governance-unread-filter-enabled')
    rows=[];ids=set()
    for row in walk(table):
        if row.get('tag')!='tr' or row.get('role')!='row' or 'governance_merchant-Table-Row' not in cls(row):continue
        if row.get('children') and all(c.get('tag')=='th' for c in row['children']):continue
        cells=[c for c in row.get('children',[]) if c.get('tag')=='td' and c.get('role')=='cell'];need(len(cells)==len(HEADERS),'governance-row-cells-incomplete');values=[text(c) for c in cells];m=re.fullmatch(r'(一般|严重|轻微)\s+(.+?)\s+ID:\s*([A-Za-z0-9_-]+)',values[0]);need(m,'governance-record-id-or-reason-invalid');level,reason,notice=m.groups();need(notice not in ids,'governance-record-id-duplicate');ids.add(notice)
        subject=one([n for n in walk(cells[1]) if 'name-iUMfRa' in cls(n) and not n.get('children')],'governance-subject-name-missing');links=[n for n in walk(cells[-1]) if n.get('tag')=='a' and text(n)=='查看详情' and {'governance_merchant-link','link-gpKMLO'}<=cls(n)];detail=one(links,'governance-detail-link-not-unique')
        when=date.fromisoformat(values[5].replace('/','-'));need(not start or when>=date.fromisoformat(start),'governance-row-before-range');need(not end_exclusive or when<date.fromisoformat(end_exclusive),'governance-row-after-range')
        rows.append({'notice_id':notice,'store_name':text(subject),'reason':reason,'severity':level,'object':values[2],'effective_status':values[3],'disposal':values[4],'violation_date':when.isoformat(),'rectification_status':values[6],'selector':row['selector'],'detail':click(detail,'navigation'),'cell_selectors':dict(zip(HEADERS,[c['selector'] for c in cells]))})
    pager=one(classnodes(r,'governance_merchant-pager'),'governance-pager-not-unique');items=[n for n in walk(pager) if n.get('tag')=='li' and 'governance_merchant-pager-item' in cls(n)];selected=one([n for n in items if 'governance_merchant-pager-item-checked' in cls(n)],'governance-page-selection-missing');need(re.fullmatch(r'[1-9]\d*',text(selected)),'governance-page-invalid');page=int(text(selected));nxt=one([n for n in items if classnodes(n,'governance_merchant-icon-right')],'governance-next-page-missing');disabled='governance_merchant-pager-item-disabled' in cls(nxt)
    if require_date:
        need(start and end_exclusive,'governance-query-date-binding-required');expected=start+' ~ '+(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat();need(date_value(tree)==expected,'governance-record-date-filter-mismatch')
    need(len(rows)<=total and (total!=0 or not rows),'governance-record-total-conflict');return {'page':page,'total':total,'rows':rows,'next':{'disabled':disabled,'command':None if disabled else click(nxt,'navigation')},'unread':False,'all_scope':True,'headers':[{'name':text(h),'selector':h['selector']} for h in heads],'date_selector':date_input(tree)['selector'],'query_verified':require_date}

def complete_pages(pages):
    need(pages and [p['page'] for p in pages]==list(range(1,len(pages)+1)),'governance-pages-not-consecutive');need(all(p['query_verified'] for p in pages),'governance-pages-not-query-verified');total=pages[0]['total'];need(all(p['total']==total for p in pages),'governance-total-changed-during-pages');need(pages[-1]['next']['disabled'] and all(not p['next']['disabled'] for p in pages[:-1]),'governance-pagination-incomplete');rows=[r for p in pages for r in p['rows']];need(len({r['notice_id'] for r in rows})==len(rows)==total,'governance-complete-record-coverage-mismatch');return rows

class QueryPlan:
    """Pure one-step planner. A caller persists unknown intent before executing a command.
    Neither an operation reply nor a saved list means a business batch is complete.
    """
    def __init__(self,start,end_exclusive):
        self.start=date.fromisoformat(start).isoformat();self.end=(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat();need(self.start<=self.end,'governance-empty-date-plan');self.end_exclusive=end_exclusive
    def next(self,tree,state):
        need(not state.get('unknown_intent'),'governance-unknown-intent-no-replay');phase=state.get('phase','open-date')
        if phase=='open-date':return {'command':click(date_input(tree)),'next_phase':'select-start'}
        if phase in ('select-start','select-end'):
            target=self.start if phase=='select-start' else self.end;action=calendar_action(tree,target);return {'command':action['action'],'next_phase':phase if action['month_navigation'] else ('select-end' if phase=='select-start' else 'verify-date'),'month_navigation':action['month_navigation'],'selected_date':action['selects_date'],'expected_month_delta':action.get('expected_month_delta')}
        if phase=='verify-date':
            need(date_value(tree)==self.start+' ~ '+self.end,'governance-selected-range-not-confirmed')
            if urlsplit(tree['url']).path==RECORDS:
                r=root(tree,RECORDS);button=one([n for n in walk(r) if n.get('tag')=='button' and text(n)=='查询' and 'governance_merchant-btn' in cls(n)],'governance-query-button-not-unique');return {'command':click(button),'next_phase':'collect-page'}
            summary=one(classnodes(root(tree,CENTER),'summary-RY8k0Q'),'governance-analysis-summary-not-unique');need(self.start in text(summary).replace('/','-') and self.end in text(summary).replace('/','-'),'governance-analysis-range-not-applied');return {'hold':'analysis-all-reasons-actual-view-profile-required','next_phase':'analysis-profile-required'}
        if phase=='collect-page':return {'page':records_page(tree,start=self.start,end_exclusive=self.end_exclusive),'next_phase':'page-collected'}
        raise ValueError('governance-query-phase-unreviewed')

def detail_action(tree,notice_id,*,start,end_exclusive):
    page=records_page(tree,start=start,end_exclusive=end_exclusive);row=one([r for r in page['rows'] if r['notice_id']==notice_id],'governance-requested-detail-not-on-current-page');return row['detail']
