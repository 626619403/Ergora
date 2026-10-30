from __future__ import annotations

import json
from pathlib import Path
import shutil

from .core import ROOT, UPSTREAM, require


def install() -> dict:
    destination = ROOT / 'templates'
    for kind in ('repository-governance', 'large-change'):
        target = destination / kind
        target.mkdir(parents=True, exist_ok=True)
        source = UPSTREAM / 'platform/portable/packages' / kind
        for name in ('instructions.md', 'input.schema.json', 'output.schema.json', 'roles.json', 'evidence.json'):
            if not (target / name).exists(): shutil.copy2(source / name, target / name)
        template = json.loads((UPSTREAM / 'platform/portable/examples' / kind / 'task.json').read_text())['input']
        if not (target / 'input.json').exists():
            (target / 'input.json').write_text(json.dumps(template, ensure_ascii=False, indent=2) + '\n')
        guide = ('# ' + kind + '\n\n复制 input.json 到具体项目，填写真实目标、路径、验收标准和 work_units。\n'
                 '每个项目独立注册；本地任务使用 --tracker local --project local/项目名，接入 GitLab 后绑定真实项目。\n'
                 '盘点 → 计划 → 人工批准 → 分单元实现 → 集成 → 命令验证 → Codex 独立新会话审查 → REVIEW_READY。\n'
                 '平台不自动合并。命令验证读取项目注册时的 checks.json；本模板不提供默认 PASS。\n'
                 '当前 Docker 是外层安全边界，Git worktree 只负责工作目录管理。\n')
        if not (target / 'LOCAL-GUIDE.md').exists(): (target / 'LOCAL-GUIDE.md').write_text(guide)
    target = destination / 'training-optimization'
    target.mkdir(parents=True, exist_ok=True)
    for path in (UPSTREAM / 'templates').iterdir():
        if path.is_file() and not (target / path.name).exists(): shutil.copy2(path, target / path.name)
    runner = {'schema_version': 1, 'runner_template_id': 'project-training-v1', 'project': 'REPLACE_PROJECT',
              'repo': '/absolute/path/your-project',
              'command': ['bash', 'scripts/run-bound-experiment.sh', '{manifest}', '{output}'],
              'timeout_seconds': 21600}
    runner_path = target / 'runner-template.example.json'
    if not runner_path.exists() or json.loads(runner_path.read_text()) == {k: v for k, v in runner.items() if k != 'project'}:
        runner_path.write_text(json.dumps(runner, indent=2) + '\n')
    guide = ('# training-optimization\n\n'
             '本地操作说明：~/multi-agent-platform/docs/TRAINING.md。\n'
             '先按项目填写 workload-contract.md、baseline.json、experiment.json 和 runner-template.example.json；'
             '人工审阅合同后再批准，示例中的提交、指标和 PASS 不能作为真实实验依据。\n'
             '每次只手动启动一个精确实验：training prepare → worker-start → start → '
             'run-local（确认 manifest SHA）→ status/result。没有常驻训练队列消费者。\n'
             '固定 perfctl 证据门禁通过后才等待人工放行；放行只创建该项目的集成/复验任务。\n'
             '真实训练使用项目自己的环境；模板不安装 CUDA/PyTorch，也未测量任何 GPU 性能。\n')
    if not (target / 'LOCAL-GUIDE.md').exists():
        (target / 'LOCAL-GUIDE.md').write_text(guide)
    return {'templates': str(destination), 'types': ['repository-governance', 'large-change', 'training-optimization']}


def copy(kind: str, destination: Path) -> dict:
    require(kind in {'repository-governance', 'large-change', 'training-optimization'}, 'Unknown workflow template')
    install()
    require(not destination.exists(), 'Choose a new directory to preserve existing project files')
    shutil.copytree(ROOT / 'templates' / kind, destination)
    return {'copied': kind, 'destination': str(destination.resolve())}
