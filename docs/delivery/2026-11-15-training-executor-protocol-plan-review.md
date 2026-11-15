# B3.3b 原生 executor 协议：独立计划审查

日期：2026-11-15。评审者为新的 fresh-context agent `training_executor_protocol_plan_audit`，未参与产品实施。先读原始要求、冻结范围、仓库协议及原调用者，再读计划与作者交付叙述；按 maintainable-project-delivery 独立审查协议和 ergora-codebase-quality 的三个引用核查。本次只审来源准备／原锁内准入合同。

|对象|需求符合|结构维护|
|---|---|---|
|固定 r1 首审|request-changes；R1 开放|approve；开放 0|
|固定 r2 同片复核|approve；开放 0，R1 在设计层关闭|approve；开放 0|

r2 可以进入 b1／b2 实施；这项结论不认证尚不存在的产品、安装、受管执行或停止证明。

审查基线为 `5182bfa03f536d4090b91014f97eedda1c5d2d3a`。r1 来源为 ignored `.ergora/checks/training-executor-protocol/design-scope-r1/`：`scope.json` SHA256 `dd23b56ae2fd8fc16d58b13d3abeb01d4c3e5e4a364e310c28a35b246397512b`，13 份冻结文件全部符合清单，首次读取时对应公开文件也逐字相同。原始要求的 SHA256 为 `52f3556a4fa8f0ff846cfc0761146fcd64dd53c0fe949deac5f65f35aed9560d`。

这 13 份包括本片计划／交付、生命周期研究、原预算执行计划，`reference.py`、`reference_training_budget.py`、`reference_training_worker.py`、原 reference manifest、原 executor／core／sandbox，以及 `test_training_runtime.py`／`test_reference.py`。另追查了原 `agent_platform/training.py` 的 `run-local`／create／poll，应用 `cli.py`／`training.py`，`test_training.py`／`test_training_submission.py` 与 runtime client fixture；这六份调用者逐字符合基线。已读根、源码、测试 AGENTS 与组件变更协议，没有发现本报告目录下额外指令。

r2 复核固定为 `.ergora/checks/training-executor-protocol/design-corrections-r2/`，scope SHA256 `f8200b5fc9e22e23336eb66ef3b8c56a2d49d3fc69d060fb4bfd759203c3b040`。它只替换两份文档，原来源与 delta 继续用 r1：

|文件|r2 字节数／SHA256|
|---|---|
|[计划](../plans/2026-11-15-training-executor-protocol.md)|13206／`e5a26c21a3df12487895df9735eb3cba8b544eb66d039cc1e42a707681988b0f`|
|[交付](2026-11-15-training-executor-protocol.md)|2758／`d81d0e9eaec94f761bc131bd5f54570bd8302f31864b2ff366f579a806425cf3`|

两份冻结原件与复核时公开文档一致；后续状态追加不改变本次审查身份。

**R1（P2，需求符合）：准备中断后，完整 base 可被当成 legacy 来源接纳。已在 r2 设计层关闭。** 固定 r1 计划第 55、57 行要求拒绝部分派生来源，却在复制原 platform、Git check／apply 之后才放 descriptor。若进程在完整复制后、descriptor 前中断，目录中没有协议声明，而原 `src/ergora/reference.py:91` 的 legacy validator 会接受全部原 Python 文件。本次用冻结函数本体和独立复制目录实际复现 `validate_installation(..., training=True)` 返回该根。这使拟议的 descriptor 缺失时 legacy 回退接纳尚未完成的协议准备，违反半成品拒绝合同。

最小修正是在复制可形成有效 legacy 树的源码之前，独占创建并持久化不完整 descriptor，任何已声明但无效的 descriptor 均拒绝回退；完整来源核验后才发布固定完整 descriptor。r2 第 55、57 行已明确空 descriptor、文件和新目录同步、失败拒绝 fallback，以及最终完整核验。此前窗口不再允许“完整 base＋缺声明”成为准备的中间状态；即使最终 descriptor 已可见，validator 仍须逐文件核完整来源。R1 的失败原件保留。这里关闭的是修订合同，未声称实现或断电恢复测试已通过。

其余边界的核查结论如下，未发现新的阻塞项：

|边界|证据与判断|
|---|---|
|原锁和拒绝位置|固定 patch 直接在原 `process` 的同一 `executor.lock` 内检查 started／受管目录、调用 hook；它们位于原业务 `try` 之前。callback 异常传播，不进入原失败归档，不写 started／result。Git、runner、archive、track 与结果主体保持原字节。|
|result／started 竞态|原 result 仍先只读返回，不运行 hook，也不形成受管停止证明。无 result 的 started 在 hook 前拒绝。真实子进程运行冻结原 process，在写 started 后于 Git 接缝异常退出；随后派生 process 拒绝，未接管该不确定执行。|
|受管命名空间|无 hook 时，固定 `managed-execution` 路径的文件、目录和悬空 symlink 均触发拒绝，覆盖部分发布。内置 hook 的精确请求／owner／clock／attempt／ack 义务已明确交给 c 片，b 片没有产生执行权限。|
|来源和 prepare|内置完整 descriptor 字节、base manifest 完整 SHA、固定 delta 和唯一 override 构成固定来源识别；元数据不能自授任意 patch 权限。r2 把新协议校验明确为全部 279 个 platform 文件，legacy 保持原用途的 Python 范围。CLI 明确新协议／新目录，只准备来源；Linux／WSL2 目录同步与跨平台已有来源识别分开。|
|旧 writer 前提|第 19 行明确新的独立状态目录、所有参与 executor 均使用新协议，不能把旧 started、活旧 owner 或旧安装转为受管执行。该前提不声称 OS 隔离，仍要求原锁内拒绝不确定 started，合同一致。|
|职责和复用|来源准备与既有 validator 沿 `reference` owner；实际消费者已有 CLI、训练应用进程和预算 worker。hook 留原 native executor owner，无第二份算法、第二实验表或通用插件类族。实际 owner 能力与全周期停止归 c 片，kernel 专家保留在原提案路径。|

实际检查保存在 ignored `.ergora/checks/training-executor-protocol/plan-audit/`：

- 核对两版 scope／文件 SHA、六份相邻调用者与 Git 身份，原 283 文件逐项摘要全部匹配；最终 `src/ergora`／`tests` 的 Git status 为空。身份清单为 `source-verification-r1-r2.json`，SHA256 `f10486d55c92a7629843ad16d9801b954cdcdd782efbb6604d7a697f6281f761`。
- 运行 `python -I -S .ergora/checks/training-executor-protocol/plan-audit/run-probes.py`，exit 0，1.168 秒。包含 R1 复现、带空格新目录中的真实 Git `apply --check`／apply、完整派生 SHA 与语法编译、10 组接缝检查。其中六种 started／namespace 形态、真实 flock 争用、hook 内另一子进程无法取得同锁、拒绝 hook 无 native 业务副作用、已有 result 只读，以及旧 process 写 started 后退出的交错均符合预期。
- 固定 patch SHA256 为 `45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`，派生 executor 为 `feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`，与 r1 计划完全一致。`probe-results-r1.json` SHA256 为 `33bfda8b35fa0cf434cde609844def62bc118e8e2d5220f135186f8c7de00752`；脚本 SHA256 为 `f6e70303a9c589665641306fe922ea92e9d4b8baae200d3bc10498f50278e9e6`。

上述行为探针执行实际原／派生 process 本体与原 core 文件读写，使用局部依赖替身，Git 业务接缝停止或异常退出；没有启动真实 clone／runner／archive／MLflow。干净无 hook／接受 hook 只证明能到达原 started 和 Git 接缝，不能当作完整 native 业务回归。r2 的准备顺序只做静态复核，尚无产品 validator／prepare 可运行。本次未安装、运行 pytest、训练、服务或 GPU，未联网跟踪前片 CI，未修改产品、提交或推送。

产品验收仍需 b1 覆盖复制前／Git 失败／最终发布中断、空／特殊／链接 descriptor 拒绝回退、全部 279 文件（含 requirements／脚本）篡改拒绝、原目录保持与真实 CLI 新目录准备；b2 保留实际原锁交错及拒绝不产生 native 结果的回归，补干净无 hook 的原生路径；b3 完成自身新非 editable 安装、相关回归、独立产品审查和精确发布门禁。c 片的显式执行请求、owner 能力、不可重用 attempt／ack／stopped、全后代停止与自动循环仍开放。
