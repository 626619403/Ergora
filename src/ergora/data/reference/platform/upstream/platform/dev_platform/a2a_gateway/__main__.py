"""Trusted gateway administration and ordinary authenticated A2A task client."""
import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import re

from google.protobuf.json_format import MessageToDict
from a2a.types import a2a_pb2 as pb

from ..contracts import need
from ..connection import connect, task_queue
from ..ingress import IngressLeases
from .backend import TemporalBackend
from .client import connect_client, send
from .server import create_app, tokens_from_config, check_url
from .store import Store, strict_loads, MAX_COMPILED_BYTES


def read_json(path, limit=MAX_COMPILED_BYTES):
    path = Path(path)
    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit, 'Missing, oversized or symlinked JSON file')
    return strict_loads(path.read_text(encoding='utf-8'))


def config(path):
    value = read_json(path, 65_536)
    need(type(value) is dict and set(value) == {'schema_version', 'ledger', 'shared_ingress_db', 'public_url', 'host', 'port', 'principals'}, 'Invalid gateway config fields')
    need(value['schema_version'] == 1 and type(value['schema_version']) is int, 'Unsupported gateway config')
    for field in ('ledger', 'shared_ingress_db'):
        need(type(value[field]) is str and Path(value[field]).is_absolute(), field + ' must be absolute')
    need(Path(value['ledger']) != Path(value['shared_ingress_db']), 'Gateway ledger and shared ingress DB must differ')
    need(value['host'] in {'127.0.0.1', '::1'}, 'Serve behind an HTTPS reverse proxy; local listener must be loopback')
    need(type(value['port']) is int and 1024 <= value['port'] <= 65535, 'Invalid gateway port')
    check_url(value['public_url'])
    need(type(value['principals']) is dict and bool(value['principals']), 'At least one principal is required')
    return value


async def serve(value):
    import uvicorn
    temporal = await connect()
    store = Store(value['ledger']); leases = IngressLeases(value['shared_ingress_db'])
    app = create_app(store, TemporalBackend(temporal, task_queue()), tokens_from_config(value), value['public_url'], leases)
    server = uvicorn.Server(uvicorn.Config(app, host=value['host'], port=value['port'], workers=1, access_log=False,
                                          limit_concurrency=64, timeout_keep_alive=5))
    await server.serve()


async def remote(args):
    need(re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', args.token_env), 'Invalid token environment variable name')
    token = os.environ[args.token_env]
    async with connect_client(args.url, token) as client:
        if args.action == 'send':
            result = await send(client, args.task_id, args.compiled_sha256, args.message_id)
        elif args.action == 'get':
            result = await client.get_task(pb.GetTaskRequest(id=args.a2a_task_id))
        elif args.action == 'cancel':
            result = await client.cancel_task(pb.CancelTaskRequest(id=args.a2a_task_id))
        else:
            result = await client.list_tasks(pb.ListTasksRequest(page_size=args.page_size, page_token=args.page_token, include_artifacts=args.include_artifacts))
        print(json.dumps(MessageToDict(result), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='A2A gateway: trusted admit/serve, authenticated send/get/list/cancel')
    sub = parser.add_subparsers(dest='action', required=True)
    admit = sub.add_parser('admit'); admit.add_argument('--config', required=True); admit.add_argument('--compiled', required=True)
    admit.add_argument('--principal', required=True); admit.add_argument('--expires-at', required=True, help='Timezone-aware ISO-8601 expiry, at most seven days ahead')
    server = sub.add_parser('serve'); server.add_argument('--config', required=True)
    recovery = sub.add_parser('reconcile'); recovery.add_argument('--config', required=True)
    recovery.add_argument('--a2a-task-id', required=True); recovery.add_argument('--proof', required=True)
    for action in ('send', 'get', 'list', 'cancel'):
        command = sub.add_parser(action)
        command.add_argument('--url', required=True); command.add_argument('--token-env', default='A2A_CLIENT_TOKEN')
        if action == 'send':
            command.add_argument('--task-id', required=True); command.add_argument('--compiled-sha256', required=True); command.add_argument('--message-id')
        elif action in {'get', 'cancel'}:
            command.add_argument('--a2a-task-id', required=True)
        else:
            command.add_argument('--page-size', type=int, default=50); command.add_argument('--page-token', default=''); command.add_argument('--include-artifacts', action='store_true')
    args = parser.parse_args()
    if args.action == 'admit':
        value = config(args.config)
        need(args.principal in value['principals'], 'Principal is not configured')
        expiry = datetime.fromisoformat(args.expires_at.replace('Z', '+00:00'))
        need(expiry.tzinfo is not None, 'Expiry must include a timezone')
        store = Store(value['ledger'])
        try:
            reference = store.admit(read_json(args.compiled), args.principal, expiry.timestamp())
            print(json.dumps(reference, ensure_ascii=False, indent=2))
        finally:
            store.close()
    elif args.action == 'reconcile':
        from .reconcile import reconcile
        value = config(args.config)
        async def recover():
            temporal = await connect()
            store = Store(value['ledger']); leases = IngressLeases(value['shared_ingress_db'])
            try:
                # Stop the server first; recovery shares its exclusive ledger lock.
                store.acquire_server_lock()
                result = await reconcile(store, TemporalBackend(temporal, task_queue()), leases, args.a2a_task_id, read_json(args.proof, 16_384))
                print(json.dumps(result, ensure_ascii=False, indent=2))
            finally:
                store.close(); leases.close()
        asyncio.run(recover())
    elif args.action == 'serve':
        asyncio.run(serve(config(args.config)))
    else:
        asyncio.run(remote(args))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from None
