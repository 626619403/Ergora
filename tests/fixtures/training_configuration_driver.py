"""Trusted TEST-ONLY adapter: construct once, observe twice, then do actual CPU work."""

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import uuid
from ergora._paths import PACKAGE_ROOT


INTEGER_ORACLE_SCHEME = 'fixture-independent-integer-output-v1'
INTEGER_COVERAGE = {'scope': 'exact integer sum-of-squares outputs for the recorded baseline inputs',
                    'model_training_quality': 'not_evaluated',
                    'optimizer': 'not_applicable', 'loss': 'not_applicable', 'schedule': 'not_applicable'}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical_sha(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode())


def artifact(output, name):
    raw = (Path(output) / name).read_bytes()
    return {'path': name, 'sha256': digest(raw), 'bytes': len(raw)}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def marker(name, value):
    directory = os.environ.get('ERGORA_TEST_CONFIGURATION_MARKERS')
    if directory:
        path = Path(directory) / (name + '.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        if 'pid' in value and sys.platform == 'linux':
            value = {**value, 'process_identity': {'pid': os.getpid(),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'start_ticks': int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19])}}
        with path.open('a') as stream:
            stream.write(json.dumps(value) + '\n')


marker('import', {'pid': os.getpid()})


def construct(path):
    supplied = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    batch = supplied['global_batch']
    micro = supplied.get('microbatch', 3)
    if type(batch) is not int or type(micro) is not int or batch < micro or batch % micro:
        raise ValueError('CPU fixture requires a divisible positive batch')
    result = {'global_batch': batch, 'microbatch': micro, 'accumulation': batch // micro,
              'precision': supplied.get('precision', 'float32'),
              'strategy': supplied.get('strategy', 'closed-form'),
              'fault': supplied.get('fault'), 'seed': supplied.get('seed', 1729)}
    if 'resource_limit_bytes' in supplied:
        limit = supplied['resource_limit_bytes']
        if type(limit) is not int or limit <= 0:
            raise ValueError('CPU fixture resource soft limit must be positive bytes')
        result['resource_limit_bytes'] = limit
    return result


def prepare(request):
    context = {'configurations': {arm: construct(item['path'])
                                for arm, item in request['configurations'].items()},
               'request': request, 'observations': 0, 'identity': uuid.uuid4().hex}
    if os.environ.get('ERGORA_TEST_REFERENCE_FAULT'):
        context['configurations']['candidate']['fault'] = os.environ['ERGORA_TEST_REFERENCE_FAULT']
    marker('prepare', {'pid': os.getpid(), 'identity': context['identity']})
    fault = context['configurations']['candidate']['fault']
    if fault == 'source-drift':
        source = Path(__file__)
        source.write_bytes(source.read_bytes() + b'\n# Controlled drift after construction\n')
    if fault == 'configuration-drift':
        path = Path(request['configurations']['candidate']['path'])
        path.write_bytes(path.read_bytes() + b'\n')
    if fault == 'receipt-sync':
        fsync = os.fsync
        def fail_receipt_sync(descriptor):
            path = Path('/proc/self/fd/' + str(descriptor)).resolve()
            if path == Path(request['output']) or path.parent == Path(request['output']):
                raise OSError('Controlled actual receipt synchronization failure')
            return fsync(descriptor)
        os.fsync = fail_receipt_sync
    if fault == 'receipt-readback-inode':
        fsync, opened = os.fsync, os.open
        receipt = Path(request['output']) / 'configuration-receipt.json'
        root = Path(request['context']['intent']['execution']['state_directory'])
        confirmation = {'file_synced': False, 'root_synced': False, 'exchanged': False}

        def sync_receipt(descriptor):
            path = Path('/proc/self/fd/' + str(descriptor)).resolve()
            result = fsync(descriptor)
            if path == receipt:
                confirmation['file_synced'] = True
            if path == root and confirmation['file_synced']:
                confirmation['root_synced'] = True
            return result

        def open_receipt(path, *args, **kwargs):
            if Path(path) == receipt and confirmation['root_synced'] and not confirmation['exchanged']:
                confirmation['exchanged'] = True
                raw = receipt.read_bytes()
                before = receipt.stat().st_ino
                replacement = receipt.with_suffix('.replacement')
                replacement.write_bytes(raw)
                replacement.replace(receipt)
                marker('receipt-inode-drift', {'before_inode': before, 'after_inode': receipt.stat().st_ino,
                                               'source_sha256': digest(raw), 'same_raw': receipt.read_bytes() == raw})
            return opened(path, *args, **kwargs)

        os.fsync, os.open = sync_receipt, open_receipt
    if fault == 'reader-timeout':
        while True:
            time.sleep(.02)
    return context


def describe(context):
    context['observations'] += 1
    result = {}
    for arm, config in context['configurations'].items():
        snapshot = deepcopy(config)
        if config['fault'] == 'describe-drift' and context['observations'] > 1:
            snapshot['seed'] += 1
        if config['fault'] == 'nonfinite':
            snapshot['seed'] = float('nan')
        if config['fault'] == 'oversize':
            snapshot['large'] = 'x' * 2_000_000
        result[arm] = {
            'observation_scheme': 'fixture-cpu-configuration-v1',
            'source_sha256': context['request']['configurations'][arm]['source_sha256'],
            'snapshot': snapshot,
            'semantic_identity': {'scheme': 'fixture-cpu-semantic-v1',
                                  'sha256': digest(json.dumps(config, sort_keys=True).encode())},
            'invariants': {'model_algorithm': 'integer-sum-of-squares',
                           'model_structure': 'stateless-scalar', 'model_size': 'one-scalar',
                           'precision_policy': config['precision'], 'objective': 'exact-output'},
            'workload': {'dataset': 'fixed-positive-integers-v1', 'initial_checkpoint': {'kind': 'stateless'},
                         'window': {'source_samples': 48}, 'global_batch': config['global_batch'],
                         'microbatch': config['microbatch'], 'accumulation': config['accumulation'],
                         'normalization': 'source-sample', 'optimizer': {'kind': 'not-applicable'},
                         'schedule': {'kind': 'not-applicable'},
                         'layout': {'kind': 'cpu-single-process',
                                    'batch_groups': (48 + config['global_batch'] - 1) // config['global_batch']}},
        }
    marker('describe', {'identity': context['identity'], 'ordinal': context['observations']})
    context['described'] = deepcopy(result)
    if context['observations'] == 2 and context['configurations']['candidate']['fault'] in (
            'last-source-fence', 'last-source-deadline', 'last-source-request-drift',
            'last-material-fence', 'last-material-deadline'):
        import sys
        import ergora.training.execution_protocol as protocol

        wrapper = sys.modules['__main__']
        source_bytes, chain = wrapper._source_bytes, wrapper._chain
        request = context['request']

        def record_rejection(value):
            try:
                return chain(value)
            except ValueError as error:
                marker('last-guard-rejected', {'reason': str(error)})
                raise

        def invalidate():
            fault = context['configurations']['candidate']['fault']
            if fault == 'last-source-request-drift':
                path = Path(request['output']).parent / 'configuration-request.json'
                original = path.read_bytes()
                (Path(request['output']) / 'request-before-drift.json').write_bytes(original)
                path.write_bytes(original + b'\n')
                marker('request-drift', {'original_sha256': digest(original),
                                         'changed_sha256': digest(path.read_bytes())})
            elif fault in ('last-source-fence', 'last-material-fence'):
                import asyncio
                from agent_platform import training
                from perf_temporal.models import Job

                record = json.loads((Path(request['output']).parent / 'request.json').read_bytes())
                asyncio.run(training.create_adapter().cancel_job_group(
                    Job(training.binding_from(record['experiment']['binding']), record['job_id'])))
            else:
                from datetime import timedelta

                clock, policy = request['context']['authorization']['clock'], request['context']['policy']
                original_clock, original_datetime = protocol.budget_clock._clock, protocol.budget_clock.datetime
                _, ticks = original_clock()
                shift = max(0, clock['boottime_ns'] + (policy['wall_seconds'] - policy['cleanup_seconds'] + 1)
                            * 1_000_000_000 - ticks)
                def shifted_clock():
                    boot, current = original_clock()
                    return boot, current + shift
                class ShiftedDateTime(original_datetime):
                    @classmethod
                    def now(cls, tz=None):
                        return original_datetime.now(tz) + timedelta(seconds=shift / 1_000_000_000)
                protocol.budget_clock._clock = shifted_clock
                protocol.budget_clock.datetime = ShiftedDateTime
            marker('last-material-returned' if fault.startswith('last-material') else 'last-source-returned',
                       {'identity': context['identity']})

        def final_source(repo, commit, relative):
            value = source_bytes(repo, commit, relative)
            if str(repo) == request['configurations']['candidate']['repo']:
                invalidate()
            return value

        wrapper._chain = record_rejection
        if context['configurations']['candidate']['fault'].startswith('last-material'):
            import ergora.training.materials as training_materials

            original_read = training_materials.read_raw
            def final_material(path, *args, **kwargs):
                value = original_read(path, *args, **kwargs)
                if Path(path) == Path(request['configurations']['candidate']['path']):
                    invalidate()
                return value
            training_materials.read_raw = final_material
        else:
            wrapper._source_bytes = final_source
    return result



def calculate(config, inputs):
    values, grouping = [], []
    for start in range(0, len(inputs), config['global_batch']):
        batch = inputs[start:start + config['global_batch']]
        chunks = []
        for offset in range(0, len(batch), config['microbatch']):
            chunk = batch[offset:offset + config['microbatch']]
            chunks.append(len(chunk))
            for n in chunk:
                if config['strategy'] == 'redundant-loop':
                    for _ in range(12):
                        total = 0
                        for item in range(1, n + 1):
                            total += item * item
                else:
                    total = n * (n + 1) * (2 * n + 1) // 6
                values.append(total)
        grouping.append(chunks)
    return values, grouping


def oracle(inputs):
    expected = []
    for n in inputs:
        square, total, odd = 0, 0, 1
        for _ in range(n):
            square += odd
            odd += 2
            total += square
        expected.append(total)
    return expected


def screen(context, request, output, *, record_first_failure):
    """Measure one candidate integer window and check its actual output independently."""
    output = Path(output)
    plan = request['execution']['plan']
    config = context['configurations']['candidate']
    fault = config['fault']
    planned_inputs = list(range(3500, 3548))
    if plan['input_plan'] != {'scheme': 'fixed-positive-integers-v1',
                              'sha256': canonical_sha(planned_inputs)}:
        raise ValueError('CPU screen does not support the frozen input plan')
    marker('screen', {'pid': os.getpid(), 'identity': context['identity'],
                      'observations': context['observations']})
    actual_inputs = planned_inputs[:-1] if fault == 'screen-missing-input' else planned_inputs
    actual_config = {**config, 'global_batch': 12} if fault == 'screen-wrong-groups' else config
    started = time.perf_counter_ns()
    values, grouping = calculate(actual_config, actual_inputs)
    elapsed = (time.perf_counter_ns() - started) / 1e9
    if fault in ('screen-nan', 'screen-first-failure-then-exception'):
        values[0] = float('nan')
    expected = oracle(planned_inputs)
    write(output / 'screen/inputs.json', {'input_plan': plan['input_plan'],
          'effective_work': len(actual_inputs), 'values': actual_inputs})
    write(output / 'screen/expected.json', {'values': expected,
          'algorithm': 'sum successive odd increments; independent of candidate execution'})
    check_inputs, check_expected = 'screen/inputs.json', 'screen/expected.json'
    if fault == 'screen-opaque-artifacts':
        check_inputs, check_expected = 'screen/check-inputs.bin', 'screen/check-expected.bin'
        (output / check_inputs).write_bytes(b''.join(value.to_bytes(8, 'big') for value in actual_inputs))
        # A deliberately wide raw integer encoding exercises the artifact capacity,
        # independently of the JSON window and the source-owned oracle report.
        (output / check_expected).write_bytes(b''.join(value.to_bytes(24_000, 'big') for value in expected))
    # A textual raw observation preserves nonfinite diagnostics without nonstandard JSON.
    (output / 'screen/actual-output.txt').write_text(repr(values) + '\n', encoding='utf-8')
    window = {'provenance': {'native_request_sha256': request['native_request_sha256'],
                'launch_sha256': request['managed']['launch_sha256'],
                'execution_phase_id': request['execution_phase_id'],
                'run_id': uuid.uuid4().hex, 'window_id': uuid.uuid4().hex},
              'input_ref': artifact(output, 'screen/inputs.json'), 'unit': plan['window']['unit'],
              'effective_work': len(actual_inputs), 'updates': 'not-applicable',
              'measurement_mode': 'unprofiled', 'aggregation': 'global_completion_window',
              'rank_coverage': {'expected': [0], 'completed': [0]}, 'elapsed_seconds': elapsed}
    write(output / 'screen/window.json', {**window, 'grouping': grouping,
          'output_ref': artifact(output, 'screen/actual-output.txt'),
          'context_identity': context['identity'], 'candidate_batch': config['global_batch'],
          'candidate_microbatch': config['microbatch']})
    window['raw_ref'] = artifact(output, 'screen/window.json')
    expected_groups = [
        [len(planned_inputs[start + offset:start + min(offset + config['microbatch'], config['global_batch'])])
         for offset in range(0, min(config['global_batch'], len(planned_inputs) - start), config['microbatch'])]
        for start in range(0, len(planned_inputs), config['global_batch'])]
    checks = []
    for order, check in enumerate(plan['checks']):
        passed = (all(math.isfinite(value) for value in values) if check['kind'] == 'finite' else
                  values == expected and actual_inputs == planned_inputs and grouping == expected_groups)
        status = 'PASS' if passed else 'FAIL'
        entry = {'id': check['id'], 'kind': check['kind'], 'contract_sha256': check['contract_sha256'],
                 'subject': {'window_id': window['provenance']['window_id'], 'rank': 0},
                 'status': status, 'input_refs': [artifact(output, check_inputs)],
                 'expected_refs': [artifact(output, check_expected)] if check['kind'] == 'behavior' else [],
                 'coverage': {'scope': 'candidate exact integer CPU outputs and configured sample grouping',
                              'expected_samples': len(planned_inputs), 'actual_samples': len(actual_inputs),
                              'model_training_quality': 'not_evaluated',
                              'optimizer': 'not_applicable', 'loss': 'not_applicable', 'schedule': 'not_applicable'}}
        name = 'screen/' + check['id'] + '.json'
        write(output / name, {'kind': 'screen-check', 'check_id': entry['id'], 'check_kind': entry['kind'],
              **{key: entry[key] for key in ('contract_sha256', 'subject', 'status', 'input_refs',
                                            'expected_refs', 'coverage')}})
        entry['report_ref'] = artifact(output, name)
        checks.append(entry)
        if not passed:
            record_first_failure({'check_id': check['id'], 'rank': 0, 'phase': 'candidate-output-check',
                'window_id': window['provenance']['window_id'], 'work_index': 0,
                'observation_order': order, 'diagnostic_refs': [artifact(output, 'screen/actual-output.txt')]})
            first = output / 'screen-first-failure.json'
            marker('screen-first-failure-returned', {'identity': context['identity'],
                'sha256': digest(first.read_bytes()), 'inode': first.stat().st_ino,
                'check_id': check['id']})
            if fault == 'screen-first-failure-then-exception':
                raise RuntimeError('Controlled exception after durable first-failure publication')
            break
    resources = [{key: resource[key] for key in ('metric', 'unit', 'scope', 'aggregation')}
                 | {'state': 'NOT_RUN', 'observed': None, 'report_ref': None}
                 for resource in plan['resources']]
    reasons = [{'code': 'resource_not_measured', 'field': resource['metric'],
                'expected': resource['scope'], 'observed': 'NOT_RUN', 'source_ref': None}
               for resource in resources]
    environment = {'device': 'CPU', 'python': sys.version, 'implementation': platform.python_implementation(),
                   'platform': platform.platform(), 'ranks': [0], 'layout': 'single-process',
                   'dependencies': 'Python standard library'}
    write(output / 'screen/environment.json', {'environment': environment,
          'executable': str(Path(sys.executable).resolve()), 'pid': os.getpid()})
    artifacts = [artifact(output, path.relative_to(output).as_posix())
                 for path in sorted((output / 'screen').rglob('*')) if path.is_file()]
    if fault == 'screen-invalid-raw':
        (output / 'screen/window.json').write_bytes((output / 'screen/window.json').read_bytes() + b'\n')
    return {'workload': {'input_plan': plan['input_plan'], 'warmup_work': 0,
                'scope': {'device': 'CPU', 'work': 'candidate integer outputs only',
                          'environment': environment,
                          'historical_window_relation': 'first oracle-covered fixed-size window; historical rate aggregates all original windows',
                          'baseline_work_executed': False, 'model_construction': 'not_applicable',
                          'optimizer': 'not_applicable', 'loss': 'not_applicable', 'schedule': 'not_applicable'}},
            'windows': [window], 'checks': checks,
            'checks_not_run': [item['id'] for item in plan['checks'][len(checks):]],
            'resources': resources, 'artifacts': artifacts, 'reasons': reasons}


def run(context, request, output):
    output = Path(output)
    marker('first-work', {'pid': os.getpid(), 'identity': context['identity'],
                          'observations': context['observations']})
    manifest_raw = Path(request['manifest']).read_bytes()
    manifest = json.loads(manifest_raw)
    reference_enabled = request['configuration_readback']['baseline_reference_protocol'] == 'baseline-reference-v1'
    comparison = {'schema_version': 1, 'experiment_id': manifest['experiment_id'],
                  'comparison_id': 'actual-cpu-readback-fixture', 'manifest_sha256': digest(manifest_raw),
                  'workload_fingerprint': manifest['workload_fingerprint'], 'independent_unit': 'paired_run',
                  **manifest['performance_policy'], 'pairs': []}
    raw_results = []
    for index in range(manifest['performance_policy']['statistics']['min_pairs']):
        inputs = list(range(3500 + index, 3548 + index))
        expected = oracle(inputs)
        if reference_enabled:
            write(output / f'inputs/{index}.json', {'values': inputs})
            context.setdefault('input_windows', []).append({
                'fingerprint': digest(json.dumps(inputs).encode()), 'source_samples': len(inputs)})
            write(output / f'expected/{index}.json', {'values': expected,
                  'algorithm': 'sum successive odd increments; independent of both execution strategies'})
        order = 'AB' if index % 2 == 0 else 'BA'
        pair = {'pair_id': 'pair-' + str(index), 'order': order}
        for arm in (('baseline', 'candidate') if order == 'AB' else ('candidate', 'baseline')):
            run_id, window_id = uuid.uuid4().hex, uuid.uuid4().hex
            started = time.perf_counter_ns()
            values, grouping = calculate(context['configurations'][arm], inputs)
            elapsed = (time.perf_counter_ns() - started) / 1e9
            if values != expected:
                raise ValueError('Independent CPU oracle rejected actual output')
            raw = {'arm': arm, 'values': values, 'grouping': grouping, 'source_samples': len(inputs),
                   'elapsed_seconds': elapsed, 'context_identity': context['identity']}
            if reference_enabled:
                raw.update(matched_input_fingerprint=digest(json.dumps(inputs).encode()),
                    measurement_mode='unprofiled', aggregation='global_completion_window',
                    provenance={'native_request_sha256': request['native_request_sha256'],
                                'launch_sha256': request['managed']['launch_sha256'],
                                'execution_phase_id': request['execution_phase_id'],
                                'run_id': run_id, 'window_id': window_id})
                if arm == 'baseline' and context['configurations']['candidate']['fault'] == 'reference-cached-window':
                    historical = context['reference']['receipt']['measurement'][index]
                    raw['elapsed_seconds'] = elapsed = historical['elapsed_seconds']
                    raw['provenance'] = {**historical['provenance'], 'run_id': run_id}
                    marker('cached-window', {'new_run_id': run_id, 'provenance': raw['provenance']})
            name = f'raw/{index}-{arm}.json'
            write(output / name, raw)
            raw_results.append(name)
            pair[arm] = {'run_id': run_id, 'code_sha': manifest[arm + '_commit'],
                         'matched_input_fingerprint': digest(json.dumps(inputs).encode()),
                         'environment_fingerprint': manifest['environment_fingerprint'],
                         'initial_checkpoint_sha256': manifest['initial_checkpoint_sha256'],
                         'config_sha256': manifest['base_config_sha256' if arm == 'baseline'
                                                   else 'candidate_config_sha256'],
                         'dataset_manifest_sha256': manifest['dataset_manifest_sha256'],
                         'measurement_mode': 'unprofiled', 'aggregation': 'global_completion_window',
                         'elapsed_seconds': elapsed, 'source_samples': len(inputs)}
            if reference_enabled:
                pair[arm]['raw_ref'] = artifact(output, name)
        comparison['pairs'].append(pair)
    if reference_enabled:
        context['comparison'] = deepcopy(comparison)
        context['resources'] = []
        if 'resource_limit_bytes' in context['configurations']['baseline']:
            import resource

            maximum_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            metric = {'metric': 'peak_rss', 'unit': 'bytes', 'aggregation': 'peak',
                      'scope': 'whole_runner_process', 'observed': maximum_kib * 1024,
                      'limit': context['configurations']['baseline']['resource_limit_bytes']}
            write(output / 'resource-peak-rss.json', {'metric': metric, 'observation': {
                'method': 'resource.getrusage(RUSAGE_SELF).ru_maxrss', 'raw_value': maximum_kib,
                'raw_unit': 'KiB', 'bytes_per_unit': 1024, 'pid': os.getpid(), 'ranks': [0],
                'window': 'process lifetime through collection after both paired integer arms completed',
                'native_request_sha256': request['native_request_sha256'],
                'launch_sha256': request['managed']['launch_sha256'],
                'execution_phase_id': request['execution_phase_id']}})
            context['resources'] = [{**metric, 'report_ref': artifact(output, 'resource-peak-rss.json')}]
        baseline_observation = deepcopy(context['described']['baseline'])
        baseline_observation['snapshot_sha256'] = canonical_sha(baseline_observation['snapshot'])
        subject = {'arm': 'baseline', 'commit': manifest['baseline_commit'],
                   'config_sha256': manifest['base_config_sha256'],
                   'observation_sha256': canonical_sha(baseline_observation),
                   'run_ids': [pair['baseline']['run_id'] for pair in comparison['pairs']],
                   'windows': [json.loads((output / pair['baseline']['raw_ref']['path']).read_bytes())['provenance']
                               for pair in comparison['pairs']]}
        context['baseline_oracle'] = {
            'scheme': INTEGER_ORACLE_SCHEME,
            'source_entrypoint': request['configuration_readback']['source']['entrypoint'],
            'validation_contract_sha256': manifest['validation_contract_sha256'],
            'subject': subject,
            'coverage': deepcopy(INTEGER_COVERAGE),
            'status': 'PASS',
            'input_refs': [artifact(output, f'inputs/{index}.json') for index in range(len(comparison['pairs']))],
            'expected_refs': [artifact(output, f'expected/{index}.json') for index in range(len(comparison['pairs']))]}
        # This report is produced only after every actual baseline output equals the independent oracle.
        write(output / 'baseline-output-oracle.json', {
            'kind': 'baseline-output-oracle',
            **{key: context['baseline_oracle'][key] for key in ('scheme', 'subject', 'coverage', 'status',
                                                               'input_refs', 'expected_refs')},
            'actual_refs': [pair['baseline']['raw_ref'] for pair in comparison['pairs']]})
        context['environment'] = {'device': 'CPU', 'python': sys.version, 'implementation': platform.python_implementation(),
                                  'executable': str(Path(sys.executable).resolve()), 'platform': platform.platform(),
                                  'ranks': [0], 'layout': 'single-process', 'dependencies': 'Python standard library'}
        write(output / 'baseline-environment.json', {'environment': context['environment']})
    write(output / 'comparison-input.json', comparison)
    # This is the original comparator; the original native executor alone archives the bundle.
    import compare_runs
    report = compare_runs.compare(comparison, digest((output / 'comparison-input.json').read_bytes()))
    write(output / 'comparison-report.json', report)
    binding = {'candidate_commit': manifest['candidate_commit'], 'manifest_sha256': digest(manifest_raw),
               'validation_contract_sha256': manifest['validation_contract_sha256']}

    def attest(kind, name, **extra):
        write(output / name, {'kind': kind, 'status': 'PASS', **binding,
                             'scope': 'TEST-ONLY actual CPU configuration contract',
                             'observations': {'raw_results': raw_results, 'context_identity': context['identity']},
                             **extra})
        return {'status': 'PASS', 'artifact': name, **extra}

    evidence = {'schema_version': 1, 'experiment_id': manifest['experiment_id'],
                'baseline_id': manifest['baseline_id'], **binding,
                'checks': {name: attest('check:' + name, 'checks/' + name + '.json')
                           for name in manifest['checks_required']},
                'comparison': {'input': 'comparison-input.json', 'report': 'comparison-report.json'},
                'quality': {'status': 'NOT_RUN', 'reason': 'Integer CPU fixture has no model quality contract'}}
    # Transport-only review attestation: this fixture never certifies a real human review.
    evidence['review'] = attest('review', 'review.json', reviewer_id='independent-fixture-review-double',
                                candidate_commit=manifest['candidate_commit'], synthetic=True)
    evidence['integration'] = attest('integration', 'integration.json',
                                     baseline_id=manifest['baseline_id'], candidate_commit=manifest['candidate_commit'])
    evidence['artifacts'] = [{'path': path.relative_to(output).as_posix(), 'sha256': digest(path.read_bytes())}
                             for path in sorted(output.rglob('*'))
                             if path.is_file() and path.name not in ('execution.log', 'configuration-receipt.json')]
    write(output / 'evidence.json', evidence)
    if context['configurations']['candidate']['fault'] == 'receipt-raw-drift':
        receipt = output / 'configuration-receipt.json'
        before = receipt.read_bytes()
        after = before + b'\n'
        receipt.write_bytes(after)
        directory = Path(os.environ['ERGORA_TEST_CONFIGURATION_MARKERS'])
        (directory / 'receipt-before.raw').write_bytes(before)
        (directory / 'receipt-after.raw').write_bytes(after)
        marker('receipt-raw-drift', {'before_sha256': digest(before), 'after_sha256': digest(after),
                                      'same_decoded_values': json.loads(before) == json.loads(after)})
    if context['configurations']['candidate']['fault'] == 'reference-read-raw-drift':
        receipt = output / 'baseline-reference-read.json'
        original = receipt.read_bytes()
        receipt.write_bytes(original + b'\n')
        marker('reference-read-raw-drift', {'before_sha256': digest(original),
               'after_sha256': digest(receipt.read_bytes()),
               'same_decoded_values': json.loads(original) == json.loads(receipt.read_bytes())})


def baseline_reference_record(context, request, output):
    """Report the already completed integer workload; this callback performs no new work."""
    manifest = json.loads(Path(request['manifest']).read_bytes())
    pairs = context['comparison']['pairs']
    baseline = context['configurations']['baseline']
    marker('reference-record', {'identity': context['identity'], 'pid': os.getpid()})
    return {'baseline': {'commit': manifest['baseline_commit'], 'config_sha256': manifest['base_config_sha256'],
                'invariants': context['described']['baseline']['invariants'],
                'initialization': {'kind': 'stateless'},
                'inputs': {'scheme': 'fixed-positive-integers-v1', 'rng': {'kind': 'not-applicable'},
                           'windows': context['input_windows'],
                           'refs': context['baseline_oracle']['input_refs'], 'mask': 'none', 'padding': 'none', 'drop': 'none'},
                'workload': {'global_batch': baseline['global_batch'], 'microbatch': baseline['microbatch'],
                             'accumulation': baseline['accumulation'], 'source_samples_per_window': 48,
                             'optimizer': {'kind': 'not-applicable'}, 'loss': {'kind': 'not-applicable'},
                             'schedule': {'kind': 'not-applicable'},
                             'layout': {'kind': 'cpu-single-process', 'batch_groups': len(json.loads(
                                 (Path(output) / pairs[0]['baseline']['raw_ref']['path']).read_bytes())['grouping'])}},
                'output_refs': [pair['baseline']['raw_ref'] for pair in pairs],
                'run_ids': [pair['baseline']['run_id'] for pair in pairs]},
            'oracle': {**context['baseline_oracle'], 'report_ref': artifact(output, 'baseline-output-oracle.json')},
            'environment': {'observed': context['environment'], 'report_ref': artifact(output, 'baseline-environment.json')},
            'measurement': [{'pair_id': pair['pair_id'], 'order': pair['order'],
                'run_id': pair['baseline']['run_id'], 'raw_ref': pair['baseline']['raw_ref'],
                'provenance': json.loads((Path(output) / pair['baseline']['raw_ref']['path']).read_bytes())['provenance'],
                'elapsed_seconds': pair['baseline']['elapsed_seconds'], 'source_samples': pair['baseline']['source_samples'],
                'unit': 'seconds', 'measurement_mode': 'unprofiled', 'aggregation': 'global_completion_window'} for pair in pairs],
            'resources': deepcopy(context['resources'])}


def baseline_reference_read(context, request, reference):
    """Consume the reference in the same context as the selected execution operation."""
    observations = {}
    for arm, observed in context['described'].items():
        observations[arm] = {**observed, 'snapshot_sha256': canonical_sha(observed['snapshot'])}
    receipt = reference.get('receipt')
    oracle_record = receipt.get('oracle') if isinstance(receipt, dict) else None
    current = context['configurations']['candidate']
    context['reference'] = deepcopy(reference)
    manifest = json.loads(Path(request['manifest']).read_bytes())
    baseline = receipt['baseline'] if receipt else {}
    inputs = baseline.get('inputs', {})
    expected_windows = [{'fingerprint': digest(json.dumps(list(range(3500 + index, 3548 + index))).encode()),
                         'source_samples': 48} for index in range(manifest['performance_policy']['statistics']['min_pairs'])]
    current_windows = (expected_windows[:1] if request['execution']['operation'] == 'training-screen-v1'
                       else expected_windows)
    supported = bool(oracle_record and oracle_record['scheme'] == INTEGER_ORACLE_SCHEME
        and oracle_record['coverage'] == INTEGER_COVERAGE
        and baseline['commit'] == manifest['baseline_commit']
        and baseline['config_sha256'] == manifest['base_config_sha256']
        and baseline['invariants'] == observations['baseline']['invariants'] == observations['candidate']['invariants']
        and baseline['initialization'] == {'kind': 'stateless'}
        and inputs.get('scheme') == 'fixed-positive-integers-v1' and inputs.get('windows') == expected_windows
        and inputs.get('rng') == {'kind': 'not-applicable'}
        and baseline['workload'].get('source_samples_per_window') == 48)
    original_layout = baseline.get('workload', {}).get('layout')
    original_groups = original_layout.get('batch_groups') if isinstance(original_layout, dict) else None
    current_groups = (48 + current['global_batch'] - 1) // current['global_batch']
    relations = [
        {'field': 'input_scheme', 'relation': 'matched' if supported else 'unknown',
         'reference': inputs.get('scheme'), 'current': 'fixed-positive-integers-v1', 'unit': 'identity'},
        {'field': 'input_windows', 'relation': ('matched' if current_windows == inputs.get('windows') else 'different')
                                             if supported else 'unknown',
         'reference': canonical_sha(inputs['windows']) if 'windows' in inputs else None,
         'current': canonical_sha(current_windows), 'unit': 'identity'},
        {'field': 'effective_samples', 'relation': 'matched' if supported else 'unknown',
         'reference': baseline.get('workload', {}).get('source_samples_per_window'), 'current': 48, 'unit': 'samples'},
        {'field': 'initialization', 'relation': 'matched' if supported else 'unknown',
         'reference': baseline.get('initialization', {}).get('kind'), 'current': 'stateless', 'unit': 'identity'},
        {'field': 'global_batch', 'relation': 'matched' if current['global_batch'] == context['configurations']['baseline']['global_batch'] else 'different',
         'reference': context['configurations']['baseline']['global_batch'],
         'current': current['global_batch'], 'unit': 'samples'},
        {'field': 'microbatch', 'relation': 'matched' if current['microbatch'] == context['configurations']['baseline']['microbatch'] else 'different',
         'reference': context['configurations']['baseline']['microbatch'],
         'current': current['microbatch'], 'unit': 'samples'},
        {'field': 'batch_groups', 'relation': ('matched' if original_groups == current_groups else 'different') if supported else 'unknown',
         'reference': original_groups, 'current': current_groups, 'unit': 'groups'},
        # Both execution strategies and the independent oracle use Python's exact unbounded integers.
        {'field': 'integer_output_environment', 'relation': 'not_applicable',
         'reference': None, 'current': None, 'unit': 'identity'},
        {'field': 'optimizer_updates', 'relation': 'not_applicable', 'reference': None, 'current': None, 'unit': 'updates'},
        {'field': 'schedule_progress', 'relation': 'not_applicable', 'reference': None, 'current': None, 'unit': 'updates'}]
    marker('reference-read', {'identity': context['identity'], 'pid': os.getpid(),
                             'candidate_batch': current['global_batch']})
    if current['fault'] == 'reference-read-sync':
        original_sync = os.fsync
        receipt_path = Path(request['output']) / 'baseline-reference-read.json'
        def fail_read_receipt(descriptor):
            if Path('/proc/self/fd/' + str(descriptor)).resolve() == receipt_path:
                marker('reference-read-sync', {'identity': context['identity']})
                raise OSError('Controlled actual reference read receipt fsync failure')
            return original_sync(descriptor)
        os.fsync = fail_read_receipt
    if current['fault'] in ('reference-read-last-sync-fence', 'reference-read-last-sync-deadline'):
        original_sync = os.fsync
        receipt_path = Path(request['output']) / 'baseline-reference-read.json'
        stopped = False
        def stop_after_read_sync(descriptor):
            nonlocal stopped
            result = original_sync(descriptor)
            if not stopped and Path('/proc/self/fd/' + str(descriptor)).resolve() == receipt_path:
                stopped = True
                if current['fault'].endswith('fence'):
                    import asyncio
                    from agent_platform import training
                    from perf_temporal.models import Job
                    record = json.loads((Path(request['output']).parent / 'request.json').read_bytes())
                    asyncio.run(training.create_adapter().cancel_job_group(
                        Job(training.binding_from(record['experiment']['binding']), record['job_id'])))
                else:
                    from datetime import timedelta
                    import ergora.training.execution_protocol as protocol
                    clock, policy = request['context']['authorization']['clock'], request['context']['policy']
                    original_clock, original_datetime = protocol.budget_clock._clock, protocol.budget_clock.datetime
                    _, ticks = original_clock()
                    shift = max(0, clock['boottime_ns'] + (policy['wall_seconds'] - policy['cleanup_seconds'] + 1)
                                * 1_000_000_000 - ticks)
                    def shifted_clock():
                        boot, current_ticks = original_clock()
                        return boot, current_ticks + shift
                    class ShiftedDateTime(original_datetime):
                        @classmethod
                        def now(cls, tz=None):
                            return original_datetime.now(tz) + timedelta(seconds=shift / 1_000_000_000)
                    protocol.budget_clock._clock = shifted_clock
                    protocol.budget_clock.datetime = ShiftedDateTime
                marker(current['fault'], {'identity': context['identity']})
            return result
        os.fsync = stop_after_read_sync
    if current['fault'] == 'reference-current-coverage-extension':
        import ergora.training.execution_protocol as protocol
        name = 'interfaces/web.py'
        assert name not in protocol.GATE_SOURCES and (PACKAGE_ROOT / name).is_file()
        before = list(protocol.GATE_SOURCES)
        protocol.GATE_SOURCES = (*protocol.GATE_SOURCES, name)
        marker(current['fault'], {'identity': context['identity'], 'before': before,
                                  'after': list(protocol.GATE_SOURCES), 'managed': request['managed']})
    return {'scheme': 'fixture-integer-reference-projection-v1',
            'baseline_observation_sha256': canonical_sha(observations['baseline']),
            'candidate_observation_sha256': canonical_sha(observations['candidate']),
            'invariants': observations['baseline']['invariants'], 'relations': relations,
            'allowed_deltas': [item['field'] for item in relations if item['relation'] == 'different'],
            'oracle_applicability': {'state': 'supported' if supported else 'unavailable',
                'scheme': INTEGER_ORACLE_SCHEME if supported else None,
                'coverage': deepcopy(INTEGER_COVERAGE) if supported else {},
                'reasons': [] if supported else [{'code': 'oracle_relation_unsupported', 'field': 'oracle_applicability',
                    'expected': INTEGER_ORACLE_SCHEME, 'observed': oracle_record['scheme'] if oracle_record else None,
                    'source_ref': oracle_record['report_ref'] if oracle_record else None}]}}


def profile(context, request, output, *, selection):
    """Actual independent CPU window; never reuse the unprofiled screen samples."""
    arm = 'baseline' if selection['phase'] == 'baseline' else 'candidate'
    config = context['configurations'][arm]
    fault = config.get('fault')
    if fault == 'profile-exception':
        raise ValueError('Controlled actual profile callback failure')
    if fault == 'profile-timeout':
        time.sleep(request['execution']['profile']['maximum_seconds'] + 1)
    window = selection['window']
    if window['unit'] != 'source_samples':
        raise ValueError('CPU integer diagnostic source supports source_samples only')
    inputs = [2500 + index % 100 for index in range(window['work'])]
    warmup = [2400 + index % 100 for index in range(window['warmup_work'])]
    calculate(config, warmup)
    values, grouping = calculate(config, inputs)
    if values != oracle(inputs):
        raise ValueError('Independent CPU diagnostic output differs from its oracle')
    marker('profile', {'pid': os.getpid(), 'identity': context['identity'], 'phase': selection['phase'],
        'window_id': selection['window_id'], 'run_id': selection['run_id'],
        'rank': selection['rank'], 'source_samples': len(inputs)})
    result = {key: deepcopy(selection[key]) for key in ('phase', 'rank', 'window_id', 'run_id', 'window')}
    result.update(input_identity={'scheme': 'fixture-independent-profile-integers-v1',
        'inputs': inputs, 'inputs_sha256': canonical_sha(inputs), 'output_sha256': canonical_sha(values),
        'initialization': {'kind': 'stateless'}, 'grouping': grouping},
        hardware={'device': 'CPU', 'ranks': [0], 'layout': 'single-process'},
        work_completed=len(inputs), warmup_work_completed=len(warmup), measurement_mode='profiled')
    return result
