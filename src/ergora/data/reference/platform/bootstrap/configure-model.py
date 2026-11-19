#!/usr/bin/env python3
"""Configure model metadata for Agentflow without accepting secret values."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'local'))
from agent_platform.core import CONFIG, read, require, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, help='A model ID supported by your Codex backend')
    parser.add_argument('--base-url', help='Configure a custom Responses API provider')
    parser.add_argument('--env-key', help='Optional credential environment variable for the custom provider')
    parser.add_argument('--provider-id', help='Custom provider ID (default: api)')
    parser.add_argument('--reasoning-effort', choices=['low', 'medium', 'high', 'xhigh'], default='high')
    args = parser.parse_args()
    if args.env_key is not None:
        require(re.fullmatch(r'[A-Z][A-Z0-9_]*', args.env_key), 'Use an environment variable name, not a key value')
    custom_provider = any(value is not None for value in (args.base_url, args.env_key, args.provider_id))
    provider_id = args.provider_id if args.provider_id is not None else 'api'
    if custom_provider:
        require(re.fullmatch(r'[a-z][a-z0-9_-]*', provider_id), 'Invalid provider ID')
        base_url = args.base_url if args.base_url is not None else 'https://api.openai.com/v1'
        url = urlsplit(base_url)
        require(url.scheme == 'https' and url.hostname and not url.username and not url.password and
                not url.query and not url.fragment, 'Use an HTTPS API base URL without credentials or query strings')
    require(args.model.strip() and '\n' not in args.model, 'Use a valid model ID')
    config = read(CONFIG / 'platform.json')
    fields = [
        'model = ' + json.dumps(args.model),
        'model_reasoning_effort = ' + json.dumps(args.reasoning_effort), 'approval_policy = "never"',
    ]
    if custom_provider:
        fields += ['model_provider = ' + json.dumps(provider_id),
                   '[model_providers.' + provider_id + ']', 'name = "Responses API"',
                   'base_url = ' + json.dumps(base_url), 'wire_api = "responses"']
        if args.env_key is not None:
            fields.append('env_key = ' + json.dumps(args.env_key))
    content = '\n'.join([*fields, ''])
    fd, temporary = tempfile.mkstemp(prefix='.model-', dir=CONFIG)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
        os.chmod(temporary, 0o600)
        os.replace(temporary, CONFIG / 'codex.toml')
    finally:
        Path(temporary).unlink(missing_ok=True)
    config.pop('codex_env_key', None)
    write(CONFIG / 'platform.json', config, replace=True)
    print(json.dumps({'model': args.model, 'provider': provider_id if custom_provider else 'openai',
                      'credential_variable': args.env_key, 'authentication': 'not_checked',
                      'credential_value_saved': False, 'restart_services_after_configuration': True}, indent=2))


if __name__ == '__main__':
    main()
