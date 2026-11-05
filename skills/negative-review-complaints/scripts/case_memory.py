#!/usr/bin/env python3
"""Portable append-only observations of actually read platform complaints; no UI."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse
import fcntl
import hashlib
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY = SKILL / 'memory'
ZONE = ZoneInfo('Asia/Shanghai')
KIND = 'negative-review-appeal-cases'
RETRIEVAL_CONTRACT = 'verified-appeal-memory-through-as-of-v2'
USE = 'style-only; merchant assertions are historical arguments, not verified facts; rejected/pending cases are not successful precedents'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return result.replace(tzinfo=ZONE) if result.tzinfo is None else result.astimezone(ZONE)


def _workflow_domain(state):
    need(state.get('mode') == 'draft-only', 'memory-negative-review-workflow-required')
    need(state.get('domain', KIND) == KIND and state.get('workspace_kind') in (None, 'negative-review-appeal-history-only-v1'), 'memory-workflow-domain-mismatch')


def _raw_ref(ref):
    p = Path(ref.get('path', ''))
    need(p.is_absolute() and p.is_file() and not p.is_symlink(), 'memory-original-ref-invalid')
    raw = p.read_bytes()
    need(sha(raw) == ref.get('sha256'), 'memory-original-ref-hash-mismatch')
    return raw


def _owned(root, ref):
    raw = _raw_ref(ref)
    p = Path(ref['path'])
    need(p.resolve().parent == root / 'evidence' and p.name == ref['sha256'] + '.json', 'memory-import-ref-not-owned')
    return raw, json.loads(raw)


def _local(memory, ref):
    expected = 'evidence/' + ref.get('sha256', '') + '.json'
    need(ref.get('path') == expected and len(ref.get('sha256', '')) == 64, 'memory-relative-ref-invalid')
    p = memory / expected
    need(p.is_file() and not p.is_symlink(), 'memory-evidence-missing')
    raw = p.read_bytes()
    need(sha(raw) == ref['sha256'], 'memory-evidence-hash-mismatch')
    return json.loads(raw)


def _facts(source, result, key):
    gid = str(source.get('groupid', ''))
    need(gid.isdigit() and key.startswith(gid + ':'), 'memory-group-key-mismatch')
    identity = source.get('identity')
    need(isinstance(identity, dict) and all(identity.get(k) for k in ('provider', 'account_id', 'manager')), 'memory-full-identity-required')
    need(source.get('account_verified') is True and source.get('source') in ('local-dom-bridge', 'codex-existing-extension'), 'memory-source-unverified')
    rows = [r for r in source.get('rows', []) if gid + ':' + r.get('review_id', '') == key]
    need(len(rows) == 1 and rows[0].get('stars') in (1, 2, 3), 'memory-review-not-unique-normal-negative')
    row = rows[0]
    need(row.get('section') == 'filtered' and row.get('folded') is not True, 'memory-normal-filtered-review-required')
    need(result.get('review_key') == key and result.get('source') == source['source'] and result.get('submitted_by_this_workflow') is False, 'memory-result-key-source-invalid')
    u = urlsplit(result.get('url', ''))
    need(u.scheme == 'https' and u.netloc == 'life.douyin.com' and u.path == '/p/life_comment/management' and parse_qs(u.query).get('groupid') == [gid], 'memory-result-url-mismatch')
    old = result.get('original_complaint', {})
    need(isinstance(old.get('投诉类型'), str) and 1 <= len(old['投诉类型']) <= 40, 'memory-platform-type-required')
    reason = old.get('投诉理由')
    need(isinstance(reason, str) and reason.strip() and reason in result.get('visible_text', ''), 'memory-original-reason-required')
    observed = timestamp(result.get('observed_at', ''))
    complaint = timestamp(old.get('投诉时间', ''))
    need(complaint <= observed and result.get('status') in ('accepted', 'rejected', 'pending', 'unknown'), 'memory-result-date-status-invalid')
    facts={'company': source['company'], 'groupid': gid, 'identity': identity, 'backend': source['source'], 'review_key': key,
            'review': {k: row.get(k, '') for k in ('review_id', 'store', 'customer', 'text', 'stars', 'date', 'product')},
            'platform_type': old['投诉类型'], 'complaint_at': old['投诉时间'], 'original_reason': reason,
            'original_reason_utf8_sha256': sha(reason.encode()), 'observed_at': result['observed_at'],
            'outcome': result['status'], 'platform_status': result.get('platform_status', ''),
            'original_result_text': result['visible_text']}
    if 'complaint_history' in result:
        history=result['complaint_history']
        need(result.get('report_sections_schema')=='semantic-current-history-v1' and result.get('current_report_section',{}).get('title')=='举报信息' and isinstance(history,list) and len(history)==1,'memory-history-schema-invalid')
        item=history[0];old_history=item.get('original_complaint',{})
        need(set(item)=={'title','form_selector','original_complaint','status'} and item['title']=='投诉历史' and item['status']=='unknown' and isinstance(item['form_selector'],str) and bool(item['form_selector']) and item['form_selector']!=result['current_report_section'].get('form_selector'),'memory-history-ownership-invalid')
        need(set(old_history)=={'投诉类型','投诉理由','投诉时间'} and all(isinstance(x,str) and bool(x.strip()) for x in old_history.values()) and len(old_history['投诉类型'])<=40 and old_history['投诉理由'] in result['visible_text'] and timestamp(old_history['投诉时间'])<complaint,'memory-history-fields-invalid')
        facts.update(report_sections_schema=result['report_sections_schema'],current_report_section=result['current_report_section'],complaint_history=history)
    return facts


def _case_id(facts):
    return sha(canonical({k: facts[k] for k in ('groupid', 'review_key', 'complaint_at', 'platform_type', 'original_reason_utf8_sha256')}))


def _validate(memory, record):
    need(record.get('kind') == KIND and record.get('domain') == KIND and record.get('schema_version') == 1, 'memory-record-kind-domain-invalid')
    source = _local(memory, record['source_ref'])
    result = _local(memory, record['result_ref'])
    need(result.get('snapshot_sha256') == record['source_ref']['sha256'], 'memory-source-result-binding-invalid')
    facts = _facts(source, result, record['review_key'])
    need(all(record.get(k) == v for k, v in facts.items()), 'memory-original-facts-changed')
    need(record.get('case_id') == _case_id(facts), 'memory-case-id-invalid')
    need(record.get('observation_id') == sha(canonical([record['case_id'], record['result_ref']['sha256']])), 'memory-observation-id-invalid')
    themes = record.get('themes')
    need(isinstance(themes, list) and themes and len(themes) <= 8 and len(set(themes)) == len(themes) and all(isinstance(x, str) and 1 <= len(x) <= 60 for x in themes), 'memory-themes-invalid')
    need(record.get('theme_annotation') == 'agent-labelled-feedback-topic-not-platform-finding' and record.get('use') == USE and record.get('coverage') == 'observed-cases-only-nonexhaustive' and record.get('month_query_complete') is False, 'memory-usage-claims-invalid')
    need(timestamp(record['imported_at']) >= timestamp(record['observed_at']), 'memory-import-before-observation')
    return record


def _read_unlocked(memory):
    p = memory / 'complaint-cases.jsonl'
    if not p.exists():
        return []
    need(not p.is_symlink(), 'memory-log-symlink-forbidden')
    raw = p.read_bytes()
    need(not raw or raw.endswith(b'\n'), 'memory-damaged-tail-refuse-repair')
    records = []
    seen = set()
    for line in raw.splitlines():
        need(line.strip(), 'memory-empty-record')
        record = _validate(memory, json.loads(line))
        need(record['observation_id'] not in seen, 'memory-duplicate-observation')
        seen.add(record['observation_id'])
        records.append(record)
    return records


def read_records(memory=DEFAULT_MEMORY):
    """Read without creating directories, lock files, rendering documents or mutating state."""
    memory = Path(memory).resolve()
    lock = memory / '.append.lock'
    if not lock.exists():
        return _read_unlocked(memory)
    need(not lock.is_symlink(), 'memory-lock-symlink-forbidden')
    with lock.open('rb') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        return _read_unlocked(memory)


def _write_exclusive(p, raw):
    try:
        with p.open('xb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
    except FileExistsError:
        need(p.is_file() and not p.is_symlink() and p.read_bytes() == raw, 'memory-existing-file-conflict')


def import_case(root, key, themes, *, memory=DEFAULT_MEMORY, at=None):
    root = Path(root).resolve()
    state = json.loads((root / 'state.json').read_text())
    _workflow_domain(state)
    need(state.get('mode') == 'draft-only' and state.get('browser_backend') in ('local-dom-bridge', 'codex-existing-extension'), 'memory-live-ledger-required')
    task = state['tasks'][key]
    result_record = task.get('result') or {}
    result_ref = result_record.get('evidence')
    need(isinstance(result_ref, dict), 'memory-actual-existing-result-required')
    result_raw, result = _owned(root, result_ref)
    need(result == {k: v for k, v in result_record.items() if k != 'evidence'}, 'memory-ledger-result-mismatch')
    sources = [r for r in (task.get('snapshot'), task.get('latest_snapshot')) if isinstance(r, dict) and r.get('sha256') == result.get('snapshot_sha256')]
    need(sources, 'memory-source-not-owned')
    source_ref = sources[0]
    source_raw, source = _owned(root, source_ref)
    facts = _facts(source, result, key)
    need(facts['company'] == state['company'] and facts['groupid'] == str(state['groupid']) and facts['identity'] == state['identity'] and facts['backend'] == state['browser_backend'], 'memory-ledger-identity-mismatch')
    need(all(facts['review'][k] == task['review'].get(k, '') for k in facts['review']), 'memory-ledger-review-mismatch')
    at = at or datetime.now(ZONE)
    record = {'kind': KIND, 'domain': KIND, 'schema_version': 1, **facts, 'case_id': _case_id(facts), 'themes': list(themes),
              'theme_annotation': 'agent-labelled-feedback-topic-not-platform-finding', 'use': USE,
              'coverage': 'observed-cases-only-nonexhaustive', 'month_query_complete': False, 'imported_at': at.isoformat(),
              'source_ref': {'path': 'evidence/' + source_ref['sha256'] + '.json', 'sha256': source_ref['sha256']},
              'result_ref': {'path': 'evidence/' + result_ref['sha256'] + '.json', 'sha256': result_ref['sha256']},
              'original_observation_refs': {'source': source_ref, 'result': result_ref}}
    record['observation_id'] = sha(canonical([record['case_id'], result_ref['sha256']]))
    memory = Path(memory).resolve()
    memory.mkdir(parents=True, exist_ok=True)
    lock = memory / '.append.lock'
    need(not lock.is_symlink(), 'memory-lock-symlink-forbidden')
    with lock.open('a+b') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        records = _read_unlocked(memory)  # Corruption is never silently trimmed or repaired.
        matches = [r for r in records if r['observation_id'] == record['observation_id']]
        if matches:
            need(matches[0]['themes'] == record['themes'], 'memory-existing-annotation-conflict')
            return {'appended': False, 'record': matches[0]}
        (memory / 'evidence').mkdir(exist_ok=True)
        need(not (memory / 'evidence').is_symlink(), 'memory-evidence-directory-symlink-forbidden')
        _write_exclusive(memory / record['source_ref']['path'], source_raw)
        _write_exclusive(memory / record['result_ref']['path'], result_raw)
        _validate(memory, record)
        log = memory / 'complaint-cases.jsonl'
        need(not log.is_symlink(), 'memory-log-symlink-forbidden')
        try:
            fd = os.open(log, os.O_APPEND | os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            fd = os.open(log, os.O_APPEND | os.O_WRONLY)
        with os.fdopen(fd, 'ab') as out:
            out.write(canonical(record) + b'\n')
            out.flush()
            os.fsync(out.fileno())
        dfd = os.open(memory, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        return {'appended': True, 'record': record}


# Observation-scoped reviewed themes. Raw record APIs above are intentionally unchanged.
ANNOTATION_KIND = 'appeal-use-theme-observation-annotation-v1'
ANNOTATION_APPROVAL = 'reviewed-appeal-theme-import-approval-v1'
ANNOTATION_KEYS = {'kind','binding','appeal_use_theme_codes','appeal_use_themes','comment_content_topics',
                   'classification_basis','exact_quotes','original_reason_utf8_sha256','proposal_freeze',
                   'proposal_line_sha256','proposal_log','result_ref','reuse_cautions','review_approval',
                   'source_ref','status','successful_precedent','supersedes','vocabulary'}


def _annotation_file(memory, name):
    p = memory / name
    need(not p.is_symlink(), 'annotation-file-symlink')
    raw = p.read_bytes() if p.exists() else b''
    return raw, {'path': str(p), 'sha256': sha(raw) if p.exists() else None, 'absent': not p.exists()}


def _annotation_lines(raw):
    need(not raw or raw.endswith(b'\n'), 'annotation-damaged-tail')
    lines = raw[:-1].split(b'\n') if raw else []
    need(all(lines), 'annotation-empty-line')
    return lines


def _annotation_cutoff(at, cutoff):
    if cutoff is None:
        cutoff = datetime.now(ZONE)
    need(isinstance(cutoff, date), 'annotation-as-of-invalid')
    return timestamp(at) <= timestamp(cutoff.isoformat()) if isinstance(cutoff, datetime) else timestamp(at).date() <= cutoff


def _annotation_validate(payload, approval, resolve, records, raw_lines):
    need(set(payload) == ANNOTATION_KEYS and payload['kind'] == ANNOTATION_KIND, 'annotation-payload-schema')
    need(payload['status'] == 'draft-requires-review-not-loadable' and payload['review_approval'] is None and payload['successful_precedent'] is False,
         'annotation-draft-not-authority')
    need(approval.get('kind') == ANNOTATION_APPROVAL and approval.get('domain') == KIND and
         approval.get('authorize_annotation_import') is True and approval.get('reviewer_role') == 'supervisor' and
         approval.get('decision') == 'approved-historical-reasoning-only' and approval.get('use') == USE,
         'annotation-independent-approval-required')
    need(approval.get('payload_sha256') == sha(canonical(payload)), 'annotation-approval-payload-mismatch')
    for k in ('vocabulary','proposal_log','proposal_freeze'):
        need(approval.get(k) == payload[k], 'annotation-approval-ref-mismatch')
    b = payload['binding']
    need(set(b) == {'case_id','observation_id','observation_sha256','line_hash_contract'} and
         b['line_hash_contract'] == 'sha256 of exact JSONL UTF-8 line bytes excluding line terminator', 'annotation-binding-schema')
    matches = [(r, line) for r,line in zip(records,raw_lines) if r['case_id'] == b['case_id'] and r['observation_id'] == b['observation_id']]
    need(len(matches) == 1 and sha(matches[0][1]) == b['observation_sha256'], 'annotation-exact-observation-required')
    record = matches[0][0]
    need(timestamp(record['observed_at']) <= timestamp(approval['reviewed_at']), 'annotation-review-before-observation')
    need(payload['source_ref'] == record['source_ref'] and payload['result_ref'] == record['result_ref'] and
         payload['original_reason_utf8_sha256'] == record['original_reason_utf8_sha256'], 'annotation-original-binding-changed')
    vocabulary = json.loads(resolve(payload['vocabulary']))
    need(vocabulary.get('schema') == 'appeal-theme-proposal-v1' and vocabulary.get('domain') == KIND, 'annotation-vocabulary-domain')
    vocab = vocabulary['vocabulary']
    need(isinstance(vocab,list) and 1 <= len(vocab) <= 100 and all(set(x) == {'code','label','definition'} for x in vocab), 'annotation-vocabulary-shape')
    bycode = {x['code']:x['label'] for x in vocab}
    need(len(bycode) == len(vocab) and len(set(bycode.values())) == len(vocab), 'annotation-vocabulary-duplicate')
    codes = payload['appeal_use_theme_codes']
    need(isinstance(codes,list) and 1 <= len(codes) <= 8 and len(set(codes)) == len(codes) and all(x in bycode for x in codes), 'annotation-unknown-theme')
    need(payload['appeal_use_themes'] == [bycode[x] for x in codes], 'annotation-theme-label-mismatch')
    for k in ('comment_content_topics','reuse_cautions'):
        value=payload[k]
        need(isinstance(value,list) and 1 <= len(value) <= 12 and len(set(value)) == len(value) and
             all(isinstance(x,str) and 1 <= len(x) <= 600 for x in value), 'annotation-topics-or-cautions-invalid')
    need(isinstance(payload['classification_basis'],str) and 1 <= len(payload['classification_basis']) <= 1200, 'annotation-basis-invalid')
    quotes=payload['exact_quotes']
    need(isinstance(quotes,list) and 1 <= len(quotes) <= 8, 'annotation-quotes-invalid')
    for q in quotes:
        need(set(q)=={'field','text'} and q['field'] in ('review.text','original_reason') and isinstance(q['text'],str) and
             1 <= len(q['text']) <= 1000, 'annotation-quote-field-invalid')
        value=record['review']['text'] if q['field']=='review.text' else record['original_reason']
        need(q['text'] in value, 'annotation-quote-not-original')
    proposal_lines=_annotation_lines(resolve(payload['proposal_log']))
    proposals=[json.loads(x) for x in proposal_lines if sha(x)==payload['proposal_line_sha256']]
    need(len(proposals)==1, 'annotation-proposal-line-missing')
    p=proposals[0]
    values={'case_id':b['case_id'],'observation_id':b['observation_id'],'observation_sha256':b['observation_sha256'],
            'company':record['company'],'platform_appeal_type_unchanged':record['platform_type'],'outcome_unchanged':record['outcome'],
            'recommended_themes':payload['appeal_use_themes'],'recommended_theme_codes':codes,
            'comment_content_topics':payload['comment_content_topics'],'classification_basis':payload['classification_basis'],
            'exact_quotes':quotes,'reuse_cautions':payload['reuse_cautions'],'successful_precedent':False,
            'original_reason_utf8_sha256':payload['original_reason_utf8_sha256'],
            'source_ref_unchanged':record['source_ref'],'result_ref_unchanged':record['result_ref']}
    need(all(p.get(k)==v for k,v in values.items()), 'annotation-proposal-facts-mismatch')
    freeze=json.loads(resolve(payload['proposal_freeze']))
    need(freeze.get('schema')=='appeal-theme-candidate-freeze-v1', 'annotation-freeze-schema')
    need(all(x in freeze.get('files',[]) for x in (payload['vocabulary'],payload['proposal_log'])), 'annotation-freeze-not-pinned')
    return record


def _annotation_snapshot_unlocked(memory):
    records=_read_unlocked(memory)  # Existing complete source/result validator remains mandatory.
    case_raw,case_ref=_annotation_file(memory,'complaint-cases.jsonl')
    raw_lines=_annotation_lines(case_raw)
    need(len(raw_lines)==len(records), 'annotation-case-frontier-mismatch')
    raw,log_ref=_annotation_file(memory,'theme-annotations.jsonl')
    annotations=[]; ids=set(); active={}
    for line in _annotation_lines(raw):
        a=json.loads(line)
        need(set(a)=={'kind','domain','annotation_id','payload','approval','artifacts'} and a['kind']=='reviewed-appeal-theme-annotation-v1' and a['domain']==KIND,
             'annotation-log-schema')
        artifacts=a['artifacts']
        need(isinstance(artifacts,dict) and len(artifacts)==5, 'annotation-artifact-count')
        def resolve(ref):
            need(isinstance(ref,dict) and set(ref)=={'path','sha256'} and ref['sha256'] in artifacts, 'annotation-ref-unpinned')
            local=artifacts[ref['sha256']]
            need(local=={'path':'evidence/'+ref['sha256']+'.json','sha256':ref['sha256']}, 'annotation-local-ref-invalid')
            p=memory/local['path'];need(not p.parent.is_symlink() and not p.is_symlink() and p.is_file(), 'annotation-evidence-missing')
            value=p.read_bytes();need(sha(value)==ref['sha256'], 'annotation-evidence-hash-mismatch');return value
        need(all(a[k] == artifacts.get(a[k].get('sha256')) for k in ('payload','approval')), 'annotation-wrapper-ref-mismatch')
        payload=json.loads(resolve(a['payload']));approval=json.loads(resolve(a['approval']))
        record=_annotation_validate(payload,approval,resolve,records,raw_lines)
        need(a['annotation_id']==sha(canonical([sha(canonical(payload)),a['approval']['sha256']])) and a['annotation_id'] not in ids,
             'annotation-id-or-duplicate')
        ids.add(a['annotation_id']);key=(record['case_id'],record['observation_id'])
        prior=active.get(key)
        need(payload['supersedes']==(prior['annotation_id'] if prior else None), 'annotation-supersedes-mismatch')
        if prior:
            need(timestamp(approval['reviewed_at'])>timestamp(prior['reviewed_at']) and a['approval']['sha256']!=prior['approval_ref']['sha256'], 'annotation-new-review-required')
        entry={'annotation_id':a['annotation_id'],'payload':payload,'reviewed_at':approval['reviewed_at'],'approval_ref':a['approval'],
               'vocabulary_ref':artifacts[payload['vocabulary']['sha256']],
               'proposal_ref':artifacts[payload['proposal_log']['sha256']],'freeze_ref':artifacts[payload['proposal_freeze']['sha256']]}
        active[key]=entry;annotations.append(entry)
    return records,raw_lines,annotations,{'case_log':case_ref,'annotation_log':log_ref}


def read_memory_view(*, memory=DEFAULT_MEMORY, as_of=None):
    """Validated raw originals plus observation-scoped deep-copy theme views; never writes."""
    from copy import deepcopy
    memory=Path(memory).resolve();lock=memory/'.append.lock'
    def read():return _annotation_snapshot_unlocked(memory)
    if lock.exists():
        need(not lock.is_symlink(),'memory-lock-symlink-forbidden')
        with lock.open('rb') as f:
            fcntl.flock(f.fileno(),fcntl.LOCK_SH);records,_,annotations,receipt=read()
    else:
        need(not lock.is_symlink(),'memory-lock-symlink-forbidden');records,_,annotations,receipt=read()
    active={}
    for a in annotations:
        if _annotation_cutoff(a['reviewed_at'],as_of):active[(a['payload']['binding']['case_id'],a['payload']['binding']['observation_id'])]=a
    views=[]
    for raw in records:
        v=deepcopy(raw);v['original_themes']=deepcopy(raw['themes']);a=active.get((raw['case_id'],raw['observation_id']))
        v.update(classification_status='needs-review',appeal_use_themes=[],comment_content_topics=[],reviewed_theme_annotation=None)
        if a and _annotation_cutoff(raw['observed_at'],as_of):
            v.update(classification_status='reviewed-observation-annotation',appeal_use_themes=deepcopy(a['payload']['appeal_use_themes']),
                     comment_content_topics=deepcopy(a['payload']['comment_content_topics']),
                     reviewed_theme_annotation=deepcopy({k:a[k] for k in ('annotation_id','reviewed_at','approval_ref','vocabulary_ref','proposal_ref','freeze_ref')}),
                     theme_reuse_cautions=deepcopy(a['payload']['reuse_cautions']))
        views.append(v)
    return views,deepcopy(receipt)


def import_theme_annotation(payload, approval_ref, *, memory=DEFAULT_MEMORY):
    """Explicit supervisor-approved data import; no UI or raw case changes.

    The caller must provide an independently approved, exact SHA-pinned review.
    The existing semantic-direction-only review is not an import authorization.
    """
    from copy import deepcopy
    payload=deepcopy(payload);approval_raw=_raw_ref(approval_ref);approval=json.loads(approval_raw)
    need(approval.get('kind')==ANNOTATION_APPROVAL and approval.get('authorize_annotation_import') is True,
         'annotation-independent-approval-required')
    # Every external file is pinned before touching storage. Copy all needed data for portability.
    blobs={sha(canonical(payload)):canonical(payload),approval_ref['sha256']:approval_raw}
    for k in ('vocabulary','proposal_log','proposal_freeze'):
        value=_raw_ref(payload[k]);blobs[payload[k]['sha256']]=value
    def external(ref):
        need(ref['sha256'] in blobs,'annotation-ref-unpinned');return blobs[ref['sha256']]
    memory=Path(memory).resolve();memory.mkdir(parents=True,exist_ok=True);lock=memory/'.append.lock'
    need(not lock.is_symlink(),'memory-lock-symlink-forbidden')
    with lock.open('a+b') as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX)
        records,raw_lines,prior,_=_annotation_snapshot_unlocked(memory)
        _annotation_validate(payload,approval,external,records,raw_lines)
        ident=sha(canonical([sha(canonical(payload)),approval_ref['sha256']]))
        if any(a['annotation_id']==ident for a in prior):return {'appended':False,'annotation_id':ident}
        key=(payload['binding']['case_id'],payload['binding']['observation_id'])
        old=[a for a in prior if (a['payload']['binding']['case_id'],a['payload']['binding']['observation_id'])==key]
        need(payload['supersedes']==(old[-1]['annotation_id'] if old else None),'annotation-supersedes-mismatch')
        if old:need(timestamp(approval['reviewed_at'])>timestamp(old[-1]['reviewed_at']) and approval_ref['sha256']!=old[-1]['approval_ref']['sha256'],'annotation-new-review-required')
        evidence=memory/'evidence';evidence.mkdir(exist_ok=True);need(not evidence.is_symlink(),'memory-evidence-directory-symlink-forbidden')
        artifacts={}
        for h,value in blobs.items():
            _write_exclusive(evidence/(h+'.json'),value);artifacts[h]={'path':'evidence/'+h+'.json','sha256':h}
        annotation={'kind':'reviewed-appeal-theme-annotation-v1','domain':KIND,'annotation_id':ident,
                    'payload':{'path':'evidence/'+sha(canonical(payload))+'.json','sha256':sha(canonical(payload))},
                    'approval':{'path':'evidence/'+approval_ref['sha256']+'.json','sha256':approval_ref['sha256']},'artifacts':artifacts}
        log=memory/'theme-annotations.jsonl';need(not log.is_symlink(),'annotation-file-symlink')
        try:fd=os.open(log,os.O_APPEND|os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:fd=os.open(log,os.O_APPEND|os.O_WRONLY)
        with os.fdopen(fd,'ab') as out:out.write(canonical(annotation)+b'\n');out.flush();os.fsync(out.fileno())
        dfd=os.open(memory,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)
        return {'appended':True,'annotation_id':ident}


def load_for_workflow(state, key=None, *, memory=DEFAULT_MEMORY, as_of=None, days=30):
    """Read-only knowledge retrieval, independent of business date/cursor.

    None: through the current instant. Datetime: through that explicit instant
    (naive values use Shanghai). Date: the entire named Shanghai calendar day.
    The last `days` calendar dates include the cutoff day; only observations
    available by that cutoff participate, before selecting latest case status.
    This never asserts complete platform history or changes a business range.
    """
    empty = {'domain': KIND, 'coverage': 'observed-cases-only-nonexhaustive', 'month_query_complete': False, 'use': USE, 'is_exhaustive': False,
             'case_count': 0, 'archived_case_count': 0, 'cases': [], 'outcomes': {}, 'refs': []}
    if state.get('mode') == 'fixture':
        return {**empty, 'fixture_isolated': True}
    _workflow_domain(state)
    need(isinstance(days, int) and 1 <= days <= 366, 'memory-window-invalid')
    cutoff = datetime.now(ZONE) if as_of is None else as_of
    need(isinstance(cutoff, date), 'memory-as-of-invalid')
    instant_mode = isinstance(cutoff, datetime)
    if instant_mode:
        cutoff = cutoff.replace(tzinfo=ZONE) if cutoff.tzinfo is None else cutoff.astimezone(ZONE)
        day = cutoff.date()
    else:
        day = cutoff
    start = day - timedelta(days=days - 1)
    end = day + timedelta(days=1)
    def available(value):
        at = timestamp(value)
        return at <= cutoff if instant_mode else at.date() < end
    need(key is None or key in state.get('tasks', {}), 'memory-target-not-owned')
    records, theme_receipt = read_memory_view(memory=memory, as_of=cutoff)
    company = [r for r in records if r['company'] == state['company'] and r['groupid'] == str(state['groupid'])]
    if state.get('identity'):
        need(all(r['identity'] == state['identity'] for r in company), 'memory-current-identity-conflict')
    latest = {}
    for r in company:
        if not available(r['observed_at']) or not available(r['complaint_at']):
            continue
        prev = latest.get(r['case_id'])
        if prev is None or timestamp(r['observed_at']) > timestamp(prev['observed_at']):
            latest[r['case_id']] = r
    related = sorted((r for r in latest.values() if start <= timestamp(r['complaint_at']).date() < end and r['review_key'] != key), key=lambda r: (r['complaint_at'], r['case_id']))
    refs = [{'case_id': r['case_id'], 'source': r['source_ref'], 'result': r['result_ref']} for r in related]
    summaries = [{k: r[k] for k in ('case_id', 'review_key', 'platform_type', 'themes', 'complaint_at', 'outcome', 'observed_at', 'original_themes', 'classification_status', 'appeal_use_themes', 'comment_content_topics', 'reviewed_theme_annotation')} for r in related]
    from appeal_history_coverage import summary as coverage_summary
    return {**empty, 'history_scope_coverage': coverage_summary(memory=memory,company=state['company'],groupid=state['groupid'],as_of=cutoff), 'retrieval_contract': RETRIEVAL_CONTRACT,
            'as_of_mode': 'instant-inclusive' if instant_mode else 'calendar-day-inclusive',
            'as_of': cutoff.isoformat(), 'observation_time_field': 'observed_at',
            'business_date_range_used': False, 'calendar_days_include_as_of_day': True,
            'start': start.isoformat(), 'end_exclusive': end.isoformat(), 'days': days,
            'memory_root': str(Path(memory).resolve()), 'case_count': len(related), 'archived_case_count': len(latest),
            'observation_count': len(company), 'outcomes': dict(Counter(r['outcome'] for r in related)),
            'cases': related if key is not None else summaries, 'refs': refs,
            'theme_loading_receipt': {**theme_receipt, 'used_annotations': [r['reviewed_theme_annotation'] for r in related if r['reviewed_theme_annotation']]}}


def auto_import(root, key, themes=None, *, memory=DEFAULT_MEMORY):
    """After record_result persists: append real originals, preserving prior AI themes."""
    state = json.loads((Path(root) / 'state.json').read_text())
    if state.get('mode') == 'fixture':
        return {'skipped': True, 'reason': 'fixture-isolated'}
    _workflow_domain(state)
    task = state['tasks'][key]
    need(task.get('result', {}).get('original_complaint'), 'memory-actual-original-complaint-required')
    if themes is None:
        prior = [r for r in read_records(memory) if r['review_key'] == key and r['company'] == state['company'] and r['groupid'] == str(state['groupid'])
                 and r['result_ref']['sha256'] == task['result'].get('evidence', {}).get('sha256')
                 and r['source_ref']['sha256'] == task['result'].get('snapshot_sha256')]
        prior.sort(key=lambda r: timestamp(r['observed_at']))
        themes = prior[-1]['themes'] if prior else ['待归类']
    return import_case(root, key, themes, memory=memory)


def render_document(out, *, memory=DEFAULT_MEMORY, as_of=None):
    day = as_of or datetime.now(ZONE).date()
    records, theme_receipt = read_memory_view(memory=memory, as_of=day)
    records = [r for r in records if timestamp(r['observed_at']).date() <= day]
    latest = {}
    for r in records:
        if r['case_id'] not in latest or timestamp(r['observed_at']) > timestamp(latest[r['case_id']]['observed_at']):
            latest[r['case_id']] = r
    labels = {'accepted': '投诉通过', 'rejected': '投诉未通过', 'pending': '平台审核中', 'unknown': '结果未知'}
    lines = ['# 差评申诉案例库', '', f'生成日期：{day}。领域仅限差评申诉。仅收录实际读过、原始证据已核验的案例；最近30天全量查询尚未完成。', '',
             '原投诉理由中的商家说法仅是历史申诉方主张，不是本流程核实事实。未通过和待审案例不可作为成功范本；后续只能借鉴表达结构，不能移植其事实或指控。', '']
    for company in sorted({r['company'] for r in latest.values()}):
        lines.extend(['## ' + company, ''])
        for category in sorted({r['platform_type'] for r in latest.values() if r['company'] == company}):
            lines.extend(['### 平台申诉类型：' + category, ''])
            items = sorted((r for r in latest.values() if r['company'] == company and r['platform_type'] == category), key=lambda r: (tuple(r['appeal_use_themes'] or r['themes']), r['case_id']))
            for r in items:
                current = day - timedelta(days=29) <= timestamp(r['complaint_at']).date() <= day
                lines.extend(['#### ' + ' / '.join(r['appeal_use_themes'] or r['themes']), '',
                              f"{r['review']['store']}｜{r['review']['customer']}｜{r['review']['stars']}心｜{labels[r['outcome']]}｜{'当前30日窗口' if current else '长期旧档'}", '',
                              f"投诉时间：{r['complaint_at']}；读取时间：{r['observed_at']}；案例：`{r['case_id']}`。", '',
                              '评价原文：', '', '> ' + r['review']['text'].replace('\n', '\n> '), '', '投诉理由原文：', '',
                              '> ' + r['original_reason'].replace('\n', '\n> '), '', '平台结果原文：', '',
                              '> ' + r['original_result_text'].replace('\n', '\n> '), '',
                              f"证据：source `{r['source_ref']['path']}` SHA256 `{r['source_ref']['sha256']}`；result `{r['result_ref']['path']}` SHA256 `{r['result_ref']['sha256']}`。", ''])
                if r['reviewed_theme_annotation']:
                    lines.extend(['主题状态：已审当前观察；申诉用途主题与原平台类型独立。原记录主题：'+' / '.join(r['original_themes'])+'；评论内容主题：'+' / '.join(r['comment_content_topics'])+'。', '',
                                  '分类证据：'+json.dumps(r['reviewed_theme_annotation'],ensure_ascii=False,sort_keys=True), ''])
                else:
                    lines.extend(['主题状态：待评审当前观察；原记录主题仅作历史标注，不作为已审分类。', ''])
                for entry in r.get('complaint_history',[]):
                    old=entry['original_complaint']
                    lines.extend(['历史申诉（未观察独立结果；不继承当前结果）：', '',
                                  '投诉类型：'+old['投诉类型']+'；投诉时间：'+old['投诉时间'], '',
                                  '> '+old['投诉理由'].replace('\n','\n> '), ''])

    from appeal_history_coverage import summary as coverage_summary
    coverage = coverage_summary(memory=memory)
    out = Path(out)
    if coverage['audits']:
        lines.extend(['## 历史查询覆盖观察', '', '评价时间不是投诉时间，评价状态为顾客可见性。已查公开菜单未发现独立申诉历史入口；成功移除/隐藏记录及更早评价的本月申诉尚未证明覆盖，已归档案例数不是公司全月总量。', ''])
        for audit in coverage['audits']:
            target = os.path.relpath(Path(memory).resolve()/audit['audit_ref']['path'],out.resolve().parent)
            lines.append(audit['company']+'｜'+audit['observed_at']+'｜[原始范围审计]('+target+')；其他公司未查情况以该审计为准。')
        lines.append('')
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = ('\n'.join(lines) + '\n').encode()
    if not out.exists() or out.read_bytes() != raw:
        pending = out.with_name(out.name + '.pending-' + str(os.getpid()))
        _write_exclusive(pending, raw)
        os.replace(pending, out)
    return {'cases': len(latest), 'observations': len(records), 'path': str(out.resolve()), 'sha256': sha(raw), 'theme_loading_receipt': theme_receipt}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--memory', default=str(DEFAULT_MEMORY))
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('import'); p.add_argument('--root', required=True); p.add_argument('--id', required=True); p.add_argument('--theme', action='append', required=True)
    p = sub.add_parser('render'); p.add_argument('--out', default=str(SKILL / 'references/投诉案例记忆.md'))
    p = sub.add_parser('import-theme'); p.add_argument('--payload', required=True); p.add_argument('--approval', required=True); p.add_argument('--approval-sha256', required=True)
    p = sub.add_parser('load'); p.add_argument('--root', required=True); p.add_argument('--id')
    a = ap.parse_args()
    try:
        if a.command == 'import-theme':
            result = import_theme_annotation(json.loads(Path(a.payload).read_text()), {'path': str(Path(a.approval).resolve()), 'sha256': a.approval_sha256}, memory=a.memory)
        elif a.command == 'import':
            result = import_case(a.root, a.id, a.theme, memory=a.memory)
        elif a.command == 'render':
            result = render_document(a.out, memory=a.memory)
        else:
            result = load_for_workflow(json.loads((Path(a.root) / 'state.json').read_text()), a.id, memory=a.memory)
        print(json.dumps({'ok': True, **result}, ensure_ascii=False)); return 0
    except (ValueError, KeyError, OSError, TypeError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
