"""Project-scoped formal task use cases; the native runtime remains authoritative."""

import base64
import hashlib
import json
from pathlib import Path
import re

from . import agent_backends, agents, bindings, contracts, issue_snapshots, issue_sources, projects, reference, workflow_definitions
from .asset_trees import inventory_tree
from .state import State
from .task_envelopes import identity


_DEFINITIONS = {version: json.loads((Path(__file__).parent / f'data/schemas/task-definition-v{version}.json').read_text(encoding='utf-8'))
                for version in (1, 2, 3, 4)}


def _project(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    registration = project.get('registration')
    if not registration or registration['status'] != 'published':
        raise ValueError('Formal tasks require a published unified project registration')
    reference.validate_installation(Path(registration['definition']['execution']['installation']))
    return project


def _revision(project: dict, expected_revision: int) -> None:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if project['revision'] != expected_revision:
        raise ValueError('Project revision changed; reload before the task operation')


def _definition(state: State, project: dict, definition: dict) -> dict:
    version = definition.get('schema_version') if isinstance(definition, dict) else None
    schema = _DEFINITIONS.get(version, _DEFINITIONS[1]) if type(version) is int else _DEFINITIONS[1]
    contracts.validate(definition, schema, 'Task definition')
    if definition['task_type'] not in project['registration']['definition']['templates']:
        raise ValueError('Task template is not registered for this project')
    if len(json.dumps(definition, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 1_048_576:
        raise ValueError('Task definition exceeds 1 MiB')
    selection = bindings.development_snapshot(project, projects.effective_configuration(project))
    result = {'definition': definition, 'selection': selection}
    if version in (2, 3, 4):
        result['composition'] = _composition(definition, selection)
    if 'source' in definition:
        from .task_envelopes import manifest_graph

        saved = issue_snapshots.snapshot(state, project['id'], definition['source']['snapshot_sha256'])
        tracker = {**project['registration']['definition']['tracker'], 'issue_id': definition['issue_id']}
        issue_sources.bind_snapshot(saved, project['id'], selection['configuration']['layers']['tracker']['binding'], tracker)
        # This lower bound is already needed by every selected work/review
        # prompt. Runtime producers and candidate files have their own later
        # complete-material check; they are not guessed during offline preview.
        minimum = json.dumps({'issue_source': saved, 'root_task': {'input': definition['input']}},
                             ensure_ascii=False, allow_nan=False).encode('utf-8')
        graph = manifest_graph(result['composition']['manifest'])
        composition = result['composition']
        paths = (composition['members'].keys() | composition['execution']['members'].keys()
                 | composition.get('preparation', {}).get('members', {}).keys())
        for path in paths:
            workflow_definitions.compile_input(graph, path, minimum, 1_000_000)
        result['issue_source'] = saved
    return result


def _member(leaf: dict, mode: str, override: dict | None) -> dict:
    """Freeze the actual backend and policy for one formally selected leaf."""
    binding = dict(override['binding'] if override else leaf['backend_request'])
    agents.validate_binding(leaf['role'], binding, formal=True)
    backend = agent_backends.for_binding(binding)
    backend.check_mode(mode)
    return {'role': leaf['role'], 'binding': binding, 'requested_binding': leaf['backend_request'],
            'backend_reason': override['reason'] if override else 'definition-selected backend',
            'mode': mode, 'policy': backend.composition_policy(mode)}


def _composition(definition: dict, selection: dict) -> dict:
    option = definition['composition']
    source = Path(option['manifest']).expanduser().absolute()
    checked = workflow_definitions.inspect_manifest(source, material=True)
    if checked['digest'] != option['manifest_digest']:
        raise ValueError('Selected composition manifest digest changed')
    reference = checked['manifest']['root']
    graph = workflow_definitions.preview(source / 'assets', reference['id'], reference['version'], checked['manifest']['grant'])
    if graph != checked['composition']:
        raise ValueError('Composition manifest changed during formal admission')
    instances = {item['path']: item for item in graph['instances']}
    position = option['review_instance']
    if (position not in instances or instances[position]['kind'] != 'workflow'
            or set(instances[position]['inputs']) != {'task'}):
        raise ValueError('Select a Workflow instance with a single task input for the review stage')
    # Expanded input names are relative to the immediate structural parent.
    # The formal review stage supplies only the root task, never sibling results.
    execution = option.get('execution')
    ancestor, port = instances[position], 'task'
    while execution is None:
        origin = ancestor['inputs'][port]
        if ancestor['depends_on'] or 'node' in origin:
            raise ValueError('Selected review subtree cannot depend on an unexecuted external node')
        port = origin['input']
        if ancestor['parent'] is None:
            if port != 'task':
                raise ValueError('Selected review subtree must resolve to the root task input')
            break
        ancestor = instances[ancestor['parent']]
    leaves = {path: item for path, item in instances.items() if item['kind'] == 'agent' and path.startswith(position + '/')}
    work = None
    if execution is not None:
        from .review_dags import WorkDelivery

        work = WorkDelivery(graph, execution, position, definition['input']['work_units'],
                            preparation=option.get('preparation'))
    overrides = option.get('backend_overrides', {})
    preparing = {leaf['path']: leaf for leaf in work.preparation.values()} if work else {}
    all_paths = leaves.keys() | (work.work.members.keys() if work else set()) | preparing.keys()
    if not leaves or set(overrides) - all_paths:
        raise ValueError('Composition backend overrides must select existing review members')
    members = {}
    implementer = selection['bindings']['implementer']['tool']
    work_members = {}
    preparation = {}
    for path, leaf in preparing.items():
        preparation[path] = _member(leaf, option['preparation']['mode'], overrides.get(path))
    if work is not None:
        for path, leaf in work.work.members.items():
            work_members[path] = _member(leaf, execution['mode'], overrides.get(path))
    implementers = {member['binding']['tool'] for member in work_members.values()} if work else {implementer}
    diversity = option.get('diversity', {'policy': 'prefer-distinct'})
    same = []
    for path, leaf in leaves.items():
        if leaf['role'] != 'reviewer':
            raise ValueError('Formal composition currently selects only reviewer leaves')
        if leaf['permissions']['write'] or leaf['permissions']['shell'] or leaf['permissions']['network']:
            raise ValueError('Formal review composition requires read-only leaves without shell or network tools')
        member = _member(leaf, option['mode'], overrides.get(path))
        if member['binding']['tool'] in implementers:
            same.append(path)
        members[path] = {**member,
            **({'review_requirement': leaf.get('review_requirement', 'required')}
               if graph['schema_version'] == 2 or 'review_protocol' in option else {})}
    if ((graph['schema_version'] == 2 or 'review_protocol' in option)
            and not any(member['review_requirement'] == 'required' for member in members.values())):
        raise ValueError('Formal review requires at least one required reviewer')
    if same and diversity['policy'] == 'require-distinct':
        raise ValueError('Review members require a backend different from the implementer: ' + ', '.join(same))
    if same and diversity['policy'] == 'prefer-distinct' and not diversity.get('reason', '').strip():
        raise ValueError('Same-backend review under prefer-distinct requires an explicit diversity reason')
    digest, files, _ = inventory_tree(source, label='Composition manifest', max_directories=1000, max_depth=48)
    snapshot = {'digest': digest, 'files': {}}
    for name, item in files.items():
        content = (source / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError('Composition manifest changed while freezing its bytes')
        snapshot['files'][name] = {'content_base64': base64.b64encode(content).decode('ascii'),
                                  'executable_bits': item['executable_bits']}
    if digest != checked['digest'] or inventory_tree(source, label='Composition manifest', max_directories=1000, max_depth=48)[0] != digest:
        raise ValueError('Composition manifest changed while freezing its complete tree')
    composition = {'manifest': snapshot, 'root': graph['root'], 'preview_sha256': graph['preview_sha256'],
            'review_instance': position, 'members': members,
            **({'review_protocol': option['review_protocol']} if 'review_protocol' in option else {}),
            **({'execution': {**execution, 'members': work_members}} if work else {}),
            **({'preparation': {**option['preparation'], 'members': preparation}} if preparing else {}),
            'diversity': {**diversity, **({'implementer_backends': sorted(implementers)} if work else
                                        {'implementer_backend': implementer}), 'same_backend_members': same}}
    if 'review_protocol' in option:
        from .task_envelopes import review_members

        review_members(composition)
    return composition


def _digest(value: str, name: str) -> None:
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError(name + ' must be a SHA256 digest')


def _run_id(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or value.strip() != value:
        raise ValueError('Run ID must be a nonempty opaque identifier of at most 128 characters')


def preview(state: State, project_id: str, definition: dict, expected_revision: int) -> dict:
    """Compile in temporary storage and return the exact proposed task and bindings."""
    project = _project(state, project_id)
    _revision(project, expected_revision)
    return reference.task_creation(project, state.root, 'preview', _definition(state, project, definition))


def create(state: State, project_id: str, definition: dict, expected_revision: int, preview_sha256: str) -> dict:
    """Publish only an explicitly previewed immutable task, after saving its intent."""
    _digest(preview_sha256, 'Preview')
    # Binding and registration writers use the same SQLite write reservation.
    # Hold it through publication so an approved revision cannot change halfway.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        return reference.task_creation(project, state.root, 'create',
                                       {**_definition(state, project, definition), 'preview_sha256': preview_sha256})


def creation(state: State, project_id: str, task_id: str) -> dict:
    """Inspect the saved creation intent and native files, without querying execution."""
    project = _project(state, project_id)
    return reference.task_creation(project, state.root, 'status', {'task_id': task_id})


def resume_create(state: State, project_id: str, task_id: str, expected_revision: int, intent_sha256: str) -> dict:
    """Finish the original saved publication without recompiling or changing its bindings."""
    _digest(intent_sha256, 'Intent')
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        return reference.task_creation(project, state.root, 'resume',
                                       {'task_id': task_id, 'intent_sha256': intent_sha256})


def status(state: State, project_id: str, task_id: str, *, run_id: str | None = None, timeout: int = 20) -> dict:
    """Read verified native execution facts; absence and transport errors stay distinct."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task runtime query timeout must be 1–60 seconds')
    if run_id is not None:
        _run_id(run_id)
    project = _project(state, project_id)
    task = reference.task_files(project, task_id=task_id)
    return {'project': project_id, 'project_revision': project['revision'], 'task_id': task_id,
            'request_sha256': task['spec']['request_sha256'], 'profile_sha256': task['spec']['profile_sha256'],
            **reference.task_runtime_status(project, task.get('admission_envelope', task['spec']), run_id=run_id, timeout=timeout)}


def external_status(state: State, project_id: str, task_id: str, *, run_id: str, timeout: int = 20) -> dict:
    """Read the closed original run's job/receipt/fence evidence without mutations."""
    _run_id(run_id)
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('External evidence query timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_external_status(project, state.root, {'task_id': task_id, 'run_id': run_id}, timeout=timeout)


def evidence(state: State, project_id: str, task_id: str, *, run_id: str, timeout: int = 20) -> dict:
    """Index a closed original run's contracts, published receipts and artifact references."""
    _run_id(run_id)
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task evidence index query timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_evidence(project, state.root, {'task_id': task_id, 'run_id': run_id}, timeout=timeout)


def handoff(state: State, project_id: str, task_id: str, *, run_id: str, output: Path, timeout: int = 20) -> dict:
    """Export verified original materials; leave task execution and ownership intact."""
    _run_id(run_id)
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task handoff timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_handoff(project, state.root,
                                  {'task_id': task_id, 'run_id': run_id, 'output': str(output.expanduser().absolute())},
                                  timeout=timeout)


def events(state: State, project_id: str, task_id: str, *, run_id: str,
           limit: int = 20, after: str | None = None, timeout: int = 20) -> dict:
    """Read one bounded page of original-run metadata without returning payloads."""
    _run_id(run_id)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Task event limit must be 1–100')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task event query timeout must be 1–60 seconds')
    if after is not None and (not isinstance(after, str) or not 1 <= len(after) <= 8192):
        raise ValueError('Invalid task event cursor')
    project = _project(state, project_id)
    return reference.task_events(project, state.root, {'task_id': task_id, 'run_id': run_id,
                                 'limit': limit, 'after': after}, timeout=timeout)


def job(state: State, project_id: str, task_id: str, *, run_id: str, event_id: int,
        artifact: str | None = None, receipt_sha256: str | None = None,
        offset: int = 0, limit: int = 8192, timeout: int = 20) -> dict:
    """Read an original scheduled job, selecting text only by its pinned receipt."""
    _run_id(run_id)
    if type(event_id) is not int or not 1 <= event_id <= 10_000:
        raise ValueError('Job scheduling event ID must be 1–10000')
    if type(offset) is not int or not 0 <= offset <= 16_777_216:
        raise ValueError('Job artifact character offset must be 0–16777216')
    if type(limit) is not int or not 1 <= limit <= 16_384:
        raise ValueError('Job artifact window limit must be 1–16384 characters')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Job evidence query timeout must be 1–60 seconds')
    if artifact is None:
        if receipt_sha256 is not None or offset:
            raise ValueError('Select an artifact before pinning a receipt or character offset')
    else:
        if not isinstance(artifact, str) or not artifact or len(artifact) > 1024:
            raise ValueError('Job artifact name must be 1–1024 characters')
        _digest(receipt_sha256, 'Job receipt')
    project = _project(state, project_id)
    return reference.task_job(project, state.root, {'task_id': task_id, 'run_id': run_id,
                              'event_id': event_id, 'artifact': artifact, 'receipt_sha256': receipt_sha256,
                              'offset': offset, 'limit': limit}, timeout=timeout)


def submission(state: State, project_id: str, task_id: str) -> dict:
    """Inspect local submission facts without connecting to Temporal or reissuing work."""
    project = _project(state, project_id)
    return reference.task_submission(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def reconciliation(state: State, project_id: str, task_id: str) -> dict:
    """Read saved cleanup evidence without querying the run, fencing or releasing."""
    project = _project(state, project_id)
    return reference.task_reconciliation(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def reconcile(state: State, project_id: str, task_id: str, expected_revision: int,
              *, run_id: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Fence a closed original run and release only its confirmed external cleanup."""
    _run_id(run_id)
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_reconciliation, 'prepare',
                                         {'task_id': task_id, 'run_id': run_id}, confirm, timeout)
    if not prepared['created']:
        return prepared['reconciliation']
    return reference.task_reconciliation(project, state.root, 'dispatch',
                                         {'task_id': task_id, 'intent_sha256': prepared['reconciliation']['intent_sha256']},
                                         timeout=timeout)


def resume_reconcile(state: State, project_id: str, task_id: str, expected_revision: int,
                     intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Resume the original immutable fence and cleanup release after interruption."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_reconciliation, 'prepare-resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'reconciled':
        return prepared
    return reference.task_reconciliation(project, state.root, 'resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, timeout=timeout)


def start(state: State, project_id: str, task_id: str, expected_revision: int,
          creation_sha256: str, *, timeout: int = 20) -> dict:
    """Submit an explicitly identified creation once through the original admission."""
    _digest(creation_sha256, 'Creation')
    return _submission(state, project_id, task_id, expected_revision, 'start',
                       {'creation_sha256': creation_sha256}, timeout)


def resume_start(state: State, project_id: str, task_id: str, expected_revision: int,
                 intent_sha256: str, *, timeout: int = 20) -> dict:
    """Resume a pre-dispatch intent or reconcile uncertain dispatch by its original ID."""
    _digest(intent_sha256, 'Intent')
    return _submission(state, project_id, task_id, expected_revision, 'resume',
                       {'intent_sha256': intent_sha256}, timeout)


def _submission(state: State, project_id: str, task_id: str, expected_revision: int,
                operation: str, payload: dict, timeout: int) -> dict:
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task submission timeout must be 1–60 seconds')
    project, prepared = _native_prepare(state, project_id, expected_revision, reference.task_submission,
                                        'prepare' if operation == 'start' else 'prepare-resume',
                                        {'task_id': task_id, **payload}, timeout)
    if operation == 'start':
        status = prepared['submission']
        if not prepared['created']:
            return status
    else:
        status = prepared
        if status['status'] in ('submitted', 'rejected'):
            return status
    return reference.task_submission(project, state.root, 'dispatch' if operation == 'start' else 'resume',
                                     {'task_id': task_id, 'intent_sha256': status['intent_sha256']}, timeout=timeout)


def approval(state: State, project_id: str, task_id: str, decision_id: str) -> dict:
    """Read one durable owner decision without querying or signaling the workflow."""
    project = _project(state, project_id)
    return reference.task_approval(project, state.root, 'status',
                                   {'task_id': task_id, 'decision_id': decision_id}, timeout=20)


def plan(state: State, project_id: str, task_id: str, *, run_id: str, plan_sha256: str, timeout: int = 20) -> dict:
    """Read bounded review materials for the original run's exact pending plan."""
    _run_id(run_id)
    _digest(plan_sha256, 'Plan')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Plan inspection timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_plan(project, state.root, {'task_id': task_id, 'run_id': run_id,
                                                    'plan_sha256': plan_sha256}, timeout=timeout)


def approve(state: State, project_id: str, task_id: str, decision_id: str, expected_revision: int,
            *, run_id: str, plan_sha256: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Freeze an explicit owner decision, then signal its exact run and plan once."""
    _run_id(run_id)
    _digest(plan_sha256, 'Plan')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_approval, 'prepare',
                                         {'task_id': task_id, 'decision_id': decision_id,
                                          'run_id': run_id, 'plan_sha256': plan_sha256}, confirm, timeout)
    if not prepared['created']:
        return prepared['approval']
    return reference.task_approval(project, state.root, 'dispatch',
                                   {'task_id': task_id, 'decision_id': decision_id,
                                    'intent_sha256': prepared['approval']['intent_sha256']}, timeout=timeout)


def resume_approve(state: State, project_id: str, task_id: str, decision_id: str, expected_revision: int,
                   intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue an undispatched decision or find its signal in the original run's history."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_approval, 'prepare-resume',
                                         {'task_id': task_id, 'decision_id': decision_id,
                                          'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'requested':
        return prepared
    return reference.task_approval(project, state.root, 'resume',
                                   {'task_id': task_id, 'decision_id': decision_id,
                                    'intent_sha256': intent_sha256}, timeout=timeout)


def cancellation(state: State, project_id: str, task_id: str, request_id: str) -> dict:
    """Read a durable cancellation request without querying or signaling its run."""
    project = _project(state, project_id)
    return reference.task_cancellation(project, state.root, 'status',
                                       {'task_id': task_id, 'request_id': request_id}, timeout=20)


def cancel(state: State, project_id: str, task_id: str, request_id: str, expected_revision: int,
           *, run_id: str, reason: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Request cooperative cancellation once, or record an already-closed run."""
    _run_id(run_id)
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
        raise ValueError('Cancellation requires a nonempty reason of at most 1000 characters')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_cancellation, 'prepare',
                                         {'task_id': task_id, 'request_id': request_id,
                                          'run_id': run_id, 'reason': reason}, confirm, timeout)
    if not prepared['created']:
        return prepared['cancellation']
    return reference.task_cancellation(project, state.root, 'dispatch',
                                       {'task_id': task_id, 'request_id': request_id,
                                        'intent_sha256': prepared['cancellation']['intent_sha256']}, timeout=timeout)


def resume_cancel(state: State, project_id: str, task_id: str, request_id: str, expected_revision: int,
                   intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue only an undispatched request; unknown delivery needs original history."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_cancellation, 'prepare-resume',
                                         {'task_id': task_id, 'request_id': request_id,
                                          'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] in ('requested', 'already_closed'):
        return prepared
    return reference.task_cancellation(project, state.root, 'resume',
                                       {'task_id': task_id, 'request_id': request_id,
                                        'intent_sha256': intent_sha256}, timeout=timeout)


def export_status(state: State, project_id: str, task_id: str) -> dict:
    """Read the saved local export, without querying the run or changing Git refs."""
    project = _project(state, project_id)
    return reference.task_export(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def exported_source_candidate(state: State, project: dict, binding: dict, task_id: str,
                              run_id: str, candidate_sha: str) -> tuple[dict, dict]:
    """Bind an original v7 source creation and exported candidate for both observations and writebacks."""
    created = creation(state, project['id'], task_id)
    original = show(state, project['id'], task_id)
    envelope = original.get('admission_envelope', {})
    if created['status'] != 'published' or 'issue_source' not in envelope:
        raise ValueError('Candidate association requires a published original v7 source task')
    saved = envelope['issue_source']
    if saved != issue_snapshots.snapshot(state, project['id'], saved['sha256']):
        raise ValueError('Task source differs from its saved original snapshot')
    issue_sources.bind_snapshot(saved, project['id'], binding, original['spec']['request']['tracker'])
    exported = export_status(state, project['id'], task_id)
    if exported['status'] != 'exported' or exported['run_id'] != run_id or exported['candidate_sha'] != candidate_sha:
        raise ValueError('Candidate association requires the exact original exported run and candidate')
    facts = {key: exported[key] for key in ('intent_sha256', 'workflow_id', 'run_id', 'candidate_sha', 'repo', 'branch', 'lease_released')}
    task = {'id': task_id, 'creation_sha256': created['intent_sha256'], 'compiled_sha256': created['compiled_sha256'],
            'request_sha256': original['request_sha256'], 'profile_sha256': original['profile_sha256'],
            'run_id': run_id, 'candidate_sha': candidate_sha, 'export_intent_sha256': exported['intent_sha256'],
            'export_facts_sha256': identity(facts), 'branch': exported['branch']}
    return saved, task


def inspect_export(state: State, project_id: str, task_id: str, *, run_id: str, candidate_sha: str,
                   base_branch: str) -> dict:
    """Read current local Git facts through the original export owner; never fetch or update refs."""
    project = _project(state, project_id)
    return reference.task_export(project, state.root, 'inspect',
        {'task_id': task_id, 'run_id': run_id, 'candidate_sha': candidate_sha, 'base_branch': base_branch}, timeout=20)


def export(state: State, project_id: str, task_id: str, expected_revision: int,
           *, run_id: str, candidate_sha: str, branch: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Confirm one original run, candidate and target branch before local export."""
    _run_id(run_id)
    if not isinstance(candidate_sha, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', candidate_sha):
        raise ValueError('Export requires the exact full candidate commit SHA')
    if not isinstance(branch, str) or not 1 <= len(branch) <= 1024:
        raise ValueError('Export requires a nonempty branch of at most 1024 characters')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_export, 'prepare',
                                         {'task_id': task_id, 'run_id': run_id,
                                          'candidate_sha': candidate_sha, 'branch': branch}, confirm, timeout)
    if not prepared['created']:
        return prepared['export']
    return reference.task_export(project, state.root, 'dispatch',
                                 {'task_id': task_id, 'intent_sha256': prepared['export']['intent_sha256']}, timeout=timeout)


def resume_export(state: State, project_id: str, task_id: str, expected_revision: int,
                  intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue only a prepared export; uncertain changes require its existing ref."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_export, 'prepare-resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'exported':
        return prepared
    return reference.task_export(project, state.root, 'resume',
                                 {'task_id': task_id, 'intent_sha256': intent_sha256}, timeout=timeout)


def _decision_prepare(state: State, project_id: str, expected_revision: int, native_operation,
                       operation: str, payload: dict, confirm: bool, timeout: int) -> tuple[dict, dict]:
    if confirm is not True:
        raise ValueError('Task decision requires explicit confirmation of the original run and operation')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task decision timeout must be 1–60 seconds')
    return _native_prepare(state, project_id, expected_revision, native_operation, operation, payload, timeout)


def _native_prepare(state: State, project_id: str, expected_revision: int, native_operation,
                     operation: str, payload: dict, timeout: int) -> tuple[dict, dict]:
    # Only local intent preparation retains the project revision. The long
    # native phase is authorized by that frozen intent, under its task lock.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        prepared = native_operation(project, state.root, operation, payload, timeout=timeout)
    return project, prepared


def listing(state: State, project_id: str, *, limit: int = 50, after: str | None = None) -> dict:
    """Read a bounded window of native task contracts, without querying execution."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Task page limit must be 1–100 inspected entries')
    project = _project(state, project_id)
    return {'project': project_id, 'project_revision': project['revision'],
            **reference.task_files(project, limit=limit, after=after)}


def show(state: State, project_id: str, task_id: str) -> dict:
    """Read frozen task inputs and optional bindings; no runtime status is inferred."""
    project = _project(state, project_id)
    return {'project': project_id, 'project_revision': project['revision'],
            **reference.task_files(project, task_id=task_id)}
