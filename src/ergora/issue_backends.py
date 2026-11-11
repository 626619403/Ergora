"""Issue protocols; each implementation owns its native identity and request paths."""

from abc import ABC, abstractmethod
import hashlib
from http.client import HTTPException
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from . import components, contracts, issue_sources


_RESPONSE_LIMIT = 1_048_576


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class IssueBackend(ABC):
    token_header: str

    def __init__(self, binding: dict):
        contracts.validate(binding, components.COMPONENTS[binding['tool']]['configuration'], 'Tracker binding')
        self.binding = dict(binding)
        self.api_url = issue_sources.tracker_identity(binding)['api_url']
        self._write_headers = None

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

    @staticmethod
    def _identifier(issue_id: str) -> None:
        if not isinstance(issue_id, str) or not re.fullmatch(r'[1-9][0-9]{0,19}', issue_id):
            raise ValueError('Issue ID must be a positive repository number or project iid')

    def _request(self, method: str, path: str, body: dict | None = None, *, authenticated: bool = False):
        headers = self.headers() if not authenticated else self._authenticated_headers()
        encoded = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if encoded is not None:
            headers = {**headers, 'Content-Type': 'application/json'}
        request = Request(self.api_url + path, data=encoded, headers=headers, method=method)
        operation, expected = ('read', 200) if method == 'GET' else ('write', 201)
        try:
            # A write is exactly one HTTP attempt: no redirect or automatic retry.
            with build_opener(_NoRedirect).open(request, timeout=20) as response:
                if response.status != expected:
                    raise ValueError(f'Tracker {operation} expected HTTP {expected}, received {response.status}')
                raw = response.read(_RESPONSE_LIMIT + 1)
                response_headers = response.headers
                remaining = response.length
        except HTTPError as error:
            error.close()
            raise ValueError(f'Tracker {operation} failed with HTTP {error.code}') from None
        except (URLError, OSError, HTTPException) as error:
            raise ValueError(f'Tracker {operation} unavailable: ' + type(error).__name__) from None
        if len(raw) > _RESPONSE_LIMIT:
            raise ValueError('Complete tracker response exceeds 1 MiB')
        if remaining not in (None, 0):
            raise ValueError('Tracker response ended before its declared content length')
        return raw, response_headers

    def read(self, issue_id: str, *, authenticated: bool = False) -> dict:
        self._identifier(issue_id)
        raw, headers = self._request('GET', self.path(issue_id), authenticated=authenticated)
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
                    'response': {'sha256': hashlib.sha256(raw).hexdigest(), 'etag': headers.get('ETag')}, 'context_only': True}
        contracts.validate(observed, contracts.ISSUE_OBSERVATION, 'Issue observation')
        return observed

    def _authenticated_headers(self) -> dict:
        if self._write_headers is None:
            if not self.binding.get('token_env'):
                raise ValueError('Issue writeback requires an external token_env binding')
            self._write_headers = self.headers()
        return self._write_headers

    def current_actor(self) -> int:
        raw, _ = self._request('GET', '/user', authenticated=True)
        try:
            actor = json.loads(raw)['id']
            if type(actor) is not int or actor < 1:
                raise ValueError('Invalid actor ID')
        except (ValueError, KeyError, TypeError):
            raise ValueError('Tracker returned an invalid authenticated actor') from None
        return actor

    @abstractmethod
    def comment_path(self, issue_id: str, comment_id: str | None = None) -> str:
        """Address this issue's comments or one native comment ID."""

    @abstractmethod
    def comment(self, document: dict, issue_id: str, native_issue_id: int) -> dict:
        """Map a supported ordinary comment and verify its original issue identity."""

    @abstractmethod
    def next_comments_page(self, headers, issue_id: str, page: int) -> int | None:
        """Return only continuation information actually supplied by the server."""

    def _next_link_page(self, headers, issue_id: str, page: int) -> int | None:
        for link in headers.get('Link', '').split(','):
            if re.search(r'\brel="next"', link):
                match = re.search(r'<([^>]+)>', link)
                target = urlsplit(match[1]) if match else None
                expected = urlsplit(self.api_url + self.comment_path(issue_id))
                if target is None or target._replace(query='') != expected:
                    raise ValueError('Comments continuation changed the target')
                query = parse_qs(target.query, keep_blank_values=True)
                value = query.get('page', [])
                if (set(query) != {'page', 'per_page'} or query['per_page'] != ['100'] or len(value) != 1
                        or not value[0].isdecimal() or not page < int(value[0]) <= 10_000):
                    raise ValueError('Unsupported comments continuation')
                return int(value[0])
        return None

    def _comment(self, document: dict, issue_id: str, native_issue_id: int) -> dict:
        try:
            item = self.comment(document, issue_id, native_issue_id)
            if (any(type(item[key]) is not int or item[key] < 1 for key in ('id', 'actor_id'))
                    or not isinstance(item['body'], str)
                    or type(item['ordinary']) is not bool
                    or any(not isinstance(item[key], str) or not item[key] for key in ('created_at', 'updated_at'))):
                raise ValueError('Invalid comment fields')
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ValueError('Tracker returned an unsupported comment or a different issue target') from None
        return item

    def create_comment(self, issue_id: str, native_issue_id: int, body: str) -> dict:
        self._identifier(issue_id)
        raw, _ = self._request('POST', self.comment_path(issue_id), {'body': body}, authenticated=True)
        item = self._comment(json.loads(raw), issue_id, native_issue_id)
        if item['ordinary'] is not True:
            raise ValueError('Tracker write returned a system or private note')
        return {'comment': item, 'response_sha256': hashlib.sha256(raw).hexdigest(), 'http_status': 201}

    def read_comment(self, issue_id: str, native_issue_id: int, comment_id: str) -> dict:
        self._identifier(issue_id)
        self._identifier(comment_id)
        raw, _ = self._request('GET', self.comment_path(issue_id, comment_id), authenticated=True)
        item = self._comment(json.loads(raw), issue_id, native_issue_id)
        if item['id'] != int(comment_id):
            raise ValueError('Tracker returned a different comment ID')
        return {'comments': [item], 'response_sha256': hashlib.sha256(raw).hexdigest(), 'next_page': None}

    def list_comments(self, issue_id: str, native_issue_id: int, page: int = 1) -> dict:
        self._identifier(issue_id)
        if type(page) is not int or not 1 <= page <= 10_000:
            raise ValueError('Comment page must be 1–10000')
        raw, headers = self._request('GET', self.comment_path(issue_id) + '?per_page=100&page=' + str(page), authenticated=True)
        documents = json.loads(raw)
        if not isinstance(documents, list) or len(documents) > 100:
            raise ValueError('Tracker returned an unsupported comment page')
        return {'comments': [self._comment(item, issue_id, native_issue_id) for item in documents],
                'response_sha256': hashlib.sha256(raw).hexdigest(), 'next_page': self.next_comments_page(headers, issue_id, page)}


class GitHubBackend(IssueBackend):
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

    def comment_path(self, issue_id: str, comment_id: str | None = None) -> str:
        if comment_id is None:
            return self.path(issue_id) + '/comments'
        return '/repos/' + quote(self.binding['project'], safe='/') + '/issues/comments/' + comment_id

    def comment(self, document: dict, issue_id: str, native_issue_id: int) -> dict:
        if (document['issue_url'] != self.api_url + self.path(issue_id)
                or document['url'] != self.api_url + self.comment_path(issue_id, str(document['id']))):
            raise ValueError('Different comment target')
        return {'id': document['id'], 'actor_id': document['user']['id'], 'body': document['body'], 'ordinary': True,
                'created_at': document['created_at'], 'updated_at': document['updated_at']}

    def next_comments_page(self, headers, issue_id: str, page: int) -> int | None:
        # Return a page number, never follow a supplied URL with credentials.
        return self._next_link_page(headers, issue_id, page)


class GitLabBackend(IssueBackend):
    token_header = 'PRIVATE-TOKEN'

    def path(self, issue_id: str) -> str:
        return '/projects/' + quote(self.binding['project'], safe='') + '/issues/' + issue_id

    def issue(self, document: dict) -> tuple[int, dict]:
        if document['issue_type'] != 'issue':
            raise ValueError('Only ordinary project issues are supported')
        return document['iid'], {'native_id': document['id'], 'title': document['title'],
            'body': document['description'] if document['description'] is not None else '', 'state': document['state'],
            'labels': sorted(set(document['labels'])), 'web_url': document['web_url'], 'updated_at': document['updated_at']}

    def comment_path(self, issue_id: str, comment_id: str | None = None) -> str:
        path = self.path(issue_id) + '/notes'
        return path if comment_id is None else path + '/' + comment_id

    def comment(self, document: dict, issue_id: str, native_issue_id: int) -> dict:
        if (document['noteable_type'] != 'Issue' or document['noteable_id'] != native_issue_id
                or document['noteable_iid'] != int(issue_id)
                or any(type(document.get(key)) is not int for key in ('noteable_id', 'noteable_iid'))
                or any(type(document.get(key)) is not bool for key in ('system', 'internal'))
                or type(document.get('confidential', False)) is not bool):
            raise ValueError('Unsupported note target or visibility')
        return {'id': document['id'], 'actor_id': document['author']['id'], 'body': document['body'],
                'ordinary': not any(document.get(key, False) for key in ('system', 'internal', 'confidential')),
                'created_at': document['created_at'], 'updated_at': document['updated_at']}

    def next_comments_page(self, headers, issue_id: str, page: int) -> int | None:
        linked = self._next_link_page(headers, issue_id, page)
        value = headers.get('X-Next-Page')
        if value in (None, ''):
            return linked
        if value.isdecimal() and page < int(value) <= 10_000:
            if linked is not None and linked != int(value):
                raise ValueError('Conflicting notes continuation')
            return int(value)
        raise ValueError('Unsupported notes continuation')


_BACKENDS = {'github': GitHubBackend, 'gitlab': GitLabBackend}


def for_binding(binding: dict) -> IssueBackend:
    try:
        implementation = _BACKENDS[binding['tool']]
    except KeyError:
        raise ValueError('Select a GitHub or GitLab tracker binding to read issues') from None
    return implementation(binding)
