"""Portable production-only loader for typed range reconciliation regressions.
No candidate/work/live input and no transport invocation at import time.
"""
import importlib,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
D=ROOT/'skills/violation-notifier/scripts'
M=ROOT/'skills/workshop-director/scripts'
FIXTURES=HERE/'fixtures/preselected-record-range'
sys.path[:0]=[str(D),str(HERE),str(M)]
recovery=importlib.import_module('preselected_record_range_recovery')
detail=importlib.import_module('governance_detail')
query=detail.query_api
zero=importlib.import_module('governance_zero_capture')
_name='preselected_range_test_production_semantic'
_spec=importlib.util.spec_from_file_location(_name,M/'semantic_progress.py')
semantic=importlib.util.module_from_spec(_spec)
sys.modules[_name]=semantic
_spec.loader.exec_module(semantic)
