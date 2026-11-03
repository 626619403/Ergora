"""Owner decisions preserve exact run/plan identity and never resend uncertain signals."""

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
def approval_task(submitted_creation,native_client):
    _start(submitted_creation)
    return submitted_creation


@pytest.fixture
def approval_client(approval_task,monkeypatch):
    original=reference.subprocess.run
    fixture=Path(__file__).parent/'fixtures/task_approval_client.py'
    def invoke(argv,**kwargs):
        if 'from ergora.reference_task_approval import main;main()' in argv:
            argv=[*argv[:-1],fixture.read_text(encoding='utf-8')]
        return original(argv,**kwargs)
    monkeypatch.setattr(reference.subprocess,'run',invoke)


def approve(creation,decision='owner-one',revision=1,**kwargs):
    return tasks.approve(creation[0],'demo','new-task',decision,revision,
                         **{'run_id':'original-run','plan_sha256':'a'*64,'confirm':True,**kwargs})


def status(creation,decision='owner-one'):
    return tasks.approval(State(creation[0].root),'demo','new-task',decision)


def resume(creation,decision='owner-one',revision=1,**kwargs):
    current=status(creation,decision)
    return tasks.resume_approve(State(creation[0].root),'demo','new-task',decision,revision,
                                current['intent_sha256'],confirm=True,**kwargs)


def test_exact_owner_approval_is_only_requested_and_repeated_commands_never_signal_again(approval_task,approval_client):
    assert status(approval_task)['status']=='not_recorded'
    result=approve(approval_task)
    assert result['status']=='requested' and result['run_id']=='original-run'
    assert result['approval_accepted'] is None and result['execution_success'] is None
    assert result['owner_receipt_saved'] and result['attempt_saved'] and result['result_saved']
    assert result['signal_delivery']=='acknowledged'
    assert approve(approval_task)==resume(approval_task)==status(approval_task)==result
    assert _calls(approval_task).count('approval-signal')==1
    assert _calls(approval_task).count('approval-query')==1
    root=_root(approval_task)
    receipt=json.loads((root/'approvals'/(result['owner_receipt_id']+'.json')).read_text())
    assert receipt['principal_type']=='human' and receipt['role']=='owner' and receipt['revoked'] is False
    assert receipt['plan_sha256']=='a'*64
    projects.bind(approval_task[0],'demo','reviewer',{'tool':'codex','model':'later-model'},1)
    assert resume(approval_task,revision=2)['owner_receipt_id']==result['owner_receipt_id']
    assert _calls(approval_task).count('approval-signal')==1


@pytest.mark.parametrize('scenario,expected',[
    ('before-intent','not_recorded'),('after-intent','prepared'),('before-publish','prepared'),
    ('after-publish','prepared'),('before-attempt','prepared'),('after-attempt','unknown'),
    ('before-result','unknown'),('after-result','requested'),('lost-ack','unknown'),('signal-not-sent','unknown'),
])
def test_each_interruption_keeps_original_owner_receipt_and_never_resends_unknown(approval_task,approval_client,monkeypatch,scenario,expected):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO',scenario)
    with pytest.raises(ValueError,match='Fixture|timed out'):
        approve(approval_task)
    current=status(approval_task)
    assert current['status']==expected
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    if expected=='not_recorded':
        assert 'approval-connect' not in _calls(approval_task)
        result=approve(approval_task)
    else:
        old_receipt=current['owner_receipt_id']
        assert approve(approval_task)['status']==expected  # same command never retries preparation
        result=resume(approval_task)
        assert result['owner_receipt_id']==old_receipt
    if scenario in ('after-attempt','signal-not-sent'):
        assert result['status']=='unknown' and result['reconciliation']=='signal_not_found'
        count=_calls(approval_task).count('approval-signal')
        assert resume(approval_task)['status']=='unknown'
        assert _calls(approval_task).count('approval-signal')==count
    else:
        assert result['status']=='requested'
        assert _calls(approval_task).count('approval-signal')==1
    if scenario in ('before-result','lost-ack'):
        assert result['signal_delivery']=='history'


@pytest.mark.parametrize('scenario,error',[
    ('old-plan','exact plan'),('already-working','exact plan'),('wrong-memo','matching submission memo'),
    ('offline','offline'),('different-actor','owner identity changed'),
    ('not-found','Original approval run was not found'),
])
def test_wrong_plan_or_run_ownership_is_rejected_before_owner_receipt_or_signal(approval_task,approval_client,monkeypatch,scenario,error):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO',scenario)
    with pytest.raises(ValueError,match=error):
        approve(approval_task)
    assert status(approval_task)['status']=='prepared'
    assert not status(approval_task)['owner_receipt_saved']
    assert 'approval-signal' not in _calls(approval_task)


def test_expired_decision_is_never_renewed_and_new_decision_requires_new_id(approval_task,approval_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','expired')
    with pytest.raises(ValueError,match='expired'):
        approve(approval_task)
    expired=status(approval_task)
    assert expired['expires_at']<time.time() and expired['status']=='prepared'
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    assert approve(approval_task)==expired
    with pytest.raises(ValueError,match='expired'):
        resume(approval_task)
    result=approve(approval_task,'owner-two')
    assert result['status']=='requested' and result['owner_receipt_id']!=expired['owner_receipt_id']
    assert status(approval_task)==expired
    assert _calls(approval_task).count('approval-signal')==1


def test_signal_ack_does_not_claim_the_workflow_accepted_a_racing_decision(approval_task,approval_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','phase-race')
    result=approve(approval_task)
    assert result['status']=='requested' and result['approval_accepted'] is None
    assert json.loads((_root(approval_task)/'sdk-fixture/approval-handler.json').read_text())['pending'] is None


def test_reconciliation_requires_the_exact_original_signal_receipt(approval_task,approval_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','lost-ack')
    with pytest.raises(ValueError):approve(approval_task)
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','different-history-signal')
    assert resume(approval_task)['status']=='unknown'
    assert _calls(approval_task).count('approval-signal')==1
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    assert resume(approval_task)['status']=='requested'
    assert _calls(approval_task).count('approval-signal')==1


def test_missing_original_run_during_unknown_recovery_never_resends(approval_task,approval_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','lost-ack')
    with pytest.raises(ValueError):approve(approval_task)
    original=status(approval_task)
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','not-found')
    with pytest.raises(ValueError,match='Original approval run was not found'):resume(approval_task)
    assert status(approval_task)==original
    assert _calls(approval_task).count('approval-signal')==1
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    assert resume(approval_task)['status']=='requested'
    assert _calls(approval_task).count('approval-signal')==1


@pytest.mark.parametrize('options,error',[
    ({'run_id':'other-run'},'original submitted run'),({'confirm':False},'confirmation'),
])
def test_invalid_decision_inputs_do_not_save_owner_intents(approval_task,approval_client,options,error):
    before = _files(_root(approval_task))
    with pytest.raises(ValueError,match=error):approve(approval_task,**options)
    assert _files(_root(approval_task)) == before
    assert status(approval_task)['status']=='not_recorded'
    assert 'approval-signal' not in _calls(approval_task)


@pytest.mark.parametrize('revision',[True,0,'1',2])
def test_stale_revisions_have_no_approval_effect(approval_task,approval_client,revision):
    with pytest.raises(ValueError,match='revision'):approve(approval_task,revision=revision)
    assert status(approval_task)['status']=='not_recorded'


def test_same_decision_id_cannot_change_plan_and_owner_receipt_drift_blocks_resume(approval_task,approval_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','after-publish')
    with pytest.raises(ValueError):approve(approval_task)
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    original=status(approval_task)
    with pytest.raises(ValueError,match='different plan'):approve(approval_task,plan_sha256='b'*64)
    path=_root(approval_task)/'approvals'/(original['owner_receipt_id']+'.json')
    value=json.loads(path.read_text());value['revoked']=True;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='owner receipt conflicts'):status(approval_task)
    with pytest.raises(ValueError,match='owner receipt conflicts'):
        tasks.resume_approve(approval_task[0],'demo','new-task','owner-one',1,original['intent_sha256'],confirm=True)
    assert 'approval-signal' not in _calls(approval_task)


def test_remote_wait_leaves_other_project_writes_available_and_busy_task_prepare_does_not_wait(approval_task,approval_client,monkeypatch):
    state=approval_task[0]
    projects.create(state,'other-project',Path(approval_task[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(approve,approval_task)
        deadline=time.monotonic()+15
        while 'approval-connect' not in _calls(approval_task):
            assert time.monotonic()<deadline
            time.sleep(.05)
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},1)['revision']==2
        assert not pending.done(), 'A different project write waited for remote completion'
        with pytest.raises(ValueError,match='temporarily unavailable|locked|would block'):
            approve(approval_task,'owner-two')
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},2)['revision']==3
        assert pending.result(timeout=15)['status']=='requested'
    assert status(approval_task,'owner-two')['status']=='not_recorded'
    assert _calls(approval_task).count('approval-signal')==1


def test_cli_and_api_use_the_same_explicit_decision_and_recovery(approval_task,approval_client,monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app
    state=approval_task[0]
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    uri='/api/projects/demo/tasks/new-task/approvals/owner-one'
    headers={'X-Ergora-Request':'1','Origin':'http://127.0.0.1'}
    body={'revision':1,'run_id':'original-run','plan_sha256':'a'*64,'confirm':True}
    assert client.post(uri,json=body).status_code==403
    for invalid in ({'revision':True},{'confirm':1},{'timeout':True},{'timeout':61}):
        assert client.post(uri,json={**body,**invalid},headers=headers).status_code==422
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','lost-ack')
    assert client.post(uri,json=body,headers=headers).status_code==400
    current=client.get(uri).json()
    assert current['status']=='unknown'
    args=['--home',str(state.root),'task']
    assert cli.main([*args,'approve','demo','new-task','--decision-id','owner-one','--revision','1',
                     '--run-id','original-run','--plan-sha256','a'*64,'--confirm'])==1
    monkeypatch.setenv('ERGORA_TEST_APPROVAL_SCENARIO','normal')
    restored=client.post(uri+'/resume',json={'revision':1,'intent_sha256':current['intent_sha256'],'confirm':True},headers=headers)
    assert restored.status_code==200 and restored.json()['status']=='requested'
    assert cli.main([*args,'resume-approve','demo','new-task','owner-one','--revision','1',
                     '--intent-sha256',current['intent_sha256'],'--confirm'])==0
    assert client.get(uri).json()==status(approval_task)
    assert _calls(approval_task).count('approval-signal')==1
