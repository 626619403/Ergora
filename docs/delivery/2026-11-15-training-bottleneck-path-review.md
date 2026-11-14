# Q3.3 独立评审：按瓶颈提案路径

日期：2026-11-15。评审者：fresh-context Codex agent `training_bottleneck_path_audit`，未继承实现对话。先读原始用户要求、项目 `AGENTS.md`、工程技能和冻结差异，再读作者交付；未采用自身模板的结论作为本报告判定。

## 最终本地判定

|审查轴|结论|
|---|---|
|需求符合性|**approve（本地范围）**：最终 22 文件、安装身份、两任务十次原调用及材料交接已核；开放实质 finding 0，片内本地验收缺口 0。|
|可维护性|**approve**：开放实质 finding 0；新增变化在原定义／目录／说明 owner 内，复用原角色及生命周期，没有新增运行时分派、拼接格式、调度器或审批权威。|

本地通过不关闭精确交付的后续门禁。普通发布、远端身份及该候选自己的适用 CI 均 **pending**；不以任何前片 CI 认证本片。

## 范围和实际检查

固定基线 `29cdcfe2f45a66dcaad1835c0860c24a78290529`，分支 `refactor/architecture-foundations`。先检查 r3 的 **22 文件**及 tracked／untracked 原件；最终按作者 `review-scope-r4` 重新逐份核对同一集合，全部冻结长度／SHA256 与实际工作树相同，完整 tracked.diff 也相同。r4 范围清单 SHA256 为 `d9a160af3f81e7700df007e3f71efe24b86fc3fe8f3a03b1cf14b9c2922e62b9`，独立记录 `final-scope-r4.json`。本报告不递归计入作者范围。

|最终作者文件组|实际路径|
|---|---|
|入口／手册，4 份|`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WORKFLOW_DEFINITIONS.md`|
|计划，2 份|`docs/plans/2026-11-15-domain-review-optimization-quality.md`、`docs/plans/2026-11-15-training-bottleneck-path.md`|
|本片交付，1 份|`docs/delivery/2026-11-15-training-bottleneck-path.md`|
|旧片追加记录，6 份|`docs/delivery/2026-11-15-training-domain-reviews.md`、`docs/delivery/2026-11-15-training-domain-reviews-review.md`、`docs/delivery/2026-11-15-training-flow-maps.md`、`docs/delivery/2026-11-15-training-flow-maps-review.md`、`docs/delivery/2026-11-15-training-measurement-contracts.md`、`docs/delivery/2026-11-15-training-measurement-contracts-review.md`|
|原创任务，2 份|`examples/training/host-redundancy.md`、`examples/training/kernel-hypothesis.md`|
|产品，6 份|`src/ergora/data/presets/presets.json`；`workflows/ergora-kernel-assessment/` 的 `workflow.json`／`instructions.md`；`workflows/ergora-training-proposal-v3/` 的 `workflow.json`／`instructions.md`／`skills/ergora-bottleneck-optimization/SKILL.md`（两 workflow 路径均相对同一 presets 目录）|
|测试，1 份|`tests/test_presets.py`|

旧 Q2／Q3.1／Q3.2 的文档差异保持其原片身份和历史观察；本报告不借 638 产品重新认证其历史运行。Q3.1 自己的 CI 追加终态由原 reviewer 另核。r3→r4 只新增当前交付事实和计划状态，没有产品或测试变化。

逐份读取新 v3 根、根 instructions／完整 Skill、assessment 子模板及 instructions；读取全部直接复用的 flow／analysis／measurement workflow、五个 Agent 的完整 instructions／Skill 和四份 `evidence-contract.md` 附件。另读 `workflow_definitions` 的安装、编译、祖先资源合并、权限检查、冻结与单叶准备，`definition_bundles` 的完整资源／版本身份，`agent_runs` 的单叶准入／后端选择，`task_mcp` 的固定资源与原读取审计，以及测试上下文和两份完整原创任务。

### 图谱、材料与权限

新根为 `flow → analysis → kernel → measurement`；analysis 内 design／profile 无相互依赖，最终 all-join 保留 flow、两分析、kernel 与 measurement。assessment 包装原 `ergora-kernel-designer@2.0.0`，没有新建同职能 Agent；其允许“无需 kernel 修改”与原 Agent 的证据不足返回路径兼容。

最终根 digest 为 `7532009200221f23d70474e5882c447df4fc65350fd94bed6e79d0566153dd79`；assessment digest 为 `3c83390524cb50e8ffd238eee57e153b672d5323008b664165f8b92c1cdf35a9`，与冻结调用所用引用一致。

四阶段均绑定原 root task。原 compiler 只校验静态端口／依赖；`compile_input` 将完整操作者 task 附加到指定叶，`run_input` 只调用该叶。新说明和训练手册明确完整前驱由操作者逐叶提供，没有声称依赖会执行或自动收集输出。按现有 schema 将模型输出直接替换下一叶 task 会丢失原资料，本片保留原 task 并显式交接的选择有实际理由。

编译后的五叶保留全部结构祖先来源，权限均为 read 上界、无 write／shell／network；权限仍由原 `_within` 和单叶准入持有。根 Skill 指向既有方向 preset，明确另行安装／冻结／调用，不冒称固定图自动分支、挂接或运行全部方向。原后端请求与通用覆盖入口保持；未实际重测全部后端。

### 安装、旧版本与测试价值

独立在本片非 editable venv 用 `-I -B` 从实际源码、r2 wheel 和实际安装目录重算全部文件：**638／638／638 逐字相同**，wheel SHA256 `6ea71afb6378980a7f74594d7124e34ddc2023c18d3d91631dbdc282dc95b11a`。与固定基线 Git blob 的 633 产品文件比较，仅新增五份资源、修改 `data/presets/presets.json`，删除 0；**283 参考文件逐字保持**。旧 v1／v2、原子模板、runtime／schema／依赖／六阶段／实验及审批 owner 没有产品差异。私有独立记录为 `package-and-baseline.json`。

已读原安装回归 stdout／XML：preset、架构边界和页面 catalog 共 **55 passed／82.97 秒**，以及原 Skill quick_validate 和 reference verify 的实际结果。独立只重跑新增组合冻结与旧 flow 冻结两项：**2 passed／13.80 秒**，记录 `targeted-tests.xml`，未安装或跑全 suite。

新增测试不检查提示措辞或模型意见。它保护旧版本共装、保留 kernel 与全部阶段汇合、原 task 绑定、移除活动定义库后仍能从 manifest 准备五叶、完整祖先文本和只读权限。这些是静态资源配方容易静默回退的边界；一项组合回归的成本与价值相称。完整附件实际送达另由旅程原 MCP 审计核验，不把 prompt 包含 SKILL.md 当作附件已读。

## 两任务十次调用的原件终核

独立检查原任务、各叶原 `task.txt`／sealed input、实际运行 `stdin.txt`、原 result JSON 及固定 scope／native MCP audit。逐字比较原任务与所需所有前驱封套，重算 input／result 身份；用原 owner 重新验证 scope 身份、握手和附件连续完整字节范围。不是依据作者 coverage 摘要判定。初次 `journey-partial-r1.json` 只核当时完成的 7 次并标余项 pending；终态 `journey-final-r1.json` 已核 **10／10 次，pending 0**。

两例均为五次显式独立会话，全部 succeeded／exit0；记录总调用耗时 **804.618683 秒**，不是工作负载性能。实际 stdin 保留 **50 份 inline 资源**；八个叶 Skill 附件共 **15,504B**，全部连续完整交付，两个 flow 无附件。两 analysis 分别只收同一 flow 原结果，kernel 收全部三份前驱，measurement 收全部四份。两例 `complete-results.json` 均与各自五份原结果同一；最终汇总／progress 也与全部独立核验身份相符。r4 交付中的十组 run／input／result 表逐项匹配原件。

主机例五叶均已核，kernel 原结果明确 **propose no kernel modification**，以 CPU 解析／生命周期为有界假设；保留空输入、iterator／exception 顺序等反例，无实测收益。measurement 原结果为 **request-changes for candidate validation**，区分只读提案完整性与缺独立执行、成对计时、恢复等证据。它不是产品实现 finding，也没有关闭真实验证缺口。

第二例五份原回复全部读完。其临界路径始终是任务明确给定的练习假设，没有提升为真实 GPU trace。kernel 给出有条件的融合设计，保留 multiply 后单独 float32 舍入，明确 primitive／compiler 意图及 wrapper／alias／stream／autograd／生命周期义务，编译和独立检查仍缺失。measurement 为 **request-changes for evidence readiness**，没有把设计、局部逻辑字节数或提案完整性当作真实 correctness／quality／性能通过。两次 request-changes 均按原结果保存。

自身原结构模板的 26 份文件共 459,033B，亦按封套标记和声明长度逐份独立重算，与完整原 task、sealed input 和实际 stdin 核同，原结果 SHA256 及 approve 回复保持，记录 `self-review-originals.json`。其 approve 只覆盖当时给定文本，明确未认证子包、安装、私有证据、旅程或 CI；本独立评审不倒填或扩大它的范围。

## Findings 和未覆盖范围

**最终本地已检范围无实证 finding，需求／可维护性分别 approve，开放 0／0。** r4 资料终核后复查实际产品仍为原独立重算的 638 文件、测试身份相同；没有用文档更新倒认证历史运行。含本报告的 19 份 Markdown 本地链接检查为 **373 条／零错误**，外网未验证；全范围 tracked diff 空白检查通过。

未运行付费模型、训练、GPU、profiler、业务仓库命令、数值／梯度／分布式／恢复／长程质量或性能验证；没有提交、推送、发平台消息或改实现。固定资源送达证明字节覆盖，不证明模型理解。两原创任务不是实际训练工作负载，不能据其验收真实 kernel、收益、自动全图执行、跨轮预算、循环或采用。Q2.3、Q4、Q5、真实 B3 与完整 Forge 等沿原开放边界。
