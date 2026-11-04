"""Original single-argument operations must bind every encoded SDK payload."""

import asyncio
from types import SimpleNamespace

import pytest

from ergora import reference
from ergora.reference_task_reconciliation import _Inspection
from ergora.reference_task_runtime import VerifiedSpecClient, find_signal_event


@pytest.fixture
def converter(monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.common.v1 import Payload
    from temporalio.converter import DataConverter, PayloadCodec

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))

    class Codec(PayloadCodec):
        async def encode(self, payloads):
            return [Payload(metadata={'encoding': b'test/original'}, data=p.SerializeToString()) for p in payloads]

        async def decode(self, payloads):
            return [Payload.FromString(p.data) for p in payloads]

    return DataConverter(payload_codec=Codec())


@pytest.mark.parametrize('count', [0, 1, 2])
def test_original_spec_requires_one_payload_before_single_type_decoding(converter, count):
    spec = {'request_sha256': 'a' * 64}
    payloads = asyncio.run(converter.encode([spec] * count))
    client = VerifiedSpecClient(SimpleNamespace(data_converter=converter), spec)
    if count == 1:
        assert asyncio.run(client.decode_spec(payloads, [dict])) == [spec]
    else:
        with pytest.raises(ValueError, match='original task spec'):
            asyncio.run(client.decode_spec(payloads, [dict]))


@pytest.mark.parametrize('name', ['approve_plan', 'request_cancel'])
@pytest.mark.parametrize('count', [0, 1, 2])
def test_signal_recovery_skips_non_single_payloads_and_keeps_scanning(converter, name, count):
    from temporalio.api.history.v1 import HistoryEvent

    body = {'request_sha256': 'a' * 64, 'operation_sha256': 'b' * 64}

    async def read():
        events = []
        for event_id, values in ((2, [body] * count), (3, [body])):
            event = HistoryEvent(event_id=event_id)
            signal = event.workflow_execution_signaled_event_attributes
            signal.signal_name = name
            signal.input.payloads.extend(await converter.encode(values))
            events.append(event)

        class Handle:
            async def fetch_history_events(self, **kwargs):
                for event in events:
                    yield event

        return await find_signal_event(Handle(), converter, name, body)

    assert asyncio.run(read()) == (2 if count == 1 else 3)


@pytest.mark.parametrize('count', [0, 1, 2])
def test_closed_history_requires_one_original_job_context(converter, count):
    from temporalio.api.history.v1 import HistoryEvent
    from dev_platform.contracts import canonical_sha

    spec = {'request_sha256': 'a' * 64, 'profile_sha256': 'b' * 64}
    context = {'task_id': 'task-one', 'job_id': 'task-one-plan', 'stage': 'plan', 'spec': spec, **spec}
    inspection = _Inspection.__new__(_Inspection)
    inspection.creation = SimpleNamespace(task_id='task-one')
    inspection.spec, inspection.sha = spec, canonical_sha

    async def read():
        start, job, end = (HistoryEvent(event_id=i) for i in (1, 2, 3))
        start.workflow_execution_started_event_attributes.SetInParent()
        scheduled = job.activity_task_scheduled_event_attributes
        scheduled.activity_type.name = 'dev_submit'
        scheduled.input.payloads.extend(await converter.encode([context] * count))
        end.workflow_execution_completed_event_attributes.SetInParent()

        class Handle:
            async def fetch_history_events(self, **kwargs):
                for event in (start, job, end):
                    yield event

        return await inspection.jobs(Handle(), converter, 'COMPLETED')

    if count == 1:
        jobs = asyncio.run(read())
        assert jobs['task-one-plan']['context'] == context
        assert jobs['task-one-plan']['job_sha256'] == canonical_sha(context)
    else:
        with pytest.raises(ValueError, match='single context'):
            asyncio.run(read())
