# Q3.1 流程图谱独立审查

日期：2026-11-15。评审者：fresh-context 独立代理 `training_flow_maps_audit`。依据仓库 `AGENTS.md`、[具体计划](../plans/2026-11-15-training-flow-maps.md)、[原要求与 Q 总计划](../plans/2026-11-15-domain-review-optimization-quality.md)，使用 `maintainable-project-delivery` 的 independent-review brief，以及 `ergora-codebase-quality` 的 repository-style／module-design／test-seams references。先读原要求和实际差异，再读作者交付叙述；产品、业务源码和原证据只读，唯一写入为本报告。

|审查轴|本地结论|
|---|---|
|需求符合性|**approve**。本片独立只读图谱配方及实际使用证据满足 Q3.1 的本地验收；开放实质问题 0。|
|可维护性|**approve**。定义、注册、冻结、授权和运行继续由原 owner 持有；开放实质问题 0。|

本结论不表示精确发布或 CI 已完成。Q3.1 仍须普通提交／推送、核完整远端身份并取得该候选自己的适用 CI；Q2 的 CI 不是 Q3 的 CI。

## 精确范围

基线及审查时 HEAD 为 `0b5b5f1ff7a3463fcb10cf5a05e5f7c7bcae7c62`，分支 `refactor/architecture-foundations`。冻结材料为本地 `training-flow-maps/review-scope-r1` 的 `scope.json`、`tracked.diff` 和 `files/`，共 **17 个完整 tracked／untracked 文件**。独立重算全部长度／SHA256 均相同，初读时这 17 文件也与工作树逐字相同。

- `scope.json` SHA256：`a1e1eea676a9d56916aa5780a4cd805c21f470eb3232a07039b1392a270436e7`。
- `tracked.diff` SHA256：`37915f354fe4d2c90e8b198012d3a6c583d5b3b203d95ec575b5f9af700473b0`。

|文件组|实际审查文件|
|---|---|
|新 Agent／完整 Skill|`src/ergora/data/presets/agents/ergora-training-flow-analyst/agent.json`、`instructions.md`、`skills/ergora-training-flow-map/SKILL.md`|
|新独立子模板|`src/ergora/data/presets/workflows/ergora-training-flow-map/workflow.json`、`instructions.md`|
|既有注册与测试|`src/ergora/data/presets/presets.json`、`tests/test_presets.py`|
|入口与操作文档|`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WORKFLOW_DEFINITIONS.md`|
|本片及总计划|`docs/plans/2026-11-15-training-flow-maps.md`、`docs/plans/2026-11-15-domain-review-optimization-quality.md`、`docs/delivery/2026-11-15-training-flow-maps.md`|
|前片状态记账|`docs/delivery/2026-11-15-local-review-packets-review.md`、`docs/delivery/2026-11-15-local-review-packets.md`、`docs/delivery/2026-11-15-training-domain-reviews.md`|

另读原 `workflow_definitions` 的安装／编译／冻结／完整输入路径、`agent_definitions`／`definition_bundles`、`agent_runs` 的准入与后端选择、既有性能分析 Skill、包配置和相应测试。没有新生产函数或模块需要建立另一复用层。

审查期间，`docs/PLAN.md`、本片交付和 Q 总计划追加了自身结构审查完成的状态；已与冻结版本逐行比对，只增加实际结果／在途状态，没有改产品或本片合同。该原调用亦独立核验如下。同期 Q2 独立报告的变化属于 Q2 记账，未纳入这 17 文件或本片产品批准；Q1／Q2 的既有验收也没有在此重新认证。

## 需求与实现核对

|要求|观察与判断|
|---|---|
|算法图、执行依赖图和生命周期分开|完整原创 Skill 明确要求两个独立图、节点／边源码锚点、状态生命周期、必要依赖与可证伪假设。真实回复确实分别产出这些材料，没有用 Agent DAG 替代目标训练图。|
|按真实源码理解，缺失边界明确|私下对照 13 份原捕获文件及完整回复，核入口与工厂、配置／阶段／贡献、资源构造与交接／清理、诊断边界等路径和函数锚点。源码观察、配置合同、条件推断与未知有明确标签；缺失 trainer／model／loader／框架／恢复实现及无 runtime 证据均保留。没有把完整读取所给文件升级成完整训练实现覆盖。|
|冗余分析可反驳，必要依赖保留|回复给出一项有条件假设，注明实际调用与启用关系尚未绑定，列明成立条件、反例、替代解释、最小补证据和反证测量；同时保留必要的语义依赖。所述锚点与原文件相符，没有据外观直接批准删除依赖或宣称训练瓶颈。|
|原参照、语义和测量／采用边界|Skill 与回复要求保存原始参照，固定模型／数据／目标／更新时钟／质量边界，由原 runner 再准入有界验证。源码图、诊断扰动和未插桩系统比较区分；没有训练成功、收益、自动优化或采用批准声明。|
|独立只读配方与后续总路径分开|一位 Agent、一份自包含 Skill、独立 `root/map` 及 all-join 注册于原 catalog，现为 31 preset。根与叶无 write／shell／network；三份父／叶资源完整进入实际输入，祖先来源为 `root` 和 `root/map`。原编译器仍核父／项目权限与容量上限，原运行接口仍可显式选择后端。kernel 专家留在后续总路径，本叶不自动调用其他节点。|
|旧版本与原权威保持|相对基线产品只新增五个定义资源文件，仅 catalog 改一项，无删除或其他运行代码变化。旧 v1／v2 等所有既有产品文件保持。未增加 schema、图数据库、trainer、指标权威、调度器或候选／批准／恢复路径。|

## 原始证据与独立检查

**安装身份。** 独立重算 wheel SHA256 为 `01dc68055211060a3193efb35480178087f549d33787ecfe042c66e38d4d3e28`。逐文件核对 **633 个产品文件**：源、wheel 与非 editable 安装逐字相同，wheel 文件集合也一致；与固定基线的差异确为五新增／零删除／catalog 一变化。`pyvenv.cfg` 的 `include-system-site-packages = false`。原 Q2 的 **628 个安装文件**仍匹配其 `package-r2.json`，未被新环境替代。

**真实只读使用。** 原 run `b86f90904e3c4a1b8db1d702a74ccff8`，218.156 秒，原 CLI 终态 `succeeded`／returncode 0。独立对照原捕获清单、当前源索引与十三原件的长度／SHA256：**13 文件／93,748B** 一致；完整 task、十三文件和三份资源均在实际 stdin，stdin 与冻结 prompt 逐字相同。安装版 `inspect_input` 重算 input digest 为 `22c05f2afb3071d3df703260b1a301437cf9b40a2b5c89d4327159248d3dd6b8`；原结果、运行目录结果与 CLI 结果身份一致，SHA256 为 `a3ab076dec7ee92be6455c39f443bed00c0604c3ae40cb7a6c851e67464cd971`，保存的回复与原结果相同。实际准入为 Codex／`text-only`，`formal_execution_authorized=false`。私有源和回复不随本报告公开。

**自身结构模板。** 原 run `a70641055ece4a6a9c1317261d227c95`，39.202 秒，`succeeded`／approve。独立核对 21 文件／424,593B 的完整清单与输入，完整 task／祖先资源进入实际 stdin，冻结 prompt＝stdin；input digest `f257946519a58eeeba9010904f3fcb03809290e0ad403230669e6a837e56153a`、原结果 SHA256 `70fbd0a9e8f5990af03da343acb62cd23ddf10dfa37dae88789f339d8be2ab4e` 均重算相同，CLI 与保存结果一致。原回复只批准所给文本结构，没有认证安装／私有运行／CI；这次原调用不代替本独立审查。

**原回归。** 直接读原 stdout、零字节 stderr 与 JUnit：preset／架构／原全 catalog 页面用例 **54 passed／76.78 秒，零失败／跳过**；Skill 原 `quick_validate` 输出成功。安装版 `reference.verify()` 本次另行执行，**PASS／283 文件**，`runtime_started=false`。

**本次有界安装检查。** 使用既有独立安装解释器，未安装依赖、调用模型或运行大套件：

```bash
.ergora/checks/training-flow-maps/venv-r1/bin/python -I -B -m pytest -q -p no:cacheprovider \
  tests/test_presets.py::test_flow_map_freezes_complete_material_without_changing_training_versions \
  tests/test_workflow_definitions.py::test_descendants_cannot_broaden_any_permission \
  tests/test_workflow_definitions.py::test_every_ancestor_and_the_project_bound_expansion_and_static_prompt_bytes \
  tests/test_workflow_definitions.py::test_prepared_input_retains_every_ancestor_skill_tree_and_is_independent_of_source_state \
  'tests/test_workflow_definitions.py::test_invalid_input_never_publishes_a_partial_bundle[capacity]'
```

结果 **8 passed／1.33 秒**。覆盖新叶共装／旧版本、活动库删除后的冻结输入、四类子权限扩大、祖先／资料预算、完整输入独立性和容量不足拒绝；没有测试提示措辞或模型观点。原 owner 已有这些不变量，无需新验证框架。另核冻结 13 份 Markdown 的 **362 个本地链接目标**均存在；此计数不表示所有旧 fragment 或远端 URL 均已验证。所审 tracked 差异的 `git diff --check` 通过。

## Findings 与剩余验收

在上述精确范围内，**没有实质正确性、范围、维护性或测试价值 finding**，无须代码修正。新增资源按既有定义协议归属明确；完整继承、只读授权、不可变版本和可替换后端的义务由原模块隐藏。新增测试保护可达的冻结／版本静默回归，不重复实现 Skill 文案。

剩余工作是本片的精确提交／普通推送、完整远端身份和自己的适用 CI，再由原 reviewer 补核。当前 Q2 `43621692177` 属于前片；不能作为 Q3 成功证据。本次没有平台写入、提交或推送。

实际业务仓库前后 HEAD／完整 status 原始字节相同；这只证明这两项观察，没有认证全部 WIP 内容。未运行训练、业务配置 parser、profiler 或 GPU 工作，未读取数据／权重，未验证数值／分布式／恢复／收敛／质量／性能；源包缺失的外部实现与实际 runtime 仍未知。这些是本片明确限制，不要求用不存在的训练结果补造 Q3.1 通过。

Q3.2 成对测量合同、Q3.3 含 kernel 专家评估的新总路径、Q2.3 报告、Q4 多轮与自动循环，以及真实 B3／完整 Forge 的原条件均保持开放。
