import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import reference


def test_public_reference_identity():
    assert reference.verify()["files"] == 283


def test_template_copy_preserves_files_and_existing_destination(tmp_path):
    for kind in reference.TEMPLATES:
        destination = tmp_path / kind
        reference.copy_template(kind, destination)
        source = reference.ROOT / "platform/templates" / kind
        assert (destination / "agent-contract.json").is_file()
        for file in source.rglob("*"):
            if file.is_file():
                assert file.read_bytes() == (destination / file.relative_to(source)).read_bytes()
        with pytest.raises(ValueError, match="preserve"):
            reference.copy_template(kind, destination)


def test_installed_compiler_runs_outside_repository(tmp_path):
    shadow = tmp_path / "dev_platform"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("")
    (shadow / "portable.py").write_text("raise RuntimeError('project must not replace the compiler')")
    example = reference.ROOT / "platform/upstream/platform/portable/examples/repository-governance"
    package = reference.ROOT / "platform/upstream/platform/portable/packages/repository-governance/manifest.json"
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
    (package / 'reference_worker.py').write_text('def main(installation):\n import native_sdk_probe\n print(native_sdk_probe.origin)\n')
    (control / 'native_sdk_probe.py').write_text("origin = 'control-shadow'")
    native = tmp_path / 'native-libraries'
    native.mkdir()
    (native / 'native_sdk_probe.py').write_text("origin = 'native-selected'")
    monkeypatch.setattr(reference, '__file__', str(package / 'reference.py'))
    command = reference.worker_command(tmp_path / 'installation')
    result = subprocess.run([sys.executable, *command[1:]], env={**os.environ, 'PYTHONPATH': str(native)},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'native-selected'


def test_versioned_input_contract_imports_without_sdk_or_native_modules():
    package_parent = str(Path(reference.__file__).parent.parent)
    script = ('import sys;sys.path.insert(0,' + repr(package_parent) + ');'
              'from ergora.reference_inputs import execution_input,CompositionInput;'
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
    reference.prepare_training(installation, protocol=reference.TRAINING_PROTOCOL)
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
    command = reference.training_budget_worker_command(installation)
    result = subprocess.run([*command[:-1], probe + command[-1]], env=environment,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    registered = json.loads(result.stdout)
    assert registered['queue'] == 'ergora-training-budget-v1'
    assert registered['adapter'] == 'BudgetAdapter'
    assert registered['factory'] == 'ergora.reference_training_worker:create_adapter'
    assert registered['workflows'] == ['ExperimentWorkflow']
    assert 'submit_or_lookup' in registered['activities'] and 'cancel_exact_job' in registered['activities']


@pytest.fixture(scope='module')
def prepared_training_installation(tmp_path_factory):
    if sys.platform != 'linux':
        pytest.skip('Native source preparation uses Linux/WSL2 directory synchronization')
    root = tmp_path_factory.mktemp('native-source-parent') / 'training runtime with spaces'
    receipt = reference.prepare_training(root, protocol=reference.TRAINING_PROTOCOL)
    return root, receipt


def test_native_source_protocol_has_one_complete_training_identity(prepared_training_installation):
    root, receipt = prepared_training_installation
    assert reference.validate_installation(root, training=True) == root.resolve()
    assert reference.validate_installation(root) == root.resolve()
    assert receipt == {'status': 'source_prepared', 'protocol': reference.TRAINING_PROTOCOL,
        'installation': str(root.resolve()), 'dependencies_installed': False,
        'runtime_started': False, 'execution_authorized': False}
    assert not (root / '.venv').exists()
    assert (root / 'local/agent_platform/training_executor.py').read_bytes() == (
        reference.ROOT / 'platform/local/agent_platform/training_executor.py').read_bytes()


def test_source_capability_pins_complete_current_gate_and_offline_saved_shape(
        prepared_training_installation, tmp_path, monkeypatch):
    from copy import deepcopy
    import shutil
    import venv
    from ergora import training_execution_protocol as protocol

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    source, _ = prepared_training_installation
    root = tmp_path / 'source-capability'
    shutil.copytree(source, root)
    venv.EnvBuilder(with_pip=False).create(root / '.venv')
    cap = protocol.source_capability(root, {'original': 'ready'})
    assert {'training_configuration.py', 'reference_training_setup.py', 'reference_training_preparation.py',
            'data/schemas/training-cycle-v1.json', 'data/native-runtime/training-executor-admission-v3.json'} <= set(cap['gate_sources'])
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
            item['gate_sources'].pop('reference.py')
        else:
            item['gate_sources']['unexpected.py'] = '0' * 64
        with pytest.raises(ValueError, match='execution capability'):
            protocol.owner_record(invalid)
    stale = deepcopy(cap)
    stale['gate_sources']['reference.py'] = '0' * 64
    assert protocol.owner_record({**owner, 'execution_capability': stale})['execution_capability'] == stale
    with pytest.raises(ValueError, match='gate source changed'):
        protocol.validate_sources(stale)


def test_capability_birth_does_not_accept_a_descriptor_changed_after_validation(
        prepared_training_installation, tmp_path, monkeypatch):
    import shutil
    from ergora import training_execution_protocol as protocol

    source, _ = prepared_training_installation
    root = tmp_path / 'racing-descriptor'
    shutil.copytree(source, root)
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    original = reference.validate_installation

    def validate(installation, **kwargs):
        result = original(installation, **kwargs)
        with (root / 'ergora-native-runtime.json').open('ab') as stream:
            stream.write(b'\n')
        return result

    monkeypatch.setattr(reference, 'validate_installation', validate)
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
        reference.validate_installation(root, training=True)


def test_interrupted_source_preparation_declares_its_incomplete_identity(prepared_training_installation, tmp_path, monkeypatch):
    root = tmp_path / 'interrupted-source'

    copy = reference.shutil.copy2
    def interrupted(source, destination):
        result = copy(source, destination)
        if Path(destination) == root / 'local/agent_platform/training_executor.py':
            raise OSError('Interrupted native source copy')
        return result

    monkeypatch.setattr(reference.shutil, 'copy2', interrupted)
    with pytest.raises(OSError, match='Interrupted native source copy'):
        reference.prepare_training(root, protocol=reference.TRAINING_PROTOCOL)
    assert (root / 'ergora-native-runtime.json').read_bytes() == b''
    original = reference.ROOT / 'platform/local/agent_platform/training_executor.py'
    assert (root / 'local/agent_platform/training_executor.py').read_bytes() == original.read_bytes()
    with pytest.raises(ValueError, match='incomplete native runtime descriptor'):
        reference.validate_installation(root, training=True)


@pytest.mark.skipif(sys.platform != 'linux', reason='Native source preparation requires Linux/WSL2')
@pytest.mark.parametrize('protocol', reference.TRAINING_PROTOCOLS)
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
