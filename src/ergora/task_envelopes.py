"""Versioned formal task identities, readable by the standard-library native bridge.

The application owns graph/permission admission. This boundary seals its complete
static manifest bytes and selections to the unchanged legacy execution spec.
"""

import base64
import hashlib
import json


_KIND = 'composition-task-admission'


def identity(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


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


def wrap(spec: dict, composition: dict) -> dict:
    value = {'schema_version': 2, 'kind': _KIND, 'legacy_spec': spec, 'composition': composition}
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


def unwrap(document: dict) -> tuple[dict, dict | None]:
    """Return the legacy projection and its explicit admission; v1 stays untouched."""
    if document.get('kind') != _KIND and 'schema_version' not in document:
        return document, None
    if (set(document) != {'schema_version', 'kind', 'legacy_spec', 'composition', 'sha256'}
            or type(document['schema_version']) is not int or document['schema_version'] != 2
            or document['kind'] != _KIND):
        raise ValueError('Unsupported formal task admission envelope')
    if document['sha256'] != identity({key: value for key, value in document.items() if key != 'sha256'}):
        raise ValueError('Formal task admission envelope digest mismatch')
    composition = document['composition']
    if not isinstance(composition, dict) or set(composition) != {'manifest', 'root', 'preview_sha256', 'review_instance', 'members', 'diversity'}:
        raise ValueError('Invalid formal composition selection')
    manifest_identity(composition['manifest'])
    graph = json.loads(base64.b64decode(composition['manifest']['files']['composition.json']['content_base64'], validate=True))
    if graph['root'] != composition['root'] or graph['preview_sha256'] != composition['preview_sha256']:
        raise ValueError('Formal composition identity differs from its frozen graph')
    instances = {item['path']: item for item in graph['instances']}
    position = composition['review_instance']
    if not isinstance(position, str) or position not in instances or instances[position]['kind'] != 'workflow':
        raise ValueError('Invalid formal composition review subtree')
    expected = {path: item for path, item in instances.items() if item['kind'] == 'agent' and path.startswith(position + '/')}
    members = composition['members']
    if not expected or not isinstance(members, dict) or set(members) != expected.keys():
        raise ValueError('Formal composition member selection differs from its review subtree')
    for path, member in members.items():
        if (not isinstance(member, dict) or set(member) != {'role', 'binding', 'requested_binding', 'backend_reason', 'mode', 'policy'}
                or member['role'] != 'reviewer' or expected[path]['role'] != 'reviewer'
                or member['mode'] not in ('text-only', 'task-mcp')
                or not isinstance(member['backend_reason'], str) or not member['backend_reason'].strip()):
            raise ValueError('Invalid formal composition member: ' + path)
        _binding(member['binding'])
        _binding(member['requested_binding'])
        if member['requested_binding'] != expected[path]['backend_request']:
            raise ValueError('Formal composition requested binding differs from its frozen graph')
        _policy(member['policy'], member['mode'])
    diversity = composition['diversity']
    if (not isinstance(diversity, dict)
            or set(diversity) - {'policy', 'reason', 'implementer_backend', 'same_backend_members'}
            or not {'policy', 'implementer_backend', 'same_backend_members'} <= diversity.keys()
            or diversity['policy'] not in ('prefer-distinct', 'require-distinct', 'allow-same')
            or not isinstance(diversity['implementer_backend'], str) or not diversity['implementer_backend'].strip()
            or not isinstance(diversity['same_backend_members'], list)
            or any(not isinstance(path, str) for path in diversity['same_backend_members'])
            or ('reason' in diversity and (not isinstance(diversity['reason'], str) or not diversity['reason'].strip()))):
        raise ValueError('Invalid formal composition diversity')
    same = sorted(path for path, member in members.items() if member['binding']['tool'] == diversity['implementer_backend'])
    if (sorted(diversity['same_backend_members']) != same
            or (same and diversity['policy'] == 'require-distinct')
            or (same and diversity['policy'] == 'prefer-distinct' and not diversity.get('reason'))):
        raise ValueError('Formal composition diversity differs from its selected member backends')
    return document['legacy_spec'], composition


def summary(document: dict) -> dict:
    """Project an already verified envelope without re-decoding its full asset tree."""
    composition = document['composition']
    return {'envelope_sha256': document['sha256'], 'manifest_digest': composition['manifest']['digest'],
            'root': composition['root'], 'review_instance': composition['review_instance'],
            'members': composition['members'], 'diversity': composition['diversity'], 'runtime_supported': False}
