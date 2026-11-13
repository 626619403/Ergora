"""Checkpoint original training starts; uncertain delivery only looks up the same run."""

import asyncio
from contextlib import redirect_stdout
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
from .state import file_lock


_MEMO_KEY = 'ergora.training_submission_sha256'
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
        result = {'project': self.project['id'], 'project_revision': self.project['revision'],
                  'experiment_id': self.ident, 'workflow_id': self.identity['workflow_id'],
                  'run_id': None, 'runtime_status': 'not_queried', 'execution_success': None}
        if intent is None:
            self.records()
            return {**result, 'status': 'not_recorded'}
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
        return {**result, 'status': 'submitted' if receipt else 'unknown' if attempt else 'prepared',
                'intent_sha256': self.sha(intent), 'submitted_revision': intent['project_revision'],
                'manifest_sha256': intent['observation']['experiment']['binding']['manifest_sha'],
                'confirmation': {'binding': intent['observation']['experiment']['binding'],
                                 'max_run_seconds': intent['observation']['experiment']['max_run_seconds'],
                                 'runner': intent['observation']['experiment']['current_runner']},
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None}

    async def dispatch(self, intent: dict) -> dict:
        from perf_temporal import client as native
        from temporalio.exceptions import WorkflowAlreadyStartedError
        from .reference_training_runtime import lookup

        operation = self
        original_connect, original_load, original_argv = native.connect, native.load_experiment, sys.argv
        spec = intent['observation']['experiment']['spec']

        class CheckpointedClient:
            def __init__(self, client):
                self.client = client

            def __getattr__(self, name):
                return getattr(self.client, name)

            async def start_workflow(self, run, experiment, **options):
                if operation.sha(asdict(experiment)) != operation.sha(spec) or options['id'] != intent['workflow_id']:
                    raise ValueError('Native start input differs from the frozen training experiment')
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
                operation.core.write(operation.path('.attempt.json'), operation.attempt(intent))
                operation.preflight(intent)
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
        if operation == 'status':
            return self.status(self.load())
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
                    if self.payload['manifest_sha256'] != intent['observation']['experiment']['binding']['manifest_sha']:
                        raise ValueError('Confirm the exact original manifest SHA before training submission')
                    return {'created': False, 'submission': self.status(intent)}
                observed = self.preflight()
                if self.payload['manifest_sha256'] != observed['experiment']['binding']['manifest_sha']:
                    raise ValueError('Confirm the exact original manifest SHA before training submission')
                intent = {**self.identity, 'project_revision': self.project['revision'],
                          'operation_id': uuid.uuid4().hex, 'observation': observed}
                # The aggregate freezes several individually bounded sources.
                # Match core.write's actual serialization before publication.
                raw = (json.dumps(intent, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
                if len(raw) > _INTENT_LIMIT:
                    raise ValueError('Training submission intent exceeds its 16 MiB aggregate read capacity; nothing was dispatched')
                self.core.write(self.path('.intent.json'), intent)
                return {'created': True, 'submission': self.status(intent)}
            if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                raise ValueError('Training resume requires the exact original intent SHA')
            status = self.status(intent)
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
        raise SystemExit('BLOCKED: Training submission timed out; inspect its original intent and reconcile, do not resubmit') from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
