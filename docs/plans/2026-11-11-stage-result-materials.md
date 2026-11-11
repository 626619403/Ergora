# C5c-M：版本化传递阶段产物，停止递归复制审计

基线`fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`。这是[C5c实际服务验收](2026-11-11-composition-runtime.md)发现的前置修正；原大变更已BLOCKED，不复写为成功。离线原输入1,928,864字节、3.59秒复现；直接前驱全表重复与递归审计正文均有尺寸证据。独立设计审查与后续候选审查记录在[本片审查](../delivery/2026-11-11-composition-runtime-review.md)。

## 合同与边界

1. 原任务定义schema-v2显式选择`execution.protocol: work-units-v2`，发布新的admission-v6。v2–v5封存合同、原输入/receipt/历史读取和恢复保持，原`work-units-v1`仍可选择。页面为新建执行组合选择v2；不改已有任务。
2. v6的具名端口交付的是**全部声明阶段产物与可信检查/意见**，不称完整模型响应。集合为profile的`artifacts_by_stage[stage]`、work的可信`test-results`、verify的可信`check-results`、receipt中全部checks引用产物，以及review的可信`composition-review-decision`。不截断这些正文，不删祖先Skill/上下文，不把审计摘要当成已读取的资料。
3. 原receipt仍携带全部产物name/path/hash，原FileAdapter逐件核验全部字节；原work request/admission/plan、actor/session/claim、formal-call/invocation/selection和实际Git祖先关系仍逐项核。审查意见沿原`review_observation`验证。调用日志、旧提示、MCP审计等留在原证据/handoff内，不能作为下游结果再次递归内联。用户可通过原task evidence/离线handoff核原件，MCP不因此获得任意文件读取。
4. v6 work输入用一个来源表保存端口来源与直接`unit.depends_on`的并集；`dependencies`明确unit→instance映射，同一来源只交付一次。原WorkDelivery仅约束传递闭包，控制先行而未绑定数据端口的依赖必须保留。原plan另列；review保持plan/verification和端口来源。材料顶层版本标明新格式。
5. `reference_inputs`本族注册v6的独立workflow/queue/request目录；新类继承原WorkDelivery调度和活动，不复制算法、不加账本/服务。`task_envelopes`拥有版本结构核验，`reference_executor`拥有可信原件核验和结果投影。tasks/CLI/HTTP沿既有用例，不另写准入器。
6. 1,000,000字节完整输入上限、资源容量、候选/精确批准/取消/未知恢复、283冻结参考均不提高。业务产物确实超预算时仍明确拒绝。没有OS权限扩张、依赖或CI新增。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|M0 原失败与设计|原输入离线复现、单变量尺寸证据；独立核合同/控制依赖/可信检查/意见；明确新旧版本|完成：原失败/尺寸、独立原件及B设计有条件通过；C5C-SP1仍开放|
|M1 最小实现|原所有者内增加显式v6结果投影、独立输入族注册与新建页面请求；旧v5路径保持|源实现与新旧创建路由/安装包定向检查通过；M1完整固定候选独立两轴新增产品finding0，原件/最终出口继续复核|
|M2 回归与真实服务|复用原fixture覆盖长链/扇入及控制依赖、未内联审计篡改仍拒绝、原调用恢复；两个新任务实际六阶段/证据/handoff/history通过；原失败run/原件保持|安装包5定向检查及串行建议意见补验通过；两个新v6任务均REVIEW_READY，原ID/evidence/handoff及194/240事件重放通过；12次native共54份17,740B完整读取补核通过，原v5的1,677文件保持。提交后回执发布前恢复仅静态保持，不称本轮已实测|
|M3 交付|非editable包/两RECORD/283、两手册与架构、实际自身模板/完整新独立审查、本地出口、普通推送/自己的CI/远端身份|439/两RECORD/283及手册/架构已更新；实际自身229.91秒approve/五scope完整读取通过，原独立SP1/ST1关闭，完整27文件独立两轴及本地出口通过，开放0；普通提交/自己的CI/远端精确交付待验|

本修正不开放任意动态MCP附件或隐藏截断，不改只读单叶run-input为整图执行，不将协议夹具称模型质量。完整原始审计按需安全交付及C6容量/模型分页成本仍是后续工作，不能从本片推断无限长链或任意节点数可执行。
