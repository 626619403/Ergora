"""Versioned formal task identities, readable by the standard-library native bridge.

The application owns graph/permission admission. This boundary seals its complete
static manifest bytes and selections to the unchanged legacy execution spec.
"""

import base64
import hashlib
import json

from .review_dags import ReviewDAG, WorkDelivery, preparation_members, require_root_task
from .issue_sources import validate_snapshot


_KIND = 'composition-task-admission'
COMPOSITION_SUBMIT = 'ergora_composition_submit'
REQUIREMENTS_SUBMIT = 'ergora_requirements_submit'
REQUIREMENTS_POLL = 'ergora_requirements_poll'
DAG_SUBMIT = 'ergora_review_dag_submit'
DAG_POLL = 'ergora_review_dag_poll'
WORK_SUBMIT = 'ergora_work_delivery_submit'
WORK_POLL = 'ergora_work_delivery_poll'


def identity(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def matches_context(spec: dict, context: dict, admission: dict | None = None) -> bool:
    """Bind a stage projection to its task/profile and optional complete admission.

    The original activity and persisted readers own their request-SHA checks.
    Both the SDK publisher and versioned readers use this additional identity.
    """
    return (context.get('task_id') == spec['request']['task_id']
            and context.get('profile_sha256') == spec['profile_sha256']
            and identity(context['spec']) == identity(spec)
            and (admission is None or identity(context.get('admission')) == identity(admission)))


def manifest_identity(snapshot: dict) -> str:
    """Check every carried byte using the original complete-tree identity rule."""
    if set(snapshot) != {'digest', 'files'} or not isinstance(snapshot['files'], dict):
        raise ValueError('Invalid frozen composition manifest')
    if not 1 <= len(snapshot['files']) <= 500:
        raise ValueError('Frozen composition manifest requires 1–500 files')
    inventory, total = {}, 0
    for name, item in snapshot['files'].items():
        if set(item) != {'content_base64', 'executable_bits'}:
            raise ValueError('Invalid frozen composition file: ' + name)
        content = base64.b64decode(item['content_base64'], validate=True)
        total += len(content)
        if total > 10_000_000 or type(item['executable_bits']) is not int or item['executable_bits'] & ~0o111:
            raise ValueError('Frozen composition content exceeds its original file-tree contract')
        inventory[name] = {'sha256': hashlib.sha256(content).hexdigest(), 'executable_bits': item['executable_bits']}
    digest = hashlib.sha256(json.dumps(dict(sorted(inventory.items())), sort_keys=True).encode()).hexdigest()
    if digest != snapshot['digest']:
        raise ValueError('Frozen composition manifest bytes differ from their original digest')
    return digest


def wrap(spec: dict, composition: dict, issue_source: dict | None = None) -> dict:
    version = (8 if 'preparation' in composition else 7 if issue_source is not None else
               6 if composition.get('execution', {}).get('protocol') == 'work-units-v2' else
               5 if 'execution' in composition else 4 if 'review_protocol' in composition else
               3 if any('review_requirement' in member for member in composition['members'].values()) else 2)
    value = {'schema_version': version, 'kind': _KIND, 'legacy_spec': spec, 'composition': composition}
    if issue_source is not None:
        value['issue_source'] = issue_source
    return {**value, 'sha256': identity(value)}


def _binding(value: dict) -> None:
    """Check persisted structure without asking a mutable backend catalog."""
    if (not isinstance(value, dict) or set(value) - {'tool', 'model', 'sandbox'}
            or not isinstance(value.get('tool'), str) or not value['tool'].strip() or '\x00' in value['tool']):
        raise ValueError('Invalid formal composition binding')
    for key in ('model', 'sandbox'):
        if key in value and (not isinstance(value[key], str) or not value[key].strip() or '\x00' in value[key]):
            raise ValueError('Invalid formal composition binding field: ' + key)
    if 'sandbox' in value and value['sandbox'] not in ('read-only', 'workspace-write', 'current-container'):
        raise ValueError('Invalid formal composition sandbox request')


def _policy(value: dict, mode: str) -> None:
    """The v2 record describes restricted calls, never an executable grant."""
    fields = {'mode', 'basis', 'model_tools', 'native_companion_tools', 'resources', 'ambient_configuration',
              'authentication', 'host_isolation', 'capabilities', 'infrastructure'}
    if (not isinstance(value, dict) or set(value) != fields or value['mode'] != mode
            or not isinstance(value['capabilities'], dict)
            or any(not isinstance(value[key], str) or not value[key].strip()
                   for key in fields - {'capabilities', 'native_companion_tools'})
            or not isinstance(value['native_companion_tools'], list)
            or any(not isinstance(name, str) or not name.strip() for name in value['native_companion_tools'])):
        raise ValueError('Invalid formal composition member policy')
    capabilities = value['capabilities']
    if set(capabilities) != {'inline_material', 'fixed_resource_read', 'workspace_read', 'write', 'shell',
                             'tool_network_origins', 'task_mcp', 'external_mcp', 'backend_sandbox', 'host_isolation'}:
        raise ValueError('Invalid formal composition capability inventory')
    for capability in capabilities.values():
        if not isinstance(capability, dict) or capability.get('status') not in ('enforced', 'advisory', 'unsupported'):
            raise ValueError('Invalid formal composition capability record')
    if mode == 'workspace-task-mcp':
        if (capabilities['inline_material'].get('status') != 'enforced'
                or capabilities['fixed_resource_read'].get('status') != 'enforced'
                or capabilities['task_mcp'] != {'status': 'enforced', 'tools': ['list', 'read']}
                or capabilities['shell'] != {'status': 'enforced', 'effective': True}
                or any(capabilities[key].get('status') != 'advisory' for key in
                       ('workspace_read', 'write', 'tool_network_origins'))
                or capabilities['backend_sandbox'] != {'status': 'advisory', 'requested': 'current-container',
                    'effective': 'current-container', 'scope': 'Explicit trusted current-user execution; no inter-agent OS isolation'}
                or capabilities['external_mcp'] != {'status': 'unsupported', 'effective': []}
                or capabilities['host_isolation'] != {'status': 'unsupported', 'effective': 'trusted user/process boundary'}):
            raise ValueError('Invalid trusted workspace capability contract')
        return
    for name, empty in (('workspace_read', []), ('write', []), ('shell', False),
                        ('tool_network_origins', []), ('external_mcp', [])):
        if identity(capabilities[name]) != identity({'status': 'unsupported', 'effective': empty}):
            raise ValueError('Formal composition restricted policy cannot grant ' + name)
    inline = capabilities['inline_material']
    fixed = capabilities['fixed_resource_read']
    isolation = capabilities['host_isolation']
    sandbox = capabilities['backend_sandbox']
    task = mode == 'task-mcp'
    if (set(inline) != {'status', 'effective', 'scope'} or inline['status'] != 'enforced'
            or any(not isinstance(inline[key], str) or not inline[key].strip() for key in ('effective', 'scope'))
            or set(fixed) != {'status', 'effective'} or fixed['status'] != ('enforced' if task else 'unsupported')
            or (task and (not isinstance(fixed['effective'], str) or not fixed['effective'].strip()))
            or (not task and fixed['effective'] != [])
            or capabilities['task_mcp'] != {'status': 'enforced' if task else 'unsupported', 'tools': ['list', 'read'] if task else []}
            or set(isolation) != {'status', 'effective'} or isolation['status'] != 'unsupported'
            or not isinstance(isolation['effective'], str) or not isolation['effective'].strip()
            or set(sandbox) != {'status', 'requested', 'effective', 'scope'}
            or not isinstance(sandbox['scope'], str) or not sandbox['scope'].strip()
            or sandbox['status'] not in ('advisory', 'unsupported')
            or sandbox['requested'] not in (None, 'read-only', 'workspace-write', 'current-container')
            or (sandbox['status'] == 'advisory' and sandbox['effective'] != 'read-only')
            or (sandbox['status'] == 'unsupported' and (sandbox['requested'] is not None or sandbox['effective'] is not None))):
        raise ValueError('Formal composition capabilities differ from their restricted mode')


def manifest_graph(snapshot: dict) -> dict:
    try:
        return json.loads(base64.b64decode(snapshot['files']['composition.json']['content_base64'], validate=True))
    except RecursionError as error:
        raise ValueError('Frozen composition JSON exceeds the decoder nesting limit') from error


def review_members(composition: dict) -> dict:
    """Select direct-input reviewers and the bounded explicit parallel shape.

    Creation and history may retain other valid static graphs. Submission and
    the executor share this narrower support contract; backend/resource checks
    still belong to the actual execution admission.
    """
    graph = manifest_graph(composition['manifest'])
    if composition.get('review_protocol') == 'dag-v1':
        dag = review_dag(composition)
        if not any(member['review_requirement'] == 'required' for member in composition['members'].values()):
            raise ValueError('Formal review requires at least one required reviewer')
        for path in dag.members:
            dag.input_ports(path)
        return dag.members
    if graph['schema_version'] != 1:
        if (graph['schema_version'] != 2
                or any(member.get('review_requirement') not in ('required', 'advisory')
                       for member in composition['members'].values())):
            raise ValueError('Formal tasks do not yet support review requirements without a v3 selection')
        if not any(member['review_requirement'] == 'required' for member in composition['members'].values()):
            raise ValueError('Formal review requires at least one required reviewer')
    instances = {item['path']: item for item in graph['instances']}
    members = {path: instances[path] for path in sorted(composition['members'])}
    for leaf in members.values():
        if (leaf['role'] != 'reviewer' or leaf['permissions']['write']
                or leaf['permissions']['shell'] or leaf['permissions']['network']):
            raise ValueError('Composition review requires a read-only reviewer without shell or network')
        require_root_task(instances, leaf)
    if len(members) == 1 and graph['schema_version'] == 1:
        return members

    covered = {}

    def coverage(path: str, port: str, active: frozenset) -> set:
        if path in active:
            raise ValueError('Composition review output cycle')
        if (path, port) in covered:
            return covered[path, port]
        node = instances[path]
        if port not in node['outputs']:
            raise ValueError('Composition review has an unknown output port')
        if node['kind'] == 'agent':
            result = {path}
        elif node['kind'] == 'workflow':
            origin = node['outputs'][port]
            if 'input' in origin:
                raise ValueError('Composition review output must refer to an executed reviewer')
            result = coverage(path + '/' + origin['node'], origin['output'], active | {path})
        else:
            if node['join'] != 'all' or not node['depends_on']:
                raise ValueError('Composition review requires a nonempty all-join')
            result = set()
            for dependency in node['depends_on']:
                for output in instances[dependency]['outputs']:
                    result |= coverage(dependency, output, active | {path})
        covered[path, port] = result
        return result

    selected = instances[composition['review_instance']]
    if len(selected['outputs']) != 1:
        raise ValueError('Parallel composition review requires one explicit all-join output')
    origin = next(iter(selected['outputs'].values()))
    if 'input' in origin:
        raise ValueError('Parallel composition review output must refer to an explicit all-join')
    terminal = instances[selected['path'] + '/' + origin['node']]
    if (terminal['kind'] != 'join' or terminal['join'] != 'all'
            or coverage(selected['path'], next(iter(selected['outputs'])), frozenset()) != members.keys()):
        raise ValueError('Parallel composition review requires an explicit all-join covering every reviewer leaf')
    scopes = {}
    for leaf in members.values():
        for scope in leaf['concurrency_scopes']:
            if (not isinstance(scope['path'], str) or type(scope['limit']) is not int or scope['limit'] < 1
                    or scopes.setdefault(scope['path'], scope['limit']) != scope['limit']):
                raise ValueError('Composition review concurrency scopes must have consistent positive limits')
    return members


def review_dag(composition: dict):
    """The selected review projection may consume only the frozen work terminal."""
    from .review_dags import StageDAG

    graph = manifest_graph(composition['manifest'])
    if 'execution' not in composition:
        return ReviewDAG(graph, composition['review_instance'])
    work = StageDAG(graph, composition['execution']['instance'], role='implementer')
    return StageDAG(graph, composition['review_instance'], external=work)


def work_delivery(composition: dict, spec: dict) -> WorkDelivery:
    return WorkDelivery(manifest_graph(composition['manifest']), composition['execution'],
        composition['review_instance'], spec['request']['input']['work_units'], preparation=composition.get('preparation'))


def outcome_reference_state(outcome: dict | None, job: dict) -> str:
    """Compare complete original job references online and in offline packets."""
    if outcome is None:
        return 'not_recorded'
    stage, reference = job['stage'], None
    if stage in ('verify', 'review'):
        receipt = outcome.get('verification' if stage == 'verify' else 'review')
        if receipt is not None:
            reference = {'stage': stage, 'job_id': receipt['job_id'], 'job_sha256': receipt['job_sha256'],
                         'receipt_sha256': identity(receipt)}
    elif stage.startswith('review:'):
        aggregate = outcome.get('review')
        if aggregate is not None and aggregate.get('kind') == 'composition-review-aggregate':
            if aggregate.get('schema_version') not in (1, 2):
                raise ValueError('Unsupported composition review aggregate')
            reference = aggregate['members'].get(stage.removeprefix('review:'))
    if reference is None:
        return 'not_recorded'
    if any(reference[key] != job[key] for key in ('stage', 'job_id', 'job_sha256')):
        return 'differs'
    if job['receipt'] is None:
        return 'unavailable'
    return 'matches' if reference['receipt_sha256'] == job['receipt_sha256'] else 'differs'


def unwrap(document: dict) -> tuple[dict, dict | None]:
    """Return the legacy projection and its explicit admission; v1 stays untouched."""
    if not isinstance(document, dict):
        raise ValueError('Formal task input must be a JSON object')
    if document.get('kind') != _KIND and 'schema_version' not in document:
        return document, None
    fields = {'schema_version', 'kind', 'legacy_spec', 'composition', 'sha256'}
    if document.get('schema_version') == 7 or (document.get('schema_version') == 8 and 'issue_source' in document):
        fields.add('issue_source')
    if (set(document) != fields
            or type(document['schema_version']) is not int or document['schema_version'] not in (2, 3, 4, 5, 6, 7, 8)
            or document['kind'] != _KIND):
        raise ValueError('Unsupported formal task admission envelope')
    if document['sha256'] != identity({key: value for key, value in document.items() if key != 'sha256'}):
        raise ValueError('Formal task admission envelope digest mismatch')
    composition = document['composition']
    fields = {'manifest', 'root', 'preview_sha256', 'review_instance', 'members', 'diversity'}
    if document['schema_version'] in (4, 5, 6, 7, 8):
        fields.add('review_protocol')
    if document['schema_version'] in (5, 6, 7, 8):
        fields.add('execution')
    if document['schema_version'] == 8:
        fields.add('preparation')
    if (not isinstance(composition, dict) or set(composition) != fields
            or (document['schema_version'] in (4, 5, 6, 7, 8) and composition['review_protocol'] != 'dag-v1')):
        raise ValueError('Invalid formal composition selection')
    manifest_identity(composition['manifest'])
    graph = manifest_graph(composition['manifest'])
    requirements = document['schema_version'] in (3, 4, 5, 6, 7, 8)
    if document['schema_version'] == 3 and graph['schema_version'] != 2:
        raise ValueError('Formal v3 admission requires a versioned review requirements graph')
    if graph['root'] != composition['root'] or graph['preview_sha256'] != composition['preview_sha256']:
        raise ValueError('Formal composition identity differs from its frozen graph')
    instances = {}
    for item in graph['instances']:
        path = item['path']
        if not isinstance(path, str) or not path or path in instances:
            raise ValueError('Formal composition instance paths must be nonempty unique strings')
        instances[path] = item
    position = composition['review_instance']
    if not isinstance(position, str) or position not in instances or instances[position]['kind'] != 'workflow':
        raise ValueError('Invalid formal composition review subtree')
    expected = {path: item for path, item in instances.items() if item['kind'] == 'agent' and path.startswith(position + '/')}
    members = composition['members']
    if not expected or not isinstance(members, dict) or set(members) != expected.keys():
        raise ValueError('Formal composition member selection differs from its review subtree')
    for path, member in members.items():
        fields = {'role', 'binding', 'requested_binding', 'backend_reason', 'mode', 'policy'}
        if requirements:
            fields.add('review_requirement')
        if (not isinstance(member, dict) or set(member) != fields
                or member['role'] != 'reviewer' or expected[path]['role'] != 'reviewer'
                or member['mode'] not in ('text-only', 'task-mcp')
                or not isinstance(member['backend_reason'], str) or not member['backend_reason'].strip()):
            raise ValueError('Invalid formal composition member: ' + path)
        if requirements and (member['review_requirement'] not in ('required', 'advisory')
                or member['review_requirement'] != expected[path].get('review_requirement', 'required')):
            raise ValueError('Formal review requirement differs from its frozen graph: ' + path)
        _binding(member['binding'])
        _binding(member['requested_binding'])
        if member['requested_binding'] != expected[path]['backend_request']:
            raise ValueError('Formal composition requested binding differs from its frozen graph')
        _policy(member['policy'], member['mode'])
    diversity = composition['diversity']
    if document['schema_version'] == 8:
        preparation = composition['preparation']
        if (not isinstance(preparation, dict)
                or set(preparation) != {'protocol', 'inventory', 'plan', 'mode', 'repository_paths', 'members'}
                or preparation['protocol'] != 'preparation-v1'
                or preparation['mode'] not in ('text-only', 'task-mcp')
                or not isinstance(preparation['members'], dict)
                or any(not isinstance(preparation[stage], str) for stage in ('inventory', 'plan'))):
            raise ValueError('Invalid formal preparation selection')
        expected = {leaf['path']: leaf for leaf in preparation_members(graph, preparation).values()}
        if preparation['members'].keys() != expected.keys():
            raise ValueError('Frozen preparation members differ from the selected stage leaves')
        for path, member in preparation['members'].items():
            if (not isinstance(member, dict)
                    or set(member) != {'role', 'binding', 'requested_binding', 'backend_reason', 'mode', 'policy'}
                    or member['role'] != expected[path]['role'] or member['mode'] != preparation['mode']
                    or not isinstance(member['backend_reason'], str) or not member['backend_reason'].strip()
                    or member['requested_binding'] != expected[path]['backend_request']):
                raise ValueError('Invalid frozen preparation member: ' + path)
            _binding(member['binding'])
            _binding(member['requested_binding'])
            _policy(member['policy'], member['mode'])
    if document['schema_version'] in (5, 6, 7, 8):
        execution = composition['execution']
        if (not isinstance(execution, dict) or set(execution) != {'protocol', 'instance', 'assignments', 'mode', 'members'}
                or execution['protocol'] != ('work-units-v2' if document['schema_version'] in (6, 7, 8) else 'work-units-v1')
                or execution['mode'] != 'workspace-task-mcp'
                or not isinstance(execution['assignments'], dict) or not isinstance(execution['members'], dict)):
            raise ValueError('Invalid formal work execution selection')
        delivery = work_delivery(composition, document['legacy_spec'])
        if execution['members'].keys() != delivery.work.members.keys():
            raise ValueError('Frozen work members differ from the selected work subtree')
        for path, member in execution['members'].items():
            if (set(member) != {'role', 'binding', 'requested_binding', 'backend_reason', 'mode', 'policy'}
                    or member['role'] != 'implementer' or member['mode'] != execution['mode']
                    or not isinstance(member['backend_reason'], str) or not member['backend_reason'].strip()
                    or member['requested_binding'] != delivery.work.members[path]['backend_request']):
                raise ValueError('Invalid frozen work member: ' + path)
            _binding(member['binding'])
            _binding(member['requested_binding'])
            _policy(member['policy'], member['mode'])
        if (not isinstance(diversity, dict)
                or set(diversity) - {'policy', 'reason', 'implementer_backends', 'same_backend_members'}
                or not {'policy', 'implementer_backends', 'same_backend_members'} <= diversity.keys()):
            raise ValueError('Invalid formal work diversity')
        tools = sorted({member['binding']['tool'] for member in execution['members'].values()})
        if diversity.get('implementer_backends') != tools:
            raise ValueError('Diversity must compare all actual work backends')
        # Keep the legacy diversity validator and its exact old shape below.
        normalized = dict(diversity)
        normalized.pop('implementer_backends')
        normalized['implementer_backend'] = tools[0]
    else:
        tools = [diversity.get('implementer_backend')]
        normalized = diversity
    diversity = normalized
    if (not isinstance(diversity, dict)
            or set(diversity) - {'policy', 'reason', 'implementer_backend', 'same_backend_members'}
            or not {'policy', 'implementer_backend', 'same_backend_members'} <= diversity.keys()
            or diversity['policy'] not in ('prefer-distinct', 'require-distinct', 'allow-same')
            or not isinstance(diversity['implementer_backend'], str) or not diversity['implementer_backend'].strip()
            or not isinstance(diversity['same_backend_members'], list)
            or any(not isinstance(path, str) for path in diversity['same_backend_members'])
            or ('reason' in diversity and (not isinstance(diversity['reason'], str) or not diversity['reason'].strip()))):
        raise ValueError('Invalid formal composition diversity')
    same = sorted(path for path, member in members.items() if member['binding']['tool'] in tools)
    if (sorted(diversity['same_backend_members']) != same
            or (same and diversity['policy'] == 'require-distinct')
            or (same and diversity['policy'] == 'prefer-distinct' and not diversity.get('reason'))):
        raise ValueError('Formal composition diversity differs from its selected member backends')
    if document['schema_version'] in (4, 5, 6, 7, 8):
        review_members(composition)
    if document['schema_version'] == 8:
        # SKILL.md and ordinary resources are already complete inline text.
        # Other Skill files require the fixed MCP resource reader; naming an
        # attachment in a prompt is not byte delivery in text-only mode.
        selected = {**members, **composition['execution']['members'], **composition['preparation']['members']}
        for path, member in selected.items():
            if member['mode'] != 'text-only':
                continue
            for resource in instances[path]['resources']:
                if resource['kind'] != 'skill':
                    continue
                for origin in resource['sources']:
                    ref = origin['definition']
                    prefix = 'assets/' + ref['kind'] + '-definitions/objects/' + ref['digest'] + '/' + origin['path'] + '/'
                    if any(name.startswith(prefix) and name != prefix + 'SKILL.md'
                           for name in composition['manifest']['files']):
                        raise ValueError('Complete Skill attachments require task-mcp mode: ' + path)
    if 'issue_source' in document:
        saved = document['issue_source']
        validate_snapshot(saved)
        source = saved['payload']['observation']['source']
        if document['legacy_spec']['request']['tracker'] != {
                'kind': source['provider'], 'project': source['project'], 'issue_id': source['issue_id']}:
            raise ValueError('Formal issue source differs from its original native tracker')
    return document['legacy_spec'], composition


def issue_inventory_context(document: dict, expected_sha: str | None) -> dict:
    """Build the complete first context of an already validated source input.

    Publication and v7 execution share these bytes; neither imports the other's
    native runtime. Later dynamic stages retain their original material limits.
    """
    spec = document['legacy_spec']
    request = spec['request']
    context = {'task_id': request['task_id'], 'request_sha256': spec['request_sha256'],
        'profile_sha256': spec['profile_sha256'], 'spec': spec, 'stage': 'inventory',
        'expected_candidate_sha': expected_sha, 'unit': None, 'dependencies': {},
        'author_ids': [], 'author_sessions': [],
        'job_id': request['task_id'] + '-' + identity({'stage': 'inventory'})[:24],
        'admission': document}
    if len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')) > 1_000_000:
        raise ValueError('Complete issue inventory context exceeds 1,000,000 bytes; split the task')
    return context


def summary(document: dict) -> dict:
    """Summarize verified history; runtime support describes shape, not readiness."""
    composition = document['composition']
    try:
        review_members(composition)
    except ValueError:
        supported = False
    else:
        supported = True
    return {'envelope_sha256': document['sha256'], 'manifest_digest': composition['manifest']['digest'],
            'root': composition['root'], 'review_instance': composition['review_instance'],
            **({'review_protocol': composition['review_protocol']} if 'review_protocol' in composition else {}),
            **({'execution': composition['execution']} if 'execution' in composition else {}),
            **({'preparation': composition['preparation']} if 'preparation' in composition else {}),
            'members': composition['members'], 'diversity': composition['diversity'], 'runtime_supported': supported,
            **({'issue_source': {'snapshot_sha256': document['issue_source']['sha256'],
                'source': document['issue_source']['payload']['observation']['source'],
                'native_id': document['issue_source']['payload']['observation']['issue']['native_id'],
                'observed_project': document['issue_source']['payload']['observation']['project']}}
               if 'issue_source' in document else {})}
