"""Trusted review opinions shared by SDK activities and the SDK-free executor.

The original FileAdapter validates the terminal receipt and all its artifacts;
this reader then binds the opinion to the actual successful model result.
"""

import hashlib
import json
import re

from dev_platform.adapter import read_raw, require


def review_observation(adapter, job: dict, receipt: dict) -> dict:
    """Read a trusted opinion after the original FileAdapter verifies its receipt."""
    # FileAdapter has verified terminal structure, job identity and every
    # artifact's bytes. A failed process alone is never a review opinion.
    artifacts = {item['name']: item for item in receipt['artifacts']}
    if 'composition-review-decision' not in artifacts:
        require(receipt['state'] != 'SUCCEEDED', 'Successful review is missing its trusted decision')
        return {'receipt': receipt, 'review_decision': None}

    def document(name):
        item = artifacts[name]
        raw = read_raw(adapter.path('artifacts', item['path']), 16_777_216)
        require(hashlib.sha256(raw).hexdigest() == item['sha256'], 'Review opinion artifact changed while reading')
        return json.loads(raw)

    decision = document('composition-review-decision')
    context = job['context']
    actor = receipt['actor']
    expected = {'schema_version': 1, 'kind': 'formal-review-decision',
        'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
        'candidate_sha': context['expected_candidate_sha']}
    require(isinstance(decision, dict) and type(decision.get('schema_version')) is int
            and set(decision) == expected.keys() | {'decision', 'result_sha256'}
            and all(decision[key] == value for key, value in expected.items()), 'Review decision binding mismatch')
    require(decision['decision'] in ('approve', 'request-changes'), 'Invalid trusted review opinion')
    require(isinstance(decision['result_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', decision['result_sha256']),
            'Invalid model result digest in trusted review opinion')
    approved = decision['decision'] == 'approve'
    require(receipt['state'] == ('SUCCEEDED' if approved else 'FAILED'), 'Review opinion differs from its original terminal state')
    require(actor['role'] == 'reviewer' and actor['kind'] == 'agent', 'Unexpected review executor role/kind')
    require(receipt['candidate_sha'] == context['expected_candidate_sha'], 'Review opinion candidate mismatch')
    require(actor['id'] not in context['author_ids'] and actor['session_id'] not in context['author_sessions'],
            'Review opinion requires an independent principal and session')
    required = set(context['spec']['profile']['artifacts_by_stage']['review'])
    require(required <= artifacts.keys(), 'Missing required review artifacts')
    checks = {check['id']: check['status'] for check in receipt.get('checks', [])}
    require(checks.get('independent-review') == ('pass' if approved else 'fail')
            and all(status == 'pass' for name, status in checks.items() if name != 'independent-review'),
            'Review checks differ from the trusted opinion')
    invocation = document('composition-invocation')
    require(invocation['status'] == 'succeeded' and invocation['result_sha256'] == decision['result_sha256'],
            'Review opinion differs from the actual successful model result')
    return {'receipt': receipt, 'review_decision': decision['decision']}
