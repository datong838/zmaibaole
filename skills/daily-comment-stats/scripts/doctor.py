#!/usr/bin/env python3
"""Read-only dependency check. Does not connect to Chrome or inspect credentials."""
import importlib.util
import json
from ds_common import SKILL, load_map, FlowError
from ds_calendar import load_calendar, shanghai_today

def main():
    checks=[]
    checks.append({'name':'openpyxl','ok':bool(importlib.util.find_spec('openpyxl'))})
    try:
        mapping=load_map();identities=json.loads((SKILL/'config/companies.json').read_text())['companies']
        checks.append({'name':'company-identities','ok':all(r['company'] in identities and str(identities[r['company']]['groupid']).isdigit() for r in mapping),'companies':len(mapping)})
    except (FlowError,OSError,ValueError,KeyError) as e:checks.append({'name':'company-identities','ok':False,'error':str(e)})
    role=SKILL.parent/'douyin-laike-operator'
    checks.append({'name':'independent-operator-skill','ok':all((role/p).is_file() for p in ['SKILL.md','backend.json','scripts/bridge-workflow.py','scripts/dom_evidence.py','scripts/role_cli.py'])})
    bridge=SKILL.parent/'chrome-dom-export'
    checks.append({'name':'local-dom-bridge-dependency','ok':all((bridge/p).is_file() for p in ['scripts/bridge.py','extension/manifest.json'])})
    cfg,_,_=load_calendar();checks.append({'name':'calendar-covered-year','ok':shanghai_today().year in cfg.get('covered_years',[]),'year':shanghai_today().year})
    result={'ok':all(c['ok'] for c in checks),'checks':checks,'backend':'local-dom-bridge','browser_connection_verified':False,'note':'File checks only. The execution role must verify the installed DOM bridge and explicit existing tab; this check does not connect to Chrome.','send_blocked':True}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
