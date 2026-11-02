"""Formal task reads preserve native contracts and never infer runtime success."""

import hashlib
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
def task_store(registration, tmp_path):
    state, definition = registration
    registrations.register(state, definition, 0)
    execution = definition['execution']
    inputs = {'goal': 'A controlled task', 'allowed_paths': ['src'], 'acceptance': ['Preserve the contract'],
              'constraints': [], 'risk': 'standard',
              'work_units': [{'id': 'one', 'depends_on': [], 'paths': ['src'], 'instructions': 'Inspect source'}]}
    input_file = tmp_path / 'input.json'
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'],
                       PYTHONPATH=os.pathsep.join([str(Path(reference.__file__).parent.parent),
                           *(str(reference.ROOT / 'platform' / p) for p in ('local', 'upstream/platform'))]))
    for task_id, template in [('first', 'repository-governance'), ('second', 'large-change')]:
        inputs['risk'] = 'high' if template == 'large-change' else 'standard'
        input_file.write_text(json.dumps(inputs), encoding='utf-8')
        result = subprocess.run([sys.executable, '-P', '-S', '-c',
            '''import os, sys
from pathlib import Path
from dev_platform import adapter, portable
if os.name == 'nt':
    from ergora.reference import _read_windows_contract
    portable._read_bytes = _read_windows_contract
    adapter.read_raw = _read_windows_contract
from agent_platform.projects import create_task
create_task("demo", sys.argv[1], sys.argv[2], "1", Path(sys.argv[3]))
''',
            template, task_id, str(input_file)], env=environment, capture_output=True, text=True, encoding='utf-8', timeout=20)
        assert result.returncode == 0, result.stderr
    return state, Path(execution['state_directory']) / 'tasks'


def test_offline_list_and_detail_preserve_native_files_and_project(task_store):
    state, folder = task_store
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
    project = state.project('demo')
    listing = tasks.listing(state, 'demo')
    assert [item['task_id'] for item in listing['items']] == ['first', 'second']
    assert listing['next_after'] is None and listing['runtime_status'] == 'not_queried'
    for task_id, template in [('first', 'repository-governance'), ('second', 'large-change')]:
        item = tasks.show(state, 'demo', task_id)
        assert item['task_type'] == template and item['runtime_status'] == 'not_queried'
        assert item['spec'] == json.loads((folder / task_id / 'task.spec.json').read_text())
        assert item['request_sha256'] == item['spec']['request_sha256']
        assert item['agent_bindings'] is None
        assert 'status' not in item and 'phase' not in item
    assert state.project('demo') == project
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before} == before


def test_list_pagination_uses_bounded_inspected_directory_windows(task_store):
    state, _ = task_store
    first = tasks.listing(state, 'demo', limit=1)
    assert [item['task_id'] for item in first['items']] == ['first'] and isinstance(first['next_after'], str)
    second = tasks.listing(state, 'demo', limit=1, after=first['next_after'])
    assert [item['task_id'] for item in second['items']] == ['second'] and second['next_after'] is None


def test_other_projects_are_excluded_and_direct_access_is_rejected(task_store):
    state, folder = task_store
    path = folder / 'first/project.json'
    data = json.loads(path.read_text());data['name'] = 'other'
    path.write_text(json.dumps(data))
    listing = tasks.listing(state, 'demo')
    assert [item['task_id'] for item in listing['items']] == ['second'] and not listing['errors']
    with pytest.raises(ValueError, match='belong'):
        tasks.show(state, 'demo', 'first')


@pytest.mark.parametrize('mutation,error', [
    ('digest', 'hash mismatch'), ('identifier', 'directory'), ('tracker', 'tracker'),
    ('oversized', 'size limit'), ('malformed', 'JSON'), ('baseline', 'baseline'),
])
def test_invalid_owned_tasks_fail_visibly_without_hiding_other_tasks(task_store, mutation, error):
    state, folder = task_store
    path = folder / 'first/task.spec.json'
    document = json.loads(path.read_text())
    if mutation == 'digest':
        document['request']['input']['goal'] = 'changed';path.write_text(json.dumps(document))
    elif mutation == 'identifier':
        second = json.loads((folder / 'second/task.spec.json').read_text())
        path.write_text(json.dumps(second))
    elif mutation == 'tracker':
        project = folder / 'first/project.json';data=json.loads(project.read_text())
        data['tracker']['project']='local/other';project.write_text(json.dumps(data))
    elif mutation == 'baseline':
        project = folder / 'first/project.json';data=json.loads(project.read_text())
        data['base_sha']='0'*40;project.write_text(json.dumps(data))
    elif mutation == 'oversized':
        path.write_bytes(b' ' * (1_048_576 + 1))
    else:
        path.write_text('{')
    with pytest.raises(ValueError, match=error):
        tasks.show(state, 'demo', 'first')
    listing = tasks.listing(state, 'demo')
    assert [item['task_id'] for item in listing['items']] == ['second']
    assert listing['errors'][0]['task_id'] == 'first'


@pytest.mark.parametrize('raw', ['{', '{}', 'null', '[]'])
def test_unowned_unreadable_entries_are_counted_without_publishing_contents(task_store, raw):
    state, folder = task_store
    (folder / 'first/project.json').write_text(raw)
    listing = tasks.listing(state, 'demo')
    assert listing['unreadable_count'] == 1 and not listing['errors']
    assert [item['task_id'] for item in listing['items']] == ['second']


@pytest.mark.skipif(os.name == 'nt', reason='POSIX no-follow/FIFO fixtures')
def test_symlink_and_fifo_contracts_are_rejected_without_blocking(task_store):
    state, folder = task_store
    path = folder / 'first/task.spec.json';stored=path.with_suffix('.saved')
    path.rename(stored);path.symlink_to(stored)
    with pytest.raises(ValueError, match='[Ss]ymlink'):
        tasks.show(state, 'demo', 'first')
    path.unlink();os.mkfifo(path)
    with pytest.raises(ValueError, match='regular file'):
        tasks.show(state, 'demo', 'first')


def test_snapshot_is_bounded_and_records_its_frozen_revision(task_store):
    state, folder = task_store
    snapshot = {'schema_version': 1, 'reference_project': 'demo', 'project_revision': 1, 'bindings': {}}
    path=folder/'first/agent-bindings.json';path.write_text(json.dumps(snapshot))
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, 1)
    item=tasks.show(state, 'demo', 'first')
    assert item['project_revision'] == 2 and item['agent_bindings'] == snapshot
    snapshot['reference_project']='other';path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match='snapshot project'):
        tasks.show(state, 'demo', 'first')


@pytest.mark.parametrize('options', [{'limit':0}, {'limit':101}, {'limit':True}, {'after':'../first'}])
def test_invalid_page_options_are_rejected_before_read(task_store, options):
    state, _ = task_store
    with pytest.raises(ValueError):
        tasks.listing(state, 'demo', **options)


def test_lightweight_and_pending_projects_have_no_formal_task_store(task_store):
    state, _ = task_store
    projects.create(state, 'light', Path(state.project('demo')['repo']))
    with pytest.raises(ValueError, match='published'):
        tasks.listing(state, 'light')
    with pytest.raises(ValueError, match='Invalid identifier'):
        tasks.show(state, 'demo', '../first')
    project = state.project('demo')
    project['registration']['status'] = 'pending'
    with state.connect() as db:
        db.execute('UPDATE projects SET document=? WHERE id=?', (json.dumps(project), 'demo'))
    with pytest.raises(ValueError, match='published'):
        tasks.show(state, 'demo', 'first')


def test_cli_and_api_read_the_same_contracts(task_store):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    state, _ = task_store
    client=TestClient(create_app(state.root),base_url='http://127.0.0.1')
    uri='/api/projects/demo/tasks'
    assert client.get(uri).json()==tasks.listing(state,'demo')
    assert client.get(uri+'/first').json()==tasks.show(state,'demo','first')
    for arguments,expected in [(['list','demo'],tasks.listing(state,'demo')),(['show','demo','first'],tasks.show(state,'demo','first'))]:
        result=subprocess.run([sys.executable,'-m','ergora','--home',str(state.root),'task',*arguments],capture_output=True,text=True,encoding='utf-8',timeout=20)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)==expected


@pytest.mark.parametrize('directory', ['bad.id', 'bad\\id'])
def test_cursor_advances_across_invalid_native_directory_names(task_store, directory):
    state, folder = task_store
    # Backslashes are legal filenames on POSIX; the cursor is never a path.
    if os.name == 'nt' and '\\' in directory:
        pytest.skip('Windows forbids backslashes in directory names')
    (folder / directory).mkdir()
    first = tasks.listing(state, 'demo', limit=1)
    assert first['items'] == [] and first['unreadable_count'] == 1 and isinstance(first['next_after'], str)
    second = tasks.listing(state, 'demo', limit=1, after=first['next_after'])
    assert [item['task_id'] for item in second['items']] == ['first']


@pytest.mark.skipif(os.name == 'nt', reason='POSIX non-UTF-8 filename fixture')
def test_opaque_cursor_roundtrips_non_utf8_native_names(task_store):
    state, folder = task_store
    (folder / os.fsdecode(b'a\xff')).mkdir()
    page = tasks.listing(state, 'demo', limit=1)
    assert page['items'] == [] and page['unreadable_count'] == 1
    assert page['next_after'].isascii()
    next_page = tasks.listing(state, 'demo', limit=1, after=page['next_after'])
    assert [item['task_id'] for item in next_page['items']] == ['first']


@pytest.mark.parametrize('failure', ['timeout', 'empty-stderr'])
def test_reader_failures_are_actionable_without_retries(task_store, monkeypatch, failure):
    state, _ = task_store
    calls = []
    def failed(*args, **kwargs):
        calls.append(args)
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(args[0], 30)
        return subprocess.CompletedProcess(args[0], -9, '', '')
    monkeypatch.setattr(reference.subprocess, 'run', failed)
    with pytest.raises(ValueError, match='Task contract reader'):
        tasks.listing(state, 'demo')
    assert len(calls) == 1
