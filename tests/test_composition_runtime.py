"""Versioned original Temporal inputs retain one compatible six-stage projection."""

import asyncio
import base64
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip('temporalio')

from ergora import reference, task_envelopes, tasks
from ergora.reference_task_runtime import VerifiedSpecClient
from test_composition_tasks import composed_creation
from test_task_creation import creation_project
from test_registrations import installation, registration


@pytest.fixture
def original_input(composed_creation, monkeypatch):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, _, task = composed_creation
    return tasks.preview(state, 'demo', task, 1)['files']['task.spec.json']


@pytest.mark.parametrize('version', [1, 2])
def test_each_input_version_starts_its_registered_entrypoint_with_the_complete_original_payload(original_input, version):
    from ergora.reference_workflows import execution_input
    from temporalio.workflow import _Definition

    document = original_input if version == 2 else original_input['legacy_spec']
    selected = execution_input(document)
    native = SimpleNamespace(start_workflow=AsyncMock(return_value='native-handle'))
    client = VerifiedSpecClient(native, document)
    assert asyncio.run(client.start_workflow(None, original_input['legacy_spec'], id='original-id', task_queue='original-queue')) == 'native-handle'
    assert native.start_workflow.call_args.args == (selected.entrypoint, document)
    assert native.start_workflow.call_args.kwargs == {'id': 'original-id', 'task_queue': 'original-queue' + ('.composition-v2' if version == 2 else '')}
    contract = _Definition.must_from_run_fn(selected.entrypoint)
    assert contract.name == ('ErgoraCompositionWorkflowV2' if version == 2 else 'DevelopmentWorkflow')
    assert set(contract.signals) == {'approve_plan', 'request_cancel'} and set(contract.queries) == {'status'}


@pytest.mark.parametrize('difference', ['legacy-only', 'other-admission', 'second-payload'])
def test_original_history_cannot_be_adopted_using_only_a_matching_legacy_projection(original_input, difference):
    from temporalio.converter import DataConverter

    other = deepcopy(original_input)
    other['composition']['members']['root/review']['backend_reason'] = 'A different admission decision'
    other['sha256'] = task_envelopes.identity({k: v for k, v in other.items() if k != 'sha256'})
    original = [original_input['legacy_spec']] if difference == 'legacy-only' else [other] if difference == 'other-admission' else [original_input] * 2
    converter = DataConverter()
    payloads = asyncio.run(converter.encode(original))
    client = VerifiedSpecClient(SimpleNamespace(data_converter=converter), original_input)
    with pytest.raises(ValueError, match='original task spec'):
        asyncio.run(client.decode_spec(payloads, [dict]))


def test_original_envelope_is_verified_before_the_native_transport_sees_its_projection(original_input):
    from temporalio.converter import DataConverter

    converter = DataConverter()
    payloads = asyncio.run(converter.encode([original_input]))
    client = VerifiedSpecClient(SimpleNamespace(data_converter=converter), original_input)
    assert asyncio.run(client.decode_spec(payloads, [dict])) == [original_input['legacy_spec']]
    changed = deepcopy(original_input['legacy_spec']); changed['request_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='six-stage projection'):
        asyncio.run(client.start_workflow(None, changed))


def test_each_inherited_stage_context_carries_the_same_complete_admission_and_candidate(original_input):
    from ergora.reference_workflows import CompositionDevelopmentWorkflow

    run = CompositionDevelopmentWorkflow()
    assert run.status()['admission_sha256'] is None
    run.spec, run.admission = original_input['legacy_spec'], original_input
    candidate = run.spec['request']['repository']['starting_sha']
    for stage in ('inventory', 'plan', 'work:one', 'integrate', 'verify', 'review'):
        context = run.context(stage, candidate)
        assert context['spec'] == run.spec and context['admission'] == original_input
        assert context['expected_candidate_sha'] == candidate
    assert run.status()['admission_sha256'] == original_input['sha256']


def test_complete_admission_counts_toward_the_existing_stage_payload_limit(original_input):
    from ergora.reference_workflows import CompositionDevelopmentWorkflow
    from dev_platform.workflow import DevelopmentWorkflow, StopWork

    legacy, composed = DevelopmentWorkflow(), CompositionDevelopmentWorkflow()
    legacy.spec = composed.spec = original_input['legacy_spec']
    composed.admission = original_input
    material = {'inherited-result': {'content': 'x' * 980_000}}
    assert legacy.context('review', dependencies=material)['dependencies'] == material
    with pytest.raises(StopWork, match='Complete composition stage context'):
        composed.context('review', dependencies=material)


def test_composition_entrypoint_rejects_legacy_input_before_any_activity(original_input):
    from ergora.reference_workflows import CompositionDevelopmentWorkflow
    from temporalio.exceptions import ApplicationError

    run = CompositionDevelopmentWorkflow()
    run.call = AsyncMock(side_effect=AssertionError('No activity before v2 admission'))
    with pytest.raises(ApplicationError, match='requires a v2 formal admission'):
        asyncio.run(run.run(original_input['legacy_spec']))
    run.call.assert_not_called()


@pytest.mark.parametrize('malformation', ['numeric-path', 'duplicate-path', 'deep-graph', 'null-document'])
def test_malformed_original_envelope_is_a_permanent_contract_failure_before_activities(original_input, malformation):
    from ergora.reference_workflows import CompositionDevelopmentWorkflow
    from temporalio.exceptions import ApplicationError

    document = deepcopy(original_input)
    if malformation == 'null-document':
        document = None
    else:
        snapshot = document['composition']['manifest']
        if malformation == 'deep-graph':
            raw = b'[' * 10_000 + b'0' + b']' * 10_000
        else:
            graph = json.loads(base64.b64decode(snapshot['files']['composition.json']['content_base64']))
            agent = next(item for item in graph['instances'] if item['kind'] == 'agent')
            if malformation == 'numeric-path':
                agent['path'] = 7
            else:
                graph['instances'].append(deepcopy(agent))
            raw = json.dumps(graph).encode()
        snapshot['files']['composition.json']['content_base64'] = base64.b64encode(raw).decode()
        inventory = {name: {'sha256': hashlib.sha256(base64.b64decode(item['content_base64'])).hexdigest(),
                            'executable_bits': item['executable_bits']} for name, item in snapshot['files'].items()}
        snapshot['digest'] = hashlib.sha256(json.dumps(dict(sorted(inventory.items())), sort_keys=True).encode()).hexdigest()
        document['sha256'] = task_envelopes.identity({k: v for k, v in document.items() if k != 'sha256'})
    run = CompositionDevelopmentWorkflow()
    run.call = AsyncMock(side_effect=AssertionError('Malformed input must not run activities'))
    with pytest.raises(ApplicationError) as rejected:
        asyncio.run(run.run(document))
    assert rejected.value.type == 'ContractViolation' and rejected.value.non_retryable is True
    run.call.assert_not_called()
