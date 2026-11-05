"""Per-workflow delivery group resolution. Single configured source, never a
hard-coded group name.

Every workflow's produced output goes to the group configured here; the
messenger policy allowlist remains the second mandatory gate. Sealed historical
orders keep their own recorded recipient - this module only decides NEW
delivery items.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'skills/workshop-director/config/delivery-targets.json'
POLICY = ROOT / 'skills/wecom-messenger/config/policy.json'
FLOWS = ('daily-comment-stats', 'negative-review-complaints', 'violation-notifier')


def _document(path, kind):
    raw = Path(path).read_bytes()
    value = json.loads(raw)
    if kind:
        from collection_ready import need
        need(value.get('kind') == kind, 'delivery-targets-kind')
    return value


def _config():
    value = _document(CONFIG, 'per-workflow-delivery-targets-v1')
    return value['targets']


def allowed():
    """Every group name the messenger policy may ever send to."""
    policy = _document(POLICY, None)
    return {r['name'] for r in policy.get('allowed_recipients', []) if r.get('kind') == 'group' and isinstance(r.get('name'), str) and r['name']}


def target(workflow):
    from collection_ready import need
    need(workflow in FLOWS, 'delivery-targets-unknown-workflow')
    targets = _config()
    need(workflow in targets, 'delivery-targets-missing-workflow')
    name = targets[workflow]
    need(type(name) is str and 0 < len(name) <= 64, 'delivery-targets-name-shape')
    need(name in allowed(), 'delivery-targets-not-in-sender-allowlist')
    return name


def all():
    return {flow: target(flow) for flow in FLOWS}
