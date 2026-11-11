"""Frozen issue origins, usable by the standard-library native input readers.

These records describe observed data. They do not grant execution permission or
prove that an Agent consumed it. No credential lookup or network operation lives
in this module.
"""

import hashlib
import json
import math
import re
from urllib.parse import urlsplit


_APIS = {'github': 'https://api.github.com', 'gitlab': 'https://gitlab.com/api/v4'}


def tracker_identity(binding: dict) -> dict:
    """Resolve a configured origin without dropping its API path or host."""
    if (not isinstance(binding, dict) or not isinstance(binding.get('tool'), str)
            or binding['tool'] not in _APIS):
        raise ValueError('Select a GitHub or GitLab tracker binding to read issues')
    provider = binding['tool']
    allowed = {'tool', 'project', 'api_url', 'token_env'} | ({'api_version'} if provider == 'github' else set())
    project = binding.get('project')
    if (set(binding) - allowed or not isinstance(project, str) or len(project) > 300
            or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+', project)
            or (provider == 'github' and len(project.split('/')) != 2)
            or any(part in ('.', '..') for part in project.split('/'))):
        raise ValueError('Tracker project must name an ordinary repository namespace')
    for name, pattern in (('token_env', r'[A-Za-z_][A-Za-z0-9_]*'),
                          ('api_version', r'[0-9]{4}-[0-9]{2}-[0-9]{2}')):
        if name in binding and (not isinstance(binding[name], str) or not re.fullmatch(pattern, binding[name])):
            raise ValueError('Invalid tracker configuration field: ' + name)
    api = binding.get('api_url', _APIS[provider])
    if not isinstance(api, str) or not api or re.search(r'\s', api):
        raise ValueError('Tracker API requires a nonempty URL without whitespace')
    api = api.rstrip('/')
    url = urlsplit(api)
    if (not url.hostname or url.username is not None or url.password is not None or url.query or url.fragment
            or url.scheme not in ('http', 'https')
            or (url.scheme == 'http' and url.hostname not in ('127.0.0.1', '::1', 'localhost'))):
        raise ValueError('Tracker API requires HTTPS (HTTP only on loopback), without credentials, query or fragment')
    url.port
    return {'provider': provider, 'api_url': api, 'project': project}


def _object(value, fields: set) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Saved issue snapshot has invalid fields')


def _sha(value) -> bool:
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def _positive(value) -> bool:
    if type(value) is not int or value < 1:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def validate_snapshot(snapshot: dict) -> None:
    """Validate the complete persisted snapshot, independently of State or SDKs."""
    _object(snapshot, {'schema_version', 'sha256', 'first_observed_at', 'payload'})
    payload = snapshot['payload']
    _object(payload, {'schema_version', 'observation', 'tracker_binding'})
    observed = payload['observation']
    _object(observed, {'schema_version', 'source', 'issue', 'response', 'context_only', 'project', 'configuration_sha256'})
    _object(observed['project'], {'id', 'revision'})
    _object(observed['source'], {'provider', 'api_url', 'project', 'issue_id'})
    _object(observed['response'], {'sha256', 'etag'})
    issue = observed['issue']
    _object(issue, {'native_id', 'title', 'body', 'state', 'labels', 'web_url', 'updated_at'})
    if (any(type(value) is not int or value != 1 for value in
            (snapshot['schema_version'], payload['schema_version'], observed['schema_version']))
            or observed['context_only'] is not True
            or any(not _sha(value) for value in
                   (snapshot['sha256'], observed['configuration_sha256'], observed['response']['sha256']))
            or any(not isinstance(value, str) or not value for value in
                   (snapshot['first_observed_at'], observed['project']['id'], issue['web_url'], issue['updated_at']))
            or any(not _positive(value) for value in
                   (observed['project']['revision'], issue['native_id']))
            or not isinstance(observed['source']['issue_id'], str)
            or not re.fullmatch('[1-9][0-9]{0,19}', observed['source']['issue_id'])
            or any(not isinstance(issue[key], str) for key in ('title', 'body'))
            or issue['state'] not in ('open', 'opened', 'closed')
            or not isinstance(issue['labels'], list) or any(not isinstance(item, str) for item in issue['labels'])
            or len(set(issue['labels'])) != len(issue['labels'])
            or observed['response']['etag'] is not None and not isinstance(observed['response']['etag'], str)):
        raise ValueError('Saved issue snapshot has invalid values')
    source = {key: observed['source'][key] for key in ('provider', 'api_url', 'project')}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    if source != tracker_identity(payload['tracker_binding']) or digest != snapshot['sha256']:
        raise ValueError('Saved issue snapshot differs from its content identity or tracker source')


def bind_snapshot(snapshot: dict, project_id: str, binding: dict, tracker: dict) -> None:
    """Bind an observed origin to this execution selection and native tracker."""
    validate_snapshot(snapshot)
    observed = snapshot['payload']['observation']
    source = observed['source']
    if (observed['project']['id'] != project_id
            or {key: source[key] for key in ('provider', 'api_url', 'project')} != tracker_identity(binding)
            or tracker != {'kind': source['provider'], 'project': source['project'], 'issue_id': source['issue_id']}):
        raise ValueError('Issue snapshot source differs from the selected project, API or native tracker')
