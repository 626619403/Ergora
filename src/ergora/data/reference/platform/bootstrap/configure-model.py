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
    parser.add_argument('--model', required=True, help='A model ID supported by your Responses API provider')
    parser.add_argument('--base-url', default='https://api.openai.com/v1')
    parser.add_argument('--env-key', default='OPENAI_API_KEY')
    parser.add_argument('--provider-id', default='api')
    parser.add_argument('--reasoning-effort', choices=['low', 'medium', 'high', 'xhigh'], default='high')
    args = parser.parse_args()
    require(re.fullmatch(r'[A-Z][A-Z0-9_]*', args.env_key), 'Use an environment variable name, not a key value')
    require(re.fullmatch(r'[a-z][a-z0-9_-]*', args.provider_id), 'Invalid provider ID')
    url = urlsplit(args.base_url)
    require(url.scheme == 'https' and url.hostname and not url.username and not url.password and
            not url.query and not url.fragment, 'Use an HTTPS API base URL without credentials or query strings')
    require(args.model.strip() and '\n' not in args.model, 'Use a valid model ID')
    config = read(CONFIG / 'platform.json')
    content = '\n'.join([
        'model = ' + json.dumps(args.model), 'model_provider = ' + json.dumps(args.provider_id),
        'model_reasoning_effort = ' + json.dumps(args.reasoning_effort), 'approval_policy = "never"',
        '[model_providers.' + args.provider_id + ']', 'name = "Responses API"',
        'base_url = ' + json.dumps(args.base_url), 'env_key = ' + json.dumps(args.env_key), 'wire_api = "responses"', '',
    ])
    fd, temporary = tempfile.mkstemp(prefix='.model-', dir=CONFIG)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
        os.chmod(temporary, 0o600)
        os.replace(temporary, CONFIG / 'codex.toml')
    finally:
        Path(temporary).unlink(missing_ok=True)
    config['codex_env_key'] = args.env_key
    write(CONFIG / 'platform.json', config, replace=True)
    print(json.dumps({'model': args.model, 'provider': args.provider_id, 'credential_variable': args.env_key,
                      'credential_value_saved': False, 'restart_services_after_exporting_environment': True}, indent=2))


if __name__ == '__main__':
    main()
