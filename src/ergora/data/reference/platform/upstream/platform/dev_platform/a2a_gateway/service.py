"""Domain service for A2A. Transport success is never merge authorization."""
import asyncio
from datetime import datetime, timezone
import json
import uuid

from google.protobuf.json_format import MessageToDict
from a2a.helpers import new_data_part, new_text_message
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import a2a_pb2 as pb
from a2a.utils.errors import (InvalidParamsError, TaskNotFoundError, TaskNotCancelableError,
                             UnsupportedOperationError, PushNotificationNotSupportedError,
                             ExtensionSupportRequiredError)

from ..contracts import canonical_sha, need, COMMIT, SHA256
from . import CONTRACT_URI
from .store import utc_text


class Gateway(RequestHandler):
    def __init__(self, store, backend, leases):
        self.store, self.backend, self.leases = store, backend, leases
        self.lock = asyncio.Lock()

    def principal(self, params, context):
        if not context.user.is_authenticated or not context.user.user_name:
            raise InvalidParamsError('Authenticated principal required')
        if params.tenant or context.tenant:
            raise UnsupportedOperationError('Tenant routing is not configured')
        unknown = context.requested_extensions - {CONTRACT_URI}
        if unknown:
            raise ExtensionSupportRequiredError('Requested extension is not supported')
        return context.user.user_name

    def row(self, task_id, principal):
        row = self.store.owned(task_id, principal)
        if row is None:
            raise TaskNotFoundError()
        return row

    def claim_args(self, params):
        message = params.message
        if message.role != pb.ROLE_USER or len(message.parts) != 1 or not message.parts[0].HasField('data'):
            raise InvalidParamsError('Send exactly one ROLE_USER data part with the admitted task reference')
        if message.reference_task_ids or message.metadata or params.metadata:
            raise InvalidParamsError('Reference tasks and request/message metadata are not executable inputs')
        if set(message.extensions) - {CONTRACT_URI}:
            raise ExtensionSupportRequiredError('Unknown message extension')
        part = message.parts[0]
        if part.metadata or part.filename or part.media_type not in ('', 'application/json'):
            raise InvalidParamsError('Only an application/json data reference is accepted')
        config = params.configuration
        if config.HasField('task_push_notification_config'):
            raise PushNotificationNotSupportedError()
        if config.accepted_output_modes and 'application/json' not in config.accepted_output_modes:
            raise InvalidParamsError('application/json output mode is required')
        if config.history_length < 0:
            raise InvalidParamsError('Negative history length')
        return MessageToDict(part.data)

    def lease_owner(self, row):
        return self.store.lease_owner(row['principal'])

    def release_if_safe(self, row, spec, snapshot):
        if row['safe_terminal'] and row['phase'] != 'RELEASED':
            self.leases.release(spec['request']['tracker'], self.lease_owner(row), row['domain_id'],
                                canonical_sha(spec), canonical_sha(snapshot))
            self.store.update(row['id'], phase='RELEASED')

    def finish_unstarted(self, row, spec, reason):
        try:
            self.leases.acquire(spec['request']['tracker'], self.lease_owner(row), row['domain_id'], canonical_sha(spec))
        except ValueError:
            self.store.update(row['id'], snapshot={'phase': 'PRE_SUBMIT_RECONCILIATION', 'terminal': False})
            return self.row(row['id'], row['principal'])
        snapshot = {'phase': 'BLOCKED', 'terminal': True, 'outcome': {
            'status': 'BLOCKED', 'task_id': row['domain_id'], 'request_sha256': spec['request_sha256'],
            'detail': reason, 'fence': {'confirmed': True, 'no_runtime_start': True}}}
        self.store.update(row['id'], phase='TERMINAL', safe_terminal=1, snapshot=snapshot)
        row = self.row(row['id'], row['principal'])
        self.release_if_safe(row, spec, snapshot)
        return self.row(row['id'], row['principal'])

    async def refresh(self, row, allow_start=False):
        compiled = self.store.compiled(row); spec = compiled['spec']
        if row['safe_terminal']:
            snapshot = json.loads(row['snapshot'])
            self.release_if_safe(row, spec, snapshot)
            return row
        if row['phase'] == 'NEW':
            if row['cancel_requested']:
                return self.finish_unstarted(row, spec, 'Canceled before runtime submission')
            if self.store.admission_expired(row):
                return self.finish_unstarted(row, spec, 'Admission expired before runtime submission')
            if not allow_start:
                return row
            # Shared lease is durable before the start-intent is recorded. A crash
            # can leave an unused lease; no timeout silently releases ownership.
            self.leases.acquire(spec['request']['tracker'], self.lease_owner(row), row['domain_id'], canonical_sha(spec))
            if self.store.admission_expired(row):
                return self.finish_unstarted(row, spec, 'Admission expired while acquiring issue ownership')
            self.store.update(row['id'], phase='SUBMITTING')
            try:
                run_id = await self.backend.start(spec)
                need(type(run_id) is str and run_id, 'Backend returned no run ID')
                self.store.update(row['id'], phase='RUNNING', run_id=run_id)
            except Exception:
                # Start may have reached Temporal. Never resubmit after ambiguity.
                self.store.update(row['id'], phase='RECONCILING', snapshot={'phase': 'START_UNCONFIRMED', 'terminal': False})
                return self.row(row['id'], row['principal'])
            row = self.row(row['id'], row['principal'])
        try:
            self.leases.assert_held(spec['request']['tracker'], self.lease_owner(row), row['domain_id'], canonical_sha(spec))
        except ValueError:
            self.store.update(row['id'], phase='RECONCILING', snapshot={'phase': 'LEASE_UNCONFIRMED', 'terminal': False})
            return self.row(row['id'], row['principal'])
        if not row['run_id']:
            try:
                run_id = await self.backend.lookup(spec)
            except Exception:
                run_id = None
            if not run_id:
                self.store.update(row['id'], phase='RECONCILING', snapshot={'phase': 'START_UNCONFIRMED', 'terminal': False})
                return self.row(row['id'], row['principal'])
            self.store.update(row['id'], phase='RUNNING', run_id=run_id)
            row = self.row(row['id'], row['principal'])
        try:
            snapshot = await self.backend.poll(spec, row['run_id'])
            if row['cancel_requested'] and not snapshot.get('terminal'):
                await self.backend.cancel(spec, row['run_id'], 'Cancellation requested by authenticated A2A task owner')
                snapshot = await self.backend.poll(spec, row['run_id'])
            need(type(snapshot) is dict and snapshot.get('run_id') == row['run_id'], 'Backend run binding mismatch')
            need(type(snapshot.get('terminal')) is bool and type(snapshot.get('phase')) is str, 'Invalid backend status')
            safe = self.safe_terminal(snapshot, spec)
            self.store.update(row['id'], phase='TERMINAL' if safe else 'RUNNING', snapshot=snapshot, safe_terminal=int(safe))
        except Exception:
            self.store.update(row['id'], phase='RECONCILING', snapshot={'phase': 'BACKEND_UNCONFIRMED', 'terminal': False})
            return self.row(row['id'], row['principal'])
        row = self.row(row['id'], row['principal'])
        self.release_if_safe(row, spec, snapshot)
        return row

    @staticmethod
    def safe_terminal(snapshot, spec):
        if not snapshot['terminal']:
            return False
        outcome = snapshot.get('outcome', {})
        if outcome.get('task_id') != spec['request']['task_id'] or outcome.get('request_sha256') != spec['request_sha256']:
            return False
        phase = snapshot['phase']
        if outcome.get('status') != phase:
            return False
        if phase == 'BLOCKED':
            return outcome.get('fence', {}).get('confirmed') is True
        if phase != 'REVIEW_READY':
            return False
        candidate = outcome.get('candidate_sha')
        need(type(candidate) is str and COMMIT.fullmatch(candidate), 'Missing final candidate SHA')
        need(outcome.get('profile_sha256') == spec['profile_sha256'], 'Outcome profile binding mismatch')
        verification, review = outcome.get('verification', {}), outcome.get('review', {})
        need(verification.get('candidate_sha') == candidate and review.get('candidate_sha') == candidate, 'Evidence candidate mismatch')
        need(outcome.get('evidence_sha256') == canonical_sha({'verification': verification, 'review': review}), 'Evidence digest mismatch')
        return True

    def task(self, row, include_artifacts=True):
        snapshot = json.loads(row['snapshot']) if row['snapshot'] else {'phase': row['phase'], 'terminal': False}
        phase = snapshot.get('phase', row['phase'])
        outcome = snapshot.get('outcome', {})
        safe = bool(row['safe_terminal'])
        if safe and phase == 'REVIEW_READY':
            state = pb.TASK_STATE_COMPLETED
            description = 'REVIEW_READY: candidate and evidence await human merge review; no merge or deployment authorized.'
        elif safe:
            state = pb.TASK_STATE_CANCELED if row['cancel_requested'] else pb.TASK_STATE_FAILED
            description = 'External work is confirmed stopped. Create a new admitted task revision for further work.'
        elif phase == 'AWAITING_PLAN_APPROVAL':
            state = pb.TASK_STATE_INPUT_REQUIRED
            description = 'A trusted human must approve the exact plan through the existing approval interface. A2A messages cannot approve.'
        elif row['phase'] == 'RECONCILING' or snapshot.get('terminal') or phase in {'START_UNCONFIRMED', 'BACKEND_UNCONFIRMED', 'PRE_SUBMIT_RECONCILIATION'}:
            state = pb.TASK_STATE_INPUT_REQUIRED
            description = 'Operator reconciliation required. Ownership is retained; cancellation or external work termination is unconfirmed.'
        else:
            state = pb.TASK_STATE_SUBMITTED if phase in {'NEW', 'SUBMITTING'} else pb.TASK_STATE_WORKING
            description = 'Cancellation requested; awaiting confirmed stop.' if row['cancel_requested'] else 'Task is running under the admitted workflow.'
        metadata = {'contract_uri': CONTRACT_URI, 'domain_task_id': row['domain_id'], 'compiled_sha256': row['digest'],
                    'phase': phase, 'merge_authorized': False, 'safe_to_rework': safe,
                    'cancel_requested': bool(row['cancel_requested'])}
        status = snapshot.get('status', {})
        for name in ('request_sha256', 'plan_sha256', 'candidate_sha'):
            value = outcome.get(name, status.get(name))
            if value is not None:
                metadata[name] = value
        if row['run_id']:
            metadata['workflow_id'] = 'dev-task/' + row['domain_id']
            metadata['run_id'] = row['run_id']
        task = pb.Task(id=row['id'], context_id=row['context_id'],
                       status=pb.TaskStatus(state=state, timestamp=datetime.fromtimestamp(row['updated'], timezone.utc),
                                            message=new_text_message(description, context_id=row['context_id'], task_id=row['id'])),
                       metadata=metadata)
        if safe and phase == 'REVIEW_READY' and include_artifacts:
            # This manifest contains hashes and relative trusted artifact handles;
            # it never exposes local file bytes, credentials or arbitrary URLs.
            refs = []
            for stage in ('verification', 'review'):
                for artifact in outcome[stage].get('artifacts', []):
                    if isinstance(artifact, dict) and isinstance(artifact.get('sha256'), str) and SHA256.fullmatch(artifact['sha256']):
                        refs.append({'stage': stage, 'name': artifact.get('name', ''), 'sha256': artifact['sha256']})
            handoff = {'task_id': row['domain_id'], 'compiled_sha256': row['digest'],
                       'request_sha256': outcome['request_sha256'], 'candidate_sha': outcome['candidate_sha'],
                       'evidence_sha256': outcome['evidence_sha256'], 'artifacts': refs, 'merge_authorized': False}
            task.artifacts.append(pb.Artifact(artifact_id='handoff-' + canonical_sha(handoff), name='verified-candidate-handoff',
                                             description='SHA-bound manifest; resolve bytes through the trusted artifact service.',
                                             parts=[new_data_part(handoff, media_type='application/json')]))
        return task

    async def on_message_send(self, params, context):
        principal = self.principal(params, context); ref = self.claim_args(params)
        try:
            async with self.lock:
                if params.message.task_id:
                    target = self.row(params.message.task_id, principal)
                    previous_message = self.store.db.execute('SELECT task_id FROM messages WHERE principal=? AND message_id=?', (principal, params.message.message_id)).fetchone()
                    if target['safe_terminal'] and previous_message is None:
                        raise UnsupportedOperationError('A terminal A2A task cannot be resumed; create a new admitted revision')
                row, created = self.store.claim(ref, principal, params.message.message_id, params.message.context_id, params.message.task_id)
                row = await self.refresh(row, allow_start=True)
                task = self.task(row)
        except ValueError as error:
            raise InvalidParamsError(str(error)) from None
        if not params.configuration.return_immediately:
            while task.status.state in {pb.TASK_STATE_WORKING, pb.TASK_STATE_SUBMITTED}:
                await asyncio.sleep(2)
                async with self.lock:
                    row = await self.refresh(self.row(row['id'], principal))
                    task = self.task(row)
        return task

    async def on_get_task(self, params, context):
        principal = self.principal(params, context)
        if params.history_length < 0:
            raise InvalidParamsError('Negative history length')
        async with self.lock:
            row = await self.refresh(self.row(params.id, principal))
            return self.task(row)

    async def on_cancel_task(self, params, context):
        principal = self.principal(params, context)
        async with self.lock:
            row = self.row(params.id, principal)
            if row['safe_terminal']:
                raise TaskNotCancelableError()
            self.store.update(row['id'], cancel_requested=1)
            row = await self.refresh(self.row(params.id, principal))
            if not row['safe_terminal'] or json.loads(row['snapshot']).get('phase') != 'BLOCKED':
                # A2A CancelTask reports failure if cancellation was not completed;
                # the durable cancel intent remains visible through GetTask.
                raise TaskNotCancelableError('Cancellation requested but stop is not confirmed; poll GetTask. Ownership remains held.')
            return self.task(row)

    async def on_list_tasks(self, params, context):
        principal = self.principal(params, context)
        if params.page_size < 0 or params.page_size > 100 or params.history_length < 0:
            raise InvalidParamsError('Page size must be 0..100 and history length non-negative')
        # Cursor binds filters and principal. It is navigation, never authority.
        filters = {'principal': principal, 'context_id': params.context_id, 'status': int(params.status),
                   'after': params.status_timestamp_after.ToJsonString() if params.HasField('status_timestamp_after') else ''}
        filter_hash = canonical_sha(filters); offset = 0
        if params.page_token:
            try:
                digest, raw = params.page_token.split(':'); offset = int(raw)
                need(digest == filter_hash and 0 <= offset <= 1_000_000, 'Invalid list cursor')
            except (ValueError, TypeError):
                raise InvalidParamsError('Invalid list cursor') from None
        async with self.lock:
            rows = self.store.owned_rows(principal)
            tasks = []
            for row in rows:
                # List observes persisted snapshots; GetTask refreshes the backend.
                task = self.task(row, include_artifacts=params.include_artifacts)
                if params.context_id and task.context_id != params.context_id:
                    continue
                if params.status and task.status.state != params.status:
                    continue
                if params.HasField('status_timestamp_after') and task.status.timestamp.ToNanoseconds() <= params.status_timestamp_after.ToNanoseconds():
                    continue
                tasks.append(task)
            tasks.sort(key=lambda t: (t.status.timestamp.seconds, t.status.timestamp.nanos, t.id), reverse=True)
            size = params.page_size or 50; selected = tasks[offset:offset + size]
            token = filter_hash + ':' + str(offset + size) if offset + size < len(tasks) else ''
            return pb.ListTasksResponse(tasks=selected, next_page_token=token, page_size=size, total_size=len(tasks))

    async def on_message_send_stream(self, params, context):
        raise UnsupportedOperationError('Streaming is not supported; send with returnImmediately=true and poll GetTask')
        yield

    async def on_subscribe_to_task(self, params, context):
        raise UnsupportedOperationError('Subscriptions are not supported')
        yield

    async def on_create_task_push_notification_config(self, params, context):
        raise PushNotificationNotSupportedError()

    async def on_get_task_push_notification_config(self, params, context):
        raise PushNotificationNotSupportedError()

    async def on_list_task_push_notification_configs(self, params, context):
        raise PushNotificationNotSupportedError()

    async def on_delete_task_push_notification_config(self, params, context):
        raise PushNotificationNotSupportedError()

    async def on_get_extended_agent_card(self, params, context):
        raise UnsupportedOperationError('Extended agent card is not configured')
