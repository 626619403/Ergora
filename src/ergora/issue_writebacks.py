"""Explicit candidate writebacks; native observations never replace a send receipt."""

from abc import ABC, abstractmethod
import json
import string

from . import contracts, issue_backends, issue_snapshots, issue_sources, projects, tasks
from .state import State, now
from .task_envelopes import identity


_TEXT = {'type': 'string', 'minLength': 1}
_SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$', 'not': {'pattern': '\\s'}}
_POSITIVE = {'type': 'integer', 'minimum': 1}
_INTENT = {'type': 'object', 'additionalProperties': False, 'properties': {
    'schema_version': {'const': 1}, 'kind': {'const': 'candidate-association-comment'},
    'template_version': {'const': 1}, 'project': _TEXT, 'project_revision': _POSITIVE,
    'configuration_sha256': _SHA, 'tracker_binding': {'type': 'object'},
    'scope_sha256': _SHA, 'actor_id': _POSITIVE, 'body': _TEXT, 'prepared_at': _TEXT,
    'target_at_prepare_sha256': _SHA,
    'source': {'type': 'object', 'additionalProperties': False, 'properties': {
        'provider': _TEXT, 'api_url': _TEXT, 'project': _TEXT, 'issue_id': _TEXT,
        'native_id': _POSITIVE, 'snapshot_sha256': _SHA}},
    'task': {'type': 'object', 'additionalProperties': False, 'properties': {
        'id': _TEXT, 'creation_sha256': _SHA, 'compiled_sha256': _SHA, 'request_sha256': _SHA,
        'profile_sha256': _SHA, 'run_id': _TEXT, 'candidate_sha': {'type': 'string', 'pattern': '^(?:[a-f0-9]{40}|[a-f0-9]{64})$'},
        'export_intent_sha256': _SHA, 'export_facts_sha256': _SHA, 'branch': _TEXT}},
}}
for _object in (_INTENT, _INTENT['properties']['source'], _INTENT['properties']['task']):
    _object['required'] = list(_object['properties'])

_LABEL_INTENT = {**_INTENT, 'properties': {
    **{key: value for key, value in _INTENT['properties'].items() if key != 'body'},
    'kind': {'const': 'candidate-label-add'}, 'label_name': _TEXT,
    'native_target': {'type': 'object', 'additionalProperties': False, 'properties': {
        'issue_id': _TEXT, 'repository_id': _TEXT, 'label_id': _TEXT, 'label_native_id': _POSITIVE},
        'required': ['issue_id', 'repository_id', 'label_id', 'label_native_id']},
    'operation': {'type': 'object', 'additionalProperties': False, 'properties': {
        'method': {'const': 'POST'}, 'url': _TEXT, 'body': {'type': 'object'}}, 'required': ['method', 'url', 'body']},
}}
_LABEL_INTENT['required'] = list(_LABEL_INTENT['properties'])
_LABEL_PAGE = {'type': 'object', 'additionalProperties': False, 'properties': {
    'issue_id': _TEXT, 'issue_number': _POSITIVE, 'project': _TEXT, 'repository_id': _TEXT,
    'labels': {'type': 'array', 'maxItems': 100, 'items': {'type': 'object', 'additionalProperties': False,
        'properties': {'id': _TEXT, 'name': _TEXT, 'repository_id': _TEXT}, 'required': ['id', 'name', 'repository_id']}},
    'page_info': {'type': 'object', 'additionalProperties': False, 'properties': {
        'has_next_page': {'type': 'boolean'}, 'end_cursor': {'anyOf': [_TEXT, {'type': 'null'}]}},
        'required': ['has_next_page', 'end_cursor']},
}}
_LABEL_PAGE['required'] = list(_LABEL_PAGE['properties'])
_LABEL_RECEIPT = {'type': 'object', 'additionalProperties': False, 'properties': {
    'http_status': {'const': 200}, 'response_sha256': _SHA, 'client_mutation_id': _TEXT, 'page': _LABEL_PAGE}}
_LABEL_RECEIPT['required'] = list(_LABEL_RECEIPT['properties'])


class _WritebackAction(ABC):
    """The two real actions share one durable lifecycle and own their actual differences."""

    kind: str
    observation_kind: str

    @abstractmethod
    def validate(self, intent: dict) -> None:
        """Validate frozen action fields offline, including the exact request/body."""

    @abstractmethod
    def select(self, backend, intent: dict) -> dict:
        """Read current native identity and return the fields to freeze/compare."""

    @abstractmethod
    def attempt_fields(self, intent: dict) -> dict:
        """Describe the request before it is sent, preserving released action formats."""

    @abstractmethod
    def write(self, backend, intent: dict) -> dict:
        """Make one native write through its provider owner."""

    @abstractmethod
    def match(self, intent: dict, native: dict) -> None:
        """Only a sufficient original response may acknowledge the saved attempt."""

    @abstractmethod
    def observe(self, backend, intent: dict, comment_id, page: int, cursor) -> dict:
        """Read one current resource/page; never claim the original attempt succeeded."""


class _CandidateComment(_WritebackAction):
    kind = 'candidate-association-comment'
    observation_kind = 'native-comment-observation'

    def validate(self, intent: dict) -> None:
        contracts.validate(intent, _INTENT, 'Issue comment intent')
        if _body(intent) != intent['body']:
            raise ValueError('Issue writeback differs from its fixed body')

    def select(self, backend, intent: dict) -> dict:
        return {'body': _body(intent), 'target_at_prepare_sha256': _target(backend, intent['source'])['response']['sha256']}

    def attempt_fields(self, intent: dict) -> dict:
        return {'method': 'POST', 'payload_sha256': identity({'body': intent['body']})}

    def write(self, backend, intent: dict) -> dict:
        return backend.create_comment(intent['source']['issue_id'], intent['source']['native_id'], intent['body'])

    def match(self, intent: dict, native: dict) -> None:
        _matched_response(intent, native)

    def observe(self, backend, intent: dict, comment_id, page: int, cursor) -> dict:
        if cursor is not None:
            raise ValueError('Comment observations use page numbers, not label cursors')
        source = intent['source']
        native = (backend.read_comment(source['issue_id'], source['native_id'], comment_id) if comment_id is not None else
                  backend.list_comments(source['issue_id'], source['native_id'], page))
        return {'native': native, 'matching_ids': [item['id'] for item in native['comments']
            if item['ordinary'] and item['actor_id'] == intent['actor_id'] and item['body'] == intent['body']]}


class _CandidateLabel(_WritebackAction):
    kind = 'candidate-label-add'
    observation_kind = 'native-label-observation'

    def validate(self, intent: dict) -> None:
        contracts.validate(intent, _LABEL_INTENT, 'Issue label intent')
        expected = issue_backends.for_binding(intent['tracker_binding']).label_operation(
            intent['source'], intent['native_target'], intent['scope_sha256'])
        if intent['operation'] != expected:
            raise ValueError('Issue label writeback differs from its exact native ID request')

    def select(self, backend, intent: dict) -> dict:
        selection = backend.label_selection(intent['source'], intent['label_name'])
        return {**selection, 'operation': backend.label_operation(intent['source'], selection['native_target'], intent['scope_sha256'])}

    def attempt_fields(self, intent: dict) -> dict:
        operation = intent['operation']
        return {'method': operation['method'], 'url': operation['url'], 'payload_sha256': identity(operation['body'])}

    def write(self, backend, intent: dict) -> dict:
        return backend.add_label(intent['source'], intent['native_target'], intent['scope_sha256'])

    def match(self, intent: dict, native: dict) -> None:
        contracts.validate(native, _LABEL_RECEIPT, 'Native label receipt')
        page, target = native['page'], intent['native_target']
        if (native['client_mutation_id'] != intent['scope_sha256'] or page['issue_id'] != target['issue_id']
                or page['repository_id'] != target['repository_id'] or page['project'] != intent['source']['project']
                or page['issue_number'] != int(intent['source']['issue_id'])
                or any(item['repository_id'] != target['repository_id'] for item in page['labels'])
                or (page['page_info']['has_next_page'] and not page['page_info']['end_cursor'])
                or not any(item['id'] == target['label_id'] and item['name'] == intent['label_name'] for item in page['labels'])):
            raise ValueError('Original label response does not prove the frozen target in its selected page; execution is not disproved')

    def observe(self, backend, intent: dict, comment_id, page: int, cursor) -> dict:
        if comment_id is not None or page != 1:
            raise ValueError('Label observations use an opaque cursor, not comment IDs or page numbers')
        native = backend.observe_label(intent['source'], intent['native_target'], cursor)
        matched = [item['id'] for item in native['page']['labels']
                   if item['id'] == intent['native_target']['label_id'] and item['name'] == intent['label_name']]
        return {'native': native, 'matching_ids': matched,
                'membership_in_page': 'present' if matched else 'not_seen'}


_ACTIONS = {action.kind: action for action in (_CandidateComment(), _CandidateLabel())}


def _action(intent: dict) -> _WritebackAction:
    if not isinstance(intent, dict) or intent.get('kind') not in _ACTIONS:
        raise ValueError('Unsupported saved issue writeback action')
    return _ACTIONS[intent['kind']]


def _scope(intent: dict) -> str:
    return identity({'kind': intent['kind'], 'project': intent['project'],
        'source': {key: value for key, value in intent['source'].items() if key != 'snapshot_sha256'},
        'task': {key: intent['task'][key] for key in ('id', 'creation_sha256', 'run_id', 'candidate_sha', 'export_intent_sha256')}})


def _body(intent: dict) -> str:
    task = intent['task']
    # JSON string literals prevent opaque run/branch names from injecting lines,
    # mentions or GitLab quick actions into the fixed association message.
    def literal(value):
        punctuation = string.punctuation.replace('"', '').replace('\\', '')
        return json.dumps(value, ensure_ascii=True).translate({ord(c): f'\\u{ord(c):04x}' for c in punctuation})
    return ('Ergora local candidate export (reference only).\n\n'
        f'Task: {literal(task["id"])}; run: {literal(task["run_id"])}.\n'
        f'Candidate: `{task["candidate_sha"]}`.\n'
        f'Local export branch: {literal(task["branch"])}. Remote publication and merge have not been verified.\n'
        f'Source snapshot: `{intent["source"]["snapshot_sha256"]}`.\n\n'
        f'<!-- ergora:candidate-association:v1:{intent["scope_sha256"]} -->')


def _record(row) -> dict:
    intent = json.loads(row['document'])
    action = _action(intent)
    action.validate(intent)
    if (intent['project'] != row['project'] or identity(intent) != row['sha']
            or intent['scope_sha256'] != row['scope'] or _scope(intent) != row['scope']
            or issue_sources.tracker_identity(intent['tracker_binding']) !=
               {key: intent['source'][key] for key in ('provider', 'api_url', 'project')}):
        raise ValueError('Issue writeback differs from its saved identity or fixed body')
    attempt = json.loads(row['attempt']) if row['attempt'] is not None else None
    result = json.loads(row['result']) if row['result'] is not None else None
    if attempt is not None:
        if not isinstance(attempt, dict):
            raise ValueError('Invalid saved issue writeback attempt')
        expected = _attempt(intent, attempt.get('saved_at'), attempt.get('target_response_sha256'))
        if attempt != expected:
            raise ValueError('Issue writeback attempt differs from its original intent')
    if result is not None:
        if (attempt is None or not isinstance(result, dict)
                or set(result) != {'schema_version', 'intent_sha256', 'attempt_sha256', 'received_at', 'native'}
                or result['schema_version'] != 1 or result['intent_sha256'] != row['sha']
                or result['attempt_sha256'] != identity(attempt) or not isinstance(result['received_at'], str)
                or not result['received_at']):
            raise ValueError('Issue writeback result has no matching original attempt')
        action.match(intent, result['native'])
    return {'project': row['project'], 'intent_sha256': row['sha'], 'intent': intent,
            'status': 'acknowledged' if result is not None else 'unknown' if attempt is not None else 'prepared',
            'attempt': attempt, 'result': result}


def _load(db, project_id: str, digest: str) -> dict:
    issue_snapshots.validate_digest(digest)
    row = db.execute('SELECT * FROM issue_writebacks WHERE project=? AND sha=?', (project_id, digest)).fetchone()
    if row is None:
        raise ValueError('No saved issue writeback for this project and intent')
    record = _record(row)
    saved = db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha=?',
                       (project_id, record['intent']['source']['snapshot_sha256'])).fetchone()
    if saved is None or _source(issue_snapshots.snapshot_from_row(saved)) != record['intent']['source']:
        raise ValueError('Issue writeback target differs from its original source snapshot')
    return record


def _source(saved: dict) -> dict:
    observed = saved['payload']['observation']
    return {**observed['source'], 'native_id': observed['issue']['native_id'], 'snapshot_sha256': saved['sha256']}


def _revision(project: dict, expected: int) -> None:
    if type(expected) is not int or project['revision'] != expected:
        raise ValueError('Project revision changed; reload before the issue writeback')


def _target(backend, source: dict) -> dict:
    observed = backend.read(source['issue_id'], authenticated=True)
    if observed['issue']['native_id'] != source['native_id']:
        raise ValueError('Current issue differs from the frozen native target')
    return observed



def prepare(state: State, project_id: str, task_id: str, expected_revision: int, *, run_id: str, candidate_sha: str) -> dict:
    return _prepare(state, project_id, task_id, expected_revision, run_id, candidate_sha, _ACTIONS['candidate-association-comment'], {})


def prepare_label(state: State, project_id: str, task_id: str, expected_revision: int, *, run_id: str,
                  candidate_sha: str, label_name: str) -> dict:
    return _prepare(state, project_id, task_id, expected_revision, run_id, candidate_sha,
                    _ACTIONS['candidate-label-add'], {'label_name': label_name})


def _prepare(state: State, project_id: str, task_id: str, expected_revision: int, run_id: str,
             candidate_sha: str, action: _WritebackAction, fields: dict) -> dict:
    project = state.project(project_id)
    _revision(project, expected_revision)
    configuration = projects.effective_configuration(project)
    binding = configuration['layers']['tracker']['binding']
    saved, task = tasks.exported_source_candidate(state, project, binding, task_id, run_id, candidate_sha)
    intent = {'schema_version': 1, 'kind': action.kind, 'template_version': 1,
        'project': project_id, 'project_revision': expected_revision, 'configuration_sha256': configuration['sha256'],
        'tracker_binding': binding,
        'source': _source(saved), 'task': task, **fields}
    scope = intent['scope_sha256'] = _scope(intent)
    with state.connect() as db:
        existing = db.execute('SELECT * FROM issue_writebacks WHERE project=? AND scope=?', (project_id, scope)).fetchone()
        if existing is not None:
            record = _load(db, project_id, existing['sha'])
            if any(record['intent'].get(key) != value for key, value in fields.items()):
                raise ValueError('This candidate action already has a frozen operand; use its original saved intent')
            return record
    backend = issue_backends.for_binding(binding)
    intent['actor_id'] = backend.current_actor()
    intent.update(action.select(backend, intent), prepared_at=now())
    digest = identity(intent)
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _revision(json.loads(db.execute('SELECT document FROM projects WHERE id=?', (project_id,)).fetchone()[0]), expected_revision)
        # Unique logical scope also covers simultaneous prepare with another actor
        # or a newly captured snapshot; there is one approved candidate association.
        db.execute('INSERT INTO issue_writebacks(project,sha,scope,document) VALUES (?,?,?,?) ON CONFLICT(project,scope) DO NOTHING',
                   (project_id, digest, scope, json.dumps(intent, ensure_ascii=False)))
        row = db.execute('SELECT * FROM issue_writebacks WHERE project=? AND scope=?', (project_id, scope)).fetchone()
        record = _load(db, project_id, row['sha'])
        if any(record['intent'].get(key) != value for key, value in fields.items()):
            raise ValueError('This candidate action already has a frozen operand; use its original saved intent')
        return record


def _attempt(intent: dict, saved_at: str, target_response_sha256: str) -> dict:
    issue_snapshots.validate_digest(target_response_sha256)
    if not isinstance(saved_at, str) or not saved_at:
        raise ValueError('Invalid issue writeback attempt time')
    return {'schema_version': 1, 'intent_sha256': identity(intent), 'saved_at': saved_at,
            'actor_id': intent['actor_id'], 'target_response_sha256': target_response_sha256,
            **_action(intent).attempt_fields(intent)}


def _matched_response(intent: dict, native: dict) -> None:
    if not isinstance(native, dict) or set(native) != {'comment', 'response_sha256', 'http_status'}:
        raise ValueError('Invalid saved native comment receipt')
    comment = native['comment']
    issue_snapshots.validate_digest(native['response_sha256'])
    if (native['http_status'] != 201 or not isinstance(comment, dict)
            or set(comment) != {'id', 'actor_id', 'body', 'ordinary', 'created_at', 'updated_at'}
            or type(comment['id']) is not int or comment['id'] < 1 or comment['ordinary'] is not True
            or type(comment['actor_id']) is not int or comment['actor_id'] != intent['actor_id'] or comment['body'] != intent['body']
            or any(not isinstance(comment[key], str) or not comment[key] for key in ('created_at', 'updated_at'))):
        raise ValueError('Write response does not match the original ordinary comment, body and actor')


def status(state: State, project_id: str, digest: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        record = _load(db, project_id, digest)
        row = db.execute('SELECT * FROM issue_writeback_observations WHERE project=? AND write_sha=? ORDER BY rowid DESC LIMIT 1',
                         (project_id, digest)).fetchone()
        if row is not None:
            record['latest_observation'] = _observation(row)
    return record


def _save_observation(state: State, project_id: str, digest: str, document: dict) -> None:
    with state.connect() as db:
        _load(db, project_id, digest)
        db.execute('INSERT INTO issue_writeback_observations VALUES (?,?,?,?) ON CONFLICT(project,write_sha,sha) DO NOTHING',
                   (project_id, digest, identity(document), json.dumps(document, ensure_ascii=False)))


def send(state: State, project_id: str, digest: str, expected_revision: int, *, confirm: bool = False) -> dict:
    if confirm is not True:
        raise ValueError('Sending an issue writeback requires explicit confirmation of its exact saved intent')
    record = status(state, project_id, digest)
    if record['status'] != 'prepared':
        return record
    intent = record['intent']
    action = _action(intent)
    project = state.project(project_id)
    _revision(project, expected_revision)
    binding = projects.effective_configuration(project)['layers']['tracker']['binding']
    if binding != intent['tracker_binding']:
        raise ValueError('Prepared issue writeback tracker binding changed; it cannot be retargeted')
    saved, task = tasks.exported_source_candidate(state, project, binding, intent['task']['id'], intent['task']['run_id'], intent['task']['candidate_sha'])
    if task != intent['task'] or _source(saved) != intent['source']:
        raise ValueError('Original task source or candidate export differs from the prepared writeback')
    backend = issue_backends.for_binding(intent['tracker_binding'])
    if backend.current_actor() != intent['actor_id']:
        raise ValueError('Authenticated actor changed; the original intent cannot be impersonated')
    selected = action.select(backend, intent)
    if any(intent[key] != value for key, value in selected.items() if key != 'target_at_prepare_sha256'):
        raise ValueError('Frozen writeback operand or native identity changed; the original intent cannot be retargeted')
    attempt = _attempt(intent, now(), selected['target_at_prepare_sha256'])
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = _load(db, project_id, digest)
        if current['status'] != 'prepared':
            return current
        _revision(json.loads(db.execute('SELECT document FROM projects WHERE id=?', (project_id,)).fetchone()[0]), expected_revision)
        db.execute('UPDATE issue_writebacks SET attempt=? WHERE project=? AND sha=?',
                   (json.dumps(attempt, ensure_ascii=False), project_id, digest))
    # The committed attempt is visible to another process before this POST.
    # Any exception or death after this point leaves unknown, never a retry slot.
    try:
        native = action.write(backend, intent)
        action.match(intent, native)
    except ValueError as error:
        _save_observation(state, project_id, digest, {'schema_version': 1, 'kind': 'write-error',
            'intent_sha256': digest, 'observed_at': now(), 'error': str(error)})
        return status(state, project_id, digest)
    result = {'schema_version': 1, 'intent_sha256': digest, 'attempt_sha256': identity(attempt),
              'received_at': now(), 'native': native}
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = _load(db, project_id, digest)
        _revision(json.loads(db.execute('SELECT document FROM projects WHERE id=?', (project_id,)).fetchone()[0]), expected_revision)
        if current['attempt'] != attempt:
            raise ValueError('Original issue writeback attempt changed before its result could be saved')
        db.execute('UPDATE issue_writebacks SET result=? WHERE project=? AND sha=?',
                   (json.dumps(result, ensure_ascii=False), project_id, digest))
    return status(state, project_id, digest)


def observe(state: State, project_id: str, digest: str, *, comment_id: str | None = None, page: int = 1,
            cursor: str | None = None) -> dict:
    record = status(state, project_id, digest)
    intent = record['intent']
    action = _action(intent)
    backend = issue_backends.for_binding(intent['tracker_binding'])
    observation = {'schema_version': 1, 'kind': action.observation_kind, 'intent_sha256': digest,
        'observed_at': now(), 'requested': {'comment_id': comment_id, 'page': page},
        'coverage': 'one_current_resource' if comment_id is not None else 'one_current_page',
        'proves_original_attempt': False}
    if cursor is not None:
        observation['requested']['cursor'] = cursor
    try:
        observation['reader_actor_id'] = backend.current_actor()
        observation.update(action.observe(backend, intent, comment_id, page, cursor))
    except ValueError as error:
        observation.update(coverage='incomplete', error=str(error))
    _save_observation(state, project_id, digest, observation)
    return status(state, project_id, digest)


def _observation(row) -> dict:
    document = json.loads(row['document'])
    if (not isinstance(document, dict) or document.get('schema_version') != 1
            or document.get('intent_sha256') != row['write_sha'] or identity(document) != row['sha']
            or document.get('kind') not in ('write-error', 'native-comment-observation', 'native-label-observation')
            or not isinstance(document.get('observed_at'), str) or not document['observed_at']
            or (document['kind'] != 'write-error' and document.get('proves_original_attempt') is not False)):
        raise ValueError('Issue writeback observation differs from its saved identity')
    return {'sha256': row['sha'], 'document': document}


def validate_storage(db) -> dict:
    """Check canonical records and references in an offline state backup."""
    counts = {'issue_writebacks': 0, 'issue_writeback_observations': 0}
    if db.execute('PRAGMA user_version').fetchone()[0] < 3:
        return counts
    for row in db.execute('SELECT * FROM issue_writebacks'):
        _load(db, row['project'], row['sha'])
        if db.execute('SELECT 1 FROM projects WHERE id=?', (row['project'],)).fetchone() is None:
            raise ValueError('Issue writeback has no owning project')
        counts['issue_writebacks'] += 1
    for row in db.execute('SELECT * FROM issue_writeback_observations'):
        _observation(row)
        _load(db, row['project'], row['write_sha'])
        counts['issue_writeback_observations'] += 1
    return counts
