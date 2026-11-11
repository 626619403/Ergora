"""Export only a recorded run's verified candidate, with conditional Git ref writes."""

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
import getpass
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

from .reference_task_submission import _Submission
from .state import file_lock, now


class _Export:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.core, self.sha = self.creation.core, self.creation.sha
        self.repo = Path(self.creation.project['repo'])
        prefix = 'ergora/task-exports/' + self.creation.task_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.result_path = self.creation.path(prefix + '.result.json')
        self.native_path = self.creation.path('tasks/' + self.creation.task_id + '/export.json')

    def prepare(self) -> None:
        self.start_intent, self.run_id = self.submission.submitted()
        self.spec = self.submission.spec
        if (self.repo.resolve() != self.repo or
                self.core.git(self.repo, 'rev-parse', '--show-toplevel').stdout.strip() != str(self.repo)):
            raise ValueError('Export repository no longer has its registered canonical Git root')

    @staticmethod
    def actor() -> str:
        return f'unix:{os.getuid()}:{getpass.getuser()}'

    def validate_branch(self, branch: str) -> None:
        if not isinstance(branch, str) or not 1 <= len(branch) <= 1024 or branch.startswith('-'):
            raise ValueError('Invalid export branch')
        checked = self.core.git(self.repo, 'check-ref-format', '--branch', branch, check=False)
        if checked.returncode != 0 or checked.stdout.rstrip('\n') != branch:
            raise ValueError('Invalid export branch')

    def record(self, revision: int, candidate: str, branch: str, actor: str) -> dict:
        if not isinstance(candidate, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', candidate):
            raise ValueError('Export requires the exact full candidate commit SHA')
        self.validate_branch(branch)
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError('Invalid saved export actor')
        return {**self.submission.expected, 'operation': 'export', 'project_revision': revision,
                'submission_sha256': self.sha(self.start_intent), 'run_id': self.run_id,
                'repo': str(self.repo), 'candidate_sha': candidate, 'branch': branch, 'actor_id': actor}

    def load(self) -> dict | None:
        record = self.creation.optional(self.intent_path)
        if record is None:
            if self.attempt_path.exists() or self.result_path.exists():
                raise ValueError('Export records have no original intent; reconcile before exporting again')
            return None
        if type(record.get('project_revision')) is not int or record['project_revision'] < 1:
            raise ValueError('Invalid saved export revision')
        expected = self.record(record['project_revision'], record['candidate_sha'], record['branch'], record['actor_id'])
        if self.sha(record) != self.sha(expected):
            raise ValueError('Export intent conflicts with its original project, submission or run')
        return record

    def attempt(self, intent: dict, outcome_sha256: str) -> dict:
        if not isinstance(outcome_sha256, str) or not re.fullmatch('[0-9a-f]{64}', outcome_sha256):
            raise ValueError('Export checkpoint requires the original outcome digest')
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': intent['run_id'], 'outcome_sha256': outcome_sha256}

    def receipt(self, attempt: dict, lease_released: bool) -> dict:
        if type(lease_released) is not bool:
            raise ValueError('Export result requires the actual lease release fact')
        return {**attempt, 'lease_released': lease_released}

    def native(self, intent: dict) -> dict:
        return {'candidate_sha': intent['candidate_sha'], 'repo': intent['repo'], 'branch': intent['branch']}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'run_id': self.run_id, 'runtime_status': 'not_queried',
                  'checked_out': False, 'merged': False, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded'}
        receipt = self.creation.optional(self.result_path)
        attempt = self.creation.optional(self.attempt_path)
        if attempt is not None and self.sha(attempt) != self.sha(self.attempt(intent, attempt.get('outcome_sha256'))):
            raise ValueError('Export checkpoint conflicts with its original intent')
        if receipt is not None:
            if (attempt is None or self.sha(receipt) != self.sha(self.receipt(attempt, receipt.get('lease_released')))
                    or self.sha(self.creation.optional(self.native_path)) != self.sha(self.native(intent))):
                raise ValueError('Export result conflicts with its checkpoint or native export record')
        return {**result, 'status': 'exported' if receipt is not None else 'unknown' if attempt is not None else 'prepared',
                'workflow_id': intent['workflow_id'], 'intent_sha256': self.sha(intent),
                'candidate_sha': intent['candidate_sha'], 'repo': intent['repo'], 'branch': intent['branch'],
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
                'lease_released': receipt['lease_released'] if receipt is not None else None}

    @asynccontextmanager
    async def git_process(self, *args: str):
        # Frozen core.git has a synchronous 120s wait. This owner needs cancellable
        # Git and an interactive ref transaction inside the export budget.
        env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
                   GIT_AUTHOR_NAME='Agent Platform', GIT_AUTHOR_EMAIL='agent-platform@localhost',
                   GIT_COMMITTER_NAME='Agent Platform', GIT_COMMITTER_EMAIL='agent-platform@localhost')
        if self.payload['operation'] == 'inspect':
            env.update(GIT_NO_LAZY_FETCH='1', GIT_NO_REPLACE_OBJECTS='1')
        process = await asyncio.create_subprocess_exec(
            '/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'protocol.file.allow=always',
            '-C', str(self.repo), *args, env=env, start_new_session=True,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            yield process
        finally:
            # TERM lets Git remove prepared ref locks; KILL bounds descendant cleanup.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(process.communicate(), 1)
            except TimeoutError:
                pass
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.communicate()

    async def git(self, *args: str, check: bool = True):
        async with self.git_process(*args) as process:
            stdout, stderr = await process.communicate()
            result = subprocess.CompletedProcess(args, process.returncode, stdout.decode('utf-8'), stderr.decode('utf-8'))
            self.core.require(not check or result.returncode == 0, f'git {args[0]} failed: {result.stderr[:1500]}')
            return result

    async def create_branch(self, intent: dict) -> None:
        ref = 'refs/heads/' + intent['branch']
        async with self.git_process('update-ref', '--no-deref', '--stdin') as process:
            process.stdin.write(f"start\noption no-deref\ncreate {ref} {intent['candidate_sha']}\nprepare\n".encode('utf-8'))
            await process.stdin.drain()
            acknowledgments = [await process.stdout.readline(), await process.stdout.readline()]
            if acknowledgments != [b'start: ok\n', b'prepare: ok\n']:
                _, stderr = await process.communicate()
                # A racing writer may have created the exact candidate already.
                if await self.branch_sha(intent) == intent['candidate_sha']:
                    return
                raise ValueError('Conditional export branch creation failed: ' + stderr.decode('utf-8')[:1500])
            # create compares resolved OIDs; even with no-deref it accepts dangling
            # symrefs. Inspect under Git's prepared ref lock before committing.
            alias = await self.git('symbolic-ref', '--quiet', ref, check=False)
            if alias.returncode == 0:
                await process.communicate(b'abort\n')
                raise ValueError('Export cannot replace an existing symbolic branch')
            self.core.require(alias.returncode == 1, 'Unable to check the export branch type: ' + alias.stderr[:1500])
            worktrees = await self.git('worktree', 'list', '--porcelain', '-z')
            if 'branch ' + ref in worktrees.stdout.split('\0'):
                await process.communicate(b'abort\n')
                raise ValueError('Export branch is checked out in an existing worktree; its HEAD must remain unchanged')
            _, stderr = await process.communicate(b'commit\n')
            self.core.require(process.returncode == 0, 'Export ref commit failed: ' + stderr.decode('utf-8')[:1500])

    async def branch_sha(self, intent: dict) -> str | None:
        alias = await self.git('symbolic-ref', '--quiet', 'refs/heads/' + intent['branch'], check=False)
        if alias.returncode == 0:
            raise ValueError('Export cannot replace an existing symbolic branch')
        self.core.require(alias.returncode == 1, 'Unable to check the export branch type: ' + alias.stderr[:1500])
        observed = await self.git('rev-parse', '--verify', '--quiet', 'refs/heads/' + intent['branch'], check=False)
        if observed.returncode == 1:
            return None
        self.core.require(observed.returncode == 0, 'Unable to read the original export branch: ' + observed.stderr[:1500])
        return observed.stdout.strip()

    async def inspect(self, intent: dict | None) -> dict:
        status = self.status(intent)
        if status['status'] != 'exported':
            raise ValueError('Candidate inspection requires the original completed local export receipt')
        if (self.payload['run_id'], self.payload['candidate_sha']) != (intent['run_id'], intent['candidate_sha']):
            raise ValueError('Candidate inspection must pin the original exported run and candidate')
        self.validate_branch(self.payload['base_branch'])
        version = re.fullmatch(r'git version (\d+)\.(\d+)(?:[^\n]*)', (await self.git('--version')).stdout.strip())
        if version is None or tuple(map(int, version.groups())) < (2, 43):
            raise ValueError('Candidate inspection requires Git 2.43 or later with GIT_NO_LAZY_FETCH support')
        base = self.spec['request']['repository']['base_sha']
        for sha in (intent['candidate_sha'], base):
            if (await self.git('cat-file', '-t', sha)).stdout.strip() != 'commit':
                raise ValueError('Candidate inspection requires the original candidate and base commit objects')
        current = await self.branch_sha(intent)
        return {'export': status, 'base_sha': base, 'candidate_sha': intent['candidate_sha'],
                'branch': intent['branch'], 'current_branch_sha': current,
                'branch_matches_candidate': None if current is None else current == intent['candidate_sha'],
                'base_branch': self.payload['base_branch'], 'objects_verified_as_commits': True,
                'observed_at': now(),
                'coverage': 'Current local objects and one ref only; no fetch, ref write or workflow lookup'}

    async def outcome(self, intent: dict) -> dict:
        from temporalio.client import WorkflowExecutionStatus

        handle, description, _ = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        if description.status != WorkflowExecutionStatus.COMPLETED:
            raise ValueError('Export requires the original completed REVIEW_READY run')
        outcome = await handle.result(follow_runs=False, rpc_timeout=timedelta(seconds=20))
        expected = {'status': 'REVIEW_READY', 'task_id': self.creation.task_id,
                    'task_type': self.spec['request']['task_type'], 'request_sha256': self.spec['request_sha256'],
                    'profile_sha256': self.spec['profile_sha256'],
                    'base_sha': self.spec['request']['repository']['base_sha'], 'candidate_sha': intent['candidate_sha']}
        if not isinstance(outcome, dict) or any(outcome.get(key) != value for key, value in expected.items()):
            raise ValueError('Export outcome must match the original task, REVIEW_READY and exact candidate')
        return outcome

    async def complete(self, intent: dict, attempt: dict, outcome: dict) -> dict:
        from agent_platform.ingress import release

        if await self.branch_sha(intent) != intent['candidate_sha']:
            raise ValueError('Export branch no longer names the exact candidate; preserve the original intent')
        native = self.creation.optional(self.native_path)
        if native is not None and self.sha(native) != self.sha(self.native(intent)):
            raise ValueError('Native export record conflicts with the original export intent')
        released = release(self.spec, outcome)
        self.core.write(self.native_path, self.native(intent))
        self.core.write(self.result_path, self.receipt(attempt, released))
        return self.status(intent)

    async def dispatch(self, intent: dict) -> dict:
        outcome = await self.outcome(intent)
        current = await self.branch_sha(intent)
        if current is not None and current != intent['candidate_sha']:
            raise ValueError('Export branch already exists at a different commit')
        native = self.creation.optional(self.native_path)
        if native is not None and self.sha(native) != self.sha(self.native(intent)):
            raise ValueError('Native export record conflicts with the original export intent')
        attempt = self.attempt(intent, self.sha(outcome))
        self.core.write(self.attempt_path, attempt)
        if current is None:
            source = self.creation.path('workspaces/' + self.creation.task_id + '/repo.git')
            await self.git('fetch', '--no-tags', '--no-write-fetch-head', str(source), intent['candidate_sha'])
            if (await self.git('cat-file', '-t', intent['candidate_sha'])).stdout.strip() != 'commit':
                raise ValueError('Export candidate must name an actual Git commit')
            await self.create_branch(intent)
        return await self.complete(intent, attempt, outcome)

    async def reconcile(self, intent: dict) -> dict:
        outcome = await self.outcome(intent)
        attempt = self.creation.document(self.attempt_path)
        if self.sha(attempt) != self.sha(self.attempt(intent, self.sha(outcome))):
            raise ValueError('Original export outcome changed; preserve the saved checkpoint')
        current = await self.branch_sha(intent)
        if current is None:
            return {**self.status(intent), 'reconciliation': 'branch_not_found',
                    'instruction': 'Export remains uncertain; inspect the original candidate and branch, do not recreate it implicitly'}
        if current != intent['candidate_sha']:
            raise ValueError('Export branch names a different commit; recovery cannot move it')
        return await self.complete(intent, attempt, outcome)

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation in ('status', 'inspect'):
            self.prepare()
            intent = self.load()
            return await self.inspect(intent) if operation == 'inspect' else self.status(intent)
        preparing = operation in ('prepare', 'prepare-resume')
        with file_lock(self.creation.lock_path, blocking=not preparing):
            self.prepare()
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Export must pin the original submitted run ID')
                if intent is not None:
                    if (intent['candidate_sha'], intent['branch']) != (self.payload['candidate_sha'], self.payload['branch']):
                        raise ValueError('Task already has a different export target; inspect its original intent')
                    return {'created': False, 'export': self.status(intent)}
                if self.native_path.exists():
                    raise ValueError('Native export already exists without this intent; legacy exports cannot be adopted')
                intent = self.record(self.creation.project['revision'], self.payload['candidate_sha'], self.payload['branch'], self.actor())
                self.core.write(self.intent_path, intent)
                return {'created': True, 'export': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Export recovery requires the exact original intent digest')
            status = self.status(intent)
            if operation == 'prepare-resume' or status['status'] == 'exported':
                return status
            if operation not in ('dispatch', 'resume'):
                raise ValueError('Unsupported task export operation')
            if intent['actor_id'] != self.actor():
                raise ValueError('Export actor changed; the original intent cannot be impersonated')
            if status['attempt_saved']:
                return await self.reconcile(intent) if operation == 'resume' else status
            return await self.dispatch(intent)


def main() -> None:
    """Keep all network/Git side effects outside the shared control database."""
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError
    from .processes import _adopt_children, _reap_children

    adopting = False
    try:
        payload = json.load(sys.stdin)
        if payload['operation'] not in ('status', 'inspect', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
            _adopt_children()
            adopting = True
        try:
            result = asyncio.run(asyncio.wait_for(_Export(payload).run(), payload['timeout']))
        finally:
            if adopting:
                _reap_children()
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Export timed out; inspect and resume the original export intent') from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original export run was not found; preserve its intent and reconcile') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Export RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
