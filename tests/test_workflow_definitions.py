"""Composition contracts through the public package, library and preview interfaces."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, agents, backups, contracts, skill_assets, workflow_definitions as workflows
from ergora.asset_trees import digest_tree
from ergora.state import State


@pytest.fixture
def workflow_retrospective(tmp_path):
    from ergora import handoff, projects
    from test_handoff import evidence, text_evidence

    repo = tmp_path / 'repo'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    state = State(tmp_path / 'state')
    projects.create(state, 'demo', repo)
    agent = agent_definitions.import_bundle(state, EXAMPLES / 'agents/architecture-reviewer')
    inner = workflows.import_bundle(state, write_bundle(tmp_path / 'inner',
        definition('inner-review', [leaf('review', ref(agent, 'agent'))]), 'Complete child context.\r\n' * 100))
    nodes = [child('first', ref(inner, 'workflow')), child('second', ref(inner, 'workflow')),
             {'id': 'gather', 'join': 'all', 'depends_on': ['first', 'second']}]
    source = write_bundle(tmp_path / 'target', definition('target-workflow', nodes), '完整保留限定。\r\n' * 300)
    skill = source / 'skills/target-guide'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_bytes(b'---\nname: target-guide\ndescription: Preserve original qualifications\n---\nKeep unknowns visible.\n')
    (skill / 'references/empty').mkdir(parents=True)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['resources'].append({'id': 'target-guide', 'kind': 'skill', 'path': 'skills/target-guide', 'digest': digest_tree(skill)[0]})
    (source / 'workflow.json').write_bytes(json.dumps(document).encode())
    target = workflows.import_bundle(state, source)
    target_manifest = workflows.prepare_manifest(state.root, document['id'], document['version'], grant(), tmp_path / 'target-manifest')
    installed = workflows.install_preset(state, 'workflow-retrospective')
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    author = workflows.prepare_manifest(state.root, root['id'], root['version'], grant(), tmp_path / 'author-manifest')
    index, blobs = text_evidence(evidence.__wrapped__(), ['Original failure; cost unrecorded.\r\n'])
    packet = tmp_path / 'evidence.zip'
    collected = handoff.create(index, lambda artifact: blobs[artifact['sha256']], packet)
    return state, packet, target, {
        'packet_sha256': collected['sha256'], 'target_manifest': Path(target_manifest['path']),
        'target_digest': target_manifest['digest'], 'next_version': '1.0.1',
        'objective': 'Propose a source-supported root revision, preserving all existing gates.',
        'manifest': Path(author['path']), 'instance': 'root/propose', 'destination': tmp_path / 'input',
        'max_prompt_bytes': 500000}


def workflow_proposal(input_path, result_path):
    import base64

    task = json.loads((input_path / 'task.txt').read_bytes())
    artifact = task['evidence']['artifacts'][0]
    document = deepcopy(task['baseline']['definition'])
    document['version'] = task['baseline']['next_version']
    document['description'] += '; retain uncertainty in source observations'
    document['nodes'][1]['depends_on'].append(document['nodes'][0]['id'])
    text = ('完整保留限定与失败；成本未知。\r\n' * 300).encode()
    proposal = {'schema_version': 1, 'evidence_sha256': task['evidence']['sha256'], 'baseline_digest': task['baseline']['digest'],
        'observations': [{'claim': 'The source records a failure.', 'uncertainty': 'No measured quality or performance benefit.',
            'citations': [{'job_id': artifact['job_id'], 'name': artifact['artifact']['name'], 'sha256': artifact['artifact']['sha256']}]}],
        'negative_results': ['Original failure retained.'], 'cost_and_uncertainty': 'Costs unrecorded; serialization may increase latency.',
        'candidate': {'definition': document, 'resource_changes': {'schema_version': 1, 'operations': [
            {'op': 'write', 'path': 'instructions.md', 'content_base64': base64.b64encode(text).decode(), 'executable_bits': 0}]},
            'hypothesis': 'Explicit ordering and qualifications may improve interpretation.', 'applicability': 'This frozen workflow only.',
            'evaluation_plan': 'Compare a fixed trusted workload and independent holdout; measure regressions and costs.'}}
    result_path.write_bytes(json.dumps({'summary': 'Bounded workflow proposal.', 'artifacts': {'response': json.dumps(proposal)}}).encode())
    return proposal, text


def test_workflow_retrospective_complete_offline_revision_export_import_and_old_manifest(workflow_retrospective, tmp_path, capsys):
    from ergora import cli, retrospectives

    state, packet, target, options = workflow_retrospective
    original = workflows.inspect_manifest(options['target_manifest'], material=True)
    prepared = retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    task = json.loads((options['destination'] / 'task.txt').read_bytes())
    for name, file in task['baseline']['files'].items():
        assert file['text'].encode() == (options['target_manifest'] / name).read_bytes()
    assert any(name.endswith('/skills/target-guide/references/empty') for name in task['baseline']['directories'])
    result = tmp_path / 'result.json'
    proposal, text = workflow_proposal(options['destination'], result)
    sha = hashlib.sha256(result.read_bytes()).hexdigest()
    shutil.rmtree(options['target_manifest'])
    shutil.rmtree(tmp_path / 'target')
    packet.unlink()
    readback = retrospectives.inspect_input(options['destination'], project_id='demo')
    assert readback['digest'] == prepared['digest'] and readback['retrospective_request'] == task
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'check-workflow', str(options['destination']), str(result),
                     '--result-sha256', sha]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert not unused.exists() and checked['input_digest'] == prepared['digest']
    destination = tmp_path / 'candidate'
    receipt = retrospectives.export_workflow(options['destination'], result, destination, result_sha256=sha,
                                              candidate_digest=checked['candidate_digest'])
    assert (destination / 'instructions.md').read_bytes() == text
    assert (destination / 'skills/target-guide/references/empty').is_dir()
    assert checked['revision_preview']['directory_changes']['removed'] == []
    assert workflows.inspect_bundle(destination)['digest'] == receipt['candidate_digest']
    assert workflows.get(state, target['definition']['id'], target['definition']['version'])['digest'] == target['digest']
    imported = workflows.import_bundle(state, destination)
    assert imported['digest'] == checked['candidate_digest']
    new = workflows.prepare_manifest(state.root, target['definition']['id'], options['next_version'], grant(), tmp_path / 'new-manifest')
    new_graph = workflows.inspect_manifest(Path(new['path']), material=True)['composition']
    assert 'root/first' in next(item for item in new_graph['instances'] if item['path'] == 'root/second')['depends_on']
    assert original['composition']['root']['digest'] == target['digest']
    assert workflows.preview(state.root, target['definition']['id'], target['definition']['version'], grant()) == original['composition']
    assert workflows.inspect_input(options['destination'])['digest'] == prepared['digest']
    assert retrospectives.check_workflow(options['destination'], result) == checked
    assert not checked['quality_evaluated'] and not receipt['adoption_authorized']
    assert not list(tmp_path.glob('.retrospective-workflow-export-*'))


@pytest.mark.parametrize('change,reason', [
    ('authority', 'authority'), ('version', 'version'), ('child', 'every node'), ('dependency', 'dependency'),
    ('resource', 'root resource declarations'), ('outside', 'declared root resources'),
    ('cycle', 'cycle'), ('source', 'frozen source'), ('citation', 'absent'),
])
def test_workflow_retrospective_rejects_authority_or_gate_changes(workflow_retrospective, tmp_path, capsys, change, reason):
    from ergora import cli, retrospectives

    state, packet, target, options = workflow_retrospective
    retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    proposal, _ = workflow_proposal(options['destination'], result)
    candidate = proposal['candidate']
    document = candidate['definition']
    if change == 'authority': document['permissions']['shell'] = True
    elif change == 'version': document['version'] = '2.0.0'
    elif change == 'child': document['nodes'][0]['ref']['digest'] = '0' * 64
    elif change == 'dependency': document['nodes'][-1]['depends_on'].remove('first')
    elif change == 'resource': document['resources'][0]['id'] = 'new-resource'
    elif change == 'outside': candidate['resource_changes']['operations'][0]['path'] = 'undeclared.txt'
    elif change == 'cycle': document['nodes'][0]['depends_on'].append('second')
    elif change == 'source': proposal['baseline_digest'] = '0' * 64
    elif change == 'citation': proposal['observations'][0]['citations'][0]['sha256'] = '0' * 64
    result.write_bytes(json.dumps({'summary': 'Unsafe proposal.', 'artifacts': {'response': json.dumps(proposal)}}).encode())
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'check-workflow', str(options['destination']), str(result)]) == 2
    captured = capsys.readouterr()
    assert not captured.out and reason.casefold() in captured.err.casefold() and not unused.exists()
    assert workflows.get(state, target['definition']['id'], target['definition']['version'])['digest'] == target['digest']


def test_workflow_retrospective_null_explicit_selection_and_no_replace(workflow_retrospective, tmp_path):
    from ergora import retrospectives

    state, packet, target, options = workflow_retrospective
    with pytest.raises(ValueError, match='manifest digest'):
        retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}],
                                         **{**options, 'target_digest': '0' * 64})
    assert not options['destination'].exists()
    retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    workflow_proposal(options['destination'], result)
    checked = retrospectives.check_workflow(options['destination'], result)
    for sha, digest, destination, reason in [
        ('0' * 64, checked['candidate_digest'], tmp_path / 'absent', 'original bytes'),
        (checked['result_sha256'], '0' * 64, tmp_path / 'absent', 'selected digest'),
        (checked['result_sha256'], checked['candidate_digest'], options['destination'] / 'inside', 'frozen input'),
        (checked['result_sha256'], checked['candidate_digest'], options['target_manifest'], 'new retrospective export'),
    ]:
        with pytest.raises(ValueError, match=reason):
            retrospectives.export_workflow(options['destination'], result, destination, result_sha256=sha, candidate_digest=digest)
    assert not (tmp_path / 'absent').exists()
    outer = json.loads(result.read_bytes());proposal = json.loads(outer['artifacts']['response']);proposal['candidate'] = None
    outer['artifacts']['response'] = json.dumps(proposal);result.write_bytes(json.dumps(outer).encode())
    checked = retrospectives.check_workflow(options['destination'], result)
    assert checked['candidate_digest'] is None
    with pytest.raises(ValueError, match='no workflow candidate'):
        retrospectives.export_workflow(options['destination'], result, tmp_path / 'absent',
                                        result_sha256=checked['result_sha256'], candidate_digest='0' * 64)


def test_workflow_retrospective_preserves_the_frozen_grant_and_complete_root_view(workflow_retrospective, tmp_path):
    from ergora import retrospectives

    state, packet, target, options = workflow_retrospective
    original = workflows.inspect_manifest(options['target_manifest'], material=True)
    strict = workflows.prepare_manifest(state.root, target['definition']['id'], target['definition']['version'],
        grant(material_bytes=original['composition']['usage']['material_bytes']), tmp_path / 'strict-manifest')
    options.update(target_manifest=Path(strict['path']), target_digest=strict['digest'])
    retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    workflow_proposal(options['destination'], result)
    with pytest.raises(ValueError, match='material_bytes budget'):
        retrospectives.check_workflow(options['destination'], result)
    outer = json.loads(result.read_bytes());proposal = json.loads(outer['artifacts']['response']);proposal['candidate'] = None
    outer['artifacts']['response'] = json.dumps(proposal);result.write_bytes(json.dumps(outer).encode())
    assert retrospectives.check_workflow(options['destination'], result)['candidate_digest'] is None
    task = json.loads((options['destination'] / 'task.txt').read_bytes())
    task['baseline']['definition']['description'] = 'A view that differs from the complete frozen manifest.'
    changed = workflows.prepare_input_from_manifest(options['manifest'], options['instance'], json.dumps(task).encode(),
                                                     tmp_path / 'changed-input', options['max_prompt_bytes'])
    with pytest.raises(ValueError, match='Frozen retrospective root'):
        retrospectives.check_workflow(Path(changed['path']), result)


@pytest.mark.parametrize('place', ['baseline', 'candidate'])
@pytest.mark.parametrize('content', [b'ordinary\x00binary', b'\xff\x01binary'])
def test_workflow_retrospective_rejects_binary_skill_support_files_at_its_own_boundary(workflow_retrospective, tmp_path, place, content):
    import base64
    from ergora import retrospectives

    state, packet, target, options = workflow_retrospective
    before = workflows.definitions(state)
    changes = {'schema_version': 1, 'operations': [{'op': 'write', 'path': 'skills/target-guide/references/data.bin',
        'content_base64': base64.b64encode(content).decode(), 'executable_bits': 0}]}
    if place == 'baseline':
        # The general-purpose library continues to support ordinary binary attachments.
        document = deepcopy(target['definition']);document['version'] = '1.0.2'
        preview = workflows.revise(state, document['id'], target['definition']['version'], target['digest'], document,
            resource_changes=changes, preview_resources=True)
        workflows.revise(state, document['id'], target['definition']['version'], target['digest'], preview['definition'],
            resource_changes=changes, accepted_candidate=preview['candidate'], publish=True)
        target_manifest = workflows.prepare_manifest(state.root, document['id'], document['version'], grant(), tmp_path / 'binary-manifest')
        options.update(target_manifest=Path(target_manifest['path']), target_digest=target_manifest['digest'], next_version='1.0.3')
        with pytest.raises(ValueError):
            retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
        assert not options['destination'].exists()
    else:
        retrospectives.prepare_workflow(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
        result = tmp_path / 'binary-result.json'
        proposal, _ = workflow_proposal(options['destination'], result)
        proposal['candidate']['resource_changes'] = changes
        result.write_bytes(json.dumps({'summary': 'Binary proposal.', 'artifacts': {'response': json.dumps(proposal)}}).encode())
        with pytest.raises(ValueError):
            retrospectives.check_workflow(options['destination'], result)
        assert workflows.definitions(state) == before


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
READ = {"read": ["workspace", "definitions"], "write": [], "shell": False, "network": []}
LIMITS = {"depth": 8, "instances": 128, "concurrency": 4, "material_bytes": 262144}


def ref(document, kind):
    return {"kind": kind, "id": document["definition"]["id"], "version": document["definition"]["version"],
            "digest": document["digest"]}


def write_bundle(path, definition, text=None):
    path.mkdir(parents=True, exist_ok=True)
    if text is not None:
        (path / "instructions.md").write_bytes(text.encode("utf-8"))
        definition["resources"] = [{"id": definition["id"] + "-instructions", "kind": "instructions",
                                     "path": "instructions.md", "sha256": hashlib.sha256(text.encode()).hexdigest()}]
    (path / "workflow.json").write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
    return path


def definition(identity, nodes):
    return {"schema_version": 1, "id": identity, "version": "1.0.0", "description": "Test workflow contract",
            "resources": [], "permissions": deepcopy(READ), "limits": deepcopy(LIMITS), "inputs": ["task"],
            "outputs": {"result": {"node": nodes[-1]["id"], "output": "result"}}, "nodes": deepcopy(nodes)}


def leaf(identity, agent):
    return {"id": identity, "ref": agent, "role": "reviewer", "depends_on": [],
            "inputs": {"task": {"input": "task"}}, "permissions": deepcopy(READ)}


def child(identity, workflow):
    return {"id": identity, "ref": workflow, "depends_on": [], "inputs": {"task": {"input": "task"}}}


def grant(**limits):
    return {"schema_version": 1, "permissions": deepcopy(READ), "limits": {**LIMITS, **limits}}


@pytest.fixture
def base(tmp_path):
    state = State(tmp_path / "state")
    agent = agent_definitions.import_bundle(state, EXAMPLES / "agents/architecture-reviewer")
    return state, ref(agent, "agent"), tmp_path


def imported(base, document, text=None):
    state, _, directory = base
    source = write_bundle(directory / (document["id"] + "-" + document["version"]), document, text)
    return workflows.import_bundle(state, source)


def test_examples_expand_serial_and_parallel_all_join_without_dependency_inheritance(tmp_path):
    for schema in contracts.WORKFLOW_DEFINITIONS.values():
        contracts.StrictValidator.check_schema(schema)
    contracts.StrictValidator.check_schema(contracts.COMPOSITION_GRANT)
    state = State(tmp_path / "state")
    for source in sorted((EXAMPLES / "agents").iterdir()):
        agent_definitions.import_bundle(state, source)
    for source in sorted((EXAMPLES / "composition/agents").iterdir()):
        agent_definitions.import_bundle(state, source)
    for name in ("structure-review", "correctness-review", "test-value-review", "parallel-review", "kernel-delivery", "review-requirements"):
        workflows.import_bundle(state, EXAMPLES / "composition" / name)
    permissions = json.loads((EXAMPLES / "composition/preview-grant.json").read_text())
    result = workflows.preview(state.root, "kernel-delivery", "1.0.0", permissions)
    assert result["executable"] is False and result["usage"]["instances"] == 10
    items = {item["path"]: item for item in result["instances"]}
    assert items["root"]["levels"] == [["root/implement"], ["root/review"]]
    assert len(items["root/review"]["levels"][0]) == 3
    assert set(items["root/review/gather"]["depends_on"]) == {
        "root/review/structure", "root/review/correctness", "root/review/test-value"}
    assert items["root/review"]["depends_on"] == ["root/implement"]
    assert len({item["path"] for item in result["instances"]}) == 10
    for item in items.values():
        if item["kind"] == "agent" and item["role"] == "reviewer":
            ids = [identity for resource in item["resources"] for identity in resource["ids"]]
            assert "kernel-measurement" not in ids and "kernel-delivery-instructions" in ids
            assert "parallel-review-instructions" in ids
            for resource in item["resources"]:
                assert resource["text"] in item["prompt"]
    assert workflows.preview(state.root, "kernel-delivery", "1.0.0", permissions) == result
    new = workflows.preview(state.root, "review-requirements", "1.0.0", permissions)
    assert new["schema_version"] == 2
    assert {item["path"]: item["review_requirement"] for item in new["instances"] if item["kind"] == "agent"} == {
        "root/structure": "required", "root/test-value": "advisory"}


@pytest.mark.parametrize("publish", [False, True])
def test_revision_uses_complete_current_compilation_before_publication(base, publish):
    state, agent, _ = base
    original = imported(base, definition("bounded-root", [leaf("review", agent)]))
    revised = deepcopy(original["definition"])
    revised.update(version="1.0.1", permissions={**READ, "read": ["definitions"]})
    index = state.root / "workflow-definitions/index.json"
    before = index.read_bytes()
    with pytest.raises(ValueError, match="Permission exceeds ancestor/project"):
        workflows.revise(state, revised["id"], original["definition"]["version"], original["digest"], revised,
                         publish=publish)
    assert index.read_bytes() == before
    assert workflows.get(state, revised["id"], original["definition"]["version"]) == original


def test_review_requirement_belongs_to_each_versioned_instance_and_survives_nested_freezing(base):
    state, agent, directory = base
    original = imported(base, definition("expert-review", [leaf("review", agent)]))
    before = workflows.preview(state.root, "expert-review", "1.0.0", grant())
    doc = definition("expert-review", [
        {**leaf("required", agent), "review_requirement": "required"},
        {**leaf("advice", agent), "review_requirement": "advisory"},
        {"id": "gather", "join": "all", "depends_on": ["required", "advice"]}])
    doc.update(schema_version=2, version="2.0.0")
    updated = imported(base, doc)
    outer = definition("nested-requirements", [child("one", ref(updated, "workflow")),
                                                child("two", ref(updated, "workflow"))])
    imported(base, outer)
    preview = workflows.preview(state.root, "nested-requirements", "1.0.0", grant())
    assert preview["schema_version"] == 2
    members = {item["path"]: item for item in preview["instances"] if item["kind"] == "agent"}
    assert {path: item["review_requirement"] for path, item in members.items()} == {
        "root/one/advice": "advisory", "root/one/required": "required",
        "root/two/advice": "advisory", "root/two/required": "required"}
    assert all(item["ref"] == agent and item["permissions"] == READ for item in members.values())
    assert workflows.preview(state.root, "expert-review", "1.0.0", grant()) == before
    assert before["schema_version"] == 1 and "review_requirement" not in before["instances"][-1]
    assert workflows.get(state, "expert-review", "1.0.0")["digest"] == original["digest"]
    manifest = workflows.prepare_manifest(state.root, "nested-requirements", "1.0.0", grant(), directory / "manifest")
    exported = workflows.export(state, "expert-review", "2.0.0", directory / "export-v2")
    assert exported["digest"] == updated["digest"]
    assert workflows.inspect_bundle(Path(exported["destination"]))["definition"] == doc
    archive = directory / "requirements-backup"
    assert backups.create(state.root, archive, offline=True)["workflow_definitions"] == 3
    shutil.rmtree(state.root)
    assert workflows.inspect_manifest(Path(manifest["path"]), material=True)["composition"] == preview
    backups.restore(state.root, archive, offline=True)
    assert workflows.preview(state.root, "nested-requirements", "1.0.0", grant()) == preview
    assert workflows.preview(state.root, "expert-review", "1.0.0", grant()) == before


@pytest.mark.parametrize("failure", ["v1-field", "missing", "invalid", "non-reviewer", "workflow", "join", "unknown-version"])
def test_review_requirement_is_explicit_and_only_valid_on_v2_reviewer_instances(base, failure):
    state, agent, directory = base
    node = {**leaf("review", agent), "review_requirement": "advisory"}
    doc = definition("bad-requirement", [node])
    doc["schema_version"] = 2
    if failure == "v1-field":
        doc["schema_version"] = 1
    elif failure == "missing":
        del doc["nodes"][0]["review_requirement"]
    elif failure == "invalid":
        doc["nodes"][0]["review_requirement"] = "ignore-errors"
    elif failure == "non-reviewer":
        doc["nodes"][0]["role"] = "implementer"
    elif failure == "workflow":
        sub = imported(base, definition("sub", [leaf("review", agent)]))
        doc["nodes"] = [{**child("review", ref(sub, "workflow")), "review_requirement": "advisory"}]
    elif failure == "join":
        doc["nodes"].append({"id": "gather", "join": "all", "depends_on": ["review"],
                             "review_requirement": "advisory"})
    else:
        doc["schema_version"] = 3
    registered = workflows.definitions(state)
    with pytest.raises(ValueError, match="Workflow definition"):
        workflows.import_bundle(state, write_bundle(directory / "invalid", doc))
    assert workflows.definitions(state) == registered


def test_repeated_references_are_distinct_instances_and_preserve_ancestor_sources(base):
    state, agent, _ = base
    sub = imported(base, definition("sub", [leaf("review", agent)]), "Sub instructions.\n")
    outer = imported(base, definition("outer", [child("first", ref(sub, "workflow")), child("second", ref(sub, "workflow"))]),
                     "Root instructions.\n")
    result = workflows.preview(state.root, "outer", "1.0.0", grant(concurrency=1))
    agents = [item for item in result["instances"] if item["kind"] == "agent"]
    assert [item["path"] for item in agents] == ["root/first/review", "root/second/review"]
    for item in agents:
        assert item["prompt"].index("Root instructions.") < item["prompt"].index("Sub instructions.")
        assert [scope["limit"] for scope in item["concurrency_scopes"]] == [1, 4, 4]
        assert all(source["instance"] in ("root", item["parent"], item["path"])
                   for material in item["resources"] for source in material["sources"])
    assert agents[0]["prompt_sha256"] != agents[1]["prompt_sha256"]
    assert outer["definition"]["nodes"][0]["ref"] == outer["definition"]["nodes"][1]["ref"]


@pytest.mark.parametrize("failure", ["missing-ref", "digest", "role", "input", "output", "not-dependent", "child-input"])
def test_unresolvable_references_and_port_bindings_never_publish(base, failure):
    state, agent, directory = base
    doc = definition("broken", [leaf("first", agent), leaf("second", agent)])
    if failure == "missing-ref":
        doc["nodes"][0]["ref"] = {**agent, "id": "absent"}
    elif failure == "digest":
        doc["nodes"][0]["ref"] = {**agent, "digest": "0" * 64}
    elif failure == "role":
        doc["nodes"][0]["role"] = "implementer"
    elif failure == "input":
        doc["nodes"][0]["inputs"]["task"] = {"input": "absent"}
    elif failure == "output":
        doc["outputs"]["result"]["output"] = "absent"
    elif failure == "not-dependent":
        doc["nodes"][1]["inputs"]["task"] = {"node": "first", "output": "result"}
    else:
        del doc["nodes"][0]["inputs"]["task"]
    with pytest.raises(ValueError):
        workflows.import_bundle(state, write_bundle(directory / "broken", doc))
    assert workflows.definitions(state) == [] and not (state.root / "workflow-definitions").exists()


@pytest.mark.parametrize("failure", ["cycle", "duplicate", "unknown", "join-empty", "version", "limit-bool", "unknown-field"])
def test_local_graph_and_schema_are_checked_without_library_access(base, failure):
    _, agent, directory = base
    doc = definition("broken", [leaf("first", agent), leaf("second", agent)])
    if failure == "cycle":
        doc["nodes"][0]["depends_on"] = ["second"]
        doc["nodes"][1]["depends_on"] = ["first"]
    elif failure == "duplicate":
        doc["nodes"][1]["id"] = "first"
    elif failure == "unknown":
        doc["nodes"][0]["depends_on"] = ["absent"]
    elif failure == "join-empty":
        doc["nodes"] = [{"id": "first", "join": "all", "depends_on": []}]
    elif failure == "version":
        doc["schema_version"] = True
    elif failure == "limit-bool":
        doc["limits"]["instances"] = True
    else:
        doc["python_expression"] = "arbitrary()"
    with pytest.raises(ValueError):
        workflows.inspect_bundle(write_bundle(directory / "broken", doc))


@pytest.mark.parametrize("access,value", [("read", ["workspace-private"]), ("write", ["workspace"]),
                                         ("shell", True), ("network", ["https://api.example.com"])])
def test_descendants_cannot_broaden_any_permission(base, access, value):
    _, agent, _ = base
    doc = definition("escalation", [leaf("review", agent)])
    doc["nodes"][0]["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission"):
        imported(base, doc)


@pytest.mark.parametrize("access,value", [("read", ["workspace-other"]), ("write", ["definitions"]),
                                         ("read", ["workspace/../private"]), ("network", ["https://user@api.example.com"]),
                                         ("network", ["https://api.example.com/path"]), ("network", ["https://api.example.com:99999"])])
def test_permission_mounts_paths_and_network_origins_have_unambiguous_meaning(base, access, value):
    _, agent, directory = base
    doc = definition("bad-permissions", [leaf("review", agent)])
    doc["permissions"][access] = value
    with pytest.raises(ValueError):
        workflows.inspect_bundle(write_bundle(directory / "bad-permissions", doc))


@pytest.mark.parametrize("access,value", [
    ("read", ["definitions/agent"]), ("read", ["definitions/agent/architecture-reviewer"]),
    ("read", ["definitions/workflow/Bad-ID/1.0.0"]), ("read", ["definitions/agent/architecture-reviewer/latest"]),
    ("network", ["https://*.example.com"]), ("network", ["https://api example.com"]),
    ("network", ["https://api.example.com:"]), ("network", ["https://api.example.com:443"]),
])
def test_illegal_definition_scopes_and_network_origins_rejected_for_definition_and_explicit_grant(base, access, value):
    state, agent, directory = base
    doc = definition("strict", [leaf("review", agent)])
    imported(base, doc)
    invalid_grant = grant()
    invalid_grant["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission|Network"):
        workflows.preview(state.root, "strict", "1.0.0", invalid_grant)
    doc["permissions"][access] = value
    doc["nodes"][0]["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission|Network"):
        workflows.import_bundle(state, write_bundle(directory / "invalid", doc))
    assert len(workflows.definitions(state)) == 1


def test_exact_version_scopes_dns_and_ip_origins_remain_supported(base):
    state, agent, _ = base
    doc = definition("strict", [leaf("review", agent)])
    permissions = {**READ, "read": ["workspace/src", "definitions/agent/architecture-reviewer/1.0.0"],
                   "network": ["https://api.example.com", "http://localhost:8765", "http://127.0.0.1", "https://[::1]:8443"]}
    doc["permissions"] = deepcopy(permissions)
    doc["nodes"][0]["permissions"] = deepcopy(permissions)
    imported(base, doc)
    actual = workflows.preview(state.root, "strict", "1.0.0", {**grant(), "permissions": permissions})
    assert actual["instances"][-1]["permissions"] == permissions


def test_narrowing_read_cannot_remove_required_inherited_material_even_when_agent_itself_is_readable(base):
    _, agent, _ = base
    doc = definition("inherited", [leaf("review", agent)])
    doc["nodes"][0]["permissions"]["read"] = ["definitions/agent/architecture-reviewer/1.0.0"]
    with pytest.raises(ValueError, match="Required inherited resource is not readable"):
        imported(base, doc, "Mandatory inherited material.\n")


@pytest.mark.parametrize("collision", ["id", "skill-name", "identical-skill"])
def test_resource_identity_and_real_skill_loading_name_conflicts(base, collision):
    state, agent, directory = base
    doc = definition("resources", [leaf("review", agent)])
    source = write_bundle(directory / "resources", doc)
    if collision == "id":
        (source / "other.md").write_text("Different instructions.\n")
        doc["resources"] = [{"id": "initial-instructions", "kind": "instructions", "path": "other.md",
                             "sha256": hashlib.sha256((source / "other.md").read_bytes()).hexdigest()}]
    else:
        skill = source / "skills/architecture-evidence"
        shutil.copytree(EXAMPLES / "agents/architecture-reviewer/skills/architecture-evidence", skill)
        if collision == "skill-name":
            with (skill / "SKILL.md").open("a", encoding="utf-8") as stream:
                stream.write("\nExtra instructions.\n")
        doc["resources"] = [{"id": "other-logical-id", "kind": "skill", "path": "skills/architecture-evidence",
                             "digest": skill_assets.digest_tree(skill)[0]}]
    write_bundle(source, doc)
    if collision != "identical-skill":
        with pytest.raises(ValueError, match="conflict"):
            workflows.import_bundle(state, source)
    else:
        workflows.import_bundle(state, source)
        result = workflows.preview(state.root, "resources", "1.0.0", grant())
        materials = result["instances"][-1]["resources"]
        skills = [item for item in materials if item["kind"] == "skill"]
        assert len(skills) == 1 and skills[0]["ids"] == ["other-logical-id", "architecture-evidence"]
        assert len(skills[0]["sources"]) == 2


def test_every_ancestor_and_the_project_bound_expansion_and_static_prompt_bytes(base):
    state, agent, _ = base
    sub = imported(base, definition("sub", [leaf("review", agent)]))
    imported(base, definition("outer", [child("one", ref(sub, "workflow")), child("two", ref(sub, "workflow"))]))
    result = workflows.preview(state.root, "outer", "1.0.0", grant())
    assert result["usage"]["instances"] == 5
    size = result["usage"]["material_bytes"]
    assert workflows.preview(state.root, "outer", "1.0.0", grant(material_bytes=size))["usage"] == result["usage"]
    for small in ({"depth": 2}, {"instances": 4}, {"material_bytes": size - 1}):
        with pytest.raises(ValueError, match="budget exceeded"):
            workflows.preview(state.root, "outer", "1.0.0", grant(**small))
    too_small = definition("local-limit", [leaf("review", agent)])
    too_small["limits"]["instances"] = 1
    with pytest.raises(ValueError, match="budget exceeded"):
        imported(base, too_small)


def test_new_parent_and_child_revision_can_raise_permissions_together_without_changing_old_root(base):
    state, agent, _ = base
    subdoc = definition("sub", [leaf("review", agent)])
    sub = imported(base, subdoc)
    rootdoc = definition("outer", [child("review", ref(sub, "workflow"))])
    imported(base, rootdoc)
    old = workflows.preview(state.root, "outer", "1.0.0", grant())
    subdoc["version"] = "1.0.1"
    for permissions in (subdoc["permissions"], subdoc["nodes"][0]["permissions"]):
        permissions["write"] = ["workspace/src"]
    newer_sub = imported(base, subdoc)
    rootdoc["version"] = "1.0.1"
    rootdoc["nodes"][0]["ref"] = ref(newer_sub, "workflow")
    with pytest.raises(ValueError, match="Permission exceeds"):
        imported(base, rootdoc)
    rootdoc["permissions"]["write"] = ["workspace/src"]
    imported(base, rootdoc)
    with pytest.raises(ValueError, match="Permission exceeds"):
        workflows.preview(state.root, "outer", "1.0.1", grant())
    updated_grant = grant()
    updated_grant["permissions"]["write"] = ["workspace/src"]
    new = workflows.preview(state.root, "outer", "1.0.1", updated_grant)
    assert new["instances"][-1]["permissions"]["write"] == ["workspace/src"]
    assert workflows.preview(state.root, "outer", "1.0.0", grant()) == old
    assert new["preview_sha256"] != old["preview_sha256"]


def test_workflow_versions_export_and_offline_backup_preserve_the_complete_reference_tree(base):
    state, agent, directory = base
    bundle = imported(base, definition("review", [leaf("review", agent)]), "Persistent instructions.\n")
    expected = workflows.preview(state.root, "review", "1.0.0", grant())
    exported = workflows.export(state, "review", "1.0.0", directory / "export")
    assert exported["digest"] == bundle["digest"]
    assert workflows.import_bundle(state, Path(exported["destination"])) == bundle
    changed = deepcopy(bundle["definition"])
    changed["description"] = "Different same-version content"
    with pytest.raises(ValueError, match="new version"):
        imported(base, changed)
    archive = directory / "backup"
    assert backups.create(state.root, archive, offline=True)["workflow_definitions"] == 1
    shutil.rmtree(state.root)
    backups.restore(state.root, archive, offline=True)
    assert workflows.preview(state.root, "review", "1.0.0", grant()) == expected
    # Even a self-consistent local object/index cannot mask a broken cross-library reference.
    object_path = Path(bundle["path"])
    definition_path = object_path / "workflow.json"
    corrupted = json.loads(definition_path.read_text())
    corrupted["nodes"][0]["ref"]["digest"] = "0" * 64
    definition_path.write_text(json.dumps(corrupted))
    new_digest = digest_tree(object_path)[0]
    object_path.rename(object_path.with_name(new_digest))
    index = state.root / "workflow-definitions/index.json"
    document = json.loads(index.read_text())
    document["definitions"]["review"]["1.0.0"] = new_digest
    index.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="reference digest mismatch"):
        backups.create(state.root, directory / "corrupt-backup", offline=True)


def test_failed_first_workflow_publication_leaves_no_library_and_can_retry(base, monkeypatch):
    state, agent, directory = base
    source = write_bundle(directory / "review", definition("review", [leaf("review", agent)]))
    original = Path.replace
    def interrupted(path, destination):
        if Path(destination).name == "index.json":
            raise OSError("interrupted reference publication")
        return original(path, destination)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", interrupted)
        with pytest.raises(OSError, match="interrupted"):
            workflows.import_bundle(state, source)
    assert not (state.root / "workflow-definitions").exists()
    assert backups.create(state.root, directory / "after-interruption", offline=True)["workflow_definitions"] == 0
    first = workflows.import_bundle(state, source)
    assert workflows.import_bundle(state, source) == first


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_nested_history_is_readable_but_new_admission_is_rejected_after_policy_change(base, monkeypatch, damage):
    state, agent, directory = base
    sub = imported(base, definition("sub", [leaf("review", agent)]), "Child instructions.\n")
    outer = imported(base, definition("outer", [child("child", ref(sub, "workflow"))]), "Parent instructions.\n")
    expected = workflows.get(state, "outer", "1.0.0", material=True)
    listing = workflows.definitions(state)
    workflows.preview(state.root, "outer", "1.0.0", grant())
    indexes = {kind: (state.root / f"{kind}-definitions/index.json").read_bytes() for kind in ("agent", "workflow")}
    def reject(role, binding, **kwargs):
        raise ValueError("Current policy rejects this binding")
    monkeypatch.setattr(agents, "validate_binding", reject)
    assert workflows.get(state, "outer", "1.0.0", material=True) == expected
    assert workflows.definitions(state) == listing and workflows.verify_store(state.root) == 2
    exported = directory / "export"
    assert workflows.export(state, "outer", "1.0.0", exported)["digest"] == outer["digest"]
    assert digest_tree(exported)[0] == outer["digest"]
    for operation in (lambda: workflows.preview(state.root, "outer", "1.0.0", grant()),
                      lambda: workflows.import_bundle(state, exported),
                      lambda: workflows.library(state.root).import_bundle(exported)):
        with pytest.raises(ValueError, match="Current policy"):
            operation()
    archive = directory / "backup"
    assert backups.create(state.root, archive, offline=True)["workflow_definitions"] == 2
    backups.verify(archive)
    state.root.rename(directory / "kept-original")
    backups.restore(state.root, archive, offline=True)
    assert workflows.get(state, "outer", "1.0.0", material=True) == expected
    assert all((state.root / f"{kind}-definitions/index.json").read_bytes() == content for kind, content in indexes.items())
    with pytest.raises(ValueError, match="Current policy"):
        workflows.preview(state.root, "outer", "1.0.0", grant())
    # A removed backend does not hide damage in the retained reference tree.
    stored = agent_definitions.get(state, agent["id"], agent["version"])
    if damage == "missing":
        shutil.rmtree(stored["path"])
    else:
        (Path(stored["path"]) / "instructions.md").write_text("Changed historical content", encoding="utf-8")
    with pytest.raises((OSError, ValueError)) as failure:
        backups.create(state.root, directory / "corrupt-backup", offline=True)
    assert "Current policy" not in str(failure.value) and not (directory / "corrupt-backup").exists()


def test_cli_check_and_failed_preview_do_not_create_state(tmp_path):
    absent = tmp_path / "absent"
    def cli(*arguments):
        return subprocess.run([sys.executable, "-m", "ergora", "--home", str(absent), "composition", *arguments],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
    checked = cli("check", str(EXAMPLES / "composition/parallel-review"), "--material")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["resources"][0]["text"] and not absent.exists()
    missing = cli("preview", "parallel-review", "1.0.0", "--grant", str(EXAMPLES / "composition/preview-grant.json"))
    assert missing.returncode == 2 and "Unknown Workflow definition" in missing.stderr and not absent.exists()


def test_prepared_input_retains_every_ancestor_skill_tree_and_is_independent_of_source_state(base, monkeypatch, capsys):
    from ergora.cli import main

    state, agent, directory = base
    sub = imported(base, definition("sub", [leaf("review", agent)]), "Child instructions.\n")
    root_source = write_bundle(directory / "outer", definition("outer", [child("child", ref(sub, "workflow"))]),
                               "Parent instructions.\n")
    skill = root_source / "skills/kernel-measurement"
    shutil.copytree(EXAMPLES / "agents/kernel-implementer/skills/kernel-measurement", skill)
    doc = json.loads((root_source / "workflow.json").read_text())
    doc["resources"].append({"id": "parent-measurement", "kind": "skill", "path": "skills/kernel-measurement",
                             "digest": digest_tree(skill)[0]})
    (root_source / "workflow.json").write_text(json.dumps(doc), encoding="utf-8")
    workflows.import_bundle(state, root_source)
    indexes = {kind: (state.root / f"{kind}-definitions/index.json").read_bytes() for kind in ("agent", "workflow")}
    raw_task = b"\xef\xbb\xbf" + "Check structure. 核对结构。\r\n".encode("utf-8")
    prepared = workflows.prepare_input(state.root, "outer", "1.0.0", "root/child/review", grant(), raw_task,
                                       directory / "prepared", 30000)
    checked = workflows.inspect_input(directory / "prepared", material=True)
    assert checked["request"]["execution_authorized"] is False and checked["digest"] == prepared["digest"]
    assert checked["prompt"].index("Parent instructions.") < checked["prompt"].index("Child instructions.")
    assert (skill / "SKILL.md").read_text() in checked["prompt"] and "Check structure. 核对结构。\r\n" in checked["prompt"]
    assert (directory / "prepared/task.txt").read_bytes() == raw_task
    copied_skill = next((directory / "prepared/assets/workflow-definitions/objects").glob("*/skills/kernel-measurement"))
    assert digest_tree(copied_skill) == digest_tree(skill)
    size = checked["request"]["prompt_bytes"]
    assert size == len(checked["prompt"].encode("utf-8")) and size > len(checked["prompt"])
    assert workflows.prepare_input(state.root, "outer", "1.0.0", "root/child/review", grant(), raw_task,
                                   directory / "exact-limit", size)["request"]["prompt_bytes"] == size
    with pytest.raises(ValueError, match="input byte limit"):
        workflows.prepare_input(state.root, "outer", "1.0.0", "root/child/review", grant(), raw_task,
                                directory / "over-limit", size - 1)
    assert not (directory / "prepared/assets/ergora.sqlite3").exists()
    task = directory / "task.txt"
    task.write_bytes(raw_task)
    permissions = directory / "grant.json"
    permissions.write_text(json.dumps(grant()), encoding="utf-8")
    assert main(["--home", str(state.root), "composition", "prepare", "outer", "1.0.0", "root/child/review",
                 "--grant", str(permissions), "--task", str(task), "--directory", str(directory / "cli-prepared"),
                 "--max-prompt-bytes", "30000"]) == 0
    assert json.loads(capsys.readouterr().out)["digest"] == checked["digest"]
    assert all((state.root / f"{kind}-definitions/index.json").read_bytes() == data for kind, data in indexes.items())
    def reject(*args, **kwargs):
        raise ValueError("Current policy rejects the backend")
    monkeypatch.setattr(agents, "validate_binding", reject)
    assert workflows.inspect_input(directory / "prepared")["digest"] == checked["digest"]
    with pytest.raises(ValueError, match="Current policy"):
        workflows.prepare_input(state.root, "outer", "1.0.0", "root/child/review", grant(), raw_task,
                                directory / "denied", 30000)
    shutil.rmtree(state.root)
    assert main(["--home", str(state.root), "composition", "verify-input", str(directory / "cli-prepared"), "--material"]) == 0
    assert json.loads(capsys.readouterr().out)["prompt"] == checked["prompt"] and not state.root.exists()


@pytest.mark.parametrize("damage", ["task", "prompt", "composition", "asset", "extra", "schema"])
def test_prepared_input_recomputes_material_instead_of_trusting_claimed_hashes(base, damage):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]), "Required parent instructions.\n")
    target = directory / "prepared"
    workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
    if damage == "task":
        (target / "task.txt").write_bytes(b"Different task.")
    elif damage == "prompt":
        (target / "prompt.txt").write_bytes(b"Material silently removed.")
        request = json.loads((target / "request.json").read_text())
        request["prompt_sha256"] = hashlib.sha256((target / "prompt.txt").read_bytes()).hexdigest()
        (target / "request.json").write_text(json.dumps(request), encoding="utf-8")
    elif damage == "composition":
        (target / "composition.json").write_bytes(b"null")
    elif damage == "asset":
        stored = next((target / "assets/agent-definitions/objects").glob("*/instructions.md"))
        stored.write_bytes(b"Different historical instructions.")
    elif damage == "extra":
        (target / "unrelated.txt").write_bytes(b"Not part of this input")
    else:
        request = json.loads((target / "request.json").read_text())
        request["schema_version"] = True
        (target / "request.json").write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError):
        workflows.inspect_input(target)


@pytest.mark.parametrize("failure", ["workflow", "missing", "capacity", "zero", "bool", "empty", "nul", "encoding", "existing", "store"])
def test_invalid_input_never_publishes_a_partial_bundle(base, failure):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    selected, task, limit = "root/review", b"Review.", 30000
    target = directory / "prepared"
    if failure == "workflow": selected = "root"
    elif failure == "missing": selected = "root/absent"
    elif failure == "capacity": limit = 1
    elif failure == "zero": limit = 0
    elif failure == "bool": limit = True
    elif failure == "empty": task = b" \n"
    elif failure == "nul": task = b"bad\0task"
    elif failure == "encoding": task = b"\xff"
    elif failure == "existing": target.mkdir()
    else: target = state.root / "agent-definitions/inside-library"
    with pytest.raises(ValueError):
        workflows.prepare_input(state.root, "review", "1.0.0", selected, grant(), task, target, limit)
    assert target.exists() == (failure == "existing")
    assert not list(target.parent.glob(".composition-bundle-*"))


def test_input_copy_failure_cleans_the_entire_staged_bundle(base, monkeypatch):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    original = agent_definitions.library(state.root).__class__.import_bundle
    def interrupted(store, source):
        result = original(store, source)
        if store.kind == "workflow":
            raise OSError("interrupted input copy")
        return result
    monkeypatch.setattr(agent_definitions.library(state.root).__class__, "import_bundle", interrupted)
    with pytest.raises(OSError, match="interrupted input copy"):
        workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", directory / "prepared", 30000)
    assert not (directory / "prepared").exists() and not list(directory.glob(".composition-bundle-*"))
    assert workflows.preview(state.root, "review", "1.0.0", grant())["usage"]["instances"] == 2


def test_input_aggregate_asset_limit_is_bounded_across_individually_valid_packages(base):
    state, agent, directory = base
    nodes = []
    for number in range(3):
        path = directory / f"agent-{number}"
        shutil.copytree(EXAMPLES / "agents/architecture-reviewer", path)
        (path / "attachment.bin").write_bytes(b"x" * 3_400_000)
        doc = json.loads((path / "agent.json").read_text())
        doc["id"] = f"reviewer-{number}"
        (path / "agent.json").write_text(json.dumps(doc), encoding="utf-8")
        saved = agent_definitions.import_bundle(state, path)
        nodes.append(leaf(f"review-{number}", ref(saved, "agent")))
    imported(base, definition("review", nodes))
    with pytest.raises(ValueError, match="10 MB"):
        workflows.prepare_input(state.root, "review", "1.0.0", "root/review-0", grant(), b"Review.", directory / "prepared", 30000)
    assert not (directory / "prepared").exists() and not list(directory.glob(".composition-bundle-*"))


@pytest.mark.parametrize("field,value", [("schema_version", True), ("executable", 0), ("instances", 2.0)])
def test_input_composition_preserves_json_types(base, field, value):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    target = directory / "prepared"
    workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
    path = target / "composition.json"
    document = json.loads(path.read_text())
    if field == "instances":
        document["usage"][field] = value
    else:
        document[field] = value
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        workflows.inspect_input(target)


def test_input_verification_rejects_index_changes_during_compilation(base, monkeypatch):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    target = directory / "prepared"
    workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
    original = workflows._Compilation.compile
    def changing(compilation, document):
        path = target / "assets/workflow-definitions/index.json"
        path.write_bytes(path.read_bytes() + b"\n")
        return original(compilation, document)
    monkeypatch.setattr(workflows._Compilation, "compile", changing)
    with pytest.raises(ValueError, match="changed during verification"):
        workflows.inspect_input(target)


def test_input_publish_keeps_a_concurrently_created_empty_destination(base, monkeypatch):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    original = workflows.publish_directory
    created = []
    def competing(staged, destination):
        destination.mkdir()
        created.append(destination.stat().st_ino)
        original(staged, destination)
    monkeypatch.setattr(workflows, "publish_directory", competing)
    target = directory / "prepared"
    with pytest.raises(FileExistsError):
        workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
    assert target.stat().st_ino == created[0] and not list(target.iterdir())
    assert not list(directory.glob(".composition-bundle-*"))


@pytest.mark.parametrize("final_files", [500, 501])
def test_input_file_limit_counts_published_assets_without_temporary_locks(base, final_files):
    state, agent, directory = base
    source = write_bundle(directory / "review", definition("review", [leaf("review", agent)]))
    # Four input files, two library indexes, one Workflow entry and the referenced Agent tree.
    agent_files = len(agent_definitions.get(state, agent["id"], agent["version"])["files"])
    for number in range(final_files - 7 - agent_files):
        (source / f"attachment-{number}.txt").write_bytes(b"")
    workflows.import_bundle(state, source)
    target = directory / "prepared"
    if final_files == 500:
        workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
        assert len(digest_tree(target)[1]) == 500
    else:
        with pytest.raises(ValueError, match="500 files"):
            workflows.prepare_input(state.root, "review", "1.0.0", "root/review", grant(), b"Review.", target, 30000)
        assert not target.exists()
    assert not list(directory.glob(".composition-bundle-*"))
