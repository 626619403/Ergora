"""Immutable authorization and known call slots for one six-stage task.

Persistence belongs to the original task creation owner. Reading this contract
needs only the standard library; observing a deadline never grants more time.
"""

import hashlib
import json
from pathlib import Path
import re
import uuid

from . import budget_clock


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def validate_policy(policy: dict) -> None:
    if (not isinstance(policy, dict)
            or set(policy) != {'wall_seconds', 'cleanup_seconds', 'model_invocations'}
            or any(type(value) is not int for value in policy.values())
            or not 2 <= policy['wall_seconds'] <= 604800
            or not 1 <= policy['cleanup_seconds'] < policy['wall_seconds']
            or not 1 <= policy['model_invocations'] <= 258):
        raise ValueError('Budget policy requires wall_seconds (2–604800), cleanup_seconds inside that total, '
                         'and model_invocations (1–258); other strict dimensions are unsupported')


def scope(project: dict, home: Path, definition: dict) -> dict:
    return {'control_home': str(home), 'project': project['id'], 'repo': project['repo'],
            'project_revision': project['revision'], 'registration_sha256': project['registration']['sha256'],
            'execution': project['registration']['definition']['execution'],
            'task_id': definition['task_id'], 'definition_sha256': _sha(definition)}


def authorize(policy: dict, owner: dict) -> dict:
    validate_policy(policy)
    value = {'schema_version': 1, 'id': uuid.uuid4().hex, 'policy': policy, 'scope': owner,
             **budget_clock.authorize(policy['wall_seconds'])}
    return {**value, 'sha256': _sha(value)}


def validate(instance: dict) -> None:
    fields = {'schema_version', 'id', 'policy', 'scope', 'authorized_at', 'deadline_at',
              'boot_id', 'boottime_ns', 'sha256'}
    if (not isinstance(instance, dict) or set(instance) != fields
            or type(instance['schema_version']) is not int or instance['schema_version'] != 1
            or not isinstance(instance['id'], str) or re.fullmatch('[0-9a-f]{32}', instance['id']) is None
            or instance['sha256'] != _sha({key: value for key, value in instance.items() if key != 'sha256'})):
        raise ValueError('Invalid immutable budget authorization')
    validate_policy(instance['policy'])
    owner = instance['scope']
    if (not isinstance(owner, dict) or set(owner) != {'control_home', 'project', 'repo', 'project_revision',
            'registration_sha256', 'execution', 'task_id', 'definition_sha256'}
            or type(owner['project_revision']) is not int or owner['project_revision'] < 1
            or any(not isinstance(owner[key], str) or not owner[key] for key in
                   ('control_home', 'project', 'repo', 'task_id'))
            or any(not isinstance(owner[key], str) or re.fullmatch('[0-9a-f]{64}', owner[key]) is None
                   for key in ('registration_sha256', 'definition_sha256'))
            or not isinstance(owner['execution'], dict)):
        raise ValueError('Invalid budget creation identity')
    budget_clock.validate(instance, instance['policy']['wall_seconds'])


def remaining(instance: dict, *, cleanup: bool = False) -> float:
    """Conservatively observe UTC and same-boot elapsed time, without mutation."""
    validate(instance)
    reserve = 0 if cleanup else instance['policy']['cleanup_seconds']
    return budget_clock.remaining(instance, instance['policy']['wall_seconds'], reserve)


def require_remaining(instance: dict, *, cleanup: bool = False) -> float:
    value = remaining(instance, cleanup=cleanup)
    if value <= 0:
        raise ValueError('Original budget is exhausted; no new work or executable contract may be published')
    return value


def call_slots(composition: dict) -> dict:
    """Finite model-stage slots; retries/observations do not create new slots."""
    preparation, execution = composition['preparation'], composition['execution']
    return {**{stage: preparation[stage] for stage in ('inventory', 'plan')},
            **{'work:' + unit: member for unit, member in sorted(execution['assignments'].items())},
            **{'review:' + member: member for member in sorted(composition['members'])}}


def validate_contract(contract: dict, composition: dict, spec: dict) -> None:
    if not isinstance(contract, dict) or set(contract) != {'instance', 'slots'}:
        raise ValueError('Invalid complete budget contract')
    validate(contract['instance'])
    if contract['instance']['scope']['task_id'] != spec['request']['task_id']:
        raise ValueError('Budget belongs to another original task')
    expected = call_slots(composition)
    if contract['slots'] != expected or len(expected) > contract['instance']['policy']['model_invocations']:
        raise ValueError('Known model call slots differ from the budget or exceed its invocation cap')
