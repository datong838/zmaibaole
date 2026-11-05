"""Offline evidence fixtures only; no browser, messenger or real memory reads."""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import case_memory as m


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'ledger'; (self.root / 'evidence').mkdir(parents=True)
        self.memory = self.base / 'memory'; self.key = '123:review'
        self.at = datetime.fromisoformat('2026-10-21T15:00:00+08:00')
        identity = {'provider': '服务商123', 'account_id': '111', 'manager': '经理'}
        row = {'review_id': 'review', 'store': '测试店', 'customer': '某顾客', 'text': '不是很甜\n口味一般', 'stars': 1, 'date': '2026-10-19', 'product': '水果', 'section': 'filtered'}
        self.source = self.pin({'company': '测试公司', 'groupid': '123', 'source': 'local-dom-bridge', 'identity': identity, 'account_verified': True, 'rows': [row]})
        self.result = {'review_key': self.key, 'snapshot_sha256': self.source['sha256'], 'source': 'local-dom-bridge', 'url': 'https://life.douyin.com/p/life_comment/management?groupid=123', 'status': 'rejected', 'platform_status': '投诉失败', 'observed_at': '2026-10-21T09:00:00+08:00', 'submitted_by_this_workflow': False, 'visible_text': '投诉失败\n原投诉方请求平台核实\n投诉类型：其他', 'original_complaint': {'投诉类型': '其他', '投诉时间': '2026-10-20 10:00:00', '投诉理由': '原投诉方请求平台核实'}}
        resultref = self.pin(self.result)
        self.state = {'mode': 'draft-only', 'company': '测试公司', 'groupid': '123', 'browser_backend': 'local-dom-bridge', 'identity': identity, 'tasks': {self.key: {'review': row, 'snapshot': self.source, 'latest_snapshot': self.source, 'result': {**self.result, 'evidence': resultref}}}}
        self.persist()

    def pin(self, value):
        raw = json.dumps(value, ensure_ascii=False).encode(); sha = hashlib.sha256(raw).hexdigest(); p = self.root / 'evidence' / (sha + '.json'); p.write_bytes(raw)
        return {'path': str(p), 'sha256': sha}

    def persist(self):
        (self.root / 'state.json').write_text(json.dumps(self.state, ensure_ascii=False))

    def insert(self):
        return m.import_case(self.root, self.key, ['口味反馈'], memory=self.memory, at=self.at)

    def load(self, key=None, **kwargs):
        return m.load_for_workflow(self.state, key, memory=self.memory, as_of=date(2026, 10, 21), **kwargs)

    def test_import_full_original_and_idempotent_read_does_not_write(self):
        result = self.insert(); self.assertTrue(result['appended'])
        log = self.memory / 'complaint-cases.jsonl'; raw = log.read_bytes(); stamp = log.stat().st_mtime_ns
        self.assertFalse(self.insert()['appended']); self.assertEqual(self.load()['outcomes'], {'rejected': 1})
        self.assertEqual(log.read_bytes(), raw); self.assertEqual(log.stat().st_mtime_ns, stamp)
        record = m.read_records(self.memory)[0]; self.assertEqual(record['original_reason'], self.result['original_complaint']['投诉理由']); self.assertEqual(record['review']['text'], '不是很甜\n口味一般')
        self.assertFalse(self.load()['is_exhaustive']); self.assertIn('historical arguments', self.load()['use'])

    def test_portable_copies_verify_without_original_ledger(self):
        self.insert(); moved = self.base / 'relocated'; shutil.copytree(self.memory, moved); shutil.rmtree(self.root)
        records = m.read_records(moved); self.assertEqual(len(records), 1); self.assertEqual(records[0]['outcome'], 'rejected')

    def test_fixtures_do_not_even_touch_default_library(self):
        with patch.object(m, 'read_records', side_effect=AssertionError('fixture read')):
            self.assertTrue(m.load_for_workflow({'mode': 'fixture'})['fixture_isolated'])

    def test_corrupt_tail_and_tampered_copies_refuse_not_repair(self):
        self.insert(); log = self.memory / 'complaint-cases.jsonl'; raw = log.read_bytes(); log.write_bytes(raw + b'{bad')
        with self.assertRaisesRegex(ValueError, 'damaged-tail'): self.insert()
        self.assertEqual(log.read_bytes(), raw + b'{bad'); log.write_bytes(raw)
        record = m.read_records(self.memory)[0]; (self.memory / record['result_ref']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'evidence-hash'): m.read_records(self.memory)

    def test_unknown_or_changed_ledger_facts_reject_import(self):
        for change in ('identity', 'review', 'reason'):
            before = copy.deepcopy(self.state)
            if change == 'identity': self.state['identity']['manager'] = '他人'
            if change == 'review': self.state['tasks'][self.key]['review']['text'] = '改写了原文'
            if change == 'reason': self.state['tasks'][self.key]['result']['original_complaint']['投诉理由'] = '伪造理由'
            self.persist()
            with self.assertRaises(ValueError): self.insert()
            self.state = before

    def test_concurrent_duplicate_append_is_one_record(self):
        with ThreadPoolExecutor(max_workers=4) as pool: values = list(pool.map(lambda _: self.insert(), range(4)))
        self.assertEqual(sum(v['appended'] for v in values), 1); self.assertEqual(len(m.read_records(self.memory)), 1)

    def test_outcome_change_appends_new_observation_keeps_old_text(self):
        self.insert(); task = self.state['tasks'][self.key]; result = copy.deepcopy(self.result); result.update(status='accepted', platform_status='投诉通过', observed_at='2026-10-21T10:00:00+08:00'); task['result'] = {**result, 'evidence': self.pin(result)}; self.persist()
        self.assertTrue(self.insert()['appended']); records = m.read_records(self.memory); self.assertEqual(len(records), 2); self.assertEqual(records[0]['outcome'], 'rejected'); self.assertEqual(records[0]['case_id'], records[1]['case_id']); self.assertEqual(self.load()['outcomes'], {'accepted': 1})

    def test_window_archive_company_isolation_and_complete_related_original(self):
        self.insert(); self.state['tasks']['123:new'] = {}
        data = self.load('123:new'); self.assertEqual(data['cases'][0]['original_reason'], self.result['original_complaint']['投诉理由'])
        old = m.load_for_workflow(self.state, memory=self.memory, as_of=date(2026, 12, 1)); self.assertEqual(old['case_count'], 0); self.assertEqual(old['archived_case_count'], 1)
        foreign = copy.deepcopy(self.state); foreign.update(company='另一公司', groupid='999'); self.assertEqual(m.load_for_workflow(foreign, memory=self.memory)['case_count'], 0)

    def test_document_full_reasons_status_and_repeat_render_stable(self):
        self.insert(); out = self.base / 'memory.md'; result = m.render_document(out, memory=self.memory, as_of=date(2026, 10, 21)); raw = out.read_bytes(); stamp = out.stat().st_mtime_ns
        self.assertIn(self.result['original_complaint']['投诉理由'], out.read_text()); self.assertIn('投诉未通过', out.read_text()); self.assertIn('不是本流程核实事实', out.read_text()); self.assertEqual(result['cases'], 1)
        m.render_document(out, memory=self.memory, as_of=date(2026, 10, 21)); self.assertEqual(out.read_bytes(), raw); self.assertEqual(out.stat().st_mtime_ns, stamp)

    def test_auto_import_appends_new_unknown_theme_preserves_existing_theme_and_fixture_isolation(self):
        self.insert(); self.assertFalse(m.auto_import(self.root, self.key, memory=self.memory)['appended'])
        self.assertEqual(m.read_records(self.memory)[0]['themes'], ['口味反馈'])
        empty = self.base / 'new-memory'; self.assertEqual(m.auto_import(self.root, self.key, memory=empty)['record']['themes'], ['待归类'])
        self.state['mode'] = 'fixture'; self.persist()
        with patch.object(m, 'read_records', side_effect=AssertionError('fixture reads')):
            self.assertTrue(m.auto_import(self.root, self.key, memory=self.base / 'must-not-exist')['skipped'])
        self.assertFalse((self.base / 'must-not-exist').exists())

    def test_wrong_domain_is_not_reinterpreted_as_appeal_memory(self):
        self.insert(); log = self.memory / 'complaint-cases.jsonl'; r = json.loads(log.read_text()); r['domain'] = 'violation'; log.write_bytes(m.canonical(r) + b'\n')
        with self.assertRaisesRegex(ValueError, 'kind-domain'): m.read_records(self.memory)

    def test_violation_or_daily_caller_cannot_load_or_import_appeal_memory(self):
        self.insert()
        for change in [{'mode':'development'},{'domain':'violation'},{'workspace_kind':'daily-comment-stats'}]:
            state={**self.state,**change}
            with patch.object(m,'read_records',side_effect=AssertionError('foreign caller must fail before reading')):
                with self.assertRaisesRegex(ValueError,'workflow-required|domain-mismatch'):m.load_for_workflow(state,memory=self.memory)
            (self.root/'state.json').write_text(json.dumps(state,ensure_ascii=False))
            with self.assertRaisesRegex(ValueError,'workflow-required|domain-mismatch'):self.insert()
        self.persist()

    def test_violation_route_result_cannot_be_imported_as_appeal_original(self):
        result=copy.deepcopy(self.result);result['url']='https://life.douyin.com/p/governance/violation_list?groupid=123';task=self.state['tasks'][self.key];task['result']={**result,'evidence':self.pin(result)};self.persist()
        with self.assertRaisesRegex(ValueError,'result-url-mismatch'):self.insert()

    def test_workflow_result_automatically_imports_then_plan_summary_and_order_full_original(self):
        import workflow as w
        task = self.state['tasks'][self.key]
        task.update(action='查看投诉结果', status='existing_pending', screenshot=None, wecom=None, history=None)
        self.state.update(next_start='2026-10-20', batches={}, events=[])
        task['result'] = None; self.persist()
        resultfile = self.base / 'result.json'; resultfile.write_text(json.dumps(self.result, ensure_ascii=False))
        original_import, original_load, original_render = m.auto_import, m.load_for_workflow, m.render_document
        def persist(root, state, event):
            self.persist(); return state
        with patch.object(w, 'save', side_effect=persist), patch.object(w, 'shanghai_today', return_value=date(2026, 10, 21)), \
             patch.object(m, 'auto_import', side_effect=lambda root,key: original_import(root,key,memory=self.memory)) as imported, \
             patch.object(m, 'render_document', side_effect=lambda out: original_render(self.base/'generated.md',memory=self.memory)) as rendered, \
             patch.object(m, 'load_for_workflow', side_effect=lambda state,key=None,**kw: original_load(state,key,memory=self.memory,as_of=kw.get('as_of',date(2026,10,21)))):
            w.record_result(self.root, self.state, self.key, resultfile)
            self.assertEqual(imported.call_count, 1); self.assertEqual(rendered.call_count, 1)
            self.assertEqual(w.plan(self.state, '2026-10-21')['appeal_case_memory']['outcomes'], {'rejected': 1})
            newkey = '123:new'; self.state['tasks'][newkey] = {**copy.deepcopy(task), 'review': {**task['review'], 'review_id': 'new'}}
            order = w.analysis_order(self.state, newkey)
            self.assertEqual(order['appeal_case_memory']['cases'][0]['original_reason'], self.result['original_complaint']['投诉理由'])
            w.record_result(self.root, self.state, self.key, resultfile)
            self.assertEqual(rendered.call_count, 1)  # Same observation never rewrites the doc.
        self.assertTrue((self.base/'generated.md').exists())

    def test_missing_normal_section_cannot_enter_portable_library(self):
        src = json.loads(Path(self.source['path']).read_text()); src['rows'][0].pop('section')
        result = copy.deepcopy(self.result); ref = self.pin(src); result['snapshot_sha256'] = ref['sha256']
        task = self.state['tasks'][self.key]; task.update(snapshot=ref, latest_snapshot=ref, result={**result,'evidence':self.pin(result)}); self.persist()
        with self.assertRaisesRegex(ValueError, 'normal-filtered-review'): self.insert()


    def set_result_dates(self, complaint_at, observed_at, *, status='rejected'):
        result = copy.deepcopy(self.result)
        result['original_complaint']['投诉时间'] = complaint_at
        result.update(observed_at=observed_at, status=status)
        self.state['tasks'][self.key]['result'] = {**result, 'evidence': self.pin(result)}
        self.persist()

    def test_same_day_verified_case_is_immediately_available_in_default_memory(self):
        self.set_result_dates('2026-10-21 10:00:00', '2026-10-21T10:30:00+08:00')
        self.insert()
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None): return cls.fromisoformat('2026-10-21T11:00:00+08:00')
        with patch.object(m, 'datetime', Clock):
            loaded = m.load_for_workflow(self.state, memory=self.memory)
        self.assertEqual(loaded['case_count'], 1)
        self.assertEqual(loaded['retrieval_contract'], 'verified-appeal-memory-through-as-of-v2')
        self.assertEqual(loaded['as_of_mode'], 'instant-inclusive')
        self.assertFalse(loaded['month_query_complete'])
        self.assertFalse(loaded['business_date_range_used'])
        self.assertEqual(self.load()['case_count'], 1)  # Explicit date includes its whole day.

    def test_future_complaint_or_observation_is_not_loaded(self):
        self.at = datetime.fromisoformat('2026-10-23T15:00:00+08:00')
        for complaint, observation in [('2026-10-22 10:00:00','2026-10-22T11:00:00+08:00'),
                                        ('2026-10-21 10:00:00','2026-10-22T10:00:00+08:00')]:
            with self.subTest(complaint=complaint, observation=observation):
                self.set_result_dates(complaint, observation);self.insert()
                self.assertEqual(self.load()['case_count'], 0)
                shutil.rmtree(self.memory)

    def test_explicit_instant_ignores_future_status_before_latest_selection(self):
        self.insert()
        self.set_result_dates('2026-10-20 10:00:00','2026-10-21T14:00:00+08:00',status='accepted')
        self.insert()
        earlier = m.load_for_workflow(self.state,memory=self.memory,as_of=datetime.fromisoformat('2026-10-21T12:00:00+08:00'))
        self.assertEqual(earlier['outcomes'], {'rejected': 1})
        self.assertEqual(self.load()['outcomes'], {'accepted': 1})
        self.assertEqual(earlier['observation_time_field'], 'observed_at')

    def test_knowledge_window_includes_today_and_preserves_business_scope_and_domain(self):
        self.set_result_dates('2026-10-21 10:00:00','2026-10-21T10:30:00+08:00');self.insert()
        self.state.update(next_start='2026-09-21',covered_through='2026-10-20',last_completed_on='2026-10-21',batches={'2026-09-21_2026-10-21':{'start':'2026-09-21','end_exclusive':'2026-10-21'}})
        before=copy.deepcopy(self.state);loaded=self.load(days=30)
        self.assertEqual((loaded['start'],loaded['end_exclusive']),('2026-09-22','2026-10-22'))
        self.assertEqual(self.state,before)
        foreign={**self.state,'company':'另一公司','groupid':'999'}
        self.assertEqual(m.load_for_workflow(foreign,memory=self.memory,as_of=date(2026,10,21))['case_count'],0)
        with patch.object(m,'read_records',side_effect=AssertionError('foreign domain read')):
            with self.assertRaisesRegex(ValueError,'domain-mismatch'):
                m.load_for_workflow({**self.state,'domain':'violation'},memory=self.memory,as_of=date(2026,10,21))

    def test_plan_business_date_does_not_limit_current_knowledge(self):
        import workflow as w
        self.set_result_dates('2026-10-21 10:00:00','2026-10-21T10:30:00+08:00');self.insert()
        self.state['tasks'][self.key].update(status='existing_pending',screenshot=None,wecom=None)
        self.state.update(next_start='2026-09-21',batches={},events=[])
        before=copy.deepcopy(self.state);original_load=m.load_for_workflow
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None):return cls.fromisoformat('2026-10-21T11:00:00+08:00')
        with patch.object(m,'datetime',Clock), patch.object(m,'load_for_workflow',side_effect=lambda state,key=None,**kw:original_load(state,key,memory=self.memory,**kw)) as loaded:
            plan=w.plan(self.state,'2026-10-20')
        self.assertEqual(loaded.call_args.args,(self.state,));self.assertEqual(loaded.call_args.kwargs,{})
        self.assertEqual((plan['start'],plan['end_exclusive'],plan['end']),('2026-09-21','2026-10-20','2026-10-19'))
        self.assertEqual(plan['appeal_case_memory']['case_count'],1)
        self.assertEqual(plan['appeal_case_memory']['as_of'],'2026-10-21T11:00:00+08:00')
        self.assertEqual(self.state,before)


if __name__ == '__main__':
    unittest.main()
