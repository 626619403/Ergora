"""Preview approval and process-loss recovery preserve one native task contract."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import projects, reference, registrations, tasks
from ergora.state import State
from test_registrations import installation, registration


@pytest.fixture
def creation_project(registration):
    state, definition = registration
    registrations.register(state, definition, 0)
    task = {'schema_version': 1, 'task_id': 'new-task', 'task_type': 'repository-governance', 'issue_id': '1',
            'input': {'goal': 'Preserve the creation contract', 'allowed_paths': ['src'],
                      'acceptance': ['Keep scope and evidence'], 'constraints': [], 'risk': 'standard',
                      'work_units': [{'id': 'one', 'depends_on': [], 'paths': ['src'], 'instructions': 'Inspect source'}]}}
    return state, definition, task


def _files(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}


def _inject(monkeypatch, code):
    original = reference.subprocess.run
    def invoke(argv, **kwargs):
        if 'from ergora.reference_task_creation import main;main()' in argv:
            argv = list(argv)
            argv[-1] = 'from ergora.reference_task_creation import main, _Creation\n' + code + '\nmain()'
        return original(argv, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', invoke)


@pytest.mark.parametrize('template', ['repository-governance', 'large-change'])
def test_preview_is_stable_offline_and_create_freezes_the_original_contract(creation_project, template):
    state, registration, definition = creation_project
    definition['task_type'] = template
    definition['input']['risk'] = 'high' if template == 'large-change' else 'standard'
    root = Path(registration['execution']['state_directory'])
    before = state.project('demo')
    preview = tasks.preview(state, 'demo', definition, 1)
    assert preview == tasks.preview(State(state.root), 'demo', definition, 1)
    assert not root.exists() and state.project('demo') == before
    assert preview['execution_started_by_operation'] is False and preview['runtime_status'] == 'not_queried'
    files = preview['files']
    assert files['compiled.json']['spec'] == files['task.spec.json']
    assert files['task.spec.json']['request']['input'] == definition['input']
    assert files['agent-bindings.json']['configuration'] == projects.effective_configuration(before)
    assert tasks.creation(state, 'demo', 'new-task')['status'] == 'not_recorded'
    assert not root.exists()
    result = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    assert result['status'] == 'published' and result['intent_sha256'] == preview['preview_sha256']
    assert result['execution_started_by_operation'] is False and result['created_revision'] == 1
    assert set(result['files'].values()) == {'matches'}
    assert {p.name: json.loads(p.read_bytes()) for p in (root/'tasks/new-task').iterdir()} == files
    original = _files(root)
    assert tasks.create(State(state.root), 'demo', definition, 1, preview['preview_sha256']) == result
    assert tasks.resume_create(State(state.root), 'demo', 'new-task', 1, result['intent_sha256']) == result
    assert _files(root) == original
    assert tasks.show(state, 'demo', 'new-task')['spec'] == files['task.spec.json']
    assert not (root/'requests').exists() and not (root/'receipts').exists()


@pytest.mark.parametrize('mutation,match', [
    (lambda d: d.update(schema_version=True), 'schema_version'),
    (lambda d: d.update(task_id='../escape'), 'task_id'),
    (lambda d: d.update(task_type='training-optimization'), 'task_type'),
    (lambda d: d.update(extra=True), 'Additional properties'),
    (lambda d: d['input'].update(allowed_paths=['outside']), 'scope|path|policy'),
    (lambda d: d['input'].update(risk='critical'), 'risk'),
    (lambda d: d['input']['work_units'][0].update(depends_on=['missing']), 'dependency|unknown'),
])
def test_invalid_inputs_are_rejected_without_actual_task_files(creation_project, mutation, match):
    state, registration, definition = creation_project
    mutation(definition)
    with pytest.raises(ValueError, match=match):
        tasks.preview(state, 'demo', definition, 1)
    assert not Path(registration['execution']['state_directory']).exists()


def test_stale_approval_binding_and_registration_drift_are_visible(creation_project):
    state, registration, definition = creation_project
    preview = tasks.preview(state, 'demo', definition, 1)
    changed = deepcopy(definition);changed['input']['goal'] = 'Changed goal'
    with pytest.raises(ValueError, match='preview changed'):
        tasks.create(state, 'demo', changed, 1, preview['preview_sha256'])
    for revision in (True, '1', 0, 2):
        with pytest.raises(ValueError, match='revision'):
            tasks.create(state, 'demo', definition, revision, preview['preview_sha256'])
    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex'}, 1)
    with pytest.raises(ValueError, match='revision changed'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    with pytest.raises(ValueError, match='preview changed'):
        tasks.create(state, 'demo', definition, 2, preview['preview_sha256'])
    path = Path(registration['execution']['config_directory'])/'policies/demo/execution.json'
    path.write_text('{"allowed_task_types": []}', encoding='utf-8')
    with pytest.raises(ValueError, match='drift'):
        tasks.preview(state, 'demo', definition, 2)
    assert not Path(registration['execution']['state_directory']).exists()


@pytest.mark.parametrize('published_files', range(8))
def test_every_publication_interruption_resumes_the_original_snapshot(creation_project, monkeypatch, published_files):
    state, registration, definition = creation_project
    preview = tasks.preview(state, 'demo', definition, 1)
    _inject(monkeypatch, f'''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    original_write = self.core.write
    count = 0
    def interrupted(path, value, **kwargs):
        nonlocal count
        if path.parent == self.target or path == self.result_path:
            if count == {published_files}:
                raise OSError('simulated publication loss')
            count += 1
        return original_write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
    with pytest.raises(ValueError, match='publication loss'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    monkeypatch.undo()
    status = tasks.creation(State(state.root), 'demo', definition['task_id'])
    assert status['status'] == 'pending'
    assert list(status['files'].values()).count('matches') == published_files
    assert status['intent_sha256'] == preview['preview_sha256']
    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'new-model'}, 1)
    _inject(monkeypatch, "def forbidden(self):\n    raise AssertionError('resume must not recompile')\n_Creation.compile = forbidden")
    result = tasks.resume_create(State(state.root), 'demo', definition['task_id'], 2, status['intent_sha256'])
    assert result['status'] == 'published' and result['project_revision'] == 2 and result['created_revision'] == 1
    assert result['agent_bindings'] == preview['files']['agent-bindings.json']
    assert result['agent_bindings']['bindings']['reviewer'] != state.project('demo')['bindings']['reviewer']


def test_intent_failure_precedes_all_native_task_files(creation_project, monkeypatch):
    state, registration, definition = creation_project
    preview = tasks.preview(state, 'demo', definition, 1)
    _inject(monkeypatch, '''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    original_write = self.core.write
    def interrupted(path, value, **kwargs):
        if path == self.intent_path:
            raise OSError('intent storage failed')
        return original_write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
    with pytest.raises(ValueError, match='intent storage failed'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    root = Path(registration['execution']['state_directory'])
    assert not (root/'tasks').exists()
    assert not list(root.rglob('*.intent.json'))


@pytest.mark.parametrize('interrupted', [False, True])
def test_large_aggregate_intent_keeps_each_contract_bound_and_remains_recoverable(creation_project, monkeypatch, interrupted):
    state, registration, definition = creation_project
    definition['input']['acceptance'] = [f'{i:02d}:' + 'a' * 3990 for i in range(51)]
    preview = tasks.preview(state, 'demo', definition, 1)
    if interrupted:
        _inject(monkeypatch, '''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    original_write = self.core.write
    def interrupted(path, value, **kwargs):
        if path == self.target / 'task.spec.json':
            raise OSError('large intent publication interrupted')
        return original_write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
        with pytest.raises(ValueError, match='large intent publication interrupted'):
            tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
        monkeypatch.undo()
    else:
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    root = Path(registration['execution']['state_directory'])
    intent = root / 'ergora/task-creations/new-task.intent.json'
    original = intent.read_bytes()
    assert len(original) > 1_048_576
    assert all(p.stat().st_size <= 1_048_576 for p in (root/'tasks/new-task').iterdir())
    status = tasks.creation(State(state.root), 'demo', 'new-task')
    assert status['status'] == ('pending' if interrupted else 'published')
    restored = tasks.resume_create(State(state.root), 'demo', 'new-task', 1, status['intent_sha256'])
    assert restored['status'] == 'published'
    assert tasks.create(state, 'demo', definition, 1, preview['preview_sha256']) == restored
    assert intent.read_bytes() == original


def test_conflicts_legacy_ids_and_foreign_controls_are_never_adopted(creation_project, tmp_path):
    state, registration, definition = creation_project
    preview = tasks.preview(state, 'demo', definition, 1)
    tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    different = deepcopy(definition);different['input']['goal'] = 'Different task'
    other_preview = tasks.preview(state, 'demo', different, 1)
    with pytest.raises(ValueError, match='different creation intent'):
        tasks.create(state, 'demo', different, 1, other_preview['preview_sha256'])
    root = Path(registration['execution']['state_directory'])
    path = root/'tasks/new-task/task.json'
    value=json.loads(path.read_bytes());value['input']['goal']='Out of band edit'
    path.write_text(json.dumps(value), encoding='utf-8')
    assert tasks.creation(state, 'demo', 'new-task')['status'] == 'conflict'
    before=_files(root)
    with pytest.raises(ValueError, match='conflict'):
        tasks.resume_create(state, 'demo', 'new-task', 1, preview['preview_sha256'])
    assert _files(root)==before
    definition['task_id']='legacy-task'
    preview=tasks.preview(state,'demo',definition,1)
    (root/'tasks/legacy-task').mkdir()
    with pytest.raises(ValueError,match='legacy tasks cannot be adopted'):
        tasks.create(state,'demo',definition,1,preview['preview_sha256'])
    with pytest.raises(ValueError,match='No saved creation intent'):
        tasks.resume_create(state,'demo','legacy-task',1,preview['preview_sha256'])
    other=State(tmp_path/'foreign-control')
    with other.connect() as db:
        db.execute('INSERT INTO projects VALUES (?,?)',('demo',json.dumps(state.project('demo'))))
    with pytest.raises(ValueError,match='another project, registration or control'):
        tasks.creation(other,'demo','new-task')
    with pytest.raises(ValueError,match='another control'):
        tasks.preview(other,'demo',definition,1)


def test_parallel_creates_and_lost_response_keep_one_intent(creation_project, monkeypatch):
    state, registration, definition = creation_project
    preview=tasks.preview(state,'demo',definition,1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda _:tasks.create(State(state.root),'demo',definition,1,preview['preview_sha256']),range(2)))
    assert outcomes[0]==outcomes[1] and outcomes[0]['status']=='published'
    root=Path(registration['execution']['state_directory'])
    before=_files(root)
    original=reference.subprocess.run
    calls=[]
    def lost(argv,**kwargs):
        result=original(argv,**kwargs)
        calls.append(result)
        raise subprocess.TimeoutExpired(argv,30)
    monkeypatch.setattr(reference.subprocess,'run',lost)
    with pytest.raises(ValueError,match='timed out; inspect task creation status'):
        tasks.create(state,'demo',definition,1,preview['preview_sha256'])
    assert len(calls)==1 and calls[0].returncode==0
    monkeypatch.undo()
    assert tasks.creation(State(state.root),'demo','new-task')['status']=='published'
    assert tasks.resume_create(state,'demo','new-task',1,preview['preview_sha256'])==outcomes[0]
    assert _files(root)==before


@pytest.mark.skipif(os.name=='nt',reason='POSIX symlink/FIFO fixtures')
@pytest.mark.parametrize('kind',['symlink','fifo','oversized','invalid-json'])
def test_saved_intent_has_a_bounded_regular_file_boundary(creation_project, kind):
    state, registration, definition=creation_project
    preview=tasks.preview(state,'demo',definition,1)
    tasks.create(state,'demo',definition,1,preview['preview_sha256'])
    root=Path(registration['execution']['state_directory'])
    path=root/'ergora/task-creations/new-task.intent.json'
    stored=path.with_suffix('.saved');path.rename(stored)
    if kind=='symlink':
        path.symlink_to(stored)
    elif kind=='fifo':
        os.mkfifo(path)
    elif kind=='oversized':
        path.write_bytes(b' '* (16*1_048_576+1))
    else:
        path.write_text('{')
    with pytest.raises(ValueError):
        tasks.creation(state,'demo','new-task')


def test_cli_and_api_share_preview_creation_and_recovery(creation_project, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    state, registration, definition=creation_project
    path=tmp_path/'task.json';path.write_text(json.dumps(definition),encoding='utf-8')
    def cli(*args):
        result=subprocess.run([sys.executable,'-m','ergora','--home',str(state.root),'task',*args],
                              capture_output=True,text=True,encoding='utf-8',timeout=30)
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout)
    preview=cli('preview','demo','--definition',str(path),'--revision','1')
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    headers={'X-Ergora-Request':'1','Origin':'http://127.0.0.1'}
    uri='/api/projects/demo/tasks'
    payload={'definition':definition,'revision':1}
    assert client.post(uri+'/preview',json=payload).status_code==403
    assert client.post(uri+'/preview',json=payload,headers={**headers,'Origin':'https://other.test'}).status_code==403
    assert client.post(uri+'/preview',json={**payload,'revision':True},headers=headers).status_code==422
    response=client.post(uri+'/preview',json=payload,headers=headers)
    assert response.status_code==200,response.text
    assert response.json()==preview
    payload['preview_sha256']=preview['preview_sha256']
    created=client.post(uri,json=payload,headers=headers)
    assert created.status_code==200,created.text
    assert created.json()==cli('create','demo','--definition',str(path),'--revision','1','--preview-sha256',preview['preview_sha256'])
    assert client.get(uri+'/new-task/creation').json()==cli('creation','demo','new-task')
    resumed=client.post(uri+'/new-task/resume-create',json={'revision':1,'intent_sha256':preview['preview_sha256']},headers=headers)
    assert resumed.json()==cli('resume-create','demo','new-task','--revision','1','--intent-sha256',preview['preview_sha256'])
