from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agents, components, projects, reference, tools
from ergora.state import State


def test_catalog_preserves_legacy_fields_and_returns_isolated_descriptions():
    baseline = json.loads((Path(__file__).parent / "fixtures/components-v0_2_0.json").read_text(encoding="utf-8"))["catalog"]
    catalog = tools.catalog()
    assert list(catalog) == list(baseline)
    for layer, expected in baseline.items():
        assert [{key: entry[key] for key in expected[index]} for index, entry in enumerate(catalog[layer])] == expected
    catalog["implementer"][0]["configuration"]["properties"]["model"]["title"] = "changed"
    catalog["implementer"][0]["capabilities"].clear()
    catalog["implementer"][0]["installation"]["url"] = "changed"
    fresh = tools.catalog()["implementer"][0]
    assert fresh["configuration"]["properties"]["model"]["title"] != "changed"
    assert "scoped-code-write" in fresh["capabilities"]
    assert fresh["installation"]["url"] != "changed"


def test_binding_matrix_preserves_acceptance_and_rejection():
    fixture_root = Path(__file__).resolve().parent
    valid = {
        "codex": [{"tool": "codex"}, {"tool": "codex", "model": "provider/model", "sandbox": "current-container"}],
        "claude-code": [{"tool": "claude-code", "model": "provider/model"}],
        "mini-swe-agent": [{"tool": "mini-swe-agent", "model": "provider/model", "python": sys.executable, "step_limit": 1, "cost_limit": 0.1}],
        "command": [{"tool": "command", "argv": [sys.executable, "-c", "print('ready')"]}],
        "sqlite": [{"tool": "sqlite"}], "manual": [{"tool": "manual"}], "urls": [{"tool": "urls"}],
        "reme": [{"tool": "reme", "endpoint": "https://example.org/memory", "token_env": "REME_TOKEN"}],
        "gepa": [{"tool": "gepa", "proposer_argv": [sys.executable, "propose.py"]}],
        "temporal": [{"tool": "temporal", "address": "localhost:7233", "namespace": "default", "task_queue": "demo"}],
        "forgekernel": [{"tool": "forgekernel", "checkout": str(fixture_root / "forge"),
                          "python": sys.executable, "task": str(fixture_root / "forge/task")}],
    }
    for layer, choices in tools.CATALOG.items():
        for tool in choices:
            for binding in valid[tool]:
                tools.validate_binding(layer, binding)
                with pytest.raises(ValueError):
                    tools.validate_binding(layer, {**binding, "unknown_option": True})
        for tool in set(valid) - set(choices):
            with pytest.raises(ValueError):
                tools.validate_binding(layer, valid[tool][0])
    invalid = [
        ("implementer", {"tool": "codex", "sandbox": "danger-full-access"}),
        ("reviewer", {"tool": "claude-code", "model": " "}),
        ("implementer", {"tool": "mini-swe-agent"}),
        ("implementer", {"tool": "mini-swe-agent", "model": "p/m", "step_limit": True}),
        ("implementer", {"tool": "mini-swe-agent", "model": "p/m", "cost_limit": 0}),
        ("reviewer", {"tool": "command", "argv": []}),
        ("reviewer", {"tool": "command", "argv": ["bad\0arg"]}),
        ("reviewer", {"tool": "command", "argv": ["tool"], "protocol": "unknown"}),
        ("reviewer", {"tool": "command", "argv": ["tool"], "protocol": "stage-json-v1", "capabilities": []}),
        ("memory", {"tool": "reme", "endpoint": "https://user:pass@example.org"}),
        ("memory", {"tool": "reme", "endpoint": "https://example.org", "token_env": "bad-name"}),
        ("optimizer", {"tool": "gepa", "proposer_argv": ["bad\0arg"]}),
        ("scheduler", {"tool": "temporal", "address": "localhost:7233", "namespace": "default"}),
        ("kernel", {"tool": "forgekernel", "checkout": "/forge", "python": "/python"}),
    ]
    for layer, binding in invalid:
        with pytest.raises(ValueError):
            tools.validate_binding(layer, binding)


def test_new_project_defaults_do_not_rewrite_existing_projects(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    before = projects.create(state, "before", repo)
    expected = {**{role: {"tool": "codex"} for role in agents.ROLE_CAPABILITIES},
                "memory": {"tool": "sqlite"}, "optimizer": {"tool": "manual"}, "research": {"tool": "urls"},
                "scheduler": {"tool": "manual"}, "kernel": {"tool": "manual"}}
    assert before["bindings"] == expected
    before["bindings"]["reviewer"]["tool"] = "claude-code"
    assert projects.create(state, "second", repo)["bindings"] == expected
    monkeypatch.setitem(components.DEFAULT_BINDINGS, "reviewer", {"tool": "claude-code"})
    assert projects.create(state, "after", repo)["bindings"]["reviewer"] == {"tool": "claude-code"}
    assert State(state.root).project("before")["bindings"] == expected


def test_platform_form_defaults_do_not_mutate_binding_contracts():
    windows = components.configuration("reviewer", "command", "win32")
    assert windows["properties"]["argv"]["default"] == ["python.exe", "C:\\path\\to\\tool.py"]
    assert windows["properties"]["capabilities"]["default"] == ["independent-candidate-review"]
    windows["properties"]["argv"]["default"].clear()
    linux = components.configuration("reviewer", "command", "linux")
    assert linux["properties"]["argv"]["default"] == ["python3", "/path/to/tool.py"]
    assert "current-container" in components.configuration("reviewer", "codex", "linux")["properties"]["sandbox"]["enum"]
    assert "current-container" not in components.configuration("reviewer", "codex", "win32")["properties"]["sandbox"]["enum"]
    tools.validate_binding("reviewer", {"tool": "codex", "sandbox": "current-container"})


def test_added_command_component_runs_template_without_vendor_branches(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    contract = reference.agent_contract("training-optimization")
    package = tmp_path / "extended" / "ergora"
    shutil.copytree(Path(components.__file__).parent, package, ignore=shutil.ignore_patterns("__pycache__"))
    manifest_path = package / "data/components.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    description = deepcopy(manifest["components"]["command"])
    description["configuration"]["properties"]["tool"]["const"] = "fixture-harness"
    manifest["components"]["fixture-harness"] = description
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    program = '''
import json, sys
from pathlib import Path
from ergora import projects, reference, tools
from ergora.state import State
state = State(Path(sys.argv[1]))
projects.create(state, 'demo', Path(sys.argv[2]))
binding = {'tool': 'fixture-harness', 'argv': [sys.executable, sys.argv[3]],
           'protocol': 'stage-json-v1', 'capabilities': ['experiment-design']}
projects.bind(state, 'demo', 'experiment-planner', binding, 1)
run = tools.run_agent(state, 'demo', 'experiment-planner', 'Propose', template='training-optimization')
print(json.dumps({'run': run, 'catalog': tools.catalog()['experiment-planner'],
                 'doctor': tools.doctor(state, 'demo'), 'contract': reference.agent_contract('training-optimization')}))
'''
    invoked = subprocess.run([sys.executable, "-c", program, str(tmp_path / "data"), str(repo),
                              str(Path(__file__).parent / "fixtures/stage_agent.py")],
                             env=dict(os.environ, PYTHONPATH=str(package.parent)), capture_output=True, text=True, timeout=15)
    assert invoked.returncode == 0, invoked.stderr
    observed = json.loads(invoked.stdout)
    assert observed["run"]["status"] == "succeeded"
    result = json.loads(Path(observed["run"]["result"]).read_text(encoding="utf-8"))
    assert set(result["artifacts"]) == {"hypothesis", "experiment-proposal"}
    assert observed["catalog"][-1]["tool"] == "fixture-harness"
    assert observed["catalog"][-1]["configuration"]["properties"]["argv"]["type"] == "array"
    check = next(item for item in observed["doctor"]["checks"] if item["layer"] == "experiment-planner")
    assert check["installed"] is True
    assert observed["contract"] == contract
    assert reference.agent_contract("training-optimization") == contract


def test_cli_works_when_optional_sdks_are_unavailable(tmp_path):
    program = '''
import importlib.abc, sys
class AbsentSDKs(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'fastapi', 'gepa', 'temporalio', 'minisweagent'}:
            raise ImportError('optional SDK deliberately unavailable')
sys.meta_path.insert(0, AbsentSDKs())
from ergora.cli import main
raise SystemExit(main(['--home', sys.argv[1], 'templates', 'list']))
'''
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path / "data")], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)["templates"]) == {"repository-governance", "large-change", "training-optimization"}
