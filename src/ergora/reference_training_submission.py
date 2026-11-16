"""Checkpoint original training starts; uncertain delivery only looks up the same run."""

import asyncio
from contextlib import nullcontext, redirect_stdout
from dataclasses import asdict
import io
import json
import os
from pathlib import Path
import re
import sys
import uuid

from .reference import _training_records
from .reference_training_context import _TrainingProject
from .reference_training_runtime import MEMO_KEY as _MEMO_KEY
from . import reference_training_budget as budgets, training_cycles
from .state import file_lock


_INTENT_LIMIT = 16 * 1_048_576


class _Submission(_TrainingProject):
    def __init__(self, payload: dict):
        super().__init__(payload)
        self.ident = self.core.slug(payload['experiment_id'])
        self.prefix = 'ergora/training-submissions/' + self.ident
        self.identity = {'schema_version': 1, 'operation': 'start',
                         'control_home': payload['control_home'], 'project': self.project['id'],
                         'repo': self.project['repo'], 'execution': self.execution,
                         'registration_sha256': self.project['registration']['sha256'],
                         'experiment_id': self.ident, 'workflow_id': 'perf-experiment/' + self.ident}

    def path(self, suffix: str) -> Path:
        path = self.adapter.safe_file(self.root, self.prefix + suffix)
        if os.name == 'nt' and any(parent.exists() and parent.lstat().st_file_attributes & 0x400
                                    for parent in (path, *path.parents)):
            raise ValueError('Symlinked or reparsed training submission path is forbidden')
        return path

    def optional(self, suffix: str) -> dict | None:
        try:
            return self.document(self.root, self.prefix + suffix, _INTENT_LIMIT if suffix == '.intent.json' else 1_048_576)
        except FileNotFoundError:
            return None

    def records(self) -> dict:
        return _training_records({'project': self.project['id'], 'repo': self.project['repo'],
                                  'experiment_id': self.ident})

    def preflight(self, intent: dict | None = None) -> dict:
        self.registration()
        observed = self.records()
        item = observed['experiment']
        if not item['baseline_matches']:
            raise ValueError('Training submission requires the current matching baseline: ' + item['baseline_error'])
        if item['current_runner'] is None:
            raise ValueError('Training submission requires its current trusted runner')
        if any(item[name] is not None for name in ('job_request', 'started', 'result', 'fence', 'negative_result')):
            raise ValueError('Native job, execution or fence records already exist; do not resubmit this experiment')
        runner = item['current_runner']
        if (set(runner) != {'schema_version', 'runner_template_id', 'project', 'repo', 'command', 'timeout_seconds'}
                or type(runner['schema_version']) is not int or runner['schema_version'] != 1
                or not isinstance(runner['command'], list) or not runner['command']
                or not all(isinstance(arg, str) and arg for arg in runner['command'])
                or type(runner['timeout_seconds']) is not int
                or not 1 <= runner['timeout_seconds'] <= min(82800, item['max_run_seconds'])):
            raise ValueError('Trusted runner command or execution walltime is invalid')
        repo = Path(self.project['repo'])
        if Path(self.core.git(repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve() != repo:
            raise ValueError('Training submission must retain the registered Git repository root')
        for name in ('candidate_sha', 'baseline_sha'):
            self.core.git(repo, 'cat-file', '-e', item['binding'][name] + '^{commit}')
        if item['manifest']['comparison_tool_sha256'] != self.core.digest(self.core.UPSTREAM / 'compare_runs.py'):
            raise ValueError('Comparator version differs from the reviewed training contract')
        if intent is not None and self.sha(observed) != self.sha(intent['observation']):
            raise ValueError('Prepared training sources changed after intent; restore the original sources before dispatch')
        return observed

    def load(self) -> dict | None:
        intent = self.optional('.intent.json')
        if intent is None:
            if any(self.path(suffix).exists() for suffix in ('.attempt.json', '.result.json', '.rejection.json')):
                # A writer may have published the immutable intent after our
                # first read, before publishing one of its dependent records.
                intent = self.optional('.intent.json')
                if intent is None:
                    raise ValueError('Training submission checkpoints have no original intent; reconcile before starting')
            else:
                return None
        expected = {**self.identity, 'project_revision': intent.get('project_revision'),
                    'operation_id': intent.get('operation_id'), 'observation': intent.get('observation')}
        if 'budget' in intent:
            budgets.validate_binding(intent['budget'])
            expected['budget'] = intent['budget']
        if (self.sha(intent) != self.sha(expected) or type(intent['project_revision']) is not int
                or intent['project_revision'] < 1 or not isinstance(intent['operation_id'], str)
                or re.fullmatch('[a-f0-9]{32}', intent['operation_id']) is None):
            raise ValueError('Training submission intent conflicts with its original project or control directory')
        item = intent['observation']['experiment']
        if (item['experiment_id'] != self.ident or item['binding'] != item['spec']['binding']
                or item['binding']['experiment_id'] != self.ident):
            raise ValueError('Training submission intent conflicts with its original experiment')
        return intent

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent),
                'workflow_id': intent['workflow_id'],
                'spec_sha256': self.sha(intent['observation']['experiment']['spec'])}

    def receipt(self, intent: dict, run_id: str) -> dict:
        if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
            raise ValueError('Native training start returned no valid run ID; reconcile the original workflow')
        return {**self.attempt(intent), 'run_id': run_id}

    def rejection(self, intent: dict, reason: str, run_id: str | None) -> dict:
        if reason in ('preexisting_run', 'start_conflict') and run_id is not None:
            return {**self.receipt(intent, run_id), 'reason': reason}
        if reason in ('lookup_rejected', 'start_conflict') and run_id is None:
            return {**self.attempt(intent), 'reason': reason, 'run_id': None}
        raise ValueError('Invalid training submission rejection')

    def status(self, intent: dict | None) -> dict:
        result = {**self.recovery_context, 'project': self.project['id'], 'project_revision': self.project_revision,
                  'experiment_id': self.ident, 'workflow_id': self.identity['workflow_id'],
                  'run_id': None, 'runtime_status': 'not_queried', 'execution_success': None}
        if intent is None:
            if self.recovery is not None:
                raise ValueError('Original registration recovery requires an existing matching start intent')
            self.records()
            return {**result, 'status': 'not_recorded'}
        result['submitted_revision'] = intent['project_revision']
        # Read completion before the checkpoint: a concurrent writer only adds
        # immutable records, and cannot make an observed result lose its attempt.
        receipt = self.optional('.result.json')
        rejection = self.optional('.rejection.json')
        attempt = self.optional('.attempt.json')
        if attempt is not None and self.sha(attempt) != self.sha(self.attempt(intent)):
            raise ValueError('Training submission attempt conflicts with its original intent')
        if receipt is not None:
            if attempt is None or self.sha(receipt) != self.sha(self.receipt(intent, receipt.get('run_id'))):
                raise ValueError('Training submission receipt has no matching original checkpoint')
            result['run_id'] = receipt['run_id']
        if rejection is not None:
            reason = rejection.get('reason')
            if (receipt is not None or (attempt is not None) != (reason == 'start_conflict')
                    or self.sha(rejection) != self.sha(self.rejection(intent, reason, rejection.get('run_id')))):
                raise ValueError('Training ownership rejection conflicts with its original checkpoint')
            return {**result, 'status': 'rejected', 'intent_sha256': self.sha(intent),
                    'reason': reason, 'conflicting_run_id': rejection['run_id'],
                    'attempt_saved': attempt is not None, 'result_saved': False}
        if 'budget' in intent:
            result['budget'] = budgets.BudgetedStart(self, intent).observe()
        return {**result, 'status': 'submitted' if receipt else 'unknown' if attempt else 'prepared',
                'intent_sha256': self.sha(intent),
                'manifest_sha256': intent['observation']['experiment']['binding']['manifest_sha'],
                'confirmation': {'binding': intent['observation']['experiment']['binding'],
                                 'max_run_seconds': intent['observation']['experiment']['max_run_seconds'],
                                 'runner': intent['observation']['experiment']['current_runner']},
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None}

    def native_request(self) -> dict | None:
        """Validate the original request path and the job ID trusted by native lookup."""
        try:
            request = self.document(self.root, 'training/jobs/' + self.ident + '/request.json')
        except FileNotFoundError:
            return None
        if request.get('job_id') != 'local-perf-' + self.ident:
            raise ValueError('Native job request differs from the original experiment job ID')
        return request

    async def fence(self) -> dict:
        from agent_platform.training import create_adapter
        from perf_temporal.models import Binding, Experiment

        intent = self.load()
        if self.recovery is not None and intent is None:
            raise ValueError('Original registration fencing requires an existing matching start intent')
        submitted = self.status(intent) if intent is not None else None
        observed = intent['observation'] if intent is not None else self.records()
        spec = observed['experiment']['spec']
        if self.payload['manifest_sha256'] != spec['binding']['manifest_sha']:
            raise ValueError('Confirm the exact original manifest SHA before applying a local fence')
        fence_relative = 'training/fences/' + self.ident + '.json'
        for relative in ('training/registry.lock', 'training/jobs/' + self.ident + '/request.json', fence_relative):
            self.adapter.safe_file(self.root, relative)
        if intent is not None:
            # Native lookup validates Experiment, but trusts the saved job ID.
            self.native_request()
        try:
            existing = self.document(self.root, fence_relative)
        except FileNotFoundError:
            existing = None
        if existing is not None and existing != {'binding': spec['binding']}:
            raise ValueError('Existing training fence differs from the confirmed original binding')
        if existing is None and submitted is not None and submitted['status'] not in ('prepared', 'unknown'):
            raise ValueError('Original submission is already submitted or rejected; use exact-run cancellation or reconcile ownership')
        # Do not wait on the submission lock held across an in-flight start RPC.
        # Native fence/create share their own registry lock and immutable binding.
        experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
        job = await create_adapter().fence_and_lookup(experiment)
        fence_path = self.adapter.safe_file(self.root, fence_relative)
        return {**self.recovery_context, 'project': self.project['id'], 'project_revision': self.project_revision,
                'experiment_id': self.ident, 'binding': spec['binding'], 'status': 'fenced',
                'submission_status_observed': submitted['status'] if submitted else 'not_recorded',
                'intent_sha256': self.sha(intent) if intent else None,
                'intent_project_revision': intent['project_revision'] if intent else None,
                'fence': {'path': str(fence_path), 'sha256': self.core.digest(fence_path)},
                'existing_job': asdict(job) if job is not None else None,
                'runtime_status': 'not_queried', 'executor_stop_confirmed': None, 'execution_success': None,
                'scope': 'Exact local experiment fence; may suppress runner/archive and future release; no run ownership, stop or ticket rollback proof'}

    async def dispatch(self, intent: dict) -> dict:
        from perf_temporal import client as native
        from temporalio.exceptions import WorkflowAlreadyStartedError
        from .reference_training_runtime import lookup

        operation = self
        original_connect, original_load, original_argv = native.connect, native.load_experiment, sys.argv
        spec = intent['observation']['experiment']['spec']
        budget = budgets.BudgetedStart(self, intent) if 'budget' in intent else None
        if budget is not None:
            budget.ensure_owner()

        class CheckpointedClient:
            def __init__(self, client):
                self.client = client

            def __getattr__(self, name):
                return getattr(self.client, name)

            async def start_workflow(self, run, experiment, **options):
                with budget.permission() if budget is not None else nullcontext() as parent:
                    if operation.sha(asdict(experiment)) != operation.sha(spec) or options['id'] != intent['workflow_id']:
                        raise ValueError('Native start input differs from the frozen training experiment')
                    if budget is not None:
                        await budget.check_controller_history(self.client)
                    try:
                        found = await lookup(self.client, spec, run_id=None, timeout=operation.payload['timeout'])
                    except ValueError:
                        operation.core.write(operation.path('.rejection.json'), operation.rejection(intent, 'lookup_rejected', None))
                        raise
                    if found is not None:
                        operation.core.write(operation.path('.rejection.json'),
                                             operation.rejection(intent, 'preexisting_run', found[1].run_id))
                        raise ValueError('Training workflow already exists without this submission attempt; reconcile its owner')
                    operation.preflight(intent)
                    if budget is not None:
                        budget.require_active(owner=True)
                    operation.core.write(operation.path('.attempt.json'), operation.attempt(intent))
                    if budget is not None:
                        training_cycles._sync_directory(operation.path('.attempt.json').parent)
                    operation.preflight(intent)
                    if budget is not None:
                        budget.require_active(owner=True)
                        options['task_queue'] = budget.binding['task_queue']
                    if parent is not None:
                        parent.check()
                    async with asyncio.timeout(budget.dispatch_remaining() if budget is not None else None):
                        return await self.client.start_workflow(run, experiment,
                            memo={_MEMO_KEY: operation.sha(intent)}, **options)

        async def connect():
            return CheckpointedClient(await original_connect())

        def load(path):
            experiment = original_load(path)
            if operation.sha(asdict(experiment)) != operation.sha(spec):
                raise ValueError('Original experiment spec changed before native submission')
            return experiment

        native.connect, native.load_experiment = connect, load
        sys.argv = ['perf_temporal.client', 'start', str(self.adapter.safe_file(self.root, 'training/specs/' + self.ident + '.json'))]
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                await native.main()
        except WorkflowAlreadyStartedError as error:
            self.core.write(self.path('.rejection.json'), self.rejection(intent, 'start_conflict', error.run_id))
            return self.status(intent)
        finally:
            native.connect, native.load_experiment, sys.argv = original_connect, original_load, original_argv
        reply = json.loads(output.getvalue())
        if reply['workflow_id'] != intent['workflow_id']:
            raise ValueError('Native start returned another workflow; reconcile the original training ID')
        self.core.write(self.path('.result.json'), self.receipt(intent, reply['run_id']))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        from perf_temporal.connection import connect
        from .reference_training_runtime import lookup

        client = await connect()
        found = await lookup(client, intent['observation']['experiment']['spec'], run_id=None, timeout=self.payload['timeout'])
        if found is None:
            return {**self.status(intent), 'reconciliation': 'not_found',
                    'instruction': 'Dispatch remains uncertain; do not resubmit or change the experiment ID to bypass it'}
        _, description = found
        if (await description.memo()).get(_MEMO_KEY) != self.sha(intent):
            raise ValueError('Original training run has no matching intent memo; ownership remains unconfirmed')
        self.core.write(self.path('.result.json'), self.receipt(intent, description.run_id))
        return self.status(intent)

    async def run(self) -> dict:
        self.registration()
        operation = self.payload['operation']
        if self.recovery is not None and operation not in ('status', 'fence', 'prepare-resume', 'resume'):
            raise ValueError('Original registration recovery permits only original start reconciliation or fencing')
        if operation == 'status':
            return self.status(self.load())
        if operation == 'fence':
            return await self.fence()
        if operation == 'check':
            intent = self.load()
            observed = self.preflight() if intent is None else None
            original = observed if intent is None else intent['observation']
            digest = original['experiment']['binding']['manifest_sha']
            if self.payload['manifest_sha256'] != digest:
                raise ValueError('Confirm the exact original manifest SHA before training start check')
            return {'project': self.project['id'], 'project_revision': self.project['revision'],
                    'experiment_id': self.ident, 'manifest_sha256': digest,
                    'ready_for_new_start': intent is None, 'read_only': True, 'execution_authorized': False,
                    'runtime_status': 'not_queried', 'observation': observed,
                    'submission': self.status(intent) if intent is not None else None}
        if operation not in ('prepare', 'prepare-resume', 'dispatch', 'resume'):
            raise ValueError('Unsupported training submission operation')
        lock = self.path('.lock')
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # A short local prepare may run under a DB reservation. Never wait for
        # another operation's remote I/O while holding that reservation.
        with file_lock(lock, blocking=False):
            intent = self.load()
            if operation == 'prepare':
                if intent is not None:
                    selector = self.payload.get('budget')
                    if selector is not None and selector != {key: value for key, value in intent.get('budget', {}).items()
                                                           if key != 'task_queue'}:
                        raise ValueError('Original training start cannot switch or adopt another budget')
                    if self.payload['manifest_sha256'] != intent['observation']['experiment']['binding']['manifest_sha']:
                        raise ValueError('Confirm the exact original manifest SHA before training submission')
                    return {'created': False, 'submission': self.status(intent)}
                observed = self.preflight()
                if self.payload['manifest_sha256'] != observed['experiment']['binding']['manifest_sha']:
                    raise ValueError('Confirm the exact original manifest SHA before training submission')
                intent = {**self.identity, 'project_revision': self.project['revision'],
                          'operation_id': uuid.uuid4().hex, 'observation': observed}
                if self.payload.get('budget') is not None:
                    intent['budget'] = budgets.prepare_binding(self, intent, self.payload['budget'])
                # The aggregate freezes several individually bounded sources.
                # Match core.write's actual serialization before publication.
                raw = (json.dumps(intent, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
                if len(raw) > _INTENT_LIMIT:
                    raise ValueError('Training submission intent exceeds its 16 MiB aggregate read capacity; nothing was dispatched')
                self.core.write(self.path('.intent.json'), intent)
                if 'budget' in intent:
                    training_cycles._sync_directory(self.path('.intent.json').parent)
                    budgets.BudgetedStart(self, intent).require_active()
                return {'created': True, 'submission': self.status(intent)}
            if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                raise ValueError('Training resume requires the exact original intent SHA')
            status = self.status(intent)
            if self.recovery is not None and not status['attempt_saved']:
                raise ValueError('Original registration recovery cannot resume a start without its original attempt')
            if operation == 'prepare-resume' or status['status'] in ('submitted', 'rejected'):
                return status
            from temporalio.service import RPCError

            try:
                if status['attempt_saved']:
                    return await self.reconcile(intent) if operation == 'resume' else status
                self.preflight(intent)
                return await self.dispatch(intent)
            except RPCError as error:
                raise ValueError('Training submission RPC failed: ' + error.status.name) from error


def main() -> None:
    from agent_platform.core import Blocked, environment

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] in ('dispatch', 'resume'):
            os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_Submission(payload).run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        if payload['operation'] == 'fence':
            raise SystemExit('BLOCKED: Local training fence timed out and may already exist; repeat the same binding confirmation, do not infer that execution stopped') from error
        raise SystemExit('BLOCKED: Training submission timed out; inspect its original intent and reconcile, do not resubmit') from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
