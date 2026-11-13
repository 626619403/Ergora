"""Offline training observations preserve the native identity and uncertainty."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import reference, registrations, training
from test_registrations import installation, registration


@pytest.fixture
def experiments(registration, request):
    state, definition = registration
    if getattr(request, 'param', None) == 'shared-directories':
        definition['execution']['state_directory'] = definition['execution']['config_directory']
    registered = registrations.register(state, definition, 0)
    runtime = Path(definition['execution']['state_directory'])
    config = Path(definition['execution']['config_directory'])
    prefix = runtime / 'training/projects/demo/perf'

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    commit = registered['registration']['definition']['base_sha']
    baseline = {'baseline_id': 'baseline-one', 'commit': commit, 'config_sha256': 'a' * 64,
                'workload_fingerprint': 'b' * 64, 'evidence_uri': 'synthetic:test', 'quality_scope': 'CPU contract only'}
    write(prefix / 'baseline.json', baseline)
    runner = {'schema_version': 1, 'runner_template_id': 'trusted', 'project': 'demo', 'repo': definition['repo'],
              'command': [sys.executable, '-c', 'pass'], 'timeout_seconds': 30}
    write(config / 'training-runners/trusted.json', runner)
    template = json.loads((reference.ROOT / 'platform/templates/training-optimization/experiment.json').read_text())
    for ident in ('alpha', 'beta'):
        manifest = {key: ('c' * 64 if value == 'REPLACE_SHA256' else value) for key, value in template.items()}
        manifest.update(experiment_id=ident, baseline_id=baseline['baseline_id'], contract_approved=True,
                        baseline_commit=commit, candidate_commit=commit, baseline_sha=commit, candidate_sha=commit,
                        base_config_sha256=baseline['config_sha256'], workload_fingerprint=baseline['workload_fingerprint'],
                        local_project='demo', runner_template_id='trusted', max_run_seconds=120)
        manifest_path = runtime / f'training/manifests/{ident}.json'
        digest = write(manifest_path, manifest)
        write(prefix / f'experiments/{ident}/manifest.json', manifest)
        binding = {'experiment_id': ident, 'manifest_sha': digest, 'candidate_sha': commit, 'baseline_sha': commit}
        spec = {'binding': binding, 'manifest_uri': manifest_path.as_uri(), 'poll_seconds': 30,
                'max_run_seconds': 120, 'release_wait_seconds': 86400, 'cancel_wait_seconds': 60}
        write(runtime / f'training/specs/{ident}.json', spec)
        job_id = 'local-perf-' + ident
        job = runtime / f'training/jobs/{ident}'
        write(job / 'request.json', {'schema_version': 1, 'experiment': spec, 'runner': runner, 'job_id': job_id})
        write(job / 'started.json', {'binding': binding, 'job_id': job_id})
        if ident == 'alpha':
            gate = {'binding': binding, 'manifest_sha256': digest, 'passed': False, 'evidence_sha256': 'd' * 64,
                    'summary': 'Synthetic negative result', 'archive_report': None}
            gate_sha = write(job / 'gate-report.json', gate)
            write(job / 'result.json', {'binding': binding, 'job_id': job_id, 'state': 'SUCCEEDED',
                'detail': gate['summary'], 'gate': {'report': str(job / 'gate-report.json'),
                'report_sha256': gate_sha, 'mlflow_run_id': 'recorded-synthetic-run'}})
            write(runtime / 'training/negative-results/alpha.json', {'project': 'demo', 'experiment_id': ident,
                  'binding': binding, 'state': 'SUCCEEDED', 'detail': gate['summary'], 'result': str(job / 'result.json')})
    return state, definition, runtime, prefix, write


def test_native_identity_gate_failure_and_unknown_do_not_mutate_records(experiments):
    state, definition, runtime, prefix, _ = experiments
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    project_before = state.project('demo')
    page = training.inspect(state, 'demo')
    assert [item['experiment_id'] for item in page['items']] == ['alpha', 'beta']
    assert page['runtime_status'] == 'not_queried' and not page['errors']
    first, second = page['items']
    assert first['recorded_result_state'] == 'SUCCEEDED' and first['recorded_gate']['passed'] is False
    assert second['started_recorded'] and second['recorded_result_state'] is None and second['recorded_gate'] is None
    detail = training.inspect(state, 'demo', 'alpha')['experiment']
    assert detail['manifest'] == json.loads((prefix / 'experiments/alpha/manifest.json').read_bytes())
    assert detail['binding']['manifest_sha'] == hashlib.sha256((prefix / 'experiments/alpha/manifest.json').read_bytes()).hexdigest()
    assert detail['negative_result']['detail'] == 'Synthetic negative result'
    assert detail['recorded_gate']['mlflow_run_id'] == 'recorded-synthetic-run'
    assert state.project('demo') == project_before
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before


def test_pagination_advances_across_broken_entries_and_baseline_drift(experiments):
    state, _, _, prefix, write = experiments
    write(prefix / 'experiments/a-broken/manifest.json', {'invalid': True})
    first = training.inspect(state, 'demo', limit=1)
    assert first['items'] == [] and first['errors'][0]['experiment_id'] == 'a-broken' and first['next_after']
    second = training.inspect(state, 'demo', limit=1, after=first['next_after'])
    assert second['items'][0]['experiment_id'] == 'alpha' and second['next_after']
    third = training.inspect(state, 'demo', limit=1, after=second['next_after'])
    assert third['items'][0]['experiment_id'] == 'beta' and third['next_after'] is None
    baseline = json.loads((prefix / 'baseline.json').read_bytes());baseline['config_sha256'] = 'e' * 64
    write(prefix / 'baseline.json', baseline)
    item = training.inspect(state, 'demo', 'alpha')['experiment']
    assert item['baseline_matches'] is False and 'config' in item['baseline_error']
    assert item['recorded_result_state'] == 'SUCCEEDED'


@pytest.mark.parametrize('mutation,error', [
    ('manifest', 'manifest bytes'), ('spec', 'spec differs'), ('runner', 'Git repository'),
    ('result', 'immutable binding'), ('gate', 'result SHA'), ('gate-path', 'outside'),
])
def test_corrupted_binding_or_gate_fails_without_hiding_other_experiments(experiments, mutation, error):
    state, definition, runtime, prefix, write = experiments
    paths = {'manifest': prefix / 'experiments/alpha/manifest.json', 'spec': runtime / 'training/specs/alpha.json',
             'runner': runtime / 'training/jobs/alpha/request.json', 'result': runtime / 'training/jobs/alpha/result.json',
             'gate': runtime / 'training/jobs/alpha/gate-report.json', 'gate-path': runtime / 'training/jobs/alpha/result.json'}
    path = paths[mutation];value = json.loads(path.read_bytes())
    if mutation == 'manifest': value['notes'] += 'changed'
    elif mutation == 'spec': value['binding']['candidate_sha'] = '0' * 40
    elif mutation == 'runner': value['runner']['repo'] = definition['repo'] + '-other'
    elif mutation == 'result': value['binding']['manifest_sha'] = '0' * 64
    elif mutation == 'gate': value['passed'] = True
    else: value['gate']['report'] = str(prefix / 'baseline.json')
    write(path, value)
    with pytest.raises(ValueError, match=error):
        training.inspect(state, 'demo', 'alpha')
    observed = training.inspect(state, 'demo')
    assert [item['experiment_id'] for item in observed['items']] == ['beta']
    assert error in observed['errors'][0]['error']


def test_shared_storage_never_exposes_another_project(experiments):
    state, definition, _, _, _ = experiments
    other = deepcopy(definition);other['id'] = 'other';other['tracker']['project'] = 'local/other'
    registrations.register(state, other, 0)
    assert training.inspect(state, 'other')['items'] == []
    with pytest.raises(ValueError):
        training.inspect(state, 'other', 'alpha')


@pytest.mark.parametrize('experiments', ['shared-directories'], indirect=True)
def test_config_and_state_can_share_the_same_registered_directory(experiments):
    state, _, _, _, _ = experiments
    page = training.inspect(state, 'demo')
    assert [item['experiment_id'] for item in page['items']] == ['alpha', 'beta'] and not page['errors']
    detail = training.inspect(state, 'demo', 'alpha')['experiment']
    assert 'config/training-runners/trusted.json' in detail['files']
    assert 'state/training/manifests/alpha.json' in detail['files']
    assert detail['recorded_gate']['passed'] is False


def test_repository_ownership_requires_current_runner_or_original_request(experiments):
    state, definition, runtime, _, _ = experiments
    current = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
    original_runner = current.read_bytes();current.unlink()
    assert training.inspect(state, 'demo', 'alpha')['experiment']['current_runner'] is None
    for name in ('request.json', 'started.json', 'result.json', 'gate-report.json'):
        (runtime / 'training/jobs/alpha' / name).unlink()
    with pytest.raises(ValueError, match='Git repository.*both missing'):
        training.inspect(state, 'demo', 'alpha')
    page = training.inspect(state, 'demo')
    assert [item['experiment_id'] for item in page['items']] == ['beta'] and page['errors']
    current.write_bytes(original_runner)
    assert training.inspect(state, 'demo', 'alpha')['experiment']['job_id'] is None


def test_read_limits_and_symlinks_are_enforced(experiments):
    state, _, runtime, prefix, _ = experiments
    original = prefix / 'experiments/alpha/manifest.json'
    original.write_bytes(b' ' * 1_048_577)
    with pytest.raises(ValueError, match='size limit'):
        training.inspect(state, 'demo', 'alpha')
    if sys.platform != 'win32':
        original.unlink();original.symlink_to(runtime / 'training/manifests/alpha.json')
        with pytest.raises(ValueError, match='Symlinks'):
            training.inspect(state, 'demo', 'alpha')


def test_cli_http_and_application_share_the_same_offline_observation(experiments):
    state, _, _, _, _ = experiments
    pytest.importorskip('fastapi');pytest.importorskip('httpx')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    with TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers) as client:
        for args, path, expected in [(['list', 'demo', '--limit', '1'], '/api/projects/demo/training?limit=1',
                                      training.inspect(state, 'demo', limit=1)),
                                     (['show', 'demo', 'alpha'], '/api/projects/demo/training/alpha',
                                      training.inspect(state, 'demo', 'alpha'))]:
            response = client.get(path)
            assert response.status_code == 200 and response.json() == expected
            cli = subprocess.run([sys.executable, '-m', 'ergora', '--home', str(state.root), 'training', *args],
                                 capture_output=True, text=True, encoding='utf-8', timeout=30)
            assert cli.returncode == 0, cli.stderr
            assert json.loads(cli.stdout) == expected
        assert client.get('/assets/training.js').status_code == 200
