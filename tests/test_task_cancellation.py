"""Cancellation preserves original-run identity and never reports confirmed stopping."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time

import pytest

from ergora import projects, reference, tasks
from ergora.state import State
from test_registrations import installation, registration
from test_task_creation import creation_project, _files
from test_task_submission import submitted_creation, native_client, _start, _root, _calls


@pytest.fixture
def cancellation_task(submitted_creation,native_client):
    _start(submitted_creation)
    return submitted_creation


@pytest.fixture
def cancellation_client(cancellation_task,monkeypatch):
    original=reference.subprocess.run
    fixture=Path(__file__).parent/'fixtures/task_cancellation_client.py'
    def invoke(argv,**kwargs):
        if 'from ergora.reference_task_cancellation import main;main()' in argv:
            argv=[*argv[:-1],fixture.read_text(encoding='utf-8')]
        return original(argv,**kwargs)
    monkeypatch.setattr(reference.subprocess,'run',invoke)


def cancel(creation,request='stop-one',revision=1,**kwargs):
    return tasks.cancel(creation[0],'demo','new-task',request,revision,
                        **{'run_id':'original-run','reason':'Owner requested stop','confirm':True,**kwargs})


def status(creation,request='stop-one'):
    return tasks.cancellation(State(creation[0].root),'demo','new-task',request)


def resume(creation,request='stop-one',revision=1,**kwargs):
    current=status(creation,request)
    return tasks.resume_cancel(State(creation[0].root),'demo','new-task',request,revision,
                               current['intent_sha256'],confirm=True,**kwargs)


def test_running_cancel_uses_the_original_handler_and_never_claims_stopped(cancellation_task,cancellation_client):
    assert status(cancellation_task)['status']=='not_recorded'
    result=cancel(cancellation_task)
    assert result['status']=='requested' and result['run_id']=='original-run'
    assert result['cancel_requested'] is True and result['cancellation_confirmed'] is None
    assert result['execution_success'] is None and result['runtime_status']=='not_queried'
    assert result['signal_delivery']=='acknowledged'
    assert cancel(cancellation_task)==resume(cancellation_task)==status(cancellation_task)==result
    assert _calls(cancellation_task).count('cancellation-signal')==1
    assert _calls(cancellation_task).count('cancellation-describe')==1
    handler=json.loads((_root(cancellation_task)/'sdk-fixture/cancellation-handler.json').read_text())
    assert handler['reason']=='Owner requested stop'
    projects.bind(cancellation_task[0],'demo','reviewer',{'tool':'codex','model':'later'},1)
    assert resume(cancellation_task,revision=2)['intent_sha256']==result['intent_sha256']
    assert _calls(cancellation_task).count('cancellation-signal')==1


@pytest.mark.parametrize('closed',['COMPLETED','FAILED','CANCELED','TERMINATED','CONTINUED_AS_NEW','TIMED_OUT'])
def test_closed_runs_record_no_new_signal_without_claiming_external_termination(cancellation_task,cancellation_client,monkeypatch,closed):
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','closed-'+closed)
    result=cancel(cancellation_task)
    assert result['status']=='already_closed' and result['temporal_status']==closed
    assert result['signal_delivery']=='not_sent' and not result['cancel_requested']
    assert not result['attempt_saved'] and result['result_saved']
    assert result['cancellation_confirmed'] is None and result['execution_success'] is None
    assert cancel(cancellation_task)==resume(cancellation_task)==status(cancellation_task)==result
    assert 'cancellation-signal' not in _calls(cancellation_task)


@pytest.mark.parametrize('scenario,expected',[
    ('closed-before-result','prepared'),('closed-after-result','already_closed'),
])
def test_closed_receipt_interruption_remains_a_no_signal_operation(cancellation_task,cancellation_client,monkeypatch,scenario,expected):
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO',scenario)
    with pytest.raises(ValueError,match='Fixture'):cancel(cancellation_task)
    assert status(cancellation_task)['status']==expected
    assert not status(cancellation_task)['attempt_saved']
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','closed-COMPLETED')
    assert resume(cancellation_task)['status']=='already_closed'
    assert 'cancellation-signal' not in _calls(cancellation_task)


def test_unsubmitted_creation_cannot_request_cancellation(submitted_creation,native_client):
    with pytest.raises(ValueError,match='original recorded submission'):cancel(submitted_creation)
    assert not (_root(submitted_creation)/'ergora/task-cancellations/new-task/stop-one.intent.json').exists()
    assert 'connect' not in _calls(submitted_creation)


@pytest.mark.parametrize('scenario,expected',[
    ('before-intent','not_recorded'),('after-intent','prepared'),('before-attempt','prepared'),
    ('after-attempt','unknown'),('before-result','unknown'),('after-result','requested'),
    ('lost-ack','unknown'),('signal-not-sent','unknown'),
])
def test_interrupted_requests_keep_their_exact_reason_and_do_not_resend_unknown(cancellation_task,cancellation_client,monkeypatch,scenario,expected):
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO',scenario)
    with pytest.raises(ValueError,match='Fixture|timed out'):cancel(cancellation_task)
    current=status(cancellation_task)
    assert current['status']==expected
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','normal')
    if expected=='not_recorded':
        assert 'cancellation-connect' not in _calls(cancellation_task)
        result=cancel(cancellation_task)
    else:
        assert cancel(cancellation_task)==current
        result=resume(cancellation_task)
        assert result['intent_sha256']==current['intent_sha256']
    if scenario in ('after-attempt','signal-not-sent'):
        assert result['status']=='unknown' and result['cancel_requested'] is None
        assert result['reconciliation']=='signal_not_found'
        count=_calls(cancellation_task).count('cancellation-signal')
        assert resume(cancellation_task)['status']=='unknown'
        assert _calls(cancellation_task).count('cancellation-signal')==count
    else:
        assert result['status']=='requested'
        assert _calls(cancellation_task).count('cancellation-signal')==1
    if scenario in ('before-result','lost-ack'):
        assert result['signal_delivery']=='history'


@pytest.mark.parametrize('scenario,error',[
    ('wrong-memo','matching submission memo'),('wrong-spec','original task spec'),
    ('offline','offline'),('not-found','Original cancellation run was not found'),
    ('rpc-unavailable','RPC failed: UNAVAILABLE'),('different-actor','actor changed'),
])
def test_wrong_ownership_or_unavailable_run_does_not_create_an_attempt(cancellation_task,cancellation_client,monkeypatch,scenario,error):
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO',scenario)
    with pytest.raises(ValueError,match=error):cancel(cancellation_task)
    result=status(cancellation_task)
    assert result['status']=='prepared' and not result['attempt_saved']
    assert 'cancellation-signal' not in _calls(cancellation_task)


@pytest.mark.parametrize('scenario',[
    'different-history-operation','same-reason-without-marker','different-history-reason',
    'history-rpc-unavailable','not-found',
])
def test_unknown_recovery_needs_the_exact_operation_marker_not_merely_the_same_reason(cancellation_task,cancellation_client,monkeypatch,scenario):
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','lost-ack')
    with pytest.raises(ValueError):cancel(cancellation_task)
    current=status(cancellation_task)
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO',scenario)
    if scenario in ('not-found','history-rpc-unavailable'):
        with pytest.raises(ValueError):resume(cancellation_task)
    else:
        assert resume(cancellation_task)['status']=='unknown'
    assert status(cancellation_task)==current
    assert _calls(cancellation_task).count('cancellation-signal')==1
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','normal')
    result=resume(cancellation_task)
    assert result['status']=='requested' and result['signal_delivery']=='history'
    assert _calls(cancellation_task).count('cancellation-signal')==1


@pytest.mark.parametrize('options,error',[
    ({'run_id':'other'},'original submitted run'),({'confirm':False},'confirmation'),
])
def test_invalid_inputs_do_not_save_requests(cancellation_task,cancellation_client,options,error):
    before = _files(_root(cancellation_task))
    with pytest.raises(ValueError,match=error):cancel(cancellation_task,**options)
    assert _files(_root(cancellation_task)) == before
    assert status(cancellation_task)['status']=='not_recorded'
    assert 'cancellation-signal' not in _calls(cancellation_task)


@pytest.mark.parametrize('revision',[True,0,'1',2])
def test_revision_rejection_has_no_cancellation_effect(cancellation_task,cancellation_client,revision):
    with pytest.raises(ValueError,match='revision'):cancel(cancellation_task,revision=revision)
    assert status(cancellation_task)['status']=='not_recorded'


def test_existing_request_cannot_change_reason_or_recover_a_different_digest(cancellation_task,cancellation_client):
    cancel(cancellation_task)
    with pytest.raises(ValueError,match='different reason'):cancel(cancellation_task,reason='A new reason')
    with pytest.raises(ValueError,match='exact original request'):
        tasks.resume_cancel(cancellation_task[0],'demo','new-task','stop-one',1,'b'*64,confirm=True)
    assert _calls(cancellation_task).count('cancellation-signal')==1


def test_remote_cancel_wait_does_not_block_other_project_writes(cancellation_task,cancellation_client,monkeypatch):
    state=cancellation_task[0]
    projects.create(state,'other-project',Path(cancellation_task[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(cancel,cancellation_task)
        deadline=time.monotonic()+15
        while 'cancellation-connect' not in _calls(cancellation_task):
            assert time.monotonic()<deadline
            time.sleep(.05)
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},1)['revision']==2
        assert not pending.done()
        with pytest.raises(ValueError,match='temporarily unavailable|locked|would block'):
            cancel(cancellation_task,'stop-two')
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},2)['revision']==3
        assert pending.result(timeout=15)['status']=='requested'
    assert status(cancellation_task,'stop-two')['status']=='not_recorded'


def test_cli_and_api_share_confirmed_commands_and_unknown_history_recovery(cancellation_task,cancellation_client,monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app
    state=cancellation_task[0]
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    uri='/api/projects/demo/tasks/new-task/cancellations/stop-one'
    headers={'X-Ergora-Request':'1','Origin':'http://127.0.0.1'}
    body={'revision':1,'run_id':'original-run','reason':'Owner requested stop','confirm':True}
    assert client.post(uri,json=body).status_code==403
    for invalid in ({'revision':True},{'confirm':1},{'timeout':True},{'reason':'x'*1001}):
        assert client.post(uri,json={**body,**invalid},headers=headers).status_code==422
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','lost-ack')
    assert client.post(uri,json=body,headers=headers).status_code==400
    current=client.get(uri).json()
    assert current['status']=='unknown' and current['cancellation_confirmed'] is None
    args=['--home',str(state.root),'task']
    assert cli.main([*args,'cancel','demo','new-task','--request-id','stop-one','--revision','1',
                     '--run-id','original-run','--reason',body['reason'],'--confirm'])==1
    monkeypatch.setenv('ERGORA_TEST_CANCELLATION_SCENARIO','normal')
    restored=client.post(uri+'/resume',json={'revision':1,'intent_sha256':current['intent_sha256'],'confirm':True},headers=headers)
    assert restored.status_code==200 and restored.json()['status']=='requested'
    assert cli.main([*args,'resume-cancel','demo','new-task','stop-one','--revision','1',
                     '--intent-sha256',current['intent_sha256'],'--confirm'])==0
    assert _calls(cancellation_task).count('cancellation-signal')==1
