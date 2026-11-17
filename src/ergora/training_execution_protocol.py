"""Identity-bound execution records shared with the dependency-isolated native hook."""

from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

from . import budget_clock, processes, reference


PROTOCOL = 'ergora-training-execution-v1'
BUDGET_TASK_QUEUE = 'ergora-training-budget-v1'
CYCLE_MEMO_KEY = 'ergora.training_cycle_sha256'
CYCLE_MEASUREMENT_MODES = ('collect-round', 'reconcile-round')
CYCLE_START_MODES = ('prepare-candidate', 'confirm-candidate', 'dispatch-candidate')
CYCLE_EXECUTION_MODES = ('request-execution-candidate', 'observe-candidate')
CYCLE_CANDIDATE_MODES = (*CYCLE_START_MODES, 'reconcile-candidate', *CYCLE_EXECUTION_MODES)
CYCLE_WORK_MODES = ('prepare-controller', 'submit-controller', *CYCLE_START_MODES, *CYCLE_EXECUTION_MODES, *CYCLE_MEASUREMENT_MODES)
CYCLE_OBSERVATION_MODES = ('inspect', 'inspect-controller-activity', 'reconcile-controller', 'reconcile-candidate')
LIMIT = 1_048_576
ARTIFACT_LIMIT = 10_000_000
MEASUREMENT_SOURCES = ('training_rounds.py', 'reference_training_evidence.py',
                       'data/schemas/training-rounds-v1.json', 'reference_training_release.py')


class _CycleCapacityError(ValueError):
    pass


def _read_cycle_bytes(path: Path, limit: int) -> bytes:
    from .asset_trees import is_link

    for selected in (path, *path.parents):
        if is_link(selected):
            raise ValueError('Training cycle records cannot use symlinks or reparse points')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Training cycle records require ordinary files')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise _CycleCapacityError(f'Complete training cycle record exceeds {limit} bytes; nothing was truncated')
    return raw


def cycle_supervisor_main() -> None:
    """Supervise one original H without loading the SDK or application owners."""
    import logging
    import signal

    limit = 32_768
    cancelled = False

    def cancel(signum, frame):
        nonlocal cancelled
        cancelled = True

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    raw = sys.stdin.buffer.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Complete cycle operation request exceeds 32 KiB')
    payload = decode(raw)
    validate_cycle_operation(payload)
    identity = payload['identity']
    expected = identity['parent']
    if processes.identity(expected['pid']) != expected or os.getppid() != expected['pid']:
        raise ValueError('Cycle operation lost its original complete parent identity')
    output = Path(identity['control_home']) / 'operations/training-cycles' / identity['operation_id']
    for parent in (output, *output.parents):
        if parent.is_symlink() or parent.exists() and not parent.is_dir():
            raise ValueError('Cycle operation output requires original ordinary directories')
    output.mkdir(parents=True, mode=0o700)
    with (output / 'supervisor.stderr').open('xb') as stderr:
        os.dup2(stderr.fileno(), sys.stderr.fileno())
    with (output / 'request.json').open('xb') as request:
        request.write(raw)

    def stopped():
        try:
            return (cancelled or cycle_operation_remaining(payload) <= 0
                    or processes.identity(expected['pid']) != expected)
        except (OSError, ValueError):
            return True

    def frame(event, field, value):
        encoded = json.dumps({**identity, 'event': event, field: value},
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(encoded) > (65_536 if event == 'stopped' else limit):
            if event == 'stopped':
                raise ValueError('Complete cycle operation stopped frame exceeds its capacity')
            logging.error('Complete cycle operation response exceeds frame capacity: %s', value)
            failure = {'status': 'capacity_exceeded',
                       'reason': 'Complete original result exceeds the cycle frame capacity'}
            if '_stdout_ref' in value:
                failure['_stdout_ref'] = value['_stdout_ref']
            encoded = json.dumps({**identity, 'event': event, field: failure},
                ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if identity['protocol'] in ('ergora-training-cycle-operation-v2', 'ergora-training-cycle-operation-v3') and len(encoded) > (
                65_536 if event == 'stopped' else limit):
            raise ValueError('Complete replacement cycle operation frame still exceeds its capacity')
        sys.stdout.buffer.write(encoded + b'\n')
        sys.stdout.buffer.flush()

    result = processes.run([sys.executable, '-P', '-c',
        'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main(False)'],
        Path.cwd(), output / 'helper', 60, raw.decode('utf-8'), dict(os.environ),
        supervised=True, stop_requested=stopped)
    frame('stopped', 'process', result)
    observed = {
        'status': 'unknown', 'reason': 'Original cycle helper did not complete within its allowance',
        'helper_status': result['status']}
    if result['status'] == 'succeeded':
        try:
            stdout = _read_cycle_bytes(output / 'helper/stdout.txt', limit)
        except _CycleCapacityError as error:
            logging.exception('Complete cycle helper stdout retained at %s', output / 'helper/stdout.txt')
            observed = {'status': 'capacity_exceeded', 'reason': str(error)}
        else:
            observed = decode(stdout)
            observed['_stdout_ref'] = {'file': 'helper/stdout.txt', 'bytes': len(stdout),
                                       'sha256': hashlib.sha256(stdout).hexdigest()}
    frame('result', 'result', observed)


def cycle_workflow_type(protocol: str) -> str:
    try:
        return {'ergora-training-cycle-v1': 'TrainingCycleWorkflow',
                'ergora-training-cycle-v2': 'TrainingCycleWorkflowV2',
                'ergora-training-cycle-v3': 'TrainingCycleWorkflowV3'}[protocol]
    except KeyError as error:
        raise ValueError('Unsupported training cycle protocol') from error


GATE_SOURCES = (
    'training_execution_protocol.py', 'reference_training_execution.py',
    'reference_training_submission.py', 'reference_training_context.py',
    'reference_training_runtime.py', 'reference_training_cancellation.py', 'reference_history.py',
    'reference_training_budget.py', 'reference_training_worker.py', 'training.py', 'reference.py',
    'training_cycles.py', 'registrations.py', 'data/schemas/training-cycle-v1.json',
    'data/schemas/project-registration-v1.json', 'definition_bundles.py', 'contracts.py',
    'asset_trees.py', 'state.py', 'budget_clock.py', 'processes.py', 'reference_creation_process.py',
    '__init__.py', 'data/reference-manifest.json', 'data/native-runtime/training-executor-admission-v1.json',
)
GATE_SOURCE_PROTOCOLS = {
    reference.TRAINING_PROTOCOL: GATE_SOURCES,
    'training-executor-admission-v2': (*GATE_SOURCES[:-1], 'data/native-runtime/training-executor-admission-v2.json'),
}


ROUND_COVERAGE = {'records': 'saved-observations', 'artifacts': 'index-only', 'runtime_status': 'not_queried',
                  'authorization_status': 'not_evaluated', 'origin_authenticated': False,
                  'execution_success': None, 'promotion_approved': False}


def encode_round_content(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def round_content_sha(value: dict) -> str:
    return hashlib.sha256(encode_round_content(value)).hexdigest()


def round_comparison(records: dict) -> dict:
    experiment = records['experiment']
    manifest = experiment['manifest']
    return {'baseline_id': manifest['baseline_id'], 'baseline_commit': manifest['baseline_commit'],
            'base_config_sha256': manifest['base_config_sha256'],
            'workload_fingerprint': manifest['workload_fingerprint'],
            'candidate_commit': manifest['candidate_commit'],
            'candidate_config_sha256': manifest['candidate_config_sha256'],
            'manifest_sha256': experiment['binding']['manifest_sha']}


def round_anchor(comparison: dict) -> dict:
    return {key: comparison[key] for key in ('baseline_id', 'baseline_commit',
                                            'base_config_sha256', 'workload_fingerprint')}


def validate_round_content(report: dict) -> None:
    """Check content of a schema-validated report, without authenticating its origin."""
    if report['coverage'] != ROUND_COVERAGE:
        raise ValueError('Training round index cannot grant execution, authorization or promotion')
    parent, seen = None, set()
    for item in report['rounds']:
        content = {key: value for key, value in item.items() if key != 'sha256'}
        if item['parent_sha256'] != parent or item['sha256'] != round_content_sha(content):
            raise ValueError('Training round content or predecessor link differs from its SHA256')
        parent = item['sha256']
        if item['experiment_id'] in seen:
            raise ValueError('Training round index contains the same original experiment twice')
        seen.add(item['experiment_id'])
        native = item['native']
        records, evidence, submission, approval = (native[key] for key in ('records', 'evidence', 'submission', 'approval'))
        experiment = records['experiment']
        binding = experiment['binding']
        revision = records['project_revision']
        for view in (records, evidence, submission, *([approval] if approval is not None else [])):
            if view['project'] != report['project']['id'] or view['project_revision'] != revision:
                raise ValueError('Training round observations belong to different projects or revisions')
        if (experiment['experiment_id'] != item['experiment_id'] or binding['experiment_id'] != item['experiment_id']
                or any(view['experiment_id'] != item['experiment_id'] for view in (evidence, submission))
                or evidence['binding'] != binding or evidence['recorded_gate_report'] != experiment['gate_report']):
            raise ValueError('Training round observations have different original experiment bindings or gates')
        files = {**records['baseline_files'], **experiment['files']}
        if any(evidence['files'].get(name) != digest for name, digest in files.items()):
            raise ValueError('Training sources changed between the original record and evidence observations')
        if (item['comparison'] != round_comparison(records)
                or item['comparison']['candidate_commit'] != binding['candidate_sha']
                or item['comparison']['baseline_commit'] != binding['baseline_sha']):
            raise ValueError('Training round comparison differs from its original manifest')
        if round_anchor(item['comparison']) != report['initial_anchor']:
            raise ValueError('Training round index requires one reviewed initial baseline; baseline migration is separate')
        if submission['status'] in ('prepared', 'unknown', 'submitted') and (
                submission['manifest_sha256'] != binding['manifest_sha']
                or submission['confirmation']['binding'] != binding):
            raise ValueError('Training round submission names a different original manifest')
        if submission['status'] == 'submitted':
            if (approval is None or approval['experiment_id'] != item['experiment_id']
                    or approval['run_id'] != submission['run_id']):
                raise ValueError('Training round approval must observe the original submitted run')
        elif approval is not None:
            raise ValueError('Training round approval is not evaluated for an unresolved or unsubmitted ingress')
    previous = report['previous_report']
    if previous is not None and (not 1 <= previous['rounds'] < len(report['rounds'])
            or previous['last_round_sha256'] != report['rounds'][previous['rounds'] - 1]['sha256']):
        raise ValueError('Training round extension does not retain its declared original prefix')


ROUND_COMMON = ('baseline_id', 'baseline_commit', 'base_config_sha256', 'workload_fingerprint',
           'dataset_manifest_sha256', 'initial_checkpoint_sha256', 'environment_fingerprint',
           'validation_contract_sha256', 'comparison_tool_sha256', 'checks_required',
           'quality_required', 'performance_policy')


def round_selection(plan: dict, authorization: dict) -> dict:
    manifest = plan['admissions'][0]['observation']['experiment']['manifest']
    return {'count': len(plan['admissions']),
        'common_sha256': CycleAdmission._sha({key: manifest[key] for key in ROUND_COMMON}),
        'measurement_sources_sha256': CycleAdmission._sha(authorization['measurement_sources'])}


def round_report_binding(saved, plan, ordinal, previous):
    report = saved['report']
    if (report['project'] != {'id': plan['project']['id'], 'repo': plan['project']['repo'],
                             'registration_sha256': plan['project']['registration']['sha256']}
            or len(report['rounds']) != ordinal + 1):
        raise ValueError('Round index differs from its original registered selection or complete count')
    for index, item in enumerate(report['rounds']):
        selected = plan['definition']['candidates'][index]
        admitted = plan['admissions'][index]['observation']['experiment']
        if (item['experiment_id'] != selected['experiment_id']
                or item['annotation'] != {key: selected[key] for key in ('change', 'next_bottleneck')}
                or item['native']['records']['experiment']['manifest'] != admitted['manifest']
                or item['native']['records']['experiment']['spec'] != admitted['spec']
                or item['native']['records']['experiment']['binding'] != admitted['binding']
                or item['native']['records']['project_revision'] != plan['project']['revision']
                or {key: admitted['manifest'][key] for key in ROUND_COMMON} != {
                    key: plan['admissions'][0]['observation']['experiment']['manifest'][key] for key in ROUND_COMMON}
                or item['comparison']['manifest_sha256'] != selected['manifest_sha256']):
            raise ValueError('Round index changed a frozen candidate, manifest or annotation')
    if previous is None:
        if report['previous_report'] is not None:
            raise ValueError('First round index cannot replace a prior prefix')
    elif (report['rounds'][:-1] != previous['report']['rounds']
            or report['initial_anchor'] != previous['report']['initial_anchor']
            or report['previous_report'] != {'sha256': previous['sha256'],
                'rounds': len(previous['report']['rounds']),
                'last_round_sha256': previous['report']['rounds'][-1]['sha256']}):
        raise ValueError('Round index differs from its complete original previous prefix')


def round_pin(saved, raw):
    if hashlib.sha256(raw).hexdigest() != saved['sha256']:
        raise ValueError('Round prefix changed its complete original raw bytes after read')
    return {'directory': saved['directory'], 'sha256': saved['sha256'], 'bytes': len(raw),
        'rounds': len(saved['report']['rounds']), 'last_round_sha256': saved['report']['rounds'][-1]['sha256'],
        'initial_anchor_sha256': CycleAdmission._sha(saved['report']['initial_anchor'])}


def round_state(observed, evidence, item, intent):
    """Combine the four original owners; local approval is never a positive predicate."""
    if observed['status'] != 'observed':
        return 'unknown'
    facts, native, runtime, execution = (observed[key] for key in ('facts', 'native', 'runtime', 'execution'))
    if not all(isinstance(value, dict) for value in (native, runtime, execution)):
        return 'unknown'
    binding = intent['observation']['experiment']['binding']
    records, indexed_evidence, submitted = (item['native'][key] for key in ('records', 'evidence', 'submission'))
    experiment = records['experiment']
    detail = runtime.get('status', runtime.get('outcome', {}))
    request = execution['records'].get('request')
    if (evidence != indexed_evidence or evidence['binding'] != binding
            or experiment['binding'] != binding or experiment['manifest'] != intent['observation']['experiment']['manifest']
            or experiment['spec'] != intent['observation']['experiment']['spec']
            or evidence['recorded_gate_report'] != experiment['gate_report']
            or records['project_revision'] != intent['project_revision']
            or submitted['status'] != 'submitted' or facts['submission']['state'] != 'submitted'
            or any(submitted[key] != observed['submission'][key] for key in ('workflow_id', 'run_id', 'intent_sha256'))
            or runtime['workflow_id'] != submitted['workflow_id'] or runtime['run_id'] != submitted['run_id']
            or detail.get('binding') != binding or native.get('job', {}).get('binding') != binding
            or request is None or request['job_id'] != native.get('job', {}).get('job_id')
            or detail.get('job_id') != request['job_id'] or experiment['job_id'] != request['job_id']
            or request['start_intent_sha256'] != CycleAdmission._sha(intent)
            or facts['candidate']['current_project_matches'] is not True
            or facts['candidate']['parent_stop_visible'] is not False
            or evidence['baseline_matches'] is not True or evidence['fence_recorded'] is not False):
        return 'unknown'
    result = experiment['result']
    if (result is not None and (native['state'] != result['state'] or native.get('detail') != result['detail'])
            or any(evidence['files'].get(name) != digest for name, digest in
                   {**records['baseline_files'], **experiment['files']}.items())):
        return 'unknown'
    gate = evidence['recorded_gate_report']
    if native['state'] in ('FAILED', 'CANCELLED') or gate is not None and gate['passed'] is False:
        return 'rejected'
    if native['state'] in ('QUEUED', 'RUNNING') or execution['durable_stop_confirmed'] is not True:
        return 'pending'
    if (native['state'] != 'SUCCEEDED' or experiment['recorded_result_state'] != 'SUCCEEDED'
            or execution['executor_stop_confirmed'] is not True or execution['reap_record_observed'] is not True
            or set(execution['record_sha256']) != {'request', 'launch', 'attempt', 'ack', 'stopped'}
            or gate is None or gate['passed'] is not True or evidence['archive_status'] != 'recorded'
            or evidence['archive'] is None or evidence['archive']['artifact_content_status'] != 'not_read'):
        return 'unknown'
    evidence_sha = evidence['archive']['evidence_sha256']
    if gate['evidence_sha256'] != evidence_sha:
        return 'unknown'
    if (runtime['temporal_status'] == 'RUNNING' and runtime['terminal'] is False
            and runtime['phase'] == 'AWAITING_RELEASE' and 'status' in runtime
            and detail.get('evidence_sha') == evidence_sha):
        return 'accepted'
    if (runtime['temporal_status'] == 'COMPLETED' and runtime['terminal'] is True
            and runtime['phase'] in ('RELEASE_EXPIRED', 'INTEGRATION_TASK_CREATED') and 'outcome' in runtime
            and detail.get('report_uri') == Path(result['gate']['report']).as_uri()):
        return 'accepted'
    if runtime['temporal_status'] == 'RUNNING' and runtime['terminal'] is False and runtime['phase'] in (
            'QUEUED', 'RUNNING', 'COLLECTING', 'GATING'):
        return 'pending'
    return 'unknown'


def round_acceptance(value, ref, intent):
    sha = CycleAdmission._sha
    facts, runtime, evidence, execution = (value[key] for key in ('facts', 'runtime', 'evidence', 'execution'))
    kind = 'status' if 'status' in runtime else 'outcome'
    detail = runtime[kind]
    return {'observation': ref, 'source_operation_id': value['identity']['operation_id'],
        'candidate': {key: facts['candidate'][key] for key in ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision')}
            | {'registration_sha256': intent['registration_sha256']},
        'submission': {key: facts['submission'][key] for key in ('intent_sha256', 'workflow_id', 'run_id')}
            | {'spec_sha256': sha(intent['observation']['experiment']['spec'])},
        'execution': {'owner_sha256': sha(execution['owner']), 'record_sha256': execution['record_sha256'],
                      'raw_inventory_sha256': sha(execution['raw_sha256'])},
        'runtime': {'namespace': value['activity_context']['service_namespace'], 'kind': kind, 'phase': runtime['phase'],
            'job_id': detail['job_id'], 'binding_sha256': sha(detail['binding']), 'memo_sha256': sha(intent),
            'evidence_sha': detail['evidence_sha'] if kind == 'status' else None,
            'report_uri': detail['report_uri'] if kind == 'outcome' else None},
        'evidence': {'evidence_sha256': evidence['archive']['evidence_sha256'],
            'gate_report_sha256': sha(evidence['recorded_gate_report']), 'files_sha256': sha(evidence['files'])},
        'common_sha256': value['selection']['common_sha256'],
        'measurement_sources_sha256': value['selection']['measurement_sources_sha256']}


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' has incomplete or unexpected fields')


def _match(actual, expected, label):
    from dev_platform.contracts import canonical_sha

    if canonical_sha(actual) != canonical_sha(expected):
        raise ValueError(label + ' differs from its complete original identity')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Execution record requires a complete SHA256')


def validate_budget_binding(value):
    common = {'cycle_id', 'authorization_sha256', 'task_queue'}
    if (not isinstance(value, dict) or set(value) not in (common, common | {'controller'})
            or not isinstance(value.get('cycle_id'), str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value['cycle_id']) is None
            or value.get('task_queue') != BUDGET_TASK_QUEUE):
        raise ValueError('Training intent requires its exact original budget and supported protocol queue')
    _digest(value.get('authorization_sha256'))
    if 'controller' in value:
        controller = value['controller']
        version = controller.get('protocol') if isinstance(controller, dict) else None
        _exact(controller, ('protocol', 'workflow_id', 'run_id', 'intent_sha256', 'ordinal',
                           *(('predecessor',) if version in ('ergora-training-cycle-v2', 'ergora-training-cycle-v3') else ())), 'Controller binding')
        if (version not in ('ergora-training-cycle-v1', 'ergora-training-cycle-v2', 'ergora-training-cycle-v3')
                or not isinstance(controller['workflow_id'], str) or not controller['workflow_id']
                or not isinstance(controller['run_id'], str) or not 1 <= len(controller['run_id']) <= 128
                or controller['run_id'].strip() != controller['run_id']
                or type(controller['ordinal']) is not int or not 0 <= controller['ordinal'] < 32):
            raise ValueError('Controller binding requires its original fixed run and selected ordinal')
        _digest(controller['intent_sha256'])
        if version in ('ergora-training-cycle-v2', 'ergora-training-cycle-v3'):
            validate_round_predecessor(controller['predecessor'], controller['ordinal'])


def validate_round_prefix(value: dict) -> None:
    _exact(value, ('directory', 'sha256', 'bytes', 'rounds', 'last_round_sha256',
                   'initial_anchor_sha256'), 'Cycle round prefix')
    if (not isinstance(value['directory'], str) or not Path(value['directory']).is_absolute()
            or '..' in Path(value['directory']).parts
            or type(value['bytes']) is not int or not 0 < value['bytes'] <= ARTIFACT_LIMIT
            or type(value['rounds']) is not int or not 1 <= value['rounds'] <= 32):
        raise ValueError('Cycle round prefix has an invalid path, length or count')
    for key in ('sha256', 'last_round_sha256', 'initial_anchor_sha256'):
        _digest(value[key])


def validate_round_acceptance(value: dict) -> None:
    _exact(value, ('observation', 'source_operation_id', 'candidate', 'submission', 'execution',
                   'runtime', 'evidence', 'common_sha256', 'measurement_sources_sha256'), 'Round acceptance')
    if not isinstance(value['source_operation_id'], str) or re.fullmatch('[a-f0-9]{32}', value['source_operation_id']) is None:
        raise ValueError('Round acceptance requires its original operation ID')
    ref = value['observation']
    _exact(ref, ('path', 'sha256', 'bytes'), 'Round observation reference')
    if (not isinstance(ref['path'], str) or not Path(ref['path']).is_absolute() or '..' in Path(ref['path']).parts
            or type(ref['bytes']) is not int or not 0 < ref['bytes'] <= ARTIFACT_LIMIT):
        raise ValueError('Round observation reference has an invalid path or complete length')
    _digest(ref['sha256'])
    candidate = value['candidate']
    _exact(candidate, ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision', 'registration_sha256'), 'Accepted candidate')
    if (type(candidate['ordinal']) is not int or not 0 <= candidate['ordinal'] < 32
            or type(candidate['project_revision']) is not int or candidate['project_revision'] < 1
            or not isinstance(candidate['experiment_id'], str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', candidate['experiment_id']) is None):
        raise ValueError('Accepted candidate identity is invalid')
    for key in ('manifest_sha256', 'registration_sha256'):
        _digest(candidate[key])
    submitted = value['submission']
    _exact(submitted, ('intent_sha256', 'workflow_id', 'run_id', 'spec_sha256'), 'Accepted submission')
    for key in ('intent_sha256', 'spec_sha256'):
        _digest(submitted[key])
    for key in ('workflow_id', 'run_id'):
        if not isinstance(submitted[key], str) or not submitted[key].strip():
            raise ValueError('Accepted submission has no original fixed run')
    execution = value['execution']
    _exact(execution, ('owner_sha256', 'record_sha256', 'raw_inventory_sha256'), 'Accepted execution')
    _exact(execution['record_sha256'], ('request', 'launch', 'attempt', 'ack', 'stopped'), 'Accepted execution records')
    for digest in (execution['owner_sha256'], execution['raw_inventory_sha256'], *execution['record_sha256'].values()):
        _digest(digest)
    runtime = value['runtime']
    _exact(runtime, ('namespace', 'kind', 'phase', 'job_id', 'binding_sha256', 'memo_sha256',
                     'evidence_sha', 'report_uri'), 'Accepted runtime')
    if (not isinstance(runtime['namespace'], str) or not runtime['namespace']
            or not isinstance(runtime['job_id'], str) or not runtime['job_id']
            or runtime['kind'] not in ('status', 'outcome')
            or runtime['kind'] == 'status' and (runtime['phase'] != 'AWAITING_RELEASE' or runtime['report_uri'] is not None)
            or runtime['kind'] == 'outcome' and (runtime['phase'] not in ('RELEASE_EXPIRED', 'INTEGRATION_TASK_CREATED')
                or runtime['evidence_sha'] is not None or not isinstance(runtime['report_uri'], str))):
        raise ValueError('Accepted runtime does not name an admissible original phase')
    for digest in (runtime['binding_sha256'], runtime['memo_sha256']):
        _digest(digest)
    if runtime['kind'] == 'status':
        _digest(runtime['evidence_sha'])
    _exact(value['evidence'], ('evidence_sha256', 'gate_report_sha256', 'files_sha256'), 'Accepted evidence')
    for digest in (*value['evidence'].values(), value['common_sha256'], value['measurement_sources_sha256']):
        _digest(digest)


def validate_round_predecessor(value, ordinal: int) -> None:
    if ordinal == 0:
        if value is not None:
            raise ValueError('First selected candidate cannot acquire a predecessor')
        return
    _exact(value, ('prefix', 'acceptance'), 'Cycle predecessor')
    validate_round_prefix(value['prefix'])
    validate_round_acceptance(value['acceptance'])
    if value['prefix']['rounds'] != ordinal or value['acceptance']['candidate']['ordinal'] != ordinal - 1:
        raise ValueError('Cycle predecessor is not the complete immediately previous prefix')


def validate_round_observation(value: dict) -> None:
    """Validate the local wire and its duplicated facts, not archive eligibility."""
    _exact(value, ('schema_version', 'kind', 'identity', 'activity_context', 'predecessor', 'selection',
                   'facts', 'runtime', 'native', 'execution', 'evidence', 'prefix'), 'Round observation')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or value['kind'] != 'training-cycle-round-observation':
        raise ValueError('Unsupported complete round observation')
    identity = value['identity']
    _exact(identity, ('protocol', 'operation_id', 'mode', 'control_home', 'project', 'cycle_id',
                     'input_sha256', 'authorization_sha256', 'ordinal', 'parent'), 'Round observation identity')
    if (identity['protocol'] not in ('ergora-training-cycle-operation-v2', 'ergora-training-cycle-operation-v3') or identity['mode'] not in CYCLE_MEASUREMENT_MODES
            or not isinstance(identity['operation_id'], str) or re.fullmatch('[a-f0-9]{32}', identity['operation_id']) is None
            or type(identity['ordinal']) is not int or not 0 <= identity['ordinal'] < 32):
        raise ValueError('Round observation has no original measurement operation')
    _process(identity['parent'])
    for key in ('input_sha256', 'authorization_sha256'):
        _digest(identity[key])
    validate_cycle_activity_context(value['activity_context'], measurement_action=identity['mode'])
    original = value['activity_context']['workflow_input']
    expected_protocol = {'ergora-training-cycle-operation-v2': 'ergora-training-cycle-v2',
                         'ergora-training-cycle-operation-v3': 'ergora-training-cycle-v3'}[identity['protocol']]
    if original['protocol'] != expected_protocol or any(identity[key] != original[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256', 'authorization_sha256')):
        raise ValueError('Round observation differs from its complete original Workflow input')
    validate_round_predecessor(value['predecessor'], identity['ordinal'])
    selection = value['selection']
    _exact(selection, ('count', 'common_sha256', 'measurement_sources_sha256'), 'Round selection')
    if type(selection['count']) is not int or not identity['ordinal'] < selection['count'] <= 32:
        raise ValueError('Round observation exceeds its original selected count')
    for key in ('common_sha256', 'measurement_sources_sha256'):
        _digest(selection[key])
    validate_round_prefix(value['prefix'])
    home = Path(identity['control_home'])
    expected = home / 'training-cycles' / identity['project'] / identity['cycle_id'] / 'controller/rounds' / str(identity['ordinal'])
    if value['prefix']['directory'] != str(expected) or value['prefix']['rounds'] != identity['ordinal'] + 1:
        raise ValueError('Round observation prefix belongs to another selected position')
    facts = value['facts']
    _exact(facts, ('source_operation_id', 'budget', 'candidate', 'submission', 'execution', 'runtime', 'native', 'request_outcome'), 'Round facts')
    fields = {'budget': ('state', 'work_remaining_seconds', 'total_remaining_seconds', 'control_timeout_seconds',
                         'boot_id', 'boottime_ns', 'observed_at'),
              'candidate': ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision', 'current_project_matches', 'parent_stop_visible'),
              'submission': ('state', 'intent_sha256', 'workflow_id', 'run_id', 'attempt_saved', 'result_saved'),
              'execution': ('state', 'request_sha256', 'record_sha256', 'reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed'),
              'runtime': ('state', 'workflow_id', 'run_id', 'temporal_status', 'terminal', 'phase', 'binding', 'job_id'),
              'native': ('state', 'job_id')}
    for key, keys in fields.items():
        _exact(facts[key], keys, 'Round ' + key + ' facts')
    if (facts['source_operation_id'] != identity['operation_id'] or type(facts['candidate']['ordinal']) is not int or facts['candidate']['ordinal'] != identity['ordinal']
            or type(facts['candidate']['project_revision']) is not int or facts['candidate']['project_revision'] < 1
            or any(facts['candidate'][key] is not None and type(facts['candidate'][key]) is not bool
                   for key in ('current_project_matches', 'parent_stop_visible'))
            or facts['request_outcome'] not in ('not_attempted', 'existing_only')):
        raise ValueError('Round facts differ from their original read-only operation')
    _digest(facts['candidate']['manifest_sha256'])
    budget = facts['budget']
    if (budget['state'] not in ('valid', 'exhausted', 'unknown') or type(budget['boottime_ns']) is not int
            or type(budget['control_timeout_seconds']) is not int or not 1 <= budget['control_timeout_seconds'] <= 60):
        raise ValueError('Round facts have an invalid original clock')
    for key in ('work_remaining_seconds', 'total_remaining_seconds'):
        number = budget[key]
        if number is not None and (type(number) not in (int, float) or not math.isfinite(number)):
            raise ValueError('Round budget requires finite remaining allowances')
    submitted = facts['submission']
    if (submitted['state'] not in ('not_recorded', 'prepared', 'unknown', 'submitted', 'rejected')
            or type(submitted['attempt_saved']) is not bool or type(submitted['result_saved']) is not bool):
        raise ValueError('Round facts have invalid original submission checkpoints')
    if (facts['execution']['state'] not in ('unknown', 'not_requested', 'requested', 'launch_consumed',
            'attempted', 'acknowledged', 'stop_observed', 'stopped')
            or not isinstance(facts['execution']['record_sha256'], dict)
            or set(facts['execution']['record_sha256']) - {'request', 'launch', 'attempt', 'ack', 'stopped'}):
        raise ValueError('Round execution projection has an invalid original record inventory')
    for digest in facts['execution']['record_sha256'].values():
        _digest(digest)
    if (not isinstance(submitted['workflow_id'], str) or not submitted['workflow_id']
            or submitted['run_id'] is not None and (not isinstance(submitted['run_id'], str) or not submitted['run_id'])):
        raise ValueError('Round submission requires its original fixed Workflow and run identity')
    if submitted['intent_sha256'] is not None:
        _digest(submitted['intent_sha256'])
    if facts['runtime']['binding'] is not None:
        _exact(facts['runtime']['binding'], ('experiment_id', 'manifest_sha', 'candidate_sha', 'baseline_sha'), 'Round runtime Binding')
        _digest(facts['runtime']['binding']['manifest_sha'])
    for key in ('reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed'):
        if facts['execution'][key] is not None and type(facts['execution'][key]) is not bool:
            raise ValueError('Round execution facts require typed stop observations')
    for key in ('runtime', 'native', 'execution', 'evidence'):
        if not isinstance(value[key], dict):
            raise ValueError('Round observation requires each complete original reader value')
    runtime, native, execution = (value[key] for key in ('runtime', 'native', 'execution'))
    candidate, evidence = facts['candidate'], value['evidence']
    binding = evidence.get('binding')
    _exact(binding, ('experiment_id', 'manifest_sha', 'candidate_sha', 'baseline_sha'), 'Round evidence Binding')
    _exact(native.get('job'), ('binding', 'job_id'), 'Round native Job')
    if (candidate['experiment_id'] != binding['experiment_id'] or candidate['manifest_sha256'] != binding['manifest_sha']
            or evidence.get('project') != identity['project'] or evidence.get('experiment_id') != candidate['experiment_id']
            or evidence.get('project_revision') != candidate['project_revision'] or native['job']['binding'] != binding):
        raise ValueError('Round candidate differs from its complete original native and evidence binding')
    detail = runtime.get('status', runtime.get('outcome', {}))
    if (facts['runtime'] != {'state': 'queried', **{key: runtime.get(key) for key in
            ('workflow_id', 'run_id', 'temporal_status', 'terminal', 'phase')},
            'binding': detail.get('binding'), 'job_id': detail.get('job_id')}
            or facts['native'] != {'state': native.get('state'), 'job_id': native.get('job', {}).get('job_id')}
            or facts['execution']['record_sha256'] != execution.get('record_sha256')
            or facts['execution']['request_sha256'] != execution.get('record_sha256', {}).get('request')
            or any(facts['execution'][key] != execution.get(key) for key in
                   ('reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed'))):
        raise ValueError('Round facts differ from their complete original reader values')


def read_round_observation(ref: dict, *, home: Path, operation_id: str) -> dict:
    _exact(ref, ('path', 'sha256', 'bytes'), 'Round observation reference')
    expected = home / 'operations/training-cycles' / operation_id / 'helper/observation.json'
    if (not isinstance(operation_id, str) or re.fullmatch('[a-f0-9]{32}', operation_id) is None
            or ref['path'] != str(expected) or type(ref['bytes']) is not int or not 0 < ref['bytes'] <= ARTIFACT_LIMIT):
        raise ValueError('Round observation reference differs from its fixed original path or capacity')
    _digest(ref['sha256'])
    raw = read_raw(expected, ARTIFACT_LIMIT)
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('Round observation differs from its complete original raw reference')
    value = decode(raw)
    validate_round_observation(value)
    if value['identity']['operation_id'] != operation_id or value['identity']['control_home'] != str(home):
        raise ValueError('Round observation identity differs from its original path')
    return value


def _process(value):
    _exact(value, ('pid', 'start_ticks', 'boot_id'), 'Process identity')
    if (type(value['pid']) is not int or value['pid'] < 1
            or not isinstance(value['start_ticks'], str) or re.fullmatch('[0-9]+', value['start_ticks']) is None
            or not isinstance(value['boot_id'], str) or re.fullmatch('[a-f0-9-]{36}', value['boot_id']) is None):
        raise ValueError('Execution process identity is invalid')


def _fd(path):
    # O_NONBLOCK is necessary before fstat: opening a FIFO must not wait for a writer.
    for parent in (path, *path.parents):
        try:
            details = parent.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(details.st_mode) or getattr(details, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Execution records cannot use symlinks or reparse points')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
    descriptor = os.open(path, flags)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError('Execution records require ordinary files')
    return descriptor


def read_raw(path: Path, limit: int = LIMIT) -> bytes:
    with os.fdopen(_fd(path), 'rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Complete execution record exceeds its read capacity')
    return raw


def decode(raw: bytes) -> dict:
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate execution record key: ' + key)
            value[key] = item
        return value

    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('Execution records require finite JSON numbers')
        return value

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=number, parse_float=number)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Execution record is not complete UTF-8 JSON') from error
    if not isinstance(value, dict):
        raise ValueError('Execution record must be a JSON object')
    return value


class PhaseFrames:
    """Read the ordered stopped/result response for one identity-bound helper."""

    def __init__(self, identity: dict, output: Path, result_limit: int):
        self.identity, self.output, self.result_limit = identity, output, result_limit
        self.frames, self.buffer, self.problem = [], bytearray(), None

    def receive(self, raw: bytes) -> None:
        if self.problem is not None:
            return
        self.buffer.extend(raw)
        while b'\n' in self.buffer:
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            event = 'stopped' if not self.frames else 'result'
            limit = 65_536 if event == 'stopped' else self.result_limit
            try:
                if len(self.frames) == 2 or len(line) > limit:
                    raise ValueError('Unexpected or oversized training phase frame')
                frame = decode(line)
                field = 'process' if event == 'stopped' else 'result'
                if (set(frame) != {*self.identity, 'event', field}
                        or any(frame.get(key) != value for key, value in self.identity.items())
                        or frame['event'] != event or not isinstance(frame[field], dict)):
                    raise ValueError('Training phase response differs from its complete original identity or order')
                if event == 'stopped':
                    process = frame[field]
                    if (set(process) != {'status', 'returncode', 'output'}
                            or process['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out')
                            or process['returncode'] is not None and type(process['returncode']) is not int
                            or process['output'] != str(self.output / 'helper')):
                        raise ValueError('Training phase stopped frame has no complete process observation')
                self.frames.append(frame)
            except ValueError as error:
                self.problem = str(error)
                return
        limit = 65_536 if not self.frames else self.result_limit
        if len(self.buffer) > limit:
            self.problem = 'Incomplete training phase frame exceeds its complete response capacity'


CYCLE_ACTIVITY_NAMES = {action: 'ergora.training_cycle.' + action + '.v1'
                        for action in ('inspect', 'start', 'reconcile', 'stop')}
CYCLE_ACTIVITY_NAMES.update({action: 'ergora.training_cycle.' + action + '.v2'
                            for action in ('request-execution-or-observe', 'observe-candidate')})
CYCLE_TASK_QUEUE = 'ergora-training-cycle-v1'
CYCLE_STOP_TASK_QUEUE = 'ergora-training-cycle-stop-v1'


CYCLE_ACTIVITY_NAMES_V3 = {action: 'ergora.training_cycle.' + action + '.v3' for action in (
    'start', 'reconcile', 'request-execution-or-observe', 'observe-candidate',
    'collect-round', 'reconcile-round', 'stop')}
CYCLE_TASK_QUEUE_V2 = 'ergora-training-cycle-v2'
CYCLE_STOP_TASK_QUEUE_V2 = 'ergora-training-cycle-stop-v2'
CYCLE_ACTIVITY_NAMES_V4 = {action: 'ergora.training_cycle.' + action + '.v4' for action in CYCLE_ACTIVITY_NAMES_V3}
CYCLE_TASK_QUEUE_V3 = 'ergora-training-cycle-v3'
CYCLE_STOP_TASK_QUEUE_V3 = 'ergora-training-cycle-stop-v3'


def cycle_activity_names(program_version: int = 1) -> dict:
    if type(program_version) is not int or program_version not in (1, 2, 3):
        raise ValueError('Unsupported training cycle program version')
    return {1: CYCLE_ACTIVITY_NAMES, 2: CYCLE_ACTIVITY_NAMES_V3, 3: CYCLE_ACTIVITY_NAMES_V4}[program_version]


def validate_cycle_activity_request(value: dict, action: str) -> None:
    workflow_input = value.get('workflow_input') if isinstance(value, dict) else None
    _exact(workflow_input, ('protocol', 'control_home', 'project', 'cycle_id',
                           'input_sha256', 'authorization_sha256'), 'Cycle workflow input')
    version2 = workflow_input['protocol'] in ('ergora-training-cycle-v2', 'ergora-training-cycle-v3')
    names = cycle_activity_names(3 if workflow_input['protocol'] == 'ergora-training-cycle-v3' else 2 if version2 else 1)
    if workflow_input['protocol'] not in ('ergora-training-cycle-v1', 'ergora-training-cycle-v2', 'ergora-training-cycle-v3') or action not in names:
        raise ValueError('Unsupported cycle workflow protocol or action')
    ordinary = action != 'stop' and action != 'inspect'
    fields = ('workflow_input', *(('ordinal', 'predecessor') if version2 and ordinary else
        ('ordinal',) if ordinary else ('reason',) if action == 'stop' else ()))
    _exact(value, fields, 'Cycle activity request')
    home = workflow_input['control_home']
    if not isinstance(home, str) or not Path(home).is_absolute() or '..' in Path(home).parts:
        raise ValueError('Cycle activity requires the original absolute control directory')
    for name, maximum in (('project', 63), ('cycle_id', 79)):
        if not isinstance(workflow_input[name], str) or re.fullmatch(
                '[A-Za-z0-9][A-Za-z0-9_-]{0,' + str(maximum) + '}', workflow_input[name]) is None:
            raise ValueError('Cycle activity requires its original portable identity')
    for name in ('input_sha256', 'authorization_sha256'):
        _digest(workflow_input[name])
    if ordinary and (type(value['ordinal']) is not int or not 0 <= value['ordinal'] < 32):
        raise ValueError('Cycle activity requires its original ordinal')
    if not version2 and action in ('request-execution-or-observe', 'observe-candidate') and value['ordinal'] != 0:
        raise ValueError('successor_not_enabled')
    if version2 and ordinary:
        validate_round_predecessor(value['predecessor'], value['ordinal'])
    if action == 'stop' and (not isinstance(value['reason'], str) or not value['reason'].strip()):
        raise ValueError('Cycle stop requires a nonempty reason')


def validate_cycle_activity_context(value: dict, *, measurement_action: str | None = None) -> None:
    _exact(value, ('workflow_input', 'activity_source', 'service_namespace'), 'Cycle activity context')
    original = value['workflow_input']
    _exact(original, ('protocol', 'control_home', 'project', 'cycle_id',
                      'input_sha256', 'authorization_sha256'), 'Cycle workflow input')
    version2 = original['protocol'] in ('ergora-training-cycle-v2', 'ergora-training-cycle-v3')
    source = value['activity_source']
    _exact(source, ('workflow_id', 'workflow_run_id', 'workflow_type', 'workflow_namespace',
                    'namespace', 'activity_id', 'activity_type', 'task_queue', 'attempt'), 'SDK activity source')
    if any(not isinstance(source[name], str) or not source[name].strip() for name in source if name != 'attempt'):
        raise ValueError('SDK activity requires complete Workflow source information')
    names = cycle_activity_names(3 if original['protocol'] == 'ergora-training-cycle-v3' else 2 if version2 else 1)
    action = next((key for key, name in names.items() if name == source['activity_type']), None)
    retried_collect = (measurement_action == 'reconcile-round' and action == 'collect-round'
                       and type(source['attempt']) is int and source['attempt'] > 1)
    if action is None or measurement_action is not None and action != measurement_action and not retried_collect:
        raise ValueError('SDK activity differs from its registered action')
    request = {'workflow_input': original}
    if action == 'stop':
        request['reason'] = 'validate-source'
    elif action != 'inspect':
        request['ordinal'] = 0
        if version2:
            request['predecessor'] = None
    validate_cycle_activity_request(request, action)
    queue = ((CYCLE_STOP_TASK_QUEUE_V3 if action == 'stop' else CYCLE_TASK_QUEUE_V3)
             if original['protocol'] == 'ergora-training-cycle-v3' else (CYCLE_STOP_TASK_QUEUE_V2 if action == 'stop' else CYCLE_TASK_QUEUE_V2) if version2 else
             (CYCLE_STOP_TASK_QUEUE if action == 'stop' else CYCLE_TASK_QUEUE))
    if (source['workflow_type'] != cycle_workflow_type(original['protocol']) or source['task_queue'] != queue
            or not isinstance(value['service_namespace'], str) or not value['service_namespace']
            or source['namespace'] != value['service_namespace']
            or source['workflow_namespace'] != value['service_namespace']
            or type(source['attempt']) is not int or source['attempt'] < 1):
        raise ValueError('SDK activity type, queue, namespace or attempt differs')


def validate_cycle_operation(payload: dict) -> None:
    """Bind a bounded operation request without loading application state or SDKs."""
    if not isinstance(payload, dict) or not isinstance(payload.get('identity'), dict):
        raise ValueError('Cycle operation requires its complete identity')
    measurement = payload['identity'].get('mode') in CYCLE_MEASUREMENT_MODES
    version2 = payload['identity'].get('protocol') in ('ergora-training-cycle-operation-v2', 'ergora-training-cycle-operation-v3')
    declared = payload['identity'].get('protocol') == 'ergora-training-cycle-operation-v3'
    input_protocol = 'ergora-training-cycle-v3' if declared else 'ergora-training-cycle-v2' if version2 else 'ergora-training-cycle-v1'
    candidate = payload['identity'].get('mode') in (*CYCLE_CANDIDATE_MODES, *CYCLE_MEASUREMENT_MODES)
    _exact(payload, ('identity', 'snapshot', 'bootstrap', 'reason', *(('start_context',) if candidate else ()),
                     *(('activity_context',) if 'activity_context' in payload else ())),
           'Cycle operation')
    identity = payload['identity']
    if 'activity_context' in payload:
        validate_cycle_activity_context(payload['activity_context'],
            measurement_action=payload['identity']['mode'] if measurement else None)
        original = payload['activity_context']['workflow_input']
        if original['protocol'] != input_protocol:
            raise ValueError('Cycle operation protocol differs from its SDK activity source')
        if any(identity.get(key) != original[key] for key in
               ('control_home', 'project', 'cycle_id', 'authorization_sha256', *(('input_sha256',) if version2 and payload['snapshot'] is not None else ()))):
            raise ValueError('Cycle operation differs from its SDK activity identity')
    if 'activity_context' in payload:
        source = payload['activity_context']['activity_source']
        mode = identity.get('mode')
        names = cycle_activity_names(3 if declared else 2 if version2 else 1)
        stop_modes = ('stop-writer', 'notify-owner', 'drain', 'observe-execution')
        if (mode in stop_modes and source['activity_type'] != names['stop']
                or mode in CYCLE_START_MODES and source['activity_type'] != names['start']
                or mode == 'reconcile-candidate' and source['activity_type'] not in
                    (names['start'], names['reconcile'])
                or mode == 'request-execution-candidate' and source['activity_type'] !=
                    names['request-execution-or-observe']
                or mode == 'observe-candidate' and source['activity_type'] not in
                    (names['request-execution-or-observe'], names['observe-candidate'],
                     *((names['start'], names['reconcile']) if version2 else ()))
                or mode == 'collect-round' and source['activity_type'] != names['collect-round']
                or mode == 'reconcile-round' and source['activity_type'] not in (
                    names['collect-round'], names['reconcile-round'])
                or mode == 'reconcile-round' and source['activity_type'] == names['collect-round']
                    and source['attempt'] == 1
                or mode in ('inspect', 'prepare-controller', 'submit-controller', 'reconcile-controller')):
            raise ValueError('Cycle operation mode differs from its SDK activity action')
    if identity.get('mode') == 'inspect-controller-activity' and 'activity_context' not in payload:
        raise ValueError('SDK cold inspection requires its actual activity context')
    if identity.get('mode') in (*CYCLE_EXECUTION_MODES, *CYCLE_MEASUREMENT_MODES) and 'activity_context' not in payload:
        raise ValueError('Candidate execution observation requires its actual SDK activity context')
    _exact(identity, ('protocol', 'operation_id', 'mode', 'control_home', 'project', 'cycle_id',
        'input_sha256', 'authorization_sha256', 'ordinal', 'parent'), 'Cycle operation identity')
    if (identity['protocol'] not in ('ergora-training-cycle-operation-v1', 'ergora-training-cycle-operation-v2', 'ergora-training-cycle-operation-v3')
            or measurement and not version2
            or not isinstance(identity['operation_id'], str)
            or re.fullmatch('[a-f0-9]{32}', identity['operation_id']) is None
            or identity['mode'] not in ('inspect', 'inspect-controller-activity', 'prepare-controller', 'submit-controller', 'reconcile-controller',
                'stop-writer', 'notify-owner', 'drain', 'observe-execution', *CYCLE_CANDIDATE_MODES, *CYCLE_MEASUREMENT_MODES)):
        raise ValueError('Unsupported cycle operation or observation identity')
    for name, maximum in (('project', 63), ('cycle_id', 79)):
        if not isinstance(identity[name], str) or re.fullmatch(
                '[A-Za-z0-9][A-Za-z0-9_-]{0,' + str(maximum) + '}', identity[name]) is None:
            raise ValueError('Cycle operation requires portable original project and cycle IDs')
    home = identity['control_home']
    if not isinstance(home, str) or not Path(home).is_absolute() or '..' in Path(home).parts:
        raise ValueError('Cycle operation requires its complete absolute control directory')
    _digest(identity['authorization_sha256'])
    _process(identity['parent'])
    ordinal = identity['ordinal']
    if identity['mode'] in ('notify-owner', 'observe-execution', *CYCLE_CANDIDATE_MODES, *CYCLE_MEASUREMENT_MODES):
        if type(ordinal) is not int or not 0 <= ordinal < 32:
            raise ValueError('Cycle target requires its original selected ordinal')
        if not version2 and identity['mode'] in CYCLE_EXECUTION_MODES and ordinal != 0:
            raise ValueError('successor_not_enabled')
    elif ordinal is not None:
        raise ValueError('This cycle operation has no selected ordinal')
    if payload['reason'] is not None and (not isinstance(payload['reason'], str) or not payload['reason'].strip()):
        raise ValueError('Cycle stop requires a nonempty reason')
    if identity['mode'] == 'stop-writer' and payload['reason'] is None:
        raise ValueError('Cycle stop writer requires its explicit reason')
    if identity['mode'] in ('inspect', 'inspect-controller-activity'):
        if identity['input_sha256'] is not None or payload['snapshot'] is not None:
            raise ValueError('Cold cycle inspection cannot assume an unverified input or snapshot')
        bootstrap = payload['bootstrap']
        _exact(bootstrap, ('boot_id', 'started_ns', 'deadline_ns'), 'Cycle observation deadline')
        if (bootstrap['boot_id'] != identity['parent']['boot_id']
                or type(bootstrap['started_ns']) is not int or bootstrap['started_ns'] < 0
                or type(bootstrap['deadline_ns']) is not int
                or bootstrap['deadline_ns'] - bootstrap['started_ns'] < 1_000_000_000
                or not declared and bootstrap['deadline_ns'] - bootstrap['started_ns'] > 60_000_000_000):
            raise ValueError('Cold inspection requires its original boot origin and deadline' if declared
                else 'Cold inspection requires one fixed 1 to 60 second observation deadline')
        if declared:
            boot, ticks = budget_clock._clock()
            if (boot != bootstrap['boot_id'] or ticks < bootstrap['started_ns']
                    or bootstrap['deadline_ns'] > ticks + 10_000_000_000):
                raise ValueError('Readonly inspection exceeds ten remaining seconds or lost its original boot origin')
        return
    _digest(identity['input_sha256'])
    if not declared and identity['mode'] not in (*CYCLE_WORK_MODES, *CYCLE_OBSERVATION_MODES) and payload['bootstrap'] is not None:
        raise ValueError('Verified cycle operations must use the original total allowance')
    snapshot = payload['snapshot']
    _exact(snapshot, ('authorization', 'policy', 'candidates'), 'Original cycle snapshot')
    authorization, policy = snapshot['authorization'], snapshot['policy']
    if (not isinstance(authorization, dict) or type(authorization.get('schema_version')) is not int
            or authorization['schema_version'] != (4 if declared else 3 if version2 else 2)
            or authorization.get('sha256') != identity['authorization_sha256']
            or CycleAdmission._sha({k: v for k, v in authorization.items() if k != 'sha256'}) != authorization['sha256']
            or any(authorization.get(key) != identity[key] for key in
                ('control_home', 'project', 'cycle_id', 'input_sha256'))):
        raise ValueError('Cycle operation differs from the complete original authorization')
    _exact(policy, ('wall_seconds', 'cleanup_seconds', 'control_timeout_seconds'), 'Original cycle policy')
    if (type(policy['wall_seconds']) is not int or type(policy['cleanup_seconds']) is not int
            or not 1 <= policy['cleanup_seconds'] < policy['wall_seconds']
            or type(policy['control_timeout_seconds']) is not int or not 1 <= policy['control_timeout_seconds'] <= 60):
        raise ValueError('Cycle operation has an invalid original budget policy')
    _exact(authorization.get('clock'), budget_clock.FIELDS, 'Original cycle clock')
    budget_clock.validate(authorization['clock'], policy['wall_seconds'])
    if identity['mode'] in CYCLE_WORK_MODES:
        window = payload['bootstrap']
        _exact(window, ('boot_id', 'started_ns', 'deadline_ns'), 'Original cycle operation window')
        if (window['boot_id'] != identity['parent']['boot_id'] or window['boot_id'] != authorization['clock']['boot_id']
                or type(window['started_ns']) is not int or window['started_ns'] < authorization['clock']['boottime_ns']
                or type(window['deadline_ns']) is not int
                or window['deadline_ns'] - window['started_ns'] > policy['control_timeout_seconds'] * 1_000_000_000
                or window['deadline_ns'] > authorization['clock']['boottime_ns']
                    + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000):
            raise ValueError('Ordinary cycle window exceeds its original compute or control allowance')
    if identity['mode'] in ('reconcile-controller', 'reconcile-candidate'):
        window = payload['bootstrap']
        _exact(window, ('boot_id', 'started_ns', 'deadline_ns'), 'Cycle reconciliation deadline')
        if (window['boot_id'] != identity['parent']['boot_id']
                or type(window['started_ns']) is not int or window['started_ns'] < 0
                or type(window['deadline_ns']) is not int
                or not 1_000_000_000 <= window['deadline_ns'] - window['started_ns'] <= 60_000_000_000):
            raise ValueError('Reconciliation requires one fixed 1 to 60 second observation deadline')
    if declared and identity['mode'] not in (*CYCLE_WORK_MODES, *CYCLE_OBSERVATION_MODES):
        window = payload['bootstrap']
        _exact(window, ('boot_id', 'started_ns', 'deadline_ns'), 'Original SDK stop window')
        if (window['boot_id'] != identity['parent']['boot_id'] or window['boot_id'] != authorization['clock']['boot_id']
                or type(window['started_ns']) is not int or window['started_ns'] < authorization['clock']['boottime_ns']
                or type(window['deadline_ns']) is not int
                or window['deadline_ns'] > authorization['clock']['boottime_ns'] + policy['wall_seconds'] * 1_000_000_000):
            raise ValueError('Cycle stop exceeds its original total or lost its original SDK window')
    candidates = snapshot['candidates']
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 32 or ordinal is not None and ordinal >= len(candidates):
        raise ValueError('Cycle operation has no complete ordered candidate index')
    if candidate:
        context = payload['start_context']
        fields = {'prepare-candidate': ('controller',), 'reconcile-candidate': ('controller',),
            'request-execution-candidate': ('controller',), 'observe-candidate': ('controller',),
            'collect-round': ('controller',), 'reconcile-round': ('controller',),
            'confirm-candidate': ('controller', 'origin_operation_id', 'intent_sha256', 'root_process'),
            'dispatch-candidate': ('controller', 'origin_operation_id', 'intent_sha256', 'owner')}
        _exact(context, fields[identity['mode']], 'Original candidate start context')
        validate_budget_binding({'cycle_id': identity['cycle_id'],
            'authorization_sha256': identity['authorization_sha256'], 'task_queue': BUDGET_TASK_QUEUE,
            'controller': context['controller']})
        if (context['controller']['ordinal'] != ordinal
                or context['controller']['protocol'] != input_protocol):
            raise ValueError('Candidate start differs from its original controller ordinal')
        if identity['mode'] in ('confirm-candidate', 'dispatch-candidate'):
            if (not isinstance(context['origin_operation_id'], str)
                    or re.fullmatch('[a-f0-9]{32}', context['origin_operation_id']) is None):
                raise ValueError('Candidate start requires its original prepare operation')
            _digest(context['intent_sha256'])
            if identity['mode'] == 'confirm-candidate':
                _process(context['root_process'])
            else:
                owner_record(context['owner'])


def cycle_operation_remaining(payload: dict) -> float:
    """Consume one fixed window, original compute or original stop total, never renew."""
    mode = payload['identity']['mode']
    bounded_stop = payload['identity']['protocol'] == 'ergora-training-cycle-operation-v3'
    window = float('inf')
    if mode in (*CYCLE_OBSERVATION_MODES, *CYCLE_WORK_MODES) or bounded_stop:
        bootstrap = payload['bootstrap']
        boot, ticks = budget_clock._clock()
        if boot != bootstrap['boot_id'] or ticks < bootstrap['started_ns']:
            raise ValueError('Cycle operation lost its original boot clock')
        window = (bootstrap['deadline_ns'] - ticks) / 1_000_000_000
        if mode in CYCLE_OBSERVATION_MODES:
            return window
    snapshot = payload['snapshot']
    if mode in CYCLE_WORK_MODES:
        return min(window, budget_clock.remaining(snapshot['authorization']['clock'],
            snapshot['policy']['wall_seconds'], snapshot['policy']['cleanup_seconds']))
    return min(window, budget_clock.remaining(snapshot['authorization']['clock'], snapshot['policy']['wall_seconds']))


def cycle_start_source(payload: dict) -> dict:
    """Read the original prepare request; later phases cannot replace its window."""
    validate_cycle_operation(payload)
    identity = payload['identity']
    if identity['mode'] not in CYCLE_START_MODES:
        raise ValueError('Candidate observation does not grant a start window')
    context = payload['start_context']
    origin = identity['operation_id'] if identity['mode'] == 'prepare-candidate' else context['origin_operation_id']
    source = decode(read_raw(Path(identity['control_home']) / 'operations/training-cycles' / origin / 'request.json', 32_768))
    validate_cycle_operation(source)
    if source['identity']['mode'] != 'prepare-candidate' or source['identity']['operation_id'] != origin:
        raise ValueError('Candidate start has no matching original prepare request')
    _match({key: value for key, value in identity.items() if key not in ('mode', 'operation_id')},
           {key: value for key, value in source['identity'].items() if key not in ('mode', 'operation_id')},
           'Original candidate operation identity')
    if payload.get('activity_context') != source.get('activity_context'):
        raise ValueError('Original candidate activity context differs from its prepare source')
    for name in ('snapshot', 'bootstrap'):
        _match(payload[name], source[name], 'Original candidate ' + name)
    _match(context['controller'], source['start_context']['controller'], 'Original candidate controller')
    return source


def cycle_execution_source(payload: dict, intent: dict) -> None:
    """Bind Execution's last request gate to this H's immutable SDK operation."""
    validate_cycle_operation(payload)
    identity = payload['identity']
    if (identity['mode'] != 'request-execution-candidate'
            or payload['activity_context']['activity_source']['attempt'] != 1):
        raise ValueError('Only the first authenticated execution request activity may publish a request')
    source = decode(read_raw(Path(identity['control_home']) / 'operations/training-cycles'
                             / identity['operation_id'] / 'request.json', 32_768))
    _match(payload, source, 'Complete execution operation source')
    binding = intent['budget']
    if (any(identity[key] != value for key, value in {
            'control_home': intent['control_home'], 'project': intent['project'],
            'cycle_id': binding['cycle_id'], 'authorization_sha256': binding['authorization_sha256']}.items())
            or payload['start_context']['controller'] != binding.get('controller')
            or any(payload['activity_context']['activity_source'][key] != binding['controller'][target]
                   for key, target in (('workflow_id', 'workflow_id'), ('workflow_run_id', 'run_id')))
            or payload['snapshot']['candidates'][identity['ordinal']]['experiment_id'] != intent['experiment_id']
            or payload['activity_context']['workflow_input']['input_sha256'] != identity['input_sha256']
            or processes.identity(identity['parent']['pid']) != identity['parent']):
        raise ValueError('Execution request lost its original controller, candidate or live parent source')


def validate_cycle_root_request(value: dict) -> None:
    """Check the bounded root envelope without reading business files in its caller."""
    _exact(value, ('protocol', 'origin_operation_id', 'parent', 'window', 'submission'), 'Controller root request')
    if (value['protocol'] != 'ergora-training-cycle-root-v1'
            or not isinstance(value['origin_operation_id'], str)
            or re.fullmatch('[a-f0-9]{32}', value['origin_operation_id']) is None):
        raise ValueError('Controller root requires its one original prepare identity')
    _process(value['parent'])
    _exact(value['window'], ('boot_id', 'started_ns', 'deadline_ns'), 'Original root window')
    submission = value['submission']
    _exact(submission, ('project', 'control_home', 'experiment_id', 'timeout', 'intent_sha256', 'mode'),
           'Controller root submission')
    if (submission['mode'] != 'controller-owner' or not isinstance(submission['project'], dict)
            or type(submission['timeout']) is not int or not 1 <= submission['timeout'] <= 60):
        raise ValueError('Controller root requires its complete original submission')
    _digest(submission['intent_sha256'])


def _capability(capability: dict) -> None:
    """Check saved identity only; history never requires the current installation."""
    _exact(capability, ('protocol', 'admission_protocol', 'descriptor_sha256', 'installation',
        'native_python', 'cycle_ready_sha256', 'gate_sources'), 'Execution capability')
    try:
        sources = GATE_SOURCE_PROTOCOLS[capability['admission_protocol']]
    except (KeyError, TypeError) as error:
        raise ValueError('Unsupported complete execution capability') from error
    if (capability['protocol'] != PROTOCOL or not isinstance(capability['gate_sources'], dict)
            or set(capability['gate_sources']) != set(sources)):
        raise ValueError('Unsupported complete execution capability')
    for digest in (*capability['gate_sources'].values(), capability['descriptor_sha256'], capability['cycle_ready_sha256']):
        _digest(digest)
    installation = Path(capability['installation'])
    if not installation.is_absolute() or capability['native_python'] != str(installation / '.venv/bin/python'):
        raise ValueError('Execution capability has no exact native interpreter')


def owner_record(value: dict) -> dict:
    common = ('schema_version', 'intent_sha256', 'authorization_sha256', 'pid', 'start_ticks', 'boot_id', 'context_sha256')
    version = value.get('schema_version')
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported original budget owner schema')
    _exact(value, (*common, 'execution_capability') if version == 2 else common, 'Budget owner')
    for name in ('intent_sha256', 'authorization_sha256', 'context_sha256'):
        _digest(value[name])
    _process({key: value[key] for key in ('pid', 'start_ticks', 'boot_id')})
    if version == 2 and value['execution_capability'] is not None:
        _capability(value['execution_capability'])
    return value


def owner_active(path: Path, expected: dict) -> bool:
    """Observe the same live owner and both existing locks; never create one."""
    import fcntl

    try:
        value = owner_record(decode(read_raw(path)))
        _match(value, expected, 'Original live owner')
        _match(processes.identity(value['pid']), {key: value[key] for key in ('pid', 'start_ticks', 'boot_id')}, 'Live process')
        with os.fdopen(_fd(path.parent / 'lock'), 'rb') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                with os.fdopen(_fd(path.parent / 'initializing.lock'), 'rb') as ready:
                    try:
                        fcntl.flock(ready, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    except BlockingIOError:
                        return False
                return True
    except (OSError, ValueError):
        return False
    return False


def source_capability(installation: Path, ready: dict) -> dict | None:
    from dev_platform.contracts import canonical_sha

    reference.validate_installation(installation, training=True)
    descriptor = installation / 'ergora-native-runtime.json'
    if not descriptor.exists():
        reference.validate_installation(installation, training=True)
        return None
    raw = read_raw(descriptor, 65_536)
    declared = reference._training_descriptor(raw)
    # Bind this exact declaration around a complete installation check. A switch
    # between two supported declarations cannot silently change the birth pin.
    reference.validate_installation(installation, training=True)
    if read_raw(descriptor, 65_536) != raw:
        raise ValueError('Native execution descriptor changed during capability birth')
    return {'protocol': PROTOCOL, 'admission_protocol': declared['protocol_id'],
        'descriptor_sha256': hashlib.sha256(raw).hexdigest(),
        'installation': str(installation), 'native_python': str(installation / '.venv/bin/python'),
        'cycle_ready_sha256': canonical_sha(ready), 'gate_sources': {
            name: hashlib.sha256(read_raw(Path(__file__).parent / name)).hexdigest()
            for name in GATE_SOURCE_PROTOCOLS[declared['protocol_id']]}}


def validate_sources(capability: dict) -> None:
    _capability(capability)
    for name, expected in capability['gate_sources'].items():
        if hashlib.sha256(read_raw(Path(__file__).parent / name)).hexdigest() != expected:
            raise ValueError('Original execution gate source changed: ' + name)
    reference.verify()
    installation = reference.validate_installation(Path(capability['installation']), training=True)
    raw = read_raw(installation / 'ergora-native-runtime.json', 65_536)
    declared = reference._training_descriptor(raw)
    if (declared['protocol_id'] != capability['admission_protocol']
            or hashlib.sha256(raw).hexdigest() != capability['descriptor_sha256']):
        raise ValueError('Original native execution descriptor changed')
    for name, expected in capability['gate_sources'].items():
        if hashlib.sha256(read_raw(Path(__file__).parent / name)).hexdigest() != expected:
            raise ValueError('Original execution gate source changed: ' + name)
    if not Path(capability['native_python']).is_file():
        raise ValueError('Original native interpreter is unavailable')


def publish(path: Path, value: dict, root: Path) -> None:
    """Synchronize an immutable publication; equal retry never grants a launch."""
    from dev_platform import adapter

    adapter.safe_file(root, path.relative_to(root).as_posix())
    # Check existing bytes with the nonblocking reader before native equal retry.
    try:
        _match(decode(read_raw(path)), value, 'Existing execution record')
    except FileNotFoundError:
        pass
    adapter.publish(path, value)
    sync_directories(path.parent, root)


def sync_directories(directory: Path, root: Path) -> None:
    for selected in (directory, *directory.parents):
        descriptor = os.open(selected, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if selected == root:
            return
    raise ValueError('Execution publication escaped its registered root')


class CycleAdmission:
    """A parent's irreversible veto, not a grant to start or execute training.

    Callers validate their complete source and clock before using this permit.
    All storage operations may block; live owners must supervise their caller.
    """

    def __init__(self, directory: Path, authorization: dict):
        if type(authorization['schema_version']) is not int or authorization['schema_version'] not in (2, 3, 4):
            raise ValueError('Controller admission requires explicit birth-time consent')
        self.directory, self.authorization = directory, authorization
        self.folder = directory / 'controller'
        self.lock = self.folder / 'admission.lock'
        self.stop = self.folder / 'stop.json'
        self.identity = {'schema_version': 1, 'kind': 'training-cycle-stop',
            'protocol': authorization['controller']['protocol'], 'control_home': authorization['control_home'],
            'project': authorization['project'], 'cycle_id': authorization['cycle_id'],
            'input_sha256': authorization['input_sha256'], 'authorization_sha256': authorization['sha256'],
            'actor_id': authorization['controller']['actor_id']}

    @staticmethod
    def _sha(value):
        # This boundary also runs in the dependency-isolated native interpreter.
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()

    def _authorization(self):
        saved = decode(read_raw(self.directory / 'authorization.json'))
        if self._sha(saved) != self._sha(self.authorization):
            raise ValueError('Original controller authorization changed')

    @contextmanager
    def _locked(self, *, shared):
        import fcntl

        with os.fdopen(_fd(self.lock), 'rb') as lock:
            if lock.read(1):
                raise ValueError('Controller admission requires its ordinary empty original lock')
            fcntl.flock(lock, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
            yield

    def validate_lock(self, *, synchronize=False):
        with os.fdopen(_fd(self.lock), 'rb') as lock:
            if lock.read(1):
                raise ValueError('Controller admission requires its ordinary empty original lock')
            if synchronize:
                os.fsync(lock.fileno())
                sync_directories(self.folder, self.directory)

    def check(self):
        """Recheck under an existing permit immediately before the original action."""
        self._authorization()
        try:
            self.stop.lstat()
        except FileNotFoundError:
            return
        raise ValueError('Controller stop is visible; no new training action is admitted')

    @contextmanager
    def permission(self):
        """Try one shared permit without waiting, creating files or extending time."""
        with self._locked(shared=True):
            self.check()
            yield self

    def intent_record(self):
        """Generate the same complete parent identity for producer and consumers."""
        authorization, controller = self.authorization, self.authorization['controller']
        workflow_input = {name: authorization[name] for name in
            ('control_home', 'project', 'cycle_id', 'input_sha256')}
        workflow_input.update(protocol=controller['protocol'], authorization_sha256=authorization['sha256'])
        return {**workflow_input, 'schema_version': 1, 'kind': 'training-cycle-controller-intent',
            'project_revision': authorization['project_revision'], 'workflow_id': controller['workflow_id'],
            'task_queue': controller['task_queue'], 'workflow_input': workflow_input}

    def controller_intent(self):
        try:
            intent = decode(read_raw(self.folder / 'intent.json'))
        except FileNotFoundError:
            return None
        if self._sha(intent) != self._sha(self.intent_record()):
            raise ValueError('Controller intent differs from its complete original authorization')
        return intent

    def _intent_sha(self):
        intent = self.controller_intent()
        return self._sha(intent) if intent is not None else None

    def attempt_record(self, intent):
        return {'schema_version': 1, 'intent_sha256': self._sha(intent),
            'workflow_id': intent['workflow_id'], 'workflow_input_sha256': self._sha(intent['workflow_input'])}

    def receipt_record(self, intent, run_id):
        if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
            raise ValueError('Controller receipt requires the exact nonempty original run ID')
        return {**self.attempt_record(intent), 'run_id': run_id}

    def rejection_record(self, intent, reason, run_id):
        if reason not in ('preexisting_run', 'lookup_rejected', 'start_conflict'):
            raise ValueError('Unsupported controller ownership rejection')
        if reason == 'preexisting_run' or run_id is not None:
            value = self.receipt_record(intent, run_id)
        else:
            value = {**self.attempt_record(intent), 'run_id': None}
        if reason == 'lookup_rejected' and run_id is not None:
            raise ValueError('Rejected controller lookup has no authenticated run ID')
        return {**value, 'reason': reason}

    def submission(self):
        """Read immutable delivery facts; neither a runtime query nor execution authority."""
        records = {}
        # A concurrent publisher adds completion only after its attempt and intent.
        for name in ('receipt', 'rejection', 'attempt'):
            try:
                records[name] = decode(read_raw(self.folder / (name + '.json')))
            except FileNotFoundError:
                records[name] = None
        intent = self.controller_intent()
        attempt, receipt, rejection = (records[name] for name in ('attempt', 'receipt', 'rejection'))
        if intent is None and any(value is not None for value in records.values()):
            raise ValueError('Controller delivery facts have no original complete intent')
        if attempt is not None and self._sha(attempt) != self._sha(self.attempt_record(intent)):
            raise ValueError('Controller binding differs from its original complete attempt')
        if receipt is not None and (attempt is None
                or self._sha(receipt) != self._sha(self.receipt_record(intent, receipt.get('run_id')))):
            raise ValueError('Controller binding differs from its original fixed-run receipt')
        if rejection is not None:
            reason = rejection.get('reason')
            if (receipt is not None or (attempt is not None) != (reason == 'start_conflict')
                    or self._sha(rejection) != self._sha(self.rejection_record(intent, reason, rejection.get('run_id')))):
                raise ValueError('Controller ownership rejection conflicts with its original checkpoint')
        return {'status': 'not_prepared' if intent is None else 'rejected' if rejection is not None else
                'submitted' if receipt is not None else 'unknown' if attempt is not None else 'prepared',
            'workflow_id': self.authorization['controller']['workflow_id'], 'intent': intent,
            'intent_sha256': self._sha(intent) if intent is not None else None,
            'run_id': receipt['run_id'] if receipt is not None else None,
            'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
            'reason': rejection['reason'] if rejection is not None else None,
            'conflicting_run_id': rejection['run_id'] if rejection is not None else None}

    def _bound_selection(self, binding, plan):
        """Bind a real controller selection before or after its child is born."""
        validate_budget_binding(binding)
        if 'controller' not in binding:
            raise ValueError('Controller authorization requires complete controller binding and final admission gates')
        controller = binding['controller']
        saved = self.submission()
        parent = saved['intent']
        if parent is None:
            raise ValueError('Controller binding has no original complete intent')
        expected = self.attempt_record(parent)
        if not saved['attempt_saved']:
            raise ValueError('Controller binding differs from its original complete attempt')
        if not saved['result_saved'] or saved['run_id'] != controller['run_id']:
            raise ValueError('Controller binding differs from its original fixed-run receipt')
        authorization = self.authorization
        if (binding['cycle_id'] != authorization['cycle_id']
                or binding['authorization_sha256'] != authorization['sha256']
                or controller['protocol'] != {2: 'ergora-training-cycle-v1', 3: 'ergora-training-cycle-v2', 4: 'ergora-training-cycle-v3'}[authorization['schema_version']]
                or controller['protocol'] != parent['protocol']
                or controller['workflow_id'] != parent['workflow_id']
                or controller['intent_sha256'] != expected['intent_sha256']
                or controller['ordinal'] >= len(plan['admissions'])):
            raise ValueError('Controller binding differs from its original authorization or selected position')
        selected = plan['admissions'][controller['ordinal']]
        return parent, selected

    def bind(self, intent, plan):
        """Bind one original selected start to its complete parent receipt."""
        parent, selected = self._bound_selection(intent['budget'], plan)
        if (selected['experiment_id'] != intent['experiment_id']
                or self._sha(selected['observation']) != self._sha(intent['observation'])):
            raise ValueError('Controller binding differs from its complete original selected admission')
        return parent

    def _stop_record(self, value):
        _exact(value, (*self.identity, 'controller_intent_sha256', 'reason', 'requested_at'), 'Controller stop')
        if value['controller_intent_sha256'] is not None:
            _digest(value['controller_intent_sha256'])
        if value['controller_intent_sha256'] != self._intent_sha():
            raise ValueError('Controller stop differs from its original controller intent')
        if not isinstance(value['reason'], str) or not value['reason'].strip():
            raise ValueError('Controller stop requires a nonempty reason')
        try:
            requested = datetime.fromisoformat(value['requested_at'])
            if requested.utcoffset() != timedelta(0) or requested.isoformat() != value['requested_at']:
                raise ValueError('Controller stop requires its complete UTC time')
        except TypeError as error:
            raise ValueError('Controller stop requires its complete UTC time') from error
        expected = {**value, **self.identity}
        if self._sha(expected) != self._sha(value):
            raise ValueError('Controller stop differs from its original authorization')
        return value

    def observe(self, *, synchronize=False, drain=False):
        """Keep visibility, durable bytes, parent permits and subtree stop separate."""
        observed = {'stop_visible': None, 'identity_matches': None, 'record': None, 'record_sha256': None,
            'stop_durable': None, 'admission_drained': None, 'executor_stop_confirmed': None, 'reason': None}
        try:
            self.stop.lstat()
        except FileNotFoundError:
            return {**observed, 'stop_visible': False}
        except OSError as error:
            return {**observed, 'reason': str(error)}
        observed['stop_visible'] = True
        try:
            self._authorization()
            with os.fdopen(_fd(self.stop), 'rb') as stream:
                raw = stream.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise ValueError('Complete controller stop exceeds its read capacity')
                value = self._stop_record(decode(raw))
                observed.update(identity_matches=True, record=value, record_sha256=hashlib.sha256(raw).hexdigest())
                if synchronize or drain:
                    os.fsync(stream.fileno())
                    sync_directories(self.folder, self.directory)
                    observed['identity_matches'] = False
                    self._authorization()
                    with os.fdopen(_fd(self.stop), 'rb') as again:
                        original, current = os.fstat(stream.fileno()), os.fstat(again.fileno())
                        if ((original.st_dev, original.st_ino) != (current.st_dev, current.st_ino)
                                or again.read(LIMIT + 1) != raw):
                            raise ValueError('Controller stop changed during durable observation')
                    self._stop_record(value)
                    observed['identity_matches'] = True
                    observed['stop_durable'] = True
        except (OSError, ValueError) as error:
            if observed['identity_matches'] is None:
                observed['identity_matches'] = False
            return {**observed, 'reason': str(error)}
        if drain:
            try:
                with self._locked(shared=False):
                    after = self.observe(synchronize=True)
                    if after['stop_durable'] is True and after['record_sha256'] == observed['record_sha256']:
                        after['admission_drained'] = True
                    else:
                        after['reason'] = after['reason'] or 'Controller stop changed before parent admission drained'
                    return after
            except (OSError, ValueError) as error:
                observed['reason'] = str(error) or 'Original parent admission permits remain active'
        return observed

    def request_stop(self, reason):
        """Publish the veto before fsync; never repair or replace an existing path."""
        self._authorization()
        self.validate_lock()
        try:
            self.stop.lstat()
        except FileNotFoundError:
            pass
        else:
            return self.observe(synchronize=True, drain=True)
        value = {**self.identity, 'controller_intent_sha256': self._intent_sha(),
            'reason': reason, 'requested_at': datetime.now(timezone.utc).isoformat()}
        self._stop_record(value)
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
        if len(raw) > LIMIT:
            raise ValueError('Complete controller stop exceeds its publication capacity')
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        try:
            descriptor = os.open(self.stop, flags, 0o600)
        except FileExistsError:
            return self.observe(synchronize=True, drain=True)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            sync_directories(self.folder, self.directory)
        except OSError as error:
            return {**self.observe(), 'reason': 'Controller stop durability is unconfirmed: ' + str(error)}
        return self.observe(synchronize=True, drain=True)


class ExecutionRecords:
    """Read and bind one original chain without importing application state or SDKs."""

    def __init__(self, project: dict, ident: str, home: str):
        from agent_platform.core import slug
        from dev_platform import adapter
        from dev_platform.contracts import canonical_sha

        self.project, self.ident, self.home, self.sha, self.adapter = project, slug(ident), home, canonical_sha, adapter
        self.execution = project['registration']['definition']['execution']
        self.root, self.config = (Path(self.execution[key]) for key in ('state_directory', 'config_directory'))
        self.prefix = 'training/jobs/' + self.ident
        self.folder = adapter.safe_file(self.root, self.prefix + '/managed-execution')
        self.budget = adapter.safe_file(self.root, 'ergora/training-submissions/' + self.ident + '.budget')
        self.originals, self.records = {}, {}

    def document(self, path: Path, *, optional=False, limit=LIMIT):
        try:
            raw = read_raw(path, limit)
        except FileNotFoundError:
            if optional:
                return None
            raise
        self.originals[path] = raw
        return decode(raw)

    def load(self):
        # Read descendants first so concurrent append-only publication is safe.
        self.records = {name: self.document(self.folder / (name + '.json'), optional=True)
                        for name in ('stopped', 'ack', 'attempt', 'launch', 'request')}
        self.intent = self.document(self.budget.parent / (self.ident + '.intent.json'), optional=True, limit=16 * LIMIT)
        self.owner = self.document(self.budget / 'owner.json', optional=True)
        if self.owner is not None:
            owner_record(self.owner)
        request = self.records['request']
        if request is None:
            if any(value is not None for value in self.records.values()):
                raise ValueError('Execution records have no original request')
            return self
        if self.intent is None or self.owner is None or self.owner.get('execution_capability') is None:
            raise ValueError('Execution request has no original capable owner and start intent')
        intent = self.intent
        common = ('schema_version', 'kind', 'protocol')
        _exact(request, (*common, 'control_home', 'project', 'project_revision', 'registration_sha256', 'execution',
            'experiment_id', 'job_id', 'workflow_id', 'run_id', 'start_intent_sha256', 'start_attempt_sha256',
            'start_receipt_sha256', 'authorization_sha256', 'owner_sha256', 'native_request_sha256',
            'native_request_semantic_sha256', 'confirmation', 'actor_id'), 'Execution request')
        if (type(request['schema_version']) is not int or type(request['project_revision']) is not int
                or request['project_revision'] < 1 or request['confirmation'] is not True
                or not isinstance(request['actor_id'], str) or not request['actor_id'].startswith('unix:')):
            raise ValueError('Execution request has invalid revision, confirmation or actor')
        expected = self.request_record(request['actor_id'])
        _match(request, expected, 'Execution request')
        _match({key: self.owner[key] for key in ('intent_sha256', 'authorization_sha256')},
            {'intent_sha256': self.sha(intent), 'authorization_sha256': request['authorization_sha256']}, 'Owner authorization')
        launch, attempt, ack, stopped = (self.records[name] for name in ('launch', 'attempt', 'ack', 'stopped'))
        if launch is not None:
            _exact(launch, (*common, 'request_sha256', 'owner_sha256', 'authorization_sha256', 'clock_sha256',
                'launch_id', 'execution_phase_id'), 'Execution launch')
            for name in ('launch_id', 'execution_phase_id'):
                if not isinstance(launch[name], str) or re.fullmatch('[a-f0-9]{32}', launch[name]) is None:
                    raise ValueError('Execution launch has an invalid observation identity')
            _digest(launch['clock_sha256'])
            _match(launch, {'schema_version': 1, 'kind': 'training-execution-launch', 'protocol': PROTOCOL,
                'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'authorization_sha256': request['authorization_sha256'], 'clock_sha256': launch['clock_sha256'],
                'launch_id': launch['launch_id'], 'execution_phase_id': launch['execution_phase_id']}, 'Execution launch')
        if attempt is not None:
            if launch is None:
                raise ValueError('Execution attempt has no consumed launch')
            _process(attempt.get('supervisor'))
            _process(attempt.get('executor'))
            _match(attempt, {'schema_version': 1, 'kind': 'training-execution-attempt', 'protocol': PROTOCOL,
                'launch_sha256': self.sha(launch), 'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'run_id': request['run_id'], 'job_id': request['job_id'], 'native_request_sha256': request['native_request_sha256'],
                'supervisor': attempt['supervisor'], 'executor': attempt['executor']}, 'Execution attempt')
        if ack is not None:
            if attempt is None:
                raise ValueError('Execution ack has no matching attempt')
            _match(ack, {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': PROTOCOL,
                'attempt_sha256': self.sha(attempt), 'launch_sha256': self.sha(launch),
                'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'executor': attempt['executor']}, 'Execution ack')
        if stopped is not None:
            if ack is None:
                raise ValueError('Execution stop has no complete attempt and ack')
            process = stopped.get('process')
            _exact(process, ('status', 'returncode', 'output'), 'Reaped process')
            if (process['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out')
                    or process['returncode'] is not None and type(process['returncode']) is not int
                    or process['output'] != str(self.budget / ('observations/execute-' + launch['execution_phase_id']) / 'helper')):
                raise ValueError('Execution stop has no original process observation')
            stamp = datetime.fromisoformat(stopped['reaped_at'])
            if stamp.utcoffset() != timedelta(0) or stamp.isoformat() != stopped['reaped_at']:
                raise ValueError('Execution stop has no UTC reap observation')
            _match(stopped, {'schema_version': 1, 'kind': 'training-execution-stopped', 'protocol': PROTOCOL,
                'request_sha256': self.sha(request), 'launch_sha256': self.sha(launch),
                'attempt_sha256': self.sha(attempt), 'ack_sha256': self.sha(ack),
                'supervisor': attempt['supervisor'], 'process': process, 'reaped_at': stopped['reaped_at']}, 'Execution stop')
        return self

    def request_record(self, actor: str) -> dict:
        intent = self.intent
        start = self.document(self.budget.parent / (self.ident + '.attempt.json'))
        receipt = self.document(self.budget.parent / (self.ident + '.result.json'))
        self.native = self.document(self.root / self.prefix / 'request.json')
        _exact(self.native, ('schema_version', 'job_id', 'experiment', 'runner'), 'Native request')
        if type(self.native['schema_version']) is not int or self.native['schema_version'] != 1:
            raise ValueError('Native request has an invalid schema')
        item = intent['observation']['experiment']
        expected_start = {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                          'spec_sha256': self.sha(item['spec'])}
        _match(start, expected_start, 'Original start attempt')
        if not isinstance(receipt.get('run_id'), str) or not 1 <= len(receipt['run_id']) <= 128:
            raise ValueError('Original start receipt has no exact run ID')
        _match(receipt, {**expected_start, 'run_id': receipt['run_id']}, 'Original start receipt')
        _match(self.native, {'schema_version': 1, 'job_id': 'local-perf-' + self.ident,
            'experiment': item['spec'], 'runner': item['current_runner']}, 'Complete native request')
        expected = {'schema_version': 1, 'kind': 'training-execution-request', 'protocol': PROTOCOL,
            'control_home': self.home, 'project': self.project['id'], 'project_revision': intent['project_revision'],
            'registration_sha256': self.project['registration']['sha256'], 'execution': self.execution,
            'experiment_id': self.ident, 'job_id': self.native['job_id'], 'workflow_id': intent['workflow_id'],
            'run_id': receipt['run_id'], 'start_intent_sha256': self.sha(intent), 'start_attempt_sha256': self.sha(start),
            'start_receipt_sha256': self.sha(receipt), 'authorization_sha256': intent['budget']['authorization_sha256'],
            'owner_sha256': self.sha(self.owner),
            'native_request_sha256': hashlib.sha256(self.originals[self.root / self.prefix / 'request.json']).hexdigest(),
            'native_request_semantic_sha256': self.sha(self.native), 'confirmation': True, 'actor_id': actor}
        return expected

    def observe(self, *, durable: bool = False) -> dict:
        request, stopped = self.records['request'], self.records['stopped']
        result = {'status': 'not_requested' if request is None else 'stop_observed' if stopped else 'pending',
            'protocol': PROTOCOL, 'read_only': True, 'runtime_status': 'not_queried',
            'execution_authorized': False, 'execution_success': None,
            'reap_record_observed': stopped is not None, 'durable_stop_confirmed': None, 'executor_stop_confirmed': None,
            'owner': self.owner, 'records': self.records,
            'record_sha256': {name: self.sha(value) for name, value in self.records.items() if value is not None},
            'raw_sha256': {str(path): hashlib.sha256(raw).hexdigest() for path, raw in self.originals.items()}}
        if stopped is not None and durable:
            try:
                for path in self.originals:
                    descriptor = _fd(path)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
                sync_directories(self.folder, self.root)
                for path, raw in self.originals.items():
                    if read_raw(path, 16 * LIMIT) != raw:
                        raise ValueError('Original execution chain changed during durability observation')
                result.update(status='stopped', durable_stop_confirmed=True, executor_stop_confirmed=True,
                              durability_observed_at=datetime.now(timezone.utc).isoformat())
            except (OSError, ValueError) as error:
                result['durability_reason'] = str(error)
        return result


def _round_candidate_intent(intent, plan, admission, ordinal):
    """Bind the complete local intent, including an unborn prepare candidate."""
    authorization, project = admission.authorization, plan['project']
    validate_budget_binding(intent['budget'])
    admission.bind(intent, plan)
    expected = {'schema_version': 1, 'operation': 'start', 'control_home': authorization['control_home'],
        'project': project['id'], 'repo': project['repo'], 'execution': authorization['execution'],
        'registration_sha256': project['registration']['sha256'],
        'experiment_id': plan['definition']['candidates'][ordinal]['experiment_id'],
        'workflow_id': 'perf-experiment/' + plan['definition']['candidates'][ordinal]['experiment_id'],
        'project_revision': authorization['project_revision'], 'operation_id': intent['operation_id'],
        'observation': plan['admissions'][ordinal]['observation'], 'budget': intent['budget']}
    if (type(intent['schema_version']) is not int or type(intent['project_revision']) is not int
            or not isinstance(intent['operation_id'], str) or re.fullmatch('[a-f0-9]{32}', intent['operation_id']) is None
            or intent['budget']['controller']['ordinal'] != ordinal):
        raise ValueError('Round candidate has no original complete intent identity')
    _match(intent, expected, 'Complete original round candidate intent')


def _round_sources(authorization, ready, owner):
    """Use birth sources; prepare has no owner capability until its one birth."""
    sources = authorization['measurement_sources']
    _exact(sources, MEASUREMENT_SOURCES, 'Original measurement sources')
    for name, expected in sources.items():
        _digest(expected)
        if hashlib.sha256(read_raw(Path(__file__).parent / name, ARTIFACT_LIMIT)).hexdigest() != expected:
            raise ValueError('Original round measurement source bytes changed: ' + name)
    if owner is not None:
        capability = owner.get('execution_capability')
        if (capability is None or capability['cycle_ready_sha256'] != CycleAdmission._sha(ready)
                or capability['installation'] != authorization['execution']['installation']):
            raise ValueError('Round candidate has no original ready-bound selected capability')
        validate_sources(capability)
    else:
        # Authorization pins only the four measurement sources. The original
        # 25-source/manifest capability is born later, in the immutable owner.
        installation = reference.validate_installation(Path(authorization['execution']['installation']), training=True)
        read_raw(installation / 'ergora-native-runtime.json')
        reference.verify()
    for name, expected in sources.items():
        if hashlib.sha256(read_raw(Path(__file__).parent / name, ARTIFACT_LIMIT)).hexdigest() != expected:
            raise ValueError('Original round measurement source changed during verification: ' + name)


def _round_authority(plan, admission, ready):
    """Read the exact original authorization, plan, ready and compute window."""
    authorization, sha = admission.authorization, admission._sha
    if type(authorization['schema_version']) is not int or authorization['schema_version'] not in (3, 4):
        raise ValueError('Complete round authentication requires the original schema3 authorization')
    if sha({key: value for key, value in authorization.items() if key != 'sha256'}) != authorization['sha256']:
        raise ValueError('Complete round authorization changed its original canonical SHA256')
    admission._authorization()
    raw_plan = read_raw(admission.directory / 'cycle.json', ARTIFACT_LIMIT)
    if hashlib.sha256(raw_plan).hexdigest() != authorization['input_sha256'] or decode(raw_plan) != plan:
        raise ValueError('Complete original cycle input changed')
    project, policy = plan['project'], plan['definition']['budget']
    if (plan['control_home'] != authorization['control_home'] or project['id'] != authorization['project']
            or project['revision'] != authorization['project_revision']
            or project['registration']['definition']['execution'] != authorization['execution']
            or project['registration']['operation_id'] != authorization['registration']['operation_id']):
        raise ValueError('Original round authorization differs from its registered project')
    _match(decode(read_raw(admission.directory / 'ready.json')), ready, 'Original cycle ready')
    _match(ready, {'schema_version': 1, 'kind': 'training-cycle-ready',
        'authorization_sha256': authorization['sha256'], 'admissions_sha256': sha(plan['admissions']),
        'project_revision': authorization['project_revision'], 'checked_at': ready['checked_at']}, 'Complete cycle ready')
    checked = datetime.fromisoformat(ready['checked_at'])
    if (checked.utcoffset() != timedelta(0) or checked.isoformat() != ready['checked_at']
            or not datetime.fromisoformat(authorization['clock']['authorized_at']) <= checked
                < datetime.fromisoformat(authorization['clock']['deadline_at']) - timedelta(seconds=policy['cleanup_seconds'])):
        raise ValueError('Original cycle ready is outside its computation window')
    admission.validate_lock()

    def active():
        admission.check()
        if budget_clock.remaining(authorization['clock'], policy['wall_seconds'], policy['cleanup_seconds']) <= 0:
            raise ValueError('Original round authentication computation allowance is exhausted')

    active()
    return raw_plan, active


def _round_predecessors(plan, admission, ready, controller, active):
    """Read every pinned original in a selected predecessor chain."""
    authorization, project, sha = admission.authorization, plan['project'], admission._sha
    policy = plan['definition']['budget']
    ordinal = controller['ordinal']
    predecessor, extension, result, namespace = controller['predecessor'], None, [], None
    for index in range(ordinal - 1, -1, -1):
        active()
        validate_round_predecessor(predecessor, index + 1)
        pin, acceptance = predecessor['prefix'], predecessor['acceptance']
        directory = admission.folder / 'rounds' / str(index)
        if pin['directory'] != str(directory) or {path.name for path in directory.iterdir()} != {'rounds.json'}:
            raise ValueError('Previous round prefix differs from its fixed original directory')
        raw = read_raw(directory / 'rounds.json', ARTIFACT_LIMIT)
        saved = {'directory': str(directory), 'sha256': hashlib.sha256(raw).hexdigest(), 'report': decode(raw)}
        if round_pin(saved, raw) != pin:
            raise ValueError('Previous round pin differs from its complete raw original index')
        validate_round_content(saved['report'])
        if extension is not None:
            round_report_binding(extension, plan, index + 1, saved)
        value = read_round_observation(acceptance['observation'], home=Path(authorization['control_home']),
                                       operation_id=acceptance['source_operation_id'])
        ident = plan['definition']['candidates'][index]['experiment_id']
        chain = ExecutionRecords(project, ident, authorization['control_home']).load()
        original = chain.intent
        _round_candidate_intent(original, plan, admission, index)
        _round_sources(authorization, ready, chain.owner)
        if (chain.owner['intent_sha256'] != sha(original)
                or chain.owner['authorization_sha256'] != authorization['sha256']):
            raise ValueError('Previous round owner differs from its original intent or authorization')
        source_path = Path(authorization['control_home']) / 'operations/training-cycles' / acceptance['source_operation_id']
        source = decode(read_raw(source_path / 'request.json', 32_768))
        validate_cycle_operation(source)
        reply = decode(read_raw(source_path / 'helper/stdout.txt', 32_768))
        selection = round_selection(plan, authorization)
        expected_snapshot = {'authorization': authorization, 'policy': policy, 'candidates': [
            {'ordinal': number, 'experiment_id': item['experiment_id'], 'manifest_sha256': item['manifest_sha256']}
            for number, item in enumerate(plan['definition']['candidates'])]}
        measurement = {'measurement_state': 'accepted', 'index_state': 'durable', 'continuation_ready': True,
                       'prefix': pin, 'acceptance': acceptance}
        expected_reply = {'status': 'observed', 'facts': {
            **value['facts'], 'selection': selection, 'measurement': measurement}}
        _match(reply, expected_reply, 'Complete original accepted helper projection')
        if (value['identity'] != source['identity'] or value['identity']['ordinal'] != index
                or value['activity_context'] != source['activity_context'] or source['snapshot'] != expected_snapshot
                or value['prefix'] != pin or value['selection'] != selection
                or value['predecessor'] != original['budget']['controller']['predecessor']
                or source['start_context']['controller'] != original['budget']['controller']
                or any(source['activity_context']['activity_source'][key] != original['budget']['controller'][target]
                       for key, target in (('workflow_id', 'workflow_id'), ('workflow_run_id', 'run_id')))
                or value['activity_context']['workflow_input'] != admission.controller_intent()['workflow_input']
                or round_acceptance(value, acceptance['observation'], original) != acceptance):
            raise ValueError('Previous acceptance differs from its complete original source operation or candidate')
        current_namespace = value['activity_context']['service_namespace']
        if namespace is not None and current_namespace != namespace:
            raise ValueError('Previous round observations changed the original service namespace')
        namespace = current_namespace
        observed = chain.observe(durable=True)
        if (any(observed[key] != value['execution'][key] for key in ('owner', 'records', 'record_sha256', 'raw_sha256'))
                or observed['durable_stop_confirmed'] is not True or observed['executor_stop_confirmed'] is not True):
            raise ValueError('Previous accepted execution complete original inventory changed')
        evidence = value['evidence']
        if not isinstance(evidence['files'], dict):
            raise ValueError('Previous evidence requires its complete original file mapping')
        for name, expected in evidence['files'].items():
            prefix, relative = name.split('/', 1)
            root = chain.root if prefix == 'state' else chain.config if prefix == 'config' else None
            if root is None or Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('Previous evidence file is outside its frozen native roots')
            _digest(expected)
            if hashlib.sha256(read_raw(chain.adapter.safe_file(root, relative))).hexdigest() != expected:
                raise ValueError('Previous evidence original raw file changed: ' + name)
        submitted = saved['report']['rounds'][-1]['native']['submission']
        if (submitted['intent_sha256'] != sha(original)
                or submitted['workflow_id'] != chain.records['request']['workflow_id']
                or submitted['run_id'] != chain.records['request']['run_id']
                or round_state({'status': 'observed', 'submission': submitted, **value}, evidence,
                               saved['report']['rounds'][-1], original) != 'accepted'):
            raise ValueError('Previous original observation does not authenticate all four accepted facts')
        result.append((saved, value, original, observed))
        extension, predecessor = saved, original['budget']['controller']['predecessor']
        active()
    if extension is not None:
        round_report_binding(extension, plan, 0, None)
    validate_round_predecessor(predecessor, 0)
    return result


def authenticate_cycle_binding(binding: dict, plan: dict, admission: CycleAdmission, ready: dict) -> list:
    """Authenticate a real selected binding without inventing a future intent."""
    authorization, project = admission.authorization, plan['project']
    raw_plan, active = _round_authority(plan, admission, ready)
    _, selected = admission._bound_selection(binding, plan)
    current = ExecutionRecords(project, selected['experiment_id'], authorization['control_home'])
    for name, expected in project['registration']['files'].items():
        _match(current.document(current.adapter.safe_file(current.config, name)), expected, 'Original registered document')
    _round_sources(authorization, ready, None)
    result = _round_predecessors(plan, admission, ready, binding['controller'], active)
    admission._bound_selection(binding, plan)
    _match(decode(read_raw(admission.directory / 'ready.json')), ready, 'Original cycle ready')
    if read_raw(admission.directory / 'cycle.json', ARTIFACT_LIMIT) != raw_plan:
        raise ValueError('Original complete cycle input changed during authentication')
    _round_sources(authorization, ready, None)
    active()
    return result


def authenticate_cycle_candidate(intent: dict, plan: dict, admission: CycleAdmission, ready: dict) -> list:
    """Authenticate the complete current intent, owner and all predecessors.

    The H additionally checks live archive and runtime eligibility. This pure
    boundary remains independent of State, schemas and the SDK.
    """
    authorization, sha, project = admission.authorization, admission._sha, plan['project']
    raw_plan, active = _round_authority(plan, admission, ready)
    validate_budget_binding(intent['budget'])
    admission.bind(intent, plan)
    controller = intent['budget']['controller']
    ordinal = controller['ordinal']
    _round_candidate_intent(intent, plan, admission, ordinal)
    current = ExecutionRecords(project, intent['experiment_id'], authorization['control_home'])
    current_owner = current.document(current.budget / 'owner.json', optional=True)
    intent_path = current.budget.parent / (current.ident + '.intent.json')
    actual_intent = current.document(intent_path, optional=current_owner is None, limit=16 * LIMIT)
    if actual_intent is not None:
        _match(actual_intent, intent, 'Complete original current candidate intent')
    if current_owner is not None:
        owner_record(current_owner)
        if (current_owner['intent_sha256'] != sha(intent)
                or current_owner['authorization_sha256'] != authorization['sha256']):
            raise ValueError('Round candidate owner differs from its original intent or authorization')
    for name, expected in project['registration']['files'].items():
        _match(current.document(current.adapter.safe_file(current.config, name)), expected, 'Original registered document')

    active()
    _round_sources(authorization, ready, current_owner)
    result = _round_predecessors(plan, admission, ready, controller, active)
    _match(current.document(current.budget / 'owner.json', optional=True), current_owner, 'Original round candidate owner')
    _match(decode(read_raw(admission.directory / 'ready.json')), ready, 'Original cycle ready')
    if read_raw(admission.directory / 'cycle.json', ARTIFACT_LIMIT) != raw_plan:
        raise ValueError('Original complete cycle input changed during authentication')
    _round_sources(authorization, ready, current_owner)
    _match(current.document(intent_path, optional=actual_intent is None, limit=16 * LIMIT), actual_intent,
           'Complete original current candidate intent')
    active()
    return result


def validate_context(context: dict, chain: ExecutionRecords, *, live=True) -> CycleAdmission | None:
    """Rebind the complete birth context and its original sources, without State."""
    _exact(context, ('intent', 'authorization', 'policy', 'project', 'published_project'), 'Cached execution context')
    owner = chain.owner
    _match(context['intent'], chain.intent, 'Complete cached intent')
    if chain.sha(context) != owner['context_sha256']:
        raise ValueError('Complete execution context differs from the original owner')
    authorization, policy, intent = (context[name] for name in ('authorization', 'policy', 'intent'))
    if (authorization['sha256'] != chain.sha({key: value for key, value in authorization.items() if key != 'sha256'})
            or authorization['sha256'] != owner['authorization_sha256']):
        raise ValueError('Execution authorization differs from its original complete SHA256')
    cycle = Path(intent['control_home']) / 'training-cycles' / intent['project'] / intent['budget']['cycle_id']
    _match(decode(read_raw(cycle / 'authorization.json')), authorization, 'Original cycle authorization')
    raw = read_raw(cycle / 'cycle.json', ARTIFACT_LIMIT)
    if hashlib.sha256(raw).hexdigest() != authorization['input_sha256']:
        raise ValueError('Original complete cycle input changed')
    plan = decode(raw)
    validate_budget_binding(intent['budget'])
    if type(authorization['schema_version']) is not int or authorization['schema_version'] not in (1, 2, 3, 4):
        raise ValueError('Unsupported original execution authorization schema')
    parent = None
    if authorization['schema_version'] in (3, 4):
        parent = CycleAdmission(cycle, authorization)
        authenticate_cycle_candidate(intent, plan, parent, decode(read_raw(cycle / 'ready.json')))
    elif authorization['schema_version'] == 2:
        parent = CycleAdmission(cycle, authorization)
        parent.bind(intent, plan)
    elif 'controller' in intent['budget']:
        raise ValueError('Manual authorization cannot acquire a controller binding')
    _match(plan['definition']['budget'], policy, 'Original complete computation policy')
    _match(plan['project'], context['project'], 'Original cycle project')
    ready = decode(read_raw(cycle / 'ready.json'))
    if (chain.sha(ready) != owner['execution_capability']['cycle_ready_sha256']
            or ready['authorization_sha256'] != authorization['sha256']):
        raise ValueError('Original cycle ready record changed')
    budget_clock.validate(authorization['clock'], policy['wall_seconds'])
    registration = context['published_project']['registration']
    for name, expected in registration['files'].items():
        _match(chain.document(chain.adapter.safe_file(chain.config, name)), expected, 'Original registered document')
    observed = intent['observation']
    for name, expected in {**observed['baseline_files'], **observed['experiment']['files']}.items():
        prefix, relative = name.split('/', 1)
        root = chain.root if prefix == 'state' else chain.config if prefix == 'config' else None
        if root is None or hashlib.sha256(read_raw(chain.adapter.safe_file(root, relative))).hexdigest() != expected:
            raise ValueError('Original experiment source changed: ' + name)
    validate_sources(owner['execution_capability'])
    if live and (not owner_active(chain.budget / 'owner.json', owner)
            or budget_clock.remaining(authorization['clock'], policy['wall_seconds'], policy['cleanup_seconds']) <= 0):
        raise ValueError('Original execution owner or computation budget is no longer active')
    if live and parent is not None:
        parent.check()
    return parent


def native_main(installation: str) -> None:
    """Use the selected venv; the callback remains inside the original executor lock."""
    from agent_platform import core

    payload = json.load(sys.stdin)
    context, phase = payload['cached'], payload['phase']
    project, intent = context['project'], context['intent']
    reference.validate_installation(Path(installation), training=True)
    if (sys.prefix != str(Path(installation) / '.venv') or core.ROOT != Path(installation)
            or core.PYTHON != Path(installation) / '.venv/bin/python'
            or core.STATE != Path(intent['execution']['state_directory'])
            or core.CONFIG != Path(intent['execution']['config_directory'])):
        raise ValueError('Managed native interpreter or registered core paths differ')
    from agent_platform.training_executor import process

    def admit(folder, record):
        nonlocal parent
        chain = ExecutionRecords(project, intent['experiment_id'], intent['control_home']).load()
        checked_parent = validate_context(context, chain)
        if parent is None and checked_parent is not None:
            parent = checked_parent
            admissions.enter_context(parent.permission())
        request, launch = chain.records['request'], chain.records['launch']
        if request is None or launch is None or any(chain.records[name] is not None for name in ('attempt', 'ack', 'stopped')):
            raise ValueError('Managed execution requires its one unused consumed launch')
        protocol_phase = {'schema_version': 1, 'intent_sha256': chain.sha(intent),
            'authorization_sha256': chain.owner['authorization_sha256'], 'protocol': 'ergora-budget-phase-v1',
            'phase_id': launch['execution_phase_id'], 'mode': 'execute', 'context_sha256': chain.sha(context),
            'owner': {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}}
        _match(phase, protocol_phase, 'Complete execution supervisor phase')
        actor = (context['authorization']['controller']['actor_id'] if context['authorization']['schema_version'] in (2, 3, 4)
                 else f'unix:{os.getuid()}:{getpass.getuser()}')
        if (folder != chain.folder.parent
                or launch['clock_sha256'] != chain.sha(context['authorization']['clock'])
                or request['actor_id'] != actor):
            raise ValueError('Native callback differs from its original supervisor, actor or clock')
        _match(record, chain.native, 'Native locked request')
        supervisor, executor = processes.identity(os.getppid()), processes.identity(os.getpid())
        _match(phase['owner'], {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}, 'Supervisor owner')
        parent_fields = Path('/proc/' + str(supervisor['pid']) + '/stat').read_text().rsplit(')', 1)[1].split()
        if int(parent_fields[1]) != chain.owner['pid']:
            raise ValueError('Native supervisor is not a child of its original budget owner')
        _match(processes.identity(chain.owner['pid']), phase['owner'], 'Original owner process')
        attempt, ack = None, None

        def active():
            refreshed = ExecutionRecords(project, intent['experiment_id'], intent['control_home']).load()
            validate_context(context, refreshed)
            _match(refreshed.owner, chain.owner, 'Native callback original owner')
            _match(refreshed.records, {**chain.records, 'attempt': attempt, 'ack': ack},
                   'Native callback current publication stage')
            if parent is not None:
                parent.check()
            # Parent authorization reads consume the same original work allowance.
            if ((chain.root / ('training/fences/' + chain.ident + '.json')).exists()
                    or not owner_active(chain.budget / 'owner.json', chain.owner)
                    or budget_clock.remaining(context['authorization']['clock'], context['policy']['wall_seconds'],
                                              context['policy']['cleanup_seconds']) <= 0):
                raise ValueError('Original execution fence, owner or computation deadline forbids work')
        active()
        attempt = {'schema_version': 1, 'kind': 'training-execution-attempt', 'protocol': PROTOCOL,
            'launch_sha256': chain.sha(launch), 'request_sha256': chain.sha(request), 'owner_sha256': chain.sha(chain.owner),
            'run_id': request['run_id'], 'job_id': request['job_id'], 'native_request_sha256': request['native_request_sha256'],
            'supervisor': supervisor, 'executor': executor}
        publish(chain.folder / 'attempt.json', attempt, chain.root)
        active()
        ack = {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': PROTOCOL,
            'attempt_sha256': chain.sha(attempt), 'launch_sha256': chain.sha(launch), 'request_sha256': chain.sha(request),
            'owner_sha256': chain.sha(chain.owner), 'executor': executor}
        publish(chain.folder / 'ack.json', ack, chain.root)
        active()
    chain = ExecutionRecords(project, intent['experiment_id'], intent['control_home'])
    parent = None
    with ExitStack() as admissions:
        # Hold the permit before the executor lock. New-version completed
        # results retain their original inert read even after the owner ends;
        # if that record vanishes, the callback still requires fresh admission.
        if (context['authorization']['schema_version'] == 2
                or context['authorization']['schema_version'] in (3, 4)
                    and not (chain.folder.parent / 'result.json').exists()):
            parent = validate_context(context, chain.load())
            admissions.enter_context(parent.permission())
        print(json.dumps(process(chain.folder.parent, admit=admit), ensure_ascii=False, allow_nan=False))


def record_stopped(context: dict, phase: dict, process: dict) -> dict:
    """Called by S only after original processes.run reaps and emits stopped."""
    intent = context['intent']
    chain = ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load()
    request, launch, attempt, ack = (chain.records[name] for name in ('request', 'launch', 'attempt', 'ack'))
    if ack is None:
        return chain.observe()
    if launch['execution_phase_id'] != phase['phase_id']:
        raise ValueError('Reaped phase differs from its original launch')
    _match(attempt['supervisor'], processes.identity(os.getpid()), 'Actual reaping supervisor')
    stopped = {'schema_version': 1, 'kind': 'training-execution-stopped', 'protocol': PROTOCOL,
        'request_sha256': chain.sha(request), 'launch_sha256': chain.sha(launch),
        'attempt_sha256': chain.sha(attempt), 'ack_sha256': chain.sha(ack),
        'supervisor': attempt['supervisor'], 'process': process, 'reaped_at': datetime.now(timezone.utc).isoformat()}
    publish(chain.folder / 'stopped.json', stopped, chain.root)
    return ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load().observe(durable=True)


def inspect_main() -> None:
    """The frozen offline contract never imports a selected native installation."""
    payload = json.load(sys.stdin)
    chain = ExecutionRecords(payload['project'], payload['experiment_id'], payload['control_home']).load()
    if payload['operation'] == 'sources':
        capability = chain.owner.get('execution_capability') if chain.owner else None
        if capability is None:
            result = {'status': 'not_declared'}
        else:
            validate_sources(capability)
            result = {'status': 'matching'}
    else:
        result = chain.observe(durable=True)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
