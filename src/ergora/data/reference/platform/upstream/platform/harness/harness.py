#!/usr/bin/env python3
"""Small, fail-closed repository harness. Python static imports + local Markdown links.

Run the installed trusted copy in CI; never execute a candidate's copy as a gate.
This scanner is deliberately not a universal correctness or security checker.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

VERSION = "1.0.0"
IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}


class HarnessError(ValueError):
    pass


def require(value, message):
    if not value:
        raise HarnessError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "Expected a regular non-symlink JSON file")
    require(p.stat().st_size <= 8 * 1024 * 1024, "JSON exceeds 8 MiB")
    return json.loads(p.read_text())


def write_new(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value, "Expected a relative POSIX path")
    p = PurePosixPath(value)
    require(not p.is_absolute() and all(x not in (".", "..") for x in value.split("/")), "Unsafe relative path")
    return value


def load_policy(path):
    policy = read_json(path)
    require(set(policy) == {"schema_version", "required_docs", "doc_roots", "python_roots", "layers", "allowed_edges", "max_file_lines"}, "Unexpected or missing policy fields")
    require(policy["schema_version"] == 1, "Unsupported harness policy")
    for key in ("required_docs", "doc_roots", "python_roots"):
        require(isinstance(policy[key], list) and policy[key], key + " must be a nonempty list")
        require(len(policy[key]) == len(set(policy[key])), "Duplicate " + key)
        for item in policy[key]:
            relative_path(item)
    require(type(policy["max_file_lines"]) is int and 30 <= policy["max_file_lines"] <= 5000, "Invalid max_file_lines")
    require(isinstance(policy["layers"], dict) and policy["layers"], "Layers required")
    prefixes = []
    for layer, names in policy["layers"].items():
        require(re.fullmatch(r"[a-z][a-z0-9_-]*", layer), "Invalid layer name")
        require(isinstance(names, list) and names, "Layer module prefixes required")
        for name in names:
            require(re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", name), "Invalid module prefix")
            prefixes.append(name)
    require(len(prefixes) == len(set(prefixes)), "Duplicate layer prefix")
    require(set(policy["allowed_edges"]) == set(policy["layers"]), "Declare allowed edges for every layer")
    for targets in policy["allowed_edges"].values():
        require(isinstance(targets, list) and set(targets) <= set(policy["layers"]), "Unknown target layer")
    return policy


def bootstrap(destination):
    """Only stage a new tree; the caller must merge this through a normal PR."""
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), "Destination already exists; choose a new staging directory")
    shutil.copytree(Path(__file__).with_name("templates"), destination)
    return str(destination.resolve())


def _files(root, path, suffix, findings):
    p = root / path
    if p.is_symlink() or not p.resolve().is_relative_to(root):
        findings.append(_finding("scan-root-unsafe", path, "root", "error", "Scan root must be a real directory/file within the repository."))
        return []
    if not p.exists():
        findings.append(_finding("scan-root-missing", path, "root", "error", "Configured scan root is missing; correct the policy or checkout."))
        return []
    entries = [p] if p.is_file() else sorted(p.rglob("*"))
    output = []
    for f in entries:
        rel = f.relative_to(root)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if f.is_symlink():
            findings.append(_finding("symlink-unsupported", str(rel), "symlink", "error", "Use a real checked-in file or a separate scanner with explicit coverage."))
            continue
        if f.is_file() and f.suffix == suffix:
            output.append(f)
    return output


def _finding(rule, path, key, level, message):
    fingerprint = digest(canonical({"rule": rule, "path": path, "key": key}))
    return {"fingerprint": fingerprint, "rule": rule, "path": path, "key": key, "level": level, "message": message}


def _layer(module, policy):
    matches = [(len(prefix), layer) for layer, prefixes in policy["layers"].items() for prefix in prefixes if module == prefix or module.startswith(prefix + ".")]
    return max(matches)[1] if matches else None


def _imports(tree, module, is_package):
    package = module.split(".") if is_package else module.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                yield name.name, None
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level > len(package):
                    yield "", "Relative import escapes the configured Python root"
                    continue
                parts = package[:len(package) - node.level + 1]
                if node.module:
                    parts += node.module.split(".")
                base = ".".join(parts)
            else:
                base = node.module or ""
            for name in node.names:
                yield (base + "." + name.name if name.name != "*" else base), base


def _module_match(target, modules):
    parts = target.split(".")
    while parts:
        value = ".".join(parts)
        if value in modules:
            return value
        parts.pop()
    return None


def scan(repo, policy):
    root = Path(repo).resolve()
    require(root.is_dir(), "Repository directory does not exist")
    findings = []
    source_hashes = {}

    def add(rule, path, key, level, message):
        findings.append(_finding(rule, path, key, level, message))

    def text(path):
        rel = path.relative_to(root).as_posix()
        require(path.resolve().is_relative_to(root), "Scan path escapes repository")
        raw = path.read_bytes()
        source_hashes[rel] = digest(raw)
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError:
            add("non-utf8-file", rel, "encoding", "error", "Scanner requires UTF-8 input.")
            return None
        if len(value.splitlines()) > policy["max_file_lines"]:
            add("file-too-long", rel, "length", "debt", "Split responsibilities; do not raise the shared threshold in this PR.")
            findings[-1]["observed"] = len(value.splitlines())
        return value

    for name in policy["required_docs"]:
        if not (root / name).is_file():
            add("required-doc-missing", name, "required", "debt", "Add the documented repository entry point.")
    markdown = set()
    for name in policy["doc_roots"]:
        markdown.update(_files(root, name, ".md", findings))
    # Deliberately supports ordinary inline/reference Markdown links, not MDX/HTML.
    link_pattern = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)")
    reference_pattern = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", re.MULTILINE)
    for path in sorted(markdown):
        rel = path.relative_to(root).as_posix()
        content = text(path)
        if content is None:
            continue
        # Code examples can contain intentionally nonexistent paths.
        content = re.sub(r"(?ms)^\s*(```+|~~~+).*?^\s*\1\s*$", "", content)
        content = re.sub(r"`[^`\n]+`", "", content)
        targets = [m.group(1).strip("<>") for pattern in (link_pattern, reference_pattern) for m in pattern.finditer(content)]
        for link in targets:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root):
                add("doc-link-escape", rel, link, "error", "Local document links must stay within the repository.")
            elif not target.exists():
                add("doc-link-broken", rel, link, "debt", "Repair or remove this local link: " + link)

    module_files = {}
    for python_root in policy["python_roots"]:
        files = _files(root, python_root, ".py", findings)
        if not files:
            add("python-coverage-empty", python_root, "empty", "error", "No Python files scanned; configure the actual source root or use a language-specific external gate.")
        for path in files:
            local = path.relative_to(root / python_root).with_suffix("")
            pieces = list(local.parts)
            if pieces[-1] == "__init__":
                pieces.pop()
            if not pieces:
                add("python-root-package", path.relative_to(root).as_posix(), "root", "error", "Set python_roots to the parent of the importable package.")
                continue
            module = ".".join(pieces)
            if module in module_files:
                add("module-ambiguous", str(path.relative_to(root)), module, "error", "Duplicate module across configured roots.")
            module_files[module] = path
    internal_roots = {m.split(".")[0] for m in module_files}
    edge_count = 0
    for module, path in sorted(module_files.items()):
        rel = path.relative_to(root).as_posix()
        source_layer = _layer(module, policy)
        if source_layer is None:
            add("python-layer-unassigned", rel, module, "error", "Assign this module to an explicit architectural layer.")
        content = text(path)
        if content is None:
            continue
        try:
            tree = ast.parse(content, filename=rel)
        except SyntaxError:
            add("python-parse-error", rel, "syntax", "error", "Fix syntax; an incomplete scan cannot be baselined.")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id == "__import__") or (isinstance(node.func, ast.Attribute) and node.func.attr == "import_module")):
                add("dynamic-import-unsupported", rel, ast.dump(node.func), "error", "Static AST cannot validate dynamic imports; replace with explicit imports or add a separately reviewed scanner.")
        for target, base in _imports(tree, module, path.name == "__init__.py"):
            if not target:
                add("python-relative-import-invalid", rel, base, "error", base)
                continue
            if target.split(".")[0] not in internal_roots:
                continue
            resolved = _module_match(target, module_files)
            # Namespace packages may have no __init__.py. Use the textual target
            # only if it is a real parent of at least one discovered module.
            if not resolved and any(m.startswith(target + ".") for m in module_files):
                resolved = target
            if not resolved and base and any(m.startswith(base + ".") for m in module_files):
                resolved = base
            if not resolved:
                add("python-import-unresolved", rel, target, "error", "Internal import could not be resolved in scanned roots: " + target)
                continue
            destination_layer = _layer(resolved, policy)
            if destination_layer is None:
                add("python-target-unassigned", rel, resolved, "error", "Imported internal module has no architectural layer.")
                continue
            edge_count += 1
            if source_layer and source_layer != destination_layer and destination_layer not in policy["allowed_edges"][source_layer]:
                add("forbidden-dependency", rel, module + "->" + resolved, "debt", f"Disallowed {source_layer} -> {destination_layer}; move the dependency behind the approved interface.")
    unique = {f["fingerprint"]: f for f in findings}
    return {"schema_version": 1, "scanner_version": VERSION, "policy_sha256": digest(canonical(policy)),
            "source_tree_sha256": digest(canonical(source_hashes)), "source_files": source_hashes,
            "coverage": {"markdown_files": len(markdown), "python_files": len(module_files), "internal_import_edges": edge_count,
                         "supports": ["local Markdown file targets", "static Python imports", "UTF-8 line count"],
                         "excludes": ["remote URLs", "Markdown heading anchors", "MDX/HTML links", "reflection/plugins", "runtime behavior", "security", "other programming languages"]},
            "findings": sorted(unique.values(), key=lambda x: (x["level"], x["path"], x["rule"], x["key"]))}


def make_baseline(report):
    require(report.get("schema_version") == 1 and report.get("scanner_version") == VERSION, "Unsupported scan report")
    require(all(f["level"] == "debt" for f in report["findings"]), "Incomplete scan / hard errors cannot become baseline debt")
    return {"schema_version": 1, "scanner_version": VERSION, "policy_sha256": report["policy_sha256"],
            "source_tree_sha256": report["source_tree_sha256"], "debt": report["findings"]}


def evaluate(report, baseline=None):
    old = set()
    measurements = {}
    if baseline is not None:
        require(baseline.get("schema_version") == 1 and baseline.get("scanner_version") == VERSION, "Baseline scanner version differs; review a separate baseline migration")
        require(baseline.get("policy_sha256") == report["policy_sha256"], "Policy differs from baseline; review a separate policy migration")
        require(all(f.get("level") == "debt" for f in baseline.get("debt", [])), "Baseline may contain only debt, never hard errors")
        old = {f["fingerprint"] for f in baseline["debt"]}
        measurements = {f["fingerprint"]: f["observed"] for f in baseline["debt"] if "observed" in f}
    current = {f["fingerprint"] for f in report["findings"]}
    new = [f for f in report["findings"] if f["fingerprint"] not in old or f["level"] == "error" or
           ("observed" in f and f["observed"] > measurements.get(f["fingerprint"], -1))]
    return {"status": "PASS" if not new else "BLOCKED", "new_findings": new,
            "existing_debt": len(current & old), "resolved_debt": sorted(old - current),
            "policy_sha256": report["policy_sha256"], "source_tree_sha256": report["source_tree_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init"); init.add_argument("--destination", required=True)
    for command in ("scan", "check"):
        p = sub.add_parser(command)
        p.add_argument("--repo", required=True); p.add_argument("--policy", required=True); p.add_argument("--out", required=True)
        if command == "check":
            p.add_argument("--baseline"); p.add_argument("--baseline-sha256")
    baseline = sub.add_parser("baseline-proposal")
    baseline.add_argument("--report", required=True); baseline.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.action == "init":
        print(bootstrap(args.destination)); return 0
    if args.action == "baseline-proposal":
        write_new(args.out, make_baseline(read_json(args.report)))
        print("PROPOSAL ONLY: review in a separate protected-branch PR; CI must pin its SHA256.")
        return 0
    policy = load_policy(args.policy)
    report = scan(args.repo, policy)
    if args.action == "scan":
        write_new(args.out, report)
        print(json.dumps({"findings": len(report["findings"]), "coverage": report["coverage"]}, ensure_ascii=False))
        return 2 if any(f["level"] == "error" for f in report["findings"]) else 0
    require(bool(args.baseline) == bool(args.baseline_sha256), "Supply both baseline and its trusted SHA256, or neither")
    prior = None
    if args.baseline:
        require(re.fullmatch(r"[a-f0-9]{64}", args.baseline_sha256), "Expected baseline SHA256")
        require(digest(Path(args.baseline).read_bytes()) == args.baseline_sha256, "Baseline bytes differ from trusted CI hash")
        prior = read_json(args.baseline)
    gate = evaluate(report, prior)
    write_new(args.out, {"report": report, "gate": gate})
    print(json.dumps(gate, ensure_ascii=False))
    return 0 if gate["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        raise SystemExit(2)
