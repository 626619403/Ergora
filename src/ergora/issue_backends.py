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
from .state import now


_RESPONSE_LIMIT = 1_048_576
_FULL_OID = r'(?:[0-9a-f]{40}|[0-9a-f]{64})'


class _HTTPStatusError(ValueError):
    def __init__(self, operation: str, status: int):
        self.status = status
        super().__init__(f'Tracker {operation} failed with HTTP {status}')


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

    def _request(self, method: str, path: str, body: dict | None = None, *, authenticated: bool = False,
                 expected_status: int | None = None, base_url: str | None = None):
        headers = self.headers() if not authenticated else self._authenticated_headers()
        encoded = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if encoded is not None:
            headers = {**headers, 'Content-Type': 'application/json'}
        request = Request((base_url or self.api_url) + path, data=encoded, headers=headers, method=method)
        operation = 'read' if method == 'GET' else 'write'
        expected = expected_status if expected_status is not None else 200 if method == 'GET' else 201
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
            raise _HTTPStatusError(operation, error.code) from None
        except (URLError, OSError, HTTPException) as error:
            raise ValueError(f'Tracker {operation} unavailable: ' + type(error).__name__) from None
        if len(raw) > _RESPONSE_LIMIT:
            raise ValueError('Complete tracker response exceeds 1 MiB')
        if remaining not in (None, 0):
            raise ValueError('Tracker response ended before its declared content length')
        return raw, response_headers

    def _document(self, path: str, *, optional: bool = False) -> tuple[dict | None, dict]:
        try:
            raw, _ = self._request('GET', path)
        except _HTTPStatusError as error:
            if optional and error.status == 404:
                return None, {'observed_at': now(), 'http_status': 404, 'response_sha256': None}
            raise
        document = json.loads(raw)
        if not isinstance(document, dict):
            raise ValueError('Tracker returned an unsupported repository or ref document')
        return document, {'observed_at': now(), 'http_status': 200, 'response_sha256': hashlib.sha256(raw).hexdigest()}

    @abstractmethod
    def repository_refs(self, head_branch: str, base_branch: str) -> dict:
        """Read two refs after export-owner branch validation; no publication receipt or CAS."""

    @abstractmethod
    def review_path(self, repository: dict, number: str) -> str:
        """Address one explicitly selected native PR/MR, with no list or search."""

    @abstractmethod
    def review_request(self, document: dict, repository: dict, number: str) -> dict:
        """Map native review fields and verify both endpoints belong to this repository."""

    def read_review_request(self, repository: dict, number: str) -> dict:
        self._identifier(number)
        path = self.review_path(repository, number)
        document, receipt = self._document(path)
        try:
            review = self.review_request(document, repository, number)
            observed = {'schema_version': 1,
                'source': issue_sources.tracker_identity(self.binding),
                'repository': {'native_id': repository['native_id'], 'node_id': repository.get('node_id'),
                               'project': repository['project']},
                'review': review, 'response': {**receipt, 'request_url': self.api_url + path}, 'context_only': True}
            contracts.validate(observed, contracts.REVIEW_REQUEST, 'Review request observation')
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValueError('Tracker returned an unsupported or different review request') from None
        return observed

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

    def label_selection(self, source: dict, label_name: str) -> dict:
        """Freeze verified native IDs, or fail before a label attempt exists."""
        raise ValueError('Candidate label writeback is unsupported by this tracker; comment writeback remains available')

    def label_operation(self, source: dict, target: dict, mutation_id: str) -> dict:
        """Describe the exact native ID request without reading credentials or sending it."""
        raise ValueError('Candidate label writeback is unsupported by this tracker')

    def add_label(self, source: dict, target: dict, mutation_id: str) -> dict:
        raise ValueError('Candidate label writeback is unsupported by this tracker')

    def observe_label(self, source: dict, target: dict, cursor: str | None) -> dict:
        raise ValueError('Candidate label writeback is unsupported by this tracker')


class GitHubBackend(IssueBackend):
    token_header = 'Authorization'
    _LABEL_PAGE = '''__typename ... on Issue {
        id number repository { id nameWithOwner }
        labels(first: 100, after: $cursor) {
            nodes { id name repository { id } }
            pageInfo { hasNextPage endCursor }
        }
    }'''
    _LABEL_ADD = '''mutation ErgoraCandidateLabel($input: AddLabelsToLabelableInput!, $cursor: String) {
        addLabelsToLabelable(input: $input) {
            clientMutationId labelable { ''' + _LABEL_PAGE + ''' }
        }
    }'''
    _LABEL_OBSERVE = '''query ErgoraCandidateLabelObservation($issue: ID!, $cursor: String) {
        node(id: $issue) { ''' + _LABEL_PAGE + ''' }
    }'''

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

    def review_path(self, repository: dict, number: str) -> str:
        return '/repos/' + quote(self.binding['project'], safe='/') + '/pulls/' + number

    def review_request(self, document: dict, repository: dict, number: str) -> dict:
        root = self.api_url + '/repos/' + quote(self.binding['project'], safe='/')
        if type(document['number']) is not int or document['number'] != int(number) or document['url'] != root + '/pulls/' + number:
            raise ValueError('Different review request')
        for endpoint in ('head', 'base'):
            native = document[endpoint]['repo']
            if (type(native['id']) is not int or native['id'] != repository['native_id']
                    or native['node_id'] != repository['node_id'] or native['full_name'] != self.binding['project']
                    or native['url'] != root):
                raise ValueError('Cross-repository or missing review endpoint')
        return {'kind': 'pull_request', 'number': number, 'native_id': document['id'], 'node_id': document['node_id'],
            'author_id': document['user']['id'], 'title': document['title'], 'body': document['body'],
            'state': document['state'], 'draft': document['draft'], 'merged': document['merged'],
            'web_url': document['html_url'], 'created_at': document['created_at'], 'updated_at': document['updated_at'],
            'head': {'branch': document['head']['ref'], 'sha': document['head']['sha']},
            'base': {'branch': document['base']['ref'], 'response_sha': document['base']['sha']}, 'diff_refs': None}

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

    def repository_refs(self, head_branch: str, base_branch: str) -> dict:
        root = '/repos/' + quote(self.binding['project'], safe='/')
        document, receipt = self._document(root)
        try:
            if (type(document['id']) is not int or document['id'] < 1
                    or not isinstance(document['node_id'], str) or not document['node_id']
                    or document['full_name'] != self.binding['project'] or document['url'] != self.api_url + root):
                raise ValueError('Different repository')
            repository = {'native_id': document['id'], 'node_id': document['node_id'],
                          'project': document['full_name'], **receipt}
        except (KeyError, TypeError, ValueError):
            raise ValueError('Tracker returned an unsupported or different repository identity') from None
        return {'repository': repository, 'head': self._branch(root, head_branch), 'base': self._branch(root, base_branch)}

    def _branch(self, root: str, branch: str) -> dict:
        ref = 'refs/heads/' + branch
        document, receipt = self._document(root + '/git/ref/heads/' + quote(branch, safe='/'), optional=True)
        if document is None:
            return {'ref': ref, 'sha': None, 'resolution': 'not_found_or_not_visible', **receipt}
        try:
            sha = document['object']['sha']
            if (document['ref'] != ref or document['object']['type'] != 'commit'
                    or document['url'] != self.api_url + root + '/git/refs/heads/' + quote(branch, safe='/')
                    or not isinstance(sha, str) or not re.fullmatch(_FULL_OID, sha)):
                raise ValueError('Different ref')
        except (KeyError, TypeError, ValueError):
            raise ValueError('Tracker returned an unsupported or different exact branch ref') from None
        return {'ref': ref, 'sha': sha, 'resolution': 'resolved', **receipt}

    def _graphql_url(self) -> str:
        parsed = urlsplit(self.api_url)
        if parsed.path == '':
            return self.api_url + '/graphql'
        if parsed.path == '/api/v3':
            return parsed._replace(path='/api/graphql').geturl()
        raise ValueError('GitHub label writeback requires a REST origin or /api/v3 base; no GraphQL endpoint was inferred')

    def label_selection(self, source: dict, label_name: str) -> dict:
        self._identifier(source['issue_id'])
        self._graphql_url()  # Reject an unsupported endpoint before any lookup.
        if not isinstance(label_name, str) or not label_name:
            raise ValueError('Select one nonempty exact existing label name')
        root = '/repos/' + quote(self.binding['project'], safe='/')
        raw, _ = self._request('GET', self.path(source['issue_id']), authenticated=True)
        repository_raw, _ = self._request('GET', root, authenticated=True)
        label_raw, _ = self._request('GET', root + '/labels/' + quote(label_name, safe=''), authenticated=True)
        try:
            document, repository, label = map(json.loads, (raw, repository_raw, label_raw))
            number, issue = self.issue(document)
            target = {'issue_id': document['node_id'], 'repository_id': repository['node_id'],
                      'label_id': label['node_id'], 'label_native_id': label['id']}
            if (type(number) is not int or number != int(source['issue_id']) or issue['native_id'] != source['native_id']
                    or repository['full_name'] != self.binding['project'] or repository['url'] != self.api_url + root
                    or label['name'] != label_name or label['url'] != self.api_url + root + '/labels/' + quote(label_name, safe='')
                    or any(not isinstance(target[key], str) or not target[key] for key in ('issue_id', 'repository_id', 'label_id'))
                    or type(target['label_native_id']) is not int or target['label_native_id'] < 1):
                raise ValueError('Different native label target')
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ValueError('Tracker returned an unsupported label identity or a different issue/repository/label target') from None
        return {'native_target': target, 'target_at_prepare_sha256': hashlib.sha256(raw).hexdigest()}

    def label_operation(self, source: dict, target: dict, mutation_id: str) -> dict:
        return {'method': 'POST', 'url': self._graphql_url(), 'body': {
            'query': self._LABEL_ADD, 'variables': {'input': {
                'labelableId': target['issue_id'], 'labelIds': [target['label_id']],
                'clientMutationId': mutation_id}, 'cursor': None}}}

    def _graphql(self, body: dict) -> tuple[dict, str]:
        raw, _ = self._request('POST', '', body, authenticated=True, expected_status=200, base_url=self._graphql_url())
        try:
            document = json.loads(raw)
            if not isinstance(document, dict) or 'errors' in document or not isinstance(document['data'], dict):
                raise ValueError('Incomplete GraphQL data')
        except (KeyError, ValueError, TypeError):
            # Do not put server-controlled error text or credentials in durable observations.
            raise ValueError('Tracker returned GraphQL errors or unsupported partial data; execution is not disproved') from None
        return document['data'], hashlib.sha256(raw).hexdigest()

    def _label_page(self, document: dict, source: dict) -> dict:
        try:
            repository, connection = document['repository'], document['labels']
            labels, page = connection['nodes'], connection['pageInfo']
            if (document['__typename'] != 'Issue' or type(document['number']) is not int
                    or document['number'] != int(source['issue_id']) or repository['nameWithOwner'] != source['project']
                    or any(not isinstance(value, str) or not value for value in (document['id'], repository['id']))
                    or not isinstance(labels, list) or len(labels) > 100 or type(page['hasNextPage']) is not bool
                    or (page['endCursor'] is not None and (not isinstance(page['endCursor'], str) or not page['endCursor']))
                    or (page['hasNextPage'] and not page['endCursor'])):
                raise ValueError('Invalid label page')
            items = []
            for label in labels:
                if (any(not isinstance(label[key], str) or not label[key] for key in ('id', 'name'))
                        or label['repository']['id'] != repository['id']):
                    raise ValueError('Invalid label identity')
                items.append({'id': label['id'], 'name': label['name'], 'repository_id': label['repository']['id']})
            return {'issue_id': document['id'], 'issue_number': document['number'], 'project': repository['nameWithOwner'],
                    'repository_id': repository['id'], 'labels': items,
                    'page_info': {'has_next_page': page['hasNextPage'], 'end_cursor': page['endCursor']}}
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ValueError('Tracker returned an unsupported label page or a different issue/repository target') from None

    def add_label(self, source: dict, target: dict, mutation_id: str) -> dict:
        operation = self.label_operation(source, target, mutation_id)
        data, digest = self._graphql(operation['body'])
        try:
            payload = data['addLabelsToLabelable']
            echo, page = payload['clientMutationId'], self._label_page(payload['labelable'], source)
        except (KeyError, TypeError, AttributeError):
            raise ValueError('Tracker returned an unsupported label mutation payload; execution is not disproved') from None
        return {'http_status': 200, 'response_sha256': digest, 'client_mutation_id': echo, 'page': page}

    def observe_label(self, source: dict, target: dict, cursor: str | None) -> dict:
        if cursor is not None and (not isinstance(cursor, str) or not cursor):
            raise ValueError('A label cursor must be a nonempty opaque string')
        data, digest = self._graphql({'query': self._LABEL_OBSERVE, 'variables': {'issue': target['issue_id'], 'cursor': cursor}})
        try:
            page = self._label_page(data['node'], source)
        except (KeyError, TypeError):
            raise ValueError('Tracker returned an unsupported label observation') from None
        if page['issue_id'] != target['issue_id'] or page['repository_id'] != target['repository_id']:
            raise ValueError('Observed label page differs from the frozen native target')
        return {'response_sha256': digest, 'page': page}


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

    def review_path(self, repository: dict, number: str) -> str:
        return '/projects/' + str(repository['native_id']) + '/merge_requests/' + number

    def review_request(self, document: dict, repository: dict, number: str) -> dict:
        if (type(document['iid']) is not int or document['iid'] != int(number)
                or any(type(document[key]) is not int or document[key] != repository['native_id']
                       for key in ('project_id', 'source_project_id', 'target_project_id'))):
            raise ValueError('Different iid or cross-project review request')
        return {'kind': 'merge_request', 'number': number, 'native_id': document['id'], 'node_id': None,
            'author_id': document['author']['id'], 'title': document['title'], 'body': document['description'],
            'state': document['state'], 'draft': document['draft'], 'merged': None,
            'web_url': document['web_url'], 'created_at': document['created_at'], 'updated_at': document['updated_at'],
            'head': {'branch': document['source_branch'], 'sha': document['sha']},
            'base': {'branch': document['target_branch'], 'response_sha': None}, 'diff_refs': document['diff_refs']}

    def repository_refs(self, head_branch: str, base_branch: str) -> dict:
        document, receipt = self._document('/projects/' + quote(self.binding['project'], safe=''))
        try:
            if (type(document['id']) is not int or document['id'] < 1
                    or document['path_with_namespace'] != self.binding['project']):
                raise ValueError('Different repository')
            repository = {'native_id': document['id'], 'project': document['path_with_namespace'], **receipt}
        except (KeyError, TypeError, ValueError):
            raise ValueError('Tracker returned an unsupported or different repository identity') from None
        root = '/projects/' + str(repository['native_id'])
        return {'repository': repository, 'head': self._branch(root, head_branch), 'base': self._branch(root, base_branch)}

    def _branch(self, root: str, branch: str) -> dict:
        ref = 'refs/heads/' + branch
        document, receipt = self._document(root + '/repository/branches/' + quote(branch, safe=''), optional=True)
        if document is None:
            return {'ref': ref, 'sha': None, 'resolution': 'not_found_or_not_visible', **receipt}
        try:
            sha = document['commit']['id']
            if document['name'] != branch or not isinstance(sha, str) or not re.fullmatch(_FULL_OID, sha):
                raise ValueError('Different branch')
        except (KeyError, TypeError, ValueError):
            raise ValueError('Tracker returned an unsupported or different exact branch ref') from None
        return {'ref': ref, 'sha': sha, 'resolution': 'resolved', **receipt}

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
