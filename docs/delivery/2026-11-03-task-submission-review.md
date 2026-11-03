# F3.3b 显式提交与恢复：独立审查

日期：2026-11-03。审查者：独立 reviewer `f3_task_submission_review`，fresh context。按 `maintainable-project-delivery`、其 independent-review reference 和 `review-pr` 执行；从原始切片要求、实际源码和原 Transport 行为判断，不以作者报告或测试通过推导正确。

范围为 `refactor/architecture-foundations` 上 HEAD `4148842be2227cd64f04a44ae233140af6354fb6` 的工作区差异，包含 untracked 文件。此次仅检查源码、证据及定向探针，写本报告；未改生产或测试、安装依赖、提交、推送或执行完整测试。运行仍在已授权 Docker 边界内，无宿主操作。

## 结论

- **需求符合性：阻塞。** 存在两项已复现 finding：派发竞争会将外部 run 保存为本次提交，原始 history 的 JSON 数值/布尔身份未严格核对。修正并复审之前不能把 F3.3b 标为完成。
- **维护性：所有权与复用总体合理，未发现独立的结构性阻塞。** CLI/API 共用 `tasks`；`reference_task_submission` 在独立进程拥有 journal 和恢复语义，复用 `_Creation.published`、原 doctor/可信检查/IngressLeases/Transport。创建临时目录改为仅编译消费者传入，使只读消费者不持有无用临时资源，理由具体。修正应维持窄边界，避免复制完整准入或新造任务状态引擎。
- **性能验收仍未完成。** 当前只可说明调用次数和上限，不能宣称端到端性能已验收；完整包/完整回归/精确两 OS CI 仍待作者独立收口。

## 已确认 findings

### [High / P1] 预查与 start 之间的竞争仍可采用外部 run

位置：[reference_task_submission.py:104](../../src/ergora/reference_task_submission.py#L104)、[reference_task_submission.py:115](../../src/ergora/reference_task_submission.py#L115)、[reference_task_submission.py:126](../../src/ergora/reference_task_submission.py#L126)。

`CheckpointedTransport.start` 的首次 `lookup` 返回 NOT_FOUND 后保存 attempt 并调用原 `DevelopmentTransport.start`。原实现捕获 `WorkflowAlreadyStartedError`，再查询同 spec 的 run 并返回其 ID（冻结 `dev_platform/runtime.py:70–72`）。另一入口只需在首次查询与 start RPC 之间启动相同任务，新的 hook 就会把其他入口的 run 保存为本次 `submitted`。统一入口的任务锁不能约束原 agentflow CLI；原 claim 对相同 owner/task/spec 的重入也是允许的，因此这是可达的入口竞争。

定向探针使用实际原 task_action、IngressLeases 和 Transport，仅在受控 SDK `start_workflow` 中模拟竞争胜者：首次 describe 返回 NOT_FOUND，在 SDK start 点保存同 spec 的 `race-foreign-run` 并抛 `WorkflowAlreadyStartedError`。实际输出为：

```text
RACE_RESULT {"status": "submitted", "run_id": "race-foreign-run", "calls": ["doctor", "connect", "describe", "start", "describe", "history"]}
```

这违反了“仅本次显式提交的原运行回执，不能采用无本次归属的既有 run”。建议在专用进程的 SDK 派发窄边界区分实际创建与 AlreadyStarted，将已知外部冲突持久化拒绝，防止原兼容 fallback 被当作本次创建成功。需要覆盖竞争发生在预查之后，以及随后历史消失时仍不得重新 start。不得修改冻结 Transport 来修复此项。置信度：99。

### [Medium / P2] 恢复接受 Python 相等但 JSON 身份不同的原始输入

位置：[reference_task_submission.py:135](../../src/ergora/reference_task_submission.py#L135)、[reference_task_submission.py:139](../../src/ergora/reference_task_submission.py#L139)。

恢复直接相信原 `Transport.lookup` 的输入核对；冻结实现仅做 `values != [spec]`（`dev_platform/runtime.py:55–57`），没有验证解码出的原 spec，也没有比较 canonical SHA。Python 将整数 `1` 与布尔值 `True` 视为相等。新 journal 已通过 canonical SHA 区分这些值，但回执的原生输入来源仍未获得同样保证。

探针先在 attempt 保存后中断，使本地为 unknown 且没有实际 start；再提供 history，其原 `profile.schema_version` 从 `1` 改为 `true`，其余字段和原 hash 保留。该 history 的 JSON 身份不同，且不是有效的原 spec，恢复仍写出了结果：

```text
NUMERIC_RESULT {"status": "submitted", "run_id": "foreign-run", "python_equal": true, "original_schema_type": "bool", "calls": ["doctor", "connect", "describe", "connect", "describe", "history"]}
```

建议在新边界严格核对原生解码输入与冻结 spec 的 canonical 身份（并保留原校验/原始 history 要求），不把原 Python equality 当作精确身份。覆盖原始 history 的整数/浮点/布尔替换；不匹配时保持原 unknown，不补 submitted 回执。派发 hook 接收的 spec 也宜在同一边界核对原意图摘要，防止预检后再次读盘的输入漂移。置信度：99。

## 实际检查与成立的边界

已阅读 AGENTS、PLAN、总计划 F3、活动记录，完整 `git diff 4148842`（含新文件），并追踪原 `task_action`、`DevelopmentTransport.start/lookup`、`IngressLeases`、doctor/environment、file_lock、SQLite 事务与 reference 子进程入口。

此次检查的生产变化为 `reference_task_creation.py`、新增 `reference_task_submission.py`、`reference.py`、`tasks.py`、`cli.py`、`web.py`；测试变化为新增 `test_task_submission.py`、新增 `fixtures/task_submission_client.py` 和 `test_architecture_boundaries.py`；文档变化为 README、USAGE、PROJECTS、AGENT_BACKENDS、current/reference-boundary、PLAN 与活动交付记录。没有其他未跟踪实现被排除。

已成立的静态/定向证据：

- 写操作在保留项目当前 revision 的事务中进入专用完整 Linux runtime；注册安装源码身份在父边界核对。控制面不直接导入 SDK。Windows/缺完整运行环境明确拒绝。
- 创建所有者校验登记、原创建意图、七合同及完成回执；提交冻结原创建 SHA/spec SHA/角色，未重新编译或隐式采用 legacy。意图先于 doctor/claim，attempt 先于原 start。现有 attempt 的 resume 只 lookup；NOT_FOUND 不重发；已有回执仅返回原 run。
- journal 的 intent/attempt/result/rejection 使用 canonical SHA；重复 start 不自动重试准备态；准备态只有显式 resume 可继续。没有把失败/未知/取消未确认映射为六阶段成功；`execution_success` 保持 null。
- 提交锁复用创建的同 ID 锁，所有新原生写在子进程完成。asyncio 超时之外，父进程有额外 5 秒并回收客户端。原 doctor/start 调用链没有生成 Agent 进程，所以当前不需把持久 worker/executor 当作客户端子进程终止。
- **真实只读路径探针通过。** 未使用 SDK fixture 替换 status 逻辑；在专用客户端加 Python audit hook，禁止 `socket.connect`、文件写入以及 mkdir/link/rename/remove/rmdir。`tasks.submission` 返回 `not_recorded`，执行状态树文件字节前后相同，未触发被禁止操作。此证据针对提交记录读取，不是网络状态查询。
- `git diff 4148842 --check` 通过；冻结目录无 diff。显式 `PYTHONPATH=src` 调用 `reference.verify()` 返回 PASS，283 文件与固定来源身份一致。

上述两个失败探针使用 `.venv-dev` 中的非 editable 包及当前测试夹具；核对 `reference_task_submission.py`、`reference_task_creation.py`、`reference.py`、`tasks.py` 的 SHA 后，确认这四个运行文件与当前工作区逐字节一致。该轮源码身份如下：

|文件|SHA256|
|---|---|
|reference_task_submission.py|bf359f6a98b5757059c2ee32ed884a0a2ab6d022999b615ce01ff10ec654ee4d|
|reference_task_creation.py|603c875efed5948aaefa66b19743447a89e24285c83834eccbffe06650592f7b|
|reference.py|52825fbb8b4ef0cf9e40a46f8eb83a553d2f121f6ca4c31b645eafec14ef9a3a|
|tasks.py|c3c21c1855fb872ea906a48de44cbfbdc2cda0c7d920edadd432b85064c8ab0a|

## 维护性与性能补核

新增文件的实际生产入口是 `reference.task_submission`，负责隔离原全局与完整依赖；这是生命周期所有权的理由，不是虚构多个调用者。`_Creation.published` 的复用使原七文件/大意图验证保持单一所有者；其余新增私有函数是同一 journal 的格式与校验算法，没有建立公共框架。窄 hook 在 finally 恢复原类且仅作用于专用进程，不污染 Web 的并发请求。

新路径每次启动完整环境子进程并校验创建快照；初次派发额外一次 ownership lookup，恢复查询只取原始输入。文件读取受原 1 MiB 单合同/16 MiB 创建意图边界约束。SQLite `BEGIN IMMEDIATE` 覆盖客户端操作，能保留当前 revision，也会在网络等待期间串行化同一控制目录的所有写者；连接现有 busy timeout 为 15 秒，提交客户端可达 60+5 秒。它目前不是本次新增的独立 correctness finding，但最终性能/并发验收应明确长连接下其他项目写操作的体验，不能从快速 SDK fixture 推导无影响。

## 已有验证与尚缺证据

已读取原始日志，未把作者测试当作独立审查：

- `.ergora/checks/f3-task-submission/source-first.log`：68 passed，140.19 秒，覆盖 submission/creation/architecture；此后已有修改，不能当作最终源码完整验证。
- `.ergora/checks/f3-task-submission/source-targeted.log`：44 passed，136.65 秒，覆盖当前 submission/architecture。两项 review finding 均未被这组用例覆盖。
- build.log 与首版 wheel 已存在；本审查未据此声称发行/身份/性能/完整回归已通过。

尚需：修正两项 finding、对应负例及独立复审；最终非 editable 包与基础/完整运行环境组合身份；本切片性能测量；适用完整回归；精确候选两 OS CI 和最终交接核对。真实服务/模型、两个模板六阶段、批准/取消和分支导出不是这组受控 SDK 探针的结论，继续留在约定的 F3.3c/F3.4 边界。


## 修正复审（2026-11-03，更新前述初审结论）

同一 reviewer 受托仅复核修正、相关新增源码/测试及原失败探针，仍仅写本报告，没有改生产/测试或重跑完整回归。基线 HEAD 仍为 `4148842be2227cd64f04a44ae233140af6354fb6`，未提交工作区包含此次修正；所有独立运行显式设置 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`，确认入口来自 `src/ergora/reference.py`，没有将初版 e285… 安装包当作修正代码。

**本次结论：P1、P2 均已关闭；源码和受控协议范围需求符合性通过，维护性通过，无新增 finding。** 初审失败证据保留，其“阻塞”结论由本节取代。最终发行、性能、完整回归、精确两 OS CI 和提交/远端身份尚待单独核对，此结论没有把整项 F3.3b 标为完成。

### 修正与归属证明

- P1 修正：[reference_task_submission.py:130](../../src/ergora/reference_task_submission.py#L130) 的专用 SDK start 窄代理给原调用添加 `ergora.submission_sha256` memo，保留原 spec/workflow ID、队列、一次尝试与重复策略；捕获 AlreadyStarted 后写 `start_conflict`，以 ValueError 退出，原 Transport 的兼容采用分支不会吞掉该冲突。已有 attempt 的拒绝现在也有明确格式与校验。即使冲突拒绝记录写失败，unknown 恢复仍须核对原 describe 响应的本次 memo，外部 run 没有标记就不能成为 submitted；历史消失仍不 start。
- P2 修正：[reference_task_runtime.py:10](../../src/ergora/reference_task_runtime.py#L10) 的 `VerifiedSpecClient` 只包装原 Transport 显式调用的原始输入 decoder，以 canonical SHA 核对完整 `[spec]`。原 get_workflow_handle/start 调用委托给实际 SDK client，返回的 description/handle 保持原 SDK converter；memo/query/result 不被误当作 spec。原生只读 status 和 submission 是两个实际生产消费者，没有重复历史读取或复制 lookup 算法。
- [reference_task_submission.py:105](../../src/ergora/reference_task_submission.py#L105) 在原 task_action 的 task_spec 输入点检查原意图 spec SHA，早于 doctor/claim；其局部 hook 与 Transport hook 均 finally 恢复，仍只作用于专用进程。
- 两个新增边界核对各拥有不同的不变量：原生 history 的精确输入身份、未知恢复的本次提交归属；memo 不是用户认证或额外执行权限。此次没有修改 283 个冻结文件。

### 独立检查结果

独立运行以下源码定向集合：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider \
  tests/test_task_submission.py::test_competing_start_after_preflight_is_never_adopted \
  tests/test_task_submission.py::test_unknown_recovery_requires_strict_json_and_own_memo \
  tests/test_task_submission.py::test_unknown_recovery_refuses_a_different_submission_memo \
  tests/test_task_submission.py::test_native_spec_read_drift_is_rejected_before_doctor_and_claim \
  tests/test_task_runtime.py::test_runtime_errors_do_not_fall_back_to_compiled_or_retry
```

结果：**12 passed，44.28 秒**。覆盖竞争及拒绝记录写丢失、原 history 的布尔/浮点替换、memo 缺失/异值、原生再次读取的输入漂移，以及已有 runtime 错误路径。除该定向集合外，未再次扩大执行完整测试。

另重放初审的独立失败探针，仍调用原 task_action、IngressLeases 和 Transport，仅替换 SDK 端口/定点中断；没有依赖作者给出的期望结论：

```text
RACE_FIXED_RESULT {"status": "rejected", "reason": "start_conflict", "run_id": null, "after_history_disappears": "rejected", "calls": ["doctor", "connect", "describe", "start"]}
NUMERIC_FIXED_RESULT {"history_scalar": true, "status": "unknown", "run_id": null, "start_calls": 0}
NUMERIC_FIXED_RESULT {"history_scalar": 1.0, "status": "unknown", "run_id": null, "start_calls": 0}
READONLY_FIXED_RESULT {"status": "unknown", "state_bytes_unchanged": true}
```

数值探针给 history 同时提供了匹配本次意图的 memo，因此是由严格原始输入校验拒绝，不是由 memo 缺失掩盖问题。只读探针仍用真实 submission 程序体，加 audit hook 禁止网络 connect、文件写入和目录/链接/重命名/删除操作；执行状态树字节保持不变。

独立查看固定 SDK **temporalio 1.34.0** 的 `Client.start_workflow` memo 参数及 `WorkflowExecutionDescription.memo/_from_raw_description/_from_raw_info` 源码。额外使用真实 SDK protobuf response、DataConverter 和 WorkflowExecutionDescription 在内存中编码/解码 memo：description 保持实际原 converter，memo 正确解码，spec decoder 会拒绝把 memo payload 当作 spec；没有网络请求。该探针初次缺少原生模块导入路径，补齐源码原生路径后通过，不是产品故障。冻结原 workflow 源码不存在 `upsert_memo`；该固定身份下 memo 的读取只解码已有 describe 响应，没有追加 RPC。

`git diff 4148842 --check` 通过；冻结目录 diff 为空，源码 `reference.verify()` 仍为 PASS / 283 文件。此次修正的精确身份为：

|文件|SHA256|
|---|---|
|src/ergora/reference_task_submission.py|a4a0c8bfae08b5b1f0804996ec09ff7f8247f97427346c88e146bdfd623da35b|
|src/ergora/reference_task_runtime.py|eca0431b30b1e3165ef2a4ee860c6e76a6c53da5174972921f62effc03fecb3b|
|tests/test_task_submission.py|8febd7722a4cb08ae0f0cfd04d81ed295ad265bbc1b22929977621b964f8f547|
|tests/fixtures/task_submission_client.py|62268d99499601cd2572580c78e7d560bf142b0a51792975d4f8cae3c4a592de|
|tests/test_task_runtime.py|c2bc830c83b9e12fca98ee2ed769f347d9008e93f8139f2ed533b78e704f2456|
|tests/fixtures/task_runtime_client.py|0bda335389d944b6d27f4db5c6b478f9e9911c8fec5d0067bf1d1d71d8edd4df|

### 验证范围与剩余验收

已读取 `.ergora/checks/f3-task-submission/review-fixed-targeted.log`：作者修正源码的 submission/runtime/architecture **71 passed，192.48 秒**，仅已有 Starlette 客户端弃用警告。该日志与独立 12 项定向分开记账。

修正新增两次有界 canonical 序列化和小型 memo；保留原 history 单次读取，memo 不增加 RPC。独立检查说明成本来源和上限，不替代最终包的真实延迟测量。SQLite 长事务与 15 秒 busy 预算的权衡已写入公开用法，本次没有据快速 fixture 宣称其跨项目并发体验无影响。

修正前 e285… 的 432 项完整回归及 72 次基础旅程仅保留历史身份；本复审不将它们应用于上述新源码。修正后的最终 wheel/两安装完整身份、性能与并发测量、适用完整回归、精确候选两 OS CI、最终提交和远端身份仍待归档审计。真实服务 memo/history/原 run 的端到端行为及模型/六阶段仍按既定 F3.4 范围验收，不从受控 SDK 或本地 SDK 解码探针扩大结论。


## 最终本地归档核对（2026-11-03）

同切片追加只读归档审计。核对时 HEAD 仍为 `4148842be2227cd64f04a44ae233140af6354fb6`，23 个文件已暂存但尚未提交；本轮唯一写入为本报告，未安装、改源码/测试、重跑完整回归、提交或推送。后续 F3.3c 的新设计记录及 runtime 文档链接只作为下一切片计划，不是本段的新生产能力。

**最终本地核对通过，无新增 finding。** 已关闭的 P1/P2 保持关闭；源码、最终 wheel、两套非 editable 安装及本地归档证据的身份一致。精确两 OS CI、最终提交和远端 SHA 仍待下一次核对。

独立读取 `review-fixed-verify-package.py` 后，另在内存运行只读校验，没有执行会重写归档的作者脚本。重新计算全部包文件，确认 **343 文件在源码、wheel、开发安装和无 SDK 基础安装之间逐字节一致**；归档 `review-fixed-package-identity.json` 的全部摘要也一致。最终 wheel 为：

```text
review-fixed-dist/ergora-0.2.0-py3-none-any.whl
SHA256 f8d92f51317a3b3d6f7466ab1bc38b97a4bd4de6658ab06358580bf1d735c44e
```

前两轮记录的 9 个相关源码/测试身份重新计算后未变，且暂存内容一致。本次变更的 12 个源码/测试文件（7 个生产文件、5 个测试/fixture 文件）均与暂存内容一致；以相对路径为键、文件 SHA256 为值，按 `sort_keys=True,separators=(',', ':')` 序列化后的聚合 SHA256 为 `0735c39c30a387d68b13110f507823731f11fc696a90c233a4d18498b4fbcdc1`。冻结目录无差异，基础安装的 `reference.verify()` 仍为 PASS / 283 文件。`git diff 4148842 --check` 通过。

已读取完整 `review-fixed-wheel-regression.log`，末尾为 **441 passed、19 skipped、36 subtests passed，397.38 秒**，仅已有 Starlette 测试客户端弃用警告。该最终包回归独立于先前 432 项初版回归；本次仅审计归档，没有重新执行全量。

### 72 次基础 CLI 旅程与测量范围

已读取 `review-fixed-journey-performance.py/json/log`；JSON 与日志中的完整结果一致。另从 72 条原始命令记录重新分组和计算各组中位数/最大值，确认每模板 36 条命令，其中 30 条为每操作各 10 次顺序重复。独立查看两份原生调用事件，均为 `doctor → connect → describe → start`，各仅 1 次 start/doctor，没有阶段 requests/receipts。脚本在重复操作前后对整个执行状态树按文件 SHA 核对，断言通过；重复命令返回原回执，任务与操作字节保持。

|模板|submission 中位 ms|重复 start 中位 ms|重复 resume-start 中位 ms|
|---|---:|---:|---:|
|repository-governance|1068.34|1000.21|1024.68|
|large-change|1068.74|1066.56|1079.09|

基础控制面为 Python 3.12.3 的独立非 editable 安装。另实际执行只读导入检查，确认 FastAPI、Temporal、GEPA 均缺失；提交子进程由登记运行时的 `.venv` 指向开发解释器，控制面不导入 SDK。未初始化完整原生解释器时，两模板均明确拒绝；配置解释器后首次 start 使用受控 SDK fixture，之后 60 次重复操作走真实本地生产入口、读取既有回执，没有 RPC。

上述中位数包含 CLI、本地预检、子进程及 SDK 启动成本，测量期间另有完整回归并行运行；不是纯存储/RPC 延迟、吞吐或优化收益。首次受控派发约 1.34 / 1.31 秒只证明该 fixture 协议路径，不证明真实服务或模型性能。跨项目写锁超过 15 秒的争用体验未实测，公开记录中的该限制保持有效。

最终本地发行、适用回归及这组有限性能证据已核对。真实服务 memo/history/run 的端到端行为、真实模型、六阶段、批准/取消及分支导出仍没有由本次本地归档取得新验收，继续按 F3.3c/F3.4 分段负责；未从 CI 待办或受控 SDK 结果扩大范围。


## 最终精确 CI、远端身份与锁争用归档复核（2026-11-03）

同切片独立复核最终候选 **`97567b984522cb2cf1da192787f5501e25b838c5`** 和 [CI 41566783007](https://github.com/626619403/Ergora/actions/runs/41566783007)。本轮仅追加本报告、读取归档及查询远端，没有修改生产/测试、安装、重跑完整测试、提交或推送。

读取 `ci/fetch-ci.py`、`ci/verify-ci.py` 后，另写仅在内存运行的 HTML parser 复核原始页面，没有执行会更新归档的作者脚本。从 `ci-actions.html` 的原始 application/json 数据重新选择 `.github/workflows/portability.yml`、完整候选 SHA 和工作分支，所得 run 与保存的 selection 完全一致，状态为 completed/success；原始 run 页面显示 Success，commit 链接精确指向上述候选。

|实际 runner / Python|Job|已完成且 success 的必需步骤|
|---|---|---|
|windows-latest / 3.12|[125690118663](https://github.com/626619403/Ergora/actions/runs/41566783007/job/125690118663)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|
|ubuntu-latest / 3.11|[125690119230](https://github.com/626619403/Ergora/actions/runs/41566783007/job/125690119230)|Build and install wheel；Packaged reference identity；Native application regression|

两个 job 原始页面都具有对应 selectedJobId；每个必需步骤的完成标志及日志 URL 均绑定相同完整候选和对应 job ID，两个 Complete job 也已完成并为 success。没有 failure/cancelled/timed_out 步骤。重新计算 selection、run、两份 job 原始归档的字节数与 SHA256，全部匹配 `ci-html-status.json` 的四份来源身份。结论来自官方 HTML 原始归档，未从摘要 success 字段直接推导，也未要求在公共 API 限流后重复请求 API。

独立从 `git show` 读取候选的 12 个变更源码/测试文件并重新计算聚合身份，仍为 `0735c39c30a387d68b13110f507823731f11fc696a90c233a4d18498b4fbcdc1`；当前相对该候选的 src、tests、pyproject 和 workflow 差异为空。最终 wheel 重新计算仍为 `f8d92f51317a3b3d6f7466ab1bc38b97a4bd4de6658ab06358580bf1d735c44e`。本地此前核对的 343 文件、441 项回归与 72 次基础旅程因此仍适用于此生产/测试候选。

独立执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，返回 **`97567b984522cb2cf1da192787f5501e25b838c5`**。精确 CI 候选、已审代码/测试、发行包及核对时远端身份一致；此时后续未提交变化仅为文档和下一切片设计，不构成已验收的新运行能力。

### 全库写锁的已知性能限制与后续责任

已读取 `lock-contention.py/json/log`，确认脚本使用最终包、实际 State/项目写者和同一个控制库，在原 SDK connect 入口注入 18 秒 await 延迟，无真实 RPC 或模型。JSON 与日志结果完全一致：提交 timeout 为 25 秒，另一项目写者在 **15035.54 ms** 后收到 `OperationalError: database is locked`，失败时 revision 保持 1；提交最终 submitted，随后显式同修订重试更新到 2，总耗时 **19600.94 ms**。另以 SQLite `mode=ro` 读取保留的验收库，确认重试后的实际 revision 为 2。本轮没有重跑会写验收目录的探针，也没有把归档中的失败前 revision 当作新的独立运行观测。

这是当前全库写保留对其他项目的可达性能/交互限制，**尚未优化**，不是 72 次快速本地路径已消除争用的证明。数据和修订一致性保持，也没有自动重发未知提交；但不能宣称跨项目写入可及时完成。先前“争用未实测”的保留项现由上述量化证据更新，不能将它继续描述为未知影响。

核对 PLAN、总计划 F3 与活动交付记录：**F3.3d 已列为 F3.4 前的 P0 跟进**，在保存不可变操作意图前保留当前 revision，随后远程等待只持原任务锁；需要另切片验收跨项目写入、同任务并发/不重复、准备与派发中断及修订漂移，不能直接提前释放锁而失去授权快照。责任与验收边界已明确记录，本复核没有将这项未完成工作标为解决。

**F3.3b 的提交/恢复正确性、发行身份及精确两平台 CI 最终独立核对通过；P1/P2 均关闭。** 全库锁限制按 F3.3d 继续负责；真实服务 memo/history/run、模型、六阶段、批准/取消及导出仍须 F3.3c/F3.4 的实际证据。完整 F3 尚未完成，本轮未扩大这些验收范围。
