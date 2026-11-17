"""Trusted TEST-ONLY adapter: construct once, observe twice, then do actual CPU work."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time
import uuid


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def marker(name, value):
    directory = os.environ.get('ERGORA_TEST_CONFIGURATION_MARKERS')
    if directory:
        path = Path(directory) / (name + '.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as stream:
            stream.write(json.dumps(value) + '\n')


marker('import', {'pid': os.getpid()})


def construct(path):
    supplied = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    batch = supplied['global_batch']
    micro = supplied.get('microbatch', 3)
    if type(batch) is not int or type(micro) is not int or batch < micro or batch % micro:
        raise ValueError('CPU fixture requires a divisible positive batch')
    return {'global_batch': batch, 'microbatch': micro, 'accumulation': batch // micro,
            'precision': supplied.get('precision', 'float32'),
            'strategy': supplied.get('strategy', 'closed-form'),
            'fault': supplied.get('fault'), 'seed': supplied.get('seed', 1729)}


def prepare(request):
    context = {'configurations': {arm: construct(item['path'])
                                for arm, item in request['configurations'].items()},
               'request': request, 'observations': 0, 'identity': uuid.uuid4().hex}
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
                         'schedule': {'updates': 48 // config['global_batch']}, 'layout': 'cpu-single-process'},
        }
    marker('describe', {'identity': context['identity'], 'ordinal': context['observations']})
    if context['observations'] == 2 and context['configurations']['candidate']['fault'] in (
            'last-source-fence', 'last-source-deadline', 'last-source-request-drift'):
        import sys
        from ergora import training_execution_protocol as protocol

        wrapper = sys.modules['__main__']
        source_bytes, chain = wrapper._source_bytes, wrapper._chain
        request = context['request']

        def record_rejection(value):
            try:
                return chain(value)
            except ValueError as error:
                marker('last-guard-rejected', {'reason': str(error)})
                raise

        def final_source(repo, commit, relative):
            value = source_bytes(repo, commit, relative)
            if str(repo) == request['configurations']['candidate']['repo']:
                fault = context['configurations']['candidate']['fault']
                if fault == 'last-source-request-drift':
                    path = Path(request['output']).parent / 'configuration-request.json'
                    original = path.read_bytes()
                    (Path(request['output']) / 'request-before-drift.json').write_bytes(original)
                    path.write_bytes(original + b'\n')
                    marker('request-drift', {'original_sha256': digest(original),
                                             'changed_sha256': digest(path.read_bytes())})
                elif fault == 'last-source-fence':
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
                marker('last-source-returned', {'identity': context['identity']})
            return value

        wrapper._chain, wrapper._source_bytes = record_rejection, final_source
    return result


def calculate(config, inputs):
    values = []
    for start in range(0, len(inputs), config['global_batch']):
        for n in inputs[start:start + config['global_batch']]:
            if config['strategy'] == 'redundant-loop':
                for _ in range(12):
                    total = 0
                    for item in range(1, n + 1):
                        total += item * item
            else:
                total = n * (n + 1) * (2 * n + 1) // 6
            values.append(total)
    return values


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


def run(context, request, output):
    output = Path(output)
    marker('first-work', {'pid': os.getpid(), 'identity': context['identity'],
                          'observations': context['observations']})
    manifest_raw = Path(request['manifest']).read_bytes()
    manifest = json.loads(manifest_raw)
    comparison = {'schema_version': 1, 'experiment_id': manifest['experiment_id'],
                  'comparison_id': 'actual-cpu-readback-fixture', 'manifest_sha256': digest(manifest_raw),
                  'workload_fingerprint': manifest['workload_fingerprint'], 'independent_unit': 'paired_run',
                  **manifest['performance_policy'], 'pairs': []}
    raw_results = []
    for index in range(manifest['performance_policy']['statistics']['min_pairs']):
        inputs = list(range(3500 + index, 3548 + index))
        expected = oracle(inputs)
        order = 'AB' if index % 2 == 0 else 'BA'
        pair = {'pair_id': 'pair-' + str(index), 'order': order}
        for arm in (('baseline', 'candidate') if order == 'AB' else ('candidate', 'baseline')):
            started = time.perf_counter_ns()
            values = calculate(context['configurations'][arm], inputs)
            elapsed = (time.perf_counter_ns() - started) / 1e9
            if values != expected:
                raise ValueError('Independent CPU oracle rejected actual output')
            raw = {'arm': arm, 'values': values, 'source_samples': len(inputs),
                   'elapsed_seconds': elapsed, 'context_identity': context['identity']}
            name = f'raw/{index}-{arm}.json'
            write(output / name, raw)
            raw_results.append(name)
            pair[arm] = {'run_id': uuid.uuid4().hex, 'code_sha': manifest[arm + '_commit'],
                         'matched_input_fingerprint': digest(json.dumps(inputs).encode()),
                         'environment_fingerprint': manifest['environment_fingerprint'],
                         'initial_checkpoint_sha256': manifest['initial_checkpoint_sha256'],
                         'config_sha256': manifest['base_config_sha256' if arm == 'baseline'
                                                   else 'candidate_config_sha256'],
                         'dataset_manifest_sha256': manifest['dataset_manifest_sha256'],
                         'measurement_mode': 'unprofiled', 'aggregation': 'global_completion_window',
                         'elapsed_seconds': elapsed, 'source_samples': len(inputs)}
        comparison['pairs'].append(pair)
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
