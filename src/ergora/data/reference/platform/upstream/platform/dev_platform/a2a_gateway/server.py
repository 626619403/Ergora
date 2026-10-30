"""Authenticated A2A 1.0 JSON-RPC transport with bounded request parsing."""
import asyncio
from contextlib import asynccontextmanager
import hmac
import os
import re
from urllib.parse import urlsplit

from starlette.applications import Starlette
from starlette.authentication import SimpleUser
from starlette.responses import JSONResponse
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.types import a2a_pb2 as pb

from ..contracts import need
from . import CONTRACT_URI
from .service import Gateway
from .store import strict_loads

MAX_REQUEST_BYTES = 65_536


def check_url(url):
    parts = urlsplit(url)
    need(parts.scheme in {'https', 'http'} and parts.hostname and not parts.username and not parts.password,
         'Public URL must be an absolute HTTP(S) origin without credentials')
    need(parts.path in {'', '/'} and not parts.query and not parts.fragment, 'Public URL must be an origin, without path/query/fragment')
    need(parts.scheme == 'https' or parts.hostname in {'localhost', '127.0.0.1', '::1'}, 'HTTP is allowed only on loopback; use an HTTPS reverse proxy')
    return url.rstrip('/')


def agent_card(public_url):
    return pb.AgentCard(
        name='Verified development tasks', version='1.3.0',
        description='Admitted repository-governance and large-change tasks. A2A completion means REVIEW_READY, never merge authorization.',
        supported_interfaces=[pb.AgentInterface(url=check_url(public_url) + '/a2a', protocol_binding='JSONRPC', protocol_version='1.0')],
        capabilities=pb.AgentCapabilities(streaming=False, push_notifications=False, extended_agent_card=False),
        security_schemes={'bearer': pb.SecurityScheme(http_auth_security_scheme=pb.HTTPAuthSecurityScheme(scheme='Bearer'))},
        security_requirements=[pb.SecurityRequirement(schemes={'bearer': pb.StringList()})],
        default_input_modes=['application/json'], default_output_modes=['application/json'],
        skills=[pb.AgentSkill(id='admitted-development-task-v1', name='Run an admitted development task',
                             description='Send {task_id,compiled_sha256}; trusted operator must admit the frozen compiled envelope for this principal first. Payload profile: ' + CONTRACT_URI,
                             tags=['development', 'repository-governance', 'large-change'],
                             input_modes=['application/json'], output_modes=['application/json'])])


class Guard:
    """No identity is taken from request JSON or reverse-proxy identity headers."""
    def __init__(self, app, tokens):
        need(type(tokens) is dict and bool(tokens), 'At least one authenticated principal is required')
        for principal, token in tokens.items():
            need(isinstance(principal, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', principal), 'Invalid configured principal')
            need(isinstance(token, str) and 32 <= len(token) <= 1024 and token.isascii() and not any(c.isspace() for c in token),
                 'Bearer secrets must be 32..1024 ASCII non-whitespace characters')
        need(len(set(tokens.values())) == len(tokens), 'Each principal must have a distinct secret')
        self.app, self.tokens = app, dict(tokens)

    async def reject(self, scope, receive, send, status, message):
        await JSONResponse({'error': message}, status_code=status)(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        if scope['path'] == '/.well-known/agent-card.json' and scope['method'] == 'GET':
            return await self.app(scope, receive, send)
        headers = scope.get('headers', [])
        auth_values = [v for k, v in headers if k.lower() == b'authorization']
        auth = auth_values[0].decode('latin1') if len(auth_values) == 1 else ''
        supplied = auth[7:] if auth.startswith('Bearer ') else ''
        principal = None
        for name, token in self.tokens.items():
            if hmac.compare_digest(supplied.encode('latin1'), token.encode('ascii')):
                principal = name
        if principal is None:
            return await self.reject(scope, receive, send, 401, 'Authentication required')
        scope['user'] = SimpleUser(principal)
        versions = [v.decode('latin1') for k, v in headers if k.lower() == b'a2a-version']
        version_supported = len(versions) == 1 and re.fullmatch(r'1\.0(?:\.\d+)?', versions[0])
        if scope['method'] == 'POST':
            header_map = dict(headers)
            if header_map.get(b'content-encoding', b'identity') != b'identity':
                return await self.reject(scope, receive, send, 415, 'Compressed request bodies are not supported')
            if header_map.get(b'content-type', b'').split(b';')[0].strip().lower() != b'application/json':
                return await self.reject(scope, receive, send, 415, 'application/json required')
            try:
                if int(header_map.get(b'content-length', b'0')) > MAX_REQUEST_BYTES:
                    return await self.reject(scope, receive, send, 413, 'Request exceeds 64 KiB')
            except ValueError:
                return await self.reject(scope, receive, send, 400, 'Invalid content length')
            body = bytearray()
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                body.extend(message.get('body', b''))
                if len(body) > MAX_REQUEST_BYTES:
                    return await self.reject(scope, receive, send, 413, 'Request exceeds 64 KiB')
                if not message.get('more_body', False):
                    break
            try:
                value = strict_loads(body.decode('utf-8'))
                need(isinstance(value, dict), 'JSON-RPC batches are not supported')
            except (ValueError, UnicodeError, RecursionError):
                return await self.reject(scope, receive, send, 400, 'Malformed or ambiguous JSON')
            if not version_supported:
                request_id = value.get('id')
                if type(request_id) not in (str, int, type(None)):
                    request_id = None
                response = {'jsonrpc': '2.0', 'id': request_id, 'error': {
                    'code': -32009, 'message': 'A2A-Version: 1.0 is required; other wire versions are not supported'}}
                return await JSONResponse(response)(scope, receive, send)
            delivered = False
            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                return await receive()
            return await self.app(scope, replay, send)
        return await self.app(scope, receive, send)


def create_app(store, backend, tokens, public_url, leases):
    gateway = Gateway(store, backend, leases)
    card = agent_card(public_url)

    async def reconcile_loop():
        while True:
            await asyncio.sleep(15)
            async with gateway.lock:
                for row in store.active_rows():
                    try:
                        await gateway.refresh(row, allow_start=False)
                    except Exception:
                        # An inaccessible lease/backend never grants a new start.
                        continue

    @asynccontextmanager
    async def lifespan(app):
        store.acquire_server_lock()
        task = asyncio.create_task(reconcile_loop())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            store.close(); leases.close()

    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(gateway, '/a2a', enable_v0_3_compat=False), lifespan=lifespan)
    return Guard(app, tokens)


def tokens_from_config(config):
    refs = config['principals']
    need(type(refs) is dict and bool(refs), 'principals must map identities to secret environment variable names')
    result = {}
    for principal, env_name in refs.items():
        need(isinstance(env_name, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', env_name), 'Invalid secret environment reference')
        result[principal] = os.environ[env_name]
    return result
