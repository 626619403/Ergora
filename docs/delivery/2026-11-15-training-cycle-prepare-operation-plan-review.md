# c1b0：普通准备操作计划独立审查

日期：2026-11-15。审查者：fresh-context独立Agent `training_cycle_prepare_plan_review`。依据原始要求、批准合同、当前三份文档和实际源码独立核对；只写本报告，未修改产品、测试、依赖或待审计划，未安装、提交、推送或运行昂贵检查。采用maintainable-project-delivery的独立审查指引，以及ergora-codebase-quality的repository-style、module-design、test-seams参考。

|审查轴|最终结论|开放阻断问题|
|---|---|---|
|需求／设计符合性|approve，限修正后的c1b0计划|0|
|可维护性|approve，原owner与验收接缝适当|0|

结论仅支持按原授权实施这一内部普通操作边界，不是对尚未实施的截止算法、接口或运行能力的批准。实际SDK投递、独立cycle服务及normal／stop Worker、Workflow、完整测量接受／rounds和真实CPU两轮仍须各片交付。

本次实际HEAD与源基线均为 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，分支 `refactor/architecture-foundations`。相对该基线，`src/`、`tests/`和`pyproject.toml`差异为空。原先报告的c1a1安装／两轴验收属于前片，本次没有重新运行或扩大其证明范围。最终直接读取的文件身份为：

|文件|字节数|SHA256|
|---|---:|---|
|[当前计划入口](../PLAN.md)|72,959|`3b5460dda453058e547ce8b39868b747b69c02bcef3ed7f802b62965f0475814`|
|[c1b0具体计划](../plans/2026-11-15-training-cycle-prepare-operation.md)|4,077|`06f27f3a2812c14f70eeb24e072c8d2737ca82e2c9411dec19aa6172214ff94e`|
|[c1b0交付记录](2026-11-15-training-cycle-prepare-operation.md)|1,183|`b9c7e37d3f5d4fb6183ecfacb336db72262b9af2f18a62e32b1e89f95ed1c824`|

读取根、源码和测试AGENTS以及[组件变更协议](../architecture/component-change-protocols.md)。父依据为[controller合同](../plans/2026-11-15-training-cycle-controller-contracts.md)和[c1实施计划](../plans/2026-11-15-training-cycle-workflow.md)，特别是后者第48–52行已经批准的一次性普通窗口与自动继续门槛。本次新片是其中的前置小片，没有变更这两份父合同。

需求和实际接缝核对如下：

- **先补普通窗口有源码依据。** [protocol](../../src/ergora/training_execution_protocol.py)第170–244行目前只认可inspect及四种停止／观察mode；inspect持固定1–60秒BOOT截止，其余直接消费原total。原[reference](../../src/ergora/reference.py)第526–556行只提供单次timeout及5秒收尾余量。它们都不能直接证明普通compute∩control。新增prepare-controller仍在同一protocol／worker owner中，适合这一缺口。
- **窗口身份及使用处已明确。** 计划第11–16行把完整snapshot、null ordinal、原boot、control跨度、原compute BOOT上界和连续UTC／BOOT校验写入同一bootstrap合同；父pipe／wait、S的stop_requested、H前后active共同消费它，poll和取消不重置。补充设计明确constructor先取BOOT ticks再取原remaining，避免中间读取增加窗口；原compute已过时允许表达已过截止，实际不spawn H。原inspect和停止total分别保留。实现仍须由`budget_clock.remaining`沿原cleanup reserve计算compute，不另造时钟或仅核BOOT数值。
- **H只组合原准备用例。** [worker](../../src/ergora/reference_training_worker.py)第173–230行已经在H读取并核完整原snapshot；可在其mode分支内active→`prepare_controller(State(...), ...)`→active，沿authorization中的原revision调用。[training_cycles](../../src/ergora/training_cycles.py)第396–429行持本地SQLite reservation，核ready／revision／stop，共用原intent生成与不可变发布；当前原接口也明确prepared intent不是dispatch permit。无需复制这套算法或让storage owner反向导入worker。回传有界typed事实及原intent路径／canonical SHA足够，不要求把完整业务报告塞回32KiB帧。
- **取消、晚到元数据和重启边界现已分清。** 计划第18行保留调用者取消时shield取回真实spawn并回收后重抛CancelledError；超时／有结果的停止观察为unknown。H可能已发布intent，原件保留，无attempt／receipt或训练授权。本片不承诺跨进程恢复同一operation；后继SDK若做恢复必须携原窗口，不能把新建请求当同一窗口已经恢复。旧不可变intent的幂等准备与同一operation恢复是不同验收责任。
- **唯一reaper和证据权威保持。** worker第83–138行仍拥有四个异步send／stdout／stderr／wait任务和原取消结构；第319–327行由`processes.run(supervised=True)`先回收唯一H子树，再发stopped、读取结果。[processes](../../src/ergora/processes.py)第155–200行在实际Popen前及等待中核stop_requested，并在finally回收后代。截止后不得接受迟到成功，清理仍须等真实回收，不能把窗口称为无条件硬返回时限。计划没有接管原start／launch slot、六阶段、v3 kernel专家、原evidence或人工release，也没有以本片准备成功放开自动派发。

初审发现与最小修正已直接复核：

|项|实证问题及后果|最小修正／复核|
|---|---|---|
|R1，取消合同歧义，已关闭|初版计划第18行把“超时／取消”均写成“只能返回unknown”，而第12行保留原shield取消；worker第124–138行与原测试第2763–2764行明确要求回收后重抛CancelledError。按前句实施可能吞掉调用者取消。|最终第18行明确两种结果，保留原异常传播；原件未知不等于没有写入。交付同步记载，未要求修改原取消产品行为。|
|验收说明，已采纳|仅观测H阻塞后的最终unknown，不能单独证明等待期间父loop仍可处理异步任务。|最终源码验收第26行增加阻塞H时并行asyncio心跳；直接纳入原阻塞用例，无需新响应矩阵。|

初版计划SHA为 `3e9cf4b4802683f313685cbe33a93b5b6d44efe2503f98078854250d6748553f`；本报告表中最终SHA对应上述两处修正。当前没有未关闭的设计发现。

验收计划对本片范围足够，实施时仍须在原接缝兑现这些具体观察：

1. 真实S-H准备成功并沿同一intent幂等重读；原授权／clock／intent字节及身份保持，无attempt、receipt、训练副作用。复用既有c1a1准备断言，不另建一套intent字段矩阵。
2. control先到与compute先到分别使用不同有效配置；同一bootstrap在父、S、H及匹配stopped后的读取期间不变。结果越界为unknown；compute已尽时观察实际spawn未发生，不能只测remaining helper。
3. 沿原fault fixture在H的State／SQLite或等价同步入口阻塞，同一父loop的心跳仍推进；在普通mode的post-stopped结果读取处阻塞，仍由原窗口结束观察。取消复用原spawn／helper真实handle及后代回收接缝，保留CancelledError。
4. 延迟准备可能已产生intent时，超时／取消不删除或重写原件，不借丢回复重开clock；原cold inspect、停止total及fan-out／原最后gate的相关回归继续覆盖其既有职责。

已有[test_training_submission](../../tests/test_training_submission.py)第990–1097行覆盖真实准备、幂等、stop交错和原compute耗尽；第2673–2771行的fixture与测试保留真实S-H／stopped读取／取消后代回收。[原fault fixture](../../tests/fixtures/training_cycle_operations.py)已在真实S/H中注入故障而复用原reaper，适合扩展普通mode。上述检查应落在这几个实际接缝，不需要新测试文件、CI分组、通用helper或第二进程driver。[架构测试](../../tests/test_architecture_boundaries.py)保护原依赖方向；新core／SDK非editable安装、652源码对应、283参考文件及适用回归仍是后续产品验收，当前均未运行。

本次轻量检查为实际Git基线／分支／完整差异、原入口与测试源码阅读、`git diff --check`及当前三文档的五个相关本地链接；均通过。待审阶段只有docs/PLAN.md的新增检查点与两份新文档，没有产品变化。报告自身本地链接另行检查。后续把设计状态或本报告链接同步到交付／PLAN属于记账；不把该同步当成新增产品验收。
