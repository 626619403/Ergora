# Candidate environment-change record

Use this record for each proposed or actual library, backend, framework or environment change. It is an artifact template, not an executable operation or a new approval gate. Keep planned and observed facts distinct; append failures and corrections without replacing original records. Use sanitized artifact references outside the target project's private store.

|Field|Candidate-bound record|
|---|---|
|Task/stage and ownership|Original task/revision, permitted and fixed changes, execution/build owner, original attempt/clock/resource/budget references|
|Original reference|Immutable baseline ID, source/configuration revision, environment ID and reproducible snapshot/lock/image/build artifact references|
|Candidate and hypothesis|Candidate ID, selected library/backend/framework and component seam, bottleneck evidence, expected tradeoffs and bounded stop conditions|
|Environment identities|Original and candidate hardware/topology, OS/container image digest, Python, framework, driver/runtime/toolkit, compiler/communication stack and relevant package versions/builds; unknown or unchanged facts stated explicitly|
|Reproduction inputs|Exact dependency lock/resolution, package/wheel/source revision and checksums, build flags, backend/precision configuration and sanitized environment-variable names/references|
|Operations and availability|Planned commands and responsible owner; append actual commands, supported tool/operation, install/build exit status, logs/artifacts and resulting environment identity|
|Compatibility observations|Preflight/smoke/semantic/restore checks actually run, original failures and causes, unsupported operations, missing evidence and resulting limitations|
|Host/process-set observations|Actual node/cgroup and parent/rank/worker process identities, covered set and sampling window; RSS/PSS/shared-page semantics, host available/cgroup current-limit and anonymous/file-backed/cache/pinned observations kept separate; reader identity, unsupported/inaccessible counters and UNKNOWN gaps|
|Task-local paths and IPC|Original task/attempt/node/rank provenance and digest namespace, exclusive-create/collision result, resolved cache/temp bindings before runtime caching, complete encoded derived socket path including runtime suffixes and terminator semantics versus actual platform limit; original directory/process/listener cleanup owner and confirmed outcome|
|Optional stream contract|Actual replay/stream selection seam and None sentinel, valid empty/non-sized/infinite behavior, any contract-defined emptiness and finite step/stop bounds; observed selection results rather than implicit truthiness|
|Native harness regressions|Exact target harness/DataLoader constructor and source, Python/framework builds, multiprocessing start method, rank/worker/temp/tensor-sharing configuration; actual Tensor FD/resource-sharer/SocketListener transfer, batch checks and owned cleanup evidence, raw originals and matched-target/standalone/unsupported/unavailable scope distinguished|
|Primary failure and telemetry|Original exception/traceback/process status/exit/cancellation/STOP identity, bounded secondary diagnostic settings and errors, original cleanup result and unknown-reconciliation requirements; preserve the primary outcome|
|Comparison scope|Original baseline/environment, paired control/environment and candidate/environment IDs; changed source/dependency/environment/workload/legal-batch dimensions, fixed quality oracle and original reuse policy|
|Actual validation|Original raw artifact references, measurement windows, correctness/quality tier and paired end-to-end results; distinguish pending, failed, unknown and observed outcomes|
|Rollback and handoff|Restorable original snapshot and rollback commands, trigger/stop conditions, actual rollback result or not-run/unknown, complete predecessor/input/result identities and next owner|

The execution owner fills actual observations inside the existing task environment and artifact policy. A readonly proposal records the handoff and marks execution pending. Successful installation and a model review do not by themselves establish compatibility, gain, adoption or a new baseline.
