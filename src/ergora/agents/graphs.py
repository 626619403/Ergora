"""Execute and observe explicitly selected standalone graphs through original leaf runs."""

from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import ExitStack
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
from ergora.development import dags, native as development_native
from ergora.runtime import budget_clock
from ergora.storage.assets import is_link, publish_directory
from ergora.storage.state import State, file_lock, resolve_home


_RESULT_LIMIT = 8_388_608
_RECEIPT_LIMIT = 10_000_000
_TERMINAL_STATUSES = ('succeeded', 'failed', 'cancelled', 'timed_out')
_VERIFICATION_NODES = ('verify-evidence', 'verify-fixed-check')
_RECOVERY_FIELDS = ('project', 'project_revision', 'root', 'manifest_digest', 'inputs', 'timeout', 'max_prompt_bytes')
_FIXED_READ_ATTEMPT = 'verification-attempt.json'
_FIXED_READ_COMPLETE = 'verification-complete.json'


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


def _graph_authority_sha(receipt):
    return hashlib.sha256(_bounded_json([receipt[name] for name in _RECOVERY_FIELDS], _RECEIPT_LIMIT)).hexdigest()


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


def _leaf_result_schema(node):
    routed = 'route_choices' in node
    schema = invocation.result_schema(['response', 'route'] if routed else ['response'], review=node['role'] == 'reviewer')
    if routed:
        schema['properties']['artifacts']['properties']['route'] = {'type': 'string', 'enum': node['route_choices']}
    return schema


def _route_record(node, choice, source):
    selected = None if choice == 'none' else f"{node['parent']}/{choice}"
    return {'instance': node['path'], 'choice': choice, 'eligible': node['branches'], 'selected': selected,
            'skipped': [path for path in node['branches'] if path != selected],
            'source': {key: source[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}}


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
        self.active_slots = Counter()
        self.completed = {}
        self.fixed_review = fixed_review
        self.recovery = recovery
        self.lock_fd = lock_fd
        self.result_limit = recovery['result_limit'] if recovery is not None else _RESULT_LIMIT
        self.unreserved = None

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
        return {'schema_version': 1, 'sequence': sequence, 'recovery_sha256': self.receipt['recovery_sha256'],
                **{key: attempt.get(key) for key in ('instance', 'run_id', 'input_digest')}}

    def check_reservations(self, names, leaves):
        witnesses = {name for name in names if name.startswith('reservation-')}
        expected = {f'reservation-{index}.json' for index in range(1, len(leaves) + 1)}
        if witnesses != expected:
            raise ValueError('Saved graph reservation witnesses differ from graph progress')
        for sequence, attempt in enumerate(leaves, 1):
            self.check_active()
            raw = native_sources.encode(self.reservation_witness(sequence, attempt)) + b'\n'
            detail = f'Saved graph reservation witness differs from its original attempt: {attempt["instance"]}'
            try:
                observed = native_sources.artifact(self.directory, f'reservation-{sequence}.json', len(raw))
            except (OSError, ValueError) as error:
                raise ValueError(detail) from error
            if observed != raw:
                raise ValueError(detail)

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
        if 'route_choices' in node:
            options['result_schema'] = _leaf_result_schema(node)
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
        return {'result': result['document']}

    def fixed_read_attempt(self, path, source, started):
        cutoff = min(self.recovery['deadline_monotonic_ns'],
                     started + development_native.FIXED_CHECK_PROOF_TIMEOUT * 1_000_000_000)
        return {'schema_version': 1, 'instance': path, 'recovery_sha256': self.receipt['recovery_sha256'],
                'mode': 'completed', 'source': source, 'source_sha256': native_sources.sha(source),
                'review': self.fixed_review, 'boot_id': self.recovery['clock']['boot_id'],
                'started_monotonic_ns': started, 'deadline_monotonic_ns': cutoff}

    def check_fixed_read_cutoff(self, attempt):
        self.check_active()
        now = time.monotonic_ns()
        if now >= attempt['deadline_monotonic_ns']:
            raise TimeoutError('The original fixed-check read deadline expired')
        return now

    def check_fixed_proof(self, source, evidence):
        expected = {**source, **self.fixed_review, 'status': 'validated', 'project': self.project['id'],
                    'project_revision': self.project['revision']}
        if (not isinstance(evidence, dict) or evidence.keys() != expected.keys() | {
                'job_id', 'authorization_sha256', 'verification_sha256', 'fixed_check_ids'}
                or any(type(evidence[key]) is not type(value) or evidence[key] != value for key, value in expected.items())
                or not isinstance(evidence['job_id'], str) or not evidence['job_id']
                or any(not isinstance(evidence[key], str) or re.fullmatch('[a-f0-9]{64}', evidence[key]) is None
                       for key in ('authorization_sha256', 'verification_sha256'))
                or not isinstance(evidence['fixed_check_ids'], list)
                or not all(isinstance(key, str) for key in evidence['fixed_check_ids'])):
            raise ValueError('Saved fixed-check proof differs from its original locator or review binding')

    def fixed_read_completion(self, attempt, evidence, validated):
        return {'schema_version': 1, 'attempt_sha256': native_sources.sha(attempt), 'evidence': evidence,
                'evidence_sha256': hashlib.sha256(_bounded_json(evidence, self.result_limit)).hexdigest(),
                'validated_monotonic_ns': validated}

    def verify_evidence(self, path, source):
        from ergora.development.application import read_candidate_verification, read_fixed_check_proof

        self.check_active()
        reads = self.receipt.setdefault('verification_reads', [])
        record = {'instance': path, 'source': source, 'status': 'attempted'}
        attempt = None
        if self.recovery is not None:
            attempt = self.fixed_read_attempt(path, source, time.monotonic_ns())
            _write_recovery_record(self.directory, _FIXED_READ_ATTEMPT, attempt)
            record['attempt_sha256'] = native_sources.sha(attempt)
        reads.append(record)
        self.save()
        try:
            options = {'expected_revision': self.project['revision'], 'deadline': self.deadline,
                       'stop_requested': self.should_stop}
            if attempt is not None:
                self.check_fixed_read_cutoff(attempt)
                options.update(deadline=attempt['deadline_monotonic_ns'] / 1_000_000_000, lock_fd=self.lock_fd)
            if self.nodes[path]['kind'] == 'verify-fixed-check':
                evidence = read_fixed_check_proof(self.state, self.project['id'], source, self.fixed_review, **options)
            else:
                evidence = read_candidate_verification(self.state, self.project['id'], source, **options)
            self.result_bytes += len(_bounded_json(evidence, self.result_limit - self.result_bytes))
            self.check_active()
            if attempt is not None:
                self.check_fixed_proof(source, evidence)
                completion = self.fixed_read_completion(attempt, evidence, self.check_fixed_read_cutoff(attempt))
                _write_recovery_record(self.directory, _FIXED_READ_COMPLETE, completion, preserve_order=True)
                record['completion_sha256'] = native_sources.sha(completion)
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
            completion = native_sources.packet(self.directory, _FIXED_READ_COMPLETE, confirm_durable=True)
        except FileNotFoundError as error:
            raise ValueError('Recovery requires the original completed fixed-check proof') from error
        source = inputs['check']
        started = attempt.get('started_monotonic_ns') if isinstance(attempt, dict) else None
        validated = completion.get('validated_monotonic_ns') if isinstance(completion, dict) else None
        graph_start = self.recovery['deadline_monotonic_ns'] - self.receipt['timeout'] * 1_000_000_000
        if (type(started) is not int or not graph_start <= started <= time.monotonic_ns()
                or native_sources.encode(attempt) != native_sources.encode(self.fixed_read_attempt(gate, source, started))):
            raise ValueError('Saved fixed-check read attempt differs from its original cutoff or authorization')
        if type(validated) is not int or not started <= validated < attempt['deadline_monotonic_ns']:
            raise ValueError('Saved fixed-check proof was not validated within its original read deadline')
        if validated > self.check_fixed_read_cutoff(attempt):
            raise ValueError('Saved fixed-check proof validation time is in the future')
        evidence = completion.get('evidence')
        self.check_fixed_proof(source, evidence)
        if native_sources.encode(completion) != native_sources.encode(self.fixed_read_completion(attempt, evidence, validated)):
            raise ValueError('Saved fixed-check completion differs from its original proof')
        record, = reads
        expected = {'instance': gate, 'source': source, 'status': 'attempted',
                    'attempt_sha256': native_sources.sha(attempt)}
        validated_record = {**expected, 'status': 'validated', 'evidence': evidence,
                            'completion_sha256': native_sources.sha(completion)}
        if record.get('status') == 'attempted':
            if self.receipt.get('leaves') or any(path.name.startswith(('input-', 'reservation-')) for path in self.directory.iterdir()):
                raise ValueError('Saved fixed-check read is still attempted with dependent work already recorded')
        else:
            expected = validated_record
        if native_sources.encode(record) != native_sources.encode(expected):
            raise ValueError('Saved verification progress differs from the original fixed-check witnesses')
        self.result_bytes += len(_bounded_json(evidence, self.result_limit - self.result_bytes))
        self.completed[gate] = {'result': evidence}
        return attempt, record, validated_record

    def recheck_fixed_read(self, restored):
        if restored is None:
            return
        from ergora.development.application import read_fixed_check_proof

        attempt, record, validated_record = restored
        self.check_fixed_read_cutoff(attempt)
        proof = read_fixed_check_proof(self.state, self.project['id'], attempt['source'], self.fixed_review,
            expected_revision=self.project['revision'], deadline=attempt['deadline_monotonic_ns'] / 1_000_000_000,
            stop_requested=self.should_stop, lock_fd=self.lock_fd)
        self.check_fixed_read_cutoff(attempt)
        if native_sources.encode(proof) != native_sources.encode(validated_record['evidence']):
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
        self.receipt.setdefault('route_decisions', []).append(record)
        self.save()
        self.check_active()
        return record

    def complete_route(self, record, pending):
        self.completed[record['instance']] = {'result': {'choice': record['choice']}}
        for branch in record['skipped']:
            del pending[branch]
            self.completed[branch] = {'status': 'skipped'}

    def ports(self, path, inputs, bindings):
        return {name: inputs[binding['input']] if 'input' in binding else
                self.completed[path + '/' + binding['node']][binding['output']] for name, binding in bindings.items()}

    def ready(self, node, opened):
        return (node['parent'] in opened and all(path in self.completed for path in node['depends_on'])
                and all(self.active_slots[scope['path']] < scope['limit'] for scope in node.get('concurrency_scopes', ())))

    def workflow_state(self, inputs):
        pending = {path: node for path, node in self.nodes.items() if path != 'root' and path not in self.completed}
        opened = {'root': inputs}
        children = {path: [child for level in node['levels'] for child in level]
                    for path, node in self.nodes.items() if node['kind'] == 'workflow'}
        return pending, opened, children

    def finalize_workflows(self, opened, children):
        for path in reversed(tuple(opened)):
            if all(child in self.completed for child in children[path]):
                self.completed[path] = self.ports(path, opened.pop(path), self.nodes[path]['outputs'])

    def open_structure(self, node, opened):
        path, parent = node['path'], node['parent']
        if node['kind'] == 'join':
            self.completed[path] = {'result': {dep: self.completed[dep] for dep in node['depends_on']}}
        else:
            opened[path] = self.ports(parent, opened[parent], node['inputs'])

    def recovery_input(self, source, path, task):
        prepared = workflows.inspect_input(source)
        limit = self.receipt['max_prompt_bytes']
        expected, _ = workflows.compile_input(self.composition, path, _bounded_json(task, limit), limit,
                                              input_origin='workflow-port')
        if native_sources.encode(prepared['request']) != native_sources.encode(expected):
            raise ValueError(f'Saved graph input differs from its reconstructed task or manifest: {path}')
        return prepared

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
        observed = runs.inspect_run(self.state, self.project['id'], run_id, max_result_bytes=remaining)
        original, result = observed['run'], observed['result']
        if original['status'] != 'succeeded':
            raise ValueError(f'Graph recovery requires a proven successful original Agent outcome: {path}')
        if (type(original.get('project_revision')) is not int
                or original['project_revision'] != self.project['revision']
                or original.get('formal_execution_authorized') is not False
                or original.get('role') != node['role'] or original.get('binding') != node['backend_request']
                or original.get('policy', {}).get('mode') != 'text-only'
                or not observed['input']['available'] or observed['input']['digest'] != prepared['digest']
                or not observed['prompt']['available'] or not result['available']
                or (('result_sha256' in attempt or status == 'succeeded') and attempt.get('result_sha256') != result['sha256'])):
            raise ValueError(f'Graph recovery requires matching original Agent input, prompt and result evidence: {path}')
        invocation.validate_result(result['document'], _leaf_result_schema(node))
        self.result_bytes += result['bytes']
        attempt.update(status='succeeded', result_sha256=result['sha256'])
        self.completed[path] = {'result': result['document']}

    def recover(self, inputs):
        agent_nodes = {path: node for path, node in self.nodes.items() if node['kind'] == 'agent'}
        selectors = {path: node for path, node in self.nodes.items() if node['kind'] == 'choose-agent'}
        decisions = deque(_observed_attempts(self.receipt, 'route_decisions', selectors))
        leaves = _observed_attempts(self.receipt, 'leaves', agent_nodes, required=True)
        reserved = {item['instance'] for item in leaves}
        names = {entry.name for entry in self.directory.iterdir()}
        self.check_reservations(names, leaves)
        expected_slots = {f'input-{index}' for index in range(1, len(leaves) + 1)}
        next_slot = f'input-{len(leaves) + 1}'
        slots = {name for name in names if name.startswith('input-')}
        if slots not in (expected_slots, expected_slots | {next_slot}):
            raise ValueError('Saved graph input slots differ from the original reservations')
        pending, opened, children = self.workflow_state(inputs)

        def advance_progress():
            while True:
                self.check_active()
                self.finalize_workflows(opened, children)
                if decisions:
                    record = decisions[0]
                    selector = selectors[record['instance']]
                    if self.ready(selector, opened):
                        parent = selector['parent']
                        source = self.ports(parent, opened[parent], selector['inputs'])['source']
                        expected = self.route_decision(selector, source)
                        if native_sources.encode(record) != native_sources.encode(expected):
                            raise ValueError(f'Saved route decision differs from its original analyzer result: {selector["path"]}')
                        decisions.popleft()
                        del pending[selector['path']]
                        self.complete_route(expected, pending)
                        continue
                structural = next((node for node in pending.values()
                                   if node['kind'] in ('workflow', 'join') and self.ready(node, opened)), None)
                if structural is None:
                    return
                del pending[structural['path']]
                self.open_structure(structural, opened)

        def task_at(path):
            advance_progress()
            node = pending.get(path)
            if node is None or node['kind'] != 'agent' or not self.ready(node, opened):
                raise ValueError(f'Saved graph input is unreachable through its original dependencies: {path}')
            parent = node['parent']
            return self.ports(parent, opened[parent], node['inputs'])['task']

        for sequence, attempt in enumerate(leaves, 1):
            path = attempt['instance']
            prepared = self.recovery_input(self.directory / f'input-{sequence}', path, task_at(path))
            self.recover_leaf(agent_nodes[path], attempt, prepared)
            del pending[path]
        advance_progress()
        if decisions:
            raise ValueError(f'Saved route decision is unreachable through its original dependencies: {decisions[0]["instance"]}')
        for path in agent_nodes.keys() - reserved:
            self.check_active()
            if native_sources.find_run(self.state, self.project['id'], self.recovery_run_id(path)) is not None:
                raise ValueError(f'An original Agent run is missing from the graph reservations: {path}')
        if next_slot in slots:
            source = self.directory / next_slot
            path = workflows.inspect_input(source)['request']['instance']
            prepared = self.recovery_input(source, path, task_at(path))
            self.unreserved = (path, prepared['digest'])

    def workflow(self, inputs, project_limit):
        pending, opened, children = self.workflow_state(inputs)
        root_limit = self.nodes['root']['limits']['concurrency']
        executor = ThreadPoolExecutor(max_workers=min(project_limit, root_limit))
        try:
            while 'root' not in self.completed:
                self.check_active()
                if self.collect_finished():
                    self.save()
                # Finalize children before their parents using frozen workflow membership.
                self.finalize_workflows(opened, children)
                if 'root' in self.completed:
                    break
                node = next((node for node in pending.values() if self.ready(node, opened)
                             and (self.unreserved is None or node['kind'] != 'agent'
                                  or node['path'] == self.unreserved[0])), None)
                if node is None:
                    if not self.running:
                        raise ValueError('No runnable workflow node remains')
                    wait(self.running, timeout=min(.05, max(0, self.deadline - time.monotonic())),
                         return_when=FIRST_COMPLETED)
                    continue
                path = node['path']
                del pending[path]
                if node['kind'] in ('workflow', 'join'):
                    self.open_structure(node, opened)
                    continue
                parent = node['parent']
                ports = self.ports(parent, opened[parent], node['inputs'])
                if node['kind'] in _VERIFICATION_NODES:
                    self.completed[path] = self.verify_evidence(path, ports['source'])
                elif node['kind'] == 'choose-agent':
                    self.complete_route(self.choose_agent(node, ports['source']), pending)
                elif node['kind'] == 'agent':
                    self.dispatch_leaf(executor, node, ports['task'])
                else:
                    raise ValueError(f'Unsupported standalone workflow node: {path}')
        except BaseException as error:
            self.stop.set()
            if isinstance(error, KeyboardInterrupt):
                self.fence_stop()
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


def _graph_inputs(composition, inputs, max_prompt_bytes, *, recoverable=False):
    if not isinstance(inputs, dict) or inputs.keys() != composition['instances'][0]['inputs'].keys():
        raise ValueError('Workflow inputs must supply exactly the declared root ports')
    encoded_inputs = _bounded_json(inputs, max_prompt_bytes)
    if recoverable:
        kinds = {node['kind'] for node in composition['instances']}
        if kinds - {'agent', 'workflow', 'join', 'choose-agent', 'verify-fixed-check'}:
            raise ValueError('Recoverable graphs support only Agent, Workflow, all-join, choose-agent and the fixed-check review gate')
        if 'verify-fixed-check' in kinds:
            from ergora.development.verification import validate_fixed_check_source

            dags.fixed_check_review(composition)
            if 'wait_seconds' in validate_fixed_check_source(inputs['check']):
                raise ValueError('Recoverable fixed-check review requires a completed locator with both original output digests')
    for leaf in (item for item in composition['instances'] if item['kind'] == 'agent'):
        if any(leaf['permissions'][name] for name in ('write', 'shell', 'network')):
            raise ValueError(f'Standalone workflow requires a read-only leaf: {leaf["path"]}')
        tool = leaf['backend_request']['tool']
        if not backends.supports_mode(tool, 'text-only'):
            raise ValueError(f'Standalone workflow requires text-only support at {leaf["path"]}: {tool}')
    return encoded_inputs


def _execute_graph(run, inputs, composition):
    receipt = run.receipt
    try:
        outputs = run.workflow(inputs, composition['grant']['limits']['concurrency'])
        _bounded_json(outputs, run.result_limit)
        run.check_active()
        receipt.update(status='succeeded', outputs=outputs)
    except TimeoutError as error:
        receipt.update(status='timed_out', error=str(error))
    except KeyboardInterrupt:
        run.fence_stop()
        receipt.update(status='cancelled', error='Workflow interrupted')
    except (OSError, ValueError, RecursionError, StateError) as error:
        receipt.update(status='failed', error=str(error))
    run.save()
    return receipt


def _graph_deadline(recovery, timeout):
    clock, deadline_ns = recovery['clock'], recovery['deadline_monotonic_ns']
    if (not isinstance(clock, dict) or clock.keys() != set(budget_clock.FIELDS)
            or type(deadline_ns) is not int or deadline_ns < timeout * 1_000_000_000
            or time.monotonic_ns() + timeout * 1_000_000_000 < deadline_ns):
        raise ValueError('Saved graph clock or deadline is invalid')
    budget_clock.validate(clock, timeout)
    deadline = deadline_ns / 1_000_000_000
    if time.monotonic() >= deadline or budget_clock.remaining(clock, timeout) <= 0:
        raise TimeoutError('The original workflow deadline expired')
    return deadline


def run_graph(state: State, project_id: str, manifest: Path, manifest_digest: str, inputs: dict, directory: Path,
              max_prompt_bytes: int, timeout: int, *, codex_config: Path | None = None, stop_requested=None,
              recoverable=False) -> dict:
    """Run a bounded, dependency-ready read-only graph with no resubmission through this entry."""
    contracts.validate(timeout, {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Workflow timeout')
    contracts.validate(max_prompt_bytes, contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'], 'Input byte limit')
    deadline = time.monotonic() + timeout
    recovery = None
    if recoverable:
        if codex_config is not None:
            raise ValueError('Recoverable graphs do not support an explicit Codex configuration')
        deadline_ns = time.monotonic_ns() + timeout * 1_000_000_000
        recovery = {'schema_version': 2, 'clock': budget_clock.authorize(timeout), 'deadline_monotonic_ns': deadline_ns,
                    'result_limit': _RESULT_LIMIT}
        deadline = _graph_deadline(recovery, timeout)
    project = state.project(project_id)
    checked = workflows.inspect_manifest(manifest, material=True)
    if checked['digest'] != manifest_digest:
        raise ValueError('Workflow manifest differs from the explicitly selected digest')
    composition = checked['composition']
    encoded_inputs = _graph_inputs(composition, inputs, max_prompt_bytes, recoverable=recoverable)
    fixed_review = None
    if any(item['kind'] in _VERIFICATION_NODES for item in composition['instances']):
        _verify_sources(composition, inputs)
        if any(item['kind'] == 'verify-fixed-check' for item in composition['instances']):
            inputs = json.loads(encoded_inputs)
            fixed_review = _fixed_review_context(composition, inputs, manifest_digest)
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
            run = _GraphRun(state, project, composition, staged, receipt, deadline, codex_config, stop_requested,
                            fixed_review, recovery=recovery, lock_fd=lock_fd)
            run.check_active()
            run.save()
            publish_directory(staged, directory)
        run.directory = directory
        if recoverable:
            native_sources.sync_directory_chain(directory)
        return _execute_graph(run, inputs, composition)


def resume_graph(home: Path | None, project_id: str, directory: Path, manifest_digest: str, *, stop_requested=None) -> dict:
    """Continue only the original, unexpired graph after verifying all its saved attempts."""
    directory = directory.expanduser().resolve()
    state_home = resolve_home(home)
    lock = directory / '.owner.lock'
    if is_link(lock) or not lock.is_file():
        raise ValueError('Select an original recoverable graph directory')
    with ExitStack() as owner:
        original_lock = _enter_owner(owner, lock)
        _, receipt = _read_graph_receipt(project_id, directory, manifest_digest)
        if receipt.get('status') != 'incomplete' or os.path.lexists(directory / 'stop.json'):
            raise ValueError('A terminal or explicitly stopped graph cannot resume')
        if 'outputs' in receipt or 'error' in receipt:
            raise ValueError('Saved graph progress differs from the supported incomplete recovery state')
        if any(field not in receipt for field in _RECOVERY_FIELDS):
            raise ValueError('Saved recovery is missing original graph authority')
        recovery = native_sources.packet(directory, 'recovery.json')
        if (not isinstance(recovery, dict) or recovery.keys() != {
                'schema_version', 'clock', 'deadline_monotonic_ns', 'result_limit', 'directory', 'state_home',
                'authority_sha256', 'owner_identity'}
                or type(recovery['schema_version']) is not int or recovery['schema_version'] != 2
                or recovery['directory'] != str(directory) or recovery['state_home'] != str(state_home)
                or native_sources.encode(recovery['owner_identity']) != native_sources.encode(
                    _owner_identity(os.fstat(original_lock.fileno())))
                or recovery['authority_sha256'] != _graph_authority_sha(receipt)
                or receipt.get('recovery_sha256') != native_sources.sha(recovery)):
            raise ValueError('Recovery authorization differs from the original graph, directory or State home')
        contracts.validate(receipt['timeout'], {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Receipt workflow timeout')
        contracts.validate(receipt['max_prompt_bytes'], contracts.COMPOSITION_INPUT['properties']['max_prompt_bytes'],
                           'Receipt input byte limit')
        limit = recovery['result_limit']
        if type(limit) is not int or not 1 <= limit <= _RESULT_LIMIT:
            raise ValueError('Saved graph result capacity is unsupported')
        deadline = _graph_deadline(recovery, receipt['timeout'])
        state = State(state_home, read_only=True)
        project = state.project(project_id)
        if type(receipt['project_revision']) is not int or receipt['project_revision'] != project['revision']:
            raise ValueError('Project revision differs from the original graph authorization')
        checked = workflows.inspect_manifest(directory / 'manifest', material=True)
        if checked['digest'] != manifest_digest or receipt['root'] != checked['manifest']['root']:
            raise ValueError('Saved graph manifest differs from the receipt or explicitly selected digest')
        composition, inputs = checked['composition'], receipt['inputs']
        _graph_inputs(composition, inputs, receipt['max_prompt_bytes'], recoverable=True)
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
        except KeyboardInterrupt:
            run.fence_stop()
            raise
        run.state = State(state_home)
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
    expected = _route_record(selector, choice, source)
    selected, skipped = expected['selected'], expected['skipped']
    if (record != expected or any(branch in attempts for branch in skipped)
            or (graph_status == 'succeeded' and selected is not None and selected not in attempts)):
        return {**observation, 'state': 'mismatch', 'proof': 'route_decision'}
    return {**observation, 'state': 'corroborated', 'choice': choice, 'selected': selected, 'skipped': skipped}


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


def inspect_graph(state: State, project: str, directory: Path, manifest_digest: str) -> dict:
    """Reconstruct graph receipt and Agent observations offline without acquiring execution authority."""
    directory = directory.expanduser().absolute()
    raw, receipt = _read_graph_receipt(project, directory, manifest_digest)
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
