# AC3a：Ergora自身模板审查原始报告

日期：2026-11-09（运行UTC为2026-11-08）。通过实际Ergora reviewer入口调用Claude Code，固定源码清单及原始需求；过程未改受保护源码。结构化结论approve，无blocking finding，建议处置见[交付记录](2026-11-08-agent-definitions.md)。独立fresh-context审查另见[原共享报告](2026-11-08-agent-definitions-review.md)。

[原始结构化回执](evidence/2026-11-09-ac3a-self-review-result.json) · [输入/输出身份](evidence/2026-11-09-ac3a-self-review-identity.json)。下方保留模型报告和handoff原文，实际覆盖及未验范围以其正文为准。

# AC3a independent review: static AgentDefinition library

## Scope and method
- **Baseline:** deace5b51681338d66bbfbe31ddeff0e114e10dc.
- **Candidate:** the uncommitted snapshot in the protected manifest (sha 4ff26be1…).
- **Files read in full:**
  - src/ergora/agent_definitions.py
  - src/ergora/asset_trees.py
  - src/ergora/data/schemas/agent-definition-v1.json
  - tests/test_agent_definitions.py
  - both examples' agent.json
  - docs/AGENT_DEFINITIONS.md
  - src/ergora/backups.py
- **Changed regions read:**
  - cli.py dispatch and the CLI's error handling (catches ValueError, OSError and RuntimeError at cli.py:691)
  - contracts.py
  - skill_assets.py (metadata, get, import_bundle)
- **Callers and consumers traced:**
  - agents.validate_binding → agent_backends.for_binding → AgentBackend/CommandBackend.validate_binding
  - components.CHOICES and ROLE_CAPABILITIES
  - the component configuration schemas for codex, claude-code, mini-swe-agent and command (none has a credential field)
- **Validation logs read:**
  - r2-source-tests.log: 98 passed, 2 skipped.
  - r2-package-identities.json: 356 installed files, 283 frozen files, verify PASS, Python 3.11.15. The hashes for agent_definitions.py, asset_trees.py, backups.py, cli.py, contracts.py, skill_assets.py and the schema match the protected manifest.
- **Not done:** I ran nothing, so I make no claims about model, Windows (the junction test is skipped here), permissions or GPU behaviour. The final r2 package test run was still in progress and was not reviewed.

## Requirement trace
- **Versioned definitions; roles, specialties and backend kept separate; several definitions per backend.**
  - The schema has separate `roles`, `specialties` and `backend` fields.
  - Both examples use codex, with different digests and different filter results (test at line 36).
  - Met.
- **Content-addressed import of prompts, context and Skills.**
  - `inventory_tree` hashes every ordinary file.
  - Text resources are checked against both the declared sha256 and the inventory sha. Skill resources are checked with `digest_tree`, plus `skill_assets.metadata` and a check that the directory name matches the Skill name.
  - The object is stored at `objects/<tree digest>`, and the index maps the exact id and version to that digest. The index schema requires the digest to be 64 hex characters, so the object path cannot be used for traversal.
  - Met.
- **Rejections.** Each of these is rejected:
  - Unknown schema: `const: 1`, and a boolean is rejected because the type is integer.
  - Unknown role: explicit check plus `CHOICES`.
  - Unknown or incompatible backend: `CHOICES[role]` plus the component configuration with `additionalProperties: false`.
  - Unsupported top-level fields such as permissions/MCP: the schema has `additionalProperties: false`.
  - Missing or mismatched sha256 or digest.
  - Paths that leave the bundle or are not portable: `_relative`.
  - Symlinks, reparse points, `.git` and special files.
  - Bundles over the size, file-count, directory-count or depth limits.
  - Duplicate JSON keys and case-insensitive path collisions.
  - Met.
- **No execution on import.**
  - The import path only reads, hashes, copies and renames.
  - `validate_binding` only validates against the schema; `available`, `probe` and `command` are never called.
  - The test with a command backend and a skill script confirms there is no marker file and no `agent_runs` row.
  - Met.
- **Immutable exact id and version.**
  - Importing a different digest under an existing id and version is refused under the file lock.
  - Re-importing the same bundle is idempotent, and the index bytes do not change.
  - A registered object that has gone missing is refused rather than re-created.
  - A missing index on an existing store is treated as corruption (`_index` raises an OSError, which the CLI catches).
  - Met.
- **Backup and restore.**
  - `_check_assets` calls `verify_store(data)` on both the staged backup and the staged restore, which re-checks every index → object → resource chain.
  - The restore test shows `get(material=True)` returns the same result before and after.
  - Met.
- **Every field has a real consumer.**
  - `description`, `roles` and `specialties` are used by list/show and the filters.
  - `backend` is used by the existing binding validator.
  - `resources` are used by verification and `--material`.
  - Resource `id` is used only for the uniqueness check and error messages. That is acceptable for a static slice.
  - Met.
- **Legacy Skill identity.**
  - The `digest_tree` algorithm is unchanged: sorted file map, sha256 plus exec bits, and the same `json.dumps(sort_keys=True)`. The test at line 296 confirms this.
  - Behaviour changes only for inputs that were already broken: a symlinked root, a missing directory (now an OSError where it used to give an empty-tree digest), and special files.
  - Legacy Skills are not subject to the new directory-count and depth limits (test at line 350).
  - The 283 frozen files and the six stages are untouched.
  - Met.

## Architecture assessment
- **asset_trees** has no imports from the project's own modules and is the single place that computes tree identity. skill_assets, agent_definitions and backups all use it. Moving `is_link` there removes a duplicate in backups. The dependency direction is acyclic: backups → agent_definitions → agents/contracts/skill_assets/asset_trees/state.
- **No new database table, active head or per-definition Python class.** Configuration is checked by the existing owner (`agents.validate_binding`) rather than by code repeated per vendor.
- **Publication protocol is sound.**
  - The source is inspected, then copied to a private staging area inside state.root on the same filesystem, re-inspected, and the digests compared.
  - Publication runs under `.agent-definitions.lock`.
  - The first import publishes the object and the index together by renaming the whole library directory.
  - Later imports rename the object first and then atomically replace the index.
  - Readers take no lock but only ever see objects that were renamed into place whole.

## Findings (blocking)
None.

## Suggestions (non-blocking; listed separately)

### S1 (P3, architecture): stored-definition reads and backups re-run admission checks against the current catalog
- **Where:**
  - agent_definitions.py:116-121: `_get` calls `inspect_bundle`, which re-runs the role check and `agents.validate_binding` at lines 63-66.
  - agent_definitions.py:215: `verify_store`.
  - backups.py:79: the backup asset check that calls it.
- **Scenario:** a later release changes components.json, for example by narrowing a role's CHOICES, renaming a role, or tightening a backend configuration.
- **Consequence:**
  - Definitions that were already imported and are byte-identical become unreadable. `definitions()` fails as a whole, because a single bad entry aborts the loop.
  - `backups.create`, `verify` and `restore` all fail for the entire State home, even though the digests are intact.
  - Integrity and current admission become one check, owned by the backup layer.
- **Not reachable in this candidate:** the catalog is static and validation does not depend on the platform.
- **Smallest fix:**
  - Split `inspect_bundle` into a structural/digest verification step and an admission step (role, backend, frontmatter).
  - `_get` and `verify_store` would require only the structural step. `import_bundle` and future runtime admission (AC3b) would also run the admission step.
  - Alternatively, record this in the AC3b/AC3c plan so the catalog/version policy is decided before any catalog change ships.

### S2 (P3, docs/portability): sharing between POSIX and Windows fails when a bundle has executable bits
- **Where:**
  - asset_trees.py:40: exec bits are part of the identity.
  - docs/AGENT_DEFINITIONS.md:21: says an export "can be imported directly on another machine".
- **Scenario:** a Skill authored on Linux contains `run.sh` with the executable bit set. Copied to Windows, Python reports exec bits as 0 for that file. Conversely, `.bat`, `.cmd`, `.exe` and `.com` files report 0o111 on Windows.
- **Consequence:** import on the other OS fails with "Agent Skill digest mismatch". It fails visibly, not silently. The bit must stay in the Skill identity because legacy Skill identity has to be preserved.
- **Smallest fix:** state in the docs that executable bits are part of the identity, so such bundles are portable only between machines with the same exec-bit semantics. Optionally, report this in `check` output.

### S3 (P4, minor)
- **(a) Missing Skill directory gives an unclear error.**
  - Where: agent_definitions.py:75.
  - A missing Skill path surfaces as a raw FileNotFoundError from `lstat`. The CLI does catch it, so the failure is visible.
  - Fix: check `resource["path"] in directories` first and raise a ValueError such as "Agent resource missing".
- **(b) Two Skill resources can share a frontmatter name.**
  - Two Skill resources in different parent directories can have the same frontmatter name, for example `a/x` and `b/x`.
  - Not harmful now, but AC3b loading will need a rule. Consider rejecting duplicate Skill names at import time.
- **(c) The index is not fsynced.**
  - Where: `_publish_index`, agent_definitions.py:124-128.
  - After a power loss the index could be empty or truncated. It would then be detected as corruption rather than silently accepted.
  - Fix: fsync the temp file before the replace. This is optional and matches existing project practice.
- **(d) A shared definition can request `sandbox: current-container`.**
  - The codex binding inside a definition can carry this field. The docs say import is not a permission approval, which is correct.
  - AC3b should decide whether a definition may request a sandbox mode or only a project binding may.

## Preserved findings from other reviewers
The r1 review's three P2 findings are recorded as fixed by the author:
- legacy Skill directory compatibility
- initialization / missing index
- portable paths for empty directories

I checked the code for each:
- `digest_tree` applies no directory limits (test at line 350).
- The first import is atomic, and a missing index on an existing store raises (tests at lines 144 and 188).
- Empty directories are covered by the case-collision and reserved-name checks (test at line 333).

I agree with those conclusions. I do not replace them.

## Decision
**Approve.** No blocking defects. S1–S3 are optional follow-ups. S1 should be scheduled before any change to the component catalog.

## 原始handoff

Decision: approve, for the uncommitted AC3a snapshot (manifest sha 4ff26be1…, baseline deace5b).

Before marking AC3a complete:
1. Record the final r2 package test result. It was still running and has not been reviewed.
2. Recheck the source hashes against the protected manifest. The r2-package-identities.json entries already match for the core modules and the schema.
3. Record this review and its suggestions in docs/delivery/2026-11-08-agent-definitions-review.md and update docs/PLAN.md.

Optional follow-ups:
- S1 (separate digest integrity from admission against the current catalog in `_get`/`verify_store`): implement now, or log it as an AC3b/AC3c prerequisite before any change to components.json.
- S2: document that sharing between POSIX and Windows fails for bundles with executable bits.
- S3:
  - turn a missing Skill directory into a clear ValueError
  - decide how to handle duplicate Skill frontmatter names
  - fsync the index (optional)
  - set the AC3b policy on `sandbox` fields inside definitions

Limits of this review: static source review only. I did not execute anything. I did not verify Windows behaviour (the junction test is skipped), real model or backend runs, or permission enforcement. The producer used Codex and this reviewer is a Claude Code binding; different harnesses do not prove the two are independent in their model errors.
