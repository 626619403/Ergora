# B1：六阶段的完整材料输入

基线 `210f58d46c3332f4d192ee8cb13e8c149dd2173f`，产品基线 `5ab6d350024de8515487d0bedb3b950be60ac867`。承接[D1设计](2026-11-12-six-stage-native-consumer.md)，进度和实际证据写入[交付记录](../delivery/2026-11-12-six-stage-materials.md)。本片只交付完整材料消费者，不关闭总预算、原生嵌套或最终真实旅程。

## 合同与范围

- 新增 task-definition v4、正式 input v8；旧 definition v1–v3、input v1–v7、队列及历史保持。v4 可选用既有工单快照合同。
- `composition.preparation` 显式选一个 inspector 和一个 planner 叶及受限模式，冻结各自实际后端、策略和覆盖范围。两叶各自只接根 task，没有未执行的外部边；原六阶段负责前后顺序与 inventory 结果交付。work/review 继续使用原 DAG、unit 分配、批准、候选与收据。所有 Agent 叶恰好覆盖一次。
- inventory/plan 复用原 Executor、stage_driver、run_input、快照和进程所有者。完整结构祖先正文、Skill、固定阶段指令、原任务、精确起始 Git 文本及 plan 的原 inventory 结果进入实际调用。容量不足整份拒绝，无截断。
- 必要仓库材料由可信 Executor 在精确 starting commit 按声明 read 范围读取，附 Git object 和内容身份。只读 agent 没有任意文件或 shell 工具；仓库文字及其他阶段结果不能授予权限。
- 新输入中 text-only 不能消费未内联的 Skill 附件时拒绝。task-mcp 保留固定 list/read，并记录成功读取的真实 URI、身份和范围；接受结果前核全部所需附件的连续覆盖。此证据证明字节交付，不证明模型理解。
- 保留 trusted current-container writer 的 advisory read/write/egress 语义、原 HEAD 与检查门禁；不新增宿主机要求、调度器、正式账本、通用 patch 应用者或外部 MCP endpoint。

## 实施与验收

|节点|可验收出口|状态|
|---|---|---|
|B1.1 版本与投影|新 schema、明确准备叶、完整覆盖、冻结创建／恢复、独立 queue/request-root；stdlib 读取不引入运行依赖|已实现并独立审查通过，含静态／创建／恢复及纯stdlib读取检查|
|B1.2 实际材料消费者|前两阶段使用真实受限调用；精确 Git、完整 inventory 结果、祖先正文／附件；容量失败、旧模式保持|已实现并独立审查通过；原进程组件旅程及MCP范围回归通过，原首轮失败保留|
|B1.3 行为验收|受影响现有 suite、必要缺失风险回归、原 Executor／stage_driver／native 夹具、安装身份与283冻结文件|已验证：整理后受影响源码295项、非editable安装58项通过；453产品文件／两RECORD／283冻结身份通过|
|B1.4 审查与交付|自己的实际审查模板、新 fresh-context 独立两轴评审、修正复核、普通提交／推送及该候选必要 CI|完整36文件及真实模板原件已由原独立评审同片补核，两轴开放0／0，本地出口通过；实际Codex377.86秒approve／五scope全文，Claude原API400保持；普通交付及该提交CI待做|

实现位置优先使用 `review_dags`、`tasks`、`task_envelopes`、`reference_task_creation`、`reference_inputs/workflows/executor` 和 `task_mcp`。共同行为放在其原所有者，仅在两个实际消费者需要时抽共享实现；不为阶段各复制一个执行器。测试复用现有原生夹具，不增加重复 CI 或覆盖普通显式异常的断言。首次验收不能把手工 stage 活动序列称为 Temporal 完整任务生命周期；完整实际旅程归 D。

每个节点更新本表和交付记录；结束或压缩后核总计划、Git 与证据身份。模型凭据保持外部变量引用，运行原件保存在仓库私有持久检查目录。
