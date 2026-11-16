# M6-V2b：closed SDK 容量接缝实施

2026-11-16。源码候选已 freeze，已交根接续新安装／原模板／fresh 独审，作者未自批接纳。准确基线 `c540939d3b3f38f3851b0de965c9cd0f969eea77`；唯一产品树 `.ergora/worktrees/training-cycle-v2-capacity`，分支 `feat/training-cycle-v2-capacity`，进入时 HEAD 相同且干净。V2a 产品 `82c6595907b4d2173890b82e6fcb6ab8920832b1` 已接纳，本片不重复认证其许可／拓扑／shutdown。

按[已审实施清单](../plans/2026-11-16-training-cycle-capacity-implementation.md)和[设计审](2026-11-16-training-cycle-capacity-design-review.md)实现；计划冻结 SHA256 `25069beea90535070de5f0691831eee3bcf2fbd1b0a552de9a24194e121956c2`。已读根／src／tests AGENTS、PLAN、组件协议、maintainable-project-delivery 与 ergora-codebase-quality 的 module-design／test-seams／repository-style。

产品预期仅 `reference_training_worker.py`：完整树 FailureConverter、V2 公共配置派生 client、controller 原发送路径两次 Payloads／Memo 计量、v3 固定 wrapper 错误。验证扩展原 runtime／controller／submission 测试和确需的原 fixture。schema3 效果、训练及设计 gate 保持关闭；schema2 同 owner 的正向 dispatch 与真实 schema3 现场分别标注。默认 payload、无 codec／external storage 的本地 SDK 接缝结果不能认证真实 server 包装或完整 M1c-V。

## 验证与证据

本轮私有证据目录 `.ergora/checks/training-cycle-v2-capacity/impl-r1/`，不覆盖 `design-r1`。源码使用现成 SDK 解释器并明确 `PYTHONPATH` 指向隔离树 `src`，不安装或改依赖。先补原 SDK completion 小红例；每次保存原始 argv、stdout／JUnit、实际自有进程身份及终态。

小红例 `red-wrapper-r2` 已在原 SDK `_ActivityWorker._handle_start_activity_task` 的 `failed.failure` 出口失败：v3 request-rejected 输出了原异常消息，并由 SDK 编入原 cause；还没有固定封闭错误。首次 `red-wrapper` 是测试接缝参数顺序错误，已修正并保留其失败原件，不作为产品反例。

已在 worker 按原计划实现完整树 converter、V2 派生 client、两次 dispatch 容量 gate 与 v3 固定出口，尚待修后验证。新安装、原模板、fresh 两轴独审由根接续；实现不能自行标为完成。真实 Temporal、10MB 晚期 reader、统一最后 gate 及真实 CPU 两候选仍未验。

- `dispatch-r1`：9 过，52.59 秒。原 H/S、claim/fsync 与实际 SDK StartWorkflowExecutionRequest；Payloads 32767/32768、Memo 2047/2048 接纳，+1 分别在 claim 前／后拒绝；后者保留 attempt 且 reconcile 无新编码或 start。最终编码阻塞受原 4 秒窗口收尾，原进程已退出。
- `runtime-r1/r2/r3`：原 SDK completion、默认 sandbox 及一个原 lifecycle 入口分账。初次新测试有 4 项数据构造失败：默认 SDK JSON 把非 ASCII 编为转义，另有 protobuf varint 增量；按实际 converter 重新推导长度后，相应失败项修后通过，没有改生产阈值、路径或预算。原失败日志保留，最终有效计数待 freeze 时汇总。
- `v3-stop-r1`：首轮 fixture 缺少独立安全 stop，而 schema3 stop-writer 按原 gate 拒绝，drain 因而继续等待原 total。已只中断本轮自有活动，并对同一隔离 fixture 写入原本地安全 stop 让第二场收尾；两场不作为验收。新测试把真实独立 stop 放在 fanout 前，未缩短或扩大原 deadline、未绕过 schema3 执行 gate。中断与原安全 stop 的实际进程／参数留在本轮私有证据。

## 固定候选与接续

准确冻结为 `impl-r1/freeze-r2/summary.json`：完整五文件 diff `source.patch` SHA256 `622a2ba0065162dc9839cc1d4c19048b372e2127bee9c9d433785e634dde49ab`；2071 完整 tracked 输入、无 untracked，`inputs.json` SHA256 `80097df2331bc2b84505409408b489c7277c959ab103e4ed801f2968b9ac4b96`；669 产品文件的字节／mode map SHA256 `8f2e88a5bdfbc3b783a6dd9707be79732d2051d80ecee392a5819f1054a84f76`。worker raw SHA256 `1fb235e141ce196d45e7c6ccdc95d04c4ed10c47dcff54335f00ef1fd0fd7044`。原 V1 和 V2 Workflow class AST 均逐个相同，推进算法未改。

产品只有 worker；其余四文件是三个原测试文件与原 operations fixture。最终发送先完成容量编码，再执行原 final-ready／remaining gate，编码不留下陈旧准入窗口。v3 封闭错误也显式保留 SDK cancellation 路径；V1 仍保留原错误／cause 行为。

`freeze-r1` 留有一次未完成冻结：根在受审原计划后追加实施状态，因此当前计划 raw SHA 与受审原件不同。`freeze-r2` 分别冻结当前状态文本和 `design-r1/plan.md` 的受审原件，后者仍为原 SHA `25069bee…`，没有把状态追加当成产品设计修改。

- 最终 runtime 接缝 79 过／1 旧 history 子进程原 10 秒超时；未改时限，单独 `replay-r2` 已在同一源码 3.56 秒通过。最初失败保留，不能抹成首跑全过。
- `core-import` 在现成无 SDK core 解释器导入本树 worker 通过，`temporalio` 实际不可用，模块未定义可选 converter。新安装尚未运行。
- `v3-stop-r2` 聚合超界场已真实到达完整 66 分支并通过；接纳场在 cold 原 10 秒窗口内未完成（并发 runtime 检查），只得到 unknown／0 分支，不认证 N32 接纳。独立 `v3-stop-positive-r3` 在原时限 41.67 秒通过接纳场，完整 66 分支／原 refs bytes+SHA／全部实际 S/H cleanup 保留，210 个观测到的自有进程终态均为身份消失。两场的最终 protobuf 与组装原件及精确大小保存在 `n32-summary.json` 和各自 fixture 目录。
  接纳场最终完整 Payloads 为 **19,424 B**；混合 ref／inline unknown 聚合为 **37,515 B**（各分支单独合界），整体拒绝，SDK 实际最终完整 Failure 为 **1,205 B**。schema3 stop-writer／notify 效果仍在真实 H gate 拒绝，其原完整诊断保留；这些结果不能认证真实 V2 dispatch 或 server 包装。
- final-ready 顺序收口后的 `final-dispatch` 4 个超界参数通过（26.19 秒）；全局 `-k` 也过滤了原 final_admission 节点，因此 6 deselected，不计成原准入重跑通过。原 9 项完整 dispatch 结果另属前述 `dispatch-r1` 身份。原许可／final-admission 行为不因本片未变而重跑；根已要求此处停止扩大检查。
- 全部实际命令、stdout／JUnit、PID／BOOT／start_ticks／终态保留在本轮私有证据；最后 core／replay／final-dispatch／N32 接纳的 command JSON 还分别保存运行前后五文件 SHA，与 freeze 相同。当前没有本轮在跑任务，未安装、提交、合入或推送。

根下一步可在该准确冻结上做一次非 editable 新安装：执行本片 39 个新参数节点、一个原 service wiring/shutdown 节点、原 SDK frame 容量／V1 原诊断节点和原 history 节点；core 无 SDK 单独复核。不要重跑未变化 V2a 许可／拓扑／shutdown 全矩阵。N32 场最重，原 32 候选准备与完整 fanout 都必须保留。源码／本地服务替身／安装／原模板／fresh 两轴独审分账，最后三项交根负责，作者不自批完成。

## 根固定候选与新安装

根已将上述完整五文件patch逐项核SHA／执行位后，应用到从c540939建立的独立固定树 `training-cycle-v2-capacity-fixed-r1`，普通保存准确产品 `919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`。原作者树和freeze保持，固定树干净；没有混入S1或文档整理。

新非editable wheel SHA256 `8fe43f445700845a4ee5e1e718ac6aacd5bcb73f031d03c0ff2ee7c4286b49d3`；core／SDK两份安装各668完整包文件，source／wheel／实际site-packages字节与执行位相同。作者669源文件包含原根AGENTS，按原打包规则排除它，未漏产品。三训练owner真实从site-packages导入，core无SDK、SDK1.34.0；283参考与依赖检查均过。相对c540939唯一包变化为worker，新增／删除均0。

原件 `package-r1/` 保存固定输入、完整diff、wheel、两安装、导入／包map和实际命令。37个新增非N32参数节点和4个受影响原接缝的新安装定向 **41 passed／52.85秒**（runner54.079秒）；捕获133个自有进程身份，结束后均absent。fresh源码独审[两轴approve／0](2026-11-16-training-cycle-v2-capacity-source-review.md)，审查者另只读解析原N32与dispatch protobuf核实际大小，没有重跑产品。

N32新安装的首次runner使用了相对Python路径，而runner将cwd设为copied-tests，因而FileNotFoundError，**pytest／产品子进程未启动**。原空stdout／stderr保留，明确启动失败记录为 `package-r1/installed-n32-not-started.json`；它不是N32产品失败或通过。接续须用绝对Python argv及新label（例如 `installed-n32-r2`），保留原时限，串行跑两场。原源码N32两场通过不转授安装。

原模板、N32新安装和普通集成／发布仍未验；真实Temporal、完整M1c、10MB晚期reader及CPU两候选保持原未验范围。用户要求交新agent接续，此时未启动其他模型／训练／服务或在跑检查，准确接续入口见中英handoff。

## 交接接续：新安装N32与原模板完成

固定树仍干净、准确HEAD仍为 `919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`。逐项重核现有core／SDK各668安装文件SHA均与冻结记录一致。按交接命令改用绝对解释器、新label `installed-n32-r2`、`-I -B`并清除PYTHONPATH，从copied-tests cwd串行跑原两参数；没有改fixture、原10秒窗口或完整fanout，也没有同时重跑runtime大组。

- **2 passed／66.88秒**（JUnit66.872秒，0 failure／error／skip；runner67.868秒）；捕获461个本命令自有进程身份，终核均absent。
- 原SDK安装只读解析保存的最终completion与assembled原件：接纳完整Payloads **19,425 B**，聚合超界 **37,525 B**，两场均 **66分支**；超界整体拒绝，最终完整SDK Failure **1,223 B**。这些是本次新安装的实际字节，不把源码19,424／37,515／1,205的不同路径／诊断长度转写过来。
- completion SHA依次为 `d2c49a4aee6730288b1d351865d1e32943be9dc3d0d0d039250fece2b5643d9f`、`dd5bcaf0dbea41a8f8beb0c5d0577fa17e233b458062c82841e99d4c04ade996`。准确argv／raw／JUnit／过程身份及 `installed-n32-r2-summary.json` 位于 `package-r1/`。原参照bytes／SHA与真实S/H清理断言均由原测试到达；schema3真实H effect仍拒绝。

自身原结构模板使用已授权Codex回退：`self-review-r1.py`／`self-review-r1-codex/`，实际 **65.349秒／approve**，两轴approve、无要求修正项。完整5文件diff、11份source／原合同和3份累积资源均进入实际stdin（823,098字节；SHA256 `1f9372739f91949479d183eace18e8ff61eb55e1580c88e574639c586249de20`），原结果SHA256 `8807ad53b8820cc23610b9e2c5dd6a7d3105164935d57f03ed54247c8f008b5d`。原输入如实将当时正在运行的N32安装标为pending；本段据其后终态补记安装通过，不篡改原模板输入／回复，也不声称异后端成功。

本片准确源码fresh两轴独审已闭合；现在新安装41＋2与原模板分别完成，可接纳为closed容量子片。普通合入／集成安装／发布及自己的CI仍待完成；完整M1c-V/R、真实server追加Failure、10MB晚期reader和CPU两候选继续开放，schema3效果保持关闭。

根已按普通非fast-forward合入开发分支，merge `329237958c0c93dbf121388a0e04d9b05ccf7283`，仅5个原候选文件，无冲突；工作区既有文档保留。后继首批文档提交不改变本片产品字节。联合新安装与普通发布／自己的CI仍待完成。
