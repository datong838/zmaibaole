"""Versioned public-DOM governance projection; only observed appeal timer is masked.
Caller must also validate pinned source/job/query/profile and normal_page tuple.
"""
import hashlib,json,re
SCHEMA='gov-records-stable5-v1'
PROVIDER_SCHEMA='gov-records-provider-scope-v2'
RECTIFICATION_CONTRACT='gov-records-rectification-display-v3'
RECTIFICATION_SCHEMA='gov-records-stable5-rectification-v3'
RECTIFICATION_PROVIDER_SCHEMA='gov-records-provider-rectification-v3'
RECTIFICATION_MARKER='rectification-v3'
RECTIFICATION_TIME=re.compile(r'(?:0|[1-9][0-9]*)天(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]')
HEADERS=['违规原因','处置主体','违规对象','处置生效状态','处置方式','违规时间','整改状态','申诉状态','违约金状态','操作']
# Observed same exact appeal wrapper switches to HH:MM:SS below one day.
# Preserve legacy N-day language byte-for-byte; only the new HH branch is 24h-bounded.
TIME=re.compile(r'(?:[0-9]+天[0-9]{2}:[0-9]{2}:[0-9]{2}|(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])')
def need(ok,why):
 if not ok:raise ValueError('governance-projection-'+why)
def walk(n):
 yield n
 for child in n.get('children',[]):yield from walk(child)
def cls(n):return n.get('attributes',{}).get('class','').split()
def one(ns,why):need(len(ns)==1,why);return ns[0]
def signature(n,name=None):
 a=n.get('attributes',{});return [n.get('selector'),n.get('tag'),n.get('role'),n.get('name','') if name is None else name,a.get('class',''),a.get('value'),n.get('disabled',False),*[a.get(k) for k in ('aria-disabled','aria-checked','aria-selected','aria-pressed')]]
def node(n,masks):
 if n.get('tag') in ('input','textarea','select') and n.get('name')!='违规时间':return [['excluded-form-control',n.get('selector'),n.get('tag')],[]]
 return [signature(n,masks.get(n.get('selector'))),[node(c,masks) for c in n.get('children',[])]]
def projection_schema(contract,provider=False):
 need(contract in (None,RECTIFICATION_CONTRACT),'contract-unreviewed')
 return (RECTIFICATION_PROVIDER_SCHEMA if provider else RECTIFICATION_SCHEMA) if contract else (PROVIDER_SCHEMA if provider else SCHEMA)
def rectification_mask(cell):
 ns=list(walk(cell));pending=any(n.get('name','').startswith('待整改') for n in ns)
 if not pending:return {},[]
 inner=cell.get('children',[]);need(len(inner)==1,'rectification-wrapper');wrapper=inner[0];parts=wrapper.get('children',[])
 need(wrapper.get('tag')=='div' and cls(wrapper)==['multi_text-ElDZAk'] and len(parts)==2,'rectification-wrapper')
 label,valuebox=parts;leaves=valuebox.get('children',[])
 need(label.get('tag')=='div' and cls(label)==['multi_text_top-gLB_CR'] and label.get('name')=='待整改' and not label.get('children') and valuebox.get('tag')=='div' and cls(valuebox)==['multi_text_second-sudxus'] and len(leaves)<=1,'rectification-shape')
 # Observed reviewed variant: 待整改 with no countdown at all. The cell then holds one static
 # word and no clock text, so the projection needs no mask; any text left in the value box
 # without its timer leaf is still a partial render and stays rejected by the aggregate rule.
 if not leaves:
  need(valuebox.get('name')=='' and wrapper.get('name')==cell.get('name')=='待整改','rectification-aggregate')
  need(all(n.get('role')==('cell' if n is cell else 'generic') and n.get('disabled',False) is False and not set(n.get('attributes',{}))-{'class','role'} for n in (cell,wrapper,label,valuebox)),'rectification-noninteractive-shape')
  return {},[]
 leaf=leaves[0];value=leaf.get('name','');need(leaf.get('tag')=='span' and not leaf.get('children') and not leaf.get('attributes') and RECTIFICATION_TIME.fullmatch(value) is not None,'rectification-timer')
 need(all(n.get('role')==('cell' if n is cell else 'generic') and n.get('disabled',False) is False and not set(n.get('attributes',{}))-{'class','role'} for n in (cell,wrapper,label,valuebox,leaf)),'rectification-noninteractive-shape')
 need(valuebox.get('name')==value and wrapper.get('name')==cell.get('name')=='待整改 '+value,'rectification-aggregate')
 return {cell['selector']:'待整改 <rectification-countdown>',wrapper['selector']:'待整改 <rectification-countdown>',valuebox['selector']:'<rectification-countdown>',leaf['selector']:'<rectification-countdown>'},[leaf['selector']]

def row_mask(row,*,projection_contract=None):
 projection_schema(projection_contract)
 cells=row.get('children',[]);need(len(cells)==10 and all(c.get('tag')=='td' and c.get('role')=='cell' and 'governance_merchant-Table-Cell' in cls(c) for c in cells),'ten-cells-required');masks={};timers=[];appeal=cells[7]
 leaves=[n for n in walk(appeal) if n.get('tag')=='span' and not n.get('children') and TIME.fullmatch(n.get('name',''))]
 if leaves:
  leaf=one(leaves,'timer-not-unique');inner=appeal.get('children',[]);need(len(inner)==1 and cls(inner[0])==['multi_text-ElDZAk'],'timer-wrapper');parts=inner[0].get('children',[]);need(len(parts)==2 and cls(parts[0])==['multi_text_top-gLB_CR'] and parts[0].get('name')=='待申诉' and not parts[0].get('children') and cls(parts[1])==['multi_text_second-sudxus'] and parts[1].get('children')==[leaf],'timer-shape');value=leaf['name'];need(parts[1].get('name')==value and inner[0].get('name')=='待申诉 '+value and appeal.get('name')=='待申诉 '+value,'timer-aggregate')
  for n in (appeal,inner[0]):masks[n['selector']]='待申诉 <appeal-countdown>'
  for n in (parts[1],leaf):masks[n['selector']]='<appeal-countdown>'
  timers=[leaf['selector']]
 if projection_contract:
  added,rectification=rectification_mask(cells[6]);masks.update(added);timers+=rectification
 return cells,masks,timers

def project(tree,groupid,*,actual_url=None,projection_contract=None):
 schema=projection_schema(projection_contract,actual_url is not None)
 need(tree.get('truncated') is False and tree.get('url')=='https://life.douyin.com/p/governance/violation_list','tree-scope');ns=list(walk(tree['root']));need(len(ns)<10000,'tree-bound');refs=[];timers=[];rectification_timers=[]
 def pick(test,why):
  n=one([n for n in ns if test(n)],why);refs.append(n['selector']);return n
 cards=[n for n in ns if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
 if actual_url is None:card=pick(lambda n:n in cards,'identity')
 else:
  from urllib.parse import urlsplit,parse_qs
  u=urlsplit(actual_url);need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and parse_qs(u.query,keep_blank_values=True).get('groupid')==[str(groupid)],'actual-url-scope')
  need(len(cards)<=1,'identity-not-unique');card=cards[0] if cards else None
 provider=pick(lambda n:'Profile-index-module__title--' in n.get('attributes',{}).get('class','') and re.fullmatch(r'服务商[0-9]+',n.get('name','')) is not None,'provider')
 date=pick(lambda n:n.get('tag')=='input' and n.get('role')=='textbox' and n.get('name')=='违规时间' and 'governance_merchant-input' in cls(n),'date')
 table=pick(lambda n:n.get('tag')=='table' and 'governance_merchant-Table-Implement' in cls(n),'table');heads=[n for n in walk(table) if n.get('tag')=='th' and n.get('role')=='columnheader'];need([n.get('name') for n in heads]==HEADERS,'headers');refs.extend(n['selector'] for n in heads)
 alltab=pick(lambda n:'governance_merchant-tab-bar-item-active' in cls(n) and re.fullmatch(r'全部\s*[0-9]+',n.get('name','')) is not None,'all');unread=pick(lambda n:n.get('tag')=='label' and n.get('name')=='只看未读' and 'governance_merchant-checkbox' in cls(n),'unread');icons=[n for n in walk(unread) if 'governance_merchant-checkbox-icon-uncheck' in cls(n)];need(len(icons)==1,'unread-off')
 pager=pick(lambda n:'governance_merchant-pager' in cls(n),'pager');need(len([n for n in walk(pager) if 'governance_merchant-pager-item-checked' in cls(n)])==1,'current-page')
 rows=[n for n in walk(table) if n.get('tag')=='tr' and any(c.get('tag')=='td' for c in n.get('children',[]))];need(0<len(rows)<=10,'row-count');out=[];ids=[]
 for row in rows:
  need(row.get('role')=='row' and 'governance_merchant-Table-Row' in cls(row),'row-semantics');cells,masks,ts=row_mask(row,projection_contract=projection_contract);rectification_timers += [n['selector'] for n in walk(cells[6]) if n.get('selector') in ts];found=re.findall(r'ID:\s*([A-Za-z0-9_-]+)',cells[0].get('name',''));need(len(found)==1 and found[0] not in ids,'notice-id');ids+=found;timers+=ts;refs.append(row['selector']);out.append([signature(row,''),[node(c,masks) for c in cells]])
 value=[schema,str(groupid),tree['url'],node(provider,{}),node(card,{}) if actual_url is None else ['actual-url',actual_url],node(date,{}),[node(h,{}) for h in heads],node(alltab,{}),node(unread,{}),node(pager,{}),ids,out]
 return {**({'rectification_timers':rectification_timers} if projection_contract else {}),'value':value,'refs':refs,'timers':timers,'rows':{r['selector']:[r_id,*[c.get('name','') for c in r['children'][:5]]] for r,r_id in zip(rows,ids)}}
def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def digest(tree,groupid,*,actual_url=None,projection_contract=None):return hashlib.sha256(canonical(project(tree,groupid,actual_url=actual_url,projection_contract=projection_contract)['value']).encode()).hexdigest()
def row_text(tree,groupid,selector,*,projection_contract=None):return canonical(project(tree,groupid,projection_contract=projection_contract)['rows'][selector])
