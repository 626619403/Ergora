# Agent backends bilingual guide: independent review

2026-11-16. Fresh-context reviewer: `bilingual_agent_backends_review` (`/root/documentation_owner/bilingual_agent_backends_review`). Scope: complete documentation sub-batch 3a, requirement compliance and maintainability. The reviewer received the raw requirements, baseline, six-file manifest, complete tracked/untracked patch and actual receipts, without the implementation conversation. Only this review report was written by the reviewer.

## Candidate and requirements

Documentation baseline and observed HEAD: `af534034cfb0264f9ec99424ec35b6a8eaca22c8`, branch `refactor/architecture-foundations`. Public product source: `6cec589f404b17f4828a70807d5e33d89fad3fa0`; an independent `git diff` against that identity found no source changes. Concurrent checkpoint, handoff and S2 work is excluded.

The requirement is a complete maintained English/Chinese guide pair, with English at the existing default path, reciprocal links, all original heading targets and commands, and unchanged recovery, platform, permission and six-stage boundaries. An index or summary alone is insufficient. Added option/status statements must distinguish frozen requests, CLI projections and actual native observations; optional availability and unsupported paths must remain visible. Neither source-journal drafts nor earlier CI/runtime results can grant new backend support.

The complete original is 287 lines / 29,818 bytes, SHA256 `40eb4c43476746816fbd776c4b9aa596c86ae11a21a413ef8db40af1a27ee565`. Its saved bytes were independently compared with the Git baseline. Initial complete patch: `.ergora/checks/bilingual-agent-backends-guide/r1/complete.patch`, SHA256 `7ec17030c3c6f1a0d47fb399211ee7c7ef0ba25ec5033968b4b5a37bc3639198`.

The accepted same-slice correction is frozen in `.ergora/checks/bilingual-agent-backends-guide/evidence-fix-r2/`: complete patch SHA256 `f675a81450b7d674936aeb43e3a3c042b08555431f48370921dbe0b4053f8f76`. All six current files match that manifest:

|File|Accepted SHA256|
|---|---|
|[English guide](../AGENT_BACKENDS.md)|`2ff5ab95c2a1fa65eb1c8284df6314a96d73e4993bc7e6b25caa5d75039ce326`|
|[Chinese guide](../zh-CN/AGENT_BACKENDS.md)|`548466fe4a843c9d1a58b29cca2e646133c102f15c8599085356eacacffd2261`|
|[English index](../README.md)|`c414c7e822f249fae22d9fc3d4a1890202c58d4df9be16d438aabb3b70ad9338`|
|[Chinese index](../README.zh-CN.md)|`697ca9ffc34da11a3f5b752373706ac6abf0772786027bb6fe289d814cbef74c`|
|[Batch plan](../plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md)|`3618c225f314375adb31e9a7fa7ac249bc3158a7b00224cf314fc4d759b11180`|
|[Delivery record](2026-11-16-bilingual-agent-backends-guide.md)|`81505b383493167646d33e016dcf5993a7d6dde2b842aade252355ea54ea171f`|

The initial delivery hash was `90cecfd9f461ff3866748f3d5e0831c64cf47c299623055ca715ac191ae02d60`; its correction is described below. The other five author files are unchanged between r1 and r2. Subsequent review-status bookkeeping has its own identity and does not extend this semantic acceptance to other guide batches.

## Verdicts

|Axis|Final verdict|Open findings|
|---|---|---|
|Requirement compliance|**Approve within this documentation slice**|0 — F1 corrected and rechecked|
|Maintainability|**Approve within this documentation slice**|0|

Both guides are complete. The English translation preserves the original role, structured-command, mini, DeepSeek history/continuation, formal bridge, Forge, component-extension and writable-work contracts. The Chinese body preserves the complete original apart from language navigation, relative-link relocation and the disclosed matching section. Existing heading targets remain reachable at the English default path.

The new section correctly separates a frozen requested effort from `-c model_reasoning_effort=...` / `--effort` and from actual applied behavior, which remains unknown without native evidence. It invents no effective-effort output field. Unified fixed/preset/planner/automatic selection remains unimplemented; existing explicit fields, workflow presets and native profiles do not imply that selector. Claude text-only safe-mode/workflow limits and DeepSeek registry capacity versus a demonstrated request cap are stated without transferring upstream options into Ergora fields. Design-policy registration remains storage-only, private S2 remains unreleased, schema3 effects remain closed, and original schema1 contracts retain their scope.

The documentation stays with existing guide and index owners, links to canonical research and operating contracts, and introduces no source/configuration abstraction or parallel implementation. Runtime availability, pins, supported modes, recovery and evidence limits remain explicit. No separate maintainability finding was identified.

## F1 — P3: correct official-source attribution — closed

Initial location: [delivery record, line 21](2026-11-16-bilingual-agent-backends-guide.md). The r1 paragraph grouped the fetched configuration and security pages as support for model/client-dependent effort and sandbox configuration.

The saved security response is genuinely HTTP 200 with SHA256 `c482fd65e3872732453a14896cd64e069d4ae5d3b1d403d3278c6029f2a5de57`, but its main heading is “Codex Security” and its body describes vulnerability scanning. It explicitly sends readers elsewhere for permissions and sandbox controls governing Codex itself. A reader following that evidence attribution would reach a different product surface and could mistake successful retrieval for support of an agent-control claim. This does not invalidate the guide: its configuration citation and the cached configuration reference do support the stated controls.

Minimal correction requested: attribute effort/sandbox statements to the configuration reference alone; retain the security response as a retrieval observation and state that it is not agent-control evidence. No new fetch or product change is needed.

The author made exactly that correction in r2. The reviewer reconstructed the initial delivery from the complete r1 patch and independently compared it with the corrected file: only that paragraph changed. It now identifies the vulnerability-scanning landing page and excludes it from Agent permission/sandbox evidence. The other five file hashes are unchanged. F1 is closed; no new finding arose. The initial requirement verdict was request-changes for this attribution correction; maintainability was approved throughout.

## Checks and limits

- Read root instructions, current checkpoint, Git branch/status/recent commits, the maintainable-project-delivery skill and independent-review brief. Read the raw original/requirements and patch before using the author narrative, then inspected the entire English and Chinese guides and all added sections.
- Independently verified the six initial/final file hashes, original Git bytes, both complete-patch hashes and both cached official HTML hashes/sizes. Applied OpenAI Docs guidance to the already fetched official material; the configuration reference explicitly describes model/client-dependent effort and sandbox settings. No new network request was made. The recorded unavailable search tool and direct-search 404 remain retrieval limits.
- Independently ran read-only, in-memory structural checks: six strict UTF-8 files, closed fences/final newlines/whitespace, 206 local links/fragments, reciprocal guide navigation, all 13 original heading targets, all 19 executable blocks and all 114 original inline-code occurrences/counts. Confirmed complete Chinese-body preservation after removing only the disclosed navigation/addition and reversing relative-link relocation. The English guide uses 12 explicit legacy aliases; the unchanged mini heading retains its automatic target. Scoped tracked `git diff --check` passed.
- Inspected current `agent_backends.py`, `agents.py`, `components.json`, `agent_runs.py`, `task_mcp.py`, the DeepSeek/mini/Forge drivers, `kernel.py`, `processes.py`, `reference_executor.py`, `task_design.py` and the schema3 execution guard. Checked actual argument projection, mode/platform admission, explicit workspace boundary, native-history identity/paging, one-use continuation intent/freeze/unknown/wall-time behavior, process ownership, Forge source/config identity and reconciliation, and closed design/training execution paths. The guide preserves these contracts without claiming new isolation or quality acceptance.
- Checked current effort enums and optional catalog pins against the guide/receipts: mini `04d809ceab9df28f9adaed044884180159172930`, Forge `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`, DeepSeek SDK/runtime-bin `0.2.2rc2`. Read the already independently reviewed backend-options research and its closed Claude safe-mode finding; its observed CLI versions are historical research observations, not newly measured versions here.
- Inspected the author's checker and parser argv/stdout/stderr: 31 fenced Ergora examples parsed with `-I -B` and no handler dispatch; numeric placeholders were substituted only in parser arguments. Compared the preserved examples and relevant current CLI declarations. The reviewer did not rerun an installed CLI or SDK. The r2 static receipt correctly retains the original parser evidence rather than claiming another run.

No backend/model invocation, SDK probe, installation, product test, service, browser, credential/environment snapshot, Git-index operation, commit or push was performed. Static/source review does not establish actual native availability, applied effort, provider acceptance, Windows execution, cancellation/session recovery or business/GPU quality. The public e5 candidate's own 8/8 CI and isolated S2 r4's two happy-path tests remain separate evidence. Ordinary publication, remaining bilingual guides and later runtime/selector acceptance remain with their original owners.
