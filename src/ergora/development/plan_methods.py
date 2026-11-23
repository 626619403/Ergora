"""Exact, bounded method guidance for an original Plan approval."""

import json
import re

from .envelopes import identity


METHOD_BYTES = 2048
METHODS_BYTES = 8192


def validate_methods(methods: dict) -> None:
    if not isinstance(methods, dict) or not 1 <= len(methods) <= 24:
        raise ValueError('Method addendum requires one to 24 named original work units')
    for unit, text in methods.items():
        if (not isinstance(unit, str) or not unit or len(unit) > 80 or not isinstance(text, str)
                or not text.strip() or '\0' in text or len(text.encode('utf-8')) > METHOD_BYTES):
            raise ValueError('Each method must name a unit and contain nonempty UTF-8 text within 2048 bytes')
    if len(json.dumps(methods, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > METHODS_BYTES:
        raise ValueError('Complete method addendum exceeds 8192 canonical bytes')


def addendum(document: dict, run_id: str, original_plan_sha256: str, methods: dict) -> dict:
    validate_methods(methods)
    if document.get('schema_version') != 12:
        raise ValueError('Method addenda require the current budgeted native task')
    if (not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id
            or not isinstance(original_plan_sha256, str) or re.fullmatch('[0-9a-f]{64}', original_plan_sha256) is None):
        raise ValueError('Method addendum requires the exact original run and Plan digest')
    spec = document['legacy_spec']
    request = spec['request']
    if not methods.keys() <= {unit['id'] for unit in request['input']['work_units']}:
        raise ValueError('Method addendum may only name frozen original work units')
    return {'schema_version': 1, 'kind': 'plan-method-addendum', 'task_id': request['task_id'],
            'run_id': run_id, 'request_sha256': spec['request_sha256'], 'admission_sha256': document['sha256'],
            'original_plan_sha256': original_plan_sha256, 'methods': dict(methods)}


def require_addendum(value: dict, document: dict, run_id: str, original_plan_sha256: str) -> None:
    if not isinstance(value, dict) or identity(value) != identity(addendum(document, run_id, original_plan_sha256,
                                                                            value.get('methods'))):
        raise ValueError('Method addendum differs from the original task, run, admission or Plan')


def approval_digest(value: dict) -> str:
    return identity({'kind': 'plan-approval-with-method-addendum', 'original_plan_sha256': value['original_plan_sha256'],
                     'method_addendum_sha256': identity(value)})


def has_method_approval(approval) -> bool:
    return isinstance(approval, dict) and bool(approval.keys() & {'method_addendum', 'approval_plan_sha256'})


def approved_addendum(approved: dict, document: dict, *, run_id: str | None = None) -> dict | None:
    approval = approved['approval']
    if not has_method_approval(approval):
        return None
    value = approval['method_addendum']
    require_addendum(value, document, value['run_id'] if run_id is None else run_id, approved['plan_sha256'])
    if identity(approved['receipt']) != approved['plan_sha256'] or approval_digest(value) != approval['approval_plan_sha256']:
        raise ValueError('Composite approval differs from the exact original Plan and method addendum')
    return value


def verify_owner_receipt(approved: dict, document: dict, read_receipt, *, run_id: str | None = None) -> str | None:
    """Bind the compound stage proof to the exact saved owner approval bytes."""
    method = approved_addendum(approved, document, run_id=run_id)
    if method is None:
        return None
    proof = approved['approval']
    receipt = read_receipt(proof['receipt_id'])
    composite = proof['approval_plan_sha256']
    expected = {'schema_version': 1, 'kind': 'plan-approval', 'task_id': method['task_id'],
                'request_sha256': method['request_sha256'], 'profile_sha256': document['legacy_spec']['profile_sha256'],
                'plan_sha256': composite, 'decision': 'approve', 'principal_type': 'human',
                'role': 'owner', 'revoked': False, 'actor_id': proof['actor_id'], 'method_addendum': method}
    if (not isinstance(receipt, dict) or identity(receipt) != proof['approval_sha256']
            or any(identity(receipt.get(key)) != identity(value) for key, value in expected.items())):
        raise ValueError('Saved owner receipt does not bind the original method-approved Plan')
    return composite


def work_unit(unit: dict, composite_sha256: str | None) -> dict:
    return unit if composite_sha256 is None else {**unit, 'approval_plan_sha256': composite_sha256}
