# Generate reports from original evidence

English · [简体中文](zh-CN/EVIDENCE_REPORTS.md) · [Documentation](README.md)

<a id="从原证据生成报告"></a>

The `evidence-report` preset provides the read-only author `ergora-evidence-report-author@1.0.0`, workflow root `ergora-evidence-report@1.0.0`, and standalone leaf `root/author`. It organizes complete engineering, research or experiment material supplied by the operator into Markdown and static self-contained HTML, with sources, actual coverage and unverified scope. Unlike the programmatic [`review report`](LOCAL_REVIEW.md), which reads original reviewer runs without an LLM call, this leaf is an explicit report-author invocation. It does not issue formal approval.

<a id="准备原材料"></a>
## Prepare original material

Read machine-checkable evidence through its original owner first. Examples include complete input/prompt/result from [`composition inspect-run`](WORKFLOW_DEFINITIONS.md#按精确-id-读取原组合运行), the complete coverage observations from `review report --format json`, fully selected handoff-packet materials, or [original training experiments and archives](TRAINING.md). Preserve original JSON/Markdown/logs; the report does not replace them. Lists, summaries and bounded windows establish only the coverage actually read.

In a UTF-8 `report-task.md`, state the audience, question, report scope, source identities/times, and full text or explicitly selected excerpts. For each source, provide its path/URL/original run ID, verified SHA256/Git OID and who checked the original bytes. When only an identity string is supplied, the author must mark it as operator-provided; the string cannot prove its own match. Include missing attachments, failed attempts, minority objections, incomplete members and unrun checks. Performance/quality claims also require the real baseline/candidate, fixed workload/configuration/environment, original data, units, samples/windows and independent correctness/quality coverage.

You can end the task with:

```text
Write an evidence report for maintainers from this material. Answer the question first,
reference source IDs for each claim, and distinguish original records, inferences,
recommendations and unverified scope. Preserve failures, objections and missing coverage.
Return both Markdown and complete static HTML. Without measurement data, use an
explanatory diagram or table. Use only the material actually supplied below;
do not invent unread sources or measured numbers.
```

For public output, prepare shareable source content and logical identifiers first; private originals retain their access boundaries. This read-only leaf does not automatically read a repository, fetch websites, execute a parser/profiler or run workflow predecessors.

<a id="固定定义并显式调用"></a>
## Pin the definition and invoke explicitly

Reuse the [complete manifest and single-leaf input](WORKFLOW_DEFINITIONS.md#准备完整的单叶输入). [Register the project](PROJECTS.md) and authenticate the actual backend first. Importing definitions publishes only to the local definition library; it does not install a CLI, change project bindings or grant execution permission.

```bash
ergora composition install-preset evidence-report
ergora composition show ergora-evidence-report 1.0.0 --material
```

Save `report-grant.json` with the new root's exact read-only ceiling:

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

The full Skill is self-contained and can be inlined in text-only mode, without MCP attachments or new tool grants. `max-prompt-bytes` limits the complete UTF-8 prompt; it does not promise model capacity. Codex is a replaceable binding. Use the same `check-input/run-input` flow to select another backend supporting this role/mode and record the reason; model names are backend-specific. Checking admission does not call the model or establish installation/authentication. There is no automatic failure fallback or implicit resend. Retain failed/unknown/timed-out original runs and reconcile through their original owner.

<a id="查看原结果并导出阅读视图"></a>
## Inspect the original result and export reading views

Inspect `run.status` plus `input.available`, `prompt.available` and `result.available` in the observation. CLI exit 0 alone does not establish report success. The complete original result stays in `result.document`, with the existing `summary` and `artifacts.response` envelope. The response is a JSON string specified by the authoring prompt:

|Field|Author output|
|---|---|
|`markdown`|Complete Markdown report with sources and limits|
|`html`|Complete static HTML with the same conclusions/numbers/sources/limits; may be empty only when Markdown alone was explicitly requested|
|`sources`|Array of objects with string fields `id/reference/identity/coverage`, recording actual reading and identity-verification coverage|
|`limitations`|String array of missing, unread, unverified or inapplicable scope|

This is a prompt convention, not an additional trusted runtime schema. A valid outer result envelope does not establish valid inner JSON, factual accuracy, agreement between views, effective CSP or checked browser layout. Inspect the original result, preserve the observation and all original machine-readable material, then explicitly export into a new directory. For example:

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

Export decodes the original model string without overwriting originals or manually rewriting HTML as purported Agent output. Before opening HTML, check that source text/excerpts are escaped, with no scripts, event handlers, remote styles/images/fonts, iframes or forms. A complete self-contained page should include a restrictive meta CSP. Markdown, source tables and HTML must agree on conclusions, failures and limits; quantitative charts must cite real original data. If output is unsuitable, retain the first result and explicitly make another call into a new version. Export is not an automatic approval/retry mechanism.

HTML navigation, tables, inline SVG and native disclosure elements are reading aids. The page has no execution, approval, adoption or release status. Record static checks, model recommendations and actual evidence acceptance separately. External publication, training, candidate adoption and human release use their existing authorization and owners.

Method sources: [research](research/2026-11-15-evidence-report-generation.md) and the bundled [Skill](../src/ergora/data/presets/agents/ergora-evidence-report-author/skills/ergora-evidence-report/SKILL.md). Original validation and limits: [delivery record](delivery/2026-11-15-evidence-report-generation.md).
