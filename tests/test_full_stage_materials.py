"""New preparation selections keep original stage ownership and complete materials."""

import asyncio
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.development.application as tasks
import ergora.definitions.workflows as workflows
from ergora.development.inputs import execution_input
from ergora.development.dags import WorkDelivery
from test_work_agents import work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_workflow_definitions import EXAMPLES


def _fixed_observation_checks(cases):
    """Small frozen declaration; no oracle or model is executed by this fixture."""
    from ergora.development import verification
    from ergora.storage.assets import manifest_digest

    text = '# Frozen stdlib observation program.\n'
    entry = {'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'executable_bits': 0}
    inventory = {'observe.py': {key: entry[key] for key in ('sha256', 'executable_bits')}}
    return {'configuration': {'format': 'fixed-text-observations-v1',
        'coverage': 'Observe every declared configuration case without candidate-defined expected values.',
        'entrypoint': 'observe.py', 'source': {'files': {'observe.py': entry}, 'digest': manifest_digest(inventory)},
        'runtime': verification.runtime_identity(Path(sys.executable).absolute()),
        'candidate_paths': ['src/config.json'], 'cases': cases, 'wall_seconds': 2}}


def test_absent_fixed_verification_keeps_original_lightweight_project_scope():
    from ergora.development import verification

    project = {'id': 'original', 'revision': 7}
    assert verification.snapshot(project) is None
    verification.require_admission(project, {'request': {'task_id': 'historical'}})
    assert project == {'id': 'original', 'revision': 7}


@pytest.mark.parametrize('executable,resolved', [
    ('/opt/ergora/.venv/bin/python', '/usr/bin/python3.12'),
    (r'C:\Ergora\.venv\Scripts\python.exe', r'C:\Python312\python.exe'),
])
def test_saved_fixed_runtime_paths_are_read_without_host_path_rewriting(executable, resolved):
    """Portable data validation; neither program is accessed or executed."""
    from ergora.development import verification

    checks = _fixed_observation_checks([{'id': 'case', 'input': {}, 'expected': True}])
    checks['configuration']['runtime'] = {'executable': executable, 'resolved': resolved, 'sha256': '1' * 64}
    original = json.dumps(checks, ensure_ascii=False)
    assert verification.validate_checks(checks) is checks
    assert json.dumps(checks, ensure_ascii=False) == original


@pytest.mark.parametrize('expected,observed,matches', [
    ({'nested': [True, {'enabled': 0}]}, {'nested': [1, {'enabled': False}]}, False),
    ([], {}, False), ({}, [], False), ([], [], True), ({}, {}, True),
    ({'b': [None, True], 'a': []}, {'a': [], 'b': [None, True]}, True),
    (-(2**53 - 1), -(2**53 - 1), True), (2**53 - 1, 2**53 - 1, True),
])
def test_fixed_observations_compare_the_exact_nested_value_domain(expected, observed, matches):
    from ergora.development import verification

    check = {'cases': [{'id': 'case', 'input': None, 'expected': expected}]}
    raw = json.dumps({'observations': [{'case_id': 'case', 'value': observed}]}).encode()
    result = verification.observations(check, raw, 0)
    assert result['passed'] is matches
    assert result['comparisons'][0]['matches'] is matches
    assert base64.b64decode(result['raw_base64'], validate=True) == raw
    assert result['raw_sha256'] == hashlib.sha256(raw).hexdigest()


def test_fixed_observations_normalize_integer_zero_without_erasing_raw_output_identity():
    from ergora.development import verification

    check = {'cases': [{'id': 'zero', 'input': None, 'expected': 0}]}
    raws = [b'{"observations":[{"case_id":"zero","value":-0}]}',
            b'{ "observations": [ { "value": 0, "case_id": "zero" } ] }']
    results = [verification.observations(check, raw, 0) for raw in raws]
    assert all(result['passed'] for result in results)
    assert results[0]['comparisons'] == results[1]['comparisons']
    assert results[0]['raw_sha256'] != results[1]['raw_sha256']
    assert [base64.b64decode(result['raw_base64'], validate=True) for result in results] == raws


@pytest.mark.parametrize('raw', [
    b'{"observations":[{"case_id":"case","value":1.0}]}',
    b'{"observations":[{"case_id":"case","value":1e0}]}',
    b'{"observations":[{"case_id":"case","value":NaN}]}',
    b'{"observations":[{"case_id":"case","value":Infinity}]}',
    b'{"observations":[{"case_id":"case","value":9007199254740992}]}',
    b'{"observations":[{"case_id":"case","value":-9007199254740992}]}',
    b'{"observations":[{"case_id":"case","value":"\\ud800"}]}',
    b'{"observations":[{"case_id":"case","value":1,"value":1}]}',
    b'{"observations":[{"case_id":"case","value":1},{"case_id":"case","value":1}]}',
    b'{"observations":[]}',
    b'{"observations":[{"case_id":"extra","value":1}]}',
    b'{"observations":[{"case_id":"case","value":1},{"case_id":"extra","value":1}]}',
    b'{"observations":[{"case_id":"case","value":1}],"passed":true}',
    b'{"observations":', b'\xff',
])
def test_fixed_observations_cannot_accept_malformed_or_replacement_case_evidence(raw):
    from ergora.development import verification

    check = {'cases': [{'id': 'case', 'input': None, 'expected': 1}]}
    result = verification.observations(check, raw, 0)
    assert result['passed'] is False and result['failure']
    assert not result['comparisons']
    assert base64.b64decode(result['raw_base64'], validate=True) == raw
    assert result['raw_sha256'] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('raw,returncode', [(None, 0), (b'{"observations":[{"case_id":"case","value":1}]}', 9)])
def test_fixed_exit_or_missing_output_cannot_replace_observation_acceptance(raw, returncode):
    from ergora.development import verification

    check = {'cases': [{'id': 'case', 'input': None, 'expected': 1}]}
    result = verification.observations(check, raw, returncode)
    assert result['passed'] is False and result['failure'] and not result['comparisons']
    assert result['raw_sha256'] == (hashlib.sha256(raw).hexdigest() if raw is not None else None)


@pytest.mark.parametrize('field', ['input', 'expected'])
@pytest.mark.parametrize('value', [1.0, {'nested': [2**53]}, '\ud800'])
def test_fixed_declarations_validate_case_inputs_and_expected_values_at_the_same_boundary(field, value):
    from ergora.development import verification

    case = {'id': 'case', 'input': [], 'expected': {}}
    case[field] = value
    checks = _fixed_observation_checks([case])
    with pytest.raises(ValueError):
        verification.validate_checks(checks)


def test_fixed_script_input_cannot_substitute_nested_integer_for_boolean():
    from copy import deepcopy
    from ergora.development import verification

    check = _fixed_observation_checks([{'id': 'case', 'input': {'nested': [True]}, 'expected': None}])['configuration']
    expected_subject = {'candidate_sha': 'a' * 40}
    oid = hashlib.sha1(b'blob 2\0{}').hexdigest()
    repository = {'candidate': {'commit': expected_subject['candidate_sha'],
        'files': {'src/config.json': {'git_object': oid, 'mode': '100644'}}},
        'blobs': {oid: {'text': '{}', 'sha256': hashlib.sha256(b'{}').hexdigest()}}, 'scope': ['src/config.json']}
    original = verification.script_input('configuration', check, expected_subject, repository)
    replacement = deepcopy(original)
    replacement['cases'][0]['input']['nested'] = [1]
    assert verification.sha(replacement) != verification.sha(original)
    with pytest.raises(ValueError, match='case set'):
        verification.validate_input(replacement, 'configuration', check, expected_subject)


def test_deep_fixed_values_preserve_complete_comparisons_and_raw_output():
    """Compact artifact encoding must not narrow the valid observation domain."""
    import base64
    from ergora.development import verification

    observed = [0] * 1000
    for _ in range(54):
        observed = [observed]
    raw = json.dumps({'observations': [{'case_id': 'case', 'value': observed}]}, separators=(',', ':')).encode()
    assert len(raw) < verification.OBSERVATION_BYTES
    check = {'cases': [{'id': 'case', 'input': {}, 'expected': observed}]}
    result = verification.observations(check, raw, 0)
    assert result['passed'] is True and result['comparisons'][0]['matches'] is True
    assert base64.b64decode(result['raw_base64'], validate=True) == raw
    assert result['raw_sha256'] == hashlib.sha256(raw).hexdigest()


@pytest.mark.skipif(sys.platform != 'linux', reason='Preparing the original native fixture requires Linux/WSL2')
def test_nonempty_fixed_input12_reads_frozen_bytes_in_dependency_isolation(full_creation, monkeypatch):
    """A controlled admission extension exercises the actual stdlib reader, without re-registration."""
    pytest.importorskip('temporalio')
    import ergora
    import ergora.native.resources as native_resources
    from ergora.development import envelopes, verification

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, _, definition = full_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    original = execution_input(document)
    assert 'verification' not in original.stage_material()
    project = state.project('demo')
    project['registration']['definition']['trusted_checks'] = _fixed_observation_checks([
        {'id': 'bounds', 'input': {'ids': [-(2**53 - 1), 2**53 - 1], 'empty': []},
         'expected': {'valid': True, 'references': {}}}])
    frozen = verification.snapshot(project)
    document = {**document, 'verification': frozen}
    document['sha256'] = envelopes.identity({key: item for key, item in document.items() if key != 'sha256'})
    selected = execution_input(document)
    selected.require_submission()
    assert selected.stage_material()['verification'] == frozen
    assert selected.evidence_contract() == {'original_input': document, 'original_input_sha256': envelopes.identity(document)}
    owner = deepcopy(document['budget']['instance']['scope'])
    assert all(frozen[key] == owner[key] for key in ('project', 'project_revision', 'registration_sha256'))
    from ergora.configuration import projects

    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later-role-binding'}, project['revision'])
    assert state.project('demo')['revision'] > frozen['project_revision']
    shutil.rmtree(definition['composition']['manifest'])
    code = 'import json,sys\nsys.path.insert(0,' + repr(str(Path(ergora.__file__).parent.parent)) + ')\n' + '''
from ergora.development.envelopes import decode_admission
from ergora.development.inputs import execution_input
try:
 document=decode_admission(sys.stdin.buffer.read())
 selected=execution_input(document)
 selected.require_submission()
 assert selected.stage_material().get('verification')==selected.document.get('verification')
 assert selected.evidence_contract()['original_input']==selected.document
 print(selected.task_queue('dev'))
finally:
 assert not any(name in sys.modules for name in ('yaml','jsonschema','temporalio','mcp',
  'ergora.storage.state','ergora.definitions.bundles'))
'''

    def isolated(value):
        return subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(value),
                              capture_output=True, text=True, timeout=20)

    for value in (document, original.document):
        result = isolated(value)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.strip() == 'dev.composition-v12'
    for field, value in (('project', 'different-project'), ('project_revision', owner['project_revision'] + 1),
                         ('registration_sha256', '0' * 64)):
        replacement = deepcopy(document)
        replacement['verification'][field] = value
        replacement['verification']['sha256'] = verification.sha({
            key: item for key, item in replacement['verification'].items() if key != 'sha256'})
        verification.validate_snapshot(replacement['verification'])
        replacement['sha256'] = envelopes.identity({key: item for key, item in replacement.items() if key != 'sha256'})
        assert replacement['budget']['instance'] == document['budget']['instance']
        result = isolated(replacement)
        assert result.returncode != 0, field + ': ' + result.stdout + result.stderr
        assert 'Fixed verification owner differs from its original budget scope' in result.stderr
    assert document['budget']['instance']['scope'] == owner
    assert 'verification' not in original.stage_material()


@pytest.fixture
def full_graph(work_graph, tmp_path, request):
    from fixtures.full_stage_acceptance import prepare_graph

    library, grant, _, execution, units = work_graph
    identity, version = prepare_graph(tmp_path / 'full-graph', library, EXAMPLES,
                                      concurrency=getattr(request, 'param', 2))
    graph = workflows.preview(library.root, identity, version, grant)
    def nested(path):
        return 'root/development/' + path.removeprefix('root/')
    execution = {**execution, 'protocol': 'work-units-v2', 'instance': nested(execution['instance']),
                 'assignments': {key: nested(path) for key, path in execution['assignments'].items()}}
    preparation = {'protocol': 'preparation-dag-v1', 'mode': 'task-mcp', 'repository_paths': ['src'],
        **{stage: {'instance': 'root/development/preparation/' + stage,
                   'coordinator': 'root/development/preparation/' + stage + '/coordinator'}
           for stage in ('inventory', 'plan')}}
    return library, grant, graph, execution, units, preparation


@pytest.fixture
def full_creation(request, tmp_path):
    if sys.platform != 'linux':
        pytest.skip('Preparing the original native fixture requires Linux/WSL2')
    state, registered, definition = request.getfixturevalue('work_creation')
    library, grant, graph, execution, _, preparation = request.getfixturevalue('full_graph')
    manifest = workflows.prepare_manifest(library.root, graph['root']['id'], graph['root']['version'], grant, tmp_path / 'full-manifest')
    definition.update(schema_version=8, budget={'wall_seconds': 120, 'cleanup_seconds': 5, 'model_invocations': 258})
    option = definition['composition']
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'], execution=execution, preparation=preparation,
                  review_instance='root/development/review', native={'protocol': 'six-stage-v1', 'instance': 'root/development'})
    option['backend_overrides'] = {'root/development/' + path.removeprefix('root/'): value
                                   for path, value in option['backend_overrides'].items()}
    return state, registered, definition


@pytest.mark.parametrize('fixed', [False, True])
def test_missing_control_project_obeys_fixed_admission_before_original_job_boundary(full_creation, monkeypatch, tmp_path, fixed):
    """Real process admission; the inert run marker stops before ownership or execution."""
    pytest.importorskip('temporalio')
    import ergora
    import ergora.configuration.registrations as registrations
    import ergora.native.resources as native_resources
    from ergora.development import envelopes
    from ergora.storage.state import State
    from test_registrations import fixed_checks
    from test_task_creation import _files

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, registered, definition = full_creation
    if fixed:
        # The declaration must be present at the first actual registration.
        state = State(tmp_path / 'fixed-control')
        registered = deepcopy(registered)
        registered['execution'].update(config_directory=str(tmp_path / 'fixed-config'),
                                       state_directory=str(tmp_path / 'fixed-runtime'))
        registered['trusted_checks'] = fixed_checks(registered['execution']['installation'])
        registrations.register(state, registered, 0)
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    assert created['status'] == 'published'
    document = preview['files']['task.spec.json']
    assert ('verification' in document) is fixed
    config, runtime = (Path(registered['execution'][key]) for key in ('config_directory', 'state_directory'))
    native = json.loads((runtime / 'tasks' / definition['task_id'] / 'project.json').read_bytes())
    marker = json.loads((config / 'ergora/registrations/demo.json').read_bytes())
    assert ('trusted_checks' in native) is fixed and marker['control_home'] == str(state.root)
    roots = {key: str(runtime / key) for key in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    (config / 'adapter.json').write_text(json.dumps({**roots, 'trusted_receipts': True}))
    selected = execution_input(document)
    adapter = selected.adapter({**roots, 'trusted_receipts': True})
    context = envelopes.initial_preparation_contexts(document, document['legacy_spec']['request']['repository']['starting_sha'])[0]
    job = asyncio.run(adapter.submit(context))
    path = adapter.roots['requests'] / definition['task_id'] / (job['job_id'] + '.json')
    before = _files(runtime), _files(config)
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime),
        PYTHONPATH=os.pathsep.join(map(str, (Path(ergora.__file__).parent.parent,
            Path(registered['execution']['installation']) / 'local',
            Path(registered['execution']['installation']) / 'upstream/platform'))))
    code = '''
import json,sys
from pathlib import Path
import ergora.development.runtime.executor as driver
from ergora.development.runtime.jobs import BudgetedJob
from ergora.storage.state import State
class JobBoundary(Exception): pass
starts={}
initialize=BudgetedJob.__init__
def counted_init(self,*args,**kwargs):
 starts['job']+=1
 return initialize(self,*args,**kwargs)
def stop_at_job(self):
 starts['run']+=1
 raise JobBoundary()
def forbidden(label):
 def record(*args,**kwargs):
  starts[label]+=1
  raise AssertionError('Unexpected '+label)
 return record
BudgetedJob.__init__=counted_init
BudgetedJob.run=stop_at_job
driver.original.claim=forbidden('claim')
driver._execute=forbidden('body')
state=State(Path(sys.argv[2]))
observations=[]
for missing in (False,True):
 if missing:
  with state.connect() as db: db.execute('DELETE FROM projects WHERE id=?',('demo',))
 starts=dict.fromkeys(('job','run','claim','body'),0)
 try:
  driver.process(Path(sys.argv[1]),state.root)
 except JobBoundary:
  outcome='job_boundary'
 except (driver.Blocked,ValueError) as error:
  outcome='refused'
  assert 'project' in str(error).lower(),str(error)
 else: raise AssertionError('Process did not reach an observed boundary')
 observations.append({'missing':missing,'outcome':outcome,'starts':starts})
print(json.dumps(observations))
'''
    result = subprocess.run([sys.executable, '-P', '-B', '-c', code, str(path), str(state.root)],
                            capture_output=True, text=True, env=environment, timeout=20)
    (tmp_path / 'admission.stdout.txt').write_text(result.stdout)
    (tmp_path / 'admission.stderr.txt').write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    healthy, missing = json.loads(result.stdout)
    boundary = {'job': 1, 'run': 1, 'claim': 0, 'body': 0}
    assert healthy == {'missing': False, 'outcome': 'job_boundary', 'starts': boundary}
    assert missing == {'missing': True, 'outcome': 'refused' if fixed else 'job_boundary',
                       'starts': dict.fromkeys(boundary, 0) if fixed else boundary}
    assert not (runtime / 'executor.sqlite3').exists()
    assert (_files(runtime), _files(config)) == before


def test_frozen_preparation_survives_source_removal_and_keeps_its_original_route(full_creation, monkeypatch):
    pytest.importorskip('temporalio')
    import ergora.native.resources as native_resources
    import ergora
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, registered, definition = full_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    selected.require_submission()
    assert document['schema_version'] == 12 and preview['schema_version'] == 8
    assert selected.task_queue('dev') == 'dev.composition-v12'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v12')
    sdk_definition = _Definition.must_from_run_fn(selected.entrypoint)
    assert sdk_definition.name == 'ErgoraCompositionWorkflowV12'
    import asyncio
    from ergora.development.runtime.worker import _ErgoraPackage
    from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

    async def prepare_sdk():
        finder = _ErgoraPackage()
        sys.meta_path.insert(0, finder)
        try:
            SandboxedWorkflowRunner().prepare_workflow(sdk_definition)
        finally:
            sys.meta_path.remove(finder)
    asyncio.run(prepare_sdk())
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(ergora.__file__).parent.parent)) + ');'
            'from ergora.development.inputs import execution_input;'
            'selected=execution_input(json.load(sys.stdin));selected.require_submission();'
            'assert not any(name in sys.modules for name in ("jsonschema","temporalio","mcp"));'
            'print(selected.task_queue("dev"))')
    isolated = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                              capture_output=True, text=True, timeout=20)
    assert isolated.returncode == 0, isolated.stderr
    assert isolated.stdout.strip() == 'dev.composition-v12'
    assert {member['role'] for member in document['composition']['preparation']['members'].values()} == {'inspector', 'planner'}
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    shutil.rmtree(definition['composition']['manifest'])
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    runtime = Path(registered['execution']['state_directory'])
    intent = runtime / 'ergora/task-creations' / (definition['task_id'] + '.intent.json')
    modified = json.loads(intent.read_bytes())
    modified['definition']['composition']['preparation']['repository_paths'] = ['src/other']
    intent.write_text(json.dumps(modified))
    with pytest.raises(ValueError, match='differs'):
        tasks.creation(state, 'demo', definition['task_id'])


def test_text_only_cannot_silently_drop_required_skill_attachments(full_creation):
    state, registered, definition = full_creation
    definition['composition']['preparation']['mode'] = 'text-only'
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'failed'
    runtime = Path(registered['execution']['state_directory'])
    stderr = (runtime / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')).read_text()
    assert 'attachments require task-mcp' in stderr


@pytest.mark.skipif(sys.platform != 'linux', reason='Native stage monitor requires Linux/WSL2')
@pytest.mark.parametrize('case', ['full', 'serial', 'capacity', 'unread', 'source-artifact', 'source-claim', 'source-receipt',
                                 'owner-source-artifact', 'issue-source', 'development-specialists', 'method-addendum',
                                 'fixed-candidate-check', 'fixed-candidate-check-graph',
                                 'fixed-candidate-check-graph-recoverable', 'fixed-candidate-check-graph-wait-recoverable'])
def test_real_preparation_calls_and_original_stage_results(tmp_path, case):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'large-change', 'command',
        'composition-work-materials-' + case], capture_output=True, text=True, timeout=210)
    (tmp_path / 'fixture.stdout.json').write_text(result.stdout)
    (tmp_path / 'fixture.stderr.log').write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    if record.get('skip'):
        pytest.skip(record['skip'])
    assert record['case'] == case and record['original_owners']
    if case == 'method-addendum':
        assert 'work:implementation' in record['method_material_consumers']
        assert any(stage.startswith('review:') for stage in record['method_material_consumers'])
    if case.startswith('fixed-candidate-check'):
        proof = record['independent_check']
        assert proof['same_observations'] is True and proof['passing_receipt']['status'] == 'succeeded'
        assert proof['stop']['status'] in ('cancelled', 'unknown') and proof['outer_cleanup_confirmed'] is True
        assert len(proof['stopped_identities']) == 3 and proof['original_starts'] == 1
    if case == 'fixed-candidate-check-graph':
        graph = proof['graph']
        assert graph['review_calls'] == 1 and graph['proof_matches'] and graph['original_check_records_unchanged']
        assert graph['blocked_before_review'] == ['wrong-requirements', 'wrong-head', 'wrong-task-packet',
                                                  'wrong-receipt', 'changed-packet', 'missing-receipt',
                                                  'nonpassing-original', 'stale-project-revision']
        assert graph['revised_project_revision'] == graph['historical_check_revision'] + 1
        wait = graph['wait']
        assert (wait['timed_out'], wait['stopped'], wait['wrong_locator']) == ('timed_out', 'cancelled', 'failed')
        assert wait['proof']['operation_id'] == 'wait-check' and wait['proof']['status'] == 'validated'
        assert wait['proof']['wait_seconds'] == 10 and wait['reviewer_run_id'] and wait['original_native_effects_only']
    if case.endswith('-recoverable'):
        recovery = proof['graph']
        assert recovery['reused_proof'] and recovery['native_records_unchanged']
        assert recovery['reviewer_calls'] == 1 and recovery['original_reviewer_reused']
        if case.endswith('-wait-recoverable'):
            assert recovery['original_wait_observed']
            assert recovery['refused'] == ['incomplete', 'changed-terminal-identity', 'reordered-proof', 'expired-read']
        else:
            assert recovery['refused'] == ['incomplete', 'altered-proof', 'stale-with-prepared-input',
                                           'missing-native-receipt', 'expired-read']


@pytest.mark.parametrize('full_graph,case', [(1, 'complete'), (2, 'complete'), (2, 'duplicate'), (2, 'stop')], indirect=['full_graph'])
def test_preparation_ready_loop_uses_frozen_capacity_and_stops_successors(full_creation, full_graph, monkeypatch, case):
    import asyncio
    from datetime import datetime, timezone
    import ergora.native.resources as native_resources
    import ergora
    from ergora.development import envelopes as task_envelopes

    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    from dev_platform.workflow import StopWork
    from temporalio import workflow

    state, _, definition = full_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    selected = execution_input(document)
    app = selected.workflow_type()()
    app.spec, app.admission = selected.spec, document
    monkeypatch.setattr(workflow, 'wait', asyncio.wait)
    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    active, maximum, contexts = set(), [], []

    async def call(name, context, result_type=dict):
        if name == 'dev_submit':
            contexts.append(context)
            active.add(context['stage'])
            maximum.append(len(active))
            return context
        assert name == 'dev_poll'
        await asyncio.sleep(.02)
        active.remove(context['stage'])
        if case == 'stop':
            app.cancel_reason = 'Controlled stop before a preparation successor'
        return {'job_id': context['job_id'], 'job_sha256': task_envelopes.identity(context),
                'state': 'SUCCEEDED', 'candidate_sha': context['expected_candidate_sha'],
                'actor': {'id': context['stage'], 'session_id': 'duplicate' if case == 'duplicate' else context['job_id']}}

    app.call = call
    async def exercise():
        starting = selected.spec['request']['repository']['starting_sha']
        inventory = await app.stage('inventory', starting)
        await app.stage('plan', starting, dependencies={'inventory': inventory})
    if case != 'complete':
        with pytest.raises(StopWork, match='distinct|Controlled stop'):
            asyncio.run(exercise())
        assert not any(context['stage'] in ('inventory', 'plan') for context in contexts)
    else:
        asyncio.run(exercise())
        assert len(contexts) == 6 and set(app.results) == set(document['budget']['slots']) - {
            stage for stage in document['budget']['slots'] if stage.startswith(('work:', 'review:'))}
        assert len(app.authors()[1]) == 6
        for context in contexts:
            group_stage = 'inventory' if context['stage'].startswith('inventory') else 'plan'
            assert context['dependencies'] == ({} if group_stage == 'inventory' else {'inventory': app.results['inventory']})
            if context['stage'] in ('inventory', 'plan'):
                assert len(context['preparation_ports']['producers']) == 2
        limit = next(group for group in task_envelopes.preparation_dags(document['composition']).values())['dag']
        expected = min(scope['limit'] for leaf in limit.members.values() for scope in leaf['concurrency_scopes'])
        assert max(maximum) == min(2, expected)
    assert not app.active_stages
