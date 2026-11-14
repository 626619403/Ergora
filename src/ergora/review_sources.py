"""Read-only native review observations linked to the original local source packet."""

import hashlib
import json
from pathlib import Path
import stat
import tempfile

from . import contracts, issue_backends, issue_sources, review_packets
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json


_MAX_SOURCE_BYTES = 2_000_000
_SCHEMA = json.loads((Path(__file__).parent / "data/schemas/external-review-source-v1.json").read_text(encoding="utf-8"))
_COVERAGE = {"platform": "repository-and-single-review-observation", "source": "local-exact-Git-objects",
             "comments_and_ci": "not-collected", "checks": "operator-supplied-unverified",
             "execution_authorized": False, "platform_approval": False}


def _repository_id(observation: dict) -> str:
    identity = json.dumps({key: observation[key] for key in ("source", "repository")}, sort_keys=True, separators=(",", ":"))
    return "native-repository-sha256:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _check(source: dict, packet: dict) -> None:
    observation = source["observation"]
    contracts.validate(observation, contracts.REVIEW_REQUEST, "Review request observation")
    origin = observation["source"]
    backend = issue_backends.for_binding({"tool": origin["provider"], "project": origin["project"],
                                         "api_url": origin["api_url"]})
    repository = source["repository"]
    identity = {"native_id": repository["native_id"], "node_id": repository.get("node_id"),
                "project": repository["project"]}
    if (issue_sources.tracker_identity(backend.binding) != origin or identity != observation["repository"]
            or repository["project"] != origin["project"]
            or observation["response"]["request_url"] != backend.api_url + backend.review_path(repository, observation["review"]["number"])):
        raise ValueError("External review source differs from its repository or request origin")
    commits = backend.review_commits(observation["review"])
    actual = packet["repository"]
    if (actual["id"] != _repository_id(observation) or actual["comparison"] != "merge-base"
            or any(actual[key] != commits[key] for key in ("base", "head"))
            or commits["diff_base"] is not None and actual["diff_base"] != commits["diff_base"]):
        raise ValueError("External review source differs from its exact source comparison")


def collect(binding: dict, number: str, repository: Path, *, requirements: Path, destination: Path,
            context_paths: list[str] | None = None, evidence: list[Path] | None = None,
            max_source_bytes: int = 1_000_000) -> dict:
    """Collect two native GET observations and local objects, never remote diffs or execution."""
    backend = issue_backends.for_binding(binding)
    native_repository = backend.repository()
    observation = backend.read_review_request(native_repository, number)
    commits = backend.review_commits(observation["review"])
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-source-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "source"
        staged.mkdir()
        prepared = review_packets.prepare(repository, repository_id=_repository_id(observation),
            base=commits["base"], head=commits["head"], requirements=requirements,
            destination=staged / "material", context_paths=context_paths, evidence=evidence,
            max_source_bytes=max_source_bytes)
        source = {"schema_version": 1, "kind": "external-source-review", "repository": native_repository,
                  "observation": observation, "packet_sha256": prepared["packet_sha256"], "coverage": dict(_COVERAGE)}
        contracts.validate(source, _SCHEMA, "External review source")
        _check(source, {"repository": prepared["repository"]})
        encoded = (json.dumps(source, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > _MAX_SOURCE_BYTES:
            raise ValueError("Complete external review observation exceeds 2 MB")
        (staged / "source.json").write_bytes(encoded)
        publish_directory(staged, destination)
    return {"directory": str(destination), "source_sha256": hashlib.sha256(encoded).hexdigest(),
            "packet_sha256": prepared["packet_sha256"], "source": observation["source"],
            "review_number": number, "repository": prepared["repository"], "coverage": dict(_COVERAGE)}


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify a saved observation and complete original packet offline; no origin authentication."""
    directory = directory.expanduser().absolute()
    if is_link(directory) or not directory.is_dir() or {path.name for path in directory.iterdir()} != {"source.json", "material"}:
        raise ValueError("External review directory must contain exactly source.json and material")
    path = directory / "source.json"
    if is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("External review source requires an ordinary file")
    with path.open("rb") as stream:
        encoded = stream.read(_MAX_SOURCE_BYTES + 1)
    if len(encoded) > _MAX_SOURCE_BYTES:
        raise ValueError("Complete external review observation exceeds 2 MB")
    actual = hashlib.sha256(encoded).hexdigest()
    if sha256 is not None and sha256 != actual:
        raise ValueError("External review source differs from expected SHA256")
    source = parse_json(encoded.decode("utf-8"), "external review source")
    contracts.validate(source, _SCHEMA, "External review source")
    material = review_packets.read(directory / "material", sha256=source["packet_sha256"])
    _check(source, material["packet"])
    return {"source_sha256": actual, "source": source, "material": material}
