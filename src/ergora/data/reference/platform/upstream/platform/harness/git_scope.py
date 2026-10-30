#!/usr/bin/env python3
"""Verify a final, exact Git commit against trusted task and project scope.

Only Git's built-in object/diff operations run. Candidate scripts, hooks,
external diffs and textconv filters are not executed. This is a scope gate,
not a behavioral or remote-repository-identity verifier.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dev_platform.contracts import (COMMIT, RESERVED_PATHS, canonical_sha,
                                    path_contains, validate_spec)


class ScopeError(ValueError):
    pass


def need(value, message):
    if not value:
        raise ScopeError(message)


def read_json(path):
    p = Path(path)
    need(p.is_file() and not p.is_symlink(), "Expected a regular, non-symlink JSON file")
    need(p.stat().st_size <= 4 * 1024 * 1024, "JSON exceeds 4 MiB")
    return json.loads(p.read_text(encoding="utf-8"))


def safe_path(value):
    need(type(value) is str and value and len(value) <= 4096, "Empty or overlong Git path")
    need(not value.startswith("/") and "\\" not in value, "Non-canonical Git path")
    need(all(part not in ("", ".", "..") for part in value.split("/")), "Unsafe Git path component")
    need(not any(c in value for c in "*?[]:") and not any(ord(c) < 32 or ord(c) == 127 for c in value),
         "Unsupported unusual Git path: globs, colon or control characters")
    return value


def validate_policy(policy):
    need(type(policy) is dict and {"schema_version", "protected_paths"} <= set(policy) and
         set(policy) <= {"schema_version", "protected_paths", "max_changed_files", "max_changed_lines"},
         "Unexpected or missing scope policy fields")
    need(type(policy["schema_version"]) is int and policy["schema_version"] == 1, "Unsupported scope policy")
    paths = policy["protected_paths"]
    need(type(paths) is list and len(paths) <= 256, "protected_paths must be a list")
    for prefix in paths:
        safe_path(prefix)
    need(len(paths) == len(set(paths)), "Duplicate protected_paths")
    for key in ("max_changed_files", "max_changed_lines"):
        if key in policy:
            need(type(policy[key]) is int and 1 <= policy[key] <= 10000000, "Invalid " + key)
    canonical_sha(policy)
    return policy


def _run_git(repo, *args, allowed=(0,)):
    # Ignore inherited alternate repositories/index/object stores and Git config
    # injection. The installed Git binary / PATH is part of the trusted runner.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
                "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": ""})
    command = ["git", "--no-replace-objects", "--no-pager", "-c", "core.hooksPath=" + os.devnull,
               "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
               "-c", "protocol.allow=never", "-C", str(repo), *args]
    result = subprocess.run(command, env=env, capture_output=True, timeout=60, check=False)
    need(result.returncode in allowed, "Git verification failed: " + result.stderr.decode("utf-8", errors="replace")[:500].strip())
    return result.returncode, result.stdout


def _preflight(repo):
    # Configuration reads do not access object contents or invoke conversion
    # filters. Inspect included/worktree config too, before ANY object read.
    _, raw = _run_git(repo, "config", "--null", "--includes", "--list")
    need(not raw or raw.endswith(b"\0"), "Invalid effective Git configuration")
    for record in raw[:-1].split(b"\0") if raw else []:
        key, _, value = record.partition(b"\n")
        key, value = key.lower(), value.strip().lower()
        if key.startswith(b"filter.") and key.endswith((b".clean", b".process")) and value:
            raise ScopeError("Configured clean/process filters are unsupported in the verification checkout")
        if key == b"extensions.partialclone" or (key.startswith(b"remote.") and key.endswith((b".promisor", b".partialclonefilter"))):
            raise ScopeError("Partial/promisor clone configuration is unsupported; provide a complete verification checkout")
        if key == b"core.sparsecheckout" and value not in (b"false", b"no", b"off", b"0"):
            raise ScopeError("Sparse verification checkouts are unsupported")


def _git(repo, *args, allowed=(0,)):
    _preflight(repo)
    if args and args[0] == "status":
        # status can invoke clean/process filters, recurse into submodule
        # configurations, or hide modified paths behind index flags.
        _, flags = _run_git(repo, "ls-files", "-v", "-z")
        for record in flags.split(b"\0"):
            if record:
                need(not record[:1].islower() and record[:1] != b"S",
                     "assume-unchanged / skip-worktree index entries are unsupported")
        _, entries = _run_git(repo, "ls-files", "--stage", "-z")
        need(not any(record.startswith(b"160000 ") for record in entries.split(b"\0")),
             "Submodule/gitlink checkouts require a separate approved scope verifier")
        args = tuple(arg for arg in args if not arg.startswith("--ignore-submodules")) + ("--ignore-submodules=all",)
    return _run_git(repo, *args, allowed=allowed)


def _no_gitlinks(repo, commit):
    _, tree = _git(repo, "ls-tree", "-r", "-z", commit)
    need(not any(record.startswith(b"160000 ") for record in tree.split(b"\0")),
         "Base/candidate contains submodules; use a separate approved scope verifier")


def _exact_commit(repo, sha):
    need(type(sha) is str and COMMIT.fullmatch(sha), "A full lowercase commit SHA is required")
    _, value = _git(repo, "rev-parse", "--verify", sha + "^{commit}")
    resolved = value.decode("ascii").strip()
    need(resolved == sha, "Supplied object is not the exact commit SHA")
    return resolved


def _paths(raw):
    need(not raw or raw.endswith(b"\0"), "Invalid NUL-separated Git output")
    if not raw:
        return []
    result = []
    for item in raw[:-1].split(b"\0"):
        try:
            path = item.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ScopeError("Non-UTF-8 Git path cannot be matched safely") from exc
        result.append(safe_path(path))
    need(len(result) == len(set(result)), "Duplicate path in Git output")
    return result


def verify(repo, candidate, spec, policy):
    spec = validate_spec(spec)
    policy = validate_policy(policy)
    root = Path(repo).resolve()
    need(root.is_dir(), "Repository checkout is missing")
    _, top = _git(root, "rev-parse", "--show-toplevel")
    need(Path(top.decode("utf-8").strip()).resolve() == root, "--repo must be the checkout root")
    base = _exact_commit(root, spec["request"]["repository"]["base_sha"])
    candidate = _exact_commit(root, candidate)
    _no_gitlinks(root, base)
    _no_gitlinks(root, candidate)
    _, head = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    need(head.decode("ascii").strip() == candidate, "Checkout HEAD differs from candidate SHA")
    _, dirty = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    need(not dirty, "Checkout must be clean, including untracked files")
    ancestry, _ = _git(root, "merge-base", "--is-ancestor", base, candidate, allowed=(0, 1))
    need(ancestry == 0, "Candidate does not descend from the pinned base commit")

    diff_flags = ["--no-renames", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none",
                  "--diff-algorithm=myers", "--no-indent-heuristic", base, candidate, "--"]
    _, names_raw = _git(root, "diff", "--name-only", "-z", *diff_flags)
    paths = _paths(names_raw)
    _, stats_raw = _git(root, "diff", "--numstat", "-z", *diff_flags)
    need(not stats_raw or stats_raw.endswith(b"\0"), "Invalid numstat output")
    rows = []
    for record in stats_raw[:-1].split(b"\0") if stats_raw else []:
        columns = record.split(b"\t", 2)
        need(len(columns) == 3, "Invalid Git numstat record")
        path = _paths(columns[2] + b"\0")[0]
        added, deleted = columns[:2]
        binary = added == deleted == b"-"
        need(binary or (re.fullmatch(rb"[0-9]+", added) and re.fullmatch(rb"[0-9]+", deleted)), "Uncountable Git diff stats")
        rows.append({"path": path, "added": None if binary else int(added),
                     "deleted": None if binary else int(deleted), "binary": binary})
    need(len(rows) == len(paths) and {row["path"] for row in rows} == set(paths), "Git name and numstat sets differ")

    # A gitlink represents another repository; a changed symlink can redirect a
    # later file reader outside the declared tree. Neither is a normal file diff.
    _, modes_raw = _git(root, "diff", "--raw", "-z", *diff_flags)
    need(not modes_raw or modes_raw.endswith(b"\0"), "Invalid raw Git diff")
    mode_parts = modes_raw[:-1].split(b"\0") if modes_raw else []
    need(len(mode_parts) % 2 == 0, "Unexpected rename/raw Git format")
    modes = {}
    for index in range(0, len(mode_parts), 2):
        fields = mode_parts[index].split()
        need(len(fields) == 5 and fields[0].startswith(b":"), "Invalid raw Git mode record")
        path = _paths(mode_parts[index + 1] + b"\0")[0]
        modes[path] = {fields[0][1:].decode("ascii"), fields[1].decode("ascii")}
    need(set(modes) == set(paths), "Git raw and name sets differ")

    allowed = spec["request"]["input"]["allowed_paths"]
    protected = sorted(set(spec["profile"]["protected_paths"] + policy["protected_paths"]))
    violations = []

    def fail(code, detail, path=None):
        violations.append({"code": code, "path": path, "detail": detail})

    for path in paths:
        if not any(path_contains(prefix, path) for prefix in allowed):
            fail("outside-scope", "Changed path is outside task allowed_paths", path)
        if any(path_contains(prefix, path) for prefix in protected) or any(part in RESERVED_PATHS for part in path.split("/")):
            fail("protected-path", "Changed path is protected by the task profile or project policy", path)
        if "160000" in modes[path]:
            fail("submodule-change-unsupported", "Gitlink changes require a separate approved repository scope verifier", path)
        if "120000" in modes[path]:
            fail("symlink-change-unsupported", "Changed symlinks require a separate approved target/path verifier", path)
    text_lines = sum(row["added"] + row["deleted"] for row in rows if not row["binary"])
    binary_paths = [row["path"] for row in rows if row["binary"]]
    if "max_changed_files" in policy and len(paths) > policy["max_changed_files"]:
        fail("file-limit", f"Changed paths {len(paths)} exceed {policy['max_changed_files']}")
    if "max_changed_lines" in policy:
        if binary_paths:
            fail("binary-line-count-unknown", "Line limit cannot be established for binary diffs")
        if text_lines > policy["max_changed_lines"]:
            fail("line-limit", f"Added + deleted text lines {text_lines} exceed {policy['max_changed_lines']}")
    return {"schema_version": 1, "check": "scope", "status": "FAIL" if violations else "PASS",
            "task_id": spec["request"]["task_id"], "request_sha256": spec["request_sha256"],
            "profile_sha256": spec["profile_sha256"], "spec_sha256": canonical_sha(spec),
            "policy_sha256": canonical_sha(policy), "base_sha": base, "candidate_sha": candidate,
            "allowed_paths": allowed, "protected_paths": protected,
            "changed_files": len(paths), "changed_text_lines": text_lines, "binary_paths": binary_paths,
            "files": rows, "violations": violations,
            "coverage": "Tracked base-to-final-commit paths and text diff size; renames are delete + add. Remote identity, runtime behavior, ignored files and workspace isolation require the trusted adapter."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--spec", required=True, help="Trusted immutable execution spec JSON")
    parser.add_argument("--policy", required=True, help="Project policy from protected CI configuration")
    parser.add_argument("--out", required=True, help="New report path outside the checkout")
    args = parser.parse_args()
    output = Path(args.out)
    need(not output.exists() and not output.is_symlink(), "Report already exists; choose a new output path")
    need(not output.resolve().is_relative_to(Path(args.repo).resolve()), "Report must be outside the candidate checkout")
    try:
        report = verify(args.repo, args.candidate, read_json(args.spec), read_json(args.policy))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        report = {"schema_version": 1, "check": "scope", "status": "FAIL",
                  "candidate_input": args.candidate,
                  "violations": [{"code": "verification-incomplete", "path": None, "detail": str(exc)[:1000]}]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(output.resolve())}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
