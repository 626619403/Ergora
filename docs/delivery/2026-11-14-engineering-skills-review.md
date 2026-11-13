# S1 工程 Skill 独立审查

日期：2026-11-14。审查者为新的 fresh-context 独立 agent `engineering_skills_review`，未继承实现对话。先读原始要求、固定差异、新文件和实际调用者，再读作者交付；遵循项目 AGENTS、maintainable-project-delivery 独立审查流程，按 codebase-design／writing-for-agents 核对职责、接口与资料可达性。

|审查轴|判词|开放发现|
|---|---|---|
|需求符合性|通过，本片本地验收范围证据齐备|0|
|可维护性|通过，未发现有实证的职责、抽象、冗余检查或资料使用缺陷|0|

基线和审查时 HEAD 均为 `560bfdfab1b48486f71b0677a5f5113923d7ad30`。初始 r1 十九文件清单 SHA 为 `65053da09242dd2354c89417f79e463de8389b3fef91daa8915375a89e1ba086`；最终 r2 为 `cfbd2470a30dfd65b82d57a80ff65e34c7c26ede36004b352289ccaec0dd0892`。十九文件逐项重算通过，最终 tracked diff SHA `4a6e6e6014503cf63c3d95553f6e3ed9d8d837bf229c086f8da5e8fdcad45473` 与基线实际 Git 差异一致。r1→r2 仅 PLAN、本片计划和交付的验证状态更新，产品及测试未变。

完整范围为 README、PLAN、TRAINING、USAGE、WORKFLOW_DEFINITIONS、本片计划／交付七份文档，catalog、原 preset 测试，以及新重构／性能父包内十文件；前片 H3a reviewer 自有报告不属于本片产品。另沿 `workflow_definitions` 的 install／materials／compile／snapshot、`definition_bundles`、`skill_assets`、`agent_runs`、`agent_backends`、`task_mcp`、`task_envelopes` 和实际子模板／角色核对消费者，未用工作树后补状态替代 Git 基线。

需求和结构的依据如下：

- `refactoring-quality` 明确选择原 ID `ergora-refactoring-template@1.1.0`，复用原 delivery 与全部角色。新父根与旧根的节点、端口、权限和预算逐项相同，原 instructions 逐字相同，仅增加标准 Skill 资源。`optimization-performance-diagnosis` 复用只读 analysis-v2→measurement-v2；原 runner、批准、候选、unknown、预算和进程 owner 均未迁移。未增加运行器、账本、库或厂商分派，未降低原 write／shell 叶以绕过准入。
- 两个 Skill 放在实际服务多个后代的父资源中。工程三分支能直接到达包内规范来源、真实依赖与测试接缝；性能路线按格式、版本、phase、硬件和证据缺口选择 reader，区分建议、可用和实际执行。既有 loader 固定完整 Skill 树、编译器累加祖先并检查权限与预算，原 MCP 提供附件；无需新抽象或复制角色。新版本完整包的少量历史重复是固定身份要求。
- 新文本依据本地经验写成可移植指导，未见未知许可用户全文、外部脚本、机器规则或完整第三方流程重新分发。研究保留来源与许可边界；包内六份 Markdown 对库存中可读的四十二份本地来源作辅助逐词比较，无连续十二词相同片段。该比较仅辅助直接内容审查，不替代第三方工具的许可和可用性核验。
- 原测试按新增 preset 参数扩展，核对版本并存、完整祖先、只读权限、冻结后重启和原正式 v10 装配，未新建框架或以措辞匹配替代行为。新增断言防止无父资料时空遍历通过；未见只复述实现的冗余保护或限制有效配置的新增常量。两条约 97–98 秒的旧方向耗时不足以归因本片资料为性能回归。

独立核验了以下原件与身份，没有启动新模型、安装或业务实验：

|证据|核验结果与范围|
|---|---|
|noneditable 包|wheel SHA `7cbf6594483b7197640b0be74a869ac05c811e014623cd7e5cb968dba9f6d8ab`；561 源码／wheel／安装／当前产品逐字一致，569／574 两 RECORD 及 283 冻结文件重算通过。基线 551 产品仅 catalog 改变，23 旧 entry、全部旧角色与根保持。|
|标准包与本地使用|两份标准 validator 原命令／stdout／stderr 均通过；原 CLI import 的 4／2 文件与注册树重算一致。home 两树与安装包一致；安装脚本只允许缺失时复制或已有完全相同，差异时先失败，未覆盖用户修订。|
|原 preset suite|原 stdout 与受控进程回执为 33 passed／352.48 秒，owner 354.014 秒、退出 0；执行的测试源码与审查快照一致。正式装配检查证明 prepare 合同，未证明六阶段实际重跑。|
|四个实际只读叶|planner 105.871 秒、structure 47.203 秒、test-value 44.847 秒、profile 56.934 秒。逐 run 重算冻结输入、实际 stdin、scope、原 audit 和原 result；25 inline 资源及 11 参考累计 16,493B 完整交付，所有祖先来源齐全。|
|角色判断|人工通读原回复：planner 保留 Queue owner、区分结构方案与既有恢复缺陷；结构／测试价值对夹具 request-changes，采用目标规范并识别双 caller／恢复 counter 与局部通过的覆盖缺口。profile 请求同症状反馈，对不同 phase／单 rank 的合成 inference 元数据保留训练通信归因 unknown；未编造 reader 已运行或收益。|
|自身原结构模板|run `089286d95a4d4123a9f83f49430aacb2`，29.730 秒 approve；十四完整文件 59,831B 及三份原继承资料均在实际 input／stdin。input `c30d57a4c3d43a6a7d005f32f15fc17f60b6d4efcebefabdf2b573c89107f8e9`、prompt `417918e9f3cacb482d4b223f361ba3f2005fd33c289496cfe378e723838141b1`、result `8b14a5c60989ddfcfa0d43315ea9134bbf8844357a06811bb0e4d4a92835f55c` 重算一致。|
|文档与收尾|完整十九文件的 347 处本地链接／142 个目标均存在，新增命令及版本选择与原 CLI 一致；Git diff check 通过。八个原 MCP audit PID 再查均不存在；夹具精确 HEAD 和八源码保持，三份 pyc 缓存独立列出。原静态驱动对缓存的过严断言及其修正范围如实保留。|

自身模型只覆盖所供十四文件及原继承资料；README／USAGE／TRAINING／WORKFLOW_DEFINITIONS／PLAN 的本片变更、相关使用说明、最终身份与本地链接由本次独立审查核对，没有算入模型输入。实际只读行为只证明资料交付和这些案例的角色判断，不证明理解保证、生产隔离、正式六阶段重跑或真实 GPU／业务收益。原 Claude 超时及显式 Codex 回退仍保留，未宣称异后端成功。许可／来源、全文读取、安装与行为的私有独立核验记录已保存。

发布前状态补核发现并关闭一项 P3：`docs/plans/2026-11-14-engineering-skills.md:24` 的步骤 2–5 段尾仍称自身模板和独立两轴待完成，与相邻完成段冲突，会给恢复工作者留下错误待办。作者已只保留“发布／自己的 CI 待验”，并将首段历史“开始步骤 2–3”改为精确基线说明。复核通过；三份状态 MD 之外的十六作者文件与 r2 逐字相同，原验证结论不变，无需产品重测。PLAN 和交付已准确回填本地出口完成，H3a CI 的独立终核仍单列归属。

本片无阻断发现，P3 已关闭、开放 0／0。r2 中“独立终核在做”对应冻结时状态，之后的本地出口回填已补核；普通发布及本片精确提交、自己的 CI 尚待核验。真实 workload、B3 实验、正式采用和其他工作片的未验范围继续由原 owner 承担。
