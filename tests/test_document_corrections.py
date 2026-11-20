"""Real temporary project files, explicit consent and original operation history."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from ergora.agents import runs
from ergora.configuration import projects
from ergora.definitions import workflows
from ergora.improvement import document_corrections as documents
from ergora.interfaces import cli
from ergora.operations import backups
from ergora.storage.state import State


def git(repo, *arguments):
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    return subprocess.run(['git', '-C', str(repo), '-c', 'core.hooksPath=' + os.devnull,
                           '-c', 'init.templateDir=', '-c', 'user.name=Fixture', '-c',
                           'user.email=fixture@example.invalid', *arguments], check=True,
                          capture_output=True, timeout=10, env=environment).stdout


@pytest.fixture
def project(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init')
    before = b'\xef\xbb\xbf# Project rules\r\nTemporary assumption.\r\n'
    (repo / 'AGENTS.md').write_bytes(before)
    (repo / 'docs').mkdir()
    (repo / 'docs/guide.md').write_bytes(b'# Existing guide\nKeep the useful context.')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'Temporary fixture baseline')
    state = State(tmp_path / 'home-a')
    projects.create(state, 'demo', repo)
    return state, repo, before


def author_manifest(state, directory):
    root = workflows.install_preset(state, 'document-correction')['root']
    definition = workflows.get(state, root['id'], root['version'])['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    return Path(workflows.prepare_manifest(state.root, root['id'], root['version'], grant, directory)['path'])


def prepare(state, directory, *, path='AGENTS.md', parent=None, max_material_bytes=8000):
    return documents.prepare(state, 'demo', path, b'Check the current contract rather than assume one.',
        source='operator-submitted deterministic fixture; no authenticated human or model', revision=state.project('demo')['revision'],
        manifest=author_manifest(state, directory / 'manifest'), instance='root/propose',
        destination=directory / 'input', max_prompt_bytes=100000, max_material_bytes=max_material_bytes,
        parent_preview=parent)


def proposal(state, directory, *, path='AGENTS.md', parent=None, replacement=None, null=False):
    prepared = prepare(state, directory, path=path, parent=parent)
    source = Path(prepared['path'])
    task = json.loads((source / 'task.txt').read_bytes())
    replacement = replacement if replacement is not None else task['baseline']['file']['text'].replace(
        'Temporary assumption.', 'Verify the current contract before changing it.')
    response = {'schema_version': 1, 'request_sha256': task['request_sha256'], 'candidate': None if null else {
        'lesson': 'Verify the currently supported contract.', 'applicability': 'This project only.',
        'replacement_text': replacement}}
    result = directory / 'result.json'
    result.write_text(json.dumps({'summary': 'Deterministic proposal fixture, not a model call.',
                                 'artifacts': {'response': json.dumps(response)}}))
    value = documents.preview(state, 'demo', source, result, revision=task['revision'],
        result_sha256=hashlib.sha256(result.read_bytes()).hexdigest(), input_digest=prepared['digest'])
    return value


def consent(value):
    return {'revision': value['request']['revision'], 'candidate_digest': value['candidate_digest'],
            'base_sha256': value['change']['before']['sha256'], 'scope_sha256': value['scope_sha256'], 'confirm': True}


def saved_preview(value, path):
    path.write_text(json.dumps(value))
    return path


def apply_args(state, path, value):
    return ['--home', str(state.root), 'retrospective', 'apply-document', 'demo', str(path),
            '--revision', str(value['request']['revision']), '--candidate-digest', value['candidate_digest'],
            '--base-sha256', value['change']['before']['sha256'], '--scope-sha256', value['scope_sha256'], '--confirm']


@pytest.mark.skipif(sys.platform != 'linux', reason='Actual local Linux/WSL replacement and directory sync')
def test_cli_readonly_native_substitute_full_preview_and_exact_application(project, tmp_path, monkeypatch, capsys):
    state, repo, before = project
    (repo / 'AGENTS.md').chmod(0o754)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    fake = bin_dir / 'codex'
    fake.write_text(f'#!{sys.executable}\n' + '''import json,pathlib,sys
prompt=sys.stdin.read()
task=json.loads(prompt.rsplit("Operator supplied task (workflow ports have not been executed):\\n",1)[1])
replacement=task['baseline']['file']['text'].replace('Temporary assumption.','Verify the current contract before changing it.')
proposal={'schema_version':1,'request_sha256':task['request_sha256'],'candidate':{'lesson':'Verify current contracts.','applicability':'This project only.','replacement_text':replacement}}
result={'summary':'Controlled deterministic substitute; no provider or model.','artifacts':{'response':json.dumps(proposal)}}
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(result))
print('{}')
''')
    fake.chmod(0o700)
    monkeypatch.setenv('PATH', str(bin_dir) + os.pathsep + os.environ['PATH'])
    user_text = b'Unrelated user edits are preserved.\n'
    (repo / 'docs/guide.md').write_bytes(user_text)
    original_index, original_head = git(repo, 'ls-files', '--stage'), git(repo, 'rev-parse', 'HEAD')
    manifest = author_manifest(state, tmp_path / 'manifest')
    correction = tmp_path / 'correction.txt'
    correction.write_bytes(b'Verify the current contract; keep this as a reusable project lesson.')
    assert cli.main(['--home', str(state.root), 'retrospective', 'prepare-document', 'demo',
        '--document', 'AGENTS.md', '--correction', str(correction), '--source', 'explicit fixture correction',
        '--revision', '1', '--manifest', str(manifest), '--instance', 'root/propose',
        '--directory', str(tmp_path / 'input'), '--max-prompt-bytes', '100000']) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert (repo / 'AGENTS.md').read_bytes() == before
    run = runs.run_input(state, 'demo', tmp_path / 'input', 5, mode='text-only', input_digest=prepared['digest'])
    assert run['status'] == 'succeeded'
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert cli.main(['--home', str(state.root), 'retrospective', 'preview-document', 'demo',
        str(tmp_path / 'input'), str(run['result']), '--revision', '1', '--input-digest', prepared['digest'],
        '--result-sha256', run['result_sha256']]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value['change']['before']['text'].encode() == before
    assert value['change']['after']['text'].encode() == before.replace(b'Temporary assumption.', b'Verify the current contract before changing it.')
    assert '-Temporary assumption.' in value['change']['diff'] and '+Verify the current contract' in value['change']['diff']
    assert not value['origin_authenticated'] and not value['adoption_authorized']
    path = saved_preview(value, tmp_path / 'preview.json')
    assert cli.main(apply_args(state, path, value)[:-1]) == 2
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert cli.main(apply_args(state, path, value)) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['status'] == 'applied'
    assert (repo / 'AGENTS.md').read_bytes() == value['change']['after']['text'].encode()
    assert (repo / 'AGENTS.md').stat().st_mode & 0o777 == value['change']['before']['mode']
    assert cli.main(apply_args(state, path, value)) == 0
    repeated = json.loads(capsys.readouterr().out)
    assert repeated['receipt'] == receipt['receipt'] and repeated['redispatched'] is False
    assert (repo / 'docs/guide.md').read_bytes() == user_text
    assert git(repo, 'ls-files', '--stage') == original_index and git(repo, 'rev-parse', 'HEAD') == original_head
    with state.connect() as db:
        assert db.execute('SELECT count(*) FROM memories').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM skill_heads').fetchone()[0] == 0


@pytest.mark.skipif(sys.platform != 'linux', reason='Exact apply admission supports Linux/WSL')
def test_null_offline_result_and_changed_candidate_cannot_become_consent(project, tmp_path):
    state, repo, before = project
    null = proposal(state, tmp_path / 'null', null=True)
    assert null['candidate_digest'] is None and (repo / 'AGENTS.md').read_bytes() == before
    value = proposal(state, tmp_path / 'candidate')
    changed = deepcopy(value)
    changed['change']['after']['text'] += 'unreviewed rule'
    with pytest.raises(ValueError, match='preview changed'):
        documents.apply(state, 'demo', changed, **consent(value))
    options = consent(value)
    for key in ('candidate_digest', 'base_sha256', 'scope_sha256', 'revision', 'confirm'):
        invalid = {**options, key: 999 if key == 'revision' else False if key == 'confirm' else '0' * 64}
        with pytest.raises(ValueError, match='explicit confirmation'):
            documents.apply(state, 'demo', value, **invalid)
    assert documents.status(state, 'demo', value)['status'] == 'ready'
    assert (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.parametrize('drift', ['bytes', 'head', 'rules', 'mode', 'inode', 'revision'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Apply supports Linux/WSL')
def test_source_drift_preserves_user_changes_and_requires_new_preview(project, tmp_path, drift):
    state, repo, _ = project
    value = proposal(state, tmp_path / 'candidate', path='docs/guide.md')
    target = repo / 'docs/guide.md'
    if drift == 'bytes':
        target.write_bytes(b'User edits must survive.\n')
    elif drift == 'head':
        git(repo, 'commit', '--allow-empty', '-m', 'Independent fixture change')
    elif drift == 'rules':
        (repo / 'docs/AGENTS.md').write_text('A newly added governing rule.\n')
    elif drift == 'mode':
        target.chmod(0o600)
    elif drift == 'inode':
        replacement = repo / 'docs/replacement'
        replacement.write_bytes(target.read_bytes())
        replacement.replace(target)
    else:
        projects.bind(state, 'demo', 'implementer', {'tool': 'codex', 'model': 'gpt-6.1-sol'}, 1)
    current = target.read_bytes()
    with pytest.raises(ValueError, match='changed'):
        documents.apply(state, 'demo', value, **consent(value))
    assert target.read_bytes() == current
    assert documents.status(state, 'demo', value)['attempt'] is None


@pytest.mark.skipif(sys.platform != 'linux', reason='POSIX links and original local application')
def test_paths_budget_and_withdrawn_parent_keep_original_scope(project, tmp_path):
    state, repo, before = project
    (repo / 'linked.md').symlink_to(repo / 'AGENTS.md')
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'rule.md').write_bytes(b'Outside the project; preserve these bytes.\n')
    (repo / 'linked-parent').symlink_to(outside, target_is_directory=True)
    os.link(repo / 'docs/guide.md', repo / 'hardlinked.md')
    for path in ('../outside.md', 'linked.md', 'linked-parent/rule.md', 'hardlinked.md', '.git/config', 'docs'):
        with pytest.raises((ValueError, OSError)):
            prepare(state, tmp_path / path.replace('/', '-'), path=path)
    assert (outside / 'rule.md').read_bytes() == b'Outside the project; preserve these bytes.\n'
    with pytest.raises(ValueError, match='byte limit'):
        prepare(state, tmp_path / 'small', max_material_bytes=60)
    value = proposal(state, tmp_path / 'old')
    assert documents.withdraw(state, 'demo', value, reason='Edit the proposed lesson first.')['status'] == 'withdrawn'
    assert documents.apply(state, 'demo', value, **consent(value))['status'] == 'withdrawn'
    edited = proposal(state, tmp_path / 'edited', parent=value, replacement=before.decode() + 'An explicitly edited lesson.\r\n')
    assert edited['candidate_digest'] != value['candidate_digest']
    assert edited['request']['parent']['candidate_digest'] == value['candidate_digest']
    assert edited['request']['parent']['outcome'] == 'withdrawn'
    assert (repo / 'AGENTS.md').read_bytes() == before


def run_process(arguments, *, code=None):
    command = [sys.executable, '-c', code, *arguments] if code else [sys.executable, '-m', 'ergora', *arguments]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name != 'nt')
    try:
        stdout, stderr = process.communicate(timeout=20)
        return process.returncode, stdout.decode(), stderr.decode()
    finally:
        if process.poll() is None:
            if os.name != 'nt':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize('boundary,expected,changed', [('attempt', 'unknown', False), ('receipt-before', 'unknown', True),
                                                       ('receipt-after', 'applied', True)])
@pytest.mark.skipif(sys.platform != 'linux', reason='Real subprocess crash/replacement on Linux/WSL')
def test_crash_original_history_and_cross_home_refusal(project, tmp_path, boundary, expected, changed):
    state, repo, before = project
    value = proposal(state, tmp_path / 'candidate')
    path = saved_preview(value, tmp_path / 'preview.json')
    code = '''import os,sys
from ergora.improvement import document_corrections as d
from ergora.interfaces import cli
original=d._publish
boundary=sys.argv.pop(1)
def publish(path,value):
    if boundary=='receipt-before' and path.name=='receipt': os._exit(77)
    original(path,value)
    if (boundary=='attempt' and path.name=='attempt') or (boundary=='receipt-after' and path.name=='receipt'): os._exit(77)
d._publish=publish
raise SystemExit(cli.main(sys.argv[1:]))
'''
    result = run_process([boundary, *apply_args(state, path, value)], code=code)
    assert result[0] == 77
    observed = documents.status(state, 'demo', value)
    assert observed['status'] == expected and observed['attempt'] is not None
    assert ((repo / 'AGENTS.md').read_bytes() != before) is changed
    assert documents.apply(state, 'demo', value, **consent(value))['status'] == expected
    other = State(tmp_path / 'home-b')
    projects.create(other, 'demo', repo)
    for action in (lambda: documents.apply(other, 'demo', value, **consent(value)),
                   lambda: documents.status(other, 'demo', value),
                   lambda: documents.withdraw(other, 'demo', value, reason='Cannot relocate consent.')):
        with pytest.raises(ValueError, match='control authority changed'):
            action()
    assert not (other.root / 'retrospectives').exists()
    assert documents.status(state, 'demo', value) == observed
    if not changed:
        child = proposal(other, tmp_path / 'new-b', parent=value, replacement=before.decode() + 'A new proposal only.\r\n')
        assert child['request']['parent']['authority'] == value['request']['authority']
        assert child['request']['parent']['outcome'] == 'unknown'
        assert child['candidate_digest'] != value['candidate_digest']
        assert (repo / 'AGENTS.md').read_bytes() == before
        staged = repo / observed['decision']['staged']
        assert [staged.stat().st_dev, staged.stat().st_ino] == observed['decision']['stage_identity']
        staged.unlink()  # only this crashed fixture's captured original staged inode


@pytest.mark.skipif(sys.platform != 'linux', reason='Exact apply admission supports Linux/WSL')
def test_withdrawal_wrong_home_and_missing_original_history_never_reopen_slot(project, tmp_path):
    state, repo, before = project
    value = proposal(state, tmp_path / 'candidate')
    documents.withdraw(state, 'demo', value, reason='Declined exact candidate.')
    other = State(tmp_path / 'home-b')
    projects.create(other, 'demo', repo)
    with pytest.raises(ValueError, match='control authority changed'):
        documents.apply(other, 'demo', value, **consent(value))
    slot = state.root / 'retrospectives/documents/demo' / value['request']['proposal_id']
    (slot / 'record.json').rename(slot / 'preserved-record.json')
    with pytest.raises(FileNotFoundError):
        documents.apply(state, 'demo', value, **consent(value))
    assert not (slot / 'record.json').exists() and (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.skipif(sys.platform != 'linux', reason='Final source admission and replacement on Linux/WSL')
def test_drift_after_durable_attempt_is_consumed_without_overwriting_user_bytes(project, tmp_path, monkeypatch):
    state, repo, _ = project
    value = proposal(state, tmp_path / 'candidate')
    original = documents._publish

    def publish(path, record):
        original(path, record)
        if path.name == 'attempt':
            (repo / 'AGENTS.md').write_bytes(b'Concurrent user correction at final admission.\n')

    monkeypatch.setattr(documents, '_publish', publish)
    with pytest.raises(ValueError, match='changed'):
        documents.apply(state, 'demo', value, **consent(value))
    observed = documents.status(state, 'demo', value)
    assert observed['status'] == 'unknown' and observed['attempt'] is not None
    assert (repo / 'AGENTS.md').read_bytes() == b'Concurrent user correction at final admission.\n'
    assert documents.apply(state, 'demo', value, **consent(value))['redispatched'] is False


@pytest.mark.skipif(sys.platform != 'linux', reason='Original authority and backup/restore identities on Linux/WSL')
def test_restored_home_preserves_history_but_cannot_consume_old_preview(project, tmp_path):
    state, repo, before = project
    value = proposal(state, tmp_path / 'candidate')
    documents.withdraw(state, 'demo', value, reason='Original terminal decision.')
    backup = tmp_path / 'backup'
    backups.create(state.root, backup, offline=True)
    state.root.rename(tmp_path / 'retained-original-home')
    backups.restore(state.root, backup, offline=True)
    restored = State(state.root)
    for action in (lambda: documents.status(restored, 'demo', value),
                   lambda: documents.apply(restored, 'demo', value, **consent(value))):
        with pytest.raises(ValueError, match='control authority changed'):
            action()
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert documents.read_preview(saved_preview(value, tmp_path / 'old-preview.json')) == value


def test_offline_preview_and_history_survive_unavailable_apply(project, tmp_path, monkeypatch):
    state, _, _ = project
    value = proposal(state, tmp_path / 'candidate')
    monkeypatch.setattr(documents.sys, 'platform', 'unsupported-fixture')
    inspected = documents.check(Path(value['source']['input']), Path(value['source']['result']),
        result_sha256=value['result_sha256'], input_digest=value['input_digest'])
    assert inspected['change'] == value['change'] and inspected['apply']['available'] is False
    assert documents.status(state, 'demo', value)['status'] == 'ready'
    with pytest.raises(ValueError, match='Linux/WSL'):
        documents.apply(state, 'demo', value, **consent(value))


@pytest.mark.skipif(sys.platform != 'linux', reason='Exact apply source admission supports Linux/WSL')
def test_changed_original_result_cannot_apply_a_previously_sealed_preview(project, tmp_path):
    state, repo, before = project
    value = proposal(state, tmp_path / 'candidate')
    Path(value['source']['result']).write_text('{}')
    with pytest.raises(ValueError, match='original bytes'):
        documents.apply(state, 'demo', value, **consent(value))
    assert documents.status(state, 'demo', value)['status'] == 'ready'
    assert (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.parametrize('missing', ['decision', 'consumption'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Original consumed-slot admission on Linux/WSL')
def test_lost_terminal_history_never_reopens_the_original_candidate(project, tmp_path, missing):
    state, repo, before = project
    value = proposal(state, tmp_path / 'candidate')
    original = documents.withdraw(state, 'demo', value, reason='Keep this original decision terminal.')
    slot = state.root / 'retrospectives/documents/demo' / value['request']['proposal_id']
    (slot / missing).rename(tmp_path / ('preserved-' + missing))
    if missing == 'decision':
        observed = documents.status(state, 'demo', value)
        assert observed['status'] == 'unknown'
        assert observed['consumption'] == original['consumption']
        assert documents.apply(state, 'demo', value, **consent(value))['redispatched'] is False
    else:
        with pytest.raises(FileNotFoundError):
            documents.status(state, 'demo', value)
        with pytest.raises(FileNotFoundError):
            documents.apply(state, 'demo', value, **consent(value))
    assert not (slot / missing).exists()
    assert (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.skipif(sys.platform != 'linux', reason='Final direct-parent lineage admission on Linux/WSL')
def test_child_refuses_new_unknown_parent_and_fresh_unknown_supersession_is_explicit(project, tmp_path, monkeypatch):
    state, repo, before = project
    parent = proposal(state, tmp_path / 'parent')
    child = proposal(state, tmp_path / 'child', parent=parent)
    assert child['request']['parent']['outcome'] == 'ready'
    original = documents._publish

    def interrupted(path, record):
        original(path, record)
        if path.name == 'attempt' and path.parent.name == parent['request']['proposal_id']:
            raise RuntimeError('Original parent attempt is durable; replacement did not start.')

    with monkeypatch.context() as context:
        context.setattr(documents, '_publish', interrupted)
        with pytest.raises(RuntimeError, match='durable'):
            documents.apply(state, 'demo', parent, **consent(parent))
    assert documents.status(state, 'demo', parent)['status'] == 'unknown'
    with pytest.raises(ValueError, match='Parent document lineage changed'):
        documents.apply(state, 'demo', child, **consent(child))
    assert documents.status(state, 'demo', child)['attempt'] is None
    assert (repo / 'AGENTS.md').read_bytes() == before
    fresh = proposal(state, tmp_path / 'fresh', parent=parent)
    assert fresh['request']['parent']['outcome'] == 'unknown'
    assert fresh['request']['parent']['observation_sha256'] != child['request']['parent']['observation_sha256']
    assert documents.apply(state, 'demo', fresh, **consent(fresh))['status'] == 'applied'
    assert documents.status(state, 'demo', parent)['status'] == 'unknown'


def wait_marker(path, processes):
    deadline = time.monotonic() + 8
    while not path.exists():
        if time.monotonic() >= deadline or any(process.poll() is not None for process in processes):
            raise AssertionError('Owned synchronization marker did not arrive before its deadline')
        time.sleep(.02)


@pytest.mark.skipif(sys.platform != 'linux', reason='Real parent-withdraw/child-apply locking on Linux/WSL')
def test_parent_withdraw_cannot_cross_child_final_admission(project, tmp_path):
    state, _, _ = project
    parent = proposal(state, tmp_path / 'parent')
    child = proposal(state, tmp_path / 'child', parent=parent)
    parent_path = saved_preview(parent, tmp_path / 'parent.json')
    child_path = saved_preview(child, tmp_path / 'child.json')
    gate, resume = tmp_path / 'at-replace', tmp_path / 'resume'
    entering, acquired = tmp_path / 'parent-entering-lock', tmp_path / 'parent-acquired-lock'
    child_code = '''import pathlib,sys,time
from ergora.improvement import document_corrections as d
from ergora.interfaces import cli
gate,resume=map(pathlib.Path,sys.argv[1:3]);original=d.os.replace
def replace(source,target,*args,**kwargs):
    if str(target)=='AGENTS.md':
        gate.write_text('final replacement reached')
        deadline=time.monotonic()+8
        while not resume.exists():
            if time.monotonic()>deadline:raise RuntimeError('owned gate timed out')
            time.sleep(.02)
    return original(source,target,*args,**kwargs)
d.os.replace=replace
raise SystemExit(cli.main(sys.argv[3:]))
'''
    parent_code = '''from contextlib import contextmanager
import pathlib,sys
from ergora.improvement import document_corrections as d
from ergora.interfaces import cli
entering,acquired=map(pathlib.Path,sys.argv[1:3]);original=d.file_lock
@contextmanager
def lock(path,*args,**kwargs):
    entering.write_text('original parent lock requested')
    with original(path,*args,**kwargs) as held:
        acquired.write_text('original parent lock acquired')
        yield held
d.file_lock=lock
raise SystemExit(cli.main(sys.argv[3:]))
'''
    processes = []
    try:
        processes.append(subprocess.Popen([sys.executable, '-c', child_code, str(gate), str(resume),
            *apply_args(state, child_path, child)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True))
        wait_marker(gate, processes)
        processes.append(subprocess.Popen([sys.executable, '-c', parent_code, str(entering), str(acquired),
            '--home', str(state.root), 'retrospective', 'withdraw-document', 'demo', str(parent_path),
            '--reason', 'Cooperating parent decision.'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True))
        wait_marker(entering, processes)
        assert not acquired.exists()
        resume.write_text('continue exact child replacement')
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            assert process.returncode == 0, (stdout, stderr)
        assert acquired.exists()
    finally:
        resume.touch(exist_ok=True)
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
    assert documents.status(state, 'demo', parent)['status'] == 'withdrawn'
    assert documents.status(state, 'demo', child)['status'] == 'applied'


@pytest.mark.skipif(sys.platform != 'linux', reason='Real cooperating process writers on Linux/WSL')
def test_two_control_homes_serialize_at_one_repository_and_reject_stale_second_writer(project, tmp_path):
    state, repo, _ = project
    other = State(tmp_path / 'home-b')
    projects.create(other, 'demo', repo)
    first = proposal(state, tmp_path / 'first', replacement='# First explicitly confirmed lesson\n')
    second = proposal(other, tmp_path / 'second', replacement='# Second explicitly confirmed lesson\n')
    paths = [saved_preview(first, tmp_path / 'first.json'), saved_preview(second, tmp_path / 'second.json')]
    processes = [subprocess.Popen([sys.executable, '-m', 'ergora', *apply_args(home, path, value)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                 for home, path, value in [(state, paths[0], first), (other, paths[1], second)]]
    outcomes = []
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            outcomes.append((process.returncode, stdout, stderr))
    finally:
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
    assert sorted(code for code, _, _ in outcomes) == [0, 2]
    assert (repo / 'AGENTS.md').read_text() in [first['change']['after']['text'], second['change']['after']['text']]
    assert sorted([documents.status(state, 'demo', first)['status'], documents.status(other, 'demo', second)['status']]) == ['applied', 'ready']
