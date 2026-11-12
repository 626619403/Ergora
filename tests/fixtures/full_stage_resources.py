"""Actual fixed-resource pagination in the deterministic native CLI fixture."""

import base64
import hashlib
import json


async def read_all(server):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async with stdio_client(StdioServerParameters(**server)) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            assert sorted(tool.name for tool in (await session.list_tools()).tools) == ['list', 'read']
            offset = 0
            while offset is not None:
                result = await session.call_tool('list', {'offset': offset, 'max_entries': 2})
                assert not result.is_error
                page = json.loads(result.content[0].text)
                for entry in page['files']:
                    content, position = bytearray(), 0
                    while position is not None:
                        result = await session.call_tool('read', {'path': entry['uri'], 'offset': position, 'max_bytes': 16384})
                        assert not result.is_error
                        part = json.loads(result.content[0].text)
                        content.extend(part['content'].encode('utf-8') if part['encoding'] == 'utf-8'
                                       else base64.b64decode(part['content'], validate=True))
                        position = part['next_offset']
                    assert len(content) == entry['size'] and hashlib.sha256(content).hexdigest() == entry['sha256']
                offset = page['next_offset']
