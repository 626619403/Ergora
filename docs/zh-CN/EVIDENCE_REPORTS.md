# 从原证据生成报告

[English](../EVIDENCE_REPORTS.md) · 简体中文 · [文档入口](../README.zh-CN.md)

`evidence-report` 提供只读报告作者 `ergora-evidence-report-author@1.0.0`，根为 `ergora-evidence-report@1.0.0`，独立叶为 `root/author`。它把操作者完整提供的工程、研究或实验材料整理为 Markdown 和静态自包含 HTML，给出来源、实际覆盖与未验证范围。它与 [`review report`](../LOCAL_REVIEW.md) 的程序汇总不同：后者读取原 reviewer runs，不调用 LLM；本叶是一次明确的报告作者调用，不产生正式批准。

## 优化报告

显式选择 `optimization-report` 可使用作者／根的 `@2.0.0`，叶仍为 `root/author`，只读上限与原四字段出口保持。新版完整保留通用证据报告 Skill，另带专门的[优化报告 Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/SKILL.md)及[占位结构模板](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/assets/optimization-report-template.md)。模板全文作为 context 进入冻结提示；原 `evidence-report` 选择仍是 `@1.0.0`。

提供完整原任务、算法／计算依赖／数据流分析（例如原 `training-flow-map` 结果）、冗余证据、baseline、每项保留试次的完整配置、真实产物位置、原测量与质量检查。报告依次展示范围／目标、源码流程与冗余假设、可比 baseline／候选表、诊断、决定与剩余瓶颈；保留完整组合配置、负结果、缺证据以及实测／估算／未验区别。不同阶段、硬件或有效工作量分表，MFU 按适用性选用。报告作者不运行前驱图谱或测量性能。

```bash
ergora composition install-preset optimization-report
ergora composition show ergora-evidence-report 2.0.0 --material
```

然后沿下文 grant 与显式调用流程，把 `prepare-manifest` 版本换成 `2.0.0`，选择新的 manifest／input／output 目录。原证据、静态 HTML 检查和显式导出义务保持。资源／加载验证及未运行范围见[交付记录](../delivery/2026-11-16-optimization-report-skill.md)。

## 准备原材料

先按原 owner 读取机器可核证据。例如使用 [`composition inspect-run`](../WORKFLOW_DEFINITIONS.md#按精确-id-读取原组合运行) 的完整原 input／prompt／result、`review report --format json` 的完整覆盖观察、任务交接包的完整选中材料，或[训练原实验与归档](../TRAINING.md)。保留原 JSON／Markdown／日志，不用报告替换它们。列表、摘要或有界窗口只证明其实际读取范围。

在 UTF-8 `report-task.md` 中写明读者、问题、报告范围、材料身份／时间及全文或明确选段。为每个来源给出路径／URL／原 run ID、已核 SHA256／Git OID，以及谁核过原字节。只提供身份字符串时，作者会标为操作者提供，不能自证匹配。缺失附件、失败尝试、少数反对、未完成成员与尚未运行的检查一并交给作者。性能／质量主张还需真实 baseline／candidate、固定 workload／配置／环境、原数据、单位、样本／窗口与独立正确性／质量覆盖。

可在任务末尾写：

```text
请给维护者生成本次材料的证据报告。先回答问题，逐项引用来源 ID，
区分原记录、推论、建议和未验证范围。保留失败、反对和缺覆盖。
同时返回 Markdown 和完整静态 HTML；若没有测量数据，使用说明图或表格。
只使用下面实际提供的材料，不补造未读资料或实测数字。
```

若产物将公开，先准备可以公开的来源内容和逻辑标识；私人原件保持原有访问边界。这个只读叶不会自动读取仓库、抓网页、执行 parser／profile 或运行工作流前驱。

## 固定定义并显式调用

以下操作复用[完整 manifest 与单叶输入](../WORKFLOW_DEFINITIONS.md#准备完整的单叶输入)。先[注册项目](../PROJECTS.md)并认证实际后端；定义导入只发布到本地版本库，不安装 CLI、不改项目绑定、不授予执行权限。

```bash
ergora composition install-preset evidence-report
ergora composition show ergora-evidence-report 1.0.0 --material
```

保存 `report-grant.json`；此处与新根的精确只读上限一致：

```json
{
  "schema_version": 1,
  "permissions": {"read": ["definitions"], "write": [], "shell": false, "network": []},
  "limits": {"depth": 4, "instances": 8, "concurrency": 1, "material_bytes": 131072}
}
```

```bash
ergora composition prepare-manifest ergora-evidence-report 1.0.0 \
  --grant ./report-grant.json --directory ./report-manifest
ergora composition prepare-from-manifest ./report-manifest root/author \
  --task ./report-task.md --directory ./report-input --max-prompt-bytes 250000
ergora composition verify-input ./report-input --material
ergora composition check-input my-project ./report-input --mode text-only --backend codex
ergora composition run-input my-project ./report-input --mode text-only --backend codex \
  --backend-reason "Explicit report author selection" --timeout 300
ergora composition inspect-run my-project RUN_ID > ./report-observation.json
```

Skill 全文自包含，text-only 内联读取即可，无需 MCP 附件或新工具授权。`max-prompt-bytes` 约束完整提示 UTF-8 字节，不承诺模型容量。内置作者要求 Codex `gpt-6.1-sol` 且推理强度至少 `high`，覆盖须满足定义下限。其他后端示例仅适用于未声明该下限的自定义定义，并仍须通过实际职能／模式准入。自定义provider按需通过`--codex-config`提供操作者原推理配置，模板不保存provider凭据。检查不会调用模型，也不证明安装／认证。没有自动失败回退或隐式重发；失败、unknown 或超时先保留原 run 并按原 owner 对账。

## 查看原结果并导出阅读视图

检查观察中的 `run.status` 及 `input.available`、`prompt.available`、`result.available`，不能仅凭 CLI exit 0 称报告成功。原完整结果仍在 `result.document`；外层沿用 `summary` 与 `artifacts.response`。response 是一个约定的 JSON 字符串：

|字段|作者返回的内容|
|---|---|
|`markdown`|完整 Markdown 报告，含来源及限制|
|`html`|同一结论／数值／来源／限制的完整静态 HTML；仅明确请求 Markdown alone 时可为空|
|`sources`|`id/reference/identity/coverage` 字符串对象数组，标明真实读取与身份核验范围|
|`limitations`|缺失、未读、未验或不适用范围字符串数组|

这是提示约定，不是运行时另加的可信 schema。原 result envelope 合格不证明 JSON 字符串正确、事实真实、两视图一致、CSP 有效或浏览器布局已验。先审阅原结果，保留 observation 与所有原机器材料，再明确导出到一个新目录；例如：

```bash
python - ./report-observation.json ./report-views <<'PY'
import json
from pathlib import Path
import sys

observation = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if observation["run"]["status"] != "succeeded" or not all(
        observation[name]["available"] for name in ("input", "prompt", "result")):
    raise SystemExit("Original report run or material is incomplete; retain and inspect it")
response = observation["result"]["document"]["artifacts"]["response"]
report = json.loads(response)
destination = Path(sys.argv[2])
destination.mkdir()
(destination / "report.json").write_bytes(response.encode("utf-8"))
(destination / "report.md").write_bytes(report["markdown"].encode("utf-8"))
if report["html"]:
    (destination / "report.html").write_bytes(report["html"].encode("utf-8"))
PY
```

导出只解码原模型字符串，不手工改写 HTML 冒充 Agent 输出，也不覆盖原件。打开 HTML 前检查来源／片段以转义文本呈现，无脚本、事件处理、远程样式／图片／字体、iframe 或表单；完整自包含页面应带限制性 meta CSP。Markdown、来源表与 HTML 的结论、失败和限制须一致，量化图绑定真实原数据。若输出不合格，保留首次结果，明确新调用后另存新版本；这不是自动批准或重试器。

HTML 的导航、表格、内联 SVG 与原生折叠用于阅读，页面没有执行、批准、采用或 release 状态。检查通过、模型建议与真实证据验收分别记录。需要外部发布、训练、候选采用或人工 release 时，继续使用其原授权及 owner。

方法来源见[研究](../research/2026-11-15-evidence-report-generation.md)及随包 [Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author/skills/ergora-evidence-report/SKILL.md)。实际验证范围与限制见[交付](../delivery/2026-11-15-evidence-report-generation.md)。
