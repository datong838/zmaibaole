"""Exact reboot screenshot binding; old source/query/profile remain immutable."""
import copy
from pathlib import Path
import role_execution_order as o
import violation_reboot_continuation as r
KIND='governance-records-reboot-derived-profile-v1'

def derive(source,original_profile,admission):
    import prepare_records_profile as api
    a=r.verify(admission);old=o.doc(original_profile);api.validate(old,source);meta=old['derivation'];r.need(a['original']['source']==source and a['original']['profile']==original_profile and a['original']['job']==meta['job'] and a['original']['query']==meta['query'],'profile-original-binding')
    fresh=o.doc(a['fresh_observation']);page=o.doc(a['fresh_page']);r.need(len(meta['pages'])==1 and page['page']==meta['pages'][0]['page']==1,'only-original-single-page')
    # Selectors are not inferred from old missing fields: fresh_facts already
    # parsed all fields from fresh DOM. page_inputs subsequently checks every
    # original selector in the current raw before native capture.
    p=copy.deepcopy(old);newmeta=copy.deepcopy(meta);newmeta.update(kind=KIND,original_profile=original_profile,reboot_continuation=admission,original_derivation=meta,tab_id=a['effective_scope']['tab_id'],window_id=a['effective_scope']['window_id'],navigation_root=str(Path(admission['path']).parent/'records-navigation'),pages=[{'page':1,'observation':a['fresh_observation'],'notice_ids':[v['notice_id'] for v in page['rows']],'row_selectors':[v['selector'] for v in page['rows']]}]);p['derivation']=newmeta;return p

def validate(profile,source):
    m=profile.get('derivation',{});r.need(m.get('kind')==KIND and m.get('source')==source,'profile-type');r.need(profile==derive(source,m['original_profile'],m['reboot_continuation']),'profile-not-derived');return profile

def nav_root(profile,source):
    validate(profile,source);return Path(profile['derivation']['navigation_root'])
