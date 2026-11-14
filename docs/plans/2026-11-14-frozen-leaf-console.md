# F10d4：原冻结输入的只读单叶调用页面

日期：2026-11-14。接[F10d3b2结果检查与导出](2026-11-14-retrospective-results-console.md)；具体实施基线在前片普通发布后固定。目前只做调用链与验收设计，没有实现或继承任何包／CI成功。[PLAN](../PLAN.md)。

## 已核接缝

`agent_runs.check_input → _admit_input → _admission` 持有当前后端准入、完整 input／祖先材料／grant 与叶权限、角色／binding／policy。`run_input` 重做原准入后，交给 `_run_prepared` 在任何模型调用前保存原 run，复制／重新核完整 snapshot，沿原 adapter 和 process owner 执行、保存结果／失败。原 `runs` 返回最近100原记录，`output` 持有有界诊断与原生归档；不能另建页面运行表或把请求超时当作没有运行。

已有普通 role/prompt 的 `agentDialog` 不是这个入口，不能用它替代冻结 input。现有 `retrospectives` prepare/check/export 不执行模型。原组合的静态端口和 `depends_on` 仍不等于自动图执行。

## 拟实施的完整小片

- [ ] 固定前片普通发布基线，核原caller／已有组合运行测试与后端支持；记录真正新增的文件与接口。
- [ ] 沿原 `agent_runs` 增加外部消费者可选的 input digest 约束，在同一次完整 `_admit_input` 读取内核对，原CLI默认不变。HTTP不得先读一次再对另一个input执行；原snapshot复制后再核仍保留。项目是本次原run的执行归属；一般组合task正文不推断为统一的项目schema，复盘特有项目关联继续由其原input检查展示，不冒称所有input都含项目声明。
- [ ] 两条薄HTTP显式检查／执行原只读叶。明确传目录、input digest、后端／model／原因、可选推理配置路径和超时；不接workspace、原生shell、权限扩张、正式Task批准或自动fallback。先以原text-only模式打通复盘作者／审查者，其他原CLI模式保持单列支持范围。
- [ ] 界面复用原Agent交互owner，允许明确选择定义请求或实际已注册后端；展示原角色、requested/actual binding、完整资料身份、原权限与准入范围。配置变化使旧检查不可作为当前就绪状态。检查是当前观察，执行前原owner重新准入，不称租约。
- [ ] 执行只能由明确提交触发，执行中防重入、不自动重发／接续。保留原目录与实际参数；切页／丢回复后通过原run目录与记录明确查证，不能因页面失败声称没有调用。需要新观察入口时只读原 `runs`／`output`，不创建operation ledger、后台调度器或另一执行状态。
- [ ] 结果展示原run ID、实际后端、状态、result路径／SHA和原输入摘要；提供明确的原结果交接动作，将这些原字段带入现有结果表单，仍由用户选择正确方向并明确检查，不自动发下一调用。已卸载或已换项目的旧回调不修改新表单。完整复盘检查继续使用d3b2原输入／结果，不能把截断stdout当作完整候选。尽量作者／审查者异后端；显式Codex回退保留原因，不当作异后端成功。切页／项目／旧回复受现有生命周期约束。
- [ ] 最终非editable包／两RECORD／283、受影响原suite、真实CLI／HTTP／浏览器原冻结只读输入→单次run→原完整结果→d3b2检查／导出，至少一次实际模型并保存完整stdin／祖先资源及原回复；失败、输入变化、不可用后端、丢回复／重复操作、观察／切页、三宽与收尾。分别记录夹具和真实模型，不把合成候选计为质量改进。
- [ ] 自身原结构审查模板、新fresh-context需求／维护性两轴终核，原件／源状态保持，文档逐步更新；前片门禁闭合后普通发布／完整Ref／自身CI与原reviewer补核。

## 接续范围

接可信Skill评价／明确采用回退与记忆／流程原保存／import旅程，再完整F10／F9d／G1公开安装升级与交接。这里不新建通用workflow执行器、执行池、自动重试／自我批准或任何形式的OS隔离承诺。
