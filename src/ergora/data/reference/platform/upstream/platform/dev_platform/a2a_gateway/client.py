"""Official-SDK client for task-level delegation to a configured gateway."""
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
import uuid

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.helpers import new_data_part
from a2a.types import a2a_pb2 as pb

from ..contracts import need, SLUG, SHA256
from .server import check_url


@asynccontextmanager
async def connect_client(url, token, timeout=30):
    url = check_url(url)
    need(isinstance(token, str) and len(token) >= 32, 'Bearer token is missing or too short')
    async with httpx.AsyncClient(headers={'Authorization': 'Bearer ' + token, 'A2A-Version': '1.0'},
                                 timeout=timeout, follow_redirects=False, trust_env=False) as http:
        card = await A2ACardResolver(http, url).get_agent_card()
        expected = urlsplit(url)
        interfaces = list(card.supported_interfaces)
        need(bool(interfaces), 'Agent card has no interfaces')
        for interface in interfaces:
            endpoint = urlsplit(interface.url)
            need((endpoint.scheme, endpoint.netloc) == (expected.scheme, expected.netloc) and endpoint.path == '/a2a'
                 and not endpoint.query and not endpoint.fragment and not endpoint.username and not endpoint.password,
                 'Agent card redirects credentials to an unexpected endpoint')
        need(any(i.protocol_binding == 'JSONRPC' and i.protocol_version.split('.')[:2] == ['1', '0'] for i in interfaces),
             'A2A 1.0 JSON-RPC interface is required')
        client = ClientFactory(ClientConfig(httpx_client=http, streaming=False, polling=True,
                                            supported_protocol_bindings=['JSONRPC'], accepted_output_modes=['application/json'])).create(card)
        yield client


async def send(client, task_id, compiled_sha256, message_id=None):
    need(type(task_id) is str and SLUG.fullmatch(task_id), 'Invalid domain task ID')
    need(type(compiled_sha256) is str and SHA256.fullmatch(compiled_sha256), 'Invalid compiled digest')
    request = pb.SendMessageRequest(message=pb.Message(message_id=message_id or str(uuid.uuid4()), role=pb.ROLE_USER,
                               parts=[new_data_part({'task_id': task_id, 'compiled_sha256': compiled_sha256}, media_type='application/json')]),
                               configuration=pb.SendMessageConfiguration(return_immediately=True))
    async for event in client.send_message(request):
        if event.HasField('task'):
            return event.task
    raise ValueError('Gateway did not return a Task')
