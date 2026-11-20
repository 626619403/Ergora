"""Real submission/native locks; controller and historical evidence are controlled inputs."""

import ergora.training.runtime.evidence as execution_evidence
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import subprocess
import stat
import time
from types import SimpleNamespace

from agent_platform import training as native
import ergora.training.runtime.submission as submissions
import ergora.training.execution_protocol as protocol
from perf_temporal.client import load_experiment


payload = json.load(sys.stdin)
marker = Path(payload['marker'])


def hold():
    marker.touch()
    deadline = time.monotonic() + 15
    while not marker.with_suffix('.release').exists():
        if time.monotonic() >= deadline:
            raise TimeoutError('Controlled admission barrier was not released')
        time.sleep(.01)


if payload['operation'] == 'native-cli-start':
    def send(argv, **options):
        with marker.with_suffix('.calls').open('a') as stream:
            stream.write('start\n')
        hold()
        return SimpleNamespace(returncode=0)
    native.subprocess.run = send
    native.cli(['start', 'alpha'])
elif payload['operation'] == 'native-approve':
    manifest_path = native.TRAINING / 'manifests/alpha.json'
    manifest = native.read(manifest_path)
    runner_path = native.CONFIG / 'training-runners' / (manifest['runner_template_id'] + '.json')
    runner = native.read(runner_path)
    if payload['profiled']:
        manifest['execution']['profile'] = {'protocol': 'training-profile-v1', 'tool': 'cprofile-json',
            'reader': 'cprofile-json-v1', 'source_operation': 'cpu-diagnostic-v1',
            'phases': ['baseline'], 'ranks': [0], 'window': {'unit': 'source_samples', 'work': 3, 'warmup_work': 0},
            'captures': 1, 'maximum_seconds': 2, 'max_raw_bytes': 100000, 'max_derived_bytes': 10000, 'required': True}
        runner['configuration_readback'] = {'profile': {'protocol': 'training-profile-v1', 'operations': ['cpu-diagnostic-v1']}}
    native.write(manifest_path, manifest, replace=True)
    spec_path = native.TRAINING / 'specs/alpha.json'
    spec = native.read(spec_path)
    spec['binding']['manifest_sha'] = native.hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    native.write(spec_path, spec, replace=True)
    experiment = load_experiment(str(spec_path))
    native.write(native.job_folder('alpha') / 'request.json', {'schema_version': 1, 'job_id': 'local-perf-alpha',
        'experiment': asdict(experiment), 'runner': runner})
    if payload['runner_state'] == 'removed':
        runner_path.unlink()
    else:
        native.write(runner_path, {**runner, 'configuration_readback': None}, replace=True)
    class Handle:
        async def query(self, *args):
            return SimpleNamespace(phase='AWAITING_RELEASE', binding=experiment.binding, evidence_sha='d' * 64)
    async def connect():
        return SimpleNamespace(get_workflow_handle=lambda wid: Handle())
    from perf_temporal import connection
    connection.connect = connect
    def release(argv, **options):
        with marker.with_suffix('.calls').open('a') as stream:
            stream.write(argv[3] + '\n')
        return SimpleNamespace(returncode=0)
    native.subprocess.run = release
    native.cli(['approve', 'alpha', '--evidence-sha', 'd' * 64])
elif payload['operation'] == 'native-executor':
    async def prepared_job():
        adapter = native.create_adapter()
        try:
            experiment = load_experiment(str(native.TRAINING / 'specs/alpha.json'))
            return await adapter.create_job_if_absent(experiment, await adapter.read_manifest(experiment.manifest_uri))
        finally:
            await adapter.close()
    asyncio.run(prepared_job())
    decision = protocol.skip_decision_path({'state_directory': str(native.STATE)}, 'alpha')
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_bytes(b'')
    from agent_platform.training_executor import process
    process(native.job_folder('alpha'))
elif payload['operation'] == 'native-prepare':
    path = native.TRAINING / 'manifests/alpha.json'
    manifest = native.read(path)
    native.prepare(path, manifest['runner_template_id'], manifest['max_run_seconds'])
elif payload['operation'] == 'native-create':
    original_write = native.write
    def held_write(path, value, **options):
        original_write(path, value, **options)
        if Path(path).name == 'request.json':
            hold()
    native.write = held_write
    async def create():
        adapter = native.create_adapter()
        try:
            experiment = load_experiment(str(native.TRAINING / 'specs/alpha.json'))
            return await adapter.create_job_if_absent(experiment, await adapter.read_manifest(experiment.manifest_uri))
        finally:
            await adapter.close()
    asyncio.run(create())
else:
    operation = submissions._Submission(payload['submission'])
    observed = operation.records()
    authorization = {'control_home': payload['submission']['control_home'], 'project': operation.project['id'],
        'cycle_id': 'controlled-admission', 'input_sha256': 'a' * 64, 'sha256': 'b' * 64,
        'execution': operation.execution}
    plan = {'admissions': [{'observation': observed}]}
    original_parent = None
    expected_parent = protocol.processes.identity(os.getppid())
    if payload['operation'] == 'skip-parent-exits':
        original_parent = subprocess.Popen([sys.executable, '-c', 'import sys; sys.stdin.read()'], stdin=subprocess.PIPE)
        expected_parent = protocol.processes.identity(original_parent.pid)
        marker.with_suffix('.parent').write_text(json.dumps(expected_parent))
    source = {'identity': {'mode': 'prepare-candidate', 'ordinal': 0, 'input_sha256': authorization['input_sha256'],
                         'parent': expected_parent},
        'snapshot': {'candidate_count': 1}, 'start_context': {'controller': {'ordinal': 0}}}
    operation.payload['cycle_operation'] = source
    class Admission:
        def __init__(self, *args):
            pass
        @contextmanager
        def permission(self):
            yield self
        def check(self):
            pass
    protocol.CycleAdmission = Admission
    protocol.cycle_start_source = lambda value: value
    protocol.resolve_cycle_snapshot = lambda value: (deepcopy(plan), deepcopy(authorization))
    protocol.cycle_operation_remaining = lambda value: 60
    execution_evidence.authenticate_cycle_binding = lambda *args: []
    submissions.training_cycles._controller_ready = lambda *args: None
    submissions.training_cycles._load = lambda *args: (deepcopy(plan), deepcopy(authorization), {})
    execution_evidence.validate_skip_decision = lambda value, **options: value
    def decision(plan, authorization, ordinal, historical, *, absence_sha256, current_context):
        assert current_context is None, 'This lock fixture has no typed CPU execution contract'
        if payload.get('hold_skip'):
            hold()
        if original_parent is not None:
            original_parent.stdin.close()
            original_parent.wait(timeout=5)
        return {'experiment_id': operation.ident, 'historical': historical,
                'absence_sha256': absence_sha256, 'kind': 'controlled-lock-test'}
    execution_evidence.make_skip_decision = decision
    if payload['operation'] == 'skip-sync-loss':
        synchronize = os.fsync
        attempts = []
        def unavailable(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                attempts.append(descriptor)
                raise OSError('Controlled directory synchronization remains unavailable')
            synchronize(descriptor)
        os.fsync = unavailable
        try:
            for retry in range(2):
                try:
                    operation.skip(plan, authorization, 0, {})
                except OSError:
                    pass
                else:
                    raise AssertionError('Visible skip became completed while original durability remained unknown')
            assert len(attempts) == 2
        finally:
            os.fsync = synchronize
        path = operation.path('.skip.json')
        original = path.read_bytes()
        result = operation.skip(plan, authorization, 0, {})
        assert path.read_bytes() == original
        print(json.dumps({**result, 'failed_sync_attempts': len(attempts)}))
    else:
        print(json.dumps(operation.skip(plan, authorization, 0, {})))
