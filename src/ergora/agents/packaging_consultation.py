"""The original supervised packaging question and the reply it can consume."""

from ergora.agents import native_sources
from ergora.definitions import bundles


REQUEST = 'packaging-request.json'
REPLY = 'packaging-reply.json'
_ACTION = 'review-standalone-packaging'
_EVIDENCE = ('input_id', 'candidate_id', 'candidate_import', 'pyproject_excerpt')
_REPLY = ('reply_to', 'candidate_id', 'recommendation', 'classification', 'basis')
_QUESTION = 'Does the proposed eager import require temporalio in the standalone CLI installation?'
_REQUESTER = {'kind': 'agent', 'id': 'ergora-structure-reviewer', 'version': '1.0.2',
              'digest': '4d64ef85205b186834c9456b9d914d43a2a3216df6775194d096297b1bcb373e'}
_RECIPIENT = {'kind': 'agent', 'id': 'ergora-dependency-reviewer', 'version': '1.0.1',
              'digest': '0d08e96f154d7948de2bda42e94b9c62c4176f0a98b0c488255546196d04bfcc'}


def binding(composition, inputs, selector):
    nodes = {node['path']: node for node in composition['instances']}
    route = nodes.get(selector, {})
    if (route.get('kind') != 'choose-agent' or route['parent'] != 'root' or len(route['branches']) != 1
            or len(route['depends_on']) != 1):
        raise ValueError('Packaging consultation requires one original supervised route and recipient')
    requester, = route['depends_on']
    recipient, = route['branches']
    analyzer, specialist = nodes[requester], nodes[recipient]
    source = {'node': requester.rsplit('/', 1)[1], 'output': 'result'}
    if (any(node['kind'] != 'agent' or node['parent'] != 'root' or node['role'] != 'reviewer'
            for node in (analyzer, specialist))
            or analyzer['ref'] != _REQUESTER or specialist['ref'] != _RECIPIENT
            or analyzer['inputs'] != {'task': {'input': 'task'}}
            or route['inputs'] != {'source': source}
            or specialist['inputs'] != {'task': source}
            or any(node['kind'] != 'join' for path, node in nodes.items()
                   if path not in {'root', selector, requester, recipient})):
        raise ValueError('Packaging consultation requires the exact packaged structure and dependency reviewer references')
    _evidence(inputs)
    return {'action': _ACTION, 'requester': requester, 'recipient': recipient, 'recipient_ref': specialist['ref']}


def _evidence(inputs):
    task = inputs.get('task')
    if (not isinstance(task, dict)
            or not all(isinstance(task.get(field), str) and task[field].strip() for field in _EVIDENCE)):
        raise ValueError('Packaging consultation requires exact input and candidate IDs, import and packaging excerpt')
    return {field: task[field] for field in _EVIDENCE}


def _answer(result):
    response = result.get('artifacts', {}).get('response')
    if not isinstance(response, str):
        raise ValueError('Packaging consultation requires a JSON response')
    return bundles.parse_json(response, 'packaging consultation response', finite=True, bounded=True)


def requester_task(task, selected):
    return {**task, 'packaging_consultation': {
        'action': selected['action'], 'question': _QUESTION,
        'route': selected['recipient'].rsplit('/', 1)[1], 'finish': 'none',
        'request_contract': 'If dependency review is needed, use the selected route and put a JSON object in '
                            'artifacts.response with question and the exact supplied input_id, candidate_id, '
                            'candidate_import and pyproject_excerpt. Otherwise select none.',
    }}


def request(receipt, route, checkpoint_sha, recovery, result, recipient_run_id):
    selected = receipt['packaging_consultation']
    evidence = _evidence(receipt['inputs'])
    if _answer(result) != {**evidence, 'question': _QUESTION}:
        raise ValueError('Packaging request differs from the original approved question or evidence')
    if route['selected'] != selected['recipient'] or route['source']['instance'] != selected['requester']:
        raise ValueError('Packaging request differs from its original reviewer and recipient')
    authority = {'recovery_sha256': receipt['recovery_sha256'], 'checkpoint_sha256': checkpoint_sha,
                 'decision_sha256': route['operator_decision_sha256'], 'original_requester': route['source'],
                 'recipient': selected['recipient'], 'recipient_ref': selected['recipient_ref'],
                 'recipient_run_id': recipient_run_id, 'deadline_monotonic_ns': recovery['deadline_monotonic_ns']}
    payload = {'action': selected['action'], 'question': _QUESTION, **evidence}
    return {'request_id': native_sources.sha([authority, payload]), 'authority': authority, 'payload': payload}


def task(issued):
    return {'request_id': issued['request_id'], **issued['payload'],
            'reply_contract': 'Put a JSON object in artifacts.response with reply_to equal to request_id, '
                              'the exact candidate_id, recommendation (hold or continue), classification and basis.'}


def reply(issued, attempt, result):
    if (attempt['instance'] != issued['authority']['recipient']
            or attempt['run_id'] != issued['authority']['recipient_run_id']):
        raise native_sources.ArtifactIdentityError('Packaging reply differs from the original recipient run')
    try:
        answer = _answer(result)
    except (ValueError, RecursionError):
        answer = None
    reason = None
    if (not isinstance(answer, dict) or answer.keys() != set(_REPLY)
            or not all(isinstance(answer[key], str) and answer[key].strip() for key in _REPLY)
            or answer['recommendation'] not in ('hold', 'continue')):
        reason = 'invalid_reply'
    elif answer['reply_to'] != issued['request_id'] or answer['candidate_id'] != issued['payload']['candidate_id']:
        reason = 'reply_identity_mismatch'
    return {'request_id': issued['request_id'], 'status': 'accepted' if reason is None else 'rejected',
            **{field: attempt[field] for field in ('instance', 'run_id', 'input_digest', 'result_sha256')},
            **({'reason': reason} if reason is not None else {})}


def verify(directory, name, expected, *, durable=False):
    observed = native_sources.packet(directory, name, confirm_durable=durable)
    if native_sources.encode(observed) != native_sources.encode(expected):
        raise native_sources.ArtifactIdentityError(f'Saved {name} differs from the original packaging consultation')
    return observed
