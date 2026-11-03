"""One immutable native submission, including interrupted admission and lost replies."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import projects, reference, tasks
from ergora.state import State
from test_registrations import installation, registration
from test_task_creation import creation_project, _files


@pytest.fixture
def submitted_creation(creation_project, request):
    if sys.platform != 'linux':
        pytest.skip('Formal admission uses the Linux reference runtime')
    pytest.importorskip('temporalio')
    state, registration, definition = creation_project
    template = getattr(request, 'param', 'repository-governance')
    definition['task_type'] = template
    definition['input']['risk'] = 'high' if template == 'large-change' else 'standard'
    interpreter = Path(registration['execution']['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    preview = tasks.preview(state, 'demo', definition, 1)
    result = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    return state, registration, definition, result


@pytest.fixture
def native_client(monkeypatch):
    if sys.platform != 'linux':
        pytest.skip('Formal admission uses the Linux reference runtime')
    original = reference.subprocess.run
    fixture = Path(__file__).parent / 'fixtures/task_submission_client.py'
    def invoke(argv, **kwargs):
        if 'from ergora.reference_task_submission import main;main()' in argv:
            argv = [*argv[:-1], fixture.read_text(encoding='utf-8')]
        return original(argv, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', invoke)


def _root(creation):
    return Path(creation[1]['execution']['state_directory'])


def _calls(creation):
    path = _root(creation) / 'sdk-fixture/calls.jsonl'
    return [json.loads(line)['event'] for line in path.read_text().splitlines()] if path.exists() else []


def _start(creation, **kwargs):
    return tasks.start(creation[0], 'demo', creation[2]['task_id'], 1, creation[3]['intent_sha256'], **kwargs)


def _status(creation):
    return tasks.submission(State(creation[0].root), 'demo', creation[2]['task_id'])


def _resume(creation):
    status = _status(creation)
    return tasks.resume_start(State(creation[0].root), 'demo', creation[2]['task_id'], 1, status['intent_sha256'])


def _seed_run(creation, *, conflicting=False, owned=False, numeric=None):
    root = _root(creation)
    folder = root/'sdk-fixture';folder.mkdir(exist_ok=True)
    spec = json.loads((root/'tasks/new-task/task.spec.json').read_text())
    if conflicting:
        spec['request']['input']['goal'] = 'A different original request'
    if numeric is not None:
        spec['profile']['schema_version'] = numeric
    memo={'ergora.submission_sha256':_status(creation)['intent_sha256']} if owned else {}
    (folder/'server.json').write_text(json.dumps({'run_id': 'owned-run' if owned else 'foreign-run',
                                                'spec': spec, 'memo': memo}), encoding='utf-8')


@pytest.mark.parametrize('template', ['repository-governance', 'large-change'])
def test_native_start_and_retries_preserve_one_run_and_frozen_roles(creation_project, native_client, template):
    pytest.importorskip('temporalio')
    state, registration, definition = creation_project
    runtime = Path(registration['execution']['installation']) / '.venv'
    if not runtime.exists():
        runtime.symlink_to(sys.prefix, target_is_directory=True)
    definition['task_type'] = template
    definition['input']['risk'] = 'high' if template == 'large-change' else 'standard'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    creation = (state, registration, definition, created)
    original = {p.name:p.read_bytes() for p in (_root(creation)/'tasks/new-task').iterdir()}
    assert _status(creation)['status'] == 'not_recorded' and _calls(creation) == []
    result = _start(creation)
    assert result['status'] == 'submitted' and result['run_id'] == 'original-run'
    assert result['workflow_id'] == 'dev-task/new-task' and result['execution_success'] is None
    assert result['runtime_status'] == 'not_queried'
    assert _start(creation) == _resume(creation) == _status(creation) == result
    assert _calls(creation).count('start') == _calls(creation).count('doctor') == 1
    assert ( _root(creation) / 'ingress/leases.sqlite3').is_file()
    assert json.loads((_root(creation)/'tasks/new-task/cli-ingress.json').read_text())['owner'] == 'local-cli'
    assert all((_root(creation)/'tasks/new-task'/name).read_bytes()==raw for name,raw in original.items())
    projects.bind(state, 'demo', 'reviewer', {'tool':'codex','model':'later-model'}, 1)
    assert tasks.resume_start(state,'demo','new-task',2,result['intent_sha256'])['run_id']=='original-run'
    assert _calls(creation).count('start')==1


@pytest.mark.parametrize('scenario,match', [
    ('doctor-blocked','prerequisites'), ('policy-blocked','policy denies'), ('connect-blocked','offline'),
])
def test_native_admission_is_not_bypassed(submitted_creation, native_client, monkeypatch, scenario, match):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', scenario)
    with pytest.raises(ValueError, match=match):
        _start(submitted_creation)
    assert _status(submitted_creation)['status']=='prepared'
    assert 'start' not in _calls(submitted_creation)
    assert not (_root(submitted_creation)/'tasks/new-task/cli-ingress.json').exists()
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    assert _start(submitted_creation)['status']=='prepared'  # repeated start never retries
    assert _resume(submitted_creation)['status']=='submitted'
    assert _calls(submitted_creation).count('start')==1


@pytest.mark.parametrize('scenario,status', [
    ('before-intent','not_recorded'), ('after-intent','prepared'), ('before-attempt','prepared'),
    ('after-attempt','unknown'), ('before-result','unknown'), ('after-result','submitted'),
    ('lost-response','unknown'),
])
def test_each_interruption_recovers_without_reissuing_uncertain_start(submitted_creation, native_client, monkeypatch, scenario, status):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', scenario)
    with pytest.raises(ValueError, match='interruption|timed out'):
        _start(submitted_creation)
    assert _status(submitted_creation)['status']==status
    if scenario=='before-intent':
        assert _calls(submitted_creation)==[]
        assert not (_root(submitted_creation)/'ingress').exists()
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    if status=='not_recorded':
        result=_start(submitted_creation)
    else:
        result=_resume(submitted_creation)
    if scenario=='after-attempt':
        assert result['status']=='unknown' and result['reconciliation']=='not_found'
        assert 'start' not in _calls(submitted_creation)
        assert _resume(submitted_creation)['status']=='unknown'
    else:
        assert result['status']=='submitted' and result['run_id']=='original-run'
        assert _calls(submitted_creation).count('start')==1
    assert _start(submitted_creation)['status']==result['status']


def test_parallel_and_lost_parent_response_keep_the_original_receipt(submitted_creation,native_client,monkeypatch):
    def concurrent_start(_):
        try:
            return _start(submitted_creation)
        except ValueError as error:
            assert any(part in str(error) for part in ('temporarily unavailable','locked','would block'))
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(concurrent_start,range(2)))
    completed=_status(submitted_creation)
    assert completed['status']=='submitted' and _calls(submitted_creation).count('start')==1
    assert any(result is not None and result['status']=='submitted' for result in outcomes)
    for observed in filter(None,outcomes):
        assert observed['status'] in ('prepared','unknown','submitted')
        assert observed['intent_sha256']==completed['intent_sha256']
        assert observed['run_id'] in (None,completed['run_id'])
    assert _start(submitted_creation)==completed
    original=reference.subprocess.run
    def lost(argv,**kwargs):
        result=original(argv,**kwargs)
        if 'reference_task_submission import' in argv[-1]:
            assert result.returncode==0
            raise subprocess.TimeoutExpired(argv,25)
        return result
    monkeypatch.setattr(reference.subprocess,'run',lost)
    with pytest.raises(ValueError,match='process timed out'):
        _start(submitted_creation)
    monkeypatch.setattr(reference.subprocess,'run',original)
    assert _resume(submitted_creation)==completed
    assert _calls(submitted_creation).count('start')==1


@pytest.mark.parametrize('record', ['cli-ingress.json','requests','receipts'])
def test_native_records_without_our_intent_are_not_adopted(submitted_creation,native_client,record):
    root=_root(submitted_creation)
    path=root/'tasks/new-task'/record if record.endswith('.json') else root/record/'new-task'
    path.parent.mkdir(parents=True,exist_ok=True)
    if record.endswith('.json'):
        path.write_text('{}')
    else:
        path.mkdir()
    with pytest.raises(ValueError,match='cannot be adopted'):
        _start(submitted_creation)
    assert _status(submitted_creation)['status']=='not_recorded'
    assert _calls(submitted_creation)==[]


def test_preexisting_run_cannot_be_adopted_even_after_its_history_disappears(submitted_creation,native_client):
    _seed_run(submitted_creation)
    with pytest.raises(ValueError,match='already exists without'):
        _start(submitted_creation)
    status=_status(submitted_creation)
    assert status['status']=='rejected' and status['conflicting_run_id']=='foreign-run'
    (_root(submitted_creation)/'sdk-fixture/server.json').unlink()
    assert _resume(submitted_creation)==_start(submitted_creation)==status
    assert 'start' not in _calls(submitted_creation)


def test_initial_input_collision_stays_rejected_after_history_disappears(submitted_creation,native_client):
    _seed_run(submitted_creation,conflicting=True)
    with pytest.raises(ValueError,match='original task spec differs'):
        _start(submitted_creation)
    status=_status(submitted_creation)
    assert status['status']=='rejected' and status['reason']=='lookup_rejected'
    (_root(submitted_creation)/'sdk-fixture/server.json').unlink()
    assert _resume(submitted_creation)==status
    assert 'start' not in _calls(submitted_creation)


@pytest.mark.parametrize('lost_rejection',[False,True])
def test_competing_start_after_preflight_is_never_adopted(submitted_creation,native_client,monkeypatch,lost_rejection):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','race-rejection-lost' if lost_rejection else 'race-foreign-run')
    with pytest.raises(ValueError,match='already started during|rejection write was lost'):
        _start(submitted_creation)
    status=_status(submitted_creation)
    assert status['status']==('unknown' if lost_rejection else 'rejected')
    assert status['run_id'] is None
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    if lost_rejection:
        with pytest.raises(ValueError,match='matching submission memo'):
            _resume(submitted_creation)
        assert _status(submitted_creation)['status']=='unknown'
    else:
        assert _resume(submitted_creation)==status
    (_root(submitted_creation)/'sdk-fixture/server.json').unlink()
    result=_resume(submitted_creation)
    assert result['status']==status['status']
    assert _calls(submitted_creation).count('start')==1


@pytest.mark.parametrize('numeric',[True,1.0])
def test_unknown_recovery_requires_strict_json_and_own_memo(submitted_creation,native_client,monkeypatch,numeric):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','after-attempt')
    with pytest.raises(ValueError):
        _start(submitted_creation)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    _seed_run(submitted_creation,owned=True,numeric=numeric)
    with pytest.raises(ValueError,match='JSON identity'):
        _resume(submitted_creation)
    assert _status(submitted_creation)['status']=='unknown'
    assert 'start' not in _calls(submitted_creation)


@pytest.mark.parametrize('memo',[{}, {'ergora.submission_sha256':'0'*64}])
def test_unknown_recovery_refuses_a_different_submission_memo(submitted_creation,native_client,monkeypatch,memo):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','after-attempt')
    with pytest.raises(ValueError):
        _start(submitted_creation)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    _seed_run(submitted_creation,owned=True)
    path=_root(submitted_creation)/'sdk-fixture/server.json'
    record=json.loads(path.read_text());record['memo']=memo;path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='matching submission memo'):
        _resume(submitted_creation)
    assert _status(submitted_creation)['status']=='unknown'
    assert 'start' not in _calls(submitted_creation)


def test_submission_requires_the_registered_full_linux_environment(creation_project,monkeypatch):
    state,registration,definition=creation_project
    monkeypatch.setattr(reference.sys,'platform','win32')
    with pytest.raises(ValueError,match='WSL2'):
        tasks.submission(state,'demo','new-task')
    monkeypatch.setattr(reference.sys,'platform','linux')
    original=Path.is_file
    monkeypatch.setattr(Path,'is_file',lambda path:False if path.name=='python' else original(path))
    with pytest.raises(ValueError,match='full Linux environment'):
        tasks.submission(state,'demo','new-task')


def test_reconciliation_requires_original_history_and_does_not_release_or_restart(submitted_creation,native_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','after-attempt')
    with pytest.raises(ValueError):
        _start(submitted_creation)
    _seed_run(submitted_creation,conflicting=True)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    with pytest.raises(ValueError,match='original task spec differs'):
        _resume(submitted_creation)
    assert _status(submitted_creation)['status']=='unknown'
    assert 'start' not in _calls(submitted_creation)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','lookup-unavailable')
    with pytest.raises(ValueError,match='unavailable|UNAVAILABLE'):
        _resume(submitted_creation)
    assert _status(submitted_creation)['status']=='unknown'


@pytest.mark.parametrize('revision',[True,0,'1',2])
def test_stale_or_coerced_revisions_never_save_intent(submitted_creation,revision):
    with pytest.raises(ValueError,match='revision'):
        tasks.start(submitted_creation[0],'demo','new-task',revision,submitted_creation[3]['intent_sha256'])
    assert _status(submitted_creation)['status']=='not_recorded'


@pytest.mark.parametrize('timeout',[True])
def test_invalid_timeouts_never_save_intent(submitted_creation,timeout):
    before = _files(_root(submitted_creation))
    with pytest.raises(ValueError,match='timeout'):
        _start(submitted_creation,timeout=timeout)
    assert _files(_root(submitted_creation)) == before
    assert _status(submitted_creation)['status']=='not_recorded'


def test_creation_identity_registration_and_legacy_boundaries(submitted_creation,native_client,tmp_path):
    state,registration,definition,created=submitted_creation
    with pytest.raises(ValueError,match='digest changed'):
        tasks.start(state,'demo','new-task',1,'0'*64)
    assert _status(submitted_creation)['status']=='not_recorded'
    with pytest.raises(ValueError,match='original submission intent'):
        tasks.resume_start(state,'demo','new-task',1,'0'*64)
    with pytest.raises(ValueError,match='Invalid identifier'):
        tasks.submission(state,'demo','../escape')
    other=State(tmp_path/'other-control')
    with other.connect() as db:
        db.execute('INSERT INTO projects VALUES (?,?)',('demo',json.dumps(state.project('demo'))))
    with pytest.raises(ValueError,match='another control directory'):
        tasks.start(other,'demo','new-task',1,created['intent_sha256'])
    (_root(submitted_creation)/'ergora/task-creations/new-task.intent.json').unlink()
    with pytest.raises(ValueError,match='legacy tasks cannot be adopted'):
        _start(submitted_creation)
    assert _calls(submitted_creation)==[]


@pytest.mark.parametrize('name,mutation',[
    ('intent',lambda d:d.update(spec_sha256='0'*64)),
    ('intent',lambda d:d.update(schema_version=True)),
    ('attempt',lambda d:d.update(intent_sha256='0'*64)),
    ('attempt',lambda d:d.update(schema_version=True)),
    ('result',lambda d:d.update(run_id=42)),
])
def test_drifted_operation_records_fail_visibly(submitted_creation,native_client,name,mutation):
    _start(submitted_creation)
    path=_root(submitted_creation)/('ergora/task-submissions/new-task.'+name+'.json')
    document=json.loads(path.read_text());mutation(document);path.write_text(json.dumps(document))
    with pytest.raises(ValueError,match='conflicts|valid run ID'):
        _status(submitted_creation)
    with pytest.raises(ValueError,match='conflicts|valid run ID'):
        _start(submitted_creation)
    assert _calls(submitted_creation).count('start')==1


def test_changed_task_files_refuse_runtime_operations(submitted_creation,native_client):
    path=_root(submitted_creation)/'tasks/new-task/agent-bindings.json'
    value=json.loads(path.read_text());value['project_revision']=99;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='incomplete or conflicted'):
        _start(submitted_creation)
    assert _calls(submitted_creation)==[]


def test_native_spec_read_drift_is_rejected_before_doctor_and_claim(submitted_creation,native_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','spec-read-drift')
    with pytest.raises(ValueError,match='spec changed after submission preflight'):
        _start(submitted_creation)
    assert _status(submitted_creation)['status']=='prepared'
    assert _calls(submitted_creation)==[]
    assert not (_root(submitted_creation)/'ingress').exists()
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    assert _resume(submitted_creation)['status']=='submitted'


def test_cli_and_api_share_submission_and_explicit_recovery(submitted_creation,native_client,monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app
    state=submitted_creation[0]
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    uri='/api/projects/demo/tasks/new-task'
    headers={'X-Ergora-Request':'1','Origin':'http://127.0.0.1'}
    body={'revision':1,'creation_sha256':submitted_creation[3]['intent_sha256']}
    assert client.post(uri+'/start',json=body).status_code==403
    assert client.post(uri+'/start',json=body,headers={**headers,'Origin':'https://foreign.test'}).status_code==403
    for invalid in ({'revision':True},{'timeout':True},{'timeout':61},{'creation_sha256':'bad'}):
        assert client.post(uri+'/start',json={**body,**invalid},headers=headers).status_code==422
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','after-attempt')
    assert client.post(uri+'/start',json=body,headers=headers).status_code==400
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    status=client.get(uri+'/submission').json()
    assert status['status']=='unknown'
    args=['--home',str(state.root),'task']
    assert cli.main([*args,'start','demo','new-task','--revision','1','--creation-sha256',body['creation_sha256']])==1
    resumed=client.post(uri+'/resume-start',json={'revision':1,'intent_sha256':status['intent_sha256']},headers=headers)
    assert resumed.status_code==200 and resumed.json()['status']=='unknown'
    _seed_run(submitted_creation,owned=True)
    resumed=client.post(uri+'/resume-start',json={'revision':1,'intent_sha256':status['intent_sha256']},headers=headers)
    assert resumed.json()['status']=='submitted' and resumed.json()['run_id']=='owned-run'
    assert cli.main([*args,'resume-start','demo','new-task','--revision','1','--intent-sha256',status['intent_sha256']])==0
    assert client.get(uri+'/submission').json()==_status(submitted_creation)
    assert 'start' not in _calls(submitted_creation)
