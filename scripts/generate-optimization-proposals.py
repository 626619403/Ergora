"""Render the repository's pinned optimization proposal Workflow bundles."""

from argparse import ArgumentParser
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory


PRESETS = Path(__file__).resolve().parents[1] / "src/ergora/data/presets"
WORKFLOW_SCHEMA = PRESETS.parent / "schemas/workflow-definition-v2.json"
DESCRIPTION = "Limited readonly {} proposal; complete optimization requires a shared training-proposal ancestor."
INSTRUCTIONS = "instructions.md"


def _ref(kind, identity, version, digest):
    return {"kind": kind, "id": identity, "version": version, "digest": digest}


DESIGNER = _ref("agent", "ergora-experiment-designer", "2.1.1",
                "90cca8c6d2b453518007043ef3fb0475b0bc62a405badcdb4cd440f6daecb3af")
KERNEL_DESIGNER = _ref("agent", "ergora-kernel-designer", "2.2.1",
                       "4a50c2dd5efab4027ad7ccb491d2c250ec850b29da8876295dfdcdf9656da50e")
PERFORMANCE_ANALYST = _ref("agent", "ergora-performance-analyst", "2.3.1",
                            "a71aee4a0a46e2dd4090cc6e078e92e814ae3a0143c3db6b1c5a7fc5f4ccd577")
MEASUREMENT = _ref("workflow", "ergora-measurement-review", "2.0.2",
                   "5042a91a1a214930935c1d5df5cdf0b1d8bebe092136f3fbc9346980976ea688")


@dataclass(frozen=True)
class Proposal:
    version: str
    instructions_sha256: str
    specialist: dict[str, str]
    role: str = "performance-analyst"
    kernel_assessment: bool = False


PROPOSALS = {
    "activation-recompute": Proposal(
        "1.2.1", "b8d1069725013519f7c93d2d3ab14519b59a10d3f9c736240942cfe87e3a85ed",
        _ref("agent", "ergora-opt-activation-recompute-expert", "1.1.1",
             "8f2b852377cdc29709301fd73c2ba6e42141eb2f5b90b982f5687d5bdee9af1f"),
    ),
    "cluster-resiliency": Proposal(
        "1.2.1", "741a8611c6180d8d91c7cc12532dee722a92ef20c71708cb506a3ad68f15423f",
        _ref("agent", "ergora-opt-cluster-resiliency-expert", "1.1.1",
             "441032d5cecd847d83363ef640285c864afa2bb7329ea8a759259e95b076c867"),
    ),
    "cpu-offloading": Proposal(
        "1.2.1", "56c37359cbcbeaba1e5ba1f8f9000c82517b7543e39e6831d8f1b70a1fda6ff4",
        _ref("agent", "ergora-opt-cpu-offloading-expert", "1.1.1",
             "ac30bd56f2e00e33de54549eec6f2421acb216b8556752005b33281e8c31b63d"),
    ),
    "cuda-graphs": Proposal(
        "1.2.1", "a2aab5604638fb842435b9358867c4c519762341856617b4f65e4682d579f30f",
        _ref("agent", "ergora-opt-cuda-graphs-expert", "1.1.1",
             "b2cddfe67e3f07f80c63df757f5bd64306b3f6a6b816f58968430082c544aad6"),
    ),
    "hierarchical-cp": Proposal(
        "1.2.1", "66c50e9163060c1ba9c654fcb70333da4fb816d8417f6321f9db2b01a819a1ff",
        _ref("agent", "ergora-opt-hierarchical-cp-expert", "1.1.1",
             "30f696c3adde86d723ff91507c743ffc11732281c7405bc7ba9f8c71aead9e85"),
    ),
    "kernel": Proposal(
        "1.2.1", "d78f4d86406e609991a33cb3dd6f856dbec54c118cd88efa0b3f4fc755719bbc",
        KERNEL_DESIGNER, role="kernel-tuner",
    ),
    "low-precision": Proposal(
        "1.2.1", "5145c7f5d263e95e459d4b569419cb77319f715c8fe06771aebc239507904da0",
        _ref("agent", "ergora-opt-low-precision-expert", "1.1.1",
             "69e995fcb537441ee6cf51012bc2d40e83e44108d8e4eefd01e91d9422251110"),
        kernel_assessment=True,
    ),
    "megatron-fsdp": Proposal(
        "1.2.1", "64b22623e258d5b874a537f6a46d5e1f75cb2df358d8e9e5cdde64c470b55759",
        _ref("agent", "ergora-opt-megatron-fsdp-expert", "1.1.1",
             "15c8cd408a949c0529874f856a00aced17e4d7ba2fa31d0c664eaad185515af6"),
    ),
    "memory-snapshot": Proposal(
        "1.2.1", "e65e28392fe60dd6b89330cef4343970167b449c8149cc0c27ee097d88856eb8",
        _ref("agent", "ergora-opt-memory-snapshot-expert", "1.1.1",
             "146a0abcf1ca72e90b118861aa99d80eef0179c978314343d618406451e7269a"),
    ),
    "memory-tuning": Proposal(
        "1.2.2", "1e1ab4735a10b995e27aedbf22ff6231cf57ac28341235002f4cbf4df66246bd",
        _ref("agent", "ergora-opt-memory-tuning-expert", "1.1.2",
             "2e70ba5f90f00987fc050787a1cf68bfb0b3bc3a32e9c314c674880b3c18a13e"),
    ),
    "model-verification": Proposal(
        "1.2.1", "2574db6363510c6042c8006ee19291521b1ce114ef0884dc6116d7a9066a04f1",
        _ref("agent", "ergora-opt-model-verification-expert", "1.1.1",
             "3f0afe04f8fc014c7f478b0d598e3866bd1b16b5c37aa1c5807845cd01e40119"),
    ),
    "moe-dispatcher": Proposal(
        "1.2.1", "01580f29786c73e95249448e08c9d910a85c51a939f0cdb48dcca58dc466d91b",
        _ref("agent", "ergora-opt-moe-dispatcher-expert", "1.1.1",
             "5969da97054f84f284220d8d765a002d13e800f92b1842ba199a1f1bcf869b42"),
    ),
    "moe-overlap": Proposal(
        "1.2.1", "61565467776de1c03dc8d1507fe326849d2ee2512ae3b51e5b95eeedade4bf89",
        _ref("agent", "ergora-opt-moe-overlap-expert", "1.1.1",
             "9fbf2e3103aa605ac42b190ce3d83d56cb12bdd9a9bb6a44d0c12d2537ae0583"),
    ),
    "parallelism": Proposal(
        "1.2.1", "aad0b961250d616f49f4cd40df274753bd7063a8ca32c198eff67e2803e8f773",
        _ref("agent", "ergora-opt-parallelism-expert", "1.1.1",
             "e3073058712304cec1ff8e510acac53380d0105b6d5f3f3ab95479fe7624dfd2"),
    ),
    "performance-diagnosis": Proposal(
        "1.2.2", "4aaf395fca252a45bdaa8255bb13132e2f9e8fa6d24eb6ca7737e58758544d13",
        PERFORMANCE_ANALYST,
    ),
    "profiling": Proposal(
        "1.2.2", "0a9e6eee732080bc940c51048fc58900c19bbd9075a314fa0566d8cdb5eb330c",
        PERFORMANCE_ANALYST,
    ),
    "recipe-model": Proposal(
        "1.2.1", "b28f32d222670fb2c14afdc9ffab059dcc0ceede68a334c3c992355f6e526102",
        _ref("agent", "ergora-opt-recipe-model-expert", "1.1.1",
             "40a28067270befaf6a43ea455db6fbbd60cf45c5c6330b5963e2cd2612ddf614"),
    ),
    "sequence-packing": Proposal(
        "1.2.1", "2c21f41184c75bcc9fd1ccb9a7abb2f2cbe44b228cbf5920f40511c1d52fb296",
        _ref("agent", "ergora-opt-sequence-packing-expert", "1.1.1",
             "9c3b9439adb73267ef263552335391a814b90e86b20a56714f967c1d4449c4f6"),
    ),
    "tp-dp-overlap": Proposal(
        "1.2.1", "aaeb75d46899fa4b756d6b056e3a123347650adab673111826ceeb888f0dea92",
        _ref("agent", "ergora-opt-tp-dp-overlap-expert", "1.1.1",
             "c1e23982d0f1d03c7a2e0a2d1e57f1513e62bd72cc66402e0350750d62ce2a5c"),
    ),
}


def _proposal_id(direction):
    return f"ergora-opt-{direction}-proposal"


def _result(node):
    return {"node": node, "output": "result"}


def _definition(direction, proposal):
    identity = _proposal_id(direction)
    permissions = {"read": ["workspace", "definitions"], "write": [], "shell": False, "network": []}
    nodes = [
        {"id": "specialist", "ref": proposal.specialist, "role": proposal.role,
         "depends_on": [], "inputs": {"task": {"input": "task"}}, "permissions": permissions},
        {"id": "design", "ref": DESIGNER, "role": "experiment-planner",
         "depends_on": [], "inputs": {"task": {"input": "task"}}, "permissions": permissions},
        {"id": "analysis-results", "join": "all", "depends_on": ["specialist", "design"]},
    ]
    measurement_input = "analysis-results"
    gathered = ["specialist", "design"]
    if proposal.kernel_assessment:
        nodes.append({"id": "kernel", "ref": KERNEL_DESIGNER, "role": "kernel-tuner",
                      "depends_on": ["analysis-results"], "inputs": {"task": _result("analysis-results")},
                      "permissions": permissions})
        measurement_input = "kernel"
        gathered.append("kernel")
    nodes.extend([
        {"id": "measurement", "ref": MEASUREMENT, "depends_on": [measurement_input],
         "inputs": {"task": _result(measurement_input)}},
        {"id": "gather", "join": "all", "depends_on": [*gathered, "measurement"]},
    ])
    return {
        "schema_version": 2,
        "id": identity,
        "version": proposal.version,
        "description": DESCRIPTION.format(direction.replace("-", " ")),
        "resources": [{"id": f"{identity}-instructions", "kind": "instructions", "path": INSTRUCTIONS,
                       "sha256": proposal.instructions_sha256}],
        "permissions": permissions,
        "limits": {"depth": 8, "instances": 128, "concurrency": 4, "material_bytes": 262144},
        "inputs": ["task"],
        "outputs": {"result": _result("gather")},
        "nodes": nodes,
    }


def _version_parts(version, schema, label):
    if (not isinstance(version, str) or len(version) > schema["maxLength"] or
            re.fullmatch(schema["pattern"], version) is None):
        raise ValueError(f"{label}: invalid Workflow version {version!r}")
    return tuple(map(int, version.split(".")))


def _check_catalog():
    catalog = json.loads((PRESETS / "presets.json").read_bytes())["presets"]
    catalog_roots = {entry["root"] for entry in catalog.values()
                     if entry["root"].startswith("ergora-opt-") and entry["root"].endswith("-proposal")}
    generated_roots = {_proposal_id(direction) for direction in PROPOSALS}
    if catalog_roots != generated_roots:
        raise ValueError(f"Proposal catalog mismatch. Missing from authoring source: {sorted(catalog_roots - generated_roots)}. "
                         f"Missing from preset catalog: {sorted(generated_roots - catalog_roots)}.")


def _generate(write):
    _check_catalog()
    version_schema = json.loads(WORKFLOW_SCHEMA.read_bytes())["properties"]["version"]
    changed = {}
    for direction, proposal in PROPOSALS.items():
        definition = _definition(direction, proposal)
        identity = definition["id"]
        revision = _version_parts(proposal.version, version_schema, identity)
        bundle = PRESETS / "workflows" / identity
        if sha256((bundle / INSTRUCTIONS).read_bytes()).hexdigest() != proposal.instructions_sha256:
            raise ValueError(f"{identity}/{INSTRUCTIONS} differs from its pinned digest")
        path = bundle / "workflow.json"
        existing = path.read_bytes()
        rendered = (json.dumps(definition, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if rendered == existing:
            continue
        if write:
            original = json.loads(existing)
            previous = _version_parts(original["version"], version_schema, str(path))
            if original["id"] != identity or revision <= previous:
                raise ValueError(f"Refusing to rewrite {original['id']}@{original['version']}. "
                                 "Use a higher version for a changed definition with the same ID.")
        changed[path] = rendered
    if changed and not write:
        raise ValueError("Generated proposal differs: " + ", ".join(path.parent.name for path in changed))
    for path, rendered in changed.items():
        with TemporaryDirectory(dir=path.parent) as staging:
            staged = Path(staging) / path.name
            staged.write_bytes(rendered)
            staged.chmod(path.stat().st_mode)
            staged.replace(path)
    print(f"Checked {len(PROPOSALS)} pinned proposal workflows, regenerated {len(changed)}.")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate changed workflow.json files after version increases")
    args = parser.parse_args()
    try:
        _generate(args.write)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
