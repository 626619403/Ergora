"""Project-scoped observations; reading issue text grants no execution authority."""

import base64
import hashlib
import json
import re

from . import contracts, issue_backends, projects
from .state import State, now


_SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$', 'not': {'pattern': '\\s'}}
_TEXT = {'type': 'string', 'minLength': 1}
_SNAPSHOT = {
    'type': 'object', 'additionalProperties': False,
    'required': ['schema_version', 'observation', 'tracker_binding'],
    'properties': {
        'schema_version': {'type': 'integer', 'const': 1},
        'observation': {**contracts.ISSUE_OBSERVATION,
            'required': [*contracts.ISSUE_OBSERVATION['required'], 'project', 'configuration_sha256'],
            'properties': {key: value for key, value in contracts.ISSUE_OBSERVATION['properties'].items()
                           if key != 'observed_at'}},
        'tracker_binding': {'type': 'object', 'required': ['tool', 'project']},
    },
}
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


def _digest(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('Issue record identity must be a SHA256 digest')


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


def _snapshot(row) -> dict:
    payload = json.loads(row['document'])
    contracts.validate(payload, _SNAPSHOT, 'Saved issue snapshot')
    observation, binding = payload['observation'], payload['tracker_binding']
    backend = issue_backends.for_binding(binding)  # Configuration only; never reads credentials or sends I/O.
    if (_identity(payload) != row['sha'] or observation['project']['id'] != row['project']
            or binding['tool'] != observation['source']['provider']
            or binding['project'] != observation['source']['project']
            or backend.api_url != observation['source']['api_url']
            or not isinstance(row['first_observed_at'], str) or not row['first_observed_at']):
        raise ValueError('Saved issue snapshot differs from its content identity or project')
    return {'schema_version': 1, 'sha256': row['sha'], 'first_observed_at': row['first_observed_at'], 'payload': payload}


def _link(row) -> dict:
    payload = json.loads(row['document'])
    contracts.validate(payload, _LINK, 'Saved issue task link')
    task = payload['task']
    if (_identity(payload) != row['sha'] or payload['project'] != row['project']
            or payload['snapshot_sha256'] != row['snapshot'] or task['id'] != row['task_id']
            or task['creation_sha256'] != row['creation_sha']):
        raise ValueError('Saved issue task link differs from its content identity or target')
    return {'schema_version': 1, 'sha256': row['sha'], 'payload': payload}


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
        saved = _snapshot(row)
    return {'snapshot': saved, 'observed_at': observed_at}


def snapshot(state: State, project_id: str, digest: str) -> dict:
    state.project(project_id)
    _digest(digest)
    with state.connect() as db:
        row = db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha=?', (project_id, digest)).fetchone()
    if row is None:
        raise ValueError('Unknown issue snapshot in this project')
    return _snapshot(row)


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
        _digest(document['after'])
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
            saved = _snapshot(row)
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
    _digest(digest)
    _digest(creation_sha256)
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
        _digest(snapshot_sha256)
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
    counts = {'issue_snapshots': 0, 'issue_task_links': 0}
    if db.execute('PRAGMA user_version').fetchone()[0] < 2:
        return counts
    for row in db.execute('SELECT * FROM issue_snapshots'):
        _snapshot(row)
        counts['issue_snapshots'] += 1
    for row in db.execute('SELECT * FROM issue_task_links'):
        _link(row)
        counts['issue_task_links'] += 1
    orphan = db.execute('''SELECT 1 FROM issue_task_links l LEFT JOIN issue_snapshots s
        ON l.project=s.project AND l.snapshot=s.sha WHERE s.sha IS NULL LIMIT 1''').fetchone()
    if orphan or db.execute('''SELECT 1 FROM issue_snapshots s LEFT JOIN projects p
        ON s.project=p.id WHERE p.id IS NULL LIMIT 1''').fetchone():
        raise ValueError('Saved issue context has a missing snapshot or project')
    return counts
