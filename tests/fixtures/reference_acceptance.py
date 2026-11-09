"""Two backend protocol fixtures through all existing stage/evidence owners; no model calls."""

import asyncio
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import threading

from ergora import agent_runs, agents, projects, reference, registrations
from ergora.state import State


async def main():
    root, kind, backend = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    mode = sys.argv[4] if len(sys.argv) > 4 else "legacy-registration"
    composition_mode = mode.startswith("composition")
    installation = root / "installation"
    for part in ("local", "upstream/platform"):
        shutil.copytree(reference.ROOT / "platform" / part, installation / part)
    (installation / ".venv").symlink_to(sys.prefix, target_is_directory=True)
    config, runtime = root / "config", root / "runtime"
    config.mkdir()
    runtime.mkdir()
    os.environ.update(AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime), ERGORA_FIXTURE_KEY="not-a-secret")
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from agent_platform.core import git, read, write
    from agent_platform.projects import register, create_task
    from agent_platform.sandbox import container_identity
    from dev_platform.adapter import FileAdapter, sha
    from dev_platform.activities import Activities
    from dev_platform.workflow import DevelopmentWorkflow
    identity = container_identity()
    if identity is None:
        print(json.dumps({"skip": "Reference executor requires an acknowledged Docker/Podman boundary"}))
        return
    programs = root / "bin"
    programs.mkdir()
    fixture = Path(__file__).with_name("stage_agent.py")
    codex = programs / "pinned-codex"
    codex.write_text(f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(fixture)!r},run_name='__main__')\n")
    codex.chmod(0o700)
    wrong_codex = programs / "codex"
    wrong_codex.write_text("#!/bin/sh\nexit 99\n")
    wrong_codex.chmod(0o700)
    os.environ["PATH"] = str(programs) + os.pathsep + os.environ["PATH"]
    write(config / "platform.json", {"current_container_trust_acknowledged": True,
        "container_boundary": identity, "stage_walltime_seconds": 20, "max_parallel_jobs": 2,
        "codex_env_key": "ERGORA_FIXTURE_KEY", "codex_bin": str(codex), "reviewer": "codex"})
    (config / "codex.toml").write_text("")
    if mode == 'composition-task-mcp':
        platform = read(config / 'platform.json')
        platform.update(codex_bin=shutil.which('codex', path=os.environ['PATH'].split(os.pathsep, 1)[1]),
                        codex_env_key='LINGZHI_API_KEY', stage_walltime_seconds=300)
        assert platform['codex_bin'] and os.environ.get('LINGZHI_API_KEY')
        write(config / 'platform.json', platform, replace=True)
        shutil.copyfile(os.environ['ERGORA_HOSTED_REVIEW_CONFIG'], config / 'codex.toml')
    adapter_config = {key: str(runtime / key) for key in ("requests", "receipts", "artifacts", "approvals", "fences")}
    adapter_config["trusted_receipts"] = True
    write(config / "adapter.json", adapter_config)
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init")
    (repo / "src").mkdir()
    (repo / "src/base.py").write_bytes(b"VALUE = 1\r\n" if composition_mode else b"VALUE = 1\n")
    if mode == 'composition-import-shadowing':
        # Candidate imports must never run inside the installed trusted driver.
        shadow = "from pathlib import Path\nPath(" + repr(str(root / 'shadow-imported')) + ").touch()\nraise RuntimeError('candidate import executed')\n"
        (repo / 'ergora').mkdir()
        (repo / 'ergora/__init__.py').write_text(shadow)
        (repo / 'json.py').write_text(shadow)
    elif mode == 'composition-replace-object':
        (repo / 'src/removed.txt').write_bytes(b'Original base-only material\r\n')
    elif mode == 'composition-binary':
        (repo / 'src/binary.bin').write_bytes(b'not text\0content')
    elif mode == 'composition-symlink':
        (repo / 'src/link.txt').symlink_to('base.py')
    elif mode == 'composition-capacity':
        (repo / 'src/complete.txt').write_text('x' * 1100000)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture baseline")
    check = [sys.executable, "-c", "import ast,pathlib;[ast.parse(p.read_text()) for p in pathlib.Path('{repo}/src').glob('*.py')]"]
    if mode == 'verify-command-failure':
        check[-1] += '; assert not pathlib.Path(' + repr(str(root / 'fail-verify')) + ').exists()'
    checks = {key: check for key in ("behavior", "architecture", "knowledge", "integration", "compatibility", "migration-rollback")}
    write(root / "checks.json", checks)
    task_input = json.loads((reference.ROOT / "platform/templates" / kind / "input.json").read_text())
    task_input.update(goal="Add a fixture module", allowed_paths=["src"],
        work_units=[{"id": "unit", "depends_on": [], "paths": ["src"], "instructions": "Add VALUE = 42 in src/new.py"}])
    if mode == 'composition-replace-object':
        task_input['work_units'][0]['instructions'] += '; fixture-delete-base-only'
    write(root / "input.json", task_input)
    state = State(root / "control")
    projects.create(state, "demo", repo)
    binding = {"tool": "codex", "sandbox": "current-container"} if backend == "codex" else {
        "tool": "command", "argv": [sys.executable, str(fixture)], "protocol": "stage-json-v1", "capabilities": agents.GENERAL_CAPABILITIES}
    cancellation = len(sys.argv) > 4 and sys.argv[4] == "cancel-ignore-term"
    if cancellation:
        binding["argv"] += ["--wait-for-cancellation", str(root / "action-ready"), str(root / "late-write")]
    for role in ("inspector", "planner", "implementer", "reviewer"):
        projects.bind(state, "demo", role, binding, state.project("demo")["revision"])
    if mode.startswith("unified") or mode == "imported-registration" or composition_mode:
        definition = {"schema_version": 1, "id": "demo", "repo": str(repo), "templates": [kind],
                      "tracker": {"kind": "github", "project": "fixtures/demo"}, "allowed_paths": ["src"],
                      "checks": checks, "scope_policy": {"schema_version": 1, "protected_paths": [".git"],
                                                          "max_changed_files": 200, "max_changed_lines": 20000},
                      "execution": {"installation": str(installation), "config_directory": str(config), "state_directory": str(runtime)}}
        if mode == "imported-registration":
            register("demo", repo, "github", "fixtures/demo", ["src"], root / "checks.json")
            sources = {path: (config / path).read_bytes() for path in ("projects/demo.json", "policies/demo/scope.json")}
            specification = {key: definition[key] for key in ("schema_version", "id", "repo", "templates", "execution")}
            preview = registrations.preview_import(state, specification, state.project("demo")["revision"])
            registrations.apply_import(state, specification, state.project("demo")["revision"], preview["preview_sha256"])
            assert all((config / path).read_bytes() == raw for path, raw in sources.items())
        else:
            registrations.register(state, definition, state.project("demo")["revision"])
    else:
        register("demo", repo, "github", "fixtures/demo", ["src"], root / "checks.json")
    if composition_mode:
        from ergora import agent_definitions, tasks, workflow_definitions

        examples = Path(__file__).resolve().parents[2] / 'examples'
        agent_definitions.import_bundle(state, examples / 'agents/architecture-reviewer')
        workflow_source = root / 'workflow-source'
        shutil.copytree(examples / 'composition/structure-review', workflow_source)
        graph_definition = read(workflow_source / 'workflow.json')
        if mode.startswith('composition-requirements-') or mode == 'composition-no-worker-sdk-v3':
            graph_definition['schema_version'] = 2
            graph_definition['nodes'][0]['review_requirement'] = 'required'
            graph_definition['nodes'].append({'id': 'gather', 'join': 'all', 'depends_on': ['review']})
            graph_definition['outputs'] = {'result': {'node': 'gather', 'output': 'result'}}
        elif mode.startswith('composition-dag-'):
            first = graph_definition['nodes'][0]
            first['review_requirement'] = 'advisory'
            graph_definition['schema_version'] = 2
            for number in range(1, 5 if mode.endswith('-capacity') else 3):
                node = deepcopy(first)
                previous = 'review' if number == 1 or not mode.endswith('-capacity') else f'review-{number - 1}'
                node.update(id=f'review-{number}', review_requirement='required', depends_on=[previous],
                            inputs={'task': {'node': previous, 'output': 'result'}})
                graph_definition['nodes'].append(node)
            graph_definition['nodes'].append({'id': 'gather', 'join': 'all',
                'depends_on': [node['id'] for node in graph_definition['nodes'][1:]]})
            graph_definition['outputs'] = {'result': {'node': 'gather', 'output': 'result'}}
        elif mode == 'composition-multiple':
            another = deepcopy(graph_definition['nodes'][0])
            another['id'] = 'another'
            graph_definition['nodes'].append(another)
        elif mode == 'composition-read-scope':
            graph_definition['nodes'][0]['permissions']['read'] = ['workspace/src/base.py', 'definitions']
        write(workflow_source / 'workflow.json', graph_definition, replace=True)
        workflow_definitions.import_bundle(state, workflow_source)
        manifest_path = root / 'manifest'
        manifest = workflow_definitions.prepare_manifest(state.root, 'structure-review', '1.0.0',
            read(examples / 'composition/preview-grant.json'), manifest_path)
        task_definition = {'schema_version': 2, 'task_id': 'task-1', 'task_type': kind, 'issue_id': '1', 'input': task_input,
            'composition': {'manifest': str(manifest_path), 'manifest_digest': manifest['digest'],
                            'review_instance': 'root', 'mode': 'task-mcp' if mode == 'composition-task-mcp' else 'text-only'}}
        if mode.startswith('composition-dag-'):
            task_definition['composition'].update(review_protocol='dag-v1', backend_overrides={
                'root/review': {'binding': {'tool': 'codex', 'model': 'fixture-reject'},
                                'reason': 'Transport the original advisory failed receipt without changing its opinion'}})
        if mode in ('composition-review-reject', 'composition-review-timeout', 'composition-review-cancel',
                    'composition-requirements-reject', 'composition-requirements-mutate'):
            model = 'fixture-' + mode.rsplit('-', 1)[1]
            task_definition['composition']['backend_overrides'] = {
                'root/review': {'binding': {'tool': 'codex', 'model': model}, 'reason': 'Explicit native protocol failure fixture'}}
        revision = state.project('demo')['revision']
        preview = tasks.preview(state, 'demo', task_definition, revision)
        tasks.create(state, 'demo', task_definition, revision, preview['preview_sha256'])
        shutil.rmtree(manifest_path)
        shutil.rmtree(state.root / 'agent-definitions')
        shutil.rmtree(state.root / 'workflow-definitions')
    else:
        create_task("demo", kind, "task-1", "1", root / "input.json")
    compiled_path = runtime / "tasks/task-1/compiled.json"
    compiled = read(compiled_path)
    instructions = compiled["package"]["templates"]["instructions.md"]
    instructions_sha = compiled["spec"]["profile"]["template_files"]["instructions.md"]
    if mode == "instructions-missing":
        compiled_path.unlink()
    elif mode == "instructions-tampered":
        compiled["package"]["templates"]["instructions.md"] += "\nChanged instructions\n"
        write(compiled_path, compiled, replace=True)
    elif mode == "instructions-cross-task":
        from dev_platform.portable import compile_task
        task = deepcopy(compiled["task"])
        task["task_id"] = "another-task"
        wrong = compile_task(task, compiled["package"], compiled["policy"], compiled["binding"])
        write(compiled_path, wrong, replace=True)
    elif mode == "instructions-frozen-source":
        shutil.rmtree(installation / "upstream/platform/portable/packages" / kind)
    if mode in ("unified-pending", "unified-drift", "unified-wrong-state"):
        if mode == "unified-drift":
            write(config / "policies/demo/scope.json", {"schema_version": 1, "protected_paths": []}, replace=True)
        else:
            project = state.project("demo")
            if mode == "unified-pending":
                project["registration"]["status"] = "pending"
            else:
                project["registration"]["definition"]["execution"]["state_directory"] = str(root / "wrong-runtime")
            with state.connect() as db:
                db.execute("UPDATE projects SET document=? WHERE id=?", (json.dumps(project), "demo"))
    if composition_mode:
        from ergora.reference_inputs import execution_input
        document = read(runtime / 'tasks/task-1/task.spec.json')
        selected_input = execution_input(document)
        app = selected_input.workflow_type()()
        app.spec, app.admission = selected_input.spec, document
        adapter = selected_input.adapter(adapter_config)
        activities = selected_input.activities(adapter_config)
        requests = selected_input.request_root(runtime / 'requests')
        wrapper = (runtime / 'tasks/task-1/task.spec.json').read_bytes()
    else:
        app = DevelopmentWorkflow()
        app.spec = read(runtime / 'tasks/task-1/task.spec.json')
        adapter = FileAdapter(adapter_config)
        activities = Activities(adapter)
        requests, wrapper = runtime / 'requests', None
    await activities.validate(app.spec)
    records = {}
    frozen_selection = None
    starting = app.spec["request"]["repository"]["starting_sha"]
    if cancellation:
        context = app.context("inventory", starting, dependencies={})
        job = await activities.submit(context)
        def cancel():
            limit = time.monotonic() + 15
            while not (root / "action-ready").exists() and time.monotonic() < limit:
                time.sleep(0.02)
            assert (root / "action-ready").exists()
            write(runtime / "fences/task-1.json", {"reason": "cancellation regression"})
        thread = threading.Thread(target=cancel)
        thread.start()
        receipt = reference.executor(installation, state.root, runtime / "requests/task-1" / (context["job_id"] + ".json"))
        thread.join(timeout=2)
        assert await activities.poll(job) == receipt
        assert receipt["state"] == "CANCELLED", receipt
        assert (root / "action-ready").exists()
        time.sleep(2.2)
        assert not (root / "late-write").exists()
        print(json.dumps({"cancelled": True, "no_late_write": True}))
        return
    def check_formal_evidence(review_receipt):
        job_output = runtime / 'workspaces/task-1/jobs' / review_receipt['job_id']
        call = read(job_output / 'selected-agent/formal-call.json')
        materials = read(job_output / 'selected-agent/materials.json')
        invocation = read(job_output / 'output/selected-agent/invocation.json')
        assert call['candidate_sha'] == materials['candidate_sha'] == review_receipt['candidate_sha']
        base_blob = materials['repository']['base']['files']['src/base.py']['git_object']
        new_blob = materials['repository']['candidate']['files']['src/new.py']['git_object']
        assert materials['repository']['blobs'][base_blob]['text'] == 'VALUE = 1\r\n'
        assert materials['repository']['blobs'][new_blob]['text'] == 'VALUE = 42\n'
        if mode == 'composition-replace-object':
            removed = materials['repository']['base']['files']['src/removed.txt']['git_object']
            assert 'src/removed.txt' not in materials['repository']['candidate']['files']
            assert materials['repository']['blobs'][removed]['text'] == 'Original base-only material\r\n'
            assert 'Original base-only material' in materials['repository']['diff']
            assert 'Substituted material' not in materials['repository']['diff']
        assert materials['template_instructions'] == {'content': instructions, 'sha256': instructions_sha}
        assert set(materials['dependency_artifacts']['verification']) == {item['name'] for item in records['verify']['artifacts']}
        assert set(materials['dependency_artifacts']['plan']) == {item['name'] for item in records['plan']['artifacts']}
        assert invocation['formal_execution_authorized'] is False and invocation['status'] == 'succeeded'
        assert invocation['input_digest'] == call['input_digest']
        saved = workflow_definitions.inspect_input(Path(invocation['input_path']), material=True)
        assert saved['request']['prompt_sha256'] == invocation['prompt_sha256'] == call['prompt_sha256']
        assert next(item for item in saved['composition']['instances'] if item['path'] == call['member'])['resources']
        assert not (runtime / 'requests').exists()
        assert len(agent_runs.runs(state, 'demo')) == 1
        if mode == 'composition-task-mcp':
            assert invocation['task_mcp']['native']['ready']
            assert Path(invocation['task_mcp']['native']['receipt']).is_file()
            names = {item['name'] for item in review_receipt['artifacts']}
            assert {'composition-materials', 'composition-prompt', 'composition-mcp-scope', 'composition-mcp-audit'} <= names
        return invocation

    for stage in ("inventory", "plan", "work:unit", "integrate", "verify", "review"):
        if stage == 'review' and mode == 'composition-evidence-capacity':
            # Simulate valid, large verifier logs under the existing adapter limits.
            verified = records['verify']
            for index in range(2):
                relative = 'task-1/' + verified['job_id'] + '/large-' + str(index) + '.md'
                raw = b'L' * 600000
                (runtime / 'artifacts' / relative).write_bytes(raw)
                verified['artifacts'].append({'name': 'large-' + str(index), 'path': relative,
                                              'sha256': hashlib.sha256(raw).hexdigest()})
            write(runtime / 'receipts/task-1' / (verified['job_id'] + '.json'), verified, replace=True)
            adapter.verify_receipt(verified, verified)
        expected = records["integrate"]["candidate_sha"] if stage in ("verify", "review") else None
        # Preserve the frozen scheduler's actual keys and authority metadata.
        dependencies = ({'inventory': records['inventory']} if stage == 'plan' else
                        {'work:unit': records['work:unit']} if stage == 'integrate' else
                        {'integration': records['integrate']} if stage == 'verify' else
                        {'verification': records['verify'], 'plan': records['plan']} if stage == 'review' else {})
        if stage == 'review' and mode.startswith('composition-dag-'):
            from review_dag_acceptance import exercise

            print(json.dumps(await exercise(root, mode.removeprefix('composition-dag-'), app, activities,
                installation, state, runtime, requests, dependencies, expected)))
            return
        actual_stage = ('review:root/review' if stage == 'review' and
            (mode.startswith('composition-requirements-') or mode == 'composition-no-worker-sdk-v3') else stage)
        context = app.context(actual_stage, expected, task_input["work_units"][0] if stage == "work:unit" else None, dependencies)
        job = await activities.submit(context)
        request = requests / "task-1" / (context["job_id"] + ".json")
        if stage == 'inventory' and mode in ('composition-missing-admission', 'composition-other-admission',
                'composition-missing-publication', 'composition-binding-drift', 'composition-config-drift', 'composition-policy-drift', 'composition-multiple'):
            from ergora.reference_executor import Executor
            from ergora import task_envelopes
            from agent_platform.core import Blocked

            envelope = read(request)
            if mode == 'composition-missing-admission':
                del envelope['context']['admission']
            elif mode == 'composition-other-admission':
                changed = deepcopy(document['composition'])
                changed['members']['root/review']['backend_reason'] = 'Different admission with the same legacy projection'
                envelope['context']['admission'] = task_envelopes.wrap(app.spec, changed)
            elif mode == 'composition-missing-publication':
                (runtime / 'ergora/task-creations/task-1.result.json').unlink()
            elif mode == 'composition-binding-drift':
                path = runtime / 'tasks/task-1/agent-bindings.json'
                selected = read(path)
                selected['bindings']['reviewer']['model'] = 'drifted'
                write(path, selected, replace=True)
            elif mode == 'composition-config-drift':
                write(config / 'policies/demo/execution.json', {'allowed_task_types': []}, replace=True)
            elif mode == 'composition-policy-drift':
                from ergora.agent_backends import CodexBackend
                policy = CodexBackend.composition_policy
                def changed_policy(self, selected_mode):
                    value = policy(self, selected_mode)
                    value['basis'] += ' changed contract'
                    return value
                CodexBackend.composition_policy = changed_policy
            envelope['job_sha256'] = sha(envelope['context'])
            write(request, envelope, replace=True)
            try:
                Executor(envelope, state.root)
            except (Blocked, OSError, ValueError, KeyError) as error:
                assert not (runtime / 'executor.sqlite3').exists() and not (runtime / 'workspaces').exists()
                print(json.dumps({'rejected': mode, 'detail': str(error), 'before_native_side_effects': True}))
                return
            raise AssertionError('Invalid composition admission was accepted')
        if stage == 'review' and composition_mode:
            if mode.startswith('composition-no-worker-sdk-'):
                import importlib.abc

                class NoWorkerSDK(importlib.abc.MetaPathFinder):
                    def find_spec(self, fullname, path=None, target=None):
                        if fullname == 'ergora.reference_workflows' or fullname == 'temporalio' or fullname.startswith('temporalio.'):
                            raise ModuleNotFoundError('Optional worker SDK is deliberately unavailable: ' + fullname)

                for name in list(sys.modules):
                    if name == 'ergora.reference_workflows' or name == 'temporalio' or name.startswith('temporalio.'):
                        del sys.modules[name]
                sys.meta_path.insert(0, NoWorkerSDK())
            if mode == 'composition-replace-object':
                mirror = runtime / 'workspaces/task-1/repo.git'
                original = git(mirror, 'rev-parse', starting + ':src/removed.txt').stdout.strip()
                replacement = subprocess.check_output(['/usr/bin/git', '-C', str(mirror), 'hash-object', '-w', '--stdin'],
                                                       input=b'Substituted material\n').decode().strip()
                git(mirror, 'replace', original, replacement)
                assert git(mirror, 'cat-file', '-p', original).stdout == 'Substituted material\n'
            elif mode == 'composition-dependency-drift':
                artifact = records['verify']['artifacts'][0]
                (runtime / 'artifacts' / artifact['path']).write_text('Changed verification evidence')
            elif mode in ('composition-review-recovery', 'composition-missing-invocation'):
                from ergora.reference_executor import Executor

                first = Executor(read(request), state.root).execute()
                if mode == 'composition-missing-invocation':
                    missing = runtime / 'workspaces/task-1/jobs' / context['job_id'] / 'output/selected-agent/invocation.json'
                    missing.unlink()
                    second = Executor(read(request), state.root).execute()
                    assert first['state'] == 'SUCCEEDED' and second['state'] == 'FAILED', (first, second)
                    assert 'invocation evidence' in second['detail']
                else:
                    second = Executor(read(request), state.root).execute()
                    assert first == second and first['state'] == 'SUCCEEDED', (first, second)
            elif mode == 'composition-review-cancel':
                def cancel_review():
                    deadline = time.monotonic() + 20
                    while not list((state.root / 'runs').glob('*.cwd/review-ready')) and time.monotonic() < deadline:
                        time.sleep(0.02)
                    assert list((state.root / 'runs').glob('*.cwd/review-ready'))
                    write(runtime / 'fences/task-1.json', {'reason': 'Formal composition cancellation fixture'})
                review_cancel_thread = threading.Thread(target=cancel_review)
                review_cancel_thread.start()
        if stage == 'verify':
            if mode in ('verify-scope-mismatch', 'verify-scope-header'):
                scope_file = runtime / 'workspaces/task-1/jobs' / context['job_id'] / 'output/scope.json'
                scope = {'status': 'PASS', 'candidate_sha': '0' * 40}
                if mode == 'verify-scope-header':
                    from dev_platform.contracts import canonical_sha

                    scope.update(schema_version=1, check='scope', task_id='task-1',
                        candidate_sha=expected, request_sha256=app.spec['request_sha256'],
                        profile_sha256=app.spec['profile_sha256'], spec_sha256=canonical_sha(app.spec),
                        policy_sha256=canonical_sha(read(config / 'policies/demo/scope.json')),
                        base_sha=app.spec['request']['repository']['base_sha'])
                write(scope_file, scope)
            elif mode == 'verify-baseline-drift':
                write(runtime / 'tasks/task-1/baseline-checks.json', {}, replace=True)
            elif mode == 'verify-command-failure':
                (root / 'fail-verify').write_text('Trusted check now fails\n')
            elif mode == 'verify-scope-recovery':
                policy_path = config / 'policies/demo/scope.json'
                policy = read(policy_path)
                policy['protected_paths'].append('src/new.py')
                write(policy_path, policy, replace=True)
                from ergora.reference_executor import Executor

                # Simulate interruption after error artifacts, before publishing
                # the receipt: rerunning the same envelope must be idempotent.
                first = Executor(read(request), state.root).execute()
                second = Executor(read(request), state.root).execute()
                assert first == second and first['state'] == 'FAILED'
        if mode in ("unified-registration", "imported-registration") and stage == "inventory":
            result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "reference", "executor",
                                     "--project", "demo", "--request", str(request)], capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stdout + result.stderr
            receipt = json.loads(result.stdout)
        else:
            if stage == 'review' and mode == 'composition-requirements-mutate':
                target = runtime / 'workspaces/task-1/jobs' / context['job_id'] / 'checkout'
                # Supply the deliberate attack only in this test wrapper. Keep
                # the production monitor's environment allowlist unchanged.
                codex.write_text(f"#!{sys.executable}\nimport runpy,sys\nsys.argv.extend(['--fixture-checkout',{str(target)!r}])\nrunpy.run_path({str(fixture)!r},run_name='__main__')\n")
            receipt = reference.executor(installation, state.root, request)
        if stage == 'review' and (mode.startswith('composition-requirements-') or mode == 'composition-no-worker-sdk-v3'):
            if mode.endswith('-mutate'):
                assert receipt['state'] == 'FAILED', receipt
                assert await activities.poll(job) == {'receipt': receipt, 'review_decision': None}
                assert 'composition-review-decision' not in {item['name'] for item in receipt['artifacts']}
                terminal = read(runtime / 'processes' / ('af-' + job['job_id'] + '-selected') / 'terminal.json')
                assert 'read-only changed the checkout' in terminal['detail']
                print(json.dumps({'receipt_state': 'FAILED', 'review_decision': None,
                    'mutation_detected': True, 'trusted_opinion_published': False}))
                return
            decision = 'request-changes' if mode.endswith('-reject') else 'approve'
            assert receipt['state'] == ('FAILED' if decision == 'request-changes' else 'SUCCEEDED'), receipt
            assert await activities.poll(job) == {'receipt': receipt, 'review_decision': decision}
            invocation = check_formal_evidence(receipt)
            item = next(item for item in receipt['artifacts'] if item['name'] == 'composition-review-decision')
            opinion = read(runtime / 'artifacts' / item['path'])
            assert opinion == {'schema_version': 1, 'kind': 'formal-review-decision',
                'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
                'candidate_sha': records['verify']['candidate_sha'], 'decision': decision,
                'result_sha256': invocation['result_sha256']}
            from ergora.reference_executor import Executor

            original = (runtime / 'receipts/task-1' / (job['job_id'] + '.json')).read_bytes()
            assert Executor(read(request), state.root).execute() == receipt
            assert (runtime / 'receipts/task-1' / (job['job_id'] + '.json')).read_bytes() == original
            print(json.dumps({'decision': decision, 'receipt_state': receipt['state'],
                'candidate_bound': True, 'recovery_preserved': True}))
            return
        if stage == 'review' and mode in ('composition-binary', 'composition-symlink', 'composition-capacity',
                'composition-read-scope', 'composition-dependency-drift', 'composition-evidence-capacity', 'composition-review-reject',
                'composition-review-timeout', 'composition-review-cancel', 'composition-missing-invocation'):
            if mode == 'composition-review-cancel':
                review_cancel_thread.join(timeout=2)
            assert receipt['state'] == ('CANCELLED' if mode == 'composition-review-cancel' else 'FAILED'), receipt
            assert receipt['candidate_sha'] == records['verify']['candidate_sha']
            if mode != 'composition-dependency-drift':
                assert await activities.poll(job) == receipt
            assert not any(item['status'] == 'pass' for item in receipt['checks'])
            time.sleep(2.2 if mode == 'composition-review-cancel' else 0)
            if mode == 'composition-review-cancel':
                assert not list((state.root / 'runs').glob('*.cwd/late-review'))
            print(json.dumps({'rejected': mode, 'detail': receipt['detail'], 'state': receipt['state']}))
            return
        if stage == 'verify' and mode in ('verify-scope-mismatch', 'verify-scope-header', 'verify-baseline-drift', 'verify-command-failure', 'verify-scope-recovery'):
            assert receipt['state'] == 'FAILED', receipt
            assert not receipt['checks']
            assert receipt['candidate_sha'] == records['integrate']['candidate_sha']
            assert await activities.poll(job) == receipt
            print(json.dumps({'rejected': mode, 'detail': receipt['detail']}))
            return
        if stage == 'verify' and wrapper is not None:
            assert (runtime / 'tasks/task-1/task.spec.json').read_bytes() == wrapper
            projection = runtime / 'workspaces/task-1/jobs' / context['job_id'] / 'output/task.legacy-spec.json'
            assert read(projection) == app.spec
        if mode in ("instructions-missing", "instructions-tampered", "instructions-cross-task"):
            assert receipt["state"] == "FAILED", receipt
            assert not (runtime / "workspaces/task-1/jobs" / context["job_id"] / "selected-agent/request.json").exists()
            print(json.dumps({"rejected": mode, "detail": receipt["detail"]}))
            return
        if mode in ("unified-pending", "unified-drift", "unified-wrong-state"):
            assert receipt["state"] == "FAILED", receipt
            assert not (runtime / "tasks/task-1/agent-bindings.json").exists()
            print(json.dumps({"rejected": mode, "detail": receipt["detail"]}))
            return
        if stage == 'review' and mode == 'composition-task-mcp' and receipt['state'] == 'FAILED':
            assert receipt['detail'] == 'Selected reviewer requested changes', receipt
            assert await activities.poll(job) == receipt
            invocation = check_formal_evidence(receipt)
            assert read(Path(invocation['result']))['decision'] == 'request-changes'
            print(json.dumps({'template': kind, 'formal_model_invoked': True, 'mcp_ready': True,
                'candidate_bound': True, 'decision': 'request-changes', 'workflow_succeeded': False,
                'detail': 'Actual reviewer correctly blocks unmet acceptance; synthetic stages do not prove acceptance'}))
            return
        assert receipt["state"] == "SUCCEEDED", receipt
        assert await activities.poll(job) == receipt
        if stage not in ("integrate", "verify") and not (composition_mode and stage == "review"):
            protocol = runtime / "workspaces/task-1/jobs" / context["job_id"] / "selected-agent/request.json"
            invocation = read(protocol)
            sent = (Path(invocation["output"]) / "stdin.txt").read_text()
            if backend == "command":
                sent = json.loads(sent)["prompt"]
            payload = json.loads(sent.splitlines()[-1])
            assert payload["template_instructions"] == {"content": instructions, "sha256": instructions_sha}
            selection = read(runtime / "artifacts" / next(a["path"] for a in receipt["artifacts"] if a["name"] == "agent-selection"))
            assert selection["template_instructions_sha256"] == instructions_sha
            assert selection["prompt_sha256"] == hashlib.sha256(sent.encode()).hexdigest()
        records[stage] = receipt
        app.results[stage] = receipt
        selection_path = runtime / "tasks/task-1/agent-bindings.json"
        selection = read(selection_path)
        if stage == "inventory":
            assert selection["configuration"] == projects.effective_configuration(state.project("demo"))
            assert selection["configuration"]["project"]["revision"] == selection["project_revision"]
            if len(sys.argv) > 4 and sys.argv[4] == "legacy-snapshot":
                # Prior task selections lack the new additive view and must stay usable.
                del selection["configuration"]
                write(selection_path, selection, replace=True)
            frozen_selection = selection
            if mode in ("unified-registration", "imported-registration"):
                # Existing task selections survive later registration changes.
                replacement = deepcopy(definition)
                replacement["templates"] = ["training-optimization"]
                replacement["execution"]["config_directory"] = str(root / "next-config")
                registrations.register(state, replacement, state.project("demo")["revision"])
            # Later project changes must not change the already-frozen task selection.
            projects.bind(state, "demo", "implementer", {"tool": "command", "argv": ["/missing/changed-binding"]}, state.project("demo")["revision"])
        else:
            assert selection == frozen_selection
        if stage == "plan":
            plan_sha = sha(receipt)
            write(runtime / "approvals/fixture-approval.json", {"schema_version": 1, "kind": "plan-approval",
                "task_id": "task-1", "request_sha256": app.spec["request_sha256"], "profile_sha256": app.spec["profile_sha256"],
                "plan_sha256": plan_sha, "decision": "approve", "principal_type": "human", "actor_id": "fixture-maintainer",
                "role": "maintainer", "expires_at": time.time() + 3600, "revoked": False})
            authorization = await adapter.authorize({"task_id": "task-1", "request_sha256": app.spec["request_sha256"],
                "profile_sha256": app.spec["profile_sha256"], "plan_sha256": plan_sha, "receipt_id": "fixture-approval"})
            app.approved_plan = {"plan_sha256": plan_sha, "receipt": receipt, "approval": authorization}
    time.sleep(1.2)
    assert not list((runtime / "workspaces").rglob("late-review.py"))
    candidate = records["integrate"]["candidate_sha"]
    assert candidate != starting
    assert records["verify"]["candidate_sha"] == records["review"]["candidate_sha"] == candidate
    assert records["review"]["actor"]["session_id"] != records["work:unit"]["actor"]["session_id"]
    assert records["review"]["actor"]["id"] == ("codex" if composition_mode else backend) + ":reviewer"
    assert set(app.spec["profile"]["required_checks"]) == {check["id"] for check in records["verify"]["checks"]}
    if wrapper is not None:
        assert (runtime / 'tasks/task-1/task.spec.json').read_bytes() == wrapper
        check_formal_evidence(records['review'])
    assert not (root / 'shadow-imported').exists()
    print(json.dumps({"template": kind, "backend": backend, "stages": list(records), "candidate_bound": True,
                      "template_instructions_bound": True}))


if __name__ == "__main__":
    asyncio.run(main())
