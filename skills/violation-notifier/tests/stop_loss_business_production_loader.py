"""Production-only imports for public stop-loss route recovery tests."""
import importlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
D=ROOT/'skills/violation-notifier/scripts'
sys.path[:0]=[str(D),str(HERE)]
d=importlib.import_module('governance_detail')
stop=importlib.import_module('governance_stop_loss')
recovery=importlib.import_module('stop_loss_route_recovery')
FIXTURE=HERE/'fixtures/stop-loss-business-route/observed-shape-synthetic-values.json'
