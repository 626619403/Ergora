"""Execute and observe explicitly selected standalone graphs through original leaf runs."""

from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from sqlite3 import Error as StateError
import tempfile
from threading import Event
import time
import uuid

from ergora.agents import backends, invocation, native_sources, runs
from ergora.configuration import validation as contracts
from ergora.definitions import agents, bundles, workflows
from ergora.development import dags
from ergora.storage.assets import publish_directory
from ergora.storage.state import State


_RESULT_LIMIT = 8_388_608
_RECEIPT_LIMIT = 10_000_000
_TERMINAL_STATUSES = ('succeeded', 'failed', 'cancelled', 'timed_out')
_VERIFICATION_NODES = ('verify-evidence', 'verify-fixed-check')


def _verify_sources(composition, inputs):
    from ergora.development.verification import validate_fixed_check_source, validate_readback_source

    sources = {}
    nodes = {node['path']: node for node in composition['instances']}
    for node in nodes.values():
        if node['kind'] not in _VERIFICATION_NODES:
            continue
        binding = node['inputs']['source']
        parent = node['parent']
        while parent is not None:
            if 'input' not in binding:
                raise ValueError(f'Verification evidence source must come from a workflow root input: {node["path"]}')
            scope = nodes[parent]
            binding = scope['inputs'][binding['input']]
            parent = scope['parent']
        validate = validate_fixed_check_source if node['kind'] == 'verify-fixed-check' else validate_readback_source
        sources[node['path']] = validate(inputs[binding['input']])
    return sources


def _fixed_review_context(composition, inputs, manifest_digest):
    from ergora.development.review.requests import task_identity

    selected = dags.fixed_check_review(composition)
    if selected is None:
        return None
    _, leaf = selected
    task = inputs['task']
    task_sha256 = task_identity(task)
    packet_sha256 = task.get('source_sha256')
    if not isinstance(packet_sha256, str) or re.fullmatch('[a-f0-9]{64}', packet_sha256) is None:
        raise ValueError('Fixed-check review requires a source-bound task with its original packet digest')
    return {'manifest_digest': manifest_digest, 'instance': leaf['path'], 'task_sha256': task_sha256,
            'packet_sha256': packet_sha256}


def _bounded_json(value, limit: int) -> bytes:
    encoded = bytearray()
    for part in json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(',', ':')).iterencode(value):
        encoded.extend(part.encode('utf-8'))
        if len(encoded) > limit:
            raise ValueError(f'Complete workflow data exceeds {limit} bytes')
    return bytes(encoded)


class _GraphRun:
    def __init__(self, state, project, composition, directory, receipt, deadline, codex_config, stop_requested, fixed_review):
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
        self.fixed_review = fixed_review

    def save(self):
        path = self.directory / 'run.json'
        descriptor, name = tempfile.mkstemp(dir=self.directory, prefix='.run-')
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(_bounded_json(self.receipt, _RECEIPT_LIMIT) + b'\n')
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
        options = {}
        if self.fixed_review is not None:
            gate, = self.nodes[node['parent']]['depends_on']
            options['_fixed_check_proof'] = self.completed[gate]['result']
        if 'route_choices' in node:
            schema = invocation.result_schema(['response', 'route'], review=node['role'] == 'reviewer')
            schema['properties']['artifacts']['properties']['route'] = {'type': 'string', 'enum': node['route_choices']}
            options['result_schema'] = schema
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
            expected_revision=self.project['revision'], stop_requested=self.should_stop, **options)
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
        from ergora.development.application import read_candidate_verification, read_fixed_check_proof

        self.check_active()
        reads = self.receipt.setdefault('verification_reads', [])
        record = {'instance': path, 'source': source, 'status': 'attempted'}
        reads.append(record)
        self.save()
        try:
            options = {'expected_revision': self.project['revision'], 'deadline': self.deadline,
                       'stop_requested': self.should_stop}
            if self.nodes[path]['kind'] == 'verify-fixed-check':
                evidence = read_fixed_check_proof(self.state, self.project['id'], source, self.fixed_review, **options)
            else:
                evidence = read_candidate_verification(self.state, self.project['id'], source, **options)
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

    def choose_agent(self, node, source):
        self.check_active()
        analyzer = node['depends_on'][0]
        artifacts = source.get('artifacts')
        choice = artifacts.get('route') if isinstance(artifacts, dict) else None
        if choice not in self.nodes[analyzer]['route_choices']:
            raise ValueError(f'Original analyzer result lacks an eligible route choice: {analyzer}')
        attempt = next(item for item in self.receipt['leaves'] if item['instance'] == analyzer)
        selected = None if choice == 'none' else f"{node['parent']}/{choice}"
        skipped = [path for path in node['branches'] if path != selected]
        record = {'instance': node['path'], 'choice': choice, 'eligible': node['branches'], 'selected': selected,
                  'skipped': skipped, 'source': {key: attempt[key] for key in
                                                ('instance', 'run_id', 'input_digest', 'result_sha256')}}
        self.receipt.setdefault('route_decisions', []).append(record)
        self.save()
        self.check_active()
        return {'result': {'choice': choice}}, skipped

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
                elif node['kind'] in _VERIFICATION_NODES:
                    self.completed[path] = self.verify_evidence(path, ports['source'])
                elif node['kind'] == 'choose-agent':
                    result, skipped = self.choose_agent(node, ports['source'])
                    self.completed[path] = result
                    for branch in skipped:
                        del pending[branch]
                        self.completed[branch] = {'status': 'skipped'}
                elif node['kind'] == 'agent':
                    self.dispatch_leaf(executor, node, ports['task'])
                else:
                    raise ValueError(f'Unsupported standalone workflow node: {path}')
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
    encoded_inputs = _bounded_json(inputs, max_prompt_bytes)
    fixed_review = None
    if any(item['kind'] in _VERIFICATION_NODES for item in composition['instances']):
        _verify_sources(composition, inputs)
        if any(item['kind'] == 'verify-fixed-check' for item in composition['instances']):
            # Bind exactly the frozen values that will reach the dependent leaf.
            inputs = json.loads(encoded_inputs)
            fixed_review = _fixed_review_context(composition, inputs, manifest_digest)
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
        run = _GraphRun(state, project, composition, staged, receipt, deadline, codex_config, stop_requested, fixed_review)
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


def _observed_attempts(receipt, name, paths, *, required=False):
    attempts = receipt.get(name, None if required else [])
    if not isinstance(attempts, list) or len(attempts) > len(paths):
        raise ValueError(f'Invalid graph receipt {name}')
    seen = set()
    for attempt in attempts:
        path = attempt.get('instance') if isinstance(attempt, dict) else None
        if not isinstance(path, str) or path not in paths or path in seen:
            raise ValueError(f'Unexpected or repeated instance in graph receipt {name}')
        seen.add(path)
    return attempts


def _matches_graph_input(request, manifest, instance, max_prompt_bytes):
    if not isinstance(request, dict):
        return False
    actual = (
        request.get('root'), request.get('grant'), request.get('preview_sha256'),
        request.get('instance'), request.get('input_origin'), request.get('max_prompt_bytes')
    )
    expected = (
        manifest['root'], manifest['grant'], manifest['preview_sha256'],
        instance, 'workflow-port', max_prompt_bytes
    )
    return actual == expected and native_sources.encode(actual) == native_sources.encode(expected)


def _observe_reserved_input(directory, attempt, manifest, max_prompt_bytes):
    try:
        checked = workflows.inspect_input(directory / f"input-{attempt['sequence']}")
        if checked['digest'] != attempt['input_digest'] or not _matches_graph_input(
                checked['request'], manifest, attempt['instance'], max_prompt_bytes):
            raise native_sources.ArtifactIdentityError('Reserved input differs from its original attempt or graph manifest')
    except (ValueError, OSError, RecursionError) as error:
        return native_sources.observation_failure(error)
    return {'state': 'available', 'digest': checked['digest'], 'task_sha256': checked['request']['task_sha256']}


def _observe_leaf_run(state, project, receipt, manifest, attempt, remaining_result_bytes, route_choices):
    try:
        observed = runs.inspect_run(state, project, attempt['run_id'], max_result_bytes=max(1, remaining_result_bytes))
    except native_sources.RunNotFound as error:
        return {'state': 'missing', 'error': str(error)}, 0, None
    except (OSError, StateError) as error:
        return {'state': 'unknown', 'error': str(error)}, 0, None
    except (ValueError, RecursionError) as error:
        return {'state': 'invalid', 'error': str(error)}, 0, None
    run = observed['run']
    if run.get('status') not in (*_TERMINAL_STATUSES, 'preparing', 'running', 'unknown'):
        return {'state': 'invalid', 'error': 'Original Agent run has an unsupported status'}, 0, None
    if (run.get('input_digest') != attempt['input_digest']
            or type(run.get('project_revision')) is not int
            or run.get('project_revision') != receipt['project_revision']
            or run.get('formal_execution_authorized') is not False
            or not _matches_graph_input(run.get('input_request'), manifest,
                                       attempt['instance'], receipt['max_prompt_bytes'])):
        return {'state': 'mismatch', 'error': 'Original Agent run differs from its graph attempt'}, 0, None
    source = {'state': 'available', 'status': run.get('status'),
              'record_created': run.get('started'), 'record_finished': run.get('finished')}
    evidence_fields = {'input': ('digest',), 'prompt': ('sha256', 'bytes'), 'result': ('sha256', 'bytes')}
    for name, fields in evidence_fields.items():
        evidence = observed[name]
        source[name] = ({'state': 'available', **{key: evidence[key] for key in fields}} if evidence['available']
                        else {'state': evidence['state'], 'error': evidence['error']})
    if attempt['status'] in ('attempted', 'unknown'):
        source['graph_outcome_agreement'] = 'not_recorded'
    elif attempt['status'] == source['status'] and attempt.get('result_sha256') == run.get('result_sha256'):
        source['graph_outcome_agreement'] = 'matching'
    else:
        source['graph_outcome_agreement'] = 'mismatch'
    choice = None
    if route_choices and observed['result']['available']:
        result = observed['result']['document']
        artifacts = result.get('artifacts') if isinstance(result, dict) else None
        route = artifacts.get('route') if isinstance(artifacts, dict) else None
        if isinstance(route, str) and route in route_choices:
            choice = route
    return source, source['result'].get('bytes', 0), choice


def _observe_verification(project, sequence, read, original_source, *, fixed_review=None):
    from ergora.development.verification import validate_fixed_check_source, validate_readback_source

    status = read.get('status')
    if status not in ('attempted', 'failed', 'timed_out', 'cancelled', 'validated'):
        raise ValueError('Invalid verification status in graph receipt')
    observation = {'sequence': sequence, 'instance': read['instance'], 'status': status,
                   'original_receipt': {'state': 'not_queried'}}
    try:
        validate = validate_fixed_check_source if fixed_review is not None else validate_readback_source
        locator = validate(read.get('source'))
    except ValueError:
        return {**observation, 'locator_state': 'mismatch'}
    if locator != original_source:
        return {**observation, 'locator_state': 'mismatch'}
    observation.update(locator_state='matching', locator=original_source)
    evidence = read.get('evidence')
    if evidence is None:
        evidence_state = 'missing' if status == 'validated' else 'not_recorded'
        return {**observation, 'recorded_evidence': {'state': evidence_state}}
    if (status != 'validated' or not isinstance(evidence, dict)
            or evidence.get('status') != 'validated' or evidence.get('project') != project
            or any(type(evidence.get(name)) is not type(value) or evidence.get(name) != value
                   for name, value in {**original_source, **(fixed_review or {})}.items())):
        return {**observation, 'recorded_evidence': {'state': 'mismatch'}}
    field = 'fixed_results_sha256' if fixed_review is not None else 'check_results_sha256'
    fields = (field, 'receipt_sha256') if fixed_review is not None and 'wait_seconds' in original_source else (field,)
    digests = {name: evidence.get(name) for name in fields}
    if any(not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None for value in digests.values()):
        return {**observation, 'recorded_evidence': {'state': 'invalid'}}
    return {**observation, 'recorded_evidence': {'state': 'recorded', **digests}}


def _observe_route(sequence, record, selector, attempts, choices, graph_status):
    analyzer, = selector['depends_on']
    branches = selector['branches']
    observation = {'sequence': sequence, 'instance': selector['path'], 'eligible': branches,
                   'source_instance': analyzer}
    attempt = attempts.get(analyzer)
    if attempt is None:
        return {**observation, 'state': 'missing', 'proof': 'analyzer_attempt'}
    source = {key: attempt[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}
    if record.get('source') != source or source['result_sha256'] is None or attempt['status'] != 'succeeded':
        return {**observation, 'state': 'mismatch', 'proof': 'analyzer_attempt'}
    observation['source'] = source
    original = attempt['original_run']
    if original['state'] != 'available':
        return {**observation, 'state': original['state'], 'proof': 'original_run'}
    if original['graph_outcome_agreement'] != 'matching':
        return {**observation, 'state': 'mismatch', 'proof': 'original_run'}
    for field in ('input', 'prompt', 'result'):
        if original[field]['state'] != 'available':
            return {**observation, 'state': original[field]['state'], 'proof': field}
    choice = choices.get(analyzer)
    if choice is None:
        return {**observation, 'state': 'invalid', 'proof': 'result'}
    selected = None if choice == 'none' else f"{selector['parent']}/{choice}"
    skipped = [branch for branch in branches if branch != selected]
    expected = {'instance': selector['path'], 'eligible': branches, 'source': source,
                'choice': choice, 'selected': selected, 'skipped': skipped}
    if (record != expected or any(branch in attempts for branch in skipped)
            or (graph_status == 'succeeded' and selected is not None and selected not in attempts)):
        return {**observation, 'state': 'mismatch', 'proof': 'route_decision'}
    return {**observation, 'state': 'corroborated', 'choice': choice, 'selected': selected, 'skipped': skipped}


def inspect_graph(state: State, project: str, directory: Path, manifest_digest: str) -> dict:
    """Reconstruct graph receipt and Agent observations offline without acquiring execution authority."""
    directory = directory.expanduser().absolute()
    contracts.validate(manifest_digest, contracts.COMPOSITION_MANIFEST['$defs']['digest'], 'Manifest SHA256')
    raw = native_sources.artifact(directory, 'run.json', _RECEIPT_LIMIT + 1)
    try:
        receipt = bundles.parse_json(raw.decode('utf-8'), 'Graph run receipt', finite=True)
    except RecursionError as error:
        raise ValueError('Graph run receipt has excessive nesting') from error
    if (not isinstance(receipt, dict) or receipt.get('kind') != 'standalone-workflow-run'
            or type(receipt.get('schema_version')) is not int or receipt['schema_version'] != 1
            or receipt.get('formal_execution_authorized') is not False):
        raise ValueError('Select an original standalone graph run receipt')
    if receipt.get('project') != project or receipt.get('manifest_digest') != manifest_digest:
        raise ValueError('Graph receipt differs from the selected project or manifest digest')
    checked = workflows.inspect_manifest(directory / 'manifest', material=True)
    manifest, composition = checked['manifest'], checked['composition']
    if checked['digest'] != manifest_digest or receipt.get('root') != manifest['root']:
        raise ValueError('Saved graph manifest differs from the receipt or explicitly selected digest')
    try:
        state.project(project)
    except StateError as error:
        raise ValueError('Cannot read the selected project state: ' + str(error)) from error
    nodes = composition['instances']
    root = nodes[0]
    inputs, outputs, status = (receipt.get(name) for name in ('inputs', 'outputs', 'status'))
    if (not isinstance(inputs, dict) or inputs.keys() != root['inputs'].keys()
            or status not in ('incomplete', *_TERMINAL_STATUSES)
            or (status == 'succeeded' and (not isinstance(outputs, dict) or outputs.keys() != root['outputs'].keys()))
            or (status != 'succeeded' and 'outputs' in receipt)):
        raise ValueError('Graph receipt status or ports differ from the frozen graph')
    contracts.validate(receipt.get('project_revision'), {'type': 'integer', 'minimum': 1}, 'Receipt project revision')
    contracts.validate(receipt.get('max_prompt_bytes'), contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'],
                       'Receipt input byte limit')
    contracts.validate(receipt.get('timeout'), {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Receipt workflow timeout')
    _bounded_json(inputs, receipt['max_prompt_bytes'])
    if outputs is not None:
        _bounded_json(outputs, _RESULT_LIMIT)
    sources = _verify_sources(composition, inputs)
    fixed_review = _fixed_review_context(composition, inputs, manifest_digest)
    if fixed_review is not None:
        revision = receipt['project_revision']
        if type(revision) is not int:
            raise ValueError('Fixed-check graph receipt requires an integer project revision')
        fixed_review['project_revision'] = revision
    agent_nodes = {node['path']: node for node in nodes if node['kind'] == 'agent'}
    selectors = {node['path']: node for node in nodes if node['kind'] == 'choose-agent'}
    leaves = _observed_attempts(receipt, 'leaves', agent_nodes, required=True)
    verification_reads = _observed_attempts(receipt, 'verification_reads', sources)
    route_records = _observed_attempts(receipt, 'route_decisions', selectors)
    attempts, choices, run_ids, remaining = {}, {}, set(), _RESULT_LIMIT
    digest_contract = contracts.COMPOSITION_MANIFEST['$defs']['digest']
    for sequence, leaf in enumerate(leaves, 1):
        run_id, input_digest, leaf_status = (leaf.get(name) for name in ('run_id', 'input_digest', 'status'))
        if not isinstance(run_id, str) or re.fullmatch('[a-f0-9]{32}', run_id) is None or run_id in run_ids:
            raise ValueError('Invalid or repeated Agent run ID in graph receipt')
        if leaf_status not in (*_TERMINAL_STATUSES, 'attempted', 'not_dispatched', 'unknown'):
            raise ValueError('Invalid Agent attempt status in graph receipt')
        run_ids.add(run_id)
        contracts.validate(input_digest, digest_contract, 'Attempt input SHA256')
        if leaf.get('result_sha256') is not None:
            contracts.validate(leaf['result_sha256'], digest_contract, 'Attempt result SHA256')
        attempt = {'sequence': sequence, 'instance': leaf['instance'], 'run_id': run_id, 'input_digest': input_digest,
                   'status': leaf_status, 'result_sha256': leaf.get('result_sha256')}
        attempt['reserved_input'] = _observe_reserved_input(directory, attempt, manifest, receipt['max_prompt_bytes'])
        route_choices = agent_nodes[leaf['instance']].get('route_choices', ())
        attempt['original_run'], result_bytes, choice = _observe_leaf_run(
            state, project, receipt, manifest, attempt, remaining, route_choices)
        remaining -= result_bytes
        attempts[leaf['instance']] = attempt
        if choice is not None:
            choices[leaf['instance']] = choice
    reads = [_observe_verification(project, sequence, read, sources[read['instance']], fixed_review=fixed_review)
             for sequence, read in enumerate(verification_reads, 1)]
    decisions = [_observe_route(sequence, record, selectors[record['instance']], attempts, choices, status)
                 for sequence, record in enumerate(route_records, 1)]
    recorded_paths = {'root', *attempts, *(item['instance'] for item in reads + decisions)}
    return {'schema_version': 1, 'kind': 'standalone-workflow-observation', 'project': project,
            'project_revision': receipt['project_revision'], 'root': receipt['root'], 'manifest_digest': manifest_digest,
            'graph_receipt': {'directory': str(directory), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                              'status': status, 'input_ports': list(root['inputs']),
                              'recorded_output_ports': list(outputs or {})},
            'ordering': {'agent_attempts': 'graph_receipt_reservation_order', 'verification_reads': 'graph_receipt_read_order',
                         'route_decisions': 'graph_receipt_decision_order', 'nodes': 'frozen_manifest_order'},
            'nodes': [{'instance': node['path'], 'kind': node['kind'], 'depends_on': node['depends_on'],
                       'graph_record': 'recorded' if node['path'] in recorded_paths else 'not_recorded'}
                      for node in nodes],
            'agent_attempts': list(attempts.values()), 'verification_reads': reads, 'route_decisions': decisions,
            'process_start': 'unknown',
            'stop_and_cleanup': 'unknown', 'formal_execution_authorized': False}
