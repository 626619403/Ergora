"""Portable development contracts compiled into the immutable development-v1 engine.

Only compile_task consults the installed registry. validate_compiled uses frozen
snapshots, so an in-flight run is not reinterpreted after an upgrade. This is a
project-specific interchange contract, not an A2A/Open Workflow standard.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import stat

from .contracts import (ContractError, ROLES, STAGES, TEMPLATE_FILES, canonical_sha,
    need, path_contains, paths_overlap, validate_profile, validate_spec, validate_task,
    _object, _slug, _integer, _paths, _strings, SHA256, COMMIT)

ROOT = Path(__file__).resolve().parent.parent / "portable"
RUNTIME = "temporal-development-v1"
CAPABILITIES = (
    "immutable-input", "durable-recovery", "dag-work-units", "human-plan-approval",
    "candidate-bound-evidence", "independent-verification", "independent-review",
    "cooperative-cancel-fence", "review-ready-only",
)
ROLE_CAPABILITIES = {
    "inspector": ["repository-read", "baseline-inspection"],
    "planner": ["repository-read", "plan-write"],
    "implementer": ["scoped-code-write", "test-execution"],
    "integrator": ["candidate-integration"],
    "verifier": ["trusted-ci-verification"],
    "reviewer": ["independent-candidate-review"],
}
ROLE_KINDS = {key: (["ci"] if key == "verifier" else ["agent", "human"]) for key in ROLE_CAPABILITIES}
STAGE_GRAPH = [
    {"id": "inventory", "role": "inspector", "depends_on": []},
    {"id": "plan", "role": "planner", "depends_on": ["inventory"]},
    {"id": "work", "role": "implementer", "depends_on": ["plan"]},
    {"id": "integrate", "role": "integrator", "depends_on": ["work"]},
    {"id": "verify", "role": "verifier", "depends_on": ["integrate"]},
    {"id": "review", "role": "reviewer", "depends_on": ["verify"]},
]
COMPONENT_NAMES = ("workflow", "roles", "evidence", *TEMPLATE_FILES)
MAX_FILE = 1_048_576
MAX_COMPILED = 524_288


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, "Duplicate JSON member: " + key)
        out[key] = value
    return out


def loads(raw):
    """Strict JSON: reject duplicate keys, non-finite numbers and invalid UTF-8."""
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        need(type(raw) is str and len(raw.encode("utf-8")) <= MAX_FILE, "JSON exceeds 1 MiB")
        value = json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ContractError("Non-finite JSON number")))
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            need(depth <= 64, "JSON nesting exceeds 64 levels")
            if type(item) is dict:
                for key, child in item.items():
                    key.encode("utf-8")
                    pending.append((child, depth + 1))
            elif type(item) is list:
                pending.extend((child, depth + 1) for child in item)
            elif type(item) is str:
                item.encode("utf-8")
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ContractError("Invalid UTF-8 JSON") from error


def read_json(path):
    return loads(_read_bytes(Path(path)))


def _read_bytes(path):
    # Trusted installations must be read-only; checks do not defeat a hostile
    # concurrent directory owner swapping ancestors after this preflight.
    path = Path(path).absolute()
    need(not any(p.is_symlink() for p in [path, *path.parents]), "Symlinked contract path is forbidden")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Contract must be a regular file")
        raw = stream.read(MAX_FILE + 1)
    need(len(raw) <= MAX_FILE, "Contract exceeds 1 MiB")
    return raw


def _version(value, keys, label):
    _object(value, ("schema_version", *keys), label)
    need(type(value["schema_version"]) is int and value["schema_version"] == 1, "Unsupported " + label + " schema")


def _digest(value, label):
    need(type(value) is str and SHA256.fullmatch(value), "Invalid SHA256: " + label)


def _component_digest(name, value):
    return canonical_sha(value) if name in ("workflow", "roles", "evidence") else hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_package(package):
    _object(package, ("manifest", "workflow", "roles", "evidence", "templates"), "package snapshot")
    m = package["manifest"]
    _version(m, ("package_id", "task_type", "task_version", "title", "legacy_profile_sha256", "components"), "package manifest")
    _slug(m["package_id"], "package_id"); _slug(m["task_type"], "task_type")
    _integer(m["task_version"], 1, 1000000, "task_version")
    need(type(m["title"]) is str and 0 < len(m["title"]) <= 200, "Invalid package title")
    _digest(m["legacy_profile_sha256"], "legacy_profile_sha256")
    _object(m["components"], COMPONENT_NAMES, "component references")
    _object(package["templates"], TEMPLATE_FILES, "template snapshots")
    for name, ref in m["components"].items():
        _object(ref, ("path", "sha256"), "component reference")
        _paths([ref["path"]], "component path")
        _digest(ref["sha256"], "component sha256")
        value = package[name] if name in ("workflow", "roles", "evidence") else package["templates"][name]
        if name in TEMPLATE_FILES:
            need(type(value) is str and len(value.encode("utf-8")) <= MAX_FILE, "Template must be bounded UTF-8 text")
        need(_component_digest(name, value) == ref["sha256"], "Component digest mismatch: " + name)
    w = package["workflow"]
    _version(w, ("workflow_id", "workflow_version", "stages", "work_units", "human_gates", "terminal",
                 "limits", "stage_timeout_seconds", "approval_timeout_seconds", "poll_seconds"), "workflow")
    need(w["workflow_id"] == "development-lifecycle" and type(w["workflow_version"]) is int and w["workflow_version"] == 1,
         "Workflow semantics are not implemented by this compiler")
    need(w["stages"] == STAGE_GRAPH and w["work_units"] == "dependency-dag" and
         w["human_gates"] == ["plan", "merge"] and w["terminal"] == "REVIEW_READY", "Unsupported workflow topology/gates")
    roles = package["roles"]
    _version(roles, ("roles",), "roles")
    _object(roles["roles"], ROLE_CAPABILITIES, "role definitions")
    for role, caps in ROLE_CAPABILITIES.items():
        value = roles["roles"][role]
        _object(value, ("capabilities", "actor_kinds", "forbidden_actions", "independent_from"), "role")
        need(value["capabilities"] == caps and value["actor_kinds"] == ROLE_KINDS[role], "Unsupported role capabilities")
        need(value["forbidden_actions"] == ["approve-own-plan", "merge", "deploy", "change-trusted-policy"], "Role restrictions were weakened")
        expected = ["authors"] if role in ("verifier", "reviewer") else []
        need(value["independent_from"] == expected, "Role independence was weakened")
    e = package["evidence"]
    _version(e, ("evidence_id", "required_checks", "artifacts_by_stage", "protected_paths", "required_capabilities"), "evidence")
    need(e["evidence_id"] == "candidate-evidence-v1", "Unsupported evidence semantics")
    _strings(e["required_capabilities"], "required capabilities", 1)
    need(set(CAPABILITIES) <= set(e["required_capabilities"]), "Evidence omits required guarantees")
    # Reuse all existing semantic constraints (types, bounds, required artifacts,
    # protected paths), without reading a newer registry during recovery.
    profile = _profile(package)
    validate_profile(profile)
    need(canonical_sha(profile) == m["legacy_profile_sha256"], "Package cannot reproduce pinned legacy profile")
    for name in ("input.schema.json", "output.schema.json"):
        schema = loads(package["templates"][name])
        need(type(schema) is dict and schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "Unsupported template schema dialect")
    return package


def _profile(package):
    m, w, e = package["manifest"], package["workflow"], package["evidence"]
    return {"schema_version": 1, "task_type": m["task_type"], "task_version": m["task_version"],
        "engine": "development-v1", "title": m["title"], "required_checks": e["required_checks"],
        "limits": w["limits"], "stage_timeout_seconds": w["stage_timeout_seconds"],
        "approval_timeout_seconds": w["approval_timeout_seconds"], "poll_seconds": w["poll_seconds"],
        "artifacts_by_stage": e["artifacts_by_stage"], "roles": dict(ROLES),
        "protected_paths": e["protected_paths"],
        "template_files": {name: m["components"][name]["sha256"] for name in TEMPLATE_FILES}}


def load_package(path):
    """Load a trusted manifest and local hash-pinned files; never fetch URLs."""
    path = Path(path).absolute()
    manifest = read_json(path)
    _version(manifest, ("package_id", "task_type", "task_version", "title", "legacy_profile_sha256", "components"), "package manifest")
    _object(manifest["components"], COMPONENT_NAMES, "component references")
    snapshot = {"manifest": manifest, "templates": {}}
    for name, ref in manifest["components"].items():
        _object(ref, ("path", "sha256"), "component reference")
        _paths([ref["path"]], "component path")
        component_path = path.parent / ref["path"]
        raw = _read_bytes(component_path)
        if name in TEMPLATE_FILES:
            try: snapshot["templates"][name] = raw.decode("utf-8")
            except UnicodeError as error: raise ContractError("Template is not UTF-8") from error
        else:
            snapshot[name] = loads(raw)
    return validate_package(snapshot)


def _prepare(task, package, policy, binding):
    validate_package(package)
    _version(task, ("task_id", "task_type", "task_version", "project_id", "package_sha256", "repository", "input"), "portable task")
    _slug(task["project_id"], "project_id")
    need(task["package_sha256"] == canonical_sha(package), "Task package pin mismatch")
    m = package["manifest"]
    need(task["task_type"] == m["task_type"] and task["task_version"] == m["task_version"], "Task/package identity mismatch")
    _version(policy, ("policy_id", "revision", "project_id", "package_sha256", "tracker_scope", "base_sha", "allowed_paths",
                      "protected_paths", "allowed_risks", "max_work_units", "max_parallel_units", "required_checks", "required_capabilities"), "project policy")
    _slug(policy["policy_id"], "policy_id"); _integer(policy["revision"], 1, 1000000, "policy revision")
    need(policy["project_id"] == task["project_id"], "Policy project mismatch")
    need(policy["package_sha256"] == task["package_sha256"], "Policy package pin mismatch")
    _object(policy["tracker_scope"], ("kind", "project"), "tracker scope")
    need(type(policy["base_sha"]) is str and COMMIT.fullmatch(policy["base_sha"]), "Policy needs full baseline commit")
    _paths(policy["allowed_paths"], "policy allowed paths")
    _paths(policy["protected_paths"], "policy protected paths", allow_reserved=True)
    need(type(policy["allowed_risks"]) is list and bool(policy["allowed_risks"]) and
         set(policy["allowed_risks"]) <= {"standard", "high"} and len(set(policy["allowed_risks"])) == len(policy["allowed_risks"]), "Invalid allowed risks")
    _integer(policy["max_work_units"], 1, 24, "policy max work units")
    _integer(policy["max_parallel_units"], 1, 8, "policy max parallel units")
    _strings(policy["required_checks"], "policy checks", 1)
    _strings(policy["required_capabilities"], "policy capabilities", 1)
    _version(binding, ("binding_id", "project_id", "policy_sha256", "runtime", "tracker"), "runtime binding")
    _slug(binding["binding_id"], "binding_id")
    need(binding["project_id"] == task["project_id"], "Binding project mismatch")
    need(binding["policy_sha256"] == canonical_sha(policy), "Binding policy pin mismatch")
    runtime = binding["runtime"]
    _object(runtime, ("kind", "executor_protocol", "capabilities", "max_parallel_units"), "runtime")
    need(runtime["kind"] == RUNTIME and runtime["executor_protocol"] == "trusted-file-v1", "No compiler for requested runtime/executor protocol")
    _strings(runtime["capabilities"], "runtime capabilities", 1)
    need(set(runtime["capabilities"]) <= set(CAPABILITIES), "Runtime claims an unsupported capability")
    _integer(runtime["max_parallel_units"], 1, 8, "runtime parallel capacity")
    _object(binding["tracker"], ("kind", "project", "issue_id"), "tracker binding")
    need({k: binding["tracker"][k] for k in ("kind", "project")} == policy["tracker_scope"], "Tracker is outside project policy")
    request = {"schema_version": 2, "task_type": task["task_type"], "task_version": task["task_version"],
        "task_id": task["task_id"], "profile_sha256": m["legacy_profile_sha256"],
        "tracker": copy.deepcopy(binding["tracker"]), "repository": copy.deepcopy(task["repository"]), "input": copy.deepcopy(task["input"])}
    validate_task(request)
    profile = _profile(package)
    spec = validate_spec({"request": request, "profile": profile, "request_sha256": canonical_sha(request), "profile_sha256": canonical_sha(profile)})
    inp = task["input"]; evidence = package["evidence"]
    need(task["repository"]["base_sha"] == policy["base_sha"], "Baseline commit is outside project policy")
    need(inp["risk"] in policy["allowed_risks"], "Task risk is not allowed by policy")
    need(len(inp["work_units"]) <= policy["max_work_units"], "Task exceeds project work unit limit")
    need(profile["limits"]["max_parallel_units"] <= min(policy["max_parallel_units"], runtime["max_parallel_units"]), "Workflow concurrency exceeds project/runtime capacity")
    need(set(policy["required_checks"]) <= set(evidence["required_checks"]), "Package omits project required checks")
    required = set(evidence["required_capabilities"]) | set(policy["required_capabilities"])
    need(required <= set(runtime["capabilities"]), "Runtime lacks mandatory capability")
    for path in inp["allowed_paths"]:
        need(any(path_contains(prefix, path) for prefix in policy["allowed_paths"]), "Task widens project allowed paths")
        need(not any(paths_overlap(path, p) for p in policy["protected_paths"]), "Task overlaps project protected paths")
    need(set(evidence["protected_paths"]) <= set(policy["protected_paths"]), "Project policy omits package protected paths")
    return spec


def compile_task(task, package, policy, binding):
    """Trusted admission-time compilation; caller must authenticate these configs."""
    from .registry import load_profile
    spec = _prepare(task, package, policy, binding)
    need(spec["profile"] == load_profile(task["task_type"], task["task_version"]), "Package is not the installed trusted profile")
    parts = {"task": task, "package": package, "policy": policy, "binding": binding}
    result = {"schema_version": 1, **copy.deepcopy(parts), "digests": {key: canonical_sha(value) for key, value in parts.items()}, "spec": copy.deepcopy(spec)}
    return validate_compiled(result)


def validate_compiled(value):
    """Validate frozen shape, all pins and semantics, without live registry I/O.

    Hashes establish integrity, NOT authority. The gateway admits the exact hash
    using a trusted principal/config; an attacker can author a self-consistent
    envelope. Never treat this function alone as an authorization decision.
    """
    _version(value, ("task", "package", "policy", "binding", "digests", "spec"), "compiled contract")
    _object(value["digests"], ("task", "package", "policy", "binding"), "compiled digests")
    for key in value["digests"]:
        need(value["digests"][key] == canonical_sha(value[key]), "Compiled digest mismatch: " + key)
    expected = _prepare(value["task"], value["package"], value["policy"], value["binding"])
    need(value["spec"] == expected, "Compiled legacy spec differs from portable inputs")
    need(len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode()) <= MAX_COMPILED, "Compiled contract exceeds 512 KiB")
    return value


def convert_v2(request, project_id="demo-project"):
    """Lossless legacy conversion. Generated policy/binding are reviewable drafts.

    It does NOT authorize a runtime start, and does NOT change existing history.
    """
    from .registry import make_spec
    original = make_spec(request)
    package = load_package(ROOT / "packages" / request["task_type"] / "manifest.json")
    profile = original["profile"]
    task = {"schema_version": 1, "task_id": request["task_id"], "task_type": request["task_type"],
            "task_version": request["task_version"], "project_id": project_id, "package_sha256": canonical_sha(package),
            "repository": copy.deepcopy(request["repository"]), "input": copy.deepcopy(request["input"])}
    policy = {"schema_version": 1, "policy_id": project_id + "-policy", "revision": 1, "project_id": project_id,
              "package_sha256": canonical_sha(package), "tracker_scope": {k: request["tracker"][k] for k in ("kind", "project")},
              "base_sha": request["repository"]["base_sha"], "allowed_paths": copy.deepcopy(request["input"]["allowed_paths"]),
              "protected_paths": copy.deepcopy(profile["protected_paths"]), "allowed_risks": [request["input"]["risk"]],
              "max_work_units": profile["limits"]["max_work_units"], "max_parallel_units": profile["limits"]["max_parallel_units"],
              "required_checks": copy.deepcopy(profile["required_checks"]), "required_capabilities": list(CAPABILITIES)}
    binding = {"schema_version": 1, "binding_id": project_id + "-temporal", "project_id": project_id,
               "policy_sha256": canonical_sha(policy), "runtime": {"kind": RUNTIME, "executor_protocol": "trusted-file-v1",
               "capabilities": list(CAPABILITIES), "max_parallel_units": profile["limits"]["max_parallel_units"]},
               "tracker": copy.deepcopy(request["tracker"])}
    compiled = compile_task(task, package, policy, binding)
    need(compiled["spec"] == original, "Legacy conversion was not lossless")
    return compiled


def main():
    p = argparse.ArgumentParser(description="Portable contracts: validation and compilation only")
    sub = p.add_subparsers(dest="action", required=True)
    c = sub.add_parser("compile")
    for field in ("task", "package", "policy", "binding", "out"):
        c.add_argument("--" + field, required=True)
    c.add_argument("--spec-out", help="Optional legacy runtime spec, immutable publication")
    v = sub.add_parser("convert-v2"); v.add_argument("--request", required=True); v.add_argument("--out-dir", required=True)
    v.add_argument("--project-id", default="demo-project")
    verify = sub.add_parser("validate"); verify.add_argument("compiled")
    export = sub.add_parser("export-v2"); export.add_argument("--compiled", required=True); export.add_argument("--out", required=True)
    a = p.parse_args()
    from .adapter import publish
    if a.action == "validate":
        compiled = validate_compiled(read_json(a.compiled))
    elif a.action == "export-v2":
        compiled = validate_compiled(read_json(a.compiled))
        publish(Path(a.out), compiled["spec"]["request"])
    elif a.action == "compile":
        compiled = compile_task(read_json(a.task), load_package(a.package), read_json(a.policy), read_json(a.binding))
        publish(Path(a.out), compiled)
        if a.spec_out: publish(Path(a.spec_out), compiled["spec"])
    else:
        compiled = convert_v2(read_json(a.request), a.project_id)
        root = Path(a.out_dir)
        need(not root.exists(), "Conversion destination already exists; use a new revision directory")
        root.mkdir(parents=True)
        for key in ("task", "policy", "binding"):
            publish(root / (key + ".json"), compiled[key])
        publish(root / "compiled.json", compiled)
        publish(root / "task.spec.json", compiled["spec"])
    print(json.dumps({"status": "VALIDATED_ONLY", "task_id": compiled["task"]["task_id"],
                      "compiled_sha256": canonical_sha(compiled), "request_sha256": compiled["spec"]["request_sha256"]}))


if __name__ == "__main__":
    try: main()
    except (OSError, ValueError, KeyError, TypeError) as error: raise SystemExit("BLOCKED: " + str(error))
