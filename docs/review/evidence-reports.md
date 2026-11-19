# Write reports from original evidence

English · [Documentation](../README.md) · [简体中文](../zh-CN/review/evidence-reports.md)

The `evidence-report` preset provides the read-only author `ergora-evidence-report-author@1.0.1`, workflow root `ergora-evidence-report@1.0.1`, and standalone leaf `root/author`. It organizes complete engineering, research or experiment material supplied by the operator into Markdown and static self-contained HTML, with sources, actual coverage and unverified scope. Unlike the programmatic [`review report`](materials.md), which reads original reviewer runs without an LLM call, this leaf is an explicit report-author invocation. It does not issue formal approval.

## Optimization reports

Select `optimization-report` for the explicitly versioned author/root `@2.0.1`, with the same `root/author`, read-only ceiling and four-field response. It retains the complete general evidence-report Skill and adds a dedicated [optimization-report Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/SKILL.md) and [placeholder layout](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/assets/optimization-report-template.md). The entire layout is a context resource included in the frozen prompt. The existing `evidence-report` selection remains `@1.0.1`.

Supply the complete original task, algorithm/computation/data-flow analysis (for example, the original `training-flow-map` result), redundancy evidence, baseline and every retained trial's full configuration, actual output locations, raw measurements and quality checks. The report proceeds from scope/objective to source flow and redundancy hypotheses, then comparable baseline/candidate tables, diagnosis, decisions and remaining bottlenecks. It preserves complete combined settings, negative results, missing evidence and measured/estimated/unverified distinctions. Different phases, hardware or useful work use separate tables; MFU is optional. This author does not run the flow-map predecessor or measure performance.

```bash
ergora composition install-preset optimization-report
ergora composition show ergora-evidence-report 2.0.1 --material
```

Then use the grant and explicit invocation flow below, replacing the `prepare-manifest` version with `2.0.1` and choosing fresh manifest/input/output directories. Original evidence, static HTML checks and explicit result export retain the same obligations. The report does not validate the workload or establish performance acceptance.

## Prepare original material

Read machine-checkable evidence through its original owner first. Examples include complete input/prompt/result from [`composition inspect-run`](../definitions/workflows/leaf-calls.md#read-an-original-composition-run-by-exact-id), the complete coverage observations from `review report --format json`, fully selected handoff-packet materials, or [original training experiments and archives](../training/overview.md). Preserve original JSON/Markdown/logs; the report does not replace them. Lists, summaries and bounded windows establish only the coverage actually read.

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

## Pin the definition and invoke explicitly

Reuse the [complete manifest and single-leaf input](../definitions/workflows/leaf-calls.md#prepare-complete-single-leaf-input). [Register the project](../projects/registration.md) and authenticate the actual backend first. Importing definitions publishes only to the local definition library; it does not install a CLI, change project bindings or grant execution permission.

```bash
ergora composition install-preset evidence-report
ergora composition show ergora-evidence-report 1.0.1 --material
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
ergora composition prepare-manifest ergora-evidence-report 1.0.1 \
  --grant ./report-grant.json --directory ./report-manifest
ergora composition prepare-from-manifest ./report-manifest root/author \
  --task ./report-task.md --directory ./report-input --max-prompt-bytes 250000
ergora composition verify-input ./report-input --material
ergora composition check-input my-project ./report-input --mode text-only --backend codex
ergora composition run-input my-project ./report-input --mode text-only --backend codex \
  --backend-reason "Explicit report author selection" --timeout 300
ergora composition inspect-run my-project RUN_ID > ./report-observation.json
```

The full Skill is self-contained and can be inlined in text-only mode, without MCP attachments or new tool grants. `max-prompt-bytes` limits the complete UTF-8 prompt; it does not promise model capacity. The bundled author requires Codex `gpt-6.1-sol` with at least `high` reasoning effort; overrides must satisfy that definition minimum. Other-backend examples apply to custom definitions without this minimum and still require actual role/mode admission. Supply the operator's existing provider configuration through `--codex-config` when needed; templates store no provider credentials. Checking admission does not call the model or establish installation/authentication. There is no automatic failure fallback or implicit resend. Retain failed/unknown/timed-out original runs and reconcile through their original owner.

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

The bundled [report Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author/skills/ergora-evidence-report/SKILL.md) defines the author's method and output obligations.

Continue: [Read original evidence and export a candidate](../development/evidence-and-export.md) · [Read training evidence and approve exact results](../training/evidence-and-approval.md).
