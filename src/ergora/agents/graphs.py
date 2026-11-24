"""Execute an explicitly selected standalone graph through original leaf runs."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import uuid

from ergora.agents import backends, runs
from ergora.configuration import validation as contracts
from ergora.definitions import agents, workflows
from ergora.storage.assets import publish_directory
from ergora.storage.state import State


_RESULT_LIMIT = 8_388_608


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
        self.result_bytes = 0

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

    def check_active(self):
        if self.stop_requested is not None and self.stop_requested():
            raise KeyboardInterrupt
        if time.monotonic() >= self.deadline:
            raise TimeoutError('The original workflow deadline expired')

    def leaf(self, path, task):
        remaining = _RESULT_LIMIT - self.result_bytes
        if remaining <= 0:
            raise ValueError('Workflow has no remaining result bytes')
        limit = self.receipt['max_prompt_bytes']
        source = self.directory / f"input-{len(self.receipt['leaves']) + 1}"
        prepared = workflows.prepare_input_from_manifest(self.directory/'manifest', path,
            _bounded_json(task, limit), source, limit, input_origin='workflow-port',
            manifest_digest=self.receipt['manifest_digest'])
        self.check_active()
        attempt = {'instance': path, 'run_id': uuid.uuid4().hex, 'input_digest': prepared['digest'], 'status': 'attempted'}
        self.receipt['leaves'].append(attempt)
        self.save()
        job = runs.run_input(self.state, self.project['id'], source, self.receipt['timeout'], mode='text-only',
            codex_config=self.codex_config, deadline=self.deadline, input_digest=prepared['digest'], run_id=attempt['run_id'],
            expected_revision=self.project['revision'], stop_requested=self.stop_requested)
        attempt.update(status=job['status'], result_sha256=job.get('result_sha256'))
        self.save()
        if job['status'] != 'succeeded':
            if job['status'] == 'timed_out':
                raise TimeoutError(f'Workflow leaf reached its deadline: {path}')
            if job['status'] == 'cancelled':
                raise KeyboardInterrupt
            raise ValueError(f'Workflow leaf {path} reported {job["status"]}')
        observed = runs.inspect_run(self.state, self.project['id'], attempt['run_id'], max_result_bytes=remaining)
        result = observed['result']
        if not result['available']:
            raise ValueError(f'Workflow leaf {path} cannot supply its original result within the remaining {remaining} bytes: '
                             + result['error'])
        if (not observed['input']['available'] or not observed['prompt']['available']
                or observed['input']['digest'] != prepared['digest'] or result['sha256'] != attempt['result_sha256']):
            raise ValueError(f'Original workflow leaf evidence is unavailable: {path}')
        self.result_bytes += result['bytes']
        return {'result': result['document']}

    def workflow(self, path, inputs):
        completed = {}

        def value(binding):
            if 'input' in binding:
                return inputs[binding['input']]
            return completed[path + '/' + binding['node']][binding['output']]

        node = self.nodes[path]
        for level in node['levels']:
            for child_path in level:
                self.check_active()
                child = self.nodes[child_path]
                if child['kind'] == 'join':
                    result = {'result': {dependency: completed[dependency] for dependency in child['depends_on']}}
                else:
                    ports = {name: value(binding) for name, binding in child['inputs'].items()}
                    result = (self.workflow(child_path, ports) if child['kind'] == 'workflow'
                              else self.leaf(child_path, ports['task']))
                completed[child_path] = result
        return {name: value(binding) for name, binding in node['outputs'].items()}


def run_graph(state: State, project_id: str, manifest: Path, manifest_digest: str, inputs: dict, directory: Path,
              max_prompt_bytes: int, timeout: int, *, codex_config: Path | None = None, stop_requested=None) -> dict:
    """Run a bounded read-only graph serially, with no resubmission through this entry."""
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
        outputs = run.workflow('root', inputs)
        _bounded_json(outputs, _RESULT_LIMIT)
        run.check_active()
        receipt.update(status='succeeded', outputs=outputs)
    except TimeoutError as error:
        receipt.update(status='timed_out', error=str(error))
    except KeyboardInterrupt:
        receipt.update(status='cancelled', error='Workflow interrupted')
    except (OSError, ValueError, RecursionError) as error:
        receipt.update(status='failed', error=str(error))
    run.save()
    return receipt
