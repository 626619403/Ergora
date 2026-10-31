import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import agents, kernel, projects, reference, tools
from ergora.state import State


pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Native Windows contracts')


def test_windows_default_data_and_explicit_home(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    monkeypatch.delenv('ERGORA_HOME', raising=False)
    assert State().root == tmp_path / 'Ergora/data'
    monkeypatch.setenv('ERGORA_HOME', str(tmp_path / 'custom'))
    assert State().root == tmp_path / 'custom'


def test_linux_only_tools_and_reference_fail_with_wsl_guidance(tmp_path):
    repo = tmp_path / 'repo'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    state = State(tmp_path / 'data')
    projects.create(state, 'demo', repo)
    projects.bind(state, 'demo', 'implementer', {'tool': 'mini-swe-agent', 'python': sys.executable, 'model': 'provider/model'}, 1)
    projects.bind(state, 'demo', 'kernel', {'tool': 'forgekernel', 'python': sys.executable, 'checkout': str(repo), 'task': str(repo)}, 2)
    checks = {item['layer']: item for item in tools.doctor(state, 'demo')['checks']}
    assert not checks['implementer']['installed'] and 'WSL2' in checks['implementer']['platform_note']
    assert not checks['kernel']['installed'] and 'WSL2' in checks['kernel']['reason']
    run = tools.run_agent(state, 'demo', 'implementer', 'fixture')
    assert run['status'] == 'failed' and 'WSL2' in run['error']
    with pytest.raises(ValueError, match='WSL2'):
        kernel.create(state, 'demo')
    with pytest.raises(ValueError, match='WSL2'):
        reference.executor(repo, state.root)
    assert not kernel.listing(state, 'demo')


def test_legacy_codepage_does_not_change_unicode_memory_and_skill_files(tmp_path):
    root = tmp_path / '中文 profile'
    root.mkdir()
    repo = root / 'repo'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    script = '''import json,sys
from pathlib import Path
from ergora import projects,memory,skills,tools
from ergora.state import State
root=Path(sys.argv[1]);state=State(root/'data')
projects.create(state,'demo',root/'repo')
memory.save(state,'demo','中文长期记忆',{'uri':'manual:中文','revision':'v1'})
bundle=root/'test-skill';bundle.mkdir()
(bundle/'SKILL.md').write_text('---\\nname: test-skill\\ndescription: 中文技能\\n---\\n中文操作说明\\n',encoding='utf-8')
item=skills.import_bundle(state,'demo',bundle)
projects.bind(state,'demo','reviewer',{'tool':'command','argv':[sys.executable,'-c','import sys;print(sys.stdin.read())']},1)
run=tools.run_agent(state,'demo','reviewer','中文提示',skill_names=['test-skill'])
assert run['status']=='succeeded',run
assert '中文操作说明' in Path(run['output'],'stdout.txt').read_text(encoding='utf-8')
assert memory.search(state,'demo','中文')['results'][0]['text']=='中文长期记忆'
print(json.dumps({'digest':skills.get(state,'demo',item['digest'])['digest']}))
'''
    env = dict(os.environ, PYTHONUTF8='0', PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, '-c', script, str(root)], env=env, capture_output=True,
                            text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(json.loads(result.stdout)['digest']) == 64


def test_container_override_cannot_disable_native_windows_sandbox(tmp_path):
    with pytest.raises(ValueError, match='native Codex sandbox'):
        agents.invoke({'tool': 'codex', 'sandbox': 'current-container'}, 'implementer', 'fixture',
                      tmp_path, tmp_path / 'output', 5)
