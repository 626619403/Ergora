"""Runtime facts stay native, spec-bound, run-pinned and independent of local publication."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import reference, tasks
from test_tasks import installation, registration, task_store


@pytest.fixture
def runtime_client(monkeypatch):
    pytest.importorskip('temporalio')
    original = reference.subprocess.run
    fixture = Path(__file__).parent/'fixtures/task_runtime_client.py'
    def select(scenario):
        def invoke(argv, **kwargs):
            if 'from ergora.reference_task_runtime import main;main()' in argv:
                argv = list(argv)
                argv[-1] = f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")'
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_RUNTIME_SCENARIO': scenario}
            return original(argv, **kwargs)
        monkeypatch.setattr(reference.subprocess, 'run', invoke)
    return select


@pytest.mark.parametrize('scenario,phase,terminal', [
    ('running','AWAITING_PLAN_APPROVAL',False), ('completed','REVIEW_READY',True),
    ('unconfirmed','CANCEL_UNCONFIRMED',True), ('terminated','NEEDS_RECONCILIATION',True),
])
def test_original_transport_status_preserves_domain_outcomes_and_changes_no_files(task_store, runtime_client, scenario, phase, terminal):
    state, folder=task_store
    before={p:p.read_bytes() for p in folder.parent.rglob('*') if p.is_file()}
    runtime_client(scenario)
    result=tasks.status(state,'demo','first',run_id='pinned-run',timeout=5)
    assert result['runtime_status']=='queried' and result['phase']==phase and result['terminal'] is terminal
    assert result['workflow_id']=='dev-task/first' and result['run_id']=='pinned-run'
    spec=json.loads((folder/'first/task.spec.json').read_bytes())
    assert result['request_sha256']==spec['request_sha256'] and result['profile_sha256']==spec['profile_sha256']
    assert {p:p.read_bytes() for p in folder.parent.rglob('*') if p.is_file()}==before
    assert 'execution_started' not in result


def test_only_authoritative_not_found_is_absence(task_store, runtime_client):
    state,_=task_store
    runtime_client('not-found')
    result=tasks.status(state,'demo','first')
    assert result['runtime_status']=='not_found' and result['run_id'] is None
    assert 'phase' not in result and 'terminal' not in result
    runtime_client('unavailable')
    with pytest.raises(ValueError,match='RPC failed: UNAVAILABLE'):
        tasks.status(state,'demo','first')


@pytest.mark.parametrize('scenario,error', [('collision','collision'),('connection-failed','connection failure'),('timeout','timed out')])
def test_runtime_errors_do_not_fall_back_to_compiled_or_retry(task_store, runtime_client, scenario, error):
    state,_=task_store
    runtime_client(scenario)
    with pytest.raises(ValueError,match=error):
        tasks.status(state,'demo','first',timeout=1)


@pytest.mark.parametrize('options',[{'timeout':True},{'timeout':0},{'timeout':61},{'run_id':''},{'run_id':' trailing '},{'run_id':'a'*129}])
def test_invalid_query_options_are_rejected_without_network(task_store, options):
    state,_=task_store
    with pytest.raises(ValueError):
        tasks.status(state,'demo','first',**options)


def test_sdk_absence_has_installation_guidance(task_store, monkeypatch):
    state,_=task_store
    original=reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util,'find_spec',lambda name:None if name=='temporalio' else original(name))
    with pytest.raises(ValueError,match=r'install ergora\[temporal\]'):
        tasks.status(state,'demo','first')


@pytest.mark.parametrize('failure',['timeout','empty-stderr'])
def test_query_process_failures_are_visible_and_not_retried(task_store, monkeypatch, failure):
    pytest.importorskip('temporalio')
    state,_=task_store
    original=reference.subprocess.run
    calls=[]
    def fail(argv,**kwargs):
        if 'from ergora.reference_task_runtime import main;main()' not in argv:
            return original(argv,**kwargs)
        calls.append(argv)
        if failure=='timeout':
            raise subprocess.TimeoutExpired(argv,25)
        return subprocess.CompletedProcess(argv,-9,'','')
    monkeypatch.setattr(reference.subprocess,'run',fail)
    with pytest.raises(ValueError,match='Task runtime query process'):
        tasks.status(state,'demo','first')
    assert len(calls)==1


def test_cli_api_and_unpinned_query_use_the_same_native_facts(task_store, runtime_client, monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    from ergora.cli import main
    import io
    from contextlib import redirect_stdout
    state,_=task_store
    runtime_client('running')
    expected=tasks.status(state,'demo','first')
    assert expected['run_id']=='run-1'
    output=io.StringIO()
    with redirect_stdout(output):
        code=main(['--home',str(state.root),'task','status','demo','first'])
    assert code==0 and json.loads(output.getvalue())==expected
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    response=client.get('/api/projects/demo/tasks/first/status')
    assert response.status_code==200 and response.json()==expected
    pinned=client.get('/api/projects/demo/tasks/first/status',params={'run_id':'pinned-run','timeout':5})
    assert pinned.json()['run_id']=='pinned-run'
    runtime_client('unavailable')
    failed=client.get('/api/projects/demo/tasks/first/status')
    assert failed.status_code==400 and 'UNAVAILABLE' in failed.json()['error']
