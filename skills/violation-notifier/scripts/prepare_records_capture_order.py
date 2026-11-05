#!/usr/bin/env python3
"""Pin separate navigation/capture profiles for one screenshot source. No UI."""
import argparse,json
from pathlib import Path
import prepare_records_profile as p
import governance_detail as d
CONTRACT='records-screenshot-profile-pair-v1'
def binding(source,navigation,capture):
 a=d.document(navigation);b=d.document(capture);p.validate(a,source);p.validate(b,source);p.need(b.get('evidence_contract')==p.BUSINESS,'capture-order-business-contract-required')
 comparable=lambda value:{k:v for k,v in value.items() if k!='evidence_contract'}
 p.need(comparable(a)==comparable(b),'capture-order-profiles-not-same-source-scope-selectors');meta=a['derivation'];folder=Path(source['path']).resolve().parent/'.records-region-navigation'/source['sha256'];journal=folder/'state.json'
 expected={'schema':'records-region-navigation-v1','source':source,'profile':navigation,'job':meta['job'],'query':meta['query'],'tab_id':meta['tab_id'],'window_id':meta['window_id']}
 if journal.exists():p.need(json.loads(journal.read_text()).get('binding')==expected,'capture-order-original-navigation-binding-required')
 return {'schema':CONTRACT,'source':source,'navigation_profile_ref':navigation,'capture_profile_ref':capture,'job':meta['job'],'query':meta['query'],'tab_id':meta['tab_id'],'window_id':meta['window_id'],'canonical_navigation_journal':str(journal)}
def validate(ref,source,navigation):
 value=d.document(ref);p.need(value.get('schema')==CONTRACT and value.get('source')==source and value.get('navigation_profile_ref')==navigation,'capture-order-original-profile-pair-required');p.need(value==binding(source,navigation,value['capture_profile_ref']),'capture-order-scope-changed');return value
def prepare(source,navigation,capture,out):
 value=binding(source,navigation,capture);out=Path(out).resolve()
 if out.exists():p.need(json.loads(out.read_text())==value,'capture-order-existing-output-conflict')
 else:d.exclusive(out,value)
 return {'ok':True,'profile_pair':d.ref(out),'navigation_profile_ref':navigation,'capture_profile_ref':capture,'ui_used':False}
def main():
 a=argparse.ArgumentParser(description=__doc__)
 for field in ('source','navigation-profile','capture-profile'):
  a.add_argument('--'+field,required=True);a.add_argument('--'+field+'-sha256',required=True)
 a.add_argument('--out',required=True);v=a.parse_args();ref=lambda n:{'path':str(Path(getattr(v,n)).resolve()),'sha256':getattr(v,n+'_sha256')}
 try:print(json.dumps(prepare(ref('source'),ref('navigation_profile'),ref('capture_profile'),v.out),ensure_ascii=False));return 0
 except (ValueError,OSError,KeyError) as e:print(json.dumps({'ok':False,'error':str(e),'ui_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
