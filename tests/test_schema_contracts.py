from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import agents, components, contracts, evaluation, projects, tools
from ergora.state import State


def test_shipped_schemas_are_valid_and_validation_does_not_supply_defaults():
    for component in components.COMPONENTS.values():
        contracts.StrictValidator.check_schema(component["configuration"])
    for schema in (contracts.EVALUATION_MANIFEST, contracts.EVALUATION_RESULT, agents.result_schema(["review"], True)):
        contracts.StrictValidator.check_schema(schema)
    binding = {"tool": "mini-swe-agent", "model": "provider/model"}
    before = deepcopy(binding)
    tools.validate_binding("implementer", binding)
    assert binding == before and "step_limit" not in binding


@pytest.mark.parametrize("value,accepted", [(1, True), (1000, True), (1.0, False), (True, False), (0, False),
                                          (1001, False), (10 ** 1000, False), (-10 ** 1000, False)])
def test_binding_keeps_python_strict_integer_limits(value, accepted):
    binding = {"tool": "mini-swe-agent", "model": "p/m", "step_limit": value}
    if accepted:
        tools.validate_binding("implementer", binding)
    else:
        with pytest.raises(ValueError, match=r"/step_limit:"):
            tools.validate_binding("implementer", binding)


@pytest.mark.parametrize("value", [True, "3", 0, -1, 100.01, float("nan"), float("inf"), -float("inf")])
def test_binding_rejects_non_numeric_nonfinite_and_out_of_budget_values(value):
    with pytest.raises(ValueError, match=r"/cost_limit:"):
        tools.validate_binding("implementer", {"tool": "mini-swe-agent", "model": "p/m", "cost_limit": value})


def test_structured_results_keep_strict_fields_and_show_json_pointer():
    schema = agents.result_schema(["review/report~v1"], True)
    valid = {"summary": "审查结果", "artifacts": {"review/report~v1": "证据"}, "decision": "approve"}
    before = deepcopy(valid)
    assert agents.validate_result(valid, schema) is valid and valid == before
    invalid = [
        ({**valid, "unexpected": "field"}, "/"),
        ({**valid, "summary": " \n\t"}, "/summary"),
        ({**valid, "artifacts": {"review/report~v1": " "}}, "/artifacts/review~1report~0v1"),
        ({**valid, "decision": "pass"}, "/decision"),
    ]
    for result, path in invalid:
        with pytest.raises(ValueError) as error:
            agents.validate_result(result, schema)
        assert f"at {path}:" in str(error.value)
    result = {"score": 0.5, "cost": 0, "passed": True, "feedback": "", "upstream_metadata": {"kept": True}}
    contracts.validate(result, contracts.EVALUATION_RESULT, "Evaluator result")
    for field, value in [("score", True), ("score", float("nan")), ("score", 1.1), ("cost", float("inf")),
                         ("cost", -1), ("cost", 10 ** 1000), ("passed", 1), ("feedback", None)]:
        with pytest.raises(ValueError, match=f"/{field}:"):
            contracts.validate({**result, field: value}, contracts.EVALUATION_RESULT, "Evaluator result")


@pytest.fixture
def contract_project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    state = State(tmp_path / "data")
    projects.create(state, "schema-demo", repo)
    scorer = repo / "evaluate.py"
    scorer.write_text('print(\'{"score": 0.5, "cost": 0, "passed": true, "feedback": "fixture"}\')\n', encoding="utf-8")
    manifest = {"schema_version": 1, "evaluator_argv": [sys.executable, str(scorer)], "evaluator_files": [str(scorer)],
                "timeout_seconds": 5, "minimum_gain": 0, "max_reported_cost": 1,
                "cases": [{"id": split, "split": split, "input": {"request": "比较结果"}} for split in ("train", "validation", "holdout")]}
    return state, manifest


def test_manifest_versions_and_domain_rules_survive_structural_validation(contract_project):
    state, manifest = contract_project
    for version in (1, 1.0, True):
        saved = evaluation.register(state, "schema-demo", {**manifest, "schema_version": version})
        assert type(saved["manifest"]["schema_version"]) is type(version)
    for changes, expected_path in [({"schema_version": 2}, "/schema_version"), ({"unexpected": True}, "/"),
                                    ({"timeout_seconds": True}, "/timeout_seconds"),
                                    ({"timeout_seconds": 5.0}, "/timeout_seconds"),
                                    ({"timeout_seconds": 10 ** 1000}, "/timeout_seconds"),
                                    ({"timeout_seconds": -10 ** 1000}, "/timeout_seconds"),
                                    ({"minimum_gain": float("nan")}, "/minimum_gain")]:
        with pytest.raises(ValueError) as error:
            evaluation.register(state, "schema-demo", {**manifest, **changes})
        assert f"at {expected_path}:" in str(error.value)
    for cases in [
        [{**case, "id": "duplicate"} for case in manifest["cases"]],
        [{**case, "split": "train"} for case in manifest["cases"]],
        [{**case, "id": "unsafe\n"} for case in manifest["cases"]],
    ]:
        with pytest.raises(ValueError):
            evaluation.register(state, "schema-demo", {**manifest, "cases": cases})


def test_cli_and_web_share_binding_and_evaluation_decisions_with_utf8_bom(contract_project, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    state, manifest = contract_project
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}

    def cli(arguments):
        return subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), *arguments],
                              capture_output=True, text=True, encoding="utf-8", timeout=10)

    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        binding_path = tmp_path / "binding.json"
        bindings = [
            ({"tool": "codex", "model": "模型/版本"}, True),
            ({"tool": "codex", "model": " "}, False),
            ({"tool": "codex", "unknown": "field"}, False),
            ({"tool": "command", "argv": ["bad\0argument"]}, False),
            ({"tool": "mini-swe-agent", "model": "p/m", "step_limit": 5.0}, False),
            ({"tool": "mini-swe-agent", "model": "p/m", "step_limit": 5}, True),
        ]
        for binding, accepted in bindings:
            binding_path.write_text(json.dumps(binding, ensure_ascii=False), encoding="utf-8-sig")
            result = cli(["project", "bind", "schema-demo", "implementer", "--binding", str(binding_path),
                          "--revision", str(state.project("schema-demo")["revision"])])
            response = client.put("/api/projects/schema-demo/bindings/implementer", json={
                "binding": binding, "revision": state.project("schema-demo")["revision"]})
            assert (result.returncode == 0) == accepted
            assert (response.status_code == 200) == accepted
            if accepted:
                assert json.loads(result.stdout)["bindings"]["implementer"] == response.json()["bindings"]["implementer"] == binding
            else:
                assert response.json()["error"] in result.stderr
        manifest_path = tmp_path / "evaluation.json"
        for changes, accepted in [({}, True), ({"schema_version": True}, True), ({"schema_version": 2}, False),
                                   ({"extra": "field"}, False), ({"timeout_seconds": 5.0}, False)]:
            value = {**manifest, **changes}
            manifest_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8-sig")
            result = cli(["evaluation", "register", "schema-demo", str(manifest_path)])
            response = client.post("/api/projects/schema-demo/evaluations/suites", json=value)
            assert (result.returncode == 0) == accepted
            assert (response.status_code == 200) == accepted
            if accepted:
                assert json.loads(result.stdout)["digest"] == response.json()["digest"]
            else:
                assert response.json()["error"] in result.stderr
        before = state.project("schema-demo")
        binding_path.write_bytes(b'{"tool":"codex","model":"\xff"}')
        rejected = cli(["project", "bind", "schema-demo", "implementer", "--binding", str(binding_path),
                        "--revision", str(before["revision"])])
        assert rejected.returncode == 2 and "utf-8" in rejected.stderr.lower()
        assert state.project("schema-demo") == before
