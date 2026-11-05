#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive a pinned records screenshot profile from verified saved public DOM.
No UI/capture/input. DOM readiness is distinct from viewport/screenshot acceptance.
"""
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import governance_detail as d
import governance_dom as g
import governance_capture as source_api
import frame_capture as fc
import governance_projection as gp
KIND='governance-records-derived-profile-v1'
BUSINESS='notice-five-business-cells-v1'
PROJECTION='gov-records-rectification-display-v3'
need=g.need

def matcher(n,*,selector=True):
 need(isinstance(n.get('selector'),str) and n['selector'],'records-profile-selector-missing');r={'selector':n['selector']} if selector else {'role':n['role']}
 if n.get('attributes',{}).get('class'):r['attributes']={'class':n['attributes']['class']}
 return r

def derive(source_ref,job_ref,query_ref,*,full_source_check=True,evidence_contract=None,projection_contract=None):
 need(projection_contract in (None,PROJECTION) and (projection_contract is None or evidence_contract==BUSINESS),'records-profile-projection-contract-unreviewed')
 need(evidence_contract in (None,BUSINESS),'records-profile-evidence-contract-unreviewed')
 source=d.document(source_ref);job=d.document(job_ref);query=d.document(query_ref);d.nav.scope(job)
 need(source.get('capture_schema')=='governance-public-dom-capture-v1' and source.get('source')=='local-dom-bridge' and source.get('capture_manifest'),'records-profile-actual-capture-required');
 if full_source_check:need(source_api.validate(source_ref['path'])==source,'records-profile-source-derived-payload-changed')
 need(source.get('account_verified') is True and source.get('records',{}).get('scope')=='全部' and source['records'].get('all_pages_read') is True and source['records'].get('filters_verified') is True and source['records'].get('unread_only') is False,'records-profile-full-record-scope-required')
 cm=d.document(source['capture_manifest']);need(cm['inputs']['job']==job_ref and cm['inputs']['query']==query_ref and source['source_evidence_refs']['job']==job_ref and source['source_evidence_refs']['query']==query_ref,'records-profile-source-ref-conflict')
 need((source['records']['start'],source['records']['end_exclusive'])==(job['start'],job['end_exclusive']),'records-profile-inner-date-conflict');need(source['company']==job['company'] and str(source['groupid'])==str(job['groupid']) and source['identity']==job['identity'] and (source['start'],source['end_exclusive'])==(job['start'],job['end_exclusive']),'records-profile-company-date-identity-conflict');need(query.get('phase')=='capture-complete' and query.get('fingerprint')==d.nav.tag(job) and query.get('approved_version')==d.nav.VERSION and query.get('tab_id')==d.document(cm['inputs']['detail_manifest'])['tab_id'],'records-profile-query-unverified')
 rows=g.complete_pages(query['pages']);need(rows==query['rows'] and len(rows)==source['records']['total'] and len(source['records']['rows'])==len(rows),'records-profile-query-coverage-conflict');need([r['notice_id'] for r in rows]==[r['notice_id'] for r in source['records']['rows']],'records-profile-source-row-order-conflict')
 expected={r['notice_id']:r for r in source['records']['rows']};profile=None;pages=[];window=None
 for page in query['pages']:
  ref=page['observation'];raw=d.document(ref);need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==query['tab_id'] and raw.get('not_business_capture') is True,'records-profile-observation-source-conflict');tab=d.nav.context([{'tabs':[raw['tab']]}],query['tab_id'],job['groupid']);need(tab['url'].startswith('https://life.douyin.com'+g.RECORDS+'?'),'records-profile-record-route-required')
  if window is None:window=tab['windowId']
  need(tab['windowId']==window,'records-profile-window-changed');tree=raw['tree'];d.nav.identity(tree,job['identity']);parsed=g.records_page(tree,start=job['start'],end_exclusive=job['end_exclusive']);need(parsed=={k:v for k,v in page.items() if k!='observation'},'records-profile-original-page-changed');root=g.root(tree,g.RECORDS);ns=list(g.walk(root));table=g.one([n for n in ns if n.get('tag')=='table' and 'governance_merchant-Table-Implement' in g.cls(n)],'records-profile-table-not-unique');cards=[n for n in d.nav.nodes(tree) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')];card=g.one(cards,'records-profile-usercard-required')
  alltab=g.one([n for n in ns if 'governance_merchant-tab-bar-item-active' in g.cls(n) and re.fullmatch(r'全部\s*\d+',g.text(n))],'records-profile-all-tab-not-unique');unread=g.one([n for n in ns if n.get('tag')=='label' and g.text(n)=='只看未读'],'records-profile-unread-not-unique');pager=g.one(g.classnodes(root,'governance_merchant-pager'),'records-profile-pager-not-unique');items=[n for n in g.walk(pager) if n.get('tag')=='li' and 'governance_merchant-pager-item' in g.cls(n)];current=g.one([n for n in items if 'governance_merchant-pager-item-checked' in g.cls(n)],'records-profile-current-page-not-unique');nxt=g.one([n for n in items if g.classnodes(n,'governance_merchant-icon-right')],'records-profile-next-not-unique')
  actualrows=[n for n in g.walk(table) if n.get('tag')=='tr' and n.get('role')=='row' and 'governance_merchant-Table-Row' in g.cls(n) and any(c.get('tag')=='td' for c in n.get('children',[]))];need(len(actualrows)==len(parsed['rows']) and actualrows,'records-profile-row-role-or-count-conflict');rowclasses={n['attributes']['class'] for n in actualrows};need(len(rowclasses)==1,'records-profile-row-class-unreviewed');subjects=[]
  for node,row in zip(actualrows,parsed['rows']):
   need(fc.row_notice_id(node,{'domProfile':'governance-records-v1','noticeIdMode':'first-cell-text-v1'})==row['notice_id'],'records-profile-notice-id-position-conflict');need(row['store_name']==expected[row['notice_id']]['subject'] and row['violation_date']==expected[row['notice_id']]['date'] and row['reason']==expected[row['notice_id']]['reason'] and row['effective_status']==expected[row['notice_id']]['effectiveness_status'] and row['disposal']==expected[row['notice_id']].get('table_disposal','，'.join(expected[row['notice_id']]['actions'])) and row['rectification_status']==expected[row['notice_id']]['rectification_status'],'records-profile-source-row-tuple-conflict');subjects.append(g.one([n for n in g.walk(node['children'][1]) if 'name-iUMfRa' in g.cls(n) and not n.get('children')],'records-profile-subject-not-unique'))
  need(len({n['attributes']['class'] for n in subjects})==1,'records-profile-subject-class-unreviewed');headnodes=[n for n in g.walk(table) if n.get('tag')=='th' and n.get('role')=='columnheader'];selected_heads=[n for n in headnodes if g.text(n) in fc.HEADERS];need(len(selected_heads)==len(fc.HEADERS) and {g.text(n) for n in selected_heads}==set(fc.HEADERS),'records-profile-five-headers-not-complete-unique');heads={g.text(n):matcher(n) for n in selected_heads};need(set(heads)==set(fc.HEADERS),'records-profile-five-headers-required')
  tbody=g.one([n for n in table.get('children',[]) if n.get('tag')=='tbody'],'records-profile-body-not-unique')
  p={'status':'DOM-derived-ready','revision':source['profile_revision'],'identity':{'mode':'governance-user-card-v1','card':matcher(card)},'records':{'domProfile':'governance-records-v1','noticeIdMode':'first-cell-text-v1','root':matcher(tbody),'row':matcher(actualrows[0],selector=False),'subject':matcher(subjects[0],selector=False),'dateInput':matcher(g.date_input(tree)),'scope':matcher(alltab),'unreadOnly':matcher(unread),'total':matcher(alltab),'currentPage':matcher(current,selector=False),'next':{'selector':nxt['selector']},'filter_contract':'same-source-date-all-unread-full-pages-v1'},'screenshot':{'headers':heads}}
  if profile is None:profile=p
  else:need(p==profile,'records-profile-cross-page-selectors-changed')
  pages.append({'page':parsed['page'],'observation':ref,'notice_ids':[r['notice_id'] for r in parsed['rows']],'row_selectors':[r['selector'] for r in parsed['rows']]})
 need(profile is not None,'records-profile-empty-query');
 if evidence_contract is not None:profile['evidence_contract']=evidence_contract
 if projection_contract is not None:profile['projection_contract']=projection_contract
 profile['derivation']={'kind':KIND,'source':source_ref,'job':job_ref,'query':query_ref,'capture_manifest':source['capture_manifest'],'tab_id':query['tab_id'],'window_id':window,'pages':pages,'scope':{'company':job['company'],'groupid':str(job['groupid']),'start':job['start'],'end_exclusive':job['end_exclusive'],'total':len(rows),'all_scope':True,'unread_only':False},'validation_scope':{'prepare':'complete-governance-capture-replay','runtime':'pinned-source-job-query-and-full-page-screenshot-semantics'},'viewport_visibility_verified':False,'screenshot_accepted':False};return profile

def validate(profile,source_ref):
 if profile.get('derivation',{}).get('kind')=='governance-records-reboot-derived-profile-v1':
  import violation_reboot_profile as reboot
  return reboot.validate(profile,source_ref)
 meta=profile.get('derivation',{});need(meta.get('kind')==KIND and meta.get('source')==source_ref,'records-profile-derived-source-required');need(profile==derive(source_ref,meta['job'],meta['query'],full_source_check=False,evidence_contract=profile.get('evidence_contract'),projection_contract=profile.get('projection_contract')),'records-profile-derived-selectors-or-refs-changed');return profile

def automatic_projection(query_ref):
 # Only prepare for a new output opts in. Derive/validate retain legacy defaults.
 query=d.document(query_ref);pending=False
 for page in query['pages']:
  raw=d.document(page['observation']);root=g.root(raw['tree'],g.RECORDS)
  table=g.one([n for n in g.walk(root) if n.get('tag')=='table' and 'governance_merchant-Table-Implement' in g.cls(n)],'records-profile-auto-table-not-unique')
  rows=[n for n in g.walk(table) if n.get('tag')=='tr' and any(c.get('tag')=='td' for c in n.get('children',[]))]
  need(bool(rows),'records-profile-auto-rows-required')
  for row in rows:
   cells=row.get('children',[]);need(len(cells)==10 and all(n.get('tag')=='td' for n in cells),'records-profile-auto-ten-cells-required')
   masks,timers=gp.rectification_mask(cells[6]);pending=pending or bool(timers)
 return PROJECTION if pending else None

def _prepare_uncached(source_ref,job_ref,query_ref,out,*,evidence_contract=None,projection_contract=None):
 out=Path(out).resolve()
 if out.exists():
  original=out.read_bytes();profile=json.loads(original);meta=profile.get('derivation',{})
  need(meta.get('source')==source_ref and meta.get('job')==job_ref and meta.get('query')==query_ref,'records-profile-output-input-conflict')
  need((evidence_contract is None or evidence_contract==profile.get('evidence_contract')) and (projection_contract is None or projection_contract==profile.get('projection_contract')),'records-profile-output-contract-conflict')
  # Full source validation remains mandatory; never upgrade an old output in place.
  expected=derive(source_ref,job_ref,query_ref,evidence_contract=profile.get('evidence_contract'),projection_contract=profile.get('projection_contract'))
  need(profile==expected and out.read_bytes()==original,'records-profile-output-conflict')
 else:
  need(projection_contract in (None,PROJECTION) and evidence_contract in (None,BUSINESS),'records-profile-projection-contract-unreviewed')
  selected=automatic_projection(query_ref)
  if projection_contract is not None or selected is not None:
   evidence_contract=BUSINESS;projection_contract=PROJECTION
  profile=derive(source_ref,job_ref,query_ref,evidence_contract=evidence_contract,projection_contract=projection_contract)
  d.exclusive(out,profile)
 return {'ok':True,'profile':d.ref(out),'status':profile['status'],'pages':len(profile['derivation']['pages']),'total':profile['derivation']['scope']['total'],'ui_used':False,'screenshot_accepted':False}

def prepare(source_ref,job_ref,query_ref,out,*,evidence_contract=None,projection_contract=None):
 from verification_session import validation_scope
 with validation_scope() as session:
  result=_prepare_uncached(source_ref,job_ref,query_ref,out,evidence_contract=evidence_contract,projection_contract=projection_contract)
  return {**result,'validation_metrics':session.summary()}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('source','source-sha256','job','job-sha256','query','query-sha256','out'):p.add_argument('--'+name,required=True)
 p.add_argument('--evidence-contract',choices=(BUSINESS,));p.add_argument('--projection-contract',choices=(PROJECTION,))
 a=p.parse_args()
 try:
  ref=lambda name:{'path':str(Path(getattr(a,name)).resolve()),'sha256':getattr(a,name+'_sha256')};print(json.dumps(prepare(ref('source'),ref('job'),ref('query'),a.out,evidence_contract=a.evidence_contract,projection_contract=a.projection_contract),ensure_ascii=False));return 0
 except (OSError,ValueError,KeyError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'ui_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
