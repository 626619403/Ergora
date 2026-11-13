# S1 工程质量与性能诊断 Skill 交付

日期：2026-11-14。按[本片计划](../plans/2026-11-14-engineering-skills.md)，从已普通推送的 `560bfdfab1b48486f71b0677a5f5113923d7ad30` 开始。前片 H3a 自己的 CI 单独验收，不借作本片结论。

## 范围与选择

[本地经验盘点](../research/2026-11-14-local-engineering-skills.md)已完成。复用原 Skill metadata／tree/import、Workflow 父资源继承、preset 与六阶段合同；新建两份原创短 Skill，通过新的 `refactoring-quality` 和 `optimization-performance-diagnosis` preset 显式选择。前者只将重构根升至 1.1.0，原子流程／角色保持；后者给共享 v2 分析／测量角色提供症状与工具路线资料。旧 23 条目和所有旧资源保持，不改权限或预算。

工程 Skill 的实际消费者为重构执行、结构审查和测试价值审查等原子角色；通过一个父资源服务全部后代，不复制四套角色。性能 Skill 只指导证据匹配、反馈命令和有限提案；parser、采集、实验和批准仍归原工具与 owner。不为资料增加运行器、数据库或上层工具分派。

## 进度与证据

两份原创 Skill、新根和 catalog 已实现。原 551 产品除 catalog 外逐字保持，23 旧条目不变；重构新根和诊断新根分别与原参考根的权限、预算、节点及数据端口一致。新增资源 10 文件，无新的产品 Python、运行器或角色分派。

独立 Python 3.11 noneditable wheel SHA `7cbf6594483b7197640b0be74a869ac05c811e014623cd7e5cb968dba9f6d8ab`；561 产品在构建源码／wheel／安装逐字一致，两 RECORD 569／574 行和 283 冻结文件核准。标准 Skill validator 两份通过。原项目 CLI 实际导入两个 Skill 成功，分别为 4／2 文件；树摘要为 `45bb58d30e958c314f29ecc9ed50c016f1ca3d2245b59d66fab7870da0a07693`、`88017dbf291214dcfe387603038b9ad3282184a7dc6fe02593d3c1abb838f5e1`。本地 home 从同一安装包复制后核相同树摘要，未覆盖既有用户修订。

原 preset suite 扩展到新根，33 项全过，352.48 秒 pytest／354.014 秒受控进程；身份并存、祖先全文、权限／预算和原正式重构装配通过。最慢两旧方向各约 97–98 秒，新方向约 4 秒；单次总耗时不直接归因为新增资料或性能回归。带写入请求的执行叶只能由原正式工作 owner 调用，本片不降低其权限绕过准入；planner 的重构建议不冒称执行者已编辑或正式六阶段已重跑。隔离夹具的局部 normalization 实际退出 0，双 caller／恢复复现实际退出 1；只验证角色如何处理这些事实，不将夹具当外部业务性能实验。

四个实际原只读叶均成功：planner 105.871 秒，结构审查 47.203 秒、测试价值审查 44.847 秒，v2 profile 56.934 秒。共 25 份完整 inline 资源在实际 stdin；11 份包内参考累计 16,493B 经原 task-MCP 连续字节读取核准。结构和测试价值对缺陷夹具均返回 request-changes：依据目标行宽 110／渐进类型而非外部风格，识别双 caller／恢复 counter 丢失和局部通过的覆盖缺口，保留原失败及必要检查；planner 未制造无价值 facade 或把行为修复混作保持行为重构。profile 对没有基线的慢现象提出具体原 runner 反馈，对不同 phase／单 rank 的合成 inference trace 保留训练通信归因 unknown，未声称执行 parser、GPU 或收益。行为结论来自原 response 的人工核查，不用字面词匹配当评测。

## 自身审查与独立终核

新的原结构模板 run `089286d95a4d4123a9f83f49430aacb2`，29.730 秒 approve；十四份完整产品／测试／计划／交付共 59,831B 和三份原继承资源均在实际 input／stdin。input digest `c30d57a4c3d43a6a7d005f32f15fc17f60b6d4efcebefabdf2b573c89107f8e9`，prompt SHA `417918e9f3cacb482d4b223f361ba3f2005fd33c289496cfe378e723838141b1`，result SHA `8b14a5c60989ddfcfa0d43315ea9134bbf8844357a06811bb0e4d4a92835f55c`。原 Claude 完整审查超时和用户授权 Codex 回退依据保留，不声称异后端成功，也不将模型阅读材料当独立运行测试。

十九作者文件的 142 个本地链接目标及凭据值匹配检查 issue 0；八个原 MCP audit PID 在终核时均已不存在，未提前采样 starttime，结论限此观察。夹具精确 HEAD 和全部八份原源码保持；只产生三份 Python bytecode 缓存。首次静态驱动把缓存当成源码改动而断言失败，修正为原字节／HEAD 加独立缓存枚举后通过，产品未变。

新的 [fresh-context 独立评审](2026-11-14-engineering-skills-review.md)已完成完整十九文件、原角色输出、安装／完整读取及最终状态终核；需求和维护性两轴通过，开放 0／0，无实证 finding，S1 本地出口完成。最终作者快照 manifest SHA `cfbd2470a30dfd65b82d57a80ff65e34c7c26ede36004b352289ccaec0dd0892`；此后仅补记状态与发布事实。普通提交／推送已核，自己的 CI 及原独立终核通过，不合入 main。真实外部参考项目只由 Ergora 工具启动的 agent 试用；不直接编辑业务仓库，也不以只读方案代替 B3 实验。

## 发布与自己的 CI

已普通提交／推送 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`，父 `560bfdf`；二十三精确 Git 文件和全部 561 产品与测试包一致，原独立报告及 H3a 收尾记录获核准。push 5.523 秒、完整 SSH Ref 1.468 秒均退出 0，Ref 与候选完整 SHA 相同；原独立发布补核通过，开放 0／0。

自己的 CI `43485238011` 第五官方 run HTML 已为 Success；八 job／30 必要步骤均 success／completed，逐步完整候选 SHA 日志路径及原 body／receipt 已核，原独立终态补核通过。前四 run 样本和 Windows 前三在途样本保留，未用 H3a 或另一候选的成功代替。产品内容仍为同一已验包，后续 [W1 源码试用](2026-11-14-workload-source-trial.md)属于独立验证片。

原独立终核重算十八份 HTTP body／receipt 共 3,078,044B、UI 批次、八 job 与全部步骤，开放 0／0；Linux 六组回归 231／301／193／162／146／233 秒，Windows 回归 963 秒、PowerShell 5.1 安装升级 60 秒。最终报告 9,701B，SHA `00c3660c187aae85d8be3cd135f651ad2fb36af64d748a3e62250116c2726b86`；S1 精确交付完成，不借其验收 W1／GPU。
