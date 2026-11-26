"""Dedicated native training clients and owned SDK-free readers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from tempfile import TemporaryDirectory

from .._paths import IMPORT_ROOT
from ..native.files import _read_windows_contract
from ..native.resources import ROOT, validate_installation
from ..runtime import processes


def training_files(project: dict, *, experiment_id: str | None = None, limit: int = 50,
                   after: str | None = None) -> dict:
    """Observe the frozen native registry in a separate, SDK-free process."""
    return _training_reader(project, 'from ergora.training.native import _training_files_main;_training_files_main()',
                            {'project': project['id'], 'repo': project['repo'],
                             'experiment_id': experiment_id, 'limit': limit, 'after': after})


def _training_reader_request(state_directory, config_directory, payload):
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=config_directory, AGENTFLOW_STATE_DIR=state_directory)
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        IMPORT_ROOT, ROOT / 'platform/local', ROOT / 'platform/upstream/platform',
        ROOT / 'platform/upstream/temporal', ROOT / 'platform/upstream')))
    raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(raw) > 16 * 1_048_576:
        raise ValueError('capacity_exceeded: complete training reader request')
    return environment, raw


def _training_reader_response(raw, stderr, returncode):
    from .materials import decode_record

    if returncode:
        lines = stderr.decode('utf-8', errors='replace').strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Training record reader exited with status {returncode}')
    return decode_record(raw)


def _stop_training_reader(process):
    try:
        process.kill()
    except ProcessLookupError:
        pass  # The original wait must still confirm the concurrent exit.


def _training_reader(project: dict, entrypoint: str, payload: dict, *, timeout: int = 30) -> dict:
    """A synchronous caller owns its actual child/wait until reap, even after T."""
    import selectors

    started = time.monotonic()
    deadline = started + timeout
    read_deadline = deadline - min(5, timeout / 4)
    execution = project['registration']['definition']['execution']
    environment, encoded = _training_reader_request(execution['state_directory'], execution['config_directory'], payload)
    if timeout <= 0:
        raise ValueError('Training record reader has no remaining allowance')
    process, selected = None, None
    stdout, stderr, offset, failure = bytearray(), bytearray(), 0, None
    pumps = []
    try:
        process = subprocess.Popen([sys.executable, '-P', '-S', '-c', entrypoint], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
        selected = selectors.DefaultSelector()
        if os.name == 'nt':
            # Windows does not select anonymous pipes. These synchronous pipe
            # pumps do no business-file I/O and remain owned/joined by this call.
            import threading
            problems, pumps = [], []
            def pump(stream, target, limit):
                try:
                    while chunk := stream.read(65_536):
                        if len(target) + len(chunk) > limit:
                            problems.append(ValueError('capacity_exceeded: complete training reader response'))
                        else:
                            target.extend(chunk)
                except OSError as error:
                    problems.append(error)
            def send():
                nonlocal offset
                try:
                    for start in range(0, len(encoded), 65_536):
                        offset += process.stdin.write(encoded[start:start + 65_536])
                        process.stdin.flush()
                except (OSError, ValueError) as error:
                    problems.append(error)
                finally:
                    process.stdin.close()
            pumps = [threading.Thread(target=send), threading.Thread(target=pump, args=(process.stdout, stdout, 8_388_608)),
                     threading.Thread(target=pump, args=(process.stderr, stderr, 65_536))]
            for pump_thread in pumps:
                pump_thread.start()
            while any(pump_thread.is_alive() for pump_thread in pumps) or process.poll() is None:
                if problems:
                    raise problems[0]
                remaining = read_deadline-time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Training record reader timed out; native execution state was not queried')
                threading.Event().wait(min(.05, remaining))
        else:
            for stream, event in ((process.stdin, selectors.EVENT_WRITE), (process.stdout, selectors.EVENT_READ), (process.stderr, selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                selected.register(stream, event)
            while selected.get_map() or process.poll() is None:
                remaining = read_deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Training record reader timed out; native execution state was not queried')
                for key, event in selected.select(min(.05, remaining)):
                    stream = key.fileobj
                    try:
                        if event == selectors.EVENT_WRITE:
                            offset += os.write(stream.fileno(), encoded[offset:offset + 65_536])
                            if offset == len(encoded):
                                selected.unregister(stream)
                                stream.close()
                        else:
                            chunk = os.read(stream.fileno(), 65_536)
                            if not chunk:
                                selected.unregister(stream)
                                stream.close()
                            else:
                                target, limit = (stdout, 8_388_608) if stream is process.stdout else (stderr, 65_536)
                                if len(target) + len(chunk) > limit:
                                    raise ValueError('capacity_exceeded: complete training reader response')
                                target.extend(chunk)
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        selected.unregister(stream)
                        stream.close()
        if offset != len(encoded) or time.monotonic() > read_deadline:
            raise TimeoutError('Training record reader timed out or did not consume its complete request')
    except BaseException as error:
        if process is None:
            raise
        failure = error
    finally:
        if process is not None:
            # Stop initiation and actual wait retain the same child across interrupts.
            # If the OS delays reap, this call remains cleanup_incomplete past T.
            while True:
                try:
                    try:
                        if process.poll() is None:
                            _stop_training_reader(process)
                    except OSError as error:
                        if not isinstance(failure, (KeyboardInterrupt, SystemExit)):
                            failure = error
                    process.wait()
                    break
                except KeyboardInterrupt as error:
                    if not isinstance(failure, KeyboardInterrupt):
                        failure = error
        for pump_thread in pumps:
            while pump_thread.is_alive():
                try:
                    pump_thread.join()
                except KeyboardInterrupt:
                    failure = failure or KeyboardInterrupt()
        if selected is not None:
            selected.close()
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if not stream.closed:
                    stream.close()
    elapsed = time.monotonic() - started
    if failure is not None:
        detail = f'; reader elapsed={elapsed:.6f}s T={timeout}s overrun={max(0, elapsed-timeout):.6f}s returncode={process.returncode}'
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure
        raise ValueError(str(failure) + detail) from failure
    result = _training_reader_response(bytes(stdout), bytes(stderr), process.returncode)
    if time.monotonic() > deadline:
        raise ValueError(f'Training record reader timed out during decoding; elapsed={time.monotonic()-started:.6f}s overrun={time.monotonic()-deadline:.6f}s returncode={process.returncode}')
    return result


async def _training_reader_async(state_directory, config_directory, operation, job, *, resources, timeout=20):
    """Await bounded pipes only; the adapter retains every child and actual wait."""
    import asyncio

    started = time.monotonic()
    timeout = min(20, timeout)
    deadline = started + timeout
    read_deadline = deadline - min(5, timeout / 4)
    if timeout <= 0 or any(item.get('unconfirmed') for item in resources.values()):
        raise ValueError('reader_cleanup_unconfirmed or original reader allowance exhausted')
    environment, encoded = _training_reader_request(state_directory, config_directory,
        {'operation': operation, 'state_directory': state_directory, 'config_directory': config_directory, 'job': job})
    spawning = asyncio.create_task(asyncio.create_subprocess_exec(sys.executable, '-P', '-S', '-c',
        'from ergora.training.runtime.evidence import main;main()', stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=environment))
    spawning_key = id(spawning)
    resource = {'process': None, 'spawn': spawning, 'unconfirmed': False, 'draining': None}
    resources[spawning_key] = resource
    try:
        process = await asyncio.wait_for(asyncio.shield(spawning), max(.001, read_deadline-time.monotonic()))
    except BaseException as error:
        async def reap_spawn():
            child = await spawning
            resource['process'] = child
            _stop_training_reader(child)
            # No request bytes were sent; this fixed child cannot do work.
            await child.communicate()
        resource['draining'] = asyncio.create_task(reap_spawn())
        while not resource['draining'].done() and time.monotonic() < deadline:
            try:
                await asyncio.wait_for(asyncio.shield(resource['draining']), max(.001, deadline-time.monotonic()))
            except asyncio.CancelledError:
                continue
            except TimeoutError:
                break
        if resource['draining'].done():
            resources.pop(spawning_key, None)
            await resource['draining']
            raise error
        resource['unconfirmed'] = True
        raise ValueError('reader_cleanup_unconfirmed: original child creation/wait retained') from error
    resources.pop(spawning_key)
    overflow = asyncio.get_running_loop().create_future()
    stdout, stderr = bytearray(), bytearray()

    async def read_pipe(stream, target, limit):
        while chunk := await stream.read(65_536):
            if len(target) + len(chunk) > limit:
                if not overflow.done():
                    overflow.set_result('capacity_exceeded: complete training reader response')
            else:
                target.extend(chunk)

    async def write_pipe():
        try:
            for offset in range(0, len(encoded), 65_536):
                process.stdin.write(encoded[offset:offset + 65_536])
                await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    wait = asyncio.create_task(process.wait())
    tasks = [asyncio.create_task(write_pipe()), asyncio.create_task(read_pipe(process.stdout, stdout, 8_388_608)),
             asyncio.create_task(read_pipe(process.stderr, stderr, 65_536))]
    draining = asyncio.gather(wait, *tasks, return_exceptions=True)
    resource = {'process': process, 'wait': wait, 'draining': draining, 'unconfirmed': False}
    resources[process.pid] = resource
    failure = None
    try:
        done, _ = await asyncio.wait((draining, overflow), timeout=max(0, read_deadline-time.monotonic()), return_when=asyncio.FIRST_COMPLETED)
        if overflow in done:
            raise ValueError(overflow.result())
        if draining not in done or time.monotonic() > read_deadline:
            raise TimeoutError('Training record reader timed out')
        outcomes = await draining
        if any(isinstance(item, BaseException) for item in outcomes):
            raise ValueError('Training reader pipe or actual wait failed')
    except BaseException as error:
        failure = error
    finally:
        overflow.cancel()
        if not draining.done() and process.returncode is None:
            _stop_training_reader(process)
        while not draining.done() and time.monotonic() < deadline:
            try:
                await asyncio.wait_for(asyncio.shield(draining), max(.001, deadline-time.monotonic()))
            except asyncio.CancelledError as error:
                failure = failure or error
            except TimeoutError:
                break
        if draining.done() and process.returncode is not None:
            resources.pop(process.pid, None)
        else:
            resource['unconfirmed'] = True
    if resource['unconfirmed']:
        raise ValueError(f'reader_cleanup_unconfirmed: pid={process.pid} returncode={process.returncode}')
    if failure is not None:
        if isinstance(failure, asyncio.CancelledError):
            raise failure
        raise ValueError(str(failure)) from failure
    result = _training_reader_response(bytes(stdout), bytes(stderr), process.returncode)
    if time.monotonic() > deadline:
        raise ValueError(f'Training record reader timed out during decoding; returncode={process.returncode}')
    return result


async def _close_training_readers(resources):
    """Drain the adapter's original resources before its loop may be closed."""
    import asyncio

    for pid, item in list(resources.items()):
        while item['draining'] is None:
            try:
                await asyncio.sleep(.01)
            except asyncio.CancelledError:
                continue
        if item['process'] is not None and item['process'].returncode is None:
            _stop_training_reader(item['process'])
        while not item['draining'].done():
            try:
                await asyncio.shield(item['draining'])
            except asyncio.CancelledError:
                continue
        await item['draining']
        resources.pop(pid, None)


def training_execution(project: dict, home: Path, operation: str, payload: dict, *, timeout: int = 20) -> dict:
    if operation == 'request':
        if sys.platform != 'linux':
            raise ValueError('Managed training execution requires Linux; use WSL2 and a trusted Linux container')
        return _training_process(project, 'worker', {'project': project, 'control_home': str(home),
            'operation': operation, **payload}, timeout, sdk=True, entrypoint='execution_main')
    entrypoint = 'from ergora.training.execution_protocol import inspect_main;inspect_main()'
    selection = {'project': project, 'control_home': str(home), **payload}
    observed = _training_reader(project, entrypoint, {**selection, 'operation': 'inspect'})
    # A current installation check cannot withhold the already-read history.
    try:
        sources = _training_reader(project, entrypoint, {**selection, 'operation': 'sources'}, timeout=5)
    except (OSError, ValueError) as error:
        sources = {'status': 'unavailable_or_changed', 'reason': str(error)}
    return {**observed, 'current_sources': sources}


def training_full_result(project: dict, home: Path, locator: dict, *, deadline: float,
                         stop_requested, supervised_cleanup) -> dict:
    return _managed_training_observation(project, home, locator, 'managed-full-result', 'full-result',
                                         deadline, stop_requested, supervised_cleanup)


def training_screen_decision(project: dict, home: Path, locator: dict, *, deadline: float,
                             stop_requested, supervised_cleanup) -> dict:
    return _managed_training_observation(project, home, locator, 'managed-screen-decision', 'screen-decision',
                                         deadline, stop_requested, supervised_cleanup)


def _managed_training_observation(project, home, locator, operation, label, deadline, stop_requested,
                                  supervised_cleanup):
    """Observe one managed result from its dedicated single-reader supervisor."""
    from .materials import read_raw

    if sys.platform != 'linux':
        raise ValueError(f'Supervised training {label} observation requires Linux')
    if (type(deadline) not in (int, float) or not math.isfinite(deadline)
            or not callable(stop_requested) or not callable(supervised_cleanup)):
        raise ValueError(f'Training {label} observation requires its original reader deadline, STOP and cleanup owner')
    if project.get('_original_registration') is not None:
        raise ValueError(f'Training {label} observation requires the selected current registration')
    deadline = min(deadline, time.monotonic() + 20)

    def stopped():
        return time.monotonic() >= deadline or stop_requested()

    def check_window():
        if time.monotonic() >= deadline:
            raise TimeoutError(f'Original training {label} read reached its deadline')
        if stop_requested():
            raise ValueError(f'Original training {label} read was stopped')

    check_window()
    execution = project['registration']['definition']['execution']
    environment, raw = _training_reader_request(execution['state_directory'], execution['config_directory'],
        {'operation': operation, 'project': project, 'control_home': str(home), 'locator': locator})
    command = [sys.executable, '-P', '-S', '-c', 'from ergora.training.runtime.evidence import main;main()']
    owner = processes.identity(os.getpid())
    with TemporaryDirectory(prefix='ergora-training-result-') as temporary:
        output = Path(temporary) / 'reader'
        check_window()
        result = processes.run(command, Path.cwd(), output, max(0, deadline - time.monotonic()), raw.decode('utf-8'),
                               environment, supervised=True, record_lifecycle=True, stop_requested=stopped)
        cleanup = _training_reader_response(read_raw(output / 'process-cleanup.json', 1_048_576), b'', 0)
        if cleanup.get('model_waited') is False and result['status'] == 'cancelled':
            check_window()
        if (cleanup.get('kind') != 'supervised-process-cleanup' or cleanup.get('schema_version') != 1
                or cleanup.get('owner') != owner or cleanup.get('model_waited') is not True
                or not isinstance(cleanup.get('model'), dict) or cleanup.get('remaining_children') != []
                or cleanup.get('returncode') != result['returncode']):
            raise ValueError(f'Original training {label} reader cleanup is unconfirmed')
        supervised_cleanup(cleanup)
        check_window()
        if result['status'] == 'cancelled':
            raise ValueError(f'Original training {label} read was stopped')
        observed = _training_reader_response(read_raw(output / 'stdout.txt', 8_388_608),
                                             read_raw(output / 'stderr.txt', 65_536), result['returncode'])
    check_window()
    return observed


def training_runtime_status(project: dict, spec: dict, *, run_id: str | None, timeout: int) -> dict:
    """Explicitly query the native training workflow, pinned to its original input."""
    return _training_process(project, 'runtime', {'spec': spec, 'run_id': run_id}, timeout, sdk=True)


def training_setup(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Preview or publish native baseline/runner configuration without starting work."""
    runner = operation in ('preview-runner', 'register-runner')
    if (operation == 'init-baseline' or runner) and sys.platform != 'linux':
        raise ValueError('Native training initialization and runner registration require Linux; use the registered runtime in WSL2')
    return _training_process(project, 'setup', {'project': project, 'control_home': str(home),
                             'operation': operation, **payload}, 20, sdk=False)


def training_preparation(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Prepare native files locally; their original intent remains explicitly recoverable."""
    if sys.platform != 'linux':
        raise ValueError('Native training preparation requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'preparation', {'project': project, 'control_home': str(home),
                             'operation': operation, **payload}, 20, sdk=False)


def training_submission(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Enter the selected training owner with durable submission checkpoints."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training submission requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'submission', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout, sdk=operation in ('dispatch', 'resume', 'fence'))


def training_evidence(project: dict, home: Path, payload: dict) -> dict:
    """Read the original archive without the optional SDK, services or release side effects."""
    if project.get('_original_registration') is not None:
        raise ValueError('Training evidence does not support registration recovery')
    return _training_reader(project, 'from ergora.training.runtime.evidence import main;main()',
                            {'project': project, 'control_home': str(home), **payload}, timeout=20)


def training_release(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Checkpoint a native owner decision without creating a second approval authority."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training approval requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'release', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout, sdk=operation in ('dispatch', 'resume'))


def training_cancellation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Keep training cancellation delivery and native stop observations with their owners."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training cancellation and executor observation require Linux; use WSL2')
    return _training_process(project, 'cancellation', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout,
                             sdk=operation in ('dispatch', 'resume', 'stop-status'))


def _training_process(project: dict, module: str, payload: dict, timeout: int, *, sdk: bool,
                      entrypoint: str = 'main') -> dict:
    recovery = project.get('_original_registration')
    if recovery is not None and module not in ('submission', 'cancellation'):
        raise ValueError('Original registration recovery is limited to submission reconciliation, cancellation and local fencing')
    if sdk and importlib.util.find_spec('temporalio') is None:
        raise ValueError('Training runtime operations require the optional Temporal SDK; install ergora[temporal] in this environment')
    execution = project['registration']['definition']['execution']
    installation = validate_installation(Path(execution['installation']), training=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        IMPORT_ROOT, installation / 'local', installation / 'upstream/platform',
        installation / 'upstream/temporal', installation / 'upstream')))
    # Submission preflight invokes native Git. Keep that entire process group
    # under the existing owner, including timeout and interrupted-call cleanup.
    native_module = 'status' if module == 'runtime' else module
    with TemporaryDirectory(prefix='ergora-training-operation-') as temporary:
        output = Path(temporary) / 'process'
        result = processes.run([sys.executable, '-P', '-c',
                               f'from ergora.training.runtime.{native_module} import {entrypoint};{entrypoint}()'],
                              Path.cwd(), output, timeout + 5,
                              stdin=json.dumps({**payload, 'timeout': timeout}, allow_nan=False), env=environment)
        if result['status'] in ('timed_out', 'cancelled'):
            if module == 'submission' and payload['operation'] == 'fence':
                raise ValueError('Local training fence process timed out or stopped and its fence may already exist; repeat the same binding confirmation, execution stop remains unknown')
            raise ValueError('Training runtime process timed out or stopped; inspect the original intent/run, execution state remains unknown')
        if result['returncode']:
            lines = (output / 'stderr.txt').read_text(encoding='utf-8').strip().splitlines()
            raise ValueError(lines[-1] if lines else f'Training runtime process exited with status {result["returncode"]}')
        return json.loads((output / 'stdout.txt').read_text(encoding='utf-8'))


def _validate_training_baseline(baseline: dict) -> None:
    import perfctl

    perfctl.ident(baseline.get('baseline_id'))
    perfctl.commit(baseline.get('commit'), 'commit')
    for key in ('config_sha256', 'workload_fingerprint'):
        perfctl.sha(baseline.get(key), key)


def _training_records(payload: dict) -> dict:
    import base64
    from dataclasses import asdict
    import heapq
    from agent_platform.core import CONFIG, STATE, Blocked, slug
    from dev_platform import adapter
    from perf_temporal.models import Binding, Experiment
    import perfctl
    from .materials import read_raw

    project_id = slug(payload['project'])
    root, config = STATE.resolve(), CONFIG.resolve()
    prefix = 'training/projects/' + project_id + '/perf/'
    if os.name == 'nt':
        adapter.read_raw = _read_windows_contract
    files = {}

    def document(relative, *, optional=False, configuration=False):
        storage = config if configuration else root
        path = adapter.safe_file(storage, relative)
        if optional and not path.exists():
            return None
        raw = read_raw(path)
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('Training JSON must be an object: ' + relative)
        files[('config/' if configuration else 'state/') + relative] = hashlib.sha256(raw).hexdigest()
        return value

    baseline = document(prefix + 'baseline.json', optional=True)
    if baseline is not None:
        _validate_training_baseline(baseline)
    baseline_files = dict(files)

    def inspect(ident, *, detail=False):
        slug(ident)
        files.clear()
        manifest = document(prefix + 'experiments/' + ident + '/manifest.json')
        perfctl.validate(manifest)
        if manifest['experiment_id'] != ident or manifest['local_project'] != project_id:
            raise ValueError('Experiment does not belong to this project and native directory')
        registered_sha = files['state/' + prefix + 'experiments/' + ident + '/manifest.json']
        frozen = document('training/manifests/' + ident + '.json')
        if files['state/training/manifests/' + ident + '.json'] != registered_sha:
            raise ValueError('Frozen manifest bytes differ from the project registry')
        binding = Binding(ident, registered_sha, manifest['candidate_commit'], manifest['baseline_commit'])
        if frozen['candidate_sha'] != binding.candidate_sha or frozen['baseline_sha'] != binding.baseline_sha:
            raise ValueError('Manifest commit aliases differ from the original binding')
        spec = document('training/specs/' + ident + '.json')
        experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
        experiment.validate()
        manifest_path = adapter.safe_file(root, 'training/manifests/' + ident + '.json')
        if (experiment.binding != binding or experiment.manifest_uri != manifest_path.as_uri()
                or experiment.max_run_seconds != manifest['max_run_seconds']):
            raise ValueError('Experiment spec differs from its frozen manifest binding')
        baseline_error = None
        if baseline is None:
            baseline_error = 'Baseline is not present in the selected registry'
        else:
            try:
                perfctl.baseline_ok(manifest, baseline)
            except perfctl.Invalid as error:
                baseline_error = str(error)
        job_prefix = 'training/jobs/' + ident + '/'
        request = document(job_prefix + 'request.json', optional=True)
        runner_id = slug(manifest['runner_template_id'])
        runner = document('training-runners/' + runner_id + '.json', optional=True, configuration=True)
        if runner is None and request is None:
            raise ValueError('Cannot verify experiment Git repository: current runner and original job request are both missing')

        def check_runner(value):
            if (value['runner_template_id'] != runner_id or value['project'] != project_id
                    or value['repo'] != payload['repo']):
                raise ValueError('Runner does not belong to the selected project and Git repository')

        if runner is not None:
            check_runner(runner)
        if request is not None:
            if request['experiment'] != spec or request['job_id'] != 'local-perf-' + ident:
                raise ValueError('Native job request differs from the original experiment')
            check_runner(request['runner'])
        started = document(job_prefix + 'started.json', optional=True)
        result = document(job_prefix + 'result.json', optional=True)
        fence = document('training/fences/' + ident + '.json', optional=True)
        negative = document('training/negative-results/' + ident + '.json', optional=True) if detail else None
        for value in (started, result, fence, negative):
            if value is not None and value['binding'] != asdict(binding):
                raise ValueError('Training record belongs to another immutable binding')
        for value in (started, result):
            if value is not None and (request is None or value['job_id'] != request['job_id']):
                raise ValueError('Training job result has no matching original request')
        from ergora.training.materials import input_descriptor, read_materials

        inputs = input_descriptor(manifest)
        for arm, raw_material in read_materials(root, manifest).items():
            files['state/' + inputs[arm]['path']] = hashlib.sha256(raw_material).hexdigest()
        gate = None
        gate_ref = result.get('gate') if result is not None else None
        if gate_ref is not None:
            expected = adapter.safe_file(root, job_prefix + 'gate-report.json')
            if gate_ref['report'] != str(expected):
                raise ValueError('Gate report is outside the original experiment job')
            gate = document(job_prefix + 'gate-report.json')
            if files['state/' + job_prefix + 'gate-report.json'] != gate_ref['report_sha256']:
                raise ValueError('Gate report bytes differ from the original result SHA')
            if gate['binding'] != asdict(binding) or gate['manifest_sha256'] != binding.manifest_sha:
                raise ValueError('Gate report belongs to another experiment manifest')
        screen_ref = result.get('screen') if result is not None else None
        screen_report = None
        if screen_ref is not None:
            screen_name = job_prefix + 'run-output/screen-result.json'
            expected = adapter.safe_file(root, screen_name)
            if screen_ref['report'] != str(expected):
                raise ValueError('Screen report is outside its original experiment job')
            screen_report = document(screen_name)
            if (files['state/' + screen_name] != screen_ref['report_sha256']
                    or screen_report['binding'] != asdict(binding) or gate_ref is not None
                    or manifest.get('execution', {}).get('operation') != 'training-screen-v1'):
                raise ValueError('Screen result raw, operation or binding changed')
        item = {'experiment_id': ident, 'binding': asdict(binding), 'track': manifest['track'],
                'baseline_id': manifest['baseline_id'], 'workload_fingerprint': manifest['workload_fingerprint'],
                'baseline_matches': baseline_error is None, 'baseline_error': baseline_error,
                'max_run_seconds': experiment.max_run_seconds, 'runtime_status': 'not_queried',
                'job_id': request['job_id'] if request else None, 'started_recorded': started is not None,
                'recorded_result_state': result['state'] if result else None, 'fence_recorded': fence is not None,
                'execution': manifest.get('execution', {'operation': 'full-verify'}), 'screen_ref': screen_ref,
                'recorded_screen': {'result_sha256': screen_ref['report_sha256'], 'decision': screen_report['decision'],
                    'achieved_quality_tier': screen_report['achieved_quality_tier']} if screen_report else None,
                'recorded_gate': {'passed': gate['passed'], 'evidence_sha256': gate['evidence_sha256'],
                                  'report_sha256': gate_ref['report_sha256'],
                                  'mlflow_run_id': gate_ref['mlflow_run_id']} if gate else None,
                'files': dict(files)}
        if detail:
            item.update(manifest=manifest, spec=spec, current_runner=runner, job_request=request,
                        started=started, result=result, gate_report=gate, screen_report=screen_report, fence=fence, negative_result=negative)
        return item

    result = {'baseline': baseline, 'baseline_files': baseline_files, 'runtime_status': 'not_queried'}
    if payload['experiment_id'] is not None:
        result['experiment'] = inspect(payload['experiment_id'], detail=True)
    else:
        after = payload['after']
        if after is not None:
            if not isinstance(after, str) or len(after) > 2048:
                raise ValueError('Invalid experiment directory cursor')
            after = os.fsdecode(base64.b64decode(after.encode('ascii'), altchars=b'-_', validate=True))
        directory = adapter.safe_file(root, prefix + 'experiments')
        if directory.exists():
            with os.scandir(directory) as entries:
                names = heapq.nsmallest(payload['limit'] + 1, (entry.name for entry in entries
                    if not entry.name.startswith('.') and (after is None or entry.name > after)))
        else:
            names = []
        count = min(len(names), payload['limit'])
        result.update(items=[], errors=[], inspected_entries=count,
                      next_after=base64.urlsafe_b64encode(os.fsencode(names[count - 1])).decode('ascii')
                      if len(names) > count else None)
        for name in names[:count]:
            try:
                result['items'].append(inspect(name))
            except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
                result['errors'].append({'experiment_id': name, 'error': str(error)})
    return result


def _training_files_main():
    from agent_platform.core import Blocked

    try:
        result = _training_records(json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
