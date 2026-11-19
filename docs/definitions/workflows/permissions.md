# Inherited resources, permissions and static budgets

English · [Documentation](../../README.md) · [简体中文](../../zh-CN/definitions/workflows/permissions.md)

## Complete inheritance and conflicts

Each leaf assembles every ancestor's Skill instructions/context and each level's initial instructions in root→parent→self order. Composition templates add no model calls themselves. Preview provides each complete body, content identity, every source, complete assembled body and SHA; a Skill's required body is `SKILL.md`, while scripts and other directory attachments remain resources read as needed.

A logical resource ID with different content or kinds is refused. Same-named Skills are checked by their actual frontmatter loading name; different trees are refused. Matching names/trees may be merged while preserving every logical ID/source and verifying every source is readable. Last-writer-wins does not replace ancestors. Sibling/predecessor Skills are not inherited; predecessors supply only port data. Repeated references do not share mutable sessions.

A preview of complete static-material delivery does not establish model understanding, compliance or actual reading. Actual calls fix the original instance and current task body, check complete input capacity and retain loading evidence; insufficient capacity is refused without silent truncation. Formal `dag-v1` adds explicitly bound predecessor artifacts according to its frozen version (the [material contract](contracts.md#specialist-writers-and-original-work-units) supplies declared artifacts and trusted checks/opinions); independent `run-input` still calls one leaf only.

## Permission paths and budgets

The preview grant file uses the schema's `$defs/grant`: `schema_version: 1` with complete `permissions` and `limits`. [preview-grant.json](../../../examples/composition/preview-grant.json) is illustrative; operators should narrow it to their projects. It is currently an explicit static input, unconnected to project configuration or formal approval.

|Permission field|Exact semantics|
|---|---|
|`read`|Array of readable logical subtrees, such as `workspace/src` and `definitions/agent/architecture-reviewer/1.0.0`; `definitions` represents the entire definition asset library.|
|`write`|Array of writable workspace subtrees, such as `workspace/src`; definition-library writes cannot be declared, and write permission does not implicitly grant reads.|
|`shell`|Whether subprocess execution is requested; a Skill script's presence does not grant this permission.|
|`network`|Array of exact canonical HTTP(S) origins, such as `https://api.example.com`; hosts must be lowercase ASCII DNS names (punycode for international domains) or IP literals, IPv6 must be compressed, and default ports omitted. Paths, credentials, queries, fragments, whitespace and wildcards are refused.|

Paths use `/` and case-sensitive path-segment containment; `workspace/src` cannot grant `workspace/src-other`. `..`, host absolute paths and globs are refused. Logical `workspace` is reserved for the project workspace at execution time; `definitions/{agent,workflow}/ID/VERSION/path` represents exact package resources. These are not current OS mount points and preview neither creates nor enforces them automatically.

The root request must fit within the grant; subworkflow requests must fit within their parents, and Agent nodes within their owning workflow. Every level is checked, transitively satisfying every ancestor. Every origin path of each required resource must fit the current instance's read scope; Skills require their entire directory to be readable. Narrowing that excludes ancestor materials fails rather than dropping materials or silently elevating privileges. Preview's `backend_request.sandbox` is only a backend request; it cannot override this chain or prove OS isolation. See [pre-call capability checks](leaf-calls.md#inspect-capabilities-and-permissions-before-invocation) for the actual `enforced/advisory/unsupported` loading matrix.

All four `limits` fields are required; booleans, floats and values outside supported ranges are refused:

|Field|Counting and supported ceiling|
|---|---|
|`depth`|Root depth is 1, increasing by 1 per structural node; each subtree counts its local depth from 1 while every ancestor/project depth is checked simultaneously. Maximum 16.|
|`instances`|Includes the root, every Workflow reference, every Agent and all-join; repeated references count separately. Constrained per subtree and globally. Maximum 512.|
|`concurrency`|Shared quotas per structural scope; leaf previews list every scope. Formal parallel review obeys project and all ancestor-scope ceilings together; a branch waiting on a narrow subtree does not occupy ancestor capacity. Maximum 64; independent leaf calls do not schedule the graph.|
|`material_bytes`|Total UTF-8 bytes of all leaves' complete static prompts, including source markers; repeated calls count separately. Constrained per subtree and globally. Maximum 1,000,000; future port values are excluded.|

These are hard ceilings of the bounded static format; they promise neither performance, model capacity nor execution at arbitrary concurrency. Smaller project/subtree limits can refuse oversized compositions during compilation.

Independent branches can select different backends, models and [reasoning levels](../../agents/backends.md#set-reasoning-effort-for-each-agent). For example, set these separately in a formal task's `composition.backend_overrides`:

```json
{
  "root/structure/review": {
    "binding": {"tool":"codex","reasoning_effort":"high"},
    "reason": "结构设计审查采用较高推理强度"
  },
  "root/correctness/review": {
    "binding": {"tool":"claude-code","effort":"medium"},
    "reason": "正确性审查使用独立后端"
  }
}
```

Paths must identify actual leaves in this manifest, and every backend must pass the selected mode's capability check; the task page's composition configuration can generate the same binding. Formal review and work-unit runners start branches as dependencies become ready and shared quotas permit. Execution/review backend diversity still follows the original `diversity` configuration. `composition run-input` calls only one leaf; arbitrary mixed-node graphs and general Repeat execution remain covered by implementation plans.

These explicit per-Agent levels are retained in exact definitions and frozen task bindings. A requested value, its projection into native CLI arguments/configuration, and an actually observed native value are separate facts; without native evidence, actual application remains unknown. Unified fixed/preset/planner/automatic tuning selection remains future work; existing workflow presets do not implement tuning presets. No level/model fallback or budget increase is implicit. See the [backend guide](../../agents/backends.md#set-reasoning-effort-for-each-agent) for mode-specific limits.

Continue: [Revise and share exact workflow versions](revisions.md) · [Invoke and inspect one frozen workflow leaf](leaf-calls.md).
