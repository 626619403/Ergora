"""Reject malformed task inputs before project storage or native preparation."""

import pytest

from ergora import tasks


_ARGUMENTS = {
    'start': {'expected_revision': 1, 'creation_sha256': 'a' * 64},
    'approve': {'decision_id': 'owner-one', 'expected_revision': 1, 'run_id': 'original-run',
                'plan_sha256': 'a' * 64, 'confirm': True},
    'cancel': {'request_id': 'stop-one', 'expected_revision': 1, 'run_id': 'original-run',
               'reason': 'Owner requested stop', 'confirm': True},
    'export': {'expected_revision': 1, 'run_id': 'original-run', 'candidate_sha': 'a' * 40,
               'branch': 'agent/exported', 'confirm': True},
    'external_status': {'run_id': 'original-run'},
    'events': {'run_id': 'original-run'},
    'reconcile': {'expected_revision': 1, 'run_id': 'original-run', 'confirm': True},
    'resume_reconcile': {'expected_revision': 1, 'intent_sha256': 'a' * 64, 'confirm': True},
}

_CASES = [
    ('start', {'timeout': True}, 'timeout'),
    ('start', {'timeout': 0}, 'timeout'),
    ('start', {'timeout': '1'}, 'timeout'),
    ('start', {'timeout': 61}, 'timeout'),
    ('approve', {'run_id': ''}, 'Run ID'),
    ('approve', {'plan_sha256': 'bad'}, 'SHA256'),
    ('approve', {'confirm': False}, 'confirmation'),
    ('approve', {'confirm': 1}, 'confirmation'),
    ('approve', {'timeout': True}, 'timeout'),
    ('approve', {'timeout': 0}, 'timeout'),
    ('approve', {'timeout': 61}, 'timeout'),
    ('cancel', {'reason': ''}, 'reason'),
    ('cancel', {'reason': ' '}, 'reason'),
    ('cancel', {'reason': 'x' * 1001}, 'reason'),
    ('cancel', {'reason': True}, 'reason'),
    ('cancel', {'confirm': False}, 'confirmation'),
    ('cancel', {'confirm': 1}, 'confirmation'),
    ('cancel', {'timeout': True}, 'timeout'),
    ('cancel', {'timeout': 61}, 'timeout'),
    ('export', {'candidate_sha': 'abc'}, 'full candidate'),
    ('export', {'candidate_sha': 'a' * 40 + '\n'}, 'full candidate'),
    ('export', {'confirm': False}, 'confirmation'),
    ('export', {'confirm': 1}, 'confirmation'),
    ('export', {'timeout': True}, 'timeout'),
    ('export', {'timeout': 61}, 'timeout'),
    ('external_status', {'run_id': ''}, 'Run ID'),
    ('external_status', {'timeout': True}, 'timeout'),
    ('external_status', {'timeout': 0}, 'timeout'),
    ('external_status', {'timeout': 61}, 'timeout'),
    ('events', {'run_id': ''}, 'Run ID'),
    ('events', {'limit': True}, 'limit'),
    ('events', {'limit': 0}, 'limit'),
    ('events', {'limit': 101}, 'limit'),
    ('events', {'timeout': True}, 'timeout'),
    ('events', {'timeout': 61}, 'timeout'),
    ('events', {'after': ''}, 'cursor'),
    ('events', {'after': 'a' * 8193}, 'cursor'),
    ('events', {'after': True}, 'cursor'),
    ('reconcile', {'run_id': ''}, 'Run ID'),
    ('reconcile', {'confirm': 1}, 'confirmation'),
    ('reconcile', {'confirm': False}, 'confirmation'),
    ('reconcile', {'timeout': True}, 'timeout'),
    ('reconcile', {'timeout': 61}, 'timeout'),
    ('resume_reconcile', {'intent_sha256': 'bad'}, 'SHA256'),
    ('resume_reconcile', {'confirm': 1}, 'confirmation'),
    ('resume_reconcile', {'timeout': 0}, 'timeout'),
]


@pytest.mark.parametrize('operation,changes,error', _CASES,
    ids=[f'{operation}-{next(iter(changes))}-{index}' for index, (operation, changes, _) in enumerate(_CASES)])
def test_invalid_inputs_stop_before_project_or_native_access(monkeypatch, operation, changes, error):
    accessed = []
    def forbidden(*args, **kwargs):
        accessed.append(True)
        raise AssertionError('Invalid input reached project storage or native preparation')
    monkeypatch.setattr(tasks, '_project', forbidden)
    monkeypatch.setattr(tasks, '_native_prepare', forbidden)
    with pytest.raises(ValueError, match=error):
        getattr(tasks, operation)(state=object(), project_id='demo', task_id='new-task',
                                  **{**_ARGUMENTS[operation], **changes})
    assert not accessed
