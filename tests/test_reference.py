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
    import shutil

    installation = tmp_path / 'installation with space'
    shutil.copytree(reference.ROOT / 'platform', installation)
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
