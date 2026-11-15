# 停止并发测试CI修复独立审查

日期：2026-11-15。Reviewer：`/root/cycle_stop_overlap_fix_review`，fresh context；未接收实现对话，未继承自身模板的approve结论。本报告为独立磁盘审查，只新增本报告，不修改产品、测试、安装或其他工作树，不提交、推送或重跑远端CI。

## 固定范围和依据

基线及审查时HEAD均为`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`，候选分支`fix/cycle-stop-overlap-ci`。完整候选包含：

- `docs/PLAN.md`：新增本片检查点。
- `docs/plans/2026-11-15-cycle-stop-overlap-ci.md`：本片范围和验收。
- `docs/delivery/2026-11-15-cycle-stop-overlap-ci.md`：原失败、各次本地运行及交接。
- `tests/fixtures/training_cycle_operations.py`：完整marker发布及真实通知前的重叠前提。

冻结原件位于主项目的`.ergora/checks/cycle-stop-ci-investigation/`，不是候选工作树内的同名目录。直接重算`candidate.patch`的SHA256为`e9edb8916cbe09367368e91cecf436de656f2515aa5c30069647ed24f134e262`；四文件均与`candidate.json`的字节数、摘要及`candidate-files/`副本一致。fixture为3,987B，SHA256为`744a6af33be635bfc0fb16e05ac00b0ec960a560688846fa10f8316a8c132155`。

标准来源为根、源码和测试的`AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)的“执行和证据／脚本和检查”、本片[计划](../plans/2026-11-15-cycle-stop-overlap-ci.md)，以及`maintainable-project-delivery`独立审查brief、`ergora-codebase-quality`三个reference和`code-review`。同时检查实际worker、原clock／protocol、pidfd通知和原测试消费者；仓库`pyproject.toml`未配置额外formatter／linter／type checker，不套用外部项目规范。

## 需求和标准：approve，开放finding 0

原测试仅等待`beta-notified`即读取另外两个marker；实际worker为各分支创建独立task和S/H进程，不承诺它们到达storage seam的先后。候选fixture第74–82行在调用保存的真实`notify_identity`之前等待writer同步和alpha owner读取两个marker。两个marker均在原阻塞钩子中发布，原测试仍立即核两个完整进程身份存活，并在结束时核unknown／notified、operation stopped和owner／阻塞进程全部回收。这保留了并发要求；串行执行阻塞分支不能靠新增等待获得通过。

等待每轮复用`cycle_operation_remaining(payload)`，该函数直接读取原授权clock和原有效policy；睡眠最多为0.01秒或当轮剩余时间，耗尽时不执行真实通知。没有增加原26／8／3预算、重开clock、续发操作或在通知之后补等。`mark`第22–25行在同目录写完后rename，再让消费者看见事件；原通知仍核完整PID／start_ticks／boot_id。产品、原测试正文、依赖和显式CI分组无diff。

直接检查官方原`run-response.json`、`jobs-response.json`及公开`job.html`，字节数和SHA与原调查报告一致：run43713822317／push／attempt1绑定精确基线，七job成功，job132810977047失败；HTML包含缺失`stop-writer`的FileNotFoundError及1 failed／524 passed／13 skipped／1612 deselected／998.57秒。新的本地通过没有改写这个failure，也没有足够原远端输出来唯一证明当时的具体调度。

## 可维护性：approve，开放finding 0

变化留在已有fixture和实际调用点，复用原clock、通知、supervisor与reaper；没有新增框架、生产分派、测试入口、CI job或重复断言。扩展既有`mark`以发布通知payload，有明确的同一fixture消费者。缺marker的分支保护真实并发前提，完整发布防止消费者看到半写JSON，均有可达风险；原检查继续保护目标身份、unknown与资源生命周期。未发现需要迁移owner、抽取额外helper或扩大回归矩阵的具体问题。

## 原件核对和本次检查

直接核对request、stdout、JUnit、受控fixture和实际operation输出：

|已有实际运行|原件结果|独立核对|
|---|---|---|
|旧fixture受控调度|1失败／29.681秒|原2698行同一FileNotFoundError；beta真实通知完成，另外两个H后到原接缝|
|修后同一受控调度|1通过／29.373秒|相同延迟块；beta H先就绪，原真实通知及全部原断言通过|
|正常非editable安装|6通过／65.729秒|原双owner、两种取消、冷inspect、旧身份通知和原clock耗尽；最终fixture副本同一|
|正常候选源码|1通过／29.631秒|原双owner并发测试，源码导入与安装导入分开|

两份受控fixture各只插入一份相同`controlled-delay.py.txt`：删除该块后，分别逐字等于旧基线fixture和候选fixture；两份完整原测试及配置均与基线一致。monotonic记录确认writer／alpha在beta就绪后约1秒释放。文件mtime精度不足以单独证明候选同一秒内的严格顺序；本审查的先后结论来自通知前的控制流、完整marker发布及仍存活的原进程断言，不将mtime同值充当严格时序证据。

本次另做只读核验：用固定Git树逐字对照652个产品文件、候选源码和现有site-packages，全部相同；源码目录另有未打包的`AGENTS.md`，也保持基线。178份候选／正常安装冻结输入的大小和SHA全部相同；实际导入分别指向候选源码及非editable wheel安装。重核28个已知actor完整身份，活匹配0；在其他只读检查结束后单独检查关联证据路径的活动命令行，匹配0。fixture AST解析及`git diff --check`通过。

自身模板原件也直接核过：12份冻结完整文件合计360,407B、三份原resource正文均完整进入实际stdin，stdin与prepared prompt一致，原result与回执SHA一致；最终fixture与该供稿同一。其19.938秒成功只证明所供文本的审查，本报告没有据此继承判定。

## 接受范围和剩余证据

本地候选在上述需求、标准和维护性范围内无阻断finding。本次没有重跑既有suite或模型，没有安装，也未执行完整group5；运行结果是经原件和身份核实的已有实际结果。本地Python为3.12.11，官方失败环境为Ubuntu3.11，精确远端调度和完整原日志仍未取得。

本报告不认证尚未执行的提交、发布或新候选远端CI。后续由主控按既有授权固定候选并验证其自己的适用CI；原失败run始终保留failure身份。
