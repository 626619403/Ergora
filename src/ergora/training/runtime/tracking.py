"""Read selected effects through the managed exporter's original local MLflow route."""

from hashlib import sha256
from http.client import HTTPConnection, HTTPException
import json
import math
import re
from urllib.parse import quote, urlencode

from ergora.training.materials import decode_record


_API = '/api/2.0/mlflow/'
_METRIC_ROWS = 256
_METADATA_BYTES = 1_048_576
_ARTIFACT_BYTES = 16 * 1_048_576


def _read(path, limit, *, query=None, search=None):
    # The native exporter and its registered service use this loopback route.
    # A direct connection avoids proxy/credential discovery and redirects.
    connection = HTTPConnection('127.0.0.1', 5000, timeout=3)
    if query is not None:
        path += '?' + urlencode(query)
    try:
        if search is None:
            connection.request('GET', path)
        else:
            connection.request('POST', _API + 'runs/search', json.dumps(search),
                               {'Content-Type': 'application/json'})
        with connection.getresponse() as response:
            if response.status == 404:
                return None
            if response.status != 200 or response.getheader('Content-Encoding', 'identity') != 'identity':
                raise ValueError(f'Original MLflow read refused: HTTP {response.status}')
            if response.length is not None and response.length > limit:
                raise ValueError('capacity_exceeded: original MLflow response')
            raw = response.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('capacity_exceeded: original MLflow response')
            if response.length:
                raise ValueError('Original MLflow response was incomplete')
            return raw
    except (OSError, HTTPException) as error:
        raise ValueError('Original local MLflow read failed: ' + type(error).__name__) from error
    finally:
        connection.close()


def _document(endpoint, *, query=None, search=None):
    raw = _read(_API + endpoint, _METADATA_BYTES, query=query, search=search)
    return None if raw is None else decode_record(raw)


def _metrics(value, key='performance'):
    if isinstance(value, dict):
        for name, item in value.items():
            yield from _metrics(item, key + '.' + name)
    elif type(value) in (int, float):
        yield key, value


def selected_metric(gate, key):
    """Select a key emitted for the verified passing archive by the exporter."""
    if key == 'gate_passed':
        return 1
    values = [value for name, value in _metrics(gate['performance']) if name == key]
    if len(values) != 1 or not math.isfinite(values[0]):
        raise ValueError('Select one finite metric from the original tracking export')
    return values[0]


def _metric_history(run_id, key, value):
    document = _document('metrics/get-history', query={'run_id': run_id, 'metric_key': key,
                                                        'max_results': _METRIC_ROWS + 1})
    if document is None:
        return {'status': 'unavailable', 'key': key, 'expected_step': 0, 'expected_value': value}
    metrics = document.get('metrics', [])
    if not isinstance(metrics, list) or document.get('next_page_token') or len(metrics) > _METRIC_ROWS:
        raise ValueError('capacity_exceeded: original MLflow metric history')
    rows = []
    context_fields = ('model_id', 'dataset_name', 'dataset_digest')
    for metric in metrics:
        if (metric['key'] != key or metric.get('run_id', run_id) != run_id
                or type(metric['value']) not in (int, float)
                or not math.isfinite(metric['value'])):
            raise ValueError('Original MLflow metric history has an invalid row')
        step, timestamp = (metric[name] for name in ('step', 'timestamp'))
        if type(step) is not int or type(timestamp) is not int or timestamp < 0:
            raise ValueError('Original MLflow metric history has an invalid row identity')
        context = {name: metric[name] for name in context_fields if name in metric}
        if any(not isinstance(item, str) or not item for item in context.values()):
            raise ValueError('Original MLflow metric history has an invalid row context')
        rows.append({'step': step, 'timestamp': timestamp, 'value': metric['value'], **context})
    matching = sum(row['step'] == 0 and row['value'] == value and all(name not in row for name in context_fields)
                   for row in rows)
    return {'status': 'observed', 'key': key, 'expected_step': 0, 'expected_value': value,
            'row_count': len(rows), 'matching_row_count': matching,
            'rows': sorted(rows, key=lambda row: (row['step'], row['timestamp'], row['value'],
                                                 *(row.get(name, '') for name in context_fields)))}


def _artifact(run, experiment_id, run_id, selected):
    path = 'immutable-evidence/' + selected['path']
    result = {'path': path, 'expected_sha256': selected['sha256']}
    root = f'{experiment_id}/{run_id}/artifacts'
    if run['artifact_uri'] != 'mlflow-artifacts:/' + root:
        return {**result, 'status': 'unsupported_artifact_route'}
    raw = _read('/api/2.0/mlflow-artifacts/artifacts/' + quote(root + '/' + path, safe='/'), _ARTIFACT_BYTES)
    if raw is None:
        return {**result, 'status': 'unavailable'}
    observed_sha = sha256(raw).hexdigest()
    status = 'matching_bytes' if observed_sha == selected['sha256'] else 'different_bytes'
    return {**result, 'status': status, 'observed_sha256': observed_sha, 'bytes': len(raw)}


def observe(project_id, binding, job_id, run_id, metric_key, metric_value, artifact):
    """Check the already selected Run, then read one metric history and one artifact."""
    experiment = 'training-' + project_id
    result = {'experiment_name': experiment, 'selected_run_id': run_id, 'metric': None, 'artifact': None}
    found = _document('experiments/get-by-name', query={'experiment_name': experiment})
    if found is None:
        return {**result, 'status': 'experiment_not_observed'}
    experiment_info = found['experiment']
    exp_id = experiment_info['experiment_id']
    if experiment_info['name'] != experiment or re.fullmatch(r'[0-9]{1,19}', exp_id) is None:
        raise ValueError('Original MLflow experiment read differs from the selected experiment')
    result['experiment_id'] = exp_id
    search = _document('runs/search', search={'experiment_ids': [exp_id], 'max_results': 2, 'run_view_type': 'ALL',
                                              'filter': f"tags.manifest_sha = '{binding['manifest_sha']}'"})
    if search is None:
        raise ValueError('Original MLflow Run search is unavailable')
    runs = search.get('runs', [])
    if not isinstance(runs, list):
        raise ValueError('Original MLflow Run search has an invalid result')
    if len(runs) > 1 or search.get('next_page_token'):
        return {**result, 'status': 'multiple_manifest_matches'}
    if not runs:
        return {**result, 'status': 'run_not_observed'}
    if runs[0]['info']['run_id'] != run_id:
        return {**result, 'status': 'selected_run_mismatch'}
    found = _document('runs/get', query={'run_id': run_id})
    if found is None:
        return {**result, 'status': 'run_not_observed'}
    run = found['run']
    info = run['info']
    if info['run_id'] != run_id or info['experiment_id'] != exp_id:
        raise ValueError('Original MLflow Run read differs from the selected Run and experiment')
    if info['lifecycle_stage'] != 'active':
        return {**result, 'status': 'run_inactive', 'lifecycle_stage': info['lifecycle_stage']}
    expected = {**binding, 'runner_job_id': job_id, 'purpose': 'paired-comparison',
                'trust_model': 'trusted-current-container'}
    tag_rows = run.get('data', {}).get('tags', [])
    tags = {row['key']: row['value'] for row in tag_rows}
    if len(tags) != len(tag_rows):
        raise ValueError('Original MLflow Run has ambiguous tags')
    if mismatched := sorted(key for key, value in expected.items() if tags.get(key) != value):
        return {**result, 'status': 'foreign_run', 'mismatched_tags': mismatched}
    return {**result, 'status': 'bound_run_observed', 'run_status': info['status'],
            'metric': _metric_history(run_id, metric_key, metric_value),
            'artifact': _artifact(info, exp_id, run_id, artifact)}
