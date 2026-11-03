"""Only local intent preparation may reserve the shared control database."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time

import pytest

from ergora import projects, reference, tasks
from ergora.state import file_lock
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_task_submission import submitted_creation, native_client, _start, _root, _calls, _status, _resume


def test_connection_environment_is_not_loaded_until_after_the_intent_is_saved(submitted_creation,native_client,monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','environment-blocked')
    with pytest.raises(ValueError,match='connection environment denied'):_start(submitted_creation)
    prepared=_status(submitted_creation)
    assert prepared['status']=='prepared' and not prepared['attempt_saved']
    assert _calls(submitted_creation)==[]
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','normal')
    assert _start(submitted_creation)==prepared
    assert _calls(submitted_creation)==[]
    assert _resume(submitted_creation)['status']=='submitted'
    assert _calls(submitted_creation).count('start')==1


def test_parent_interruption_after_prepare_keeps_a_resumable_intent_without_admission(submitted_creation,native_client,monkeypatch):
    original=reference.task_submission
    def interrupted(project,home,operation,payload,**kwargs):
        if operation=='dispatch':raise ValueError('Fixture parent interrupted before dispatch')
        return original(project,home,operation,payload,**kwargs)
    monkeypatch.setattr(reference,'task_submission',interrupted)
    with pytest.raises(ValueError,match='parent interrupted'):_start(submitted_creation)
    prepared=_status(submitted_creation)
    assert prepared['status']=='prepared' and _calls(submitted_creation)==[]
    monkeypatch.setattr(reference,'task_submission',original)
    assert _start(submitted_creation)==prepared
    result=_resume(submitted_creation)
    assert result['status']=='submitted' and result['intent_sha256']==prepared['intent_sha256']
    assert _calls(submitted_creation).count('start')==1


def test_revision_changes_between_prepare_and_dispatch_keep_the_authorized_snapshot(submitted_creation,native_client,monkeypatch):
    state=submitted_creation[0]
    original=reference.task_submission
    snapshots=[]
    def change_revision(project,home,operation,payload,**kwargs):
        if operation=='dispatch':
            snapshots.append(project['revision'])
            assert projects.bind(state,'demo','reviewer',{'tool':'codex','model':'later-model'},1)['revision']==2
        return original(project,home,operation,payload,**kwargs)
    monkeypatch.setattr(reference,'task_submission',change_revision)
    before=(_root(submitted_creation)/'tasks/new-task/agent-bindings.json').read_bytes()
    result=_start(submitted_creation)
    assert snapshots==[1] and result['status']=='submitted' and result['submitted_revision']==1
    assert result['project_revision']==1  # Snapshot used for this operation, not a fresh control query.
    assert state.project('demo')['revision']==2
    assert (_root(submitted_creation)/'tasks/new-task/agent-bindings.json').read_bytes()==before
    intent=json.loads((_root(submitted_creation)/'ergora/task-submissions/new-task.intent.json').read_text())
    assert intent['project_revision']==1
    assert tasks.start(state,'demo','new-task',2,submitted_creation[3]['intent_sha256'])['run_id']==result['run_id']
    assert _calls(submitted_creation).count('start')==1


def test_remote_submission_holds_only_the_task_lock_and_other_projects_can_write(submitted_creation,native_client,monkeypatch):
    state=submitted_creation[0]
    projects.create(state,'other-project',Path(submitted_creation[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO','slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(_start,submitted_creation)
        deadline=time.monotonic()+15
        while 'connect' not in _calls(submitted_creation):
            assert time.monotonic()<deadline
            time.sleep(.05)
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},1)['revision']==2
        assert not pending.done(), 'Other project writer waited for remote submission'
        with pytest.raises(ValueError,match='temporarily unavailable|locked|would block'):_start(submitted_creation)
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},2)['revision']==3
        assert pending.result(timeout=15)['status']=='submitted'
    assert _calls(submitted_creation).count('start')==1
    assert _calls(submitted_creation).count('doctor')==1


@pytest.mark.parametrize('operation',['create','resume-create'])
def test_publication_does_not_wait_on_a_remote_task_lock_while_reserving_the_database(submitted_creation,native_client,operation):
    state,registration,definition,created=submitted_creation
    root=_root(submitted_creation)
    projects.create(state,'other-project',Path(registration['repo']))
    before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with file_lock(root/'ergora/task-creations/new-task.lock'):
        with pytest.raises(ValueError,match='temporarily unavailable|locked|would block'):
            if operation=='create':
                tasks.create(state,'demo',definition,1,created['intent_sha256'])
            else:
                tasks.resume_create(state,'demo','new-task',1,created['intent_sha256'])
        assert projects.bind(state,'other-project','memory',{'tool':'sqlite'},1)['revision']==2
    assert {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}==before
    assert _calls(submitted_creation)==[]
