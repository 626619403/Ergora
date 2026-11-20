import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import ergora.native.commands as native_commands
import ergora.native.resources as native_resources
import ergora
import shutil


def test_public_reference_identity():
    assert native_resources.verify()["files"] == 283


def test_reference_public_payload_preserves_current_native_auth_sources():
    import runpy

    root = native_resources.ROOT / 'platform'
    builder = runpy.run_path(str(root / 'bootstrap/report/build_report.py'))
    payload = builder['payload_files'](root)
    for module in ('setup.py', 'doctor.py', 'process_job.py', 'executor.py'):
        name = 'local/agent_platform/' + module
        assert payload[name] == payload['bootstrap/' + name] == (root / name).read_bytes()


def test_template_copy_preserves_files_and_existing_destination(tmp_path):
    for kind in native_resources.TEMPLATES:
        destination = tmp_path / kind
        native_resources.copy_template(kind, destination)
        source = native_resources.ROOT / "platform/templates" / kind
        assert (destination / "agent-contract.json").is_file()
        for file in source.rglob("*"):
            if file.is_file():
                assert file.read_bytes() == (destination / file.relative_to(source)).read_bytes()
        with pytest.raises(ValueError, match="preserve"):
            native_resources.copy_template(kind, destination)


def test_large_change_defaults_and_copies_use_the_current_complete_contract(tmp_path):
    source = native_resources.ROOT / "platform"
    current = native_resources.template_details("large-change")["input"]
    request = json.loads((source / "upstream/platform/task-types/large-change/examples/request.json").read_text())
    portable = json.loads((source / "upstream/platform/portable/examples/large-change/task.json").read_text())
    assert current == request["input"] == portable["input"]
    assert {unit["id"]: unit["depends_on"] for unit in current["work_units"]} == {
        "contract": [], "server": ["contract"], "client": ["contract"],
        "integration-tests": ["server", "client"],
    }
    instructions = (source / "templates/large-change/instructions.md").read_bytes()
    assert instructions == (source / "upstream/platform/task-types/large-change/instructions.md").read_bytes()
    assert instructions == (source / "upstream/platform/portable/packages/large-change/instructions.md").read_bytes()

    destination = tmp_path / "api copy"
    native_resources.copy_template("large-change", destination)
    cli_destination = tmp_path / "cli copy"
    command = [sys.executable, "-m", "ergora", "templates", "copy", "large-change", str(cli_destination)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    for copied in (destination, cli_destination):
        assert json.loads((copied / "input.json").read_bytes()) == current
        assert (copied / "instructions.md").read_bytes() == instructions
    before = {path: path.read_bytes() for path in cli_destination.rglob("*") if path.is_file()}
    repeated = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert repeated.returncode != 0
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_native_large_change_initialization_uses_current_sources_and_preserves_existing_files(
        prepared_training_installation, tmp_path):
    import shutil

    source, _ = prepared_training_installation
    installation = tmp_path / "native installation"
    shutil.copytree(source, installation)
    shutil.rmtree(installation / "templates/large-change")
    destination = tmp_path / "native copy"
    probe = ("import sys;from pathlib import Path;sys.path.insert(0," + repr(str(installation / "local")) + ");"
             "from agent_platform import templates;templates.install();templates.copy('large-change',Path(sys.argv[1]))")
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(tmp_path / "config"),
                       AGENTFLOW_STATE_DIR=str(tmp_path / "runtime"))
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", probe, str(destination)],
                            cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    expected = native_resources.template_details("large-change")["input"]
    instructions = (native_resources.ROOT / "platform/templates/large-change/instructions.md").read_bytes()
    for copied in (installation / "templates/large-change", destination):
        assert json.loads((copied / "input.json").read_bytes()) == expected
        assert (copied / "instructions.md").read_bytes() == instructions

    existing = installation / "templates/large-change"
    (existing / "input.json").write_bytes(b'{"goal":"existing project input"}\n')
    (existing / "instructions.md").write_bytes(b"Existing project instructions.\n")
    before = {path: path.read_bytes() for path in (installation / "templates").rglob("*") if path.is_file()}
    preserved_copy = tmp_path / "preserved native copy"
    repeated = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", probe, str(preserved_copy)],
                              cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30)
    assert repeated.returncode == 0, repeated.stderr
    assert all(path.read_bytes() == raw for path, raw in before.items())
    for name in ("input.json", "instructions.md"):
        assert (preserved_copy / name).read_bytes() == (existing / name).read_bytes()


def test_installed_compiler_runs_outside_repository(tmp_path):
    shadow = tmp_path / "dev_platform"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("")
    (shadow / "portable.py").write_text("raise RuntimeError('project must not replace the compiler')")
    example = native_resources.ROOT / "platform/upstream/platform/portable/examples/repository-governance"
    package = native_resources.ROOT / "platform/upstream/platform/portable/packages/repository-governance/manifest.json"
    result = subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "compile", "--task", str(example / "task.json"),
         "--package", str(package), "--policy", str(example / "policy.json"),
         "--binding", str(example / "binding.json"), "--out", str(tmp_path / "compiled.json")],
        cwd=tmp_path, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    compiled = json.loads((tmp_path / "compiled.json").read_text())
    assert compiled["spec"]["request"]["task_type"] == "repository-governance"


def test_workflow_help_is_forwarded(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "--help"],
        cwd=tmp_path, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "compile" in result.stdout


def test_worker_bootstrap_loads_ergora_without_shadowing_native_dependencies(tmp_path, monkeypatch):
    control = tmp_path / 'control'
    package = control / 'ergora'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    worker = package / 'development/runtime'
    worker.mkdir(parents=True)
    (worker.parent / '__init__.py').write_text('')
    (worker / '__init__.py').write_text('')
    (worker / 'worker.py').write_text('def main(installation):\n import native_sdk_probe\n print(native_sdk_probe.origin)\n')
    (control / 'native_sdk_probe.py').write_text("origin = 'control-shadow'")
    native = tmp_path / 'native-libraries'
    native.mkdir()
    (native / 'native_sdk_probe.py').write_text("origin = 'native-selected'")
    monkeypatch.setattr(native_commands, 'IMPORT_ROOT', control)
    command = native_commands.worker_command(tmp_path / 'installation')
    result = subprocess.run([sys.executable, *command[1:]], env={**os.environ, 'PYTHONPATH': str(native)},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'native-selected'


def test_versioned_input_contract_imports_without_sdk_or_native_modules():
    package_parent = str(Path(ergora.__file__).parent.parent)
    script = ('import sys;sys.path.insert(0,' + repr(package_parent) + ');'
              'from ergora.development.inputs import execution_input,CompositionInput;'
              'selected=execution_input({"request": {"task_id": "offline"}});'
              'assert selected.task_queue("q")=="q";'
              'assert CompositionInput.task_queue("q")=="q.composition-v2";'
              'assert not any(n.split(".")[0] in ("temporalio","dev_platform","agent_platform") for n in sys.modules)')
    result = subprocess.run([sys.executable, '-I', '-S', '-c', script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(sys.platform != 'linux', reason='Budget worker uses the local Linux/WSL2 runtime')
def test_budget_worker_bootstrap_registers_its_actual_queue_adapter_and_native_activities(tmp_path):
    pytest.importorskip('temporalio')

    installation = tmp_path / 'installation with space'
    native_resources.prepare_training(installation, protocol=native_resources.TRAINING_PROTOCOL)
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(tmp_path / 'config'),
        AGENTFLOW_STATE_DIR=str(tmp_path / 'runtime'), PYTHONPATH=os.pathsep.join(map(str, (
            installation / 'local', installation / 'upstream/platform',
            installation / 'upstream/temporal', installation / 'upstream'))))
    probe = '''import asyncio,json,os,signal
from perf_temporal import connection
from temporalio import worker
async def connect(): return object()
class Probe:
    def __init__(self,client,**options):
        adapter=options['activities'][0].__self__.adapter
        print(json.dumps({'queue':options['task_queue'], 'adapter':type(adapter).__name__,
            'factory':os.environ['PERF_CLUSTER_ADAPTER'],
            'activities':[fn.__name__ for fn in options['activities']],
            'workflows':[wf.__name__ for wf in options['workflows']]}),flush=True)
    async def __aenter__(self):
        asyncio.get_running_loop().call_soon(os.kill,os.getpid(),signal.SIGTERM)
        return self
    async def __aexit__(self,*exc): pass
connection.connect=connect
worker.Worker=Probe
'''
    command = native_commands.training_budget_worker_command(installation)
    result = subprocess.run([*command[:-1], probe + command[-1]], env=environment,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    registered = json.loads(result.stdout)
    assert registered['queue'] == 'ergora-training-budget-v1'
    assert registered['adapter'] == 'BudgetAdapter'
    assert registered['factory'] == 'ergora.training.runtime.worker:create_adapter'
    assert registered['workflows'] == ['ExperimentWorkflow']
    assert 'submit_or_lookup' in registered['activities'] and 'cancel_exact_job' in registered['activities']


@pytest.fixture(scope='module')
def prepared_training_installation(tmp_path_factory):
    if sys.platform != 'linux':
        pytest.skip('Native source preparation uses Linux/WSL2 directory synchronization')
    root = tmp_path_factory.mktemp('native-source-parent') / 'training runtime with spaces'
    receipt = native_resources.prepare_training(root, protocol=native_resources.TRAINING_PROTOCOL)
    return root, receipt


def test_native_model_configuration_uses_backend_auth_and_only_selected_environment_refs(
        prepared_training_installation, tmp_path):
    import tomllib

    installation, _ = prepared_training_installation
    config = tmp_path / 'config'
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(tmp_path / 'runtime'),
                       HOME=str(tmp_path / 'home'), CODEX_HOME=str(tmp_path / 'codex-home'),
                       PYTHONDONTWRITEBYTECODE='1')
    for key in ('OPENAI_API_KEY', 'LINGZHI_API_KEY', 'ERGORA_FIXTURE_KEY'):
        environment.pop(key, None)

    def native(code):
        result = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys;sys.path.insert(0,' + repr(str(installation / 'local')) + ');' + code],
            env=environment, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    initialized = native('from agent_platform import setup;'
        'setup.install_commands=lambda:None;setup.supervisor_config=lambda:None;'
        'setup.shutil.which=lambda name:"/fixture/bin/"+name;setup.initialize();'
        'from agent_platform.core import settings;import json;print(json.dumps(settings()))')
    assert 'codex_env_key' not in initialized
    initial_model = tomllib.loads((config / 'codex.toml').read_text())
    assert initial_model['model'] == 'CONFIGURE_MODEL_BEFORE_USE' and 'model_provider' not in initial_model

    script = installation / 'bootstrap/configure-model.py'
    for arguments in ([], ['--base-url', 'https://provider.example/v1', '--env-key', 'ERGORA_TEST_API_REFERENCE'],
                      ['--base-url', 'https://provider.example/v1']):
        result = subprocess.run([sys.executable, '-B', str(script), '--model', 'backend-supported-model', *arguments],
                                env=environment, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)['authentication'] == 'not_checked'
        model = tomllib.loads((config / 'codex.toml').read_text())
        if not arguments:
            assert 'model_provider' not in model and 'model_providers' not in model
        else:
            provider = model['model_providers'][model['model_provider']]
            assert provider.get('env_key') == ('ERGORA_TEST_API_REFERENCE' if '--env-key' in arguments else None)
        assert (config / 'codex.toml').stat().st_mode & 0o077 == 0

    (config / 'codex.toml').write_text('''model = "backend-supported-model"
model_provider = "chosen"
[model_providers.chosen]
env_key = "ERGORA_TEST_API_REFERENCE"
env_http_headers = { "X-Token" = "ERGORA_TEST_HEADER_REFERENCE" }
[model_providers.other]
env_key = "ERGORA_TEST_UNSELECTED_REFERENCE"
''')
    environment.update(ERGORA_TEST_API_REFERENCE='synthetic-api-value', ERGORA_TEST_HEADER_REFERENCE='synthetic-header-value',
                       ERGORA_TEST_UNSELECTED_REFERENCE='synthetic-unselected-value', OPENAI_API_KEY='synthetic-ambient-value')
    names = native('from agent_platform.process_job import child_environment;import json;'
                   'print(json.dumps(sorted(child_environment("codex"))))')
    assert {'HOME', 'CODEX_HOME', 'ERGORA_TEST_API_REFERENCE', 'ERGORA_TEST_HEADER_REFERENCE'} <= set(names)
    assert not {'ERGORA_TEST_UNSELECTED_REFERENCE', 'OPENAI_API_KEY'} & set(names)
    model = (config / 'codex.toml').read_text().replace('env_key = "ERGORA_TEST_API_REFERENCE"',
        'env_key = "ERGORA_TEST_API_REFERENCE"\nrequires_openai_auth = true')
    (config / 'codex.toml').write_text(model)
    names = native('from agent_platform.process_job import child_environment;import json;'
                   'print(json.dumps(sorted(child_environment("codex"))))')
    assert 'ERGORA_TEST_API_REFERENCE' not in names and 'ERGORA_TEST_HEADER_REFERENCE' in names
    environment.pop('ERGORA_TEST_API_REFERENCE')
    names = native('from agent_platform.process_job import child_environment;import json;'
                   'print(json.dumps(sorted(child_environment("codex"))))')
    assert 'ERGORA_TEST_API_REFERENCE' not in names
    platform = json.loads((config / 'platform.json').read_text())
    platform['execution_enabled'] = True
    (config / 'platform.json').write_text(json.dumps(platform))
    doctor = native('from agent_platform import doctor;import contextlib,json;'
        'doctor.importlib.metadata.version=lambda name:"fixture";'
        'doctor.shutil.which=lambda name:"/fixture/bin/"+name;'
        'doctor.Sandbox.probe=lambda self:{"available":True};'
        'doctor.socket.create_connection=lambda *args,**kwargs:contextlib.nullcontext();'
        'doctor.projects=lambda:[{"name":"fixture"}];print(json.dumps(doctor.report()))')
    assert doctor['ready_for_real_tasks'] and doctor['checks']['codex-auth']['status'] == 'not_checked'
    assert 'local prerequisites' in doctor['readiness_scope']
    (config / 'codex.toml').unlink()
    names = native('from agent_platform.process_job import child_environment;import json;'
                   'print(json.dumps(sorted(child_environment("codex"))))')
    assert 'CODEX_HOME' in names and 'ERGORA_TEST_HEADER_REFERENCE' not in names
    for content in ('model_providers = "irrelevant"', 'model_provider = ["irrelevant"]',
                    'model_provider = "chosen"\n[model_providers]\nchosen = "irrelevant"',
                    'model_provider = "chosen"\n[model_providers.chosen]\nenv_key = ["irrelevant"]\nenv_http_headers = ["irrelevant"]',
                    'model_provider = "chosen"\n[model_providers.chosen]\nenv_http_headers = { "X-Token" = ["irrelevant"] }'):
        (config / 'codex.toml').write_text(content)
        names = native('from agent_platform.process_job import child_environment;import json;'
                       'print(json.dumps(sorted(child_environment("codex"))))')
        assert 'CODEX_HOME' in names and 'ERGORA_TEST_HEADER_REFERENCE' not in names
    (config / 'codex.toml').write_text('invalid = [')
    names = native('from agent_platform.process_job import child_environment;import json;'
                   'print(json.dumps(sorted(child_environment("codex"))))')
    assert 'CODEX_HOME' in names and 'ERGORA_TEST_HEADER_REFERENCE' not in names
    import ergora.agents.invocation as agents
    with pytest.raises(tomllib.TOMLDecodeError):
        agents.invoke({'tool': 'codex'}, 'inspector', 'unused', tmp_path, tmp_path / 'invalid-codex-output', 5,
                      codex_config=str(config / 'codex.toml'), codex_bin='/unavailable-fixture-codex')
    assert not (tmp_path / 'invalid-codex-output').exists()


def test_native_source_protocol_has_one_complete_training_identity(prepared_training_installation):
    root, receipt = prepared_training_installation
    assert native_resources.validate_installation(root, training=True) == root.resolve()
    assert native_resources.validate_installation(root) == root.resolve()
    assert receipt == {'status': 'source_prepared', 'protocol': native_resources.TRAINING_PROTOCOL,
        'installation': str(root.resolve()), 'dependencies_installed': False,
        'runtime_started': False, 'execution_authorized': False}
    assert not (root / '.venv').exists()
    assert (root / 'local/agent_platform/training_executor.py').read_bytes() == (
        native_resources.ROOT / 'platform/local/agent_platform/training_executor.py').read_bytes()


def test_source_capability_pins_complete_current_gate_and_offline_saved_shape(
        prepared_training_installation, tmp_path, monkeypatch):
    from copy import deepcopy
    import shutil
    import venv
    import ergora.training.execution_protocol as protocol

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    source, _ = prepared_training_installation
    root = tmp_path / 'source-capability'
    shutil.copytree(source, root)
    venv.EnvBuilder(with_pip=False).create(root / '.venv')
    cap = protocol.source_capability(root, {'original': 'ready'})
    assert {'training/configuration.py', 'training/runtime/setup.py', 'training/runtime/preparation.py',
            'data/schemas/training-cycle-v2.json', 'data/native-runtime/training-executor-admission-v3.json'} <= set(cap['gate_sources'])
    protocol.validate_sources(cap)
    owner = {'schema_version': 2, 'intent_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64,
        'pid': 1, 'start_ticks': '0', 'boot_id': '0' * 36, 'context_sha256': 'c' * 64,
        'execution_capability': cap}
    root.rename(root.with_name(root.name + '-unavailable'))
    assert protocol.owner_record(owner) == owner
    with pytest.raises(OSError):
        protocol.validate_sources(cap)
    root.with_name(root.name + '-unavailable').rename(root)
    for changed in ('missing', 'extra'):
        invalid = deepcopy(owner)
        item = invalid['execution_capability']
        if changed == 'missing':
            item['gate_sources'].pop('native/resources.py')
        else:
            item['gate_sources']['unexpected.py'] = '0' * 64
        assert protocol.owner_record(invalid) == invalid
        with pytest.raises(ValueError, match='source coverage'):
            protocol.validate_sources(item)
        path = tmp_path / ('current-' + changed + '.json')
        path.write_text(json.dumps(invalid))
        assert protocol.owner_active(path, invalid) is False
    stale = deepcopy(cap)
    stale['gate_sources']['native/resources.py'] = '0' * 64
    assert protocol.owner_record({**owner, 'execution_capability': stale})['execution_capability'] == stale
    with pytest.raises(ValueError, match='gate source changed'):
        protocol.validate_sources(stale)


def test_capability_birth_does_not_accept_a_descriptor_changed_after_validation(
        prepared_training_installation, tmp_path, monkeypatch):
    import shutil
    import ergora.training.execution_protocol as protocol

    source, _ = prepared_training_installation
    root = tmp_path / 'racing-descriptor'
    shutil.copytree(source, root)
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    original = native_resources.validate_installation

    def validate(installation, **kwargs):
        result = original(installation, **kwargs)
        with (root / 'ergora-native-runtime.json').open('ab') as stream:
            stream.write(b'\n')
        return result

    monkeypatch.setattr(native_resources, 'validate_installation', validate)
    with pytest.raises(ValueError, match='native runtime descriptor'):
        protocol.source_capability(root, {'original': 'ready'})


@pytest.mark.parametrize('changed', ['missing-descriptor', 'formatted-descriptor', 'truncated-descriptor', 'oversized-descriptor',
                                    'linked-descriptor', 'fifo-descriptor', 'executor', 'training', 'requirements'])
def test_native_source_identity_cannot_fall_back_or_accept_an_unverified_file(prepared_training_installation, tmp_path, changed):
    import shutil

    source, _ = prepared_training_installation
    root = tmp_path / 'changed-source'
    shutil.copytree(source, root)
    descriptor = root / 'ergora-native-runtime.json'
    if changed == 'missing-descriptor':
        descriptor.unlink()
    elif changed == 'formatted-descriptor':
        descriptor.write_text(json.dumps(json.loads(descriptor.read_bytes())))
    elif changed == 'truncated-descriptor':
        descriptor.write_bytes(descriptor.read_bytes()[:100])
    elif changed == 'oversized-descriptor':
        with descriptor.open('ab') as stream:
            stream.write(b' ' * 65_537)
    elif changed == 'linked-descriptor':
        descriptor.unlink()
        descriptor.symlink_to(source / 'ergora-native-runtime.json')
    elif changed == 'fifo-descriptor':
        descriptor.unlink()
        os.mkfifo(descriptor)
    elif changed in ('executor', 'training'):
        path = 'local/agent_platform/' + ('training_executor.py' if changed == 'executor' else 'training.py')
        (root / path).write_bytes((root / path).read_bytes() + b'\n')
    else:
        with (root / 'requirements.lock').open('ab') as stream:
            stream.write(b'\n')
    with pytest.raises(ValueError, match='runtime (identity|descriptor)'):
        native_resources.validate_installation(root, training=True)


def test_interrupted_source_preparation_declares_its_incomplete_identity(prepared_training_installation, tmp_path, monkeypatch):
    root = tmp_path / 'interrupted-source'

    copy = shutil.copy2
    def interrupted(source, destination):
        result = copy(source, destination)
        if Path(destination) == root / 'local/agent_platform/training_executor.py':
            raise OSError('Interrupted native source copy')
        return result

    monkeypatch.setattr(shutil, 'copy2', interrupted)
    with pytest.raises(OSError, match='Interrupted native source copy'):
        native_resources.prepare_training(root, protocol=native_resources.TRAINING_PROTOCOL)
    assert (root / 'ergora-native-runtime.json').read_bytes() == b''
    original = native_resources.ROOT / 'platform/local/agent_platform/training_executor.py'
    assert (root / 'local/agent_platform/training_executor.py').read_bytes() == original.read_bytes()
    with pytest.raises(ValueError, match='incomplete native runtime descriptor'):
        native_resources.validate_installation(root, training=True)


@pytest.mark.skipif(sys.platform != 'linux', reason='Native source preparation requires Linux/WSL2')
@pytest.mark.parametrize('protocol', native_resources.TRAINING_PROTOCOLS)
def test_cli_prepares_only_new_native_source_without_creating_control_state(tmp_path, protocol):
    root = tmp_path / 'cli source'
    control = tmp_path / 'unused-control'
    command = [sys.executable, '-B', '-m', 'ergora', '--home', str(control), 'reference', 'prepare-training',
               '--protocol', protocol, '--directory', str(root)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt['status'] == 'source_prepared' and receipt['installation'] == str(root.resolve())
    assert not receipt['runtime_started'] and not receipt['dependencies_installed'] and not receipt['execution_authorized']
    assert not control.exists() and not (root / '.venv').exists()
    before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    repeated = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert repeated.returncode != 0 and all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.skipif(sys.platform != 'linux', reason='CPU bootstrap uses Linux descriptor reads')
@pytest.mark.parametrize('source_fault', [
    None, 'omitted-nested', 'tampered-nested', 'omitted-initializer', 'omitted-paths'])
def test_cpu_bootstrap_checks_recursive_sources_before_import(tmp_path, source_fault):
    """Frozen synthetic lineage reaches only the selected wrapper's import marker."""
    import hashlib

    def raw(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

    def sha(value):
        return hashlib.sha256(raw(value)).hexdigest()

    def publish(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw(value))

    package = tmp_path / 'core/ergora'
    imported = tmp_path / 'wrapper-imported'
    files = {
        '__init__.py': b'', '_paths.py': b'', 'training/__init__.py': b'',
        'runtime/__init__.py': b'', 'runtime/processes.py': b'ORIGINAL = True\n',
        'training/configuration.py': (
            'from pathlib import Path\nPath(' + repr(str(imported)) + ").write_text('selected')\n").encode(),
    }
    native_name = 'data/reference/platform/local/agent_platform/process_job.py'
    files[native_name] = (native_resources.ROOT / 'platform/local/agent_platform/process_job.py').read_bytes()
    for name, content in files.items():
        path = package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    sources = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    omitted = {'omitted-nested': 'runtime/processes.py', 'omitted-initializer': 'training/__init__.py',
               'omitted-paths': '_paths.py'}.get(source_fault)
    if omitted is not None:
        del sources[omitted]
    if source_fault == 'tampered-nested':
        (package / 'runtime/processes.py').write_bytes(b'ORIGINAL = False\n')

    installation, runtime = tmp_path / 'native', tmp_path / 'state'
    descriptor = installation / 'ergora-native-runtime.json'
    publish(descriptor, {'synthetic': 'fixed-descriptor'})
    job = runtime / 'training/jobs/alpha'
    output = job / 'run-output'
    command = [sys.executable, str(package / 'training/configuration.py'), str(job / 'configuration-request.json')]
    runner = {'project': 'synthetic', 'repo': str(tmp_path / 'repo'), 'command': command,
              'configuration_readback': {'synthetic': True}}
    contract = {'kind': 'training-cpu-execution-contract', 'implementation': {
        'wrapper_entry': 'ergora.training.configuration:main', 'runner_sha256': sha(runner),
        'core_sources_sha256': sha(sources)}}
    contract['sha256'] = sha(contract)
    manifest = {'experiment_id': 'alpha', 'execution': {'cpu_contract': contract}}
    binding = {'experiment_id': 'alpha', 'manifest_sha': hashlib.sha256(raw(manifest)).hexdigest()}
    native = {'experiment': {'binding': binding}, 'runner': runner}
    intent = {'schema_version': 1, 'operation': 'start', 'experiment_id': 'alpha',
        'workflow_id': 'perf-experiment/alpha', 'project': runner['project'], 'repo': runner['repo'],
        'execution': {'state_directory': str(runtime)}, 'budget': {'authorization_sha256': 'a' * 64},
        'observation': {'experiment': {
            'experiment_id': 'alpha', 'spec': native['experiment'], 'binding': binding,
            'manifest': manifest, 'current_runner': runner}}}
    context = {'intent': intent, 'authorization': {'sha256': 'a' * 64}}
    owner = {'authorization_sha256': 'a' * 64, 'intent_sha256': sha(intent),
        'context_sha256': sha(context), 'execution_capability': {'installation': str(installation),
            'descriptor_sha256': hashlib.sha256(descriptor.read_bytes()).hexdigest()}}
    managed = {'kind': 'training-execution-request', 'experiment_id': 'alpha',
        'native_request_sha256': hashlib.sha256(raw(native)).hexdigest(), 'owner_sha256': sha(owner),
        'start_intent_sha256': sha(intent), 'authorization_sha256': 'a' * 64}
    configuration = {'binding': binding, 'output': str(output),
        'native_request_sha256': managed['native_request_sha256'],
        'managed': {'request_sha256': sha(managed)}, 'context': context, 'runner_sha256': sha(runner),
        'cpu_contract_core': {'package_directory': str(package), 'sources_sha256': sha(sources)}}
    preparation = {'schema_version': 2, 'experiment_id': 'alpha', 'project_revision': 1,
        'request': {'synthetic': True}, 'files': {'training/manifests/alpha.json': raw(manifest).decode()}}
    preparation['confirmed_preview_sha256'] = sha(preparation)
    preparation['confirmation'] = {'request_sha256': sha(preparation['request']), 'project_revision': 1}
    admission = {'preparation_intent_sha256': sha(preparation), 'manifest_sha256': binding['manifest_sha'],
        'contract_sha256': contract['sha256'], 'confirmed_preview_sha256': preparation['confirmed_preview_sha256'],
        'confirmation': preparation['confirmation']}
    for path, value in (
        (job / 'request.json', native), (runtime / 'training/manifests/alpha.json', manifest),
        (runtime / 'ergora/training-submissions/alpha.intent.json', intent),
        (runtime / 'ergora/training-submissions/alpha.budget/owner.json', owner),
        (job / 'managed-execution/request.json', managed), (job / 'configuration-request.json', configuration),
        (runtime / 'ergora/training-preparations/alpha.intent.json', preparation),
        (runtime / 'ergora/training-preparations/alpha.cpu-contract-admission.json', admission),
        (output / 'cpu-contract-admission.json', admission),
        (output / 'cpu-core-sources.json', {'package_directory': str(package), 'sources': sources,
            'contract_sha256': contract['sha256']}),
    ):
        publish(path, value)
    process_folder = runtime / 'processes/af-perf-alpha-run'
    script = '''import importlib.util,json,sys,types
from pathlib import Path
package,native_root,state,output,folder,command=json.loads(sys.argv[1])
core=types.ModuleType('agent_platform.core')
core.CONFIG=Path(native_root)/'config'
core.ROOT=Path(native_root)
core.STATE=Path(state)
core.UPSTREAM=Path(native_root)/'upstream'
def require(condition,message):
    if not condition: raise ValueError(message)
def forbidden(*args,**kwargs): raise AssertionError('Bootstrap reached an unrelated native effect')
core.require=require
core.environment=core.git=core.read=core.write=forbidden
parent=types.ModuleType('agent_platform')
parent.__path__=[]
sys.modules['agent_platform']=parent
sys.modules['agent_platform.core']=core
source=Path(package)/'data/reference/platform/local/agent_platform/process_job.py'
spec=importlib.util.spec_from_file_location('agent_platform.process_job',source)
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
selected=monitor._cpu_training_module(command,Path(output),Path(folder),{'name':Path(folder).name})
print(selected.__file__)
'''
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', script, json.dumps([
        str(package), str(installation), str(runtime), str(output), str(process_folder), command])],
        capture_output=True, text=True, timeout=10)
    if source_fault is None:
        assert result.returncode == 0, result.stderr
        assert Path(result.stdout.strip()) == package / 'training/configuration.py'
        assert imported.read_text() == 'selected'
    else:
        expected = ('Original CPU core source bytes changed' if source_fault == 'tampered-nested'
                    else 'CPU bootstrap package inventory changed')
        assert result.returncode != 0 and expected in result.stderr
        assert not imported.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native final admission uses Linux process locks')
def test_cpu_final_admission_follows_environment_log_and_stdin_io(tmp_path):
    source = native_resources.ROOT / 'platform/local/agent_platform/process_job.py'
    script = '''import importlib.util,json,sys,types
from pathlib import Path
source,root=map(Path,sys.argv[1:])
state=root/'state'
folder=state/'processes/synthetic'
output=root/'output'
protocol=root/'protocol'
folder.mkdir(parents=True)
protocol.mkdir()
(protocol/'prompt.txt').write_bytes(b'fixed synthetic input')
request={'name':'synthetic','output':str(output),'checkout':str(root), 'writable':True,
    'command':['unreachable-business-command'],'fence':None,'model':'codex','protocol':str(protocol),
    'policy':None,'timeout':5}
(folder/'request.json').write_text(json.dumps(request))
core=types.ModuleType('agent_platform.core')
core.CONFIG=root/'config'
core.ROOT=root
core.STATE=state
core.UPSTREAM=root/'upstream'
def require(condition,message):
    if not condition: raise ValueError(message)
def read(path): return json.loads(path.read_bytes())
def write(path,value): path.write_text(json.dumps(value))
def forbidden(*args,**kwargs): raise AssertionError('Unrelated native effect')
core.require,core.read,core.write=require,read,write
core.environment=core.git=forbidden
parent=types.ModuleType('agent_platform')
parent.__path__=[]
sys.modules['agent_platform']=parent
sys.modules['agent_platform.core']=core
spec=importlib.util.spec_from_file_location('agent_platform.process_job',source)
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
events=[]
original_open=Path.open
def opened(path,*args,**kwargs):
    result=original_open(path,*args,**kwargs)
    if path==output/'execution.log': events.append('log')
    if path==protocol/'prompt.txt': events.append('stdin')
    return result
Path.open=opened
def environment(model):
    assert model=='codex'
    events.append('environment')
    return {}
def denied(owned):
    assert owned=='fixed-original-context'
    assert events==['log','stdin','environment'],events
    events.append('admission')
    raise ValueError('fixed synthetic final denial')
def spawn(*args,**kwargs):
    events.append('business-popen')
    raise AssertionError('Final denial must prevent business Popen')
monitor._cpu_training_module=lambda *args: types.SimpleNamespace(
    cpu_process_context=lambda *args:'fixed-original-context',cpu_process_last_admission=denied)
monitor.child_environment=environment
monitor.subprocess.Popen=spawn
monitor.time.time=lambda:0
monitor.run(folder)
result=read(folder/'terminal.json')
assert result['returncode']==125 and result['detail']=='ValueError: fixed synthetic final denial',result
assert events[:4]==['log','stdin','environment','admission'] and 'business-popen' not in events,events
print(json.dumps({'events':events,'returncode':result['returncode']}))
'''
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', script, str(source), str(tmp_path)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed['returncode'] == 125 and 'business-popen' not in observed['events']
