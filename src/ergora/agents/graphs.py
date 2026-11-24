"""Execute an explicitly selected standalone graph through original leaf runs."""

from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import os
from pathlib import Path
import shutil
from sqlite3 import Error as StateError
import tempfile
from threading import Event
import time
import uuid

from ergora.agents import backends, native_sources, runs
from ergora.configuration import validation as contracts
from ergora.definitions import agents, workflows
from ergora.storage.assets import publish_directory
from ergora.storage.state import State


_RESULT_LIMIT = 8_388_608


def _verify_sources(composition, inputs):
    from ergora.development.verification import validate_readback_source

    nodes = {node['path']: node for node in composition['instances']}
    for node in nodes.values():
        if node['kind'] != 'verify-evidence':
            continue
        binding = node['inputs']['source']
        parent = node['parent']
        while parent is not None:
            if 'input' not in binding:
                raise ValueError(f'Verification evidence source must come from a workflow root input: {node["path"]}')
            scope = nodes[parent]
            binding = scope['inputs'][binding['input']]
            parent = scope['parent']
        validate_readback_source(inputs[binding['input']])


def _bounded_json(value, limit: int) -> bytes:
    encoded = bytearray()
    for part in json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(',', ':')).iterencode(value):
        encoded.extend(part.encode('utf-8'))
        if len(encoded) > limit:
            raise ValueError(f'Complete workflow data exceeds {limit} bytes')
    return bytes(encoded)


class _GraphRun:
    def __init__(self, state, project, composition, directory, receipt, deadline, codex_config, stop_requested):
        self.state, self.project = state, project
        self.nodes = {item['path']: item for item in composition['instances']}
        self.directory, self.receipt, self.deadline = directory, receipt, deadline
        self.codex_config = codex_config
        self.stop_requested = stop_requested
        self.stop = Event()
        self.result_bytes = 0
        self.running = {}
        self.active_slots = Counter()
        self.completed = {}

    def save(self):
        path = self.directory / 'run.json'
        descriptor, name = tempfile.mkstemp(dir=self.directory, prefix='.run-')
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(_bounded_json(self.receipt, 10_000_000) + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)

    def should_stop(self):
        return self.stop.is_set() or (self.stop_requested is not None and self.stop_requested())

    def check_active(self):
        if self.should_stop():
            raise KeyboardInterrupt
        if time.monotonic() >= self.deadline:
            raise TimeoutError('The original workflow deadline expired')

    def check_leaf_admission(self):
        self.check_active()
        settled = self.collect_finished()
        self.check_active()
        if self.result_bytes >= _RESULT_LIMIT:
            raise ValueError('Workflow has no remaining result bytes')
        return settled

    def dispatch_leaf(self, executor, node, task):
        if self.result_bytes >= _RESULT_LIMIT:
            raise ValueError('Workflow has no remaining result bytes')
        path = node['path']
        limit = self.receipt['max_prompt_bytes']
        source = self.directory / f"input-{len(self.receipt['leaves']) + 1}"
        prepared = workflows.prepare_input_from_manifest(self.directory/'manifest', path,
            _bounded_json(task, limit), source, limit, input_origin='workflow-port',
            manifest_digest=self.receipt['manifest_digest'])
        self.check_leaf_admission()
        attempt = {'instance': path, 'run_id': uuid.uuid4().hex, 'input_digest': prepared['digest'], 'status': 'attempted'}
        self.receipt['leaves'].append(attempt)
        try:
            self.save()
            # Final admission observes results and stops that arrived during durable publication.
            settled = self.check_leaf_admission()
        except BaseException:
            self.stop.set()
            attempt['status'] = 'not_dispatched'
            raise
        future = executor.submit(runs.run_input, self.state, self.project['id'], source, self.receipt['timeout'], mode='text-only',
            codex_config=self.codex_config, deadline=self.deadline, input_digest=prepared['digest'], run_id=attempt['run_id'],
            expected_revision=self.project['revision'], stop_requested=self.should_stop)
        self.running[future] = attempt
        self.active_slots.update(scope['path'] for scope in node['concurrency_scopes'])
        if settled:
            self.save()

    def collect_finished(self):
        settled = False
        while finished := [future for future in self.running if future.done()]:
            for future in finished:
                attempt = self.running.pop(future)
                node = self.nodes[attempt['instance']]
                self.active_slots.subtract(scope['path'] for scope in node['concurrency_scopes'])
                self.completed[node['path']] = self.finish_leaf(future, attempt)
            settled = True
        return settled

    def finish_leaf(self, future, attempt):
        path = attempt['instance']
        try:
            job = future.result()
        except (OSError, ValueError, RecursionError, KeyboardInterrupt, StateError) as error:
            # The caller can lose the outcome after the original owner stored it.
            try:
                job = native_sources.record(self.state, self.project['id'], attempt['run_id'])
                if (job['kind'] != 'composition-agent-run' or job.get('input_digest') != attempt['input_digest']
                        or job['status'] in ('preparing', 'running')):
                    raise ValueError('No matching terminal Agent outcome')
            except (OSError, ValueError, KeyError, StateError):
                attempt['status'] = 'unknown'
                raise error
        attempt.update(status=job['status'], result_sha256=job.get('result_sha256'))
        if job['status'] != 'succeeded':
            if job['status'] == 'timed_out':
                raise TimeoutError(f'Workflow leaf reached its deadline: {path}')
            if job['status'] == 'cancelled':
                raise KeyboardInterrupt
            raise ValueError(f'Workflow leaf {path} reported {job["status"]}')
        remaining = _RESULT_LIMIT - self.result_bytes
        if remaining <= 0:
            raise ValueError('Workflow has no remaining result bytes')
        observed = runs.inspect_run(self.state, self.project['id'], attempt['run_id'], max_result_bytes=remaining)
        result = observed['result']
        if not result['available']:
            raise ValueError(f'Workflow leaf {path} cannot supply its original result within the remaining {remaining} bytes: '
                             + result['error'])
        if (not observed['input']['available'] or not observed['prompt']['available']
                or observed['input']['digest'] != attempt['input_digest'] or result['sha256'] != attempt['result_sha256']):
            raise ValueError(f'Original workflow leaf evidence is unavailable: {path}')
        self.result_bytes += result['bytes']
        return {'result': result['document']}

    def verify_evidence(self, path, source):
        from ergora.development.application import read_candidate_verification

        self.check_active()
        reads = self.receipt.setdefault('verification_reads', [])
        record = {'instance': path, 'source': source, 'status': 'attempted'}
        reads.append(record)
        self.save()
        try:
            evidence = read_candidate_verification(
                self.state, self.project['id'], source, expected_revision=self.project['revision'],
                deadline=self.deadline, stop_requested=self.should_stop)
            self.result_bytes += len(_bounded_json(evidence, _RESULT_LIMIT - self.result_bytes))
            self.check_active()
        except TimeoutError:
            record['status'] = 'timed_out'
            raise
        except KeyboardInterrupt:
            record['status'] = 'cancelled'
            raise
        except (OSError, ValueError):
            record['status'] = 'failed'
            raise
        record.update(status='validated', evidence=evidence)
        self.save()
        return {'result': evidence}

    def ports(self, path, inputs, bindings):
        return {name: inputs[binding['input']] if 'input' in binding else
                self.completed[path + '/' + binding['node']][binding['output']] for name, binding in bindings.items()}

    def ready(self, node, opened):
        return (node['parent'] in opened and all(path in self.completed for path in node['depends_on'])
                and all(self.active_slots[scope['path']] < scope['limit'] for scope in node.get('concurrency_scopes', ())))

    def workflow(self, inputs, project_limit):
        pending = {path: node for path, node in self.nodes.items() if path != 'root'}
        opened = {'root': inputs}
        children = {path: [child for level in node['levels'] for child in level]
                    for path, node in self.nodes.items() if node['kind'] == 'workflow'}
        root_limit = self.nodes['root']['limits']['concurrency']
        executor = ThreadPoolExecutor(max_workers=min(project_limit, root_limit))
        try:
            while 'root' not in self.completed:
                self.check_active()
                if self.collect_finished():
                    self.save()
                # Finalize children before their parents using frozen workflow membership.
                for path in reversed(tuple(opened)):
                    if all(child in self.completed for child in children[path]):
                        self.completed[path] = self.ports(path, opened.pop(path), self.nodes[path]['outputs'])
                if 'root' in self.completed:
                    break
                node = next((node for node in pending.values() if self.ready(node, opened)), None)
                if node is None:
                    if not self.running:
                        raise ValueError('No runnable workflow node remains')
                    wait(self.running, timeout=min(.05, max(0, self.deadline - time.monotonic())),
                         return_when=FIRST_COMPLETED)
                    continue
                path = node['path']
                del pending[path]
                if node['kind'] == 'join':
                    self.completed[path] = {'result': {dep: self.completed[dep] for dep in node['depends_on']}}
                    continue
                parent = node['parent']
                ports = self.ports(parent, opened[parent], node['inputs'])
                if node['kind'] == 'workflow':
                    opened[path] = ports
                elif node['kind'] == 'verify-evidence':
                    self.completed[path] = self.verify_evidence(path, ports['source'])
                else:
                    self.dispatch_leaf(executor, node, ports['task'])
        except BaseException:
            self.stop.set()
            raise
        finally:
            executor.shutdown()
            # The executor joins after the stop fence. Persist original terminal outcomes even after a graph failure.
            for future, attempt in self.running.items():
                try:
                    self.finish_leaf(future, attempt)
                except (OSError, ValueError, RecursionError, KeyboardInterrupt, StateError):
                    pass
        return self.completed['root']


def run_graph(state: State, project_id: str, manifest: Path, manifest_digest: str, inputs: dict, directory: Path,
              max_prompt_bytes: int, timeout: int, *, codex_config: Path | None = None, stop_requested=None) -> dict:
    """Run a bounded, dependency-ready read-only graph with no resubmission through this entry."""
    contracts.validate(timeout, {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Workflow timeout')
    contracts.validate(max_prompt_bytes, contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'], 'Input byte limit')
    deadline = time.monotonic() + timeout
    project = state.project(project_id)
    checked = workflows.inspect_manifest(manifest, material=True)
    if checked['digest'] != manifest_digest:
        raise ValueError('Workflow manifest differs from the explicitly selected digest')
    composition = checked['composition']
    if not isinstance(inputs, dict) or inputs.keys() != composition['instances'][0]['inputs'].keys():
        raise ValueError('Workflow inputs must supply exactly the declared root ports')
    _bounded_json(inputs, max_prompt_bytes)
    if any(item['kind'] == 'verify-evidence' for item in composition['instances']):
        _verify_sources(composition, inputs)
    for leaf in (item for item in composition['instances'] if item['kind'] == 'agent'):
        if any(leaf['permissions'][name] for name in ('write', 'shell', 'network')):
            raise ValueError(f'Standalone workflow requires a read-only leaf: {leaf["path"]}')
        tool = leaf['backend_request']['tool']
        if not backends.supports_mode(tool, 'text-only'):
            raise ValueError(f'Standalone workflow requires text-only support at {leaf["path"]}: {tool}')
    directory = directory.expanduser().absolute()
    manifest = Path(checked['path'])
    if directory.exists() or directory.is_symlink():
        raise ValueError('Choose a new workflow directory; the original run is retained')
    assets = [agents.library(state.root).store, workflows.library(state.root).store, manifest]
    if any(directory.resolve().is_relative_to(path.resolve()) for path in assets):
        raise ValueError('Workflow execution directory cannot be inside immutable source assets')
    receipt = {'schema_version': 1, 'kind': 'standalone-workflow-run', 'status': 'incomplete',
               'project': project_id, 'project_revision': project['revision'], 'root': composition['root'],
               'manifest_digest': manifest_digest, 'inputs': inputs, 'timeout': timeout,
               'max_prompt_bytes': max_prompt_bytes, 'leaves': [], 'formal_execution_authorized': False}
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.workflow-run-', dir=directory.parent) as temporary:
        staged = Path(temporary)/'run'
        staged.mkdir(mode=0o700)
        shutil.copytree(manifest, staged/'manifest', symlinks=True)
        if workflows.inspect_manifest(staged/'manifest')['digest'] != manifest_digest:
            raise ValueError('Workflow manifest changed while freezing the run')
        run = _GraphRun(state, project, composition, staged, receipt, deadline, codex_config, stop_requested)
        run.check_active()
        run.save()
        publish_directory(staged, directory)
    run.directory = directory
    try:
        outputs = run.workflow(inputs, composition['grant']['limits']['concurrency'])
        _bounded_json(outputs, _RESULT_LIMIT)
        run.check_active()
        receipt.update(status='succeeded', outputs=outputs)
    except TimeoutError as error:
        receipt.update(status='timed_out', error=str(error))
    except KeyboardInterrupt:
        receipt.update(status='cancelled', error='Workflow interrupted')
    except (OSError, ValueError, RecursionError, StateError) as error:
        receipt.update(status='failed', error=str(error))
    run.save()
    return receipt
