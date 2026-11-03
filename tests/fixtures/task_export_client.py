"""Controllable SDK port; export journals, Git objects/refs and leases stay real."""

import asyncio
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode

from dev_platform import connection
from ergora.reference_task_export import _Export, main

payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
scenario = os.environ.get('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
root = Path(payload['project']['registration']['definition']['execution']['state_directory']) / 'sdk-fixture'


def log(event):
    with (root / 'calls.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'event': event}) + '\n')


def saved():
    return json.loads((root / 'server.json').read_text())


class Handle:
    async def describe(self, **kwargs):
        log('export-describe')
        if scenario == 'not-found':
            raise RPCError('missing', RPCStatusCode.NOT_FOUND, b'')
        if scenario == 'rpc-unavailable':
            raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
        async def memo():
            return {} if scenario == 'wrong-memo' else saved()['memo']
        return SimpleNamespace(run_id=saved()['run_id'], memo=memo,
                               status=WorkflowExecutionStatus.RUNNING if scenario == 'running' else WorkflowExecutionStatus.COMPLETED)

    async def fetch_history_events(self, **kwargs):
        assert kwargs['page_size'] == 1
        yield SimpleNamespace(HasField=lambda key: key == 'workflow_execution_started_event_attributes',
            workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=['spec'])))

    async def result(self, **kwargs):
        log('export-result')
        assert kwargs['follow_runs'] is False and kwargs['rpc_timeout'].total_seconds() == 20
        return json.loads((root / 'outcome.json').read_text())


class Converter:
    async def decode(self, payloads, types):
        assert payloads == ['spec']
        spec = saved()['spec']
        if scenario == 'wrong-spec':
            spec['profile']['schema_version'] = True
        return [spec]


class Client:
    data_converter = Converter()
    def get_workflow_handle(self, workflow_id, *, run_id, result_type):
        assert workflow_id == 'dev-task/' + payload['task_id'] and result_type is dict
        assert run_id == saved()['run_id']
        return Handle()


async def connect():
    log('export-connect')
    if scenario == 'slow-connect':
        await asyncio.sleep(3)
    if scenario == 'offline':
        raise OSError('Fixture export service is offline')
    return Client()


connection.connect = connect
if scenario == 'slow-fetch':
    spawn = asyncio.create_subprocess_exec
    async def slow_tool(*args, **kwargs):
        if args[0] == '/usr/bin/git' and 'fetch' in args:
            code = "import os,time;from pathlib import Path;p=Path(" + repr(str(root)) + ");(p/'git-parent.pid').write_text(str(os.getpid()));pid=os.fork();(p/('git-child.pid' if pid==0 else 'git-group.pid')).write_text(str(os.getpid()));time.sleep(30)"
            args = (sys.executable, '-c', code)
        return await spawn(*args, **kwargs)
    asyncio.create_subprocess_exec = slow_tool
if scenario == 'different-actor' and payload['operation'] == 'dispatch':
    _Export.actor = staticmethod(lambda: 'unix:99999:another-user')
original_init = _Export.__init__


def initialize(self, *args):
    original_init(self, *args)
    write, git = self.core.write, self.core.git
    def interrupted(path, value, **kwargs):
        for name, target in (('intent', self.intent_path), ('attempt', self.attempt_path),
                             ('native', self.native_path), ('result', self.result_path)):
            if path == target and scenario == 'before-' + name:
                raise OSError('Fixture before ' + name)
            if path == target and scenario == 'after-' + name:
                write(path, value, **kwargs)
                raise OSError('Fixture after ' + name)
        return write(path, value, **kwargs)
    original_git, original_branch = self.git, self.create_branch
    async def git_operation(*args, **kwargs):
        if args[0] == 'fetch':
            log('export-fetch')
            if scenario == 'before-fetch':
                raise OSError('Fixture before fetch')
            result = await original_git(*args, **kwargs)
            if scenario == 'after-fetch':
                raise OSError('Fixture after fetch')
            return result
        if args[0] == 'symbolic-ref' and scenario in ('after-ref-prepare', 'slow-ref-prepare'):
            lock = self.repo / '.git/refs/heads/agent/exported.lock'
            if lock.exists():
                log('export-ref-prepared')
                if scenario == 'after-ref-prepare':
                    raise OSError('Fixture after ref prepare')
                await asyncio.sleep(10)
        return await original_git(*args, **kwargs)
    async def create_branch(intent):
        log('export-update-ref')
        if scenario == 'before-update-ref':
            raise OSError('Fixture before update-ref')
        if scenario == 'branch-race-dangling':
            git(self.repo, 'symbolic-ref', 'refs/heads/agent/exported', 'refs/heads/missing')
        if scenario == 'branch-race':
            git(self.repo, 'update-ref', 'refs/heads/agent/exported', self.spec['request']['repository']['base_sha'])
        result = await original_branch(intent)
        if scenario == 'after-update-ref':
            raise OSError('Fixture after update-ref')
        return result
    self.core.write, self.git, self.create_branch = interrupted, git_operation, create_branch


_Export.__init__ = initialize
main()
