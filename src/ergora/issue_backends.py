"""Read-only issue protocols; each implementation owns its native identity mapping."""

from abc import ABC, abstractmethod
import hashlib
from http.client import HTTPException
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from . import components, contracts


_RESPONSE_LIMIT = 1_048_576


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class IssueBackend(ABC):
    default_api_url: str
    token_header: str

    def __init__(self, binding: dict):
        contracts.validate(binding, components.COMPONENTS[binding['tool']]['configuration'], 'Tracker binding')
        self.binding = dict(binding)
        self.api_url = binding.get('api_url', self.default_api_url).rstrip('/')
        url = urlsplit(self.api_url)
        # The connection is trusted project configuration, never an issue-text URL.
        if (not url.hostname or url.username is not None or url.password is not None or url.query or url.fragment
                or url.scheme not in ('http', 'https')
                or (url.scheme == 'http' and url.hostname not in ('127.0.0.1', '::1', 'localhost'))):
            raise ValueError('Tracker API requires HTTPS (HTTP only on loopback), without credentials, query or fragment')
        url.port  # Validate an explicitly supplied port before sending credentials.
        if any(part in ('.', '..') for part in binding['project'].split('/')):
            raise ValueError('Tracker project must name an ordinary repository namespace')

    def diagnostics(self) -> dict:
        variable = self.binding.get('token_env')
        present = not variable or bool(os.environ.get(variable))
        return {'installed': True, 'authentication': 'not_required' if not variable else
                'credentials_present' if present else 'credentials_missing',
                'task_availability': 'not_checked' if present else 'blocked',
                'remediation': ['Use issue show for an explicit read; credential presence does not verify access or quota.']}

    @abstractmethod
    def path(self, issue_id: str) -> str:
        """Address a repository number or project iid, never a global issue ID."""

    def headers(self) -> dict:
        headers = {'Accept': 'application/json', 'User-Agent': 'Ergora-issue-reader'}
        variable = self.binding.get('token_env')
        if variable:
            token = os.environ.get(variable)
            if not token:
                raise ValueError('Missing tracker credential environment variable: ' + variable)
            if not all(33 <= ord(character) <= 126 for character in token):
                raise ValueError('Tracker credential must be a single printable ASCII header value: ' + variable)
            headers[self.token_header] = self.token_value(token)
        return headers

    def token_value(self, token: str) -> str:
        return token

    @abstractmethod
    def issue(self, document: dict) -> tuple[int, dict]:
        """Return the local issue number and a common, lossless-text observation."""

    def read(self, issue_id: str) -> dict:
        if not isinstance(issue_id, str) or not re.fullmatch(r'[1-9][0-9]{0,19}', issue_id):
            raise ValueError('Issue ID must be a positive repository number or project iid')
        request = Request(self.api_url + self.path(issue_id), headers=self.headers(), method='GET')
        try:
            # No redirect, retry, paging, background polling or write operation.
            with build_opener(_NoRedirect).open(request, timeout=20) as response:
                if response.status != 200:
                    raise ValueError(f'Tracker read expected HTTP 200, received {response.status}')
                raw = response.read(_RESPONSE_LIMIT + 1)
                etag = response.headers.get('ETag')
                remaining = response.length
        except HTTPError as error:
            error.close()
            raise ValueError(f'Tracker read failed with HTTP {error.code}') from None
        except (URLError, OSError, HTTPException) as error:
            raise ValueError('Tracker read unavailable: ' + type(error).__name__) from None
        if len(raw) > _RESPONSE_LIMIT:
            raise ValueError('Complete tracker response exceeds 1 MiB; no observation was returned')
        if remaining not in (None, 0):
            raise ValueError('Tracker response ended before its declared content length')
        try:
            document = json.loads(raw)
            if not isinstance(document, dict) or not isinstance(document['labels'], list):
                raise ValueError('Invalid issue labels')
            number, issue = self.issue(document)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ValueError('Tracker returned an invalid issue document') from None
        if type(number) is not int or number != int(issue_id):
            raise ValueError('Tracker returned a different issue number or iid')
        observed = {'schema_version': 1, 'source': {'provider': self.binding['tool'], 'api_url': self.api_url,
                    'project': self.binding['project'], 'issue_id': issue_id}, 'issue': issue,
                    'response': {'sha256': hashlib.sha256(raw).hexdigest(), 'etag': etag}, 'context_only': True}
        contracts.validate(observed, contracts.ISSUE_OBSERVATION, 'Issue observation')
        return observed


class GitHubBackend(IssueBackend):
    default_api_url = 'https://api.github.com'
    token_header = 'Authorization'

    def path(self, issue_id: str) -> str:
        return '/repos/' + quote(self.binding['project'], safe='/') + '/issues/' + issue_id

    def headers(self) -> dict:
        return {**super().headers(), 'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': self.binding.get('api_version', '2022-11-28')}

    def token_value(self, token: str) -> str:
        return 'Bearer ' + token

    def issue(self, document: dict) -> tuple[int, dict]:
        if 'pull_request' in document:
            raise ValueError('Select an issue, not a pull request')
        return document['number'], {'native_id': document['id'], 'title': document['title'],
            'body': document['body'] if document['body'] is not None else '', 'state': document['state'],
            'labels': sorted({item if isinstance(item, str) else item['name'] for item in document['labels']}),
            'web_url': document['html_url'], 'updated_at': document['updated_at']}


class GitLabBackend(IssueBackend):
    default_api_url = 'https://gitlab.com/api/v4'
    token_header = 'PRIVATE-TOKEN'

    def path(self, issue_id: str) -> str:
        return '/projects/' + quote(self.binding['project'], safe='') + '/issues/' + issue_id

    def issue(self, document: dict) -> tuple[int, dict]:
        if document['issue_type'] != 'issue':
            raise ValueError('Only ordinary project issues are supported')
        return document['iid'], {'native_id': document['id'], 'title': document['title'],
            'body': document['description'] if document['description'] is not None else '', 'state': document['state'],
            'labels': sorted(set(document['labels'])), 'web_url': document['web_url'], 'updated_at': document['updated_at']}


_BACKENDS = {'github': GitHubBackend, 'gitlab': GitLabBackend}


def for_binding(binding: dict) -> IssueBackend:
    try:
        implementation = _BACKENDS[binding['tool']]
    except KeyError:
        raise ValueError('Select a GitHub or GitLab tracker binding to read issues') from None
    return implementation(binding)
