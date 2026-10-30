from __future__ import annotations

import copy
from pathlib import Path

from dev_platform.contracts import canonical_sha, validate_task
from dev_platform.portable import CAPABILITIES, compile_task, load_package

from .core import CONFIG, STATE, UPSTREAM, git, project, read, require, slug, write


def check_task_type(name: str, task_type: str) -> None:
    policy = CONFIG / 'policies' / slug(name) / 'execution.json'
    if policy.exists():
        require(task_type in read(policy)['allowed_task_types'], 'This project policy does not enable task type ' + task_type)


def register(name: str, repo: Path, tracker: str, remote_project: str, paths: list[str], checks_file: Path | None) -> dict:
    slug(name)
    repo = repo.resolve()
    require(repo.is_dir(), "Repository directory is missing")
    require(Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve() == repo, "Use the repository root")
    checks = read(checks_file) if checks_file else {}
    require(isinstance(checks, dict), "Check configuration must be a JSON object of argv arrays")
    for command in checks.values():
        require(isinstance(command, list) and command and all(isinstance(x, str) and x for x in command), "Checks must use argv arrays")
    value = {"schema_version": 1, "name": name, "repo": str(repo), "tracker": {"kind": tracker, "project": remote_project},
             "base_sha": git(repo, "rev-parse", "HEAD").stdout.strip(), "allowed_paths": paths, "checks": checks}
    write(CONFIG / "projects" / f"{name}.json", value)
    policy_dir = CONFIG / "policies" / name
    write(policy_dir / "scope.json", {"schema_version": 1,
          "protected_paths": [".git", ".symphony", ".agent-control", ".agent-platform-private"],
          "max_changed_files": 200, "max_changed_lines": 20000})
    return value


def create_task(name: str, task_type: str, task_id: str, issue: str, input_file: Path, starting_sha: str | None = None) -> dict:
    p = project(name)
    task_id = slug(task_id)
    package = load_package(UPSTREAM / "platform/portable/packages" / task_type / "manifest.json")
    example_root = UPSTREAM / "platform/portable/examples" / task_type
    task = read(example_root / "task.json")
    task.update(task_id=task_id, project_id=name, package_sha256=canonical_sha(package), input=read(input_file),
                repository={"base_sha": p["base_sha"], "starting_sha": starting_sha or p["base_sha"]})
    policy = read(example_root / "policy.json")
    policy.update(policy_id=name + "-policy", project_id=name, package_sha256=task["package_sha256"],
                  tracker_scope=p["tracker"], base_sha=p["base_sha"], allowed_paths=p["allowed_paths"])
    binding = read(example_root / "binding.json")
    binding.update(binding_id=name + "-temporal", project_id=name, policy_sha256=canonical_sha(policy),
                   tracker={**p["tracker"], "issue_id": issue})
    compiled = compile_task(task, package, policy, binding)
    target = STATE / "tasks" / task_id
    for filename, value in (("task.json", task), ("policy.json", policy), ("binding.json", binding),
                            ("compiled.json", compiled), ("task.spec.json", compiled["spec"]), ("project.json", p)):
        write(target / filename, value)
    return {"task_id": task_id, "directory": str(target), "compiled_sha256": canonical_sha(compiled),
            "state": "COMPILED", "execution_started": False}
