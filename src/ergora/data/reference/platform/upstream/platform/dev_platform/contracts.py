"""Pure, deterministic v2 task contracts; no filesystem or network access.

Path declarations are ownership claims, not an operating-system sandbox. A
trusted verifier must check the actual final Git diff and protected paths.
"""
import hashlib
import json
import re


class ContractError(ValueError):
    """An input, pinned profile or execution snapshot is not valid."""


SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
SHA256 = re.compile(r"[a-f0-9]{64}")
COMMIT = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})")
STAGES = ("inventory", "plan", "work", "integrate", "verify", "review")
ROLES = dict(zip(STAGES, ("inspector", "planner", "implementer", "integrator", "verifier", "reviewer")))
RESERVED_PATHS = (".git", ".symphony", ".agent-control", ".agent-platform-private")
TEMPLATE_FILES = ("README.md", "instructions.md", "input.schema.json", "output.schema.json")


def need(condition, message):
    if not condition:
        raise ContractError(message)


def canonical_sha(value):
    """Hash UTF-8 canonical JSON; NaN/infinity are invalid protocol values."""
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Value cannot be encoded as canonical JSON") from exc
    return hashlib.sha256(encoded).hexdigest()


def _object(value, keys, label):
    need(type(value) is dict, f"{label} must be an object")
    need(set(value) == set(keys), f"{label} fields must be exactly: {', '.join(sorted(keys))}")


def _text(value, label, limit=12000):
    need(type(value) is str and bool(value.strip()) and len(value) <= limit,
         f"{label} must be a non-empty string of at most {limit} characters")
    need("\x00" not in value, f"{label} contains NUL")


def _slug(value, label):
    need(type(value) is str and SLUG.fullmatch(value) is not None, f"Invalid {label}")


def _integer(value, lo, hi, label):
    need(type(value) is int and lo <= value <= hi, f"{label} must be an integer in [{lo}, {hi}]")


def _list(value, label, lo=0, hi=64):
    need(type(value) is list and lo <= len(value) <= hi, f"{label} requires {lo}..{hi} entries")


def _unique(values, label):
    need(len(set(values)) == len(values), f"Duplicate entries in {label}")


def _path(value, label, allow_reserved=False):
    _text(value, label, 300)
    need(not value.startswith("/") and not value.endswith("/") and "\\" not in value,
         f"{label} must be a canonical relative POSIX prefix")
    parts = value.split("/")
    need(all(p not in ("", ".", "..") for p in parts), f"Unsafe path in {label}")
    need(not any(c in value for c in "*?[]:") and not any(ord(c) < 32 or ord(c) == 127 for c in value),
         f"{label} cannot contain globs, colon or control characters")
    if not allow_reserved:
        need(not any(p in RESERVED_PATHS for p in parts), f"{label} names reserved control metadata")
    return value


def path_contains(prefix, path):
    """Component-wise prefix; src/a does not own src/ab."""
    return path == prefix or path.startswith(prefix + "/")


def paths_overlap(left, right):
    return path_contains(left, right) or path_contains(right, left)


def _paths(value, label, lo=1, allow_reserved=False):
    _list(value, label, lo, 64)
    for path in value:
        _path(path, label, allow_reserved)
    _unique(value, label)


def _strings(value, label, lo=0, hi=64):
    _list(value, label, lo, hi)
    for item in value:
        _text(item, label, 4000)
    _unique(value, label)


def _ancestors(units):
    by_id = {unit["id"]: unit for unit in units}
    result, visiting = {}, set()

    def visit(uid):
        need(uid not in visiting, "Work unit dependency graph contains a cycle")
        if uid in result:
            return result[uid]
        visiting.add(uid)
        parents = set()
        for dep in by_id[uid]["depends_on"]:
            need(dep in by_id, f"Unknown dependency {dep} for {uid}")
            parents.add(dep)
            parents.update(visit(dep))
        visiting.remove(uid)
        result[uid] = parents
        return parents

    for uid in by_id:
        visit(uid)
    return result


def validate_task(request):
    """Validate shape, ownership and DAG only; installed profile is make_spec's job."""
    _object(request, ("schema_version", "task_type", "task_version", "task_id", "profile_sha256",
                      "tracker", "repository", "input"), "request")
    need(type(request["schema_version"]) is int and request["schema_version"] == 2,
         "Unsupported task request schema")
    _slug(request["task_type"], "task_type")
    _integer(request["task_version"], 1, 1000000, "task_version")
    _slug(request["task_id"], "task_id")
    need(type(request["profile_sha256"]) is str and SHA256.fullmatch(request["profile_sha256"]),
         "profile_sha256 must pin a trusted installed profile")
    tracker = request["tracker"]
    _object(tracker, ("kind", "project", "issue_id"), "tracker")
    need(tracker["kind"] in ("local", "github", "gitlab"), "Unsupported tracker kind")
    project = tracker["project"]
    need(type(project) is str and len(project) <= 300 and
         re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", project) is not None,
         "Invalid tracker project")
    need(all(p not in (".", "..") for p in project.split("/")), "Invalid tracker project component")
    need(tracker["kind"] != "github" or len(project.split("/")) == 2, "GitHub project must be owner/repo")
    need(type(tracker["issue_id"]) is str and
         re.fullmatch(r"[1-9][0-9]{0,19}", tracker["issue_id"]) is not None,
         "issue_id must be a positive issue number / IID")
    repo = request["repository"]
    _object(repo, ("base_sha", "starting_sha"), "repository")
    for key in repo:
        need(type(repo[key]) is str and COMMIT.fullmatch(repo[key]), f"Full commit required: {key}")
    inp = request["input"]
    _object(inp, ("goal", "allowed_paths", "acceptance", "constraints", "risk", "work_units"), "input")
    _text(inp["goal"], "goal")
    _paths(inp["allowed_paths"], "allowed_paths")
    _strings(inp["acceptance"], "acceptance", 1)
    _strings(inp["constraints"], "constraints")
    need(inp["risk"] in ("standard", "high"), "risk must be standard or high")
    units = inp["work_units"]
    _list(units, "work_units", 1, 24)
    for unit in units:
        _object(unit, ("id", "depends_on", "paths", "instructions"), "work unit")
        _slug(unit["id"], "work unit id")
        _list(unit["depends_on"], "depends_on", 0, 23)
        for dep in unit["depends_on"]:
            _slug(dep, "dependency id")
        _unique(unit["depends_on"], "depends_on")
        _paths(unit["paths"], "work unit paths")
        _text(unit["instructions"], "work unit instructions")
        for path in unit["paths"]:
            need(any(path_contains(allowed, path) for allowed in inp["allowed_paths"]),
                 f"Work unit {unit['id']} path {path} is outside allowed_paths")
    _unique([u["id"] for u in units], "work unit ids")
    ancestors = _ancestors(units)
    for i, left in enumerate(units):
        for right in units[i + 1:]:
            ordered = left["id"] in ancestors[right["id"]] or right["id"] in ancestors[left["id"]]
            overlap = any(paths_overlap(a, b) for a in left["paths"] for b in right["paths"])
            need(ordered or not overlap,
                 f"Parallel units {left['id']} and {right['id']} have overlapping write ownership")
    canonical_sha(request)  # reject non-JSON scalars early
    return request


def validate_profile(profile):
    """Validate a frozen development-v1 profile without reading installed files."""
    _object(profile, ("schema_version", "task_type", "task_version", "engine", "title", "required_checks",
                      "limits", "stage_timeout_seconds", "approval_timeout_seconds", "poll_seconds",
                      "artifacts_by_stage", "roles", "protected_paths", "template_files"), "profile")
    need(type(profile["schema_version"]) is int and profile["schema_version"] == 1, "Unsupported profile schema")
    _slug(profile["task_type"], "profile task_type")
    _integer(profile["task_version"], 1, 1000000, "profile task_version")
    need(profile["engine"] == "development-v1", "Unsupported task engine")
    _text(profile["title"], "profile title", 200)
    _list(profile["required_checks"], "required_checks", 1, 40)
    for check in profile["required_checks"]:
        _slug(check, "check id")
    _unique(profile["required_checks"], "required_checks")
    need("scope" in profile["required_checks"], "Every development profile requires a trusted scope check")
    limits = profile["limits"]
    _object(limits, ("max_work_units", "max_parallel_units"), "profile limits")
    _integer(limits["max_work_units"], 1, 24, "max_work_units")
    _integer(limits["max_parallel_units"], 1, min(8, limits["max_work_units"]), "max_parallel_units")
    _integer(profile["stage_timeout_seconds"], 30, 86400, "stage_timeout_seconds")
    _integer(profile["approval_timeout_seconds"], 60, 604800, "approval_timeout_seconds")
    _integer(profile["poll_seconds"], 1, min(300, profile["stage_timeout_seconds"]), "poll_seconds")
    _object(profile["artifacts_by_stage"], STAGES, "artifacts_by_stage")
    for stage in STAGES:
        artifacts = profile["artifacts_by_stage"][stage]
        _list(artifacts, f"{stage} artifacts", 1, 30)
        for artifact in artifacts:
            _slug(artifact, "artifact name")
        _unique(artifacts, f"{stage} artifacts")
    need(profile["roles"] == ROLES, "Role mapping differs from development-v1 stage semantics")
    _paths(profile["protected_paths"], "protected_paths", allow_reserved=True)
    need(set(RESERVED_PATHS).issubset(profile["protected_paths"]), "Profile omits reserved control metadata")
    _object(profile["template_files"], TEMPLATE_FILES, "template_files")
    for value in profile["template_files"].values():
        need(type(value) is str and SHA256.fullmatch(value), "Template file requires SHA256")
    canonical_sha(profile)
    return profile


def validate_spec(spec):
    """Check a persisted immutable snapshot; authenticity is the worker's duty."""
    _object(spec, ("request", "profile", "request_sha256", "profile_sha256"), "execution spec")
    request = validate_task(spec["request"])
    profile = validate_profile(spec["profile"])
    need(spec["request_sha256"] == canonical_sha(request), "Request hash mismatch")
    need(spec["profile_sha256"] == canonical_sha(profile), "Profile hash mismatch")
    need(request["profile_sha256"] == spec["profile_sha256"], "Request does not pin this profile")
    need(request["task_type"] == profile["task_type"] and request["task_version"] == profile["task_version"],
         "Request and profile type/version differ")
    need(len(request["input"]["work_units"]) <= profile["limits"]["max_work_units"],
         "Task exceeds profile work unit limit; split into smaller task instances")
    for path in request["input"]["allowed_paths"]:
        need(not any(paths_overlap(path, protected) for protected in profile["protected_paths"]),
             f"allowed_paths overlaps trusted protected path: {path}")
    return spec


def make_spec(request):
    """Convenience boundary; unlike validators this loads the trusted registry."""
    from .registry import make_spec as resolve
    return resolve(request)
