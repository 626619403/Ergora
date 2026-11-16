# 逐 Agent 推理设置与原并行执行独立审查

2026-11-16。Reviewer：`agent_reasoning_options_review`，fresh context。先读原始用户要求、[本片合同](../plans/2026-11-16-agent-reasoning-and-parallelism.md)、完整差异和生产调用，再读作者交付。遵循根／src／tests AGENTS、[组件变更协议](../architecture/component-change-protocols.md)、maintainable-project-delivery 独审规则和 ergora-codebase-quality 的源码／模块／测试接缝准则。只读源码和证据；唯一写入为本报告。

## 结论

- **需求符合性：approve，限定本片冻结源码合同。** Codex／Claude 的逐 Agent 可选请求值贯通原 schema、定义、叶子覆盖、正式冻结和后端命令；缺省兼容、Codex 显式值优先级、restricted 模式及原并行 owner 保持。一般 Repeat、任意混合图不在本片。
- **可维护性：approve。** 配置留在组件目录，命令投影留在各后端；原 ABC／工厂、完整 binding 读写和页面 schema 消费者足够，没有新增上层具体后端分派、转换层、状态表或 scheduler。
- **开放 finding：0。** 下述一项证据记账 finding 已由作者更正并复核关闭。没有发现其余需要修正的可达源码问题。本结论不代替新安装、Ergora 自身模板审查或本候选自己的发布 CI。

## 候选与检查范围

准确基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`；隔离树 `.ergora/worktrees/agent-reasoning-options`，HEAD `0dcbc207e33ad4ed1a8674e2bed43f65c4ecda89`，审查前后 clean。

已核 `.ergora/checks/agent-reasoning-options/fixed-r1/`：完整 `source.patch` SHA-256 `5ad344dcd73e6158bbac7ed65f562d84e59daf3d2365e87997343a1ca3500ae2`，与准确 Git baseline→HEAD 的 `--full-index --binary` 输出逐字相同；`source-inputs.json` SHA-256 `6266c66184fc138e0627b0fd8d882316bf3b33436c7dc15dd1ad6c0484b57f14`，2071 个输入文件内容 SHA 全部吻合；`changed-files.json` 的10文件长度／SHA吻合。

完整审查的10个变更文件：`docs/AGENT_BACKENDS.md`、`docs/WORKFLOW_DEFINITIONS.md`、`src/ergora/agent_backends.py`、`src/ergora/data/components.json`、`src/ergora/task_envelopes.py`、`tests/test_agent_definitions.py`、`tests/test_agents.py`、`tests/test_components.py`、`tests/test_composition_tasks.py`、`tests/test_parallel_reviews.py`。

邻接生产路径核至 `components`／`bindings`→`agent_definitions`／`workflow_definitions`→`tasks._member`→`task_envelopes.unwrap`→`reference_executor`／`stage_driver`／`agent_runs`→`agents.invoke`／后端工厂；页面核 `binding-fields.js` 的原 `tools.js` 与 `task-composition.js` 两个消费者。原 `reference_workflows` 的 review／work-unit 调度仍持有依赖、所有祖先并发配额、取消与预算。

## Finding 与处置

**F1，P2，已关闭：后继并行运行被误记为补齐前次8个 skip。** 位置：[作者交付](2026-11-16-agent-reasoning-options.md) 首版验证段（当前第17行），以及本片计划 A3。首版称后继 SDK 环境“补跑原8个缺依赖节点”，会错误扩大验收覆盖。

原 `source-check-r1/junit.xml` 实际为53节点，45通过、8跳过；13个 `test_parallel_reviews` 节点全部已通过，跳过的是 ForgeKernel／mini-swe 外部可选依赖。`source-sdk-parallel-r1/junit.xml` 的8个并行节点均为重复验证，不是上述8个 skip。最小修正只需据原 JUnit 核正分类、重复覆盖和未验范围，无需为本片重跑无关 SDK。

作者已在交付第15／17行与计划 A3 作出上述更正，保留原运行且不计重复节点为新增覆盖。审查者重读更正文档及两份原 JUnit 后关闭 F1；源码候选不变。

## 行为、测试价值与证据界限

Codex 在 `agent_backends.py:197` 于原 TOML 装载／restricted 过滤之后写入显式 `model_reasoning_effort`；Claude 在同文件第274行添加原生 `--effort`。字段缺省时均不添加新请求。组件 schema 拒绝交叉字段及其他后端的未实现字段。`task_envelopes.py:152` 只扩展历史结构 reader 的允许字段及字符串检查，没有改用可变 catalog；实时准入仍归后端，旧无字段记录无需重写。

定义编译保留完整 `backend_request`；正式逐叶选择、工作／准备／审查成员和实际 invocation 都传完整 binding，未见只保留 tool／model 而丢新字段的路径。原冻结、权限逐级收窄、执行准入、预算及唯一调度 owner 未被本片改动。原并行测试保留真实 async 等待／释放、峰值、窄子树、取消、作者排除与完整 admission 转发；异后端用例扩展同一接缝，不新增测试文件或 CI job。

作者记录的 `source-check-r1` 为 **45 passed／8 skipped，53.95秒**；后继为 **8 passed／5 deselected，25.26秒**，是重复并行验证。已核原 argv、stdout、JUnit；首次运行保存 patch 的 src／tests 内容与冻结候选相同。CLI 进程用例使用替身，能证明参数传递及结果正规化，不能证明真实模型应用强度。新增缺省／不同显式值、native／text-only、配置优先级、定义修订和正式任务冻结均沿现有有状态接缝覆盖，没有发现应因重复而删除的新增独立测试设施。

审查者未重跑 pytest、安装或模型。额外只读内存检查覆盖两后端全部公开可选值和全部既有 invocation modes，共49组合，确认新参数投影及原 restricted tools／sandbox；清空内存 catalog 后，旧绑定与两个新字段的历史结构检查仍通过。该检查不创建协议、State或进程，不认证 CLI／服务支持。

已读官方参数原页和 `browser-r1/RESULT.md`。项目工具绑定页面的 Codex high／Claude medium／另一角色 low 保存重开与读回由独立页面证据报告通过；本次源码审查未亲自重跑浏览器，正式组合 selector 仍未验。Claude 的组织 cap、环境／原生优先级和 `ultracode` 的原生特殊语义均不能从传入请求推导实际计算强度；本结论只认证明确 binding 到原生请求的投影。真实多提供方同时执行、模型支持／成本／质量，以及新 wheel 和远端 CI 均保持各自未验状态。
