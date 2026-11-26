"""Read one selected execution path alongside the immutable definition preview."""

import hashlib
from pathlib import Path

from ergora.definitions import workflows
from ergora.development.route_errors import RouteBlocked
from ergora.storage.state import State


def _path(value, name):
    if not isinstance(value, str) or not value.strip() or '\0' in value:
        raise ValueError(f'{name} requires an explicit path')
    return Path(value)


def _standalone(composition, selection, result):
    from ergora.agents import graphs

    recoverable = selection.get('recoverable', False)
    if type(recoverable) is not bool:
        raise ValueError('recoverable must be a boolean')
    override = selection.get('codex_config')
    config = _path(override, 'codex_config') if override is not None else None
    capacity = selection['max_prompt_bytes']
    graphs.graph_options(capacity, selection.get('timeout', 300), recoverable=recoverable, codex_config=config)
    manifest_digest = selection.get('manifest_digest')
    manifest = selection.get('manifest')
    if manifest is not None or manifest_digest is not None:
        if manifest is None or manifest_digest is None:
            raise ValueError('Select both the standalone manifest and its original digest')
        frozen = workflows.inspect_manifest(_path(manifest, 'manifest'), material=True)
        if frozen['digest'] != manifest_digest or frozen['composition'] != composition:
            raise ValueError('Selected standalone manifest differs from the definition preview or its original digest')
    encoded, _ = graphs.preflight_graph(composition, selection['inputs'], capacity, manifest_digest=manifest_digest,
        recoverable=recoverable, pause_before_route=selection.get('pause_before_route'), codex_config=config,
        packaging_consultation=selection.get('packaging_consultation', False))
    result.update(capability={'route': 'standalone-graph', 'status': 'admitted'}, manifest_digest=manifest_digest,
        inputs_sha256=hashlib.sha256(encoded).hexdigest(),
        bindings=[{'instance': node['path'], 'role': node['role'], 'mode': 'text-only',
                   **{key: node['backend_request'][key] for key in ('tool', 'model') if key in node['backend_request']}}
                  for node in composition['instances'] if node['kind'] == 'agent'])


def _formal(state, composition, selection, result):
    from ergora.development import application as tasks

    observed = tasks.preview_selected_route(state, selection['project'], selection['definition'], selection['revision'],
                                            composition['preview_sha256'])
    result.update(capability=observed['route_admission'], manifest_digest=observed['manifest_digest'],
                  definition_sha256=observed['definition_sha256'], bindings=observed.get('bindings', []),
                  executor_owned_steps=['inventory', 'plan', 'approval_before_work', 'work', 'integrate', 'verify', 'review'])


def _leaf(state, composition, selection, result):
    from ergora.agents import runs

    directory = _path(selection['directory'], 'directory')
    prepared = workflows.inspect_input(directory)
    request = prepared['request']
    instance = request['instance']
    if request['preview_sha256'] != composition['preview_sha256'] or prepared['digest'] != selection['input_digest']:
        raise RouteBlocked(instance, 'Selected leaf input differs from the definition preview or its original digest')
    config = selection.get('codex_config')
    try:
        admitted = runs.check_input(state, selection['project'], directory, input_digest=selection['input_digest'],
            mode=selection.get('mode', 'text-only'), backend=selection.get('backend'), model=selection.get('model'),
            reason=selection.get('backend_reason'), codex_config=_path(config, 'codex_config') if config is not None else None)
    except (OSError, ValueError) as error:
        raise RouteBlocked(instance, str(error)) from error
    if admitted['project_revision'] != result['project_revision']:
        raise RouteBlocked(instance, 'Project revision changed during the selected leaf admission')
    result.update(capability={'route': 'single-leaf', 'status': 'admitted', 'instance': instance},
                  input_digest=admitted['input_digest'], policy=admitted['policy'],
                  bindings=[{'instance': instance, 'role': admitted['role'], 'mode': admitted['policy']['mode'],
                             **{key: admitted['binding'][key] for key in ('tool', 'model') if key in admitted['binding']}}])


def preview(home: Path, identity: str, version: str, grant: dict, admission: dict | None = None) -> dict:
    composition = workflows.preview(home, identity, version, grant)
    if admission is None:
        return composition
    if not isinstance(admission, dict):
        raise ValueError('Select a structured execution route for the definition preview')
    route = admission.get('route')
    if route == 'standalone-graph':
        required = ['project', 'inputs', 'max_prompt_bytes']
        optional = {'revision', 'manifest', 'manifest_digest', 'timeout', 'recoverable', 'pause_before_route',
                    'codex_config', 'packaging_consultation'}
    elif route == 'formal-task':
        required = ['project', 'revision', 'definition']
        optional = set()
    elif route == 'single-leaf':
        required = ['project', 'directory', 'input_digest']
        optional = {'revision', 'mode', 'backend', 'model', 'backend_reason', 'codex_config'}
    else:
        raise ValueError('Select standalone-graph, formal-task or single-leaf for execution preview')
    extra = admission.keys() - {'route', *required} - optional
    if extra:
        raise ValueError('Unexpected execution preview fields: ' + ', '.join(sorted(extra)))
    missing = [key for key in required if admission.get(key) is None]
    result = {'preview_sha256': composition['preview_sha256'], 'project': admission.get('project'),
              'selection': route, 'capability': {'route': route, 'status': 'not_checked'},
              'required_bindings': {'status': 'required' if missing else 'supplied', 'fields': required, 'missing_fields': missing},
              'bindings': [], 'runtime_status': 'not_queried', 'execution_started_by_operation': False}
    if not missing:
        try:
            project_id = admission['project']
            if not isinstance(project_id, str) or not project_id.strip():
                raise ValueError('Select an existing project for execution preview')
            state = State(home, read_only=True)
            project = state.project(project_id)
            result['project_revision'] = project['revision']
            expected = admission.get('revision')
            if expected is not None and (type(expected) is not int or expected != project['revision']):
                raise ValueError('Project revision differs from the selected execution preview')
            if route == 'standalone-graph':
                _standalone(composition, admission, result)
            elif route == 'formal-task':
                _formal(state, composition, admission, result)
            else:
                _leaf(state, composition, admission, result)
        except (OSError, ValueError) as error:
            result['capability'] = {'route': route, 'status': 'blocked',
                'reason': error.reason if isinstance(error, RouteBlocked) else str(error),
                **({'instance': error.instance} if isinstance(error, RouteBlocked) else {})}
    return {'composition': composition, 'route_admission': result}
