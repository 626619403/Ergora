"""Versioned readers bind SDK histories and file evidence to the full admission."""

import asyncio
from copy import deepcopy
import sys

import pytest

pytest.importorskip('temporalio')
pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task evidence uses Linux/WSL2')

from ergora import reference_task_approval, reference_task_evidence, reference_task_reconciliation, task_envelopes
from ergora.reference_inputs import execution_input
from test_composition_runtime import original_input, composed_creation, creation_project, installation, registration
from test_task_plan import pending_plan, snapshot
from test_task_job_evidence import original_job
from test_task_evidence_index import closed_evidence
from test_original_payloads import converter


def bind(data, composition):
    document = task_envelopes.wrap(data.spec, composition)
    data.input = execution_input(document)
    data.submission.input = data.input
    data.context['admission'] = document
    data.envelope_path.unlink()
    data.envelope_path = data.creation.path('requests-composition-v2/task-one/task-one-plan.json')
    digest = data.creation.sha(data.context)
    data.receipt['job_sha256'] = digest
    data.write(data.envelope_path, {'schema_version': 1, 'job_id': data.context['job_id'],
                                  'job_sha256': digest, 'context': data.context})
    data.save_receipt()
    return data


@pytest.fixture
def versioned_plan(original_job, original_input):
    return bind(original_job, original_input['composition'])


@pytest.fixture
def versioned_closed(closed_evidence, original_input):
    data = bind(closed_evidence, original_input['composition'])
    data.closed_submission.input = data.input
    return data


def inspect(data, reader):
    if reader == 'plan':
        return asyncio.run(reference_task_approval._plan(data.payload))
    if reader == 'job':
        return asyncio.run(reference_task_evidence._job(data.payload))
    return asyncio.run(reference_task_reconciliation._Inspection(data.payload).run())


@pytest.mark.parametrize('reader', ['plan', 'job', 'closed'])
def test_versioned_reader_uses_original_activity_and_its_own_request_root(request, reader):
    data = request.getfixturevalue('versioned_closed' if reader == 'closed' else 'versioned_plan')
    before = snapshot(data.creation.root)
    result = inspect(data, reader)
    assert result['run_id'] == 'original-run'
    if reader == 'plan':
        assert result['history_plan_event_id'] == 5 and len(result['materials']) == 3
    elif reader == 'job':
        assert result['receipt_status'] == 'published' and result['receipt'] == data.receipt
    else:
        assert len(result['jobs']) == 1 and result['jobs'][0]['request_state'] == 'matches'
        assert result['unexpected_jobs'] == result['unresolved_jobs'] == []
    assert snapshot(data.creation.root) == before


@pytest.mark.parametrize('reader', ['plan', 'job', 'closed'])
@pytest.mark.parametrize('difference', ['missing', 'same-legacy-other-admission'])
def test_matching_legacy_projection_cannot_replace_original_admission(request, reader, difference):
    data = request.getfixturevalue('versioned_closed' if reader == 'closed' else 'versioned_plan')
    if difference == 'missing':
        del data.context['admission']
    else:
        other = deepcopy(data.context['admission']['composition'])
        member = next(iter(other['members'].values()))
        member['backend_reason'] = 'Another separately admitted review call'
        data.context['admission'] = task_envelopes.wrap(data.spec, other)
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match='recorded task spec'):
        inspect(data, reader)
    assert snapshot(data.creation.root) == before
