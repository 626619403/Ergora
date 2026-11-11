"""Project-scoped observations; reading issue text grants no execution authority."""

import base64
import hashlib
import json

from . import contracts, issue_backends, projects
from .issue_snapshots import snapshot, snapshot_from_row, validate_digest
from .state import State, now


_SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$', 'not': {'pattern': '\\s'}}
_TEXT = {'type': 'string', 'minLength': 1}
_LINK = {
    'type': 'object', 'additionalProperties': False,
    'required': ['schema_version', 'project', 'snapshot_sha256', 'task', 'reason', 'linked_at',
                 'context_only', 'relationship', 'execution_authorized'],
    'properties': {
        'schema_version': {'type': 'integer', 'const': 1}, 'project': _TEXT,
        'snapshot_sha256': _SHA, 'linked_at': _TEXT,
        'reason': {'type': 'string', 'minLength': 1, 'maxLength': 2000, 'pattern': '\\S'},
        'context_only': {'const': True}, 'execution_authorized': {'const': False},
        'relationship': {'const': 'operator_asserted_context'},
        'task': {'type': 'object', 'additionalProperties': False,
            'required': ['id', 'creation_sha256', 'compiled_sha256', 'created_revision'],
            'properties': {'id': _TEXT, 'creation_sha256': _SHA, 'compiled_sha256': _SHA,
                           'created_revision': {'type': 'integer', 'minimum': 1}}},
    },
}


def _identity(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _revision(project: dict, expected: int) -> None:
    if type(expected) is not int or project['revision'] != expected:
        raise ValueError('Project revision changed; reload before the issue operation')


def _observe(project: dict, issue_id: str) -> tuple[dict, dict]:
    configuration = projects.effective_configuration(project)
    binding = configuration['layers']['tracker']['binding']
    backend = issue_backends.for_binding(binding)
    registration = project.get('registration')
    if registration and registration['definition']['tracker'] != {'kind': binding['tool'], 'project': binding['project']}:
        raise ValueError('Tracker source differs from the registered project namespace; use its registered source')
    observation = backend.read(issue_id)
    return ({**observation, 'project': {'id': project['id'], 'revision': project['revision']},
             'configuration_sha256': configuration['sha256'], 'observed_at': now()}, binding)


def show(state: State, project_id: str, issue_id: str) -> dict:
    return _observe(state.project(project_id), issue_id)[0]


def remote_candidate(state: State, project_id: str, task_id: str, expected_revision: int, *,
                     run_id: str, candidate_sha: str, base_branch: str) -> dict:
    """Compare original exported content with current local and remote refs; persist nothing."""
    from . import tasks

    project = state.project(project_id)
    _revision(project, expected_revision)
    configuration = projects.effective_configuration(project)
    binding = configuration['layers']['tracker']['binding']
    saved, task = tasks.exported_source_candidate(state, project, binding, task_id, run_id, candidate_sha)
    local = tasks.inspect_export(state, project_id, task_id, run_id=run_id,
                                candidate_sha=candidate_sha, base_branch=base_branch)
    if local['export']['intent_sha256'] != task['export_intent_sha256']:
        raise ValueError('Local candidate inspection differs from the original export intent')
    remote = issue_backends.for_binding(binding).repository_refs(task['branch'], base_branch)
    _revision(state.project(project_id), expected_revision)
    return {'schema_version': 1, 'kind': 'remote-candidate-observation',
        'project': {'id': project_id, 'revision': expected_revision}, 'configuration_sha256': configuration['sha256'],
        'source': saved['payload']['observation']['source'], 'snapshot_sha256': saved['sha256'], 'task': task,
        'local': local, 'remote': remote, 'observed_at': now(),
        'comparisons': {
            'local_export_ref_matches_candidate': local['branch_matches_candidate'],
            'head_matches_candidate': None if remote['head']['sha'] is None else remote['head']['sha'] == candidate_sha,
            'base_matches_task_base': None if remote['base']['sha'] is None else remote['base']['sha'] == local['base_sha']},
        'context_only': True, 'execution_authorized': False, 'proves_original_attempt': False,
        'coverage': 'Separate current reads, not a shared snapshot or CAS; cannot detect ABA or prove who published. '
                    'Repository identity is observed now at the frozen source namespace, not frozen at task creation. '
                    '404 means not found or not visible. No fetch, push, tracker mutation or persisted receipt.'}


def _link(row) -> dict:
    payload = json.loads(row['document'])
    contracts.validate(payload, _LINK, 'Saved issue task link')
    task = payload['task']
    if (_identity(payload) != row['sha'] or payload['project'] != row['project']
            or payload['snapshot_sha256'] != row['snapshot'] or task['id'] != row['task_id']
            or task['creation_sha256'] != row['creation_sha']):
        raise ValueError('Saved issue task link differs from its content identity or target')
    return {'schema_version': 1, 'sha256': row['sha'], 'payload': payload}


def _review_scope(project_id: str, task: dict) -> str:
    return _identity({'schema_version': 1, 'kind': 'candidate-review-context', 'project': project_id, 'task': task})


def _review_link(row, db) -> dict:
    payload = json.loads(row['document'])
    if len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) > 1_048_576:
        raise ValueError('Complete saved review context exceeds 1 MiB')
    contracts.validate(payload, contracts.CANDIDATE_REVIEW_CONTEXT, 'Saved review context')
    task, local, request = payload['task'], payload['local'], payload['review_request']
    review, repository = request['review'], payload['repository']
    diff = review['diff_refs']
    comparisons = {'local_export_ref_matches_candidate': local['current_branch_sha'] == task['candidate_sha'],
        'head_matches_candidate': payload['head']['sha'] == task['candidate_sha'],
        'base_matches_task_base': payload['base']['sha'] == local['base_sha'],
        'diff_version_head_matches_candidate': None if not diff else diff['head_sha'] == task['candidate_sha']}
    source_row = db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha=?',
                            (row['project'], payload['snapshot_sha256'])).fetchone()
    if source_row is None:
        raise ValueError('Saved review context has a missing source snapshot')
    snapshot_payload = snapshot_from_row(source_row)['payload']
    saved = snapshot_payload['observation']
    backend = issue_backends.for_binding(snapshot_payload['tracker_binding'])
    if (_identity(payload) != row['sha'] or _review_scope(row['project'], task) != row['scope']
            or payload['project']['id'] != row['project'] or payload['source'] != saved['source']
            or payload['source_check']['native_id'] != saved['issue']['native_id']
            or request['source'] != {key: payload['source'][key] for key in ('provider', 'api_url', 'project')}
            or request['repository'] != {key: repository[key] for key in ('native_id', 'node_id', 'project')}
            or request['response']['request_url'] != backend.api_url + backend.review_path(repository, review['number'])
            or repository['project'] != payload['source']['project']
            or local['candidate_sha'] != task['candidate_sha'] or local['branch'] != task['branch']
            or payload['head']['ref'] != 'refs/heads/' + task['branch']
            or review['head'] != {'branch': task['branch'], 'sha': task['candidate_sha']}
            or payload['base']['ref'] != 'refs/heads/' + review['base']['branch']
            or payload['comparisons'] != comparisons
            or db.execute('SELECT 1 FROM projects WHERE id=?', (row['project'],)).fetchone() is None):
        raise ValueError('Saved review context differs from its original identity, source or candidate')
    return {'schema_version': 1, 'sha256': row['sha'], 'scope_sha256': row['scope'], 'payload': payload}


def review_link(state: State, project_id: str, digest: str) -> dict:
    """Read the immutable saved association without Git, credentials or network."""
    state.project(project_id)
    validate_digest(digest)
    with state.connect() as db:
        row = db.execute('SELECT * FROM candidate_review_links WHERE project=? AND sha=?', (project_id, digest)).fetchone()
        if row is None:
            raise ValueError('Unknown saved review context in this project')
        return _review_link(row, db)


def link_review(state: State, project_id: str, task_id: str, expected_revision: int, *,
                run_id: str, candidate_sha: str, base_branch: str, review_number: str, reason: str) -> dict:
    """Associate one existing native review with the original candidate; never mutate the provider."""
    from . import tasks

    project = state.project(project_id)
    _revision(project, expected_revision)
    contracts.validate(reason, contracts.CANDIDATE_REVIEW_CONTEXT['properties']['reason'], 'Review context reason')
    binding = projects.effective_configuration(project)['layers']['tracker']['binding']
    saved, task = tasks.exported_source_candidate(state, project, binding, task_id, run_id, candidate_sha)
    scope = _review_scope(project_id, task)
    query = 'SELECT * FROM candidate_review_links WHERE project=? AND scope=?'

    def existing(row, db) -> dict:
        result = _review_link(row, db)
        review = result['payload']['review_request']['review']
        if review['number'] != review_number or review['base']['branch'] != base_branch:
            raise ValueError('Original candidate already has a different saved review context; inspect its original record')
        return {'record': result, 'already_saved': True, 'fresh_observations': False}

    with state.connect() as db:
        row = db.execute(query, (project_id, scope)).fetchone()
        if row is not None:
            return existing(row, db)
    observed = remote_candidate(state, project_id, task_id, expected_revision,
                               run_id=run_id, candidate_sha=candidate_sha, base_branch=base_branch)
    if (observed['task'] != task or observed['snapshot_sha256'] != saved['sha256']
            or observed['comparisons']['local_export_ref_matches_candidate'] is not True
            or observed['comparisons']['head_matches_candidate'] is not True or observed['remote']['base']['sha'] is None):
        raise ValueError('Review context requires the original current local and remote candidate heads and a visible base ref')
    backend = issue_backends.for_binding(binding)
    request = backend.read_review_request(observed['remote']['repository'], review_number)
    review = request['review']
    if review['head'] != {'branch': task['branch'], 'sha': candidate_sha} or review['base']['branch'] != base_branch:
        raise ValueError('Review request head or base differs from the selected candidate and branches')
    source_now = backend.read(observed['source']['issue_id'])
    if source_now['source'] != observed['source'] or source_now['issue']['native_id'] != saved['payload']['observation']['issue']['native_id']:
        raise ValueError('Source issue native identity changed; original snapshot was not replaced')
    diff = review['diff_refs']
    payload = {'schema_version': 1, 'kind': 'candidate-review-context',
        'project': {'id': project_id, 'revision': expected_revision},
        'configuration_sha256': observed['configuration_sha256'], 'snapshot_sha256': saved['sha256'],
        'source': observed['source'], 'source_check': {'native_id': source_now['issue']['native_id'],
            'response_sha256': source_now['response']['sha256'], 'observed_at': now()}, 'task': task,
        'repository': {**observed['remote']['repository'], 'node_id': observed['remote']['repository'].get('node_id')},
        'local': {key: observed['local'][key] for key in
                  ('base_sha', 'candidate_sha', 'branch', 'current_branch_sha', 'objects_verified_as_commits', 'observed_at')},
        'head': observed['remote']['head'], 'base': observed['remote']['base'],
        'comparisons': {**observed['comparisons'],
            'diff_version_head_matches_candidate': None if not diff else diff['head_sha'] == candidate_sha},
        'review_request': request, 'reason': reason, 'linked_at': now(),
        'relationship': 'operator_asserted_review_context', 'context_only': True,
        'execution_authorized': False, 'proves_original_attempt': False}
    row = {'project': project_id, 'scope': scope, 'sha': _identity(payload), 'document': json.dumps(payload, ensure_ascii=False)}
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = json.loads(db.execute('SELECT document FROM projects WHERE id=?', (project_id,)).fetchone()[0])
        _revision(current, expected_revision)
        previous = db.execute(query, (project_id, scope)).fetchone()
        if previous is not None:
            return existing(previous, db)
        result = _review_link(row, db)
        db.execute('INSERT INTO candidate_review_links VALUES (?,?,?,?)',
                   (project_id, scope, row['sha'], row['document']))
        return {'record': result, 'already_saved': False, 'fresh_observations': True}


def capture(state: State, project_id: str, issue_id: str, expected_revision: int) -> dict:
    project = state.project(project_id)
    _revision(project, expected_revision)
    observation, binding = _observe(project, issue_id)
    observed_at = observation.pop('observed_at')
    payload = {'schema_version': 1, 'observation': observation, 'tracker_binding': binding}
    digest = _identity(payload)
    # The GET has finished. A changed binding cannot retarget this frozen read.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO issue_snapshots VALUES (?,?,?,?) ON CONFLICT(project,sha) DO NOTHING',
                   (project_id, digest, observed_at, json.dumps(payload, ensure_ascii=False)))
        row = db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha=?', (project_id, digest)).fetchone()
        saved = snapshot_from_row(row)
    return {'snapshot': saved, 'observed_at': observed_at}


def _page(project_id: str, kind: str, filters: dict, limit: int, after: str | None) -> tuple[dict, str]:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Issue history page limit must be 1–100')
    scope = {'schema_version': 1, 'kind': kind, 'project': project_id, 'filters': filters}
    if after is None:
        return scope, ''
    try:
        if not isinstance(after, str) or len(after) > 2048:
            raise ValueError('Invalid cursor')
        document = json.loads(base64.b64decode(after + '=' * (-len(after) % 4), altchars=b'-_', validate=True))
        if not isinstance(document, dict) or set(document) != {*scope, 'after'} or any(document[key] != value for key, value in scope.items()):
            raise ValueError('Cursor scope changed')
        validate_digest(document['after'])
    except (ValueError, TypeError):
        raise ValueError('Issue history cursor is invalid or belongs to another query') from None
    return scope, document['after']


def _continuation(scope: dict, digest: str) -> str:
    return base64.urlsafe_b64encode(json.dumps({**scope, 'after': digest}, sort_keys=True).encode()).decode().rstrip('=')


def snapshots(state: State, project_id: str, *, limit: int = 50, after: str | None = None) -> dict:
    state.project(project_id)
    scope, position = _page(project_id, 'issue-snapshots', {}, limit, after)
    result, more = [], False
    with state.connect() as db:
        for index, row in enumerate(db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha>? ORDER BY sha LIMIT ?',
                                                (project_id, position, limit + 1))):
            if index == limit:
                more = True
                break
            saved = snapshot_from_row(row)
            observation = saved['payload']['observation']
            title = observation['issue']['title']
            result.append({'sha256': saved['sha256'], 'first_observed_at': saved['first_observed_at'],
                'source': observation['source'], 'project_revision': observation['project']['revision'],
                'title_preview': title[:160], 'title_truncated': len(title) > 160})
    return {'project': project_id, 'snapshots': result,
            'next_cursor': _continuation(scope, result[-1]['sha256']) if more else None}


def link_task(state: State, project_id: str, digest: str, task_id: str, creation_sha256: str,
              expected_revision: int, reason: str) -> dict:
    from . import tasks

    project = state.project(project_id)
    validate_digest(digest)
    validate_digest(creation_sha256)
    contracts.validate(reason, _LINK['properties']['reason'], 'Issue task link reason')
    key = (project_id, digest, task_id, creation_sha256)
    query = 'SELECT * FROM issue_task_links WHERE project=? AND snapshot=? AND task_id=? AND creation_sha=?'
    with state.connect() as db:
        existing = db.execute(query, key).fetchone()
    if existing is not None:
        return _link(existing)
    _revision(project, expected_revision)
    snapshot(state, project_id, digest)
    target = tasks.creation(state, project_id, task_id)
    if target['status'] != 'published' or target['intent_sha256'] != creation_sha256:
        raise ValueError('Issue context link requires the exact published original task creation')
    payload = {'schema_version': 1, 'project': project_id, 'snapshot_sha256': digest,
        'task': {'id': task_id, 'creation_sha256': creation_sha256, 'compiled_sha256': target['compiled_sha256'],
                 'created_revision': target['created_revision']}, 'reason': reason, 'linked_at': now(),
        'context_only': True, 'relationship': 'operator_asserted_context', 'execution_authorized': False}
    contracts.validate(payload, _LINK, 'Issue task link')
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute(query, key).fetchone()
        if existing is not None:
            return _link(existing)
        current = json.loads(db.execute('SELECT document FROM projects WHERE id=?', (project_id,)).fetchone()[0])
        _revision(current, expected_revision)
        db.execute('INSERT INTO issue_task_links VALUES (?,?,?,?,?,?)',
                   (*key, _identity(payload), json.dumps(payload, ensure_ascii=False)))
        return _link(db.execute(query, key).fetchone())


def links(state: State, project_id: str, *, snapshot_sha256: str | None = None, task_id: str | None = None,
          limit: int = 50, after: str | None = None) -> dict:
    state.project(project_id)
    filters = {'snapshot_sha256': snapshot_sha256, 'task_id': task_id}
    scope, position = _page(project_id, 'issue-links', filters, limit, after)
    conditions, parameters = ['project=?', 'sha>?'], [project_id, position]
    if snapshot_sha256 is not None:
        validate_digest(snapshot_sha256)
        conditions.append('snapshot=?')
        parameters.append(snapshot_sha256)
    if task_id is not None:
        conditions.append('task_id=?')
        parameters.append(task_id)
    result, more = [], False
    with state.connect() as db:
        query = 'SELECT * FROM issue_task_links WHERE ' + ' AND '.join(conditions) + ' ORDER BY sha LIMIT ?'
        for index, row in enumerate(db.execute(query, (*parameters, limit + 1))):
            if index == limit:
                more = True
                break
            result.append(_link(row))
    return {'project': project_id, 'links': result,
            'next_cursor': _continuation(scope, result[-1]['sha256']) if more else None}


def validate_storage(db) -> dict:
    """Verify domain records in an offline backup without State or external I/O."""
    counts = {'issue_snapshots': 0, 'issue_task_links': 0, 'candidate_review_links': 0}
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version < 2:
        return counts
    for row in db.execute('SELECT * FROM issue_snapshots'):
        snapshot_from_row(row)
        counts['issue_snapshots'] += 1
    for row in db.execute('SELECT * FROM issue_task_links'):
        _link(row)
        counts['issue_task_links'] += 1
    orphan = db.execute('''SELECT 1 FROM issue_task_links l LEFT JOIN issue_snapshots s
        ON l.project=s.project AND l.snapshot=s.sha WHERE s.sha IS NULL LIMIT 1''').fetchone()
    if orphan or db.execute('''SELECT 1 FROM issue_snapshots s LEFT JOIN projects p
        ON s.project=p.id WHERE p.id IS NULL LIMIT 1''').fetchone():
        raise ValueError('Saved issue context has a missing snapshot or project')
    if version >= 4:
        for row in db.execute('SELECT * FROM candidate_review_links'):
            _review_link(row, db)
            counts['candidate_review_links'] += 1
    return counts
