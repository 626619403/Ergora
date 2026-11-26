"""Execute and observe explicitly selected standalone graphs through original leaf runs."""

from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import ExitStack
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
from sqlite3 import Error as StateError
import tempfile
from threading import Event
import time
import uuid

from ergora.agents import backends, invocation, native_sources, runs
from ergora.configuration import validation as contracts
from ergora.definitions import agents, bundles, workflows
from ergora.development import dags, native as development_native
from ergora.development.route_errors import RouteBlocked
from ergora.runtime import action_observations, budget_clock
from ergora.storage.assets import is_link, publish_directory
from ergora.storage.state import State, file_lock, resolve_home


_RESULT_LIMIT = 8_388_608
_RECEIPT_LIMIT = 10_000_000
_TERMINAL_STATUSES = ('succeeded', 'failed', 'cancelled', 'timed_out')
_VERIFICATION_NODES = ('verify-evidence', 'verify-fixed-check')
_RECOVERY_FIELDS = ('project', 'project_revision', 'root', 'manifest_digest', 'inputs', 'timeout', 'max_prompt_bytes')
_AWAITING_ROUTE = 'awaiting_route_decision'
_ROUTE_DECISION = 'route-operator-decision.json'
_FOLLOW_UP_MANIFEST = 'follow-up-manifest'
_FOLLOW_UP_INVOCATION = 'follow-up-invocation.json'
_ROUTE_ACTIONS = ('follow-up', 'finish')
_FIXED_READ_ATTEMPT = 'verification-attempt.json'
_FIXED_READ_COMPLETE = 'verification-complete.json'
_FIXED_OUTPUT_DIGESTS = ('receipt_sha256', 'fixed_results_sha256')


@dataclass(frozen=True)
class PinnedFixedReview:
    branch: str
    manifest: Path
    manifest_digest: str
    inputs: dict


class _UnknownFollowUp(ValueError):
    pass


class _TerminalFollowUp(ValueError):
    def __init__(self, observation):
        self.status = observation['terminal_status']
        super().__init__(f'Original follow-up {observation["id"]} reported {self.status}')


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
                raise RouteBlocked(node['path'], 'Verification evidence source must come from a workflow root input')
            scope = nodes[parent]
            binding = scope['inputs'][binding['input']]
            parent = scope['parent']
        validate = validate_fixed_check_source if node['kind'] == 'verify-fixed-check' else validate_readback_source
        try:
            sources[node['path']] = validate(inputs[binding['input']])
        except ValueError as error:
            raise RouteBlocked(node['path'], str(error)) from error
    return sources


def _fixed_review_context(composition, inputs, manifest_digest):
    from ergora.development.review.requests import task_identity

    selected = dags.fixed_check_review(composition)
    if selected is None:
        return None
    _, leaf = selected
    task = inputs['task']
    try:
        task_sha256 = task_identity(task)
        packet_sha256 = task.get('source_sha256')
        if not isinstance(packet_sha256, str) or re.fullmatch('[a-f0-9]{64}', packet_sha256) is None:
            raise ValueError('Fixed-check review requires a source-bound task with its original packet digest')
    except ValueError as error:
        raise RouteBlocked(leaf['path'], str(error)) from error
    return {'manifest_digest': manifest_digest, 'instance': leaf['path'], 'task_sha256': task_sha256,
            'packet_sha256': packet_sha256}


def _bounded_json(value, limit: int) -> bytes:
    encoded = bytearray()
    for part in json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(',', ':')).iterencode(value):
        encoded.extend(part.encode('utf-8'))
        if len(encoded) > limit:
            raise workflows.PromptCapacityError(f'Complete workflow data exceeds {limit} bytes')
    return bytes(encoded)


def _graph_authority_sha(receipt):
    authority = [receipt[name] for name in _RECOVERY_FIELDS]
    if 'pause_before_route' in receipt:
        authority.append(receipt['pause_before_route'])
    for name in ('fixed_follow_up', 'follow_up_parent'):
        if name in receipt:
            authority.append([name, receipt[name]])
    return hashlib.sha256(_bounded_json(authority, _RECEIPT_LIMIT)).hexdigest()


def _write_recovery_record(directory, name, record, *, preserve_order=False):
    encoded = _bounded_json(record, _RECEIPT_LIMIT) if preserve_order else native_sources.encode(record)
    with (directory / name).open('xb') as stream:
        stream.write(encoded + b'\n')
        stream.flush()
        native_sources.sync_descriptor(stream.fileno())
    native_sources.sync_directory_chain(directory)


def _enter_owner(stack, path):
    try:
        return stack.enter_context(file_lock(path, blocking=False))
    except BlockingIOError as error:
        raise ValueError('The original graph coordinator is still active') from error


def _owner_identity(stat_result):
    return [stat_result.st_dev, stat_result.st_ino]


def _leaf_result_schema(node, *, flow_map_producer=False):
    routed = 'route_choices' in node
    schema = invocation.result_schema(['response', 'route'] if routed else ['response'], review=node['role'] == 'reviewer')
    artifacts = schema['properties']['artifacts']
    if routed:
        artifacts['properties']['route'] = {'type': 'string', 'enum': node['route_choices']}
    if flow_map_producer:
        artifacts['properties']['response']['type'] = ['string', 'null']
    return schema


def _route_record(node, choice, source):
    selected = None if choice == 'none' else f"{node['parent']}/{choice}"
    return {'instance': node['path'], 'choice': choice, 'eligible': node['branches'], 'selected': selected,
            'skipped': [path for path in node['branches'] if path != selected],
            'source': {key: source[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}}


def _check_route_pause(composition, selector, recoverable):
    if not recoverable:
        raise ValueError('A route checkpoint requires an original recoverable graph')
    if not any(node['kind'] == 'choose-agent' and node['path'] == selector for node in composition['instances']):
        raise ValueError('Select an exact choose-agent instance from the frozen graph')


def _fixed_follow_up_binding(composition, selector, selection, max_prompt_bytes, *, preflight=False):
    nodes = {node['path']: node for node in composition['instances']}
    route = nodes.get(selector, {})
    if (route.get('kind') != 'choose-agent' or route['parent'] != 'root'
            or selection.branch not in route['branches']):
        raise ValueError('Fixed review follow-up must bind one original root route branch')
    selected = set(route['branches']) | set(route['depends_on']) | {selector, 'root'}
    if any(node['path'] not in selected and node['kind'] != 'join' for node in nodes.values()):
        raise ValueError('Fixed review follow-up requires one original analyzer and route')
    manifest = workflows.inspect_manifest(selection.manifest, material=True)
    if manifest['digest'] != selection.manifest_digest:
        raise ValueError('Fixed review follow-up manifest differs from its exact selection')
    child = manifest['composition']
    gate = dags.fixed_check_review(child)
    if gate is None:
        raise ValueError('Fixed review follow-up requires the exact fixed-check review workflow')
    _, leaf = gate
    branch = nodes[selection.branch]
    if any(leaf[name] != branch[name] for name in ('ref', 'role', 'backend_request')):
        raise ValueError('Fixed review follow-up reviewer differs from the original branch')
    workflows._within(leaf['permissions'], branch['permissions'], selection.branch)
    workflows._within(child['grant']['permissions'], composition['grant']['permissions'], selection.branch)
    if any(value > composition['grant']['limits'][name]
           for name, value in child['grant']['limits'].items()):
        raise ValueError('Fixed review follow-up exceeds an original graph grant limit')
    encoded = _graph_inputs(child, selection.inputs, max_prompt_bytes, recoverable=True)
    inputs = json.loads(encoded)
    _verify_sources(child, inputs)
    _fixed_review_context(child, inputs, selection.manifest_digest)
    if preflight:
        _preflight_leaves(child, inputs, max_prompt_bytes, None)
    if 'wait_seconds' in inputs['check']:
        raise ValueError('Fixed review follow-up requires a completed original check')
    root = child['instances'][0]
    projection = {'port': 'result', 'binding': root['outputs']['result'], 'producer': leaf['path']}
    return {'branch': selection.branch, 'manifest_digest': selection.manifest_digest, 'root': child['root'],
            'grant_sha256': native_sources.sha(child['grant']), 'inputs': inputs, 'output_projection': projection}


def _follow_up_invocation(receipt, checkpoint, decision, result_limit):
    binding = receipt['fixed_follow_up']
    return {'parent_recovery_sha256': receipt['recovery_sha256'], 'route_checkpoint_sha256': checkpoint,
            'decision_sha256': decision, 'binding_sha256': native_sources.sha(binding),
            'output_projection': binding['output_projection'], 'result_limit': result_limit}


def _reservation_witness(receipt, sequence, attempt):
    return {'schema_version': 1, 'sequence': sequence, 'recovery_sha256': receipt['recovery_sha256'],
            **{key: attempt.get(key) for key in ('instance', 'run_id', 'input_digest')}}


def _check_reservation(directory, receipt, sequence, attempt):
    raw = native_sources.encode(_reservation_witness(receipt, sequence, attempt)) + b'\n'
    detail = f'Saved graph reservation witness differs from its original attempt: {attempt["instance"]}'
    try:
        observed = native_sources.artifact(directory, f'reservation-{sequence}.json', len(raw))
    except (OSError, ValueError) as error:
        raise native_sources.ArtifactIdentityError(detail) from error
    if observed != raw:
        raise native_sources.ArtifactIdentityError(detail)


def _reconstruct_graph_input(composition, source, path, task, limit):
    prepared = workflows.inspect_input(source)
    expected, _ = workflows.compile_input(composition, path, _bounded_json(task, limit), limit,
                                          input_origin='workflow-port')
    if native_sources.encode(prepared['request']) != native_sources.encode(expected):
        raise native_sources.ArtifactIdentityError(
            f'Saved graph input differs from its reconstructed task or manifest: {path}')
    return prepared


def _recover_agent_result(state, project, revision, node, attempt, prepared, result_limit):
    path, run_id = node['path'], attempt['run_id']
    observed = runs.inspect_run(state, project, run_id, max_result_bytes=result_limit)
    original, result = observed['run'], observed['result']
    if original['status'] != 'succeeded':
        raise ValueError(f'Graph recovery requires a proven successful original Agent outcome: {path}')
    if (type(original.get('project_revision')) is not int
            or original['project_revision'] != revision
            or original.get('formal_execution_authorized') is not False
            or original.get('role') != node['role'] or original.get('binding') != node['backend_request']
            or original.get('policy', {}).get('mode') != 'text-only'
            or not observed['input']['available'] or observed['input']['digest'] != prepared['digest']
            or not observed['prompt']['available'] or not result['available']
            or (('result_sha256' in attempt or attempt['status'] == 'succeeded')
                and attempt.get('result_sha256') != result['sha256'])):
        raise native_sources.ArtifactIdentityError(
            f'Graph recovery requires matching original Agent input, prompt and result evidence: {path}')
    return result


def _route_checkpoint_record(receipt, recommendation):
    return {'schema_version': 1, 'recovery_sha256': receipt['recovery_sha256'], 'recommendation': recommendation}


def _checked_checkpoint_sha(receipt, recommendation):
    checkpoint = receipt.get('route_checkpoint')
    if (recommendation['selected'] is None or native_sources.encode(checkpoint)
            != native_sources.encode(_route_checkpoint_record(receipt, recommendation))):
        raise native_sources.ArtifactIdentityError('Saved route checkpoint differs from its original analyzer evidence')
    return native_sources.sha(checkpoint)


def _check_operator_decision(decision, checkpoint_sha, deadline_ns, timeout, *, now_ns=None):
    if (not isinstance(decision, dict) or decision.keys() != {
            'schema_version', 'checkpoint_sha256', 'action', 'accepted_monotonic_ns'}
            or type(decision['schema_version']) is not int or decision['schema_version'] != 1
            or decision['checkpoint_sha256'] != checkpoint_sha or decision['action'] not in _ROUTE_ACTIONS):
        raise native_sources.ArtifactIdentityError('Saved operator decision differs from the original route checkpoint')
    accepted = decision['accepted_monotonic_ns']
    if (type(accepted) is not int or not deadline_ns - timeout * 1_000_000_000 <= accepted < deadline_ns
            or (now_ns is not None and accepted > now_ns)):
        raise ValueError('Saved operator decision is outside the original graph clock')


def _decided_route(node, recommendation, decision):
    choice = recommendation['choice'] if decision['action'] == 'follow-up' else 'none'
    return {**_route_record(node, choice, recommendation['source']), 'operator_decision_sha256': native_sources.sha(decision)}


def _fixed_read_attempt(receipt, recovery, review, path, source, started):
    waiting = 'wait_seconds' in source
    window = source['wait_seconds'] if waiting else development_native.FIXED_CHECK_PROOF_TIMEOUT
    cutoff = min(recovery['deadline_monotonic_ns'], started + window * 1_000_000_000)
    return {'schema_version': 1, 'instance': path, 'recovery_sha256': receipt['recovery_sha256'],
            'mode': 'wait' if waiting else 'completed', 'source': source, 'source_sha256': native_sources.sha(source),
            'review': review, 'boot_id': recovery['clock']['boot_id'],
            'started_monotonic_ns': started, 'deadline_monotonic_ns': cutoff}


def _check_fixed_proof(receipt, review, source, evidence):
    expected = {**source, **review, 'status': 'validated', 'project': receipt['project'],
                'project_revision': receipt['project_revision']}
    digests = {'authorization_sha256', 'verification_sha256'}
    if 'wait_seconds' in source:
        digests.update(_FIXED_OUTPUT_DIGESTS)
    if (not isinstance(evidence, dict) or evidence.keys() != expected.keys() | {'job_id', 'fixed_check_ids'} | digests
            or any(type(evidence[key]) is not type(value) or evidence[key] != value for key, value in expected.items())
            or not isinstance(evidence['job_id'], str) or not evidence['job_id']
            or any(not isinstance(evidence[key], str) or re.fullmatch('[a-f0-9]{64}', evidence[key]) is None
                   for key in digests)
            or not isinstance(evidence['fixed_check_ids'], list)
            or not all(isinstance(key, str) for key in evidence['fixed_check_ids'])):
        raise native_sources.ArtifactIdentityError('Saved fixed-check proof differs from its original locator or review binding')


def _fixed_read_completion(attempt, evidence, validated, result_limit):
    return {'schema_version': 1, 'attempt_sha256': native_sources.sha(attempt), 'evidence': evidence,
            'evidence_sha256': hashlib.sha256(_bounded_json(evidence, result_limit)).hexdigest(),
            'validated_monotonic_ns': validated}


def _fixed_attempt_progress(receipt, recovery, review, gate, source, attempt, *, now_ns=None):
    started = attempt.get('started_monotonic_ns') if isinstance(attempt, dict) else None
    graph_start = recovery['deadline_monotonic_ns'] - receipt['timeout'] * 1_000_000_000
    detail = 'Saved fixed-check read attempt differs from its original cutoff or authorization'
    if type(started) is not int or started < graph_start or (now_ns is not None and started > now_ns):
        raise ValueError(detail)
    if native_sources.encode(attempt) != native_sources.encode(_fixed_read_attempt(receipt, recovery, review, gate, source, started)):
        raise native_sources.ArtifactIdentityError(detail)
    return {'instance': gate, 'source': source, 'status': 'attempted', 'attempt_sha256': native_sources.sha(attempt)}


def _check_attempted_progress(receipt, record, expected):
    if receipt.get('leaves'):
        raise native_sources.ArtifactIdentityError('Saved fixed-check read is still attempted with dependent work already recorded')
    if native_sources.encode(record) != native_sources.encode(expected):
        raise native_sources.ArtifactIdentityError('Saved verification progress differs from the original fixed-check witnesses')


def _fixed_completion_tick(attempt, completion):
    validated = completion.get('validated_monotonic_ns') if isinstance(completion, dict) else None
    if type(validated) is not int or not attempt['started_monotonic_ns'] <= validated < attempt['deadline_monotonic_ns']:
        raise ValueError('Saved fixed-check proof was not validated within its original read deadline')
    return validated


def _fixed_completed_progress(receipt, recovery, review, attempt, expected, completion, validated):
    evidence = completion.get('evidence')
    _check_fixed_proof(receipt, review, expected['source'], evidence)
    original = _fixed_read_completion(attempt, evidence, validated, recovery['result_limit'])
    if native_sources.encode(completion) != native_sources.encode(original):
        raise native_sources.ArtifactIdentityError('Saved fixed-check completion differs from its original proof')
    return {**expected, 'status': 'validated', 'evidence': evidence, 'completion_sha256': native_sources.sha(completion)}


def _join_executor(executor, futures):
    interrupted = False
    while True:
        try:
            executor.shutdown()
            # An interrupted thread join can return early on retry. The calls own their cleanup until the futures settle.
            wait(futures)
            return interrupted
        except KeyboardInterrupt:
            interrupted = True


_FLOW_MAP_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['schema_version', 'kind', 'baseline_sha256', 'source_sha256', 'map'],
    'properties': {
        'schema_version': {'type': 'integer', 'const': 1},
        'kind': {'const': 'training-flow-map'},
        'baseline_sha256': {'type': 'string', 'minLength': 64, 'maxLength': 64, 'pattern': '^[a-f0-9]{64}$'},
        'source_sha256': {'type': 'string', 'minLength': 64, 'maxLength': 64, 'pattern': '^[a-f0-9]{64}$'},
        'map': {'type': 'string', 'pattern': r'\S'},
    },
}
_FLOW_MAP_BLOCKS = {
    'unverified-producer', 'original-task-mismatch', 'missing-flow-map', 'invalid-flow-map',
    'missing-original-identities', 'baseline-mismatch', 'source-mismatch', 'oversize-flow-map',
}


class _FlowMapBlocked(ValueError):
    def __init__(self, reason, producer=None):
        super().__init__(reason)
        self.producer = producer


def _flow_map_producers(nodes):
    """Resolve the original Agent behind each required named FlowMap port."""
    producers = {}
    for path, leaf in nodes.items():
        if 'required_flow_map' not in leaf:
            continue
        scope = nodes[leaf['parent']]
        binding, parent = scope['inputs'][leaf['required_flow_map']], scope['parent']
        while 'input' in binding and parent is not None:
            scope = nodes[parent]
            binding, parent = scope['inputs'][binding['input']], scope['parent']
        if 'node' not in binding or parent is None:
            continue
        flow = nodes[f"{parent}/{binding['node']}"]
        if flow['kind'] != 'workflow' or flow['ref']['id'] != 'ergora-training-flow-map':
            continue
        result = flow['outputs'][binding['output']]
        if 'node' not in result or result['output'] != 'result':
            continue
        join = nodes[f"{flow['path']}/{result['node']}"]
        if join['kind'] != 'join' or len(join['depends_on']) != 1:
            continue
        producer, = join['depends_on']
        actor = nodes[producer]
        if actor['kind'] == 'agent' and actor['ref']['id'] == 'ergora-training-flow-analyst':
            producers[path] = producer
    return producers


def _checked_flow_map_task(composition, path, original, result, task_sha256, producer, limit):
    original_task = _bounded_json(original, limit)
    if task_sha256 != hashlib.sha256(original_task).hexdigest():
        raise _FlowMapBlocked('original-task-mismatch', producer)
    try:
        flow = bundles.parse_json(result['artifacts']['response'], 'Training FlowMap', finite=True, bounded=True)
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        raise _FlowMapBlocked('missing-flow-map', producer) from error
    try:
        contracts.validate(flow, _FLOW_MAP_SCHEMA, 'Training FlowMap')
    except (ValueError, RecursionError) as error:
        raise _FlowMapBlocked('invalid-flow-map', producer) from error
    baseline = original.get('baseline') if isinstance(original, dict) else None
    source = original.get('source') if isinstance(original, dict) else None
    if not isinstance(baseline, dict) or not isinstance(source, dict):
        raise _FlowMapBlocked('missing-original-identities', producer)
    if baseline.get('raw_sha256') != flow['baseline_sha256']:
        raise _FlowMapBlocked('baseline-mismatch', producer)
    if source.get('source_sha256') != flow['source_sha256']:
        raise _FlowMapBlocked('source-mismatch', producer)
    task = {'task': original, 'flow_map': flow, 'flow_map_producer': producer}
    try:
        bundles.check_document_tree(task, 'FlowMap profile input')
    except ValueError as error:
        raise _FlowMapBlocked('oversize-flow-map', producer) from error
    try:
        workflows.compile_input(composition, path, _bounded_json(task, limit), limit, input_origin='workflow-port')
    except workflows.PromptCapacityError as error:
        raise _FlowMapBlocked('oversize-flow-map', producer) from error
    except UnicodeEncodeError as error:
        raise _FlowMapBlocked('invalid-flow-map', producer) from error
    return task


def _flow_map_blocks(receipt, nodes):
    paths = {path for path, node in nodes.items() if 'required_flow_map' in node}
    values = _observed_attempts(receipt, 'flow_map_blocks', paths)
    for value in values:
        if (value.keys() != {'instance', 'reason', 'producer'} or not isinstance(value['reason'], str)
                or value['reason'] not in _FLOW_MAP_BLOCKS):
            raise ValueError('Invalid required FlowMap block record')
        producer = value['producer']
        if producer is not None and (not isinstance(producer, dict)
                or producer.keys() != {'instance', 'run_id', 'input_digest', 'result_sha256'}
                or any(not isinstance(item, str) for item in producer.values())):
            raise ValueError('Invalid required FlowMap producer record')
    return {value['instance']: value for value in values}


class _GraphRun:
    def __init__(self, state, project, composition, directory, receipt, deadline, codex_config, stop_requested, fixed_review,
                 *, recovery=None, lock_fd=None):
        self.state, self.project = state, project
        self.composition = composition
        self.nodes = {item['path']: item for item in composition['instances']}
        self.directory, self.receipt, self.deadline = directory, receipt, deadline
        self.codex_config = codex_config
        self.stop_requested = stop_requested
        self.stop = Event()
        self.result_bytes = 0
        self.running = {}
        self.candidate_read = None
        self.active_slots = Counter()
        self.completed = {}
        self.blocked = set()
        self.leaf_task_hashes = {}
        self.flow_map_producers = _flow_map_producers(self.nodes)
        self.flow_map_producer_paths = set(self.flow_map_producers.values())
        self.has_flow_map_gate = any('required_flow_map' in node for node in self.nodes.values())
        self.fixed_review = fixed_review
        self.recovery = recovery
        self.lock_fd = lock_fd
        self.result_limit = recovery['result_limit'] if recovery is not None else _RESULT_LIMIT
        self.unreserved = None
        self.resumed_wait = None
        self.pause_before_route = receipt.get('pause_before_route')
        self.checkpoint_sha = None
        self.operator_decision = None
        self.follow_up_output = None

    def save(self):
        self.check_owner()
        path = self.directory / 'run.json'
        descriptor, name = tempfile.mkstemp(dir=self.directory, prefix='.run-')
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(_bounded_json(self.receipt, _RECEIPT_LIMIT) + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
            if self.recovery is not None:
                native_sources.sync_directory_chain(self.directory)
        finally:
            Path(name).unlink(missing_ok=True)

    def stop_signalled(self):
        return self.stop.is_set() or (self.stop_requested is not None and self.stop_requested())

    def recovery_clock_expired(self):
        return self.recovery is not None and budget_clock.remaining(self.recovery['clock'], self.receipt['timeout']) <= 0

    def should_stop(self):
        return self.stop_signalled() or self.recovery_clock_expired()

    def operation_stop(self):
        if 'follow_up_parent' in self.receipt:
            return self.stop_signalled()
        return self.should_stop()

    def check_active(self):
        self.check_owner()
        if self.stop_signalled():
            self.fence_stop()
            raise KeyboardInterrupt
        if time.monotonic() >= self.deadline or self.recovery_clock_expired():
            raise TimeoutError('The original workflow deadline expired')

    def fence_stop(self):
        if self.recovery is not None and not (self.directory / 'stop.json').exists():
            self.check_owner()
            _write_recovery_record(self.directory, 'stop.json', {'status': 'cancelled'})

    def check_owner(self):
        if self.recovery is not None:
            lock = self.directory / '.owner.lock'
            if _owner_identity(lock.stat(follow_symlinks=False)) != self.recovery['owner_identity']:
                raise ValueError('The original graph owner lock was replaced')

    def recovery_run_id(self, path):
        return native_sources.sha([self.receipt['recovery_sha256'], path])[:32]

    def reservation_witness(self, sequence, attempt):
        return _reservation_witness(self.receipt, sequence, attempt)

    def check_reservations(self, names, leaves):
        witnesses = {name for name in names if name.startswith('reservation-')}
        expected = {f'reservation-{index}.json' for index in range(1, len(leaves) + 1)}
        if witnesses != expected:
            raise ValueError('Saved graph reservation witnesses differ from graph progress')
        for sequence, attempt in enumerate(leaves, 1):
            self.check_active()
            _check_reservation(self.directory, self.receipt, sequence, attempt)

    def check_leaf_admission(self):
        self.check_active()
        settled = self.collect_finished()
        self.check_active()
        if self.result_bytes >= self.result_limit:
            raise ValueError('Workflow has no remaining result bytes')
        return settled

    def dispatch_leaf(self, executor, node, task):
        if self.result_bytes >= self.result_limit:
            raise ValueError('Workflow has no remaining result bytes')
        path = node['path']
        limit = self.receipt['max_prompt_bytes']
        source = self.directory / f"input-{len(self.receipt['leaves']) + 1}"
        if self.unreserved is None:
            prepared = workflows.prepare_input_from_manifest(self.directory/'manifest', path,
                _bounded_json(task, limit), source, limit, input_origin='workflow-port',
                manifest_digest=self.receipt['manifest_digest'])
        else:
            prepared = self.recovery_input(source, path, task)
            if (path, prepared['digest']) != self.unreserved:
                raise ValueError('Unreserved graph input changed before its original leaf was dispatched')
            self.unreserved = None
        options = {}
        if self.fixed_review is not None:
            gate, = self.nodes[node['parent']]['depends_on']
            options['_fixed_check_proof'] = self.completed[gate]['result']
        flow_map_producer = path in self.flow_map_producer_paths
        if 'route_choices' in node or flow_map_producer:
            options['result_schema'] = _leaf_result_schema(node, flow_map_producer=flow_map_producer)
        if flow_map_producer:
            options['_allow_omitted_response'] = True
        self.check_leaf_admission()
        run_id = uuid.uuid4().hex if self.recovery is None else self.recovery_run_id(path)
        attempt = {'instance': path, 'run_id': run_id, 'input_digest': prepared['digest'], 'status': 'attempted'}
        self.receipt['leaves'].append(attempt)
        try:
            if self.recovery is not None:
                # Keep immutable pre-send identity even if progress is restored from an older snapshot.
                sequence = len(self.receipt['leaves'])
                _write_recovery_record(self.directory, f'reservation-{sequence}.json',
                                       self.reservation_witness(sequence, attempt))
            self.save()
            # Final admission observes results and stops that arrived during durable publication.
            settled = self.check_leaf_admission()
        except BaseException:
            attempt['status'] = 'not_dispatched'
            raise
        future = executor.submit(runs.run_input, self.state, self.project['id'], source, self.receipt['timeout'], mode='text-only',
            codex_config=self.codex_config, deadline=self.deadline, input_digest=prepared['digest'], run_id=attempt['run_id'],
            expected_revision=self.project['revision'], stop_requested=self.operation_stop, **options)
        self.running[future] = attempt
        self.active_slots.update(scope['path'] for scope in node['concurrency_scopes'])
        if settled:
            self.save()

    def collect_finished(self):
        settled = False
        if self.candidate_read is not None:
            future, record = self.candidate_read
            if future.done():
                self.candidate_read = None
                self.completed[record['instance']] = self.finish_verification(record, None, future.result)
                settled = True
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
        remaining = self.result_limit - self.result_bytes
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
        if path in self.flow_map_producer_paths:
            self.leaf_task_hashes[path] = observed['input']['request']['task_sha256']
        return {'result': result['document']}

    def check_fixed_read_cutoff(self, attempt):
        self.check_active()
        now = time.monotonic_ns()
        if now >= attempt['deadline_monotonic_ns']:
            raise TimeoutError('The original fixed-check read deadline expired')
        return now

    def prepare_verification(self, path, source):
        self.check_active()
        if self.resumed_wait is None:
            reads = self.receipt.setdefault('verification_reads', [])
            record = {'instance': path, 'source': source, 'status': 'attempted'}
            attempt = None
            if self.recovery is not None:
                attempt = _fixed_read_attempt(self.receipt, self.recovery, self.fixed_review, path, source, time.monotonic_ns())
                _write_recovery_record(self.directory, _FIXED_READ_ATTEMPT, attempt)
                record['attempt_sha256'] = native_sources.sha(attempt)
            reads.append(record)
            self.save()
        else:
            record, attempt = self.resumed_wait
            self.resumed_wait = None
        return record, attempt

    def read_verification(self, kind, source, attempt):
        from ergora.development.application import read_candidate_verification, read_fixed_check_proof

        options = {'expected_revision': self.project['revision'], 'deadline': self.deadline,
                   'stop_requested': self.operation_stop}
        if attempt is not None:
            self.check_fixed_read_cutoff(attempt)
            options.update(deadline=attempt['deadline_monotonic_ns'] / 1_000_000_000, lock_fd=self.lock_fd)
        if kind == 'verify-fixed-check':
            return read_fixed_check_proof(self.state, self.project['id'], source, self.fixed_review, **options)
        try:
            evidence = read_candidate_verification(self.state, self.project['id'], source, **options)
        except RuntimeError as error:
            raise ValueError(f'Candidate verification evidence reader failed: {error}') from error
        if self.should_stop():
            raise KeyboardInterrupt
        if time.monotonic() >= self.deadline:
            raise TimeoutError('The original workflow deadline expired')
        return evidence

    def finish_verification(self, record, attempt, read, *, graph_expired=False, completed_before_fence=False):
        try:
            evidence = read()
            result_bytes = len(_bounded_json(evidence, self.result_limit - self.result_bytes))
            if not completed_before_fence:
                self.check_active()
            if attempt is not None:
                _check_fixed_proof(self.receipt, self.fixed_review, record['source'], evidence)
                completion = _fixed_read_completion(attempt, evidence, self.check_fixed_read_cutoff(attempt), self.result_limit)
                _write_recovery_record(self.directory, _FIXED_READ_COMPLETE, completion, preserve_order=True)
                record['completion_sha256'] = native_sources.sha(completion)
        except TimeoutError:
            record['status'] = 'timed_out'
            raise
        except KeyboardInterrupt:
            record['status'] = 'timed_out' if graph_expired else 'cancelled'
            raise
        except Exception:
            record['status'] = 'failed'
            raise
        self.result_bytes += result_bytes
        record.update(status='validated', evidence=evidence)
        self.save()
        return {'result': evidence}

    def restore_fixed_read(self, inputs):
        if self.fixed_review is None:
            if ('verification_reads' in self.receipt
                    or any(os.path.lexists(self.directory / name) for name in (_FIXED_READ_ATTEMPT, _FIXED_READ_COMPLETE))):
                raise ValueError('Saved verification progress has no original fixed-check gate')
            return None
        gate, = (node['path'] for node in self.nodes.values() if node['kind'] == 'verify-fixed-check')
        reads = _observed_attempts(self.receipt, 'verification_reads', {gate})
        if len(reads) != 1:
            raise ValueError('Recovery requires the original completed fixed-check proof')
        try:
            attempt = native_sources.packet(self.directory, _FIXED_READ_ATTEMPT, confirm_durable=True)
        except FileNotFoundError as error:
            raise ValueError('Recovery requires the immutable original fixed-check read attempt') from error
        source = inputs['check']
        expected = _fixed_attempt_progress(self.receipt, self.recovery, self.fixed_review, gate, source, attempt,
                                           now_ns=time.monotonic_ns())
        record, = reads
        pending = record.get('status') == 'attempted'
        if pending:
            _check_attempted_progress(self.receipt, record, expected)
            if any(path.name.startswith(('input-', 'reservation-')) for path in self.directory.iterdir()):
                raise ValueError('Saved fixed-check read is still attempted with dependent work already recorded')
        if not os.path.lexists(self.directory / _FIXED_READ_COMPLETE):
            if not pending or attempt['mode'] != 'wait':
                raise ValueError('Recovery requires the original completed fixed-check proof')
            self.check_fixed_read_cutoff(attempt)
            run_id = self.recovery_run_id(self.fixed_review['instance'])
            try:
                entries = (self.state.root / 'runs').iterdir()
                if any(path.name == run_id or path.name.startswith(run_id + '.') for path in entries):
                    raise ValueError('Saved fixed-check wait has dependent Agent run artifacts')
            except FileNotFoundError:
                pass
            self.resumed_wait = record, attempt
            return None
        # A present completion must corroborate the proof, including after an interrupted write.
        completion = native_sources.packet(self.directory, _FIXED_READ_COMPLETE, confirm_durable=True)
        validated = _fixed_completion_tick(attempt, completion)
        if validated > self.check_fixed_read_cutoff(attempt):
            raise ValueError('Saved fixed-check proof validation time is in the future')
        validated_record = _fixed_completed_progress(self.receipt, self.recovery, self.fixed_review,
                                                     attempt, expected, completion, validated)
        if not pending and native_sources.encode(record) != native_sources.encode(validated_record):
            raise ValueError('Saved verification progress differs from the original fixed-check witnesses')
        evidence = validated_record['evidence']
        self.result_bytes += len(_bounded_json(evidence, self.result_limit - self.result_bytes))
        self.completed[gate] = {'result': evidence}
        return attempt, record, validated_record

    def recheck_fixed_read(self, restored):
        if restored is None:
            return
        from ergora.development.application import read_fixed_check_proof

        attempt, record, validated_record = restored
        source, saved = self.receipt['inputs']['check'], validated_record['evidence']
        wait_seconds = source.get('wait_seconds')
        locator = source
        options = {}
        if wait_seconds is not None:
            locator = {key: value for key, value in source.items() if key != 'wait_seconds'}
            locator.update({key: saved[key] for key in _FIXED_OUTPUT_DIGESTS})
            options['original_wait_seconds'] = wait_seconds
        self.check_fixed_read_cutoff(attempt)
        proof = read_fixed_check_proof(self.state, self.project['id'], locator, self.fixed_review,
            expected_revision=self.project['revision'], deadline=attempt['deadline_monotonic_ns'] / 1_000_000_000,
            stop_requested=self.operation_stop, lock_fd=self.lock_fd, **options)
        self.check_fixed_read_cutoff(attempt)
        if (not isinstance(proof, dict) or proof.keys() != saved.keys() - {'wait_seconds'}
                or _bounded_json({**source, **proof}, self.result_limit) != _bounded_json(saved, self.result_limit)):
            raise ValueError('Original native proof differs from the saved fixed-check proof')
        record.update(validated_record)

    def route_decision(self, node, source):
        analyzer = node['depends_on'][0]
        artifacts = source.get('artifacts')
        choice = artifacts.get('route') if isinstance(artifacts, dict) else None
        if choice not in self.nodes[analyzer]['route_choices']:
            raise ValueError(f'Original analyzer result lacks an eligible route choice: {analyzer}')
        attempt = next(item for item in self.receipt['leaves'] if item['instance'] == analyzer)
        return _route_record(node, choice, attempt)

    def choose_agent(self, node, source):
        self.check_active()
        record = self.route_decision(node, source)
        if node['path'] == self.pause_before_route and record['selected'] is not None:
            if self.operator_decision is None:
                while self.running:
                    self.check_active()
                    self.wait_for_work()
                    if self.collect_finished():
                        self.save()
                self.check_active()
                self.receipt['route_checkpoint'] = _route_checkpoint_record(self.receipt, record)
                return None
            record = _decided_route(node, record, self.operator_decision)
            if self.selects_follow_up(record):
                self.follow_up_output = self.fixed_follow_up(record, launch=True)
        self.receipt.setdefault('route_decisions', []).append(record)
        self.save()
        self.check_active()
        return record

    def check_route_checkpoint(self, recommendation):
        self.checkpoint_sha = _checked_checkpoint_sha(self.receipt, recommendation)
        if self.operator_decision is not None:
            _check_operator_decision(self.operator_decision, self.checkpoint_sha, self.recovery['deadline_monotonic_ns'],
                                     self.receipt['timeout'], now_ns=time.monotonic_ns())

    def publish_route_decision(self, decision):
        self.publish_route_record(_ROUTE_DECISION, decision)

    def publish_route_record(self, name, record):
        raw = native_sources.encode(record) + b'\n'
        destination = self.directory / name
        staged = self.directory / f'.{name}.pending'
        # The original coordinator lock gives each retry exclusive use of this staging path.
        staged.unlink(missing_ok=True)
        descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                native_sources.sync_descriptor(stream.fileno())
            self.check_active()
            os.link(staged, destination)
        finally:
            staged.unlink(missing_ok=True)
        saved = native_sources.artifact(self.directory, name, len(raw), confirm_durable=True)
        if saved != raw:
            raise native_sources.ArtifactIdentityError('Published route record differs from its complete packet')

    def accept_route_action(self, checkpoint_sha, action):
        if checkpoint_sha != self.checkpoint_sha:
            raise ValueError('Select the exact original route checkpoint SHA256')
        if self.operator_decision is not None:
            if self.operator_decision['action'] != action:
                raise ValueError('The original route checkpoint already has a different decision')
            return
        if self.receipt['status'] != _AWAITING_ROUTE:
            raise ValueError('The original graph is not awaiting a route decision')
        self.check_active()
        decision = {'schema_version': 1, 'checkpoint_sha256': checkpoint_sha, 'action': action,
                    'accepted_monotonic_ns': time.monotonic_ns()}
        _check_operator_decision(decision, checkpoint_sha, self.recovery['deadline_monotonic_ns'], self.receipt['timeout'])
        self.publish_route_decision(decision)
        self.operator_decision = decision
        self.check_active()

    def selects_follow_up(self, record):
        return ('fixed_follow_up' in self.receipt and record['instance'] == self.pause_before_route
                and record['selected'] == self.receipt['fixed_follow_up']['branch'])

    def fixed_follow_up(self, route, *, launch=False):
        binding = self.receipt['fixed_follow_up']
        manifest = self.directory / _FOLLOW_UP_MANIFEST
        selected = PinnedFixedReview(binding['branch'], manifest, binding['manifest_digest'], binding['inputs'])
        checked = _fixed_follow_up_binding(self.composition, self.pause_before_route, selected,
                                           self.receipt['max_prompt_bytes'])
        if native_sources.encode(checked) != native_sources.encode(binding):
            raise ValueError('Fixed review follow-up differs from the original binding')
        self.check_route_checkpoint(self.receipt['route_checkpoint']['recommendation'])
        decision = native_sources.sha(self.operator_decision)
        if self.operator_decision['action'] != 'follow-up' or route['operator_decision_sha256'] != decision:
            raise ValueError('Fixed review follow-up requires its original operator decision')
        invocation_record = _follow_up_invocation(
            self.receipt, self.checkpoint_sha, decision, self.result_limit - self.result_bytes)
        child_id = native_sources.sha(invocation_record)
        child = self.directory / ('follow-up-' + child_id)
        marker = self.directory / _FOLLOW_UP_INVOCATION
        if os.path.lexists(marker):
            observed = native_sources.packet(self.directory, _FOLLOW_UP_INVOCATION, confirm_durable=True)
            if observed != invocation_record:
                raise ValueError('Saved follow-up invocation differs from the original selected route')
        elif launch and not os.path.lexists(child):
            self.check_active()
            self.publish_route_record(_FOLLOW_UP_INVOCATION, invocation_record)
            self.check_active()
            check = binding['inputs']['check']
            action = action_observations.FixedCheckStatus(check['operation_id'], check['job_sha256'])
            status = action_observations.observe(action, self.project, self.state.root, deadline=self.deadline,
                                                 stop_requested=self.stop_signalled)
            if (status['status'] != 'succeeded' or status['cleanup_confirmed'] is not True
                    or status['stop_requested'] is not False
                    or any(status.get(key) != value for key, value in check.items())):
                raise ValueError('Original follow-up fixed check does not support the bound review')
            self.check_active()
            _run_graph(self.state, self.project['id'], manifest, binding['manifest_digest'], binding['inputs'], child,
                       self.receipt['max_prompt_bytes'], self.receipt['timeout'], recoverable=True,
                       follow_up_parent=(self, child_id, invocation_record['result_limit']))
        else:
            raise ValueError('Original follow-up child has no saved invocation')
        return self.read_fixed_follow_up(child, child_id, invocation_record)

    def read_fixed_follow_up(self, child, child_id, invocation_record):
        self.check_active()
        observed, result = _read_fixed_follow_up(self.state, self.project['id'], self.receipt, self.recovery,
                                                  child, child_id, invocation_record)
        self.check_active()
        if result is None:
            if observed['terminal_status'] is not None:
                raise _TerminalFollowUp(observed)
            raise _UnknownFollowUp('Original follow-up attempt has no proven successful outcome')
        return result['document'], result['bytes']

    def complete_route(self, record, pending):
        self.completed[record['instance']] = {'result': {'choice': record['choice']}}
        if self.selects_follow_up(record):
            if self.follow_up_output is None:
                self.follow_up_output = self.fixed_follow_up(record)
            selected = record['selected']
            output, size = self.follow_up_output
            if size > self.result_limit - self.result_bytes:
                raise ValueError('Original follow-up exceeds the remaining graph result size')
            self.result_bytes += size
            del pending[selected]
            self.completed[selected] = {'result': output}
        for branch in record['skipped']:
            del pending[branch]
            self.completed[branch] = {'status': 'skipped'}

    def ports(self, path, inputs, bindings):
        return {name: inputs[binding['input']] if 'input' in binding else
                self.completed[path + '/' + binding['node']][binding['output']] for name, binding in bindings.items()}

    def ready(self, node, opened):
        return (node['parent'] in opened and all(path in self.completed for path in node['depends_on'])
                and all(self.active_slots[scope['path']] < scope['limit'] for scope in node.get('concurrency_scopes', ())))

    def block_node(self, path):
        self.blocked.add(path)
        self.completed[path] = {'status': 'blocked'}

    def propagate_blocks(self, pending, opened):
        if not self.blocked:
            return False
        settled = False
        for path, node in tuple(pending.items()):
            if node['parent'] in opened and any(dependency in self.blocked for dependency in node['depends_on']):
                del pending[path]
                self.block_node(path)
                settled = True
        return settled

    def flow_map_task(self, node, original, result):
        path = self.flow_map_producers.get(node['path'])
        if path is None or not isinstance(result, dict) or result.keys() != {path}:
            raise _FlowMapBlocked('unverified-producer')
        produced = result[path]
        if not isinstance(produced, dict) or produced != self.completed.get(path):
            raise _FlowMapBlocked('unverified-producer')
        attempt = next((row for row in self.receipt['leaves'] if row['instance'] == path), None)
        if attempt is None or attempt['status'] != 'succeeded' or attempt.get('result_sha256') is None:
            raise _FlowMapBlocked('unverified-producer')
        producer = {key: attempt[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}
        return _checked_flow_map_task(self.composition, node['path'], original, produced['result'],
                                      self.leaf_task_hashes.get(path), producer, self.receipt['max_prompt_bytes'])

    def agent_task(self, node, opened):
        parent = node['parent']
        task = self.ports(parent, opened[parent], node['inputs'])['task']
        if 'required_flow_map' in node:
            return self.flow_map_task(node, task, opened[parent][node['required_flow_map']])
        return task

    def record_flow_map_block(self, path, error, *, original=None):
        record = {'instance': path, 'reason': str(error), 'producer': error.producer}
        if original is None:
            self.receipt.setdefault('flow_map_blocks', []).append(record)
        elif original != record:
            raise ValueError(f'Saved FlowMap block differs from its original artifact: {path}')
        self.block_node(path)

    def workflow_state(self, inputs):
        pending = {path: node for path, node in self.nodes.items() if path != 'root' and path not in self.completed}
        opened = {'root': inputs}
        children = {path: [child for level in node['levels'] for child in level]
                    for path, node in self.nodes.items() if node['kind'] == 'workflow'}
        return pending, opened, children

    def finalize_workflows(self, opened, children):
        for path in reversed(tuple(opened)):
            if all(child in self.completed for child in children[path]):
                inputs = opened.pop(path)
                if any(child in self.blocked for child in children[path]):
                    self.block_node(path)
                else:
                    self.completed[path] = self.ports(path, inputs, self.nodes[path]['outputs'])

    def open_structure(self, node, opened):
        path, parent = node['path'], node['parent']
        if node['kind'] == 'join':
            self.completed[path] = {'result': {dep: self.completed[dep] for dep in node['depends_on']}}
        else:
            opened[path] = self.ports(parent, opened[parent], node['inputs'])

    def recovery_input(self, source, path, task):
        return _reconstruct_graph_input(self.composition, source, path, task, self.receipt['max_prompt_bytes'])

    def recover_leaf(self, node, attempt, prepared):
        path, run_id = node['path'], attempt.get('run_id')
        if run_id != self.recovery_run_id(path) or attempt.get('input_digest') != prepared['digest']:
            raise ValueError(f'Saved Agent reservation differs from its original identity: {path}')
        status = attempt.get('status')
        if status not in ('attempted', 'succeeded'):
            raise ValueError(f'Graph recovery is blocked by the prior {status!r} Agent attempt: {path}')
        remaining = self.result_limit - self.result_bytes
        if remaining <= 0:
            raise ValueError('Original leaves exceed the graph result capacity')
        result = _recover_agent_result(self.state, self.project['id'], self.project['revision'], node, attempt,
                                       prepared, remaining)
        flow_map_producer = path in self.flow_map_producer_paths
        invocation.validate_result(result['document'], _leaf_result_schema(node, flow_map_producer=flow_map_producer),
                                   allow_omitted_response=flow_map_producer)
        self.result_bytes += result['bytes']
        attempt.update(status='succeeded', result_sha256=result['sha256'])
        if path in self.flow_map_producer_paths:
            self.leaf_task_hashes[path] = observed['input']['request']['task_sha256']
        self.completed[path] = {'result': result['document']}

    def recover(self, inputs):
        agent_nodes = {path: node for path, node in self.nodes.items() if node['kind'] == 'agent'}
        selectors = {path: node for path, node in self.nodes.items() if node['kind'] == 'choose-agent'}
        decisions = deque(_observed_attempts(self.receipt, 'route_decisions', selectors))
        leaves = _observed_attempts(self.receipt, 'leaves', agent_nodes, required=True)
        reserved = {item['instance'] for item in leaves}
        names = {entry.name for entry in self.directory.iterdir()}
        checkpoint_saved = 'route_checkpoint' in self.receipt
        if ((self.receipt['status'] == _AWAITING_ROUTE or _ROUTE_DECISION in names) and not checkpoint_saved
                or (checkpoint_saved and self.pause_before_route is None)):
            raise ValueError('Saved graph progress is missing original route checkpoint authority')
        if checkpoint_saved and self.receipt['status'] == 'incomplete' and _ROUTE_DECISION not in names:
            raise ValueError('Saved graph progress is missing the original operator decision')
        if _ROUTE_DECISION in names:
            self.operator_decision = native_sources.packet(self.directory, _ROUTE_DECISION, confirm_durable=True)
            if not isinstance(self.operator_decision, dict):
                raise ValueError('Saved operator decision is invalid')
        self.check_reservations(names, leaves)
        expected_slots = {f'input-{index}' for index in range(1, len(leaves) + 1)}
        next_slot = f'input-{len(leaves) + 1}'
        slots = {name for name in names if name.startswith('input-')}
        if slots not in (expected_slots, expected_slots | {next_slot}):
            raise ValueError('Saved graph input slots differ from the original reservations')
        pending, opened, children = self.workflow_state(inputs)
        original_blocks = _flow_map_blocks(self.receipt, self.nodes)

        def advance_progress():
            while True:
                self.check_active()
                self.finalize_workflows(opened, children)
                if self.propagate_blocks(pending, opened):
                    continue
                if decisions:
                    record = decisions[0]
                    selector = selectors[record['instance']]
                    if self.ready(selector, opened):
                        parent = selector['parent']
                        source = self.ports(parent, opened[parent], selector['inputs'])['source']
                        expected = self.route_decision(selector, source)
                        authority = 'analyzer result'
                        if selector['path'] == self.pause_before_route and expected['selected'] is not None:
                            self.check_route_checkpoint(expected)
                            if self.operator_decision is None:
                                raise ValueError('Saved route depends on a missing original operator decision')
                            expected = _decided_route(selector, expected, self.operator_decision)
                            authority = 'operator decision'
                        if native_sources.encode(record) != native_sources.encode(expected):
                            raise ValueError(f'Saved route decision differs from its original {authority}: {selector["path"]}')
                        decisions.popleft()
                        del pending[selector['path']]
                        self.complete_route(expected, pending)
                        continue
                structural = next((node for node in pending.values()
                                   if node['kind'] in ('workflow', 'join') and self.ready(node, opened)), None)
                if structural is not None:
                    del pending[structural['path']]
                    self.open_structure(structural, opened)
                    continue
                if not self.has_flow_map_gate:
                    return
                for gated in tuple(pending.values()):
                    if 'required_flow_map' not in gated or not self.ready(gated, opened):
                        continue
                    path = gated['path']
                    try:
                        self.agent_task(gated, opened)
                    except _FlowMapBlocked as error:
                        self.record_flow_map_block(path, error, original=original_blocks.pop(path, None))
                        del pending[path]
                        break
                    if path in original_blocks:
                        raise ValueError(f'Saved FlowMap block has no matching original artifact failure: {path}')
                else:
                    return

        def task_at(path):
            advance_progress()
            node = pending.get(path)
            if node is None or node['kind'] != 'agent' or not self.ready(node, opened):
                raise ValueError(f'Saved graph input is unreachable through its original dependencies: {path}')
            return self.agent_task(node, opened)

        for sequence, attempt in enumerate(leaves, 1):
            path = attempt['instance']
            prepared = self.recovery_input(self.directory / f'input-{sequence}', path, task_at(path))
            self.recover_leaf(agent_nodes[path], attempt, prepared)
            del pending[path]
        advance_progress()
        if original_blocks:
            raise ValueError('Saved FlowMap block is unreachable from its original producer')
        if decisions:
            raise ValueError(f'Saved route decision is unreachable through its original dependencies: {decisions[0]["instance"]}')
        if checkpoint_saved and self.checkpoint_sha is None:
            selector = pending.get(self.pause_before_route)
            if selector is None or not self.ready(selector, opened):
                raise ValueError('Saved route checkpoint is unreachable through its original dependencies')
            source = self.ports(selector['parent'], opened[selector['parent']], selector['inputs'])['source']
            self.check_route_checkpoint(self.route_decision(selector, source))
        for path in agent_nodes.keys() - reserved:
            self.check_active()
            if native_sources.run_id_exists(self.state, self.recovery_run_id(path)):
                raise ValueError(f'An Agent run ID is already recorded outside the graph reservations: {path}')
        if next_slot in slots:
            source = self.directory / next_slot
            path = workflows.inspect_input(source)['request']['instance']
            prepared = self.recovery_input(source, path, task_at(path))
            self.unreserved = (path, prepared['digest'])

    def wait_for_work(self):
        futures = list(self.running)
        if self.candidate_read is not None:
            futures.append(self.candidate_read[0])
        wait(futures, timeout=min(.05, max(0, self.deadline - time.monotonic())), return_when=FIRST_COMPLETED)

    def workflow(self, inputs, project_limit):
        pending, opened, children = self.workflow_state(inputs)
        root_limit = self.nodes['root']['limits']['concurrency']
        executor = ThreadPoolExecutor(max_workers=min(project_limit, root_limit))
        # Keep one original candidate read at a time, alongside the frozen Agent capacity.
        reader = ThreadPoolExecutor(max_workers=1)
        graph_aborted = False
        graph_expired = False
        completed_before_fence = False
        try:
            while 'root' not in self.completed:
                self.check_active()
                if self.collect_finished():
                    self.save()
                # Finalize children before their parents using frozen workflow membership.
                self.finalize_workflows(opened, children)
                if self.propagate_blocks(pending, opened):
                    continue
                if 'root' in self.completed:
                    break
                node = next((node for node in pending.values() if self.ready(node, opened)
                             and (node['kind'] != 'verify-evidence' or self.candidate_read is None)
                             and (self.unreserved is None or node['kind'] != 'agent'
                                  or node['path'] == self.unreserved[0])), None)
                if node is None:
                    if not self.running and self.candidate_read is None:
                        raise ValueError('No runnable workflow node remains')
                    self.wait_for_work()
                    continue
                path = node['path']
                del pending[path]
                if node['kind'] in ('workflow', 'join'):
                    self.open_structure(node, opened)
                    continue
                if node['kind'] == 'agent':
                    try:
                        task = self.agent_task(node, opened)
                    except _FlowMapBlocked as error:
                        self.record_flow_map_block(path, error)
                        self.save()
                    else:
                        self.dispatch_leaf(executor, node, task)
                    continue
                parent = node['parent']
                ports = self.ports(parent, opened[parent], node['inputs'])
                if node['kind'] == 'verify-evidence':
                    record, attempt = self.prepare_verification(path, ports['source'])
                    future = reader.submit(self.read_verification, node['kind'], ports['source'], attempt)
                    self.candidate_read = future, record
                elif node['kind'] == 'verify-fixed-check':
                    record, attempt = self.prepare_verification(path, ports['source'])
                    self.completed[path] = self.finish_verification(record, attempt,
                        lambda: self.read_verification(node['kind'], ports['source'], attempt))
                elif node['kind'] == 'choose-agent':
                    route = self.choose_agent(node, ports['source'])
                    if route is None:
                        return None
                    self.complete_route(route, pending)
                else:
                    raise ValueError(f'Unsupported standalone workflow node: {path}')
        except BaseException as error:
            graph_aborted = True
            graph_expired = isinstance(error, TimeoutError) and time.monotonic() >= self.deadline
            # Reuse a passing read that settled before a disjoint branch failed and fenced further dispatch.
            completed_before_fence = (self.candidate_read is not None and self.candidate_read[0].done()
                                      and isinstance(error, Exception) and not isinstance(error, TimeoutError))
            self.stop.set()
            if isinstance(error, KeyboardInterrupt):
                self.fence_stop()
            raise
        finally:
            candidate_futures = () if self.candidate_read is None else (self.candidate_read[0],)
            reader_interrupted = _join_executor(reader, candidate_futures)
            executor_interrupted = _join_executor(executor, self.running)
            # Join after the stop fence, then retain original terminal outcomes after a graph failure.
            if self.candidate_read is not None:
                future, record = self.candidate_read
                try:
                    self.finish_verification(record, None, future.result, graph_expired=graph_expired,
                                             completed_before_fence=completed_before_fence)
                except (Exception, KeyboardInterrupt):
                    pass
            for future, attempt in self.running.items():
                try:
                    self.finish_leaf(future, attempt)
                except (Exception, KeyboardInterrupt):
                    if attempt['status'] == 'attempted':
                        attempt['status'] = 'unknown'
            if not graph_aborted and (reader_interrupted or executor_interrupted):
                raise KeyboardInterrupt
        return self.completed['root']


def _graph_inputs(composition, inputs, max_prompt_bytes, *, recoverable=False):
    bundles.check_document_tree(inputs, 'Workflow inputs')
    if not isinstance(inputs, dict) or inputs.keys() != composition['instances'][0]['inputs'].keys():
        raise RouteBlocked(composition['instances'][0]['path'], 'Workflow inputs must supply exactly the declared root ports')
    encoded_inputs = _bounded_json(inputs, max_prompt_bytes)
    if recoverable:
        allowed = {'agent', 'workflow', 'join', 'choose-agent', 'verify-fixed-check'}
        unsupported = next((node for node in composition['instances'] if node['kind'] not in allowed), None)
        if unsupported is not None:
            raise RouteBlocked(unsupported['path'],
                'Recoverable graphs support only Agent, Workflow, all-join, choose-agent and the fixed-check review gate')
        if any(node['kind'] == 'verify-fixed-check' for node in composition['instances']):
            dags.fixed_check_review(composition)
    for leaf in (item for item in composition['instances'] if item['kind'] == 'agent'):
        if any(leaf['permissions'][name] for name in ('write', 'shell', 'network')):
            raise RouteBlocked(leaf['path'], 'Standalone workflow requires a read-only leaf')
        tool = leaf['backend_request']['tool']
        if not backends.supports_mode(tool, 'text-only'):
            raise RouteBlocked(leaf['path'], f'Standalone workflow requires text-only support: {tool}')
    return encoded_inputs


def graph_options(max_prompt_bytes, timeout, *, recoverable, codex_config):
    contracts.validate(timeout, {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Workflow timeout')
    contracts.validate(max_prompt_bytes, contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'], 'Input byte limit')
    if recoverable and codex_config is not None:
        raise ValueError('Recoverable graphs do not support an explicit Codex configuration')


def _root_task_port(leaf, nodes):
    binding, parent = leaf['inputs']['task'], leaf['parent']
    while 'input' in binding:
        if parent == 'root':
            return binding['input']
        scope = nodes[parent]
        binding = scope['inputs'][binding['input']]
        parent = scope['parent']
    return None


def _preflight_leaves(composition, inputs, max_prompt_bytes, codex_config):
    nodes = {node['path']: node for node in composition['instances']}
    branches = [path for node in nodes.values() if node['kind'] == 'choose-agent' for path in node['branches']]
    for path, leaf in nodes.items():
        if leaf['kind'] != 'agent' or any(path == branch or path.startswith(branch + '/') for branch in branches):
            continue
        try:
            runs.preflight_graph_leaf(leaf, codex_config)
            port = _root_task_port(leaf, nodes)
            if port is not None:
                workflows.compile_input(composition, path, _bounded_json(inputs[port], max_prompt_bytes), max_prompt_bytes,
                                        input_origin='workflow-port')
        except (OSError, ValueError) as error:
            raise RouteBlocked(path, str(error)) from error


def preflight_graph(composition, inputs, max_prompt_bytes, *, manifest_digest=None, recoverable=False,
                    pause_before_route=None, codex_config=None):
    """Validate the same selected graph and declared port values before reserving a run."""
    if pause_before_route is not None:
        _check_route_pause(composition, pause_before_route, recoverable)
    encoded = _graph_inputs(composition, inputs, max_prompt_bytes, recoverable=recoverable)
    _verify_sources(composition, inputs)
    fixed = None
    if any(node['kind'] == 'verify-fixed-check' for node in composition['instances']):
        fixed = _fixed_review_context(composition, json.loads(encoded), manifest_digest)
    _preflight_leaves(composition, inputs, max_prompt_bytes, codex_config)
    return encoded, fixed


def _execute_graph(run, inputs, composition):
    receipt = run.receipt
    try:
        outputs = run.workflow(inputs, composition['grant']['limits']['concurrency'])
        if outputs is not None:
            _bounded_json(outputs, run.result_limit)
        run.check_active()
        if outputs is None:
            receipt['status'] = _AWAITING_ROUTE
        elif run.blocked:
            receipt.update(status='failed', error='Required training FlowMap evidence blocked a dependent Agent')
        else:
            receipt.update(status='succeeded', outputs=outputs)
    except TimeoutError as error:
        receipt.update(status='timed_out', error=str(error))
    except KeyboardInterrupt:
        run.fence_stop()
        receipt.update(status='cancelled', error='Workflow interrupted')
    except _UnknownFollowUp:
        raise
    except _TerminalFollowUp as error:
        if error.status == 'cancelled':
            run.fence_stop()
        receipt.update(status=error.status, error=str(error))
    except (OSError, ValueError, RecursionError, StateError) as error:
        receipt.update(status='failed', error=str(error))
    run.save()
    return receipt


def _saved_graph_deadline(recovery, timeout, *, now_ns=None):
    clock, deadline_ns = recovery['clock'], recovery['deadline_monotonic_ns']
    if (not isinstance(clock, dict) or clock.keys() != set(budget_clock.FIELDS)
            or type(deadline_ns) is not int or deadline_ns < timeout * 1_000_000_000
            or (now_ns is not None and now_ns + timeout * 1_000_000_000 < deadline_ns)):
        raise ValueError('Saved graph clock or deadline is invalid')
    budget_clock.validate(clock, timeout)
    return deadline_ns / 1_000_000_000


def _graph_deadline(recovery, timeout):
    deadline = _saved_graph_deadline(recovery, timeout, now_ns=time.monotonic_ns())
    clock = recovery['clock']
    if time.monotonic() >= deadline or budget_clock.remaining(clock, timeout) <= 0:
        raise TimeoutError('The original workflow deadline expired')
    return deadline


def _check_recovery_authority(receipt, recovery, directory, state_home, owner_identity):
    detail = 'Recovery authorization differs from the original graph, directory or State home'
    if (not isinstance(recovery, dict) or recovery.keys() != {
            'schema_version', 'clock', 'deadline_monotonic_ns', 'result_limit', 'directory', 'state_home',
            'authority_sha256', 'owner_identity'}
            or type(recovery['schema_version']) is not int or recovery['schema_version'] != 2):
        raise ValueError(detail)
    if (recovery['directory'] != str(directory) or recovery['state_home'] != str(state_home)
            or native_sources.encode(recovery['owner_identity']) != native_sources.encode(owner_identity)
            or recovery['authority_sha256'] != _graph_authority_sha(receipt)
            or receipt.get('recovery_sha256') != native_sources.sha(recovery)):
        raise native_sources.ArtifactIdentityError(detail)


def _check_recovery_result_limit(recovery):
    limit = recovery['result_limit']
    if type(limit) is not int or not 1 <= limit <= _RESULT_LIMIT:
        raise ValueError('Saved graph result capacity is unsupported')


def run_graph(state: State, project_id: str, manifest: Path, manifest_digest: str, inputs: dict, directory: Path,
              max_prompt_bytes: int, timeout: int, *, codex_config: Path | None = None, stop_requested=None,
              recoverable=False, pause_before_route: str | None = None, fixed_follow_up: PinnedFixedReview | None = None) -> dict:
    """Run a bounded, dependency-ready read-only graph with no resubmission through this entry."""
    return _run_graph(state, project_id, manifest, manifest_digest, inputs, directory, max_prompt_bytes, timeout,
                      codex_config=codex_config, stop_requested=stop_requested, recoverable=recoverable,
                      pause_before_route=pause_before_route, fixed_follow_up=fixed_follow_up)


def _run_graph(state, project_id, manifest, manifest_digest, inputs, directory, max_prompt_bytes, timeout, *,
               codex_config=None, stop_requested=None, recoverable=False, pause_before_route=None,
               fixed_follow_up=None, follow_up_parent=None):
    graph_options(max_prompt_bytes, timeout, recoverable=recoverable, codex_config=codex_config)
    deadline = time.monotonic() + timeout
    recovery = None
    if recoverable:
        if follow_up_parent is None:
            deadline_ns = time.monotonic_ns() + timeout * 1_000_000_000
            recovery = {'schema_version': 2, 'clock': budget_clock.authorize(timeout), 'deadline_monotonic_ns': deadline_ns,
                        'result_limit': _RESULT_LIMIT}
        else:
            parent, _, child_limit = follow_up_parent
            parent.check_active()
            recovery = {'schema_version': 2, 'clock': parent.recovery['clock'],
                        'deadline_monotonic_ns': parent.recovery['deadline_monotonic_ns'], 'result_limit': child_limit}
            _check_recovery_result_limit(recovery)
            stop_requested = lambda: os.path.lexists(parent.directory / 'stop.json') or parent.stop_signalled()
        deadline = _graph_deadline(recovery, timeout)
    project = state.project(project_id)
    if follow_up_parent is not None and project['revision'] != parent.project['revision']:
        raise ValueError('Project changed before original follow-up admission')
    checked = workflows.inspect_manifest(manifest, material=True)
    if checked['digest'] != manifest_digest:
        raise ValueError('Workflow manifest differs from the explicitly selected digest')
    composition = checked['composition']
    encoded_inputs, fixed_review = preflight_graph(composition, inputs, max_prompt_bytes, manifest_digest=manifest_digest,
        recoverable=recoverable, pause_before_route=pause_before_route, codex_config=codex_config)
    if fixed_review is not None:
        inputs = json.loads(encoded_inputs)
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
    if pause_before_route is not None:
        receipt['pause_before_route'] = pause_before_route
    if fixed_follow_up is not None:
        if pause_before_route is None:
            raise ValueError('A fixed review follow-up requires its original supervisor checkpoint')
        receipt['fixed_follow_up'] = _fixed_follow_up_binding(
            composition, pause_before_route, fixed_follow_up, max_prompt_bytes, preflight=True)
    if follow_up_parent is not None:
        receipt['follow_up_parent'] = follow_up_parent[1]
    if recoverable:
        directory = directory.resolve()
        receipt['inputs'] = inputs = json.loads(encoded_inputs)
        recovery.update(directory=str(directory), state_home=str(state.root.resolve()),
                        authority_sha256=_graph_authority_sha(receipt))
    directory.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as owner:
        lock_fd = None
        with tempfile.TemporaryDirectory(prefix='.workflow-run-', dir=directory.parent) as temporary:
            staged = Path(temporary)/'run'
            staged.mkdir(mode=0o700)
            if recoverable:
                lock = _enter_owner(owner, staged / '.owner.lock')
                lock_fd = lock.fileno()
                recovery['owner_identity'] = _owner_identity(os.fstat(lock_fd))
                receipt['recovery_sha256'] = native_sources.sha(recovery)
                _write_recovery_record(staged, 'recovery.json', recovery)
            shutil.copytree(manifest, staged/'manifest', symlinks=True)
            if workflows.inspect_manifest(staged/'manifest')['digest'] != manifest_digest:
                raise ValueError('Workflow manifest changed while freezing the run')
            if fixed_follow_up is not None:
                target = staged / _FOLLOW_UP_MANIFEST
                shutil.copytree(fixed_follow_up.manifest, target, symlinks=True)
                if workflows.inspect_manifest(target)['digest'] != fixed_follow_up.manifest_digest:
                    raise ValueError('Fixed review follow-up manifest changed while freezing the run')
            run = _GraphRun(state, project, composition, staged, receipt, deadline, codex_config, stop_requested,
                            fixed_review, recovery=recovery, lock_fd=lock_fd)
            run.check_active()
            run.save()
            publish_directory(staged, directory)
        run.directory = directory
        if recoverable:
            native_sources.sync_directory_chain(directory)
        return _execute_graph(run, inputs, composition)


def resume_graph(home: Path | None, project_id: str, directory: Path, manifest_digest: str, *, stop_requested=None,
                 route_checkpoint: str | None = None, route_action: str | None = None) -> dict:
    """Continue only the original, unexpired graph after verifying all its saved attempts."""
    if route_checkpoint is not None or route_action is not None:
        contracts.validate(route_checkpoint, contracts.COMPOSITION_MANIFEST['$defs']['digest'], 'Route checkpoint SHA256')
        if route_action not in _ROUTE_ACTIONS:
            raise ValueError('Select follow-up or finish for the original route checkpoint')
    directory = directory.expanduser().resolve()
    state_home = resolve_home(home)
    lock = directory / '.owner.lock'
    if is_link(lock) or not lock.is_file():
        raise ValueError('Select an original recoverable graph directory')
    with ExitStack() as owner:
        original_lock = _enter_owner(owner, lock)
        _, receipt = _read_graph_receipt(project_id, directory, manifest_digest)
        if 'follow_up_parent' in receipt:
            raise ValueError('Resume a bound child through its original parent graph')
        if receipt.get('status') not in ('incomplete', _AWAITING_ROUTE) or os.path.lexists(directory / 'stop.json'):
            raise ValueError('A terminal or explicitly stopped graph cannot resume')
        if 'outputs' in receipt or 'error' in receipt:
            raise ValueError('Saved graph progress differs from the supported incomplete recovery state')
        if any(field not in receipt for field in _RECOVERY_FIELDS):
            raise ValueError('Saved recovery is missing original graph authority')
        recovery = native_sources.packet(directory, 'recovery.json')
        _check_recovery_authority(receipt, recovery, directory, state_home, _owner_identity(os.fstat(original_lock.fileno())))
        contracts.validate(receipt['timeout'], {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Receipt workflow timeout')
        contracts.validate(receipt['max_prompt_bytes'], contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'],
                           'Receipt input byte limit')
        _check_recovery_result_limit(recovery)
        deadline = _graph_deadline(recovery, receipt['timeout'])
        state = State(state_home, read_only=True)
        project = state.project(project_id)
        if type(receipt['project_revision']) is not int or receipt['project_revision'] != project['revision']:
            raise ValueError('Project revision differs from the original graph authorization')
        checked = workflows.inspect_manifest(directory / 'manifest', material=True)
        if checked['digest'] != manifest_digest or receipt['root'] != checked['manifest']['root']:
            raise ValueError('Saved graph manifest differs from the receipt or explicitly selected digest')
        composition, inputs = checked['composition'], receipt['inputs']
        if 'pause_before_route' in receipt:
            _check_route_pause(composition, receipt['pause_before_route'], True)
        _graph_inputs(composition, inputs, receipt['max_prompt_bytes'], recoverable=True)
        _verify_sources(composition, inputs)
        fixed_review = _fixed_review_context(composition, inputs, manifest_digest)
        run = _GraphRun(state, project, composition, directory, receipt, deadline, None, stop_requested, fixed_review,
                        recovery=recovery, lock_fd=original_lock.fileno())
        try:
            restored = run.restore_fixed_read(inputs)
            run.recover(inputs)
            run.recheck_fixed_read(restored)
            if state.project(project_id)['revision'] != project['revision']:
                raise ValueError('Project revision changed during graph recovery')
            run.check_active()
            if route_checkpoint is not None:
                run.accept_route_action(route_checkpoint, route_action)
        except KeyboardInterrupt:
            run.fence_stop()
            raise
        if receipt['status'] == _AWAITING_ROUTE and run.operator_decision is None:
            return receipt
        run.state = State(state_home)
        receipt['status'] = 'incomplete'
        run.save()
        return _execute_graph(run, inputs, composition)


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


def _observe_leaf_run(state, project, receipt, manifest, attempt, remaining_result_bytes, route_choices,
                      *, flow_evidence=None):
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
    source['process_start'] = observed['process_start']
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
    if (flow_evidence is not None and source['status'] == 'succeeded'
            and source['graph_outcome_agreement'] == 'matching'
            and all(observed[name]['available'] for name in ('input', 'prompt', 'result'))):
        flow_evidence[attempt['instance']] = (observed['input']['request']['task_sha256'],
                                               observed['result']['document'])
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


def _observe_route_recommendation(record, selector, attempts, choices):
    analyzer, = selector['depends_on']
    branches = selector['branches']
    observation = {'instance': selector['path'], 'eligible': branches, 'source_instance': analyzer}
    attempt = attempts.get(analyzer)
    if attempt is None:
        return {**observation, 'state': 'missing', 'proof': 'analyzer_attempt'}, None
    source = {key: attempt[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}
    if record.get('source') != source or source['result_sha256'] is None or attempt['status'] != 'succeeded':
        return {**observation, 'state': 'mismatch', 'proof': 'analyzer_attempt'}, None
    observation['source'] = source
    original = attempt['original_run']
    if original['state'] != 'available':
        return {**observation, 'state': original['state'], 'proof': 'original_run'}, None
    if original['graph_outcome_agreement'] != 'matching':
        return {**observation, 'state': 'mismatch', 'proof': 'original_run'}, None
    for field in ('input', 'prompt', 'result'):
        if original[field]['state'] != 'available':
            return {**observation, 'state': original[field]['state'], 'proof': field}, None
    choice = choices.get(analyzer)
    if choice is None:
        return {**observation, 'state': 'invalid', 'proof': 'result'}, None
    return observation, _route_record(selector, choice, source)


def _observe_route(sequence, record, selector, attempts, choices, graph_status, *, supervised=False,
                   operator_route=None, follow_up=None):
    observation, expected = _observe_route_recommendation(record, selector, attempts, choices)
    observation = {'sequence': sequence, **observation}
    if expected is None:
        return observation
    if supervised and expected['selected'] is not None:
        if operator_route is None:
            return {**observation, 'state': 'mismatch', 'proof': 'operator_decision'}
        expected = operator_route
        observation['operator_decision_sha256'] = expected['operator_decision_sha256']
    selected, skipped = expected['selected'], expected['skipped']
    if record != expected or any(branch in attempts for branch in skipped):
        return {**observation, 'state': 'mismatch', 'proof': 'route_decision'}
    if follow_up is not None:
        linked = {**observation, 'follow_up': follow_up}
        if selected in attempts:
            return {**linked, 'state': 'mismatch', 'proof': 'follow_up'}
        if follow_up['state'] != 'corroborated':
            return {**linked, 'state': follow_up['state'], 'proof': 'follow_up'}
        if graph_status == 'succeeded' and follow_up['terminal_status'] != 'succeeded':
            return {**linked, 'state': 'mismatch', 'proof': 'follow_up'}
        observation = linked
    elif graph_status == 'succeeded' and selected is not None and selected not in attempts:
        return {**observation, 'state': 'mismatch', 'proof': 'route_decision'}
    return {**observation, 'state': 'corroborated', 'choice': expected['choice'], 'selected': selected, 'skipped': skipped}


def _observe_route_checkpoint(directory, receipt, selectors, attempts, choices, recovery):
    target = receipt.get('pause_before_route')
    decision_exists = os.path.lexists(directory / _ROUTE_DECISION)
    checkpoint = receipt.get('route_checkpoint')
    if 'pause_before_route' not in receipt and not decision_exists and 'route_checkpoint' not in receipt:
        return None, None
    if not isinstance(target, str) or target not in selectors or recovery['authorization']['state'] != 'corroborated':
        return {'state': 'mismatch', 'proof': 'recovery_authority'}, None
    if checkpoint is None:
        if decision_exists or receipt['status'] == _AWAITING_ROUTE:
            return {'state': 'missing', 'proof': 'route_checkpoint'}, None
        return {'state': 'not_recorded', 'instance': target}, None
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get('recommendation'), dict):
        return {'state': 'invalid', 'proof': 'route_checkpoint'}, None
    selector = selectors[target]
    observation, recommendation = _observe_route_recommendation(checkpoint['recommendation'], selector, attempts, choices)
    if recommendation is None:
        return observation, None
    try:
        checkpoint_sha = _checked_checkpoint_sha(receipt, recommendation)
        observation = {**observation, 'sha256': checkpoint_sha, 'recommendation': recommendation}
        if decision_exists:
            clock = recovery['clock']
            deadline_ns = clock.get('deadline_monotonic_ns')
            if type(deadline_ns) is not int or clock['state'] == 'invalid':
                return {**observation, 'state': 'invalid', 'proof': 'clock'}, None
            decision = native_sources.packet(directory, _ROUTE_DECISION)
            now = time.monotonic_ns() if clock['state'] in ('within_deadline', 'expired') else None
            _check_operator_decision(decision, checkpoint_sha, deadline_ns, receipt['timeout'], now_ns=now)
            route = _decided_route(selector, recommendation, decision)
            return {**observation, 'state': 'decided', 'decision': decision,
                    'decision_sha256': route['operator_decision_sha256']}, route
    except (OSError, ValueError, RecursionError) as error:
        return {**observation, 'state': _local_evidence_state(error)}, None
    if receipt['status'] in ('incomplete', 'succeeded') or any(
            record['instance'] == target for record in receipt.get('route_decisions', ())):
        return {**observation, 'state': 'missing', 'proof': 'operator_decision'}, None
    available = (receipt['status'] == _AWAITING_ROUTE and recovery['clock']['state'] == 'within_deadline'
                 and recovery['stop']['state'] == 'not_recorded' and recovery['project_revision']['state'] == 'matching')
    return {**observation, 'state': 'awaiting' if available else 'closed'}, None


def _read_graph_receipt(project, directory, manifest_digest):
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
    return raw, receipt


def _local_evidence_state(error):
    state = native_sources.observation_failure(error)['state']
    return 'invalid' if state == 'over_capacity' else state


def _observe_recovery_clock(recovery, timeout):
    deadline_ns = recovery['deadline_monotonic_ns']
    clock = {'deadline_monotonic_ns': deadline_ns} if type(deadline_ns) is int else {}
    try:
        _saved_graph_deadline(recovery, timeout)
    except (ValueError, OverflowError, TypeError, RecursionError):
        return {**clock, 'state': 'invalid'}, None
    try:
        remaining = budget_clock.remaining(recovery['clock'], timeout)
        now = time.monotonic_ns()
        if now + timeout * 1_000_000_000 < deadline_ns:
            raise ValueError('Saved graph clock or deadline is invalid')
    except (OSError, ValueError, OverflowError, TypeError, RecursionError):
        return {**clock, 'state': 'unknown'}, None
    return {**clock, 'state': 'expired' if now >= deadline_ns or remaining <= 0 else 'within_deadline'}, now


def _observe_recovery_stop(directory):
    if not os.path.lexists(directory / 'stop.json'):
        return {'state': 'not_recorded'}
    try:
        marker = native_sources.packet(directory, 'stop.json')
    except (OSError, ValueError, RecursionError) as error:
        state = _local_evidence_state(error)
        return {'state': 'invalid' if state == 'missing' else state}
    return {'state': 'recorded' if marker == {'status': 'cancelled'} else 'invalid'}


def _observe_fixed_recovery(directory, receipt, recovery, review, gate, record, now):
    observation = {'original_receipt': {'state': 'not_queried'}}
    if record is None:
        present = any(os.path.lexists(directory / name) for name in (_FIXED_READ_ATTEMPT, _FIXED_READ_COMPLETE))
        return {**observation, 'state': 'missing' if present else 'not_recorded'}
    observation['progress_status'] = record['status']
    try:
        _saved_graph_deadline(recovery, receipt['timeout'])
        attempt = native_sources.packet(directory, _FIXED_READ_ATTEMPT)
        if now is not None:
            now = time.monotonic_ns()
        expected = _fixed_attempt_progress(receipt, recovery, review, gate, receipt['inputs']['check'], attempt, now_ns=now)
        started, deadline_ns = attempt['started_monotonic_ns'], attempt['deadline_monotonic_ns']
        cutoff = 'not_checked' if now is None else 'expired' if now >= deadline_ns else 'within_deadline'
        observation.update(mode=attempt['mode'], attempt_sha256=expected['attempt_sha256'], started_monotonic_ns=started,
                           read_cutoff={'state': cutoff, 'deadline_monotonic_ns': deadline_ns})
        pending = record['status'] == 'attempted'
        if pending:
            _check_attempted_progress(receipt, record, expected)
        if not os.path.lexists(directory / _FIXED_READ_COMPLETE):
            if record['status'] == 'validated':
                return {**observation, 'state': 'missing'}
            if native_sources.encode(record) != native_sources.encode({**expected, 'status': record['status']}):
                raise native_sources.ArtifactIdentityError('Saved verification progress differs from the original attempt')
            return {**observation, 'state': 'attempted'}
        completion = native_sources.packet(directory, _FIXED_READ_COMPLETE)
        validated = _fixed_completion_tick(attempt, completion)
        if now is not None and validated > time.monotonic_ns():
            raise ValueError('Saved fixed-check proof validation time is in the future')
        completed = _fixed_completed_progress(receipt, recovery, review, attempt, expected, completion, validated)
        if not pending and native_sources.encode(record) != native_sources.encode(completed):
            raise native_sources.ArtifactIdentityError('Saved verification progress differs from the original fixed-check witnesses')
        return {**observation, 'state': 'recorded_complete', 'completion_sha256': completed['completion_sha256'],
                'validated_monotonic_ns': validated}
    except (OSError, ValueError, OverflowError, TypeError, RecursionError) as error:
        return {**observation, 'state': _local_evidence_state(error)}


def _observe_graph_recovery(directory, state_home, receipt, selected_project, review, gate, reads):
    status = receipt['status']
    revision = selected_project.get('revision')
    revision_state = ('unknown' if type(revision) is not int else
                      'matching' if revision == receipt['project_revision'] else 'mismatch')
    observation = {'owner_activity': 'unknown', 'terminal_status': status if status in _TERMINAL_STATUSES else None,
                   'project_revision': {'state': revision_state, 'original': receipt['project_revision']},
                   'stop': _observe_recovery_stop(directory), 'clock': {'state': 'not_checked'},
                   'fixed_check': {'state': 'not_checked' if review is not None else 'not_applicable'}}
    if type(revision) is int:
        observation['project_revision']['current'] = revision
    if 'recovery_sha256' not in receipt and not any(os.path.lexists(directory / name) for name in
            ('recovery.json', '.owner.lock', 'stop.json', _FIXED_READ_ATTEMPT, _FIXED_READ_COMPLETE)):
        return {**observation, 'authorization': {'state': 'ordinary'}}
    try:
        recovery = native_sources.packet(directory, 'recovery.json')
        lock = directory / '.owner.lock'
        details = lock.stat(follow_symlinks=False)
        if is_link(lock) or not stat.S_ISREG(details.st_mode):
            raise ValueError('Original graph lock entry is invalid')
        identity = _owner_identity(details)
        _check_recovery_authority(receipt, recovery, directory.resolve(), state_home.resolve(), identity)
        _check_recovery_result_limit(recovery)
    except (OSError, ValueError, RecursionError, RuntimeError) as error:
        return {**observation, 'authorization': {'state': _local_evidence_state(error)}}
    observation['authorization'] = {'state': 'corroborated', 'sha256': receipt['recovery_sha256'], 'owner_identity': identity}
    observation['clock'], now = _observe_recovery_clock(recovery, receipt['timeout'])
    if review is not None:
        record = next((row for row in reads if row['instance'] == gate), None)
        observation['fixed_check'] = _observe_fixed_recovery(directory, receipt, recovery, review, gate, record, now)
    return observation


def _read_fixed_follow_up(state, project, parent_receipt, parent_recovery, child, child_id, invocation_record):
    binding = parent_receipt['fixed_follow_up']
    projection = invocation_record['output_projection']
    observation = {'id': child_id, 'directory': str(child), 'manifest_digest': binding['manifest_digest'],
                   'projection': projection, 'terminal_status': None, 'state': 'unknown'}
    if not os.path.lexists(child):
        return observation, None
    if is_link(child) or not child.is_dir():
        raise native_sources.ArtifactIdentityError('Original follow-up directory was replaced')
    raw, receipt = _read_graph_receipt(project, child, binding['manifest_digest'])
    recovery = native_sources.packet(child, 'recovery.json')
    checked = workflows.inspect_manifest(child / 'manifest', material=True)
    composition = checked['composition']
    if (checked['digest'] != binding['manifest_digest'] or receipt.get('root') != binding['root']
            or receipt.get('follow_up_parent') != child_id or 'fixed_follow_up' in receipt
            or receipt.get('project_revision') != parent_receipt['project_revision']
            or native_sources.encode(receipt.get('inputs')) != native_sources.encode(binding['inputs'])
            or receipt.get('timeout') != parent_receipt['timeout']
            or receipt.get('max_prompt_bytes') != parent_receipt['max_prompt_bytes']
            or recovery['clock'] != parent_recovery['clock']
            or recovery['deadline_monotonic_ns'] != parent_recovery['deadline_monotonic_ns']
            or recovery['result_limit'] != invocation_record['result_limit']):
        raise native_sources.ArtifactIdentityError('Saved child receipt differs from the original follow-up authority')
    gate, leaf = dags.fixed_check_review(composition)
    review = _fixed_review_context(composition, binding['inputs'], binding['manifest_digest'])
    reads = _observed_attempts(receipt, 'verification_reads', {gate['path']})
    authority = _observe_graph_recovery(child, state.root, receipt, {'revision': parent_receipt['project_revision']},
                                         review, gate['path'], reads)
    if authority['authorization']['state'] != 'corroborated':
        raise native_sources.ArtifactIdentityError('Original follow-up graph authority is not corroborated')
    status, outputs = receipt.get('status'), receipt.get('outputs')
    if (status not in ('incomplete', *_TERMINAL_STATUSES)
            or (status == 'succeeded' and (not isinstance(outputs, dict)
                or outputs.keys() != composition['instances'][0]['outputs'].keys()))
            or (status != 'succeeded' and 'outputs' in receipt)):
        raise native_sources.ArtifactIdentityError('Original follow-up status or output ports are inconsistent')
    terminal = status if status in _TERMINAL_STATUSES else None
    if (authority['stop']['state'] not in ('not_recorded', 'recorded')
            or (terminal is not None and (terminal == 'cancelled') != (authority['stop']['state'] == 'recorded'))):
        raise native_sources.ArtifactIdentityError('Original follow-up STOP contradicts its saved outcome')
    observation.update(terminal_status=terminal, receipt_sha256=hashlib.sha256(raw).hexdigest(),
                       stop=authority['stop'], state='corroborated' if terminal is not None else 'unknown')
    leaves = _observed_attempts(receipt, 'leaves', {projection['producer']}, required=True)
    if leaves:
        attempt, = leaves
        if attempt['run_id'] != native_sources.sha([receipt['recovery_sha256'], leaf['path']])[:32]:
            raise native_sources.ArtifactIdentityError('Original follow-up output producer differs from its reservation')
        _check_reservation(child, receipt, 1, attempt)
        prepared = _reconstruct_graph_input(composition, child / 'input-1', leaf['path'],
                                            binding['inputs']['task'], receipt['max_prompt_bytes'])
        if prepared['digest'] != attempt['input_digest']:
            raise native_sources.ArtifactIdentityError('Original follow-up input differs from its reservation')
        observation['source'] = {key: attempt.get(key)
                                 for key in ('instance', 'run_id', 'input_digest', 'result_sha256', 'status')}
    if status != 'succeeded':
        return observation, None
    if (not leaves or attempt['status'] != 'succeeded' or authority['fixed_check']['state'] != 'recorded_complete'
            or len(reads) != 1 or native_sources.encode(outputs['proof']) != native_sources.encode(reads[0].get('evidence'))):
        raise native_sources.ArtifactIdentityError('Original follow-up Agent and fixed-check receipts are not corroborated')
    result = _recover_agent_result(state, project, receipt['project_revision'], leaf, attempt, prepared,
                                  invocation_record['result_limit'])
    invocation.validate_result(result['document'], _leaf_result_schema(leaf))
    projected = {projection['producer']: {'result': result['document']}}
    if native_sources.encode(projected) != native_sources.encode(outputs[projection['port']]):
        raise native_sources.ArtifactIdentityError('Original follow-up output differs from its Agent result')
    return observation, result


def _observe_fixed_follow_up(state, project, directory, composition, receipt, recovery, checkpoint, route, attempts):
    binding = receipt.get('fixed_follow_up')
    if binding is None:
        return None
    if not isinstance(binding, dict):
        return {'state': 'invalid', 'proof': 'follow_up'}
    marker = directory / _FOLLOW_UP_INVOCATION
    if route is None or route['selected'] != binding.get('branch'):
        return {'state': 'mismatch', 'proof': 'operator_decision'} if os.path.lexists(marker) else None
    observation = {'branch': route['selected'], 'proof': 'follow_up'}
    try:
        selected = PinnedFixedReview(binding['branch'], directory / _FOLLOW_UP_MANIFEST,
                                     binding['manifest_digest'], binding['inputs'])
        original = _fixed_follow_up_binding(composition, route['instance'], selected, receipt['max_prompt_bytes'])
        if original != binding:
            raise native_sources.ArtifactIdentityError('Fixed review follow-up differs from the original binding')
        if not os.path.lexists(marker):
            return {**observation, 'state': 'missing'}
        parent = native_sources.packet(directory, 'recovery.json')
        if native_sources.sha(parent) != recovery['authorization'].get('sha256'):
            raise native_sources.ArtifactIdentityError('Original parent authority changed during follow-up readback')
        analyzer = attempts[route['source']['instance']]['original_run']['result']
        expected = _follow_up_invocation(receipt, checkpoint['sha256'], route['operator_decision_sha256'],
                                        parent['result_limit'] - analyzer['bytes'])
        if native_sources.packet(directory, _FOLLOW_UP_INVOCATION) != expected:
            raise native_sources.ArtifactIdentityError('Saved follow-up invocation differs from the original selected route')
        child_id = native_sources.sha(expected)
        child = directory / ('follow-up-' + child_id)
        observation.update(id=child_id, directory=str(child), projection=expected['output_projection'])
        readback, _ = _read_fixed_follow_up(state, project, receipt, parent, child, child_id, expected)
        return {**observation, **readback}
    except (OSError, ValueError, TypeError, KeyError, RecursionError, StateError) as error:
        return {**observation, 'state': _local_evidence_state(error), 'error': str(error)}


def inspect_graph(state: State, project: str, directory: Path, manifest_digest: str) -> dict:
    """Reconstruct graph receipt and Agent observations offline without acquiring execution authority."""
    directory = directory.expanduser().absolute()
    raw, receipt = _read_graph_receipt(project, directory, manifest_digest)
    checked = workflows.inspect_manifest(directory / 'manifest', material=True)
    manifest, composition = checked['manifest'], checked['composition']
    if checked['digest'] != manifest_digest or receipt.get('root') != manifest['root']:
        raise ValueError('Saved graph manifest differs from the receipt or explicitly selected digest')
    try:
        selected_project = state.project(project)
    except StateError as error:
        raise ValueError('Cannot read the selected project state: ' + str(error)) from error
    nodes = composition['instances']
    root = nodes[0]
    inputs, outputs, status = (receipt.get(name) for name in ('inputs', 'outputs', 'status'))
    if (not isinstance(inputs, dict) or inputs.keys() != root['inputs'].keys()
            or status not in ('incomplete', _AWAITING_ROUTE, *_TERMINAL_STATUSES)
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
    review = fixed_review = _fixed_review_context(composition, inputs, manifest_digest)
    if fixed_review is not None:
        revision = receipt['project_revision']
        if type(revision) is not int:
            raise ValueError('Fixed-check graph receipt requires an integer project revision')
        fixed_review = {**fixed_review, 'project_revision': revision}
    agent_nodes = {node['path']: node for node in nodes if node['kind'] == 'agent'}
    selectors = {node['path']: node for node in nodes if node['kind'] == 'choose-agent'}
    leaves = _observed_attempts(receipt, 'leaves', agent_nodes, required=True)
    verification_reads = _observed_attempts(receipt, 'verification_reads', sources)
    route_records = _observed_attempts(receipt, 'route_decisions', selectors)
    flow_blocks = _flow_map_blocks(receipt, agent_nodes)
    if status == 'succeeded' and flow_blocks:
        raise ValueError('Successful graph receipt contains a required FlowMap block')
    attempts, choices, run_ids, remaining = {}, {}, set(), _RESULT_LIMIT
    nodes_by_path = {node['path']: node for node in nodes}
    flow_producers = _flow_map_producers(nodes_by_path) if flow_blocks else {}
    flow_producer_paths = set(flow_producers.values())
    flow_evidence = {}
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
            state, project, receipt, manifest, attempt, remaining, route_choices,
            flow_evidence=flow_evidence if leaf['instance'] in flow_producer_paths else None)
        remaining -= result_bytes
        attempts[leaf['instance']] = attempt
        if choice is not None:
            choices[leaf['instance']] = choice
    reads = [_observe_verification(project, sequence, read, sources[read['instance']], fixed_review=fixed_review)
             for sequence, read in enumerate(verification_reads, 1)]
    gate = next((node['path'] for node in nodes if node['kind'] == 'verify-fixed-check'), None)
    recovery = _observe_graph_recovery(directory, state.root, receipt, selected_project, review, gate, verification_reads)
    checkpoint, operator_route = _observe_route_checkpoint(directory, receipt, selectors, attempts, choices, recovery)
    follow_up = _observe_fixed_follow_up(state, project, directory, composition, receipt, recovery,
                                        checkpoint, operator_route, attempts)
    decisions = []
    for sequence, record in enumerate(route_records, 1):
        supervised = record['instance'] == receipt.get('pause_before_route')
        decisions.append(_observe_route(sequence, record, selectors[record['instance']], attempts, choices, status,
                          supervised=supervised, operator_route=operator_route if supervised else None,
                          follow_up=follow_up if supervised else None))
    if checkpoint is not None:
        recovery['route_checkpoint'] = checkpoint
    observed_blocks = []
    for path, block in flow_blocks.items():
        if path in attempts:
            raise ValueError('Blocked FlowMap consumer has an original Agent attempt')
        producer = block['producer']
        reason_state = 'receipt-reported'
        if producer is not None:
            original_path = flow_producers.get(path)
            observed = attempts.get(original_path)
            if observed is None or producer != {name: observed[name]
                    for name in ('instance', 'run_id', 'input_digest', 'result_sha256')}:
                raise ValueError('Saved FlowMap block differs from the original producer attempt')
            port = _root_task_port(agent_nodes[path], nodes_by_path)
            if port is not None and original_path in flow_evidence:
                task_sha256, original_result = flow_evidence[original_path]
                original_task = _bounded_json(inputs[port], receipt['max_prompt_bytes'])
                if task_sha256 != hashlib.sha256(original_task).hexdigest():
                    observed_blocks.append({**block, 'reason_state': reason_state})
                    continue
                try:
                    _checked_flow_map_task(composition, path, inputs[port], original_result, task_sha256,
                                           producer, receipt['max_prompt_bytes'])
                except _FlowMapBlocked as error:
                    if str(error) != block['reason']:
                        raise ValueError('Saved FlowMap block differs from the original producer evidence') from error
                else:
                    raise ValueError('Original producer evidence does not establish the saved FlowMap block')
                reason_state = 'corroborated'
        observed_blocks.append({**block, 'reason_state': reason_state})
    recorded_paths = {'root', *attempts, *flow_blocks, *(item['instance'] for item in reads + decisions)}
    if follow_up is not None and follow_up.get('state') == 'corroborated':
        recorded_paths.add(follow_up['branch'])
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
            **({'follow_up': follow_up} if follow_up is not None else {}),
            **({'flow_map_blocks': observed_blocks} if observed_blocks else {}),
            'recovery': recovery,
            'process_start': 'unknown',
            'stop_and_cleanup': 'unknown', 'formal_execution_authorized': False}
