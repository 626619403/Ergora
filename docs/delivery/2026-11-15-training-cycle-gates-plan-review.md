# Q4.2c0.2b0：最后门禁与停止分片的独立设计审查

日期：2026-11-15。审查者为新的 fresh-context 独立 reviewer；先读原始[控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)，再读本片[计划](../plans/2026-11-15-training-cycle-gates.md)和[交付](2026-11-15-training-cycle-gates.md)，并沿实际源码核对，没有继承实现者的结论。本次只审 b0 设计，不是 b1／b2 产品验收。

**需求符合性：approve。维护性：approve。开放阻断 finding：0／0。** b1 可以作为完整的门禁消费片独立交付；b2 的共用监管接口仍须另作具体设计并独立审查，当前没有给该接口或停止 fan-out 产品通过结论。前置 a 片自己的 CI 与原 reviewer 终核仍是产品实施的依赖；本审查没有访问网络，不能据此关闭该门禁。

## 固定范围与身份

产品基线／当前 HEAD 为 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`，分支为 `refactor/architecture-foundations`。独立重算 `.ergora/checks/training-cycle-gates/design-r1.json` 的全部 12 个文件，长度／SHA256 均相同，其中两份新文件为：

|文件|字节数|SHA256|
|---|---:|---|
|本片计划|9,613|`300f96140f7624dcfd673888e51413a57a6e439afaf5c498ff76d533523983f4`|
|本片交付|1,580|`663417933751bd2a0f22f1d3f9449158a28c5fde431bd35515bc99a59f10c0b2`|

四份既有文档的完整 tracked 差异与 `design-r1.diff` 逐字相同：14,204B，SHA256 `4803003c8ad8135c99422f8cc6690ce513e93dd427de6963f5a60402c214d885`。这些差异是根 PLAN 和 a 片发布／CI 状态接续，没有新产品行为。`src/`、`scripts/`、`.github/`、`pyproject.toml` 相对基线没有差异或 untracked 产品文件；因此原 native 文件与 delta 也未改变。此检查没有重新认证前片安装或 283 文件验收。

读过根及源码 `AGENTS.md`、当前 PLAN、组件变更协议，以及 maintainable-project-delivery／ergora-codebase-quality 和相应独立审查、所有权、风格、测试接缝参考。源码检查包括清单中的十份产品文件，另读原 native `agent_platform/training.py`、executor 及其固定 admission patch、原取消通知、备份／恢复代码和手册。

## 需求与可达接缝

1. **b1 与后继 producer 的边界成立。** 计划第 23–29、54 行要求先交付严格的 controller binding、本地三件套、三个原异步消费者的固定父 run 检查及四动作父许可，不创建总 Workflow。现有 `training.start`／`resume_start`、`_Submission`、`BudgetAdapter`、`Execution` 和 native callback 已是实际消费者；可以通过原接缝提供完整冻结输入验证这些分支，无须先交付 c1 producer。b1 验收必须包含有效 controller 分支的真实动作与停止交错，不能只有 schema2 拒绝或孤立许可 helper 通过。b1 完成仍不表示自动循环或即时父取消可用；b2、c1 独立进程／loop／queue 与 producer 均保留前置关系。

2. **许可范围与现有锁可以对应。** 原唯一 RPC 位于 `reference_training_submission.py:233–256`，原 attempt 在 RPC 前发布，`run` 在已有 attempt 时只 reconcile（第 360–364 行）。计划第 13、33–35 行把共享许可保留至实际投递返回，且在阻塞来源／同步之后末次核 stop，没有把早期检查或客户端退出当成服务端取消。原 native create 在 `agent_platform/training.py:137–144` 的 registry lock 内调用可覆盖的 lookup；计划第 14 行在进入原 create 前取父共享许可，锁内 lookup 只复核已选上下文，许可持有到真正 create 返回。原 request／launch 分别在 `reference_training_execution.py:69–72`、89–105 的 execution lock 下发布；计划给出的顺序是父共享许可→原 execution lock。native patch 把 callback 留在 executor lock 内、任何 Git／runner 前，计划第 16 行再以父许可覆盖整个原 process，并在 attempt／ack 同步前后复核。没有要求 drain 反向取得这些原锁，未发现计划引入的锁环。

3. **本地与远端证明各归其 owner。** 计划第 25 行严格核本地 intent／attempt／receipt、原授权、ordinal 与完整 admission；第 27 行另核固定 run 的 describe／首个 started input、类型、queue、独立 memo 与 RUNNING，NOT_FOUND／不可达不放行。现有 `reference_training_runtime.lookup` 只能构造 Experiment 并按其实验身份查询（第 11–41 行），因此同文件中新增明确的 controller 读取用例有必要，不能给旧 lookup 塞特殊 Experiment。submission、worker、Execution 是三个不同生产文件中的真实消费者。具体落点须沿这两类验证：`training._submission` 的 prepare 仍在 SQLite reservation 内（第 280–287 行），所以 `prepare_binding` 只做本地验证；dispatch 的固定父 run 检查在事务退出后；worker 在 `super().create_job_if_absent` 之前做远端检查，registry lock 内 lookup 只作本地末次检查；执行的远端检查在 `Execution.check`，不进入 execution／executor 锁。持父共享许可期间可以 await 原动作；不能为了复用校验把 RPC 挪进本地 prepare、registry 或 executor 锁。native 只消费与 owner context 冻结相同的 binding，复核本地 stop、source、owner、原 clock；不导入 State／SDK，也不声称实时远端查询。该限制与原合同一致，不能据远端 RUNNING 的一次观察承诺取消／terminate 后绝无晚到工作。

4. **actor 与一次机会没有被放宽。** 计划第 23、37 行明确比较完整 selector、schema1／schema2 分支及自动 actor 的原授权来源。当前重复 prepare 只比较两个 selector 字段（submission 第 330–333 行），当前 request 和 native callback 都生成／比较当前 Unix actor（execution 第 30 行、protocol 第 609 行）；这些是 b1 必须迁移的实际位置。按计划让 schema2 request／callback 同核原 authorization actor，而 schema1 保持当前显式操作者，不需要另一种执行授权。原 attempt、launch、operation ID、clock、unknown 对账和已占用机会仍沿原件；计划第 35 行禁止擦除或补发部分落盘记录。

5. **停止的四类事实保持分列。** 计划第 41–47 行要求 writer、各候选的身份读取／通知和 drain 分别监管；通知复用 `processes.notify_identity` 的 pidfd 身份绑定，不按裸 PID 或统一 Temporal cancel。原 `Execution.drive` 及 fence helper 的 completion 判断继续拥有已完成实验的处理，不能为了通知方便取消已接受测量的人工 release 窗口。父 stop 可见、stop 持久、父许可排空和 c2 原 stopped 链的 executor stop 均独立返回；writer 阻塞不挡已识别其他 owner，目标原件本身不可读则保留 unknown。这与 raw contract 的实际能力一致。

## 维护性与尚未批准的设计

计划把 stdlib 记录／binding 校验留在已有 `training_execution_protocol`，让 `BudgetedStart.source` 与 `validate_context` 的实际消费边界复用；项目／State 与远端 SDK 仍留在应用侧。既有平铺 owner、五 key context、source key 集合、原 executor 和唯一 reaper 的职责没有被新建总框架取代。未发现需调整 owner 或新增模块的设计 finding。

b2 目前只有受约束的方向，**尚无具体共用 transport 接口**。这是计划第 45、55–56 行明确保留的后继设计门禁，不计作已完成接口。当前 `_BudgetPhase` 的构造、payload、mode、两帧和输出路径依赖 budget；`processes.run(supervised=True)` 是同步接口；`reference_creation_process` 的专用准备观察也不能直接承担 peer fan-out。不能简单为 cycle 构造假 BudgetedStart，也不能复制 selector／reap 状态机。b2 开始产品改动前，仍须固定实际调用签名、预算与取消来源、frame 身份／容量、start／poll／stop／finish 生命周期、每个 helper 的输出归属和停止后不再 spawn 的顺序，并用原 budget 与 cycle 两个真实消费者解释复用。若需抽取则 b2a 行为保持，随后 b2b 才接停止语义；当前报告没有预先批准该抽取。

另核父锁 inode 疑点：`CycleAdmission._locked`（protocol 第 235–243 行）不把 lock inode 固定进 ready；若活共享 holder 的文件被 unlink／替换，确实可能对另一 inode 排空并误报 drained。但没有发现受支持的并发替换路径：授权创建在原 cycle 锁内使用无覆盖 link，ready 后只打开既有锁，不补建（training_cycles 第 419、461–473 行）；`backups.restore` 要求停写／停止外部工作、原 home 不存在，且拒绝覆盖（第 189–208 行），联合恢复手册也禁止旧栈和恢复栈同时运行。因此不把任意同用户改盘推定为本片可达故障，也不要求修改 ready schema 或新增持久 inode 字段。后继 helper 的清理只能关闭自身 fd，须保留原 admission.lock；在线替换／恢复若将来成为支持范围，应另定义锁代际和排空证明，再宣称支持。

## 实际检查与限制

独立完成两新文档和十份清单源码的长度／SHA 核对、四个本地链接目标检查、tracked diff 逐字比较、产品相对基线零差异检查，以及 `git diff --check BASELINE -- docs`。结合真实调用顺序审过身份、许可、锁、actor、原恢复及 reaper 边界。

未运行产品测试、安装、服务、Temporal RPC、模型、训练或 GPU；未访问网络、提交或推送，也未修改产品。真实晚到 RPC、registry／executor 锁交错、request／launch／attempt／ack 同步窗口、阻塞文件和 peer 通知、进程收尾及 SDK-free 历史链均须在各产品片以其自身候选验收。没有认证 b2 实现、c1 运行边界、自动循环、实际子树停止、业务训练质量或性能收益。kernel 专家保留在 v3 总优化路径，设计没有把全部优化归为 kernel 改写。
