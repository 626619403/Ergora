"""Observe original actions through their registered native owners."""

from dataclasses import asdict, dataclass
from pathlib import Path
import re


class FixedCheckJobIdentityError(ValueError):
    """The original native owner rejected the selected Job digest."""


@dataclass(frozen=True)
class FixedCheckStatus:
    operation_id: str
    job_sha256: str | None = None
    verify_pending: bool = False

    def __post_init__(self):
        if type(self.verify_pending) is not bool or (self.verify_pending and self.job_sha256 is None):
            raise ValueError('Pending fixed-check observation requires its exact original Job digest')
        if self.job_sha256 is not None and (not isinstance(self.job_sha256, str)
                or re.fullmatch('[a-f0-9]{64}', self.job_sha256) is None):
            raise ValueError('Candidate check job must be a SHA256 digest')


@dataclass(frozen=True)
class TrainingExecutionStatus:
    experiment_id: str


@dataclass(frozen=True)
class TrainingFullResult:
    """Select one current managed full verification by its original native Run and raw attempt."""

    experiment_id: str
    workflow_id: str
    run_id: str
    job_id: str
    native_request_sha256: str
    attempt_sha256: str

    def __post_init__(self):
        if (not isinstance(self.experiment_id, str)
                or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', self.experiment_id) is None
                or self.workflow_id != 'perf-experiment/' + self.experiment_id
                or self.job_id != 'local-perf-' + self.experiment_id
                or not isinstance(self.run_id, str) or not 1 <= len(self.run_id) <= 128):
            raise ValueError('Training full-result observation requires the original experiment, workflow, Run and Job')
        for digest in (self.native_request_sha256, self.attempt_sha256):
            if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
                raise ValueError('Training full-result observation requires the original raw request and attempt SHA256')


def _require_identity(receipt, expected, description):
    if not isinstance(receipt, dict) or any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError(f'{description} differs from the selected original action')


def _fixed_check(action, project, home, *, deadline, stop_requested, supervised_cleanup):
    from ergora.development.native import task_fixed_candidate_check

    payload = {'operation_id': action.operation_id, 'job_sha256': action.job_sha256}
    if action.verify_pending:
        payload['verify_pending'] = True
    try:
        receipt = task_fixed_candidate_check(project, home, 'status-fixed-check', payload, deadline=deadline,
                                             stop_requested=stop_requested, supervised_cleanup=supervised_cleanup)
    except ValueError as error:
        # This exact refusal is emitted by the native Job digest selector.
        if str(error) == 'BLOCKED: Select the exact original candidate check job':
            raise FixedCheckJobIdentityError(str(error)) from error
        raise
    identity = {'operation_id': action.operation_id}
    if action.job_sha256 is not None:
        identity['job_sha256'] = action.job_sha256
    if isinstance(receipt, dict) and ('project' in receipt or receipt.get('status') != 'request_not_observed'):
        identity['project'] = project['id']
    _require_identity(receipt, identity, 'Fixed-check receipt')
    return receipt


def _training_execution(action, project, home, *, deadline, stop_requested, supervised_cleanup):
    from ergora.training.native import training_execution

    if any(option is not None for option in (deadline, stop_requested, supervised_cleanup)):
        raise ValueError('Training execution observation does not support a caller-owned reader window')
    receipt = training_execution(project, home, 'inspect', {'experiment_id': action.experiment_id})
    records = receipt.get('records') if isinstance(receipt, dict) else None
    if not isinstance(records, dict) or 'request' not in records:
        raise ValueError('Training lifecycle receipt does not include its original request record')
    if records['request'] is not None:
        _require_identity(records['request'], {'project': project['id'], 'experiment_id': action.experiment_id},
                          'Training execution request')
    return receipt


def _training_full_result(action, project, home, *, deadline, stop_requested, supervised_cleanup):
    from ergora.training.native import training_full_result

    locator = asdict(action)
    receipt = training_full_result(project, home, locator, deadline=deadline, stop_requested=stop_requested,
                                   supervised_cleanup=supervised_cleanup)
    _require_identity(receipt, {'project': project['id'], 'project_revision': project['revision'],
                                'registration_sha256': project['registration']['sha256'], 'locator': locator},
                      'Training full-result receipt')
    return receipt


_OBSERVERS = {FixedCheckStatus: _fixed_check, TrainingExecutionStatus: _training_execution,
              TrainingFullResult: _training_full_result}


def observe(action: FixedCheckStatus | TrainingExecutionStatus | TrainingFullResult, project: dict, home: Path, *,
            deadline: float | None = None, stop_requested=None, supervised_cleanup=None) -> dict:
    """Read the original owner receipt under an already selected project registration.

    Unknown action types fail before native invocation. The nominated reader retains
    its existing admission, clock and cleanup. No operation renews execution authority.
    """
    reader = _OBSERVERS.get(type(action))
    if reader is None:
        raise ValueError('Unsupported original action observation')
    return reader(action, project, home, deadline=deadline, stop_requested=stop_requested,
                  supervised_cleanup=supervised_cleanup)
