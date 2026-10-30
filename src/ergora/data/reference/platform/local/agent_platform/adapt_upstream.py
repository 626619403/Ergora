"""Add explicit local tracker identities without inventing GitLab issues."""
from __future__ import annotations

import hashlib
import json

from .core import STATE, UPSTREAM, require, write


def apply() -> list[dict]:
    records = []
    for relative in ['platform/dev_platform/contracts.py', 'platform/dev_platform/ingress.py']:
        path = UPSTREAM / relative
        original = path.read_bytes()
        before = '("github", "gitlab")'
        after = '("local", "github", "gitlab")'
        text = original.decode()
        require(text.count(before) == 1 or text.count(after) == 1, 'Upstream tracker contract changed: ' + relative)
        if before in text:
            path.write_text(text.replace(before, after))
        records.append({'file': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for path in (UPSTREAM / 'platform/portable/schemas').glob('*.json'):
        data = json.loads(path.read_text())
        changed = False
        def visit(node):
            nonlocal changed
            if isinstance(node, dict):
                if node.get('enum') == ['github', 'gitlab']:
                    node['enum'] = ['local', 'github', 'gitlab']; changed = True
                for value in node.values(): visit(value)
            elif isinstance(node, list):
                for value in node: visit(value)
        visit(data)
        if changed:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        if '"local"' in path.read_text():
            records.append({'file': str(path.relative_to(UPSTREAM)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    write(STATE / 'upstream-local-tracker-adaptation.json', {'files': records}, replace=True)
    return records


if __name__ == '__main__':
    print(json.dumps(apply(), indent=2))
