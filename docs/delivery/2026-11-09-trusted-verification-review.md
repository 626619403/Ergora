# CR3a 可信验证迁入独立审查

日期：2026-11-09。审查者：`trusted_verification_review`，fresh-context；原始依据为 [CR3a 验收](2026-11-09-trusted-verification.md)、[CR3 总体要求](2026-11-09-composition-executor.md)、`AGENTS.md` 及 maintainable-project-delivery / codebase-design。基线为 `8151a1c674fd6c664b4ce6aeba11a5fdf12be426`；初审覆盖未提交的本片实现及同片修正，固定候选交付终核见文末。不包含前片 CR2b 的 CI 终核。

## 对象与两轴结论

本次检查的最终源码身份如下；R3 wheel 为 `5a66f3898ccfae55cd76d8563d7975373f16c4eef9a46c1b8b3b11fcf1573bff`。

| 文件 | SHA-256 |
| --- | --- |
| `src/ergora/reference_executor.py` | `f005a9c425e1a1efc2f804e5ee1a822b4fa76dce5cea4444a187e67bbe057475` |
| `tests/test_reference_executor.py` | `7b0d195a89ef00089cb286086872d867ebad7720eea3e4e8c3555c75f0107380` |
| `tests/fixtures/reference_acceptance.py` | `3ae0b851cfdb0b878153f71b453680d6b6f42adc3452385bc9d463b77983d081` |

**Standards：本地审查通过。** 新增 `_verify` 是现有 executor 的私有阶段算法，实际消费者只有同类的 `execute`，没有为单一调用者另建通用模块。冻结执行器没有 verify 路径 hook；局部重写该阶段入口及其必要的错误/取消包装有具体原因，其余五阶段直接 `super().execute()`。可信命令、checkout 准备、候选、artifact 和 receipt 仍使用原所有者，没有复制六阶段 scheduler 或 scope 算法。

完整 scope 重算调用冻结 harness，再由现有不可变 `write` 比较整个报告，避免平行维护一套身份字段合同。私有临时目录对应 harness 的“输出必须不存在”约束；最终 scope 发布到持久 scratch。新控制流都有实际输入或恢复场景：发布投影不匹配、已保存 scope 内容不匹配、命令集合变化、实际命令失败、harness 失败/超时/缺输出及 fence 取消。临时路径规范化的 handler 用于稳定不可变失败证据，具有独立作用。

新增六种验收模式分别保护 wrapper、无身份/错候选 scope、只有匹配身份头的伪报告、基线集合、真实命令失败和错误产物发布后的恢复。后者要求原 artifact/receipt 接口给出相同结果；没有添加实现形状断言或重复的 CI 工作流。旧两模板和两后端的现有矩阵继续复用，新模式只选一个模板/command，未扩成无必要的乘积矩阵。

**Spec：本地实现审查通过，TV-SP1 已修正复核。** 发布的 v1/v2 文档只读；私有 legacy projection 与 stage spec 先核一致，再传给原 scope harness。完整 report 的不可变比较包含 task/request/profile/spec/policy/base/candidate 及实际文件结果。无身份、错候选或缺结果字段的保存文件不能成为本次 pass。原 `commands('verify')`、基线集合比较、失败 `check-results`、必需 checks 和 `local-ci` receipt 保留。本地最终发行与实际自身审查已在下方补核；精确提交/CI/远端交付仍须单独终结。

## 实证 finding 与同片复核

**TV-SP1，P2，已关闭：正常 scope 失败的随机临时路径破坏恢复。** 位置为 `reference_executor.py` 原完整重算版的失败 detail 组装，以及冻结 `Executor.artifact` 的不可变比较。原 harness 正常 FAIL 时 stdout 带临时 `--out` 路径；相同 job 若已发布 `executor-error`、尚未发布 receipt，重跑会把另一个临时路径写入同名 error artifact，从而在错误 handler 内再次抛出 `Artifact publication conflicts with earlier evidence`，无法形成正常失败 receipt。

审查者先用真实只读 harness 的 `protected-path` FAIL 报告做内存拦截探针：两次 scope 内容相同，异常 detail 及按原 artifact 格式序列化的字节不同。作者随后以 R2 非 editable 包运行真实新回归，`1 failed in 4.68s`；日志直接显示第二次 `Executor.execute()` 在原不可变 artifact 比较处冲突。该证据保存在 `.ergora/checks/ac3c3-verification/r2/recovery-red.log`，不与修后结果混记。

修正后，正常 harness 失败 detail 只指向持久 `scope.json`，完整 FAIL scope 在报错前保存；launch/read/timeout 异常中的临时前缀被规范化后继续传播。审查者对修后源码独立检查五种隔离控制流：正常 scope FAIL、TimeoutExpired、缺输出、启动文件缺失、带 fence 的 timeout；各执行两次，receipt 和 error artifact 字节均相同，均无 pass checks，最后一种为 `CANCELLED`。这些探针拦截磁盘写和 subprocess，不冒充真实 OS 超时或进程取消。

真实新增 fixture 先执行两次同 envelope，模拟 error artifact 已写而 receipt 尚未发布，再经正式 `process` 发布并由 activity poll 核 receipt。修后源码六边界加原架构检查为 `15 passed in 28.29s`，已检查实际日志。当前检查范围内没有未解决的 correctness 或 maintainability finding。

## 已核证据及实际限制

- 静态核查：基线 diff、原冻结 executor/core/harness、任务 envelope、公开提交/status 拒绝及实际调用者；`git diff --check` 通过。独立 `reference.verify()` 为 PASS / 283，冻结目录相对基线无 diff。
- 独立发行身份核查：对 R3 的 368 个文件逐一比较当前源码、wheel ZIP 和现存安装字节；全部一致。wheel digest 与记录一致，安装的 `direct_url.json` 未标 editable；另逐一核冻结 manifest 的 283 文件摘要。
- 已读取 R1 旧包日志：wrapper 覆盖冲突和假 PASS scope 对照为 `2 failed / 2 passed, 17.23s`；wrapper 原始失败 receipt 确认是不可变发布冲突。只有匹配身份头的额外反例在旧包为 `1 failed, 4.95s`。重算版修前源码 14 项 / R2 包 33 项的通过属于各自历史身份，不移记为 TV-SP1 修后验收。
- 已独立抽查保留的源码 fixture receipt：wrapper 成功，五个必需 checks 和真实命令 exit 0；两种 scope 拒绝及基线变化均 FAILED / 零 checks；真实命令失败保留 `check-results` 和 `executor-error`，最终命令 exit 1、baseline exit 0。另以只读隔离探针确认发布 projection 不同会在私有写入及 harness 启动前被拒绝。
- 性能只读抽样：既有合成仓库、一个改动文件，调用原 `git_scope.verify` 三次，完整输出与保存 PASS 报告相同；耗时 0.056479 / 0.054790 / 0.053543 秒。该值不含新 Python 子进程启动、真实命令或大仓库成本，也不证明最大 v2 manifest 的解码开销。每次恢复新增一次完整 scope 重算是确保保存报告真实对应当前输入的明确成本。

旧四组合六阶段 `4 passed / 24.42s` 是作者首轮报告；源码修后 15 项及下述 R3 最终包回归均已核日志。本审查未安装依赖、未编辑源码、未运行昂贵旅程，所有动态探针仅作只读或内存拦截；仅写本报告。

## R3 本地最终材料补核

已独立读取 `.ergora/checks/ac3c3-verification/r3/wheel-regression.log`：最终包 executor/架构定向 `34 passed in 113.18s`，没有跳过；当前三文件仍与本报告的最终身份表一致，未将 R2 结果移记为 R3。

实际自身模板审查的公开原件为 [身份记录](evidence/2026-11-09-cr3a-self-review-identity.json) 和 [原生结果](evidence/2026-11-09-cr3a-self-review-result.json)。run 为 `63f5eb19d9294a6bad6af0cae0e2f603`，经现有非 editable R3 包的 `structure-review` / task MCP 调用配置的 Codex `gpt-6.1-sol` / high，105.42 秒，进程 exit 0、保存状态 succeeded、结果 approve。该结果补充本次独立审查。

补核直接读取原始 input、manifest、scope、模型 stdout、protocol result 和只读 SQLite，而非只接受汇总 JSON：

- 从当前完整 executor、原 executor/harness 及相对 `8151a1c` 的测试 hunks 重建附件；与源 Agent、静态 manifest、准备 input、运行 input 四份文件逐字节相同，共 68,920 字节，SHA-256 `7d8a1154d5aedd51898536b3d6b5b6d2727949f90f8be0276ff95d83c8b46280`。
- 通过已安装包的只读 `inspect_manifest` / `inspect_input` 重核完整树；manifest 为 `2084e472a70c957f206782d61b2ab72459409b55dd2bd4913410f0b6047669b0`，准备与运行 input 同为 `b0d0da73f2dba5b4cdac4534ffbf45fbef9c15a3219db9a1049780e5931002f5`。原 definition libraries 确已移除，所供静态快照仍可完整核验。
- SQLite 唯一 run 与原 `codex.stdout` 完整记录相同，预检与运行 binding/policy 相同。protocol prompt 与实际 stdin 字节相同，SHA-256 `c6ccd4ade13d1682dcc9db98bb2635a3eb6326b6e2d53f0de01b9c781f5ab2b2`；实际原生命令包含忽略用户配置、限制 shell、仅启用 task MCP list/read 的选项。
- 原生 MCP 收据的九条事件均绑定同一 scope 摘要，initialize 和 tools/list 成功；模型 stdout 的完整附件读取范围连续为 `[0,32000)`、`[32000,54000)`、`[54000,68920)`，最后 `next_offset=null`，逐段字节与附件相同；另有一次前 18,000 字节重读。故完整读取由原件支持，不仅是模型自述。
- 公开结果与原 `protocol/result.json` 逐字节相同，原始 SHA-256 `b5c4bfee30ed478db7f314a295e6e30b2c68ef793388ed352b34526a47eedfb7`。运行记录的 `result_sha256=3c1e7c4a5a5b88ee549ae6b276ef376ef488fbc3f93b4e513a741f89ce4c7bb6` 对应另存的校验后 result 文件；两种表示的 JSON 完全相同，`artifacts.response` 与公开审查文本相同。

自身结果两轴没有 blocking finding；它提出正常 scope FAIL 之外的 launch/缺输出/timeout 恢复覆盖建议。上述独立内存探针已验证这些失败分支的重复 error artifact/receipt 稳定性；真实 OS 启动失败/超时和 scope 子进程中取消仍未实测。该建议保留为覆盖限制，未发现需阻塞本片的额外缺陷。

自身审查明确只审供给的源码，没有执行测试，也没有据附件验证 read/write、unwrap、完整仓库或冻结/发行身份；这些能力的本次独立核查各有上文的来源。其 input 为 `operator-supplied`，input/admission 的正式执行授权均为 false；固定资源 list/read、只读后端请求不构成 OS 隔离或正式 v2 执行验收。

wrapper fixture 使用旧六阶段活动和合成协议 Agent，只证明 verify seam 能读取完整封装并保持原字节。公开 v2 入口仍拒绝；原构造副作用前的完整准入、实际组合成员/Agent/权限/动态资源、正式 v2 运行和 CR4 整栈均不属于本片已验范围。原有取消合同的沿用已核源码与隔离终态；本审查未实测在 scope 子进程执行中发生的 OS 取消。

本地最终 Standards/Spec 通过，TV-SP1 关闭，无新增未解决 finding。前片 8151a1c 的 CI 由另一审查者负责；本片自己的精确交付终核如下。

## 固定候选、双 OS CI 与远端终核

精确候选为 `d8668a43abf5adcbabdf12d0ee5b1f570114262b`，父提交为 `8151a1c674fd6c664b4ce6aeba11a5fdf12be426`。审查者从固定 Git 对象读取变更集合和 blob，核其恰为 `.ergora/checks/ac3c3-verification/r3/review-scope.json` 的 16 个文件，每个文件 SHA-256 均一致；固定候选的 `git diff --check` 通过。

固定 Git 树中 `src/ergora` 的完整文件集合、R3 wheel 内 `ergora/` 的完整集合与身份清单均恰为 368 文件；逐文件字节与现存 R3 非 editable 安装一致，wheel 仍为 `5a66f3898ccfae55cd76d8563d7975373f16c4eef9a46c1b8b3b11fcf1573bff`。另从该提交读取冻结 manifest 及 283 个对应 Git blob，摘要全通过，冻结目录相对父提交无变化。本节的运行身份绑定固定 Git 对象，后片工作区变化不参与这些比较。

本候选自身的 [Portability CI 42540516079](https://github.com/626619403/Ergora/actions/runs/42540516079) 为 push / attempt 1。2026-11-09 00:45:27.868343 UTC，独立公开 API 查询确认总 run 为 completed / success；两个作业的 `head_sha` 均精确等于本候选。

| 平台 / Python | 作业 | 适用必要步骤 | 完成时间 UTC |
| --- | --- | --- | --- |
| Ubuntu / 3.11 | [128914165433](https://github.com/626619403/Ergora/actions/runs/42540516079/job/128914165433) | 构建安装、包身份、应用回归：3 项 success | 2026-11-09 00:45:06 |
| Windows / 3.12 | [128914165589](https://github.com/626619403/Ergora/actions/runs/42540516079/job/128914165589) | 构建安装、包身份、应用回归、PowerShell 安装/升级：4 项 success | 2026-11-09 00:37:31 |

七项适用必要步骤均成功；Ubuntu 的 Windows PowerShell 条件步骤按 workflow 跳过。此处记录 CI 步骤结果，不据此声称所有平台条件测试均实际执行。

确认 CI 成功后于 00:45:28.678491 UTC 立即发起 SSH `git ls-remote`，默认代理返回 HTTP 407，直接连接的 22/443 端口亦超时。随后复用既有代理认证，以 SSH 443 通道及现存 GitHub host identity 核验重试；没有改 SSH 配置、写入凭据或安装工具。2026-11-09 00:48:29.338026–00:48:33.728775 UTC，SSH 只读命令 exit 0，返回：

```text
d8668a43abf5adcbabdf12d0ee5b1f570114262b  refs/heads/refactor/architecture-foundations
```

本片 V4 的独立精确终核完成，Standards / Spec 通过，TV-SP1 关闭，无未解决阻塞 finding。该结论只覆盖 CR3a；前述正式 v2、CR3b/CR4 和 OS 失败路径限制保持。本节为候选提交之后的同片审查记录追记。
