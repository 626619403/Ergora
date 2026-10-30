from dev_platform.contracts import canonical_sha
from dev_platform.ingress import IngressLeases

from .core import STATE, read, write


def claim(spec: dict) -> None:
    request = spec['request']
    record = {'tracker': request['tracker'], 'owner': 'local-cli', 'task_id': request['task_id'],
              'spec_sha256': canonical_sha(spec)}
    leases = IngressLeases(STATE / 'ingress/leases.sqlite3')
    try:
        leases.acquire(**record)
        write(STATE / 'tasks' / request['task_id'] / 'cli-ingress.json', record)
    finally:
        leases.close()


def release(spec: dict, outcome: dict) -> bool:
    path = STATE / 'tasks' / spec['request']['task_id'] / 'cli-ingress.json'
    confirmed = outcome['status'] == 'REVIEW_READY' or (outcome['status'] == 'BLOCKED' and outcome.get('fence', {}).get('confirmed') is True)
    if not path.exists() or not confirmed: return False
    leases = IngressLeases(STATE / 'ingress/leases.sqlite3')
    try:
        leases.release(**read(path), evidence_digest=canonical_sha(outcome))
    finally:
        leases.close()
    return True
