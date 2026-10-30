"""Build the home report and credential-free source/template/runtime exports."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import posixpath
import re
import tempfile
import zipfile


VERSION = '2026-10-28'
KIT_NAME = 'agentflow-platform-v2.2-linux-x86_64.zip'
RUNTIME_NAME = 'agentflow-runtime-linux-x86_64-' + VERSION + '.zip'
STAMP = (2026, 10, 28, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_bytes(files: dict[str, bytes], prefix: str = '') -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for name, raw in sorted(files.items()):
            entry = zipfile.ZipInfo(prefix + name, STAMP)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            bundle.writestr(entry, raw)
    return output.getvalue()


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.report-', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def inline(text: str, link_base: str = '') -> str:
    pattern = re.compile(r'`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*')
    parts, start = [], 0
    for match in pattern.finditer(text):
        parts.append(html.escape(text[start:match.start()]))
        if match.group(1):
            parts.append('<code>' + html.escape(match.group(1)) + '</code>')
        elif match.group(2):
            label, target = html.escape(match.group(2)), match.group(3)
            if target.startswith('https://'):
                parts.append('<a href="' + html.escape(target, quote=True) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>')
            else:
                target = posixpath.normpath(posixpath.join(link_base, target))
                parts.append('<button class="text-button" data-download="' + html.escape(target, quote=True) + '">' + label + ' ↓</button>')
        else:
            parts.append('<strong>' + html.escape(match.group(4)) + '</strong>')
        start = match.end()
    parts.append(html.escape(text[start:]))
    return ''.join(parts)


def code(text: str) -> str:
    return '<div class="code-wrap"><button class="copy" aria-label="复制代码">复制</button><pre><code>' + html.escape(text.rstrip()) + '</code></pre></div>'


def markdown(text: str, *, skip_title: bool = True, link_base: str = '') -> str:
    render = lambda value: inline(value, link_base)
    lines, blocks, index = text.splitlines(), [], 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
        elif line.startswith('```'):
            index += 1
            content = []
            while index < len(lines) and not lines[index].startswith('```'):
                content.append(lines[index]); index += 1
            blocks.append(code('\n'.join(content))); index += 1
        elif line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if not (level == 1 and skip_title):
                tag = 'h' + str(min(level + 1, 5))
                blocks.append('<' + tag + '>' + render(line[level:].strip()) + '</' + tag + '>')
            index += 1
        elif line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].startswith('|'):
                row = [item.strip() for item in lines[index].strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', item) for item in row):
                    rows.append(row)
                index += 1
            header = '<tr>' + ''.join('<th>' + render(item) + '</th>' for item in rows[0]) + '</tr>'
            body = ''.join('<tr>' + ''.join('<td>' + render(item) + '</td>' for item in row) + '</tr>' for row in rows[1:])
            blocks.append('<div class="table-wrap"><table><thead>' + header + '</thead><tbody>' + body + '</tbody></table></div>')
        elif re.match(r'^(- |\d+\. )', line):
            ordered = not line.startswith('- ')
            tag, items = ('ol' if ordered else 'ul'), []
            while index < len(lines) and re.match(r'^(- |\d+\. )', lines[index]):
                items.append('<li>' + render(re.sub(r'^(- |\d+\. )', '', lines[index])) + '</li>')
                index += 1
            blocks.append('<' + tag + '>' + ''.join(items) + '</' + tag + '>')
        else:
            paragraph = []
            while index < len(lines) and lines[index].strip() and not re.match(r'^(#|```|\||- |\d+\. )', lines[index]):
                paragraph.append(lines[index]); index += 1
            blocks.append('<p>' + render(' '.join(paragraph)) + '</p>')
    return '\n'.join(blocks)


def chapters(text: str) -> dict[str, str]:
    parts = re.split(r'(?m)^## ', text)
    return {part.split('\n', 1)[0]: '## ' + part for part in parts[1:]}


def payload_files(root: Path) -> dict[str, bytes]:
    source = root / 'bootstrap/report'
    paths = [root / 'README.zh-CN.md', root / 'requirements.lock', root / 'downloads/temporal-cli.json',
             root / 'source/upstream-original.zip', root / 'bootstrap/configure-model.py',
             root / 'bootstrap/requirements.in',
             *[root / 'bootstrap' / name for name in ('install-multi-agent-linux-deps.sh', 'install-multi-agent-platform.sh')],
             *[root / 'docs' / name for name in ('TRAINING.md', 'PROJECT-ONBOARDING.zh-CN.md', 'VALIDATION.md')]]
    for name in ('local/agent_platform', 'upstream', 'templates'):
        paths.extend((root / name).rglob('*'))
    for name in ('build_report.py', 'install-from-report.sh', 'install_from_bundle.py', 'test_install_from_bundle.py',
                 'public-release.json', 'public-manual-body.html', 'base-head.html', 'report.js', 'research.html'):
        paths.append(source / name)
    paths.extend((source / 'public').rglob('*'))
    result = {}
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink() or '__pycache__' in path.parts:
            continue
        name = path.relative_to(root).as_posix()
        if path.suffix in ('.pyc', '.log', '.sqlite3') or path.name in ('source-manifest.json',):
            continue
        if name.startswith('source/') and path.name not in ('multi-agent-development-platform.html', 'upstream-original.zip', 'SHA256SUMS'):
            continue
        result[name] = path.read_bytes()
    for path in (source / 'tooling').glob('*.json'):
        result['tooling/' + path.name] = path.read_bytes()
        result['bootstrap/report/tooling/' + path.name] = path.read_bytes()
    for name, raw in list(result.items()):
        if name.endswith(('.md', '.json', '.py', '.txt', '.in', '.lock')):
            text = raw.decode()
            if name == 'bootstrap/requirements.in':
                text = re.sub(r'-r .*/upstream/', '-r ../upstream/', text)
            elif name == 'requirements.lock':
                text = re.sub(r'/home/[^\s]+/multi-agent-platform/', '', text)
            if name == 'templates/training-optimization/runner-template.example.json':
                value = json.loads(text); value['repo'] = '/absolute/path/your-project'
                text = json.dumps(value, indent=2) + '\n'
            result[name] = text.encode()
    for module in ('setup.py', 'doctor.py', 'templates.py'):
        text = result['local/agent_platform/' + module].decode()
        if module == 'setup.py':
            old = '''    source = tomllib.loads((Path.home() / ".codex/config.toml").read_text())
    provider_id = source["model_provider"]
    provider = source["model_providers"][provider_id]
    require(provider.get("env_key"), "Codex provider must reference an environment variable")'''
            new = '''    provider_id = "api"
    provider = {"name": "Responses API", "base_url": "https://api.openai.com/v1",
                "env_key": "OPENAI_API_KEY", "wire_api": "responses"}
    source = {"model": "CONFIGURE_MODEL_BEFORE_USE", "model_provider": provider_id,
              "model_providers": {provider_id: provider}, "model_reasoning_effort": "high"}'''
            if old not in text and new not in text:
                raise ValueError('Setup source has changed; review the public export')
            text = text.replace(old, new)
            text = text.replace("local_bin = Path.home() / '.local/bin'", "local_bin = ROOT / 'bin'")
            text = text.replace("    path = ':'.join([str(local_bin), str(ROOT / 'bin'), config['node_root'] + '/bin'])",
                                "    user_entry = Path.home() / '.local/bin/agentflow'\n"
                                "    user_entry.parent.mkdir(parents=True, exist_ok=True)\n"
                                "    if not user_entry.exists() and not user_entry.is_symlink(): user_entry.symlink_to(wrapper)\n"
                                "    path = ':'.join([str(local_bin), str(Path.home() / '.local/bin'), config['node_root'] + '/bin'])")
        elif module == 'doctor.py':
            if 'checks["model-configuration"]' not in text:
                raise ValueError('Doctor must validate model configuration before public export')
        else:
            text = re.sub(r"'repo': '/home/[^']+/project/REPLACE_PROJECT'", "'repo': '/absolute/path/your-project'", text)
        for prefix in ('local/agent_platform/', 'bootstrap/local/agent_platform/'):
            result[prefix + module] = text.encode()
    for name, raw in list(result.items()):
        if name.startswith('local/agent_platform/'):
            result['bootstrap/' + name] = raw
    return result


def self_extracting_installer(kit: bytes, checksum: str, linux_script: bytes) -> bytes:
    header = r'''#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  printf '%s\n' 'Usage: bash install-agentflow.sh [--check] [--start] [--runtime-cache DIR] [--trust-current-container]'
  printf '%s\n' 'Bootstraps Ubuntu 24.04 Linux x86_64. Installs tools only; model credentials and project execution are configured separately.'
  exit 0
fi
check_only=0
validate_options() {
  while (( $# )); do
    case "$1" in
      --check) check_only=1 ;;
      --start|--trust-current-container) ;;
      --runtime-cache)
        if (( $# < 2 )); then printf '%s\n' '--runtime-cache requires a directory' >&2; exit 2; fi
        shift ;;
      *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
    esac
    shift
  done
}
validate_options "$@"
if (( check_only == 0 )); then
  bash -s -- --install <<'AGENTFLOW_LINUX_DEPS'
__LINUX_SCRIPT__
AGENTFLOW_LINUX_DEPS
elif ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python is missing; run the installer without --check to bootstrap Ubuntu prerequisites.' >&2
  exit 2
fi
bundle_sha='__BUNDLE_SHA__'
extract_root="$HOME/.local/share/agentflow/installers/$bundle_sha"
mkdir -p "$extract_root"
archive="$extract_root/package.zip"
sed '1,/^__AGENTFLOW_ARCHIVE__$/d' "$0" | base64 --decode > "$archive"
printf '%s  %s\n' "$bundle_sha" "$archive" | sha256sum --check --status
python3 - "$archive" "$extract_root" <<'AGENTFLOW_EXTRACT'
from pathlib import Path
import stat,sys,zipfile
destination=Path(sys.argv[2])
with zipfile.ZipFile(sys.argv[1]) as bundle:
    for info in bundle.infolist():
        target=destination/info.filename
        if not target.resolve().is_relative_to(destination.resolve()) or stat.S_ISLNK(info.external_attr >> 16):
            raise SystemExit('Unsafe package entry')
    bundle.extractall(destination)
AGENTFLOW_EXTRACT
exec bash "$extract_root/agentflow-platform/install-from-report.sh" "$@"
__AGENTFLOW_ARCHIVE__
'''
    header = header.replace('__BUNDLE_SHA__', checksum).replace('__LINUX_SCRIPT__', linux_script.decode().rstrip())
    return header.encode() + base64.encodebytes(kit)


def runtime_archive(root: Path, releases: Path) -> tuple[str, str]:
    names = {'downloads/temporal-cli.tar.gz': '09a0326a51db84d02735e53542b9ebd8c4758daf47482a9ab0abce15844e60d5',
             'bin/symphony': '08d7aac26747fdc14022ade870cf7e530a6343ab92a040f39a4294b27a0cd5af'}
    target = releases / RUNTIME_NAME
    contents = {}
    for name, expected in names.items():
        raw = (root / name).read_bytes()
        if sha(raw) != expected:
            raise ValueError('Runtime checksum mismatch: ' + name)
        contents[name] = raw
    contents['RUNTIME-SHA256SUMS'] = ''.join(expected + '  ' + name + '\n' for name, expected in names.items()).encode()
    raw = zip_bytes(contents, 'agentflow-runtime-linux-x86_64/')
    if not target.exists() or sha(target.read_bytes()) != sha(raw):
        atomic_write(target, raw)
    return RUNTIME_NAME, sha(raw)


def stack_rows(manifest: dict) -> str:
    versions = manifest['versions']
    rows = [
        ('实现 / Codex', '0.164.0；规划、分单元实现、集成', '原生工具、Responses API 与 worktree', '使用者配置自己的模型、API URL 与凭据变量', 'https://developers.openai.com/codex/cli/'),
        ('独立审查 / Codex', '0.164.0；新 ephemeral 会话审查固定候选', '复用 API 配置；不同角色与会话，不续接实现上下文', '默认同一模型；按只读指令审查并检查工作区与 HEAD 未变', 'https://developers.openai.com/codex/noninteractive/'),
        ('持久流程 / Temporal', 'CLI 1.9.1；SDK ' + versions['temporalio'], '历史、定时器、人工等待、重启恢复', '本地 SQLite 单机开发服务；Cloud 可后续接入', 'https://docs.temporal.io/develop/python'),
        ('工单入口 / Symphony', '固定 be10a1b79df7…；按项目 workspace + bridge', '持续领取工单与结果标签同步', '按项目配置自己的 tracker；nightly 严格校验', 'https://github.com/openai/symphony/tree/be10a1b79df723d6d7612b5651c8522704dafb2e'),
        ('互操作 / A2A', 'SDK ' + versions['a2a-sdk'] + '；版本头 1.0', '外部 agent 委托、查询、鉴权与共享所有权', 'localhost 服务；业务仍受模板与审批约束', 'https://a2a-protocol.org/v1.0.1/specification/'),
        ('服务管理 / Supervisor', versions['supervisor'] + '；管理五个开发服务', '适合无 systemd 的 Docker 容器', '容器重启后手动 services start；不等同取消作业', 'https://supervisord.org/'),
        ('实验记录 / MLflow', versions['mlflow'] + '；SQLite + 本地产物', '参数、指标、产物与代码/数据/环境绑定', '实验观测；正式任务状态由 Temporal 保存', 'https://mlflow.org/docs/latest/ml/tracking/'),
        ('候选搜索 / LangGraph', versions['langgraph'] + '；SQLite checkpoint', '有界 1–5 项提案、恢复与负面结果回流', '不会自动实施、调度或开始训练', 'https://docs.langchain.com/oss/python/langgraph/overview'),
        ('执行 / 可信容器 + 原生进程', 'namespace 绑定确认、独立 worktree、超时与取消 fence', '明确的容器边界和进程管理', '仅可信项目；agent 可访问该用户文件；无每任务 OS 隔离', ''),
        ('训练 / perfctl + 手动 runner', '固定 manifest / baseline / candidate / evidence SHA', '独立门禁、统计重算、人工放行', '控制 worker 默认关闭；资源、硬件与质量由项目配置验证', ''),
        ('环境 / uv + Python', 'uv 0.11.16 / Python 3.12；127 个锁定包', '平台依赖独立、哈希校验与可修复', 'CUDA/PyTorch 与业务环境由具体项目管理', 'https://docs.astral.sh/uv/'),
    ]
    output = []
    for name, role, strength, limit, url in rows:
        link = ' <a href="' + html.escape(url, quote=True) + '" target="_blank" rel="noopener noreferrer">官方资料 ↗</a>' if url else ''
        output.append('<tr><td>' + html.escape(name) + '</td><td>' + html.escape(role) + '</td><td>' + html.escape(strength) + '</td><td>' + html.escape(limit) + link + '</td></tr>')
    return ''.join(output)


def template_cards(root: Path) -> str:
    descriptions = [
        ('repository-governance', '仓库治理', '仓库导航、架构边界、重复问题防回归', ['input.json', 'LOCAL-GUIDE.md', 'input.schema.json'], '基线、行为、架构、知识、范围检查 → Codex 独立审查 → REVIEW_READY'),
        ('large-change', '大型变更', '跨模块接口、依赖 DAG、集成与可回滚迁移', ['input.json', 'LOCAL-GUIDE.md', 'input.schema.json'], '额外要求 integration / compatibility / migration-rollback 的真实检查'),
        ('training-optimization', '训练优化', '冻结 workload、基线、实验清单和可信 runner', ['experiment.json', 'baseline.json', 'workload-contract.md', 'runner-template.example.json', 'LOCAL-GUIDE.md'], '手动 run-local → perfctl 门禁 → AWAITING_RELEASE → 项目集成/复验任务'),
    ]
    cards = []
    for kind, label, purpose, files, gate in descriptions:
        buttons = ''.join('<button class="text-button" data-download="templates/' + kind + '/' + name + '">' + html.escape(name) + ' ↓</button><br>' for name in files)
        command = 'agentflow templates copy ' + kind + ' ~/project/MY_PROJECT/workflow-' + kind
        example_name = 'experiment.json' if kind == 'training-optimization' else 'input.json'
        example = (root / 'templates' / kind / example_name).read_text()
        cards.append('<div class="card"><span class="tag">' + kind + '</span><h3>' + label + '</h3><p>' + purpose + '</p><p class="mini">' + gate + '</p>' + code(command) + '<div class="downloads">' + buttons + '</div><details><summary>查看待填写的输入示例</summary><div class="detail-body">' + code(example) + '</div></details></div>')
    return ''.join(cards)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--legacy-copy', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source = root / 'bootstrap/report'
    releases = root / 'releases'
    releases.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / 'public-release.json').read_text())
    runtime_name, runtime_sha = runtime_archive(root, releases)

    payload = payload_files(root)
    outer = {'platform/' + name: raw for name, raw in payload.items()}
    outer['install-from-report.sh'] = (source / 'install-from-report.sh').read_bytes()
    outer['INSTALL.zh-CN.md'] = (source / 'public/INSTALL.zh-CN.md').read_bytes()
    outer['BUNDLE-MANIFEST.json'] = (json.dumps({'version': '2.2', 'export_date': VERSION, 'selection': manifest['selection'], 'versions': manifest['versions'], 'native_tools': manifest['native_tools'], 'accounts_exported': False}, ensure_ascii=False, indent=2) + '\n').encode()
    outer['BUNDLE-SHA256SUMS'] = ''.join(sha(raw) + '  ' + name + '\n' for name, raw in sorted(outer.items())).encode()
    kit = zip_bytes(outer, 'agentflow-platform/')
    kit_sha = sha(kit)
    atomic_write(releases / KIT_NAME, kit)
    installer = self_extracting_installer(kit, kit_sha, payload['bootstrap/install-multi-agent-linux-deps.sh'])
    installer_sha = sha(installer)
    atomic_write(releases / 'install-agentflow.sh', installer)
    template_files = {name.removeprefix('templates/'): raw for name, raw in payload.items() if name.startswith('templates/')}
    templates_zip = zip_bytes(template_files, 'agentflow-templates/')
    atomic_write(releases / ('agentflow-templates-' + VERSION + '.zip'), templates_zip)

    files = dict(payload)
    files['INSTALL.zh-CN.md'] = outer['INSTALL.zh-CN.md']
    files['install-from-report.sh'] = outer['install-from-report.sh']
    files['install-agentflow.sh'] = installer
    files['downloads/agentflow-templates.zip'] = templates_zip
    readme = chapters((root / 'README.zh-CN.md').read_text())
    temporal = json.loads((root / 'downloads/temporal-cli.json').read_text())
    symphony = json.loads((root / 'upstream/symphony/upstream.lock.json').read_text())
    research = (source / 'research.html').read_text()
    parts = {
        'STACK_ROWS': stack_rows(manifest), 'BOUNDARY': markdown(readme['执行配置与边界']),
        'PATHS': markdown(readme['持久目录']),
        'BOOTSTRAP_CODE': code('bash ~/Downloads/install-agentflow.sh\nsource ~/multi-agent-platform/env.sh\nagentflow doctor'),
        'EXPORT_CODE': code('unzip ' + KIT_NAME + '\ncd agentflow-platform\nbash install-from-report.sh'),
        'INSTALL': markdown((source / 'public/INSTALL.zh-CN.md').read_text()),
        'FIRST_INSTALL': markdown(readme['全新环境安装']), 'AUTH': markdown(readme['模型配置与认证']),
        'TEMPORAL_URL': html.escape(temporal['source_url'], quote=True), 'SYMPHONY_URL': html.escape(symphony['binary_url'], quote=True),
        'KIT_SHA256': kit_sha, 'INSTALLER_SHA256': installer_sha,
        'TEMPLATE_CARDS': template_cards(root),
        'DEVELOPMENT': markdown(readme['接入一个具体项目'] + '\n' + readme['开发任务的关键步骤']),
        'SEARCH': markdown(readme['候选搜索与实验']), 'GITLAB': markdown(readme['GitLab 与 Symphony 后续绑定']),
        'TRAINING': markdown((root / 'docs/TRAINING.md').read_text(), link_base='docs'),
        'SERVICES': markdown(readme['服务与交互']), 'BACKUP': markdown(readme['修复、验证与备份']),
        'VALIDATION': markdown((root / 'docs/VALIDATION.md').read_text()), 'RESEARCH': research,
    }
    body = (source / 'public-manual-body.html').read_text()
    for name, content in parts.items():
        body = body.replace('{{' + name + '}}', content)
    if re.search(r'\{\{[A-Z_]+\}\}', body):
        raise ValueError('Unresolved report placeholder')
    head = (source / 'base-head.html').read_text()
    head = re.sub(r'<title>.*?</title>', '<title>多 agent 平台 · 从零安装、模板与使用手册 v2.2</title>', head)
    head = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="公开多 agent 工作流：全新 Linux 一键安装、三个模板、部署使用与训练优化完整手册">', head)
    head += '<style>.rail{overflow-y:auto}.rail nav{margin:20px 0}.rail-foot{padding-top:16px}.downloads{overflow-wrap:anywhere}section>h3{margin-top:25px}.grid3 .tag{font-size:10px;overflow-wrap:anywhere}details .detail-body>h3{margin-top:20px}.training-appendix{margin-top:34px}.hero .muted{max-width:900px}.runtime-note{font-size:12px}code.mono{display:inline-block;max-width:100%}@media(max-width:760px){.hero .actions button{min-width:160px}.rail{overflow:visible}.grid3{grid-template-columns:minmax(0,1fr)}}@media print{details>summary{font-size:12pt}.code-wrap pre{white-space:pre-wrap;overflow-wrap:anywhere}}</style>'
    nav = [('platform', 'A 工具栈与边界'), ('portable-deploy', 'B 安装与下载'), ('task-templates', 'C 三个适配模板'), ('dev-deploy', 'D 项目与开发使用'), ('training-local', 'E 逐实验训练'), ('dev-operations', 'F 运维与验收'), ('training-appendix', 'G 优化研究附录')]
    links = ''.join('<a href="#' + key + '">' + label + '</a>' for key, label in nav)
    rail = '<aside class="rail"><div class="brand"><small>AGENTFLOW</small>工作流部署与使用</div><nav>' + links + '</nav><div class="mobile-nav">' + links + '</div><div class="rail-foot"><p>使用清单 <span id="progress-text">0 / 0</span></p><progress id="progress" value="0" max="1"></progress><p>仅保存到此浏览器，<br>不会批准或启动任务。</p><button id="reset" class="text-button">重置清单</button><p>公开版 v2.2 · 2026.10.28<br>持久资产保存到 home</p></div></aside>'
    setup = (root / 'docs/PROJECT-ONBOARDING.zh-CN.md').read_text()
    data = {'version': '2.2', 'kitFilename': KIT_NAME, 'kitSha256': kit_sha, 'files': {name: base64.b64encode(raw).decode() for name, raw in sorted(files.items())}, 'zip': base64.b64encode(kit).decode(), 'setup': setup}
    script = (source / 'report.js').read_text()
    script = script.replace("saveBase64(data.zip,'training-efficiency-kit.zip','application/zip')", "saveBase64(data.zip,data.kitFilename,'application/zip')")
    script = script.replace("'training-efficiency-v1-checks'", "'agentflow-public-v2.2-checks'")
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    document = head + '</head><body><a class="skip" href="#main">跳到正文</a><div class="shell">' + rail + '<main id="main">' + body + '</main></div><div class="toast" id="toast" role="status" aria-live="polite"></div><script id="artifact-data" type="application/json">' + encoded + '</script><script>' + script + '</script></body></html>'
    raw = document.encode()
    output = root / 'reports/multi-agent-development-platform.html'
    atomic_write(output, raw)
    if args.legacy_copy:
        target = args.legacy_copy
        if target.exists() and target.read_bytes() != raw:
            atomic_write(root / 'reports/history' / ('previous-' + sha(target.read_bytes())[:12] + '.html'), target.read_bytes())
        atomic_write(target, raw)
    atomic_write(releases / 'SHA256SUMS', ''.join(value + '  ' + name + '\n' for name, value in [(KIT_NAME, kit_sha), ('install-agentflow.sh', installer_sha), (RUNTIME_NAME, runtime_sha), ('agentflow-templates-' + VERSION + '.zip', sha(templates_zip))]).encode())
    result = {'version': '2.2', 'html': str(output), 'html_sha256': sha(raw), 'html_bytes': len(raw), 'source_bundle': str(releases / KIT_NAME), 'source_bundle_sha256': kit_sha, 'installer_sha256': installer_sha, 'source_files': len(payload), 'downloadable_files': len(files), 'runtime_cache': str(releases / runtime_name), 'runtime_sha256': runtime_sha, 'templates_sha256': sha(templates_zip)}
    atomic_write(root / 'reports/build-manifest.json', (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
