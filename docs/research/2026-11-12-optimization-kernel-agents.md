# Kernel 专家与优化流程候选

检索日期：2026-11-12。只采用项目官方仓库、厂商文档及作者论文；下列 SHA 均经官方 Git Ref 只读核对。已阅读实现入口与评测契约，未安装、调用模型、运行 GPU 或复现成绩。研究原件保存在 `.ergora/checks/specialist-template-refresh/research/kernel/`。没有跨项目统一实验，因此不作通用 SOTA 排序。

建议先吸收 **NVIDIA KDA 的任务／证据合同**，再沿既有 **ForgeKernel 原生 campaign** 补齐可执行子模板。Ascend 任务采用具名的 **华为 MindSpore AKG-AGENT**；Triton 生成可选 **PyTorch KernelAgent**；若有 AMD 资源，**GEAK v4** 是完整嵌套流程的优先候选。**Sakana robust-kbench** 优先作为独立评测组件。

## 具名候选、版本与调用面

|候选／固定快照|实际交付形态与流程|硬件、语言及版本边界|可调用入口|
|---|---|---|---|
|[NVlabs KDA][kda] `acdd79343c5e9d0c7cb96289f26fd3f1051ce785`|早期 agent-centric 工作流：契约→调研→草稿→计划→实现→验证／测量→保留、修订或拒绝。提供 prompts 和技能资料；实际执行者是外部 coding agent，未交付统一自主调度器。|流程可用于不同目标；community wishlist 当前仅 B200/B300。CUDA／CuTe 资料与 profiler 参数须随任务配置，不能将附带 B200 NCU 技能当通用硬件参数。|把 `prompts/basic-flow.md` 与 `docs/agent-flow.md` 交给 coding agent；未核到独立 KDA CLI／SDK／MCP。|
|[OpenBMB ForgeKernel][forge] `b2c8ae8510e02c28576808910a6b8827721ab7dc`，包 `0.1.0`|有原生双层循环：arch/teacher 分解架构里程碑，coding/student 逐决策实现；同一 GPU job 判断、计时、profile；停滞重规划；跨代提升 reference 并积累 probe 认证知识。|公开 quickstart 支持 Hopper `sm90`／Blackwell `sm100`，语言为 CuTe DSL、CUDA C++。论文环境含 H100 CUDA12.8、B200 CUDA13.1／CuTe4.4.2，并有其他镜像；不是唯一兼容组合。CLI 主机 Linux/macOS、Python≥3.11。|`forge new --dry-run`、`forge new`、`forge run`、`forge status`、`forge export`；可恢复 run。内部 Python 模块存在；稳定外部 SDK／原生 MCP 未核实。|
|[MindSpore AKG-AGENT][akg]，推荐分支 `br_agents`：`64b84b59541c134279f5d2ee0a5f35de0ec40022`，`0.2.0.dev1`|真实多 agent 框架及算子场景：KernelGen、UCB AdaptiveSearch、Evolve、AutoResearch；LangGraph 编排、worker 验证、trace／session。另有 `akg-op` 交互 agent 与 hook 约束的 `workspace_autoresearch`。|README 保守支持表为 Atlas A2 Triton、NVIDIA Triton、CPU C++；参数枚举另含 AscendC、TileLang、PyPTO、950 等，不能把枚举当已验兼容矩阵。依赖文件为 torch／torch_npu≥2.7、triton-ascend≥3.2；未给统一 CANN 锁定版本。|`scripts/run_autoresearch.py --ref … --kernel …`；Python `LangGraphTask(..., workflow="autoresearch").run()`；OpenCode／Claude 工作区入口。`akg_cli` 自2026-04-28废弃；`call_autoresearch_workflow` 是框架 tool 名，不能据此称 MCP。|
|[PyTorch KernelFalcon／KernelAgent][meta] `e0647170da36ef9b059ac0bd3d60103aa4ed378b`|同一仓库中的生成／优化流程：router→可融合子图→并行生成→重组验证；另有 NCU→瓶颈诊断→优化→验证→计时／回退的 beam search。|Triton 生成支持 NVIDIA CUDA、Intel XPU；NCU 优化的公开性能证据为 H100。Triton 需另装，README 未提供统一 CUDA／Triton 锁。|Python `TritonKernelAgent.generate_kernel()` 可作候选生成专家；`python -m Fuser.pipeline --verify` 可承接完整流程；优化示例 `run_opt_manager.py`。未核到官方 MCP。|
|[AMD GEAK v4][geak] `ec97e49ca886f8d02f8415192fdaac45d1005d2a`|确定性 JS 管预算、并行、验证与停止；Director→TechLead→algorithm／memory／compute／host_runtime 等专家。整模 `e2e_workflow` 原样递归调用 `kernel_workflow`，是可引用子模板的直接实例。|AMD MI/CDNA `gfx942/gfx950` 等、ROCm6+，Triton／HIP／FlyDSL／TileLang；另有具名 Radeon 支持。工具链先由用户环境准备。原生 Claude Workflow 要求 CLI≥2.1.177；Codex runtime 要求 Node20+、上游指定 Codex0.146.1。|单 kernel：`run_workflow.mjs …kernel_workflow.js --agent codex`；整模：[versioned JSON handoff→result 的 Python 接口][geak-interface]。Codex 自然语言启动尚未接线；这是进程／Workflow 接口，未核到 MCP。|
|[Sakana robust-kbench][sakana] `078f5bab29934a822268d59a4e707d449abf9b4e`；[论文 v1][sakana-paper]|论文包含翻译→LLM verifier→进化优化研究流程；公开仓库明确交付 benchmark、数据与 evaluator，不能把它称作已开箱可用的完整 AI-CUDA-Engineer agent。|CUDA C++，官方 quickstart Python3.11／PyTorch cu124，论文实验 H100／CUDA12.4。|CLI `run_filter.py`／`run_kernel.py`；Python `ParallelKernelExecutor` 的 compile／test／evaluate／profile，可独立接可信 runner。未核到公开完整搜索引擎／MCP。|

AKG 的 `setup.py` 明示 Huawei Technologies 版权，足以确认华为来源；用户未给项目名，因此只能认定为**已核实的华为候选**，不能断言它就是用户唯一所指。官方 `master` 为 `d4f8b4b42c68966d7cb7c834af3344b850c21bcb`，与 `br_agents` 不同；本文以安装指南指定的后者为接入研究快照。Ascend/agent-skills 是技能集合，Ascend/AgentSDK 是 Agentic RL／应用生态，均不能直接替代此 kernel agent。[akg-source]

## 正确性、收益证据与复用边界

|候选|correctness／benchmark／judge 的实际边界|训练反向／JVP|许可与可复用部分|
|---|---|---|---|
|KDA|正确性与计时命令由任务提供；工作区记录 `candidates.jsonl`、benchmark、profile 和晋升原因。README 引用的 MLSys contest 成绩属于下游特定任务，不等于通用 evaluator。|通用任务合同可要求导数，但上游最小流程未自动检查 backward／JVP。|文档、prompts 等 CC-BY4.0；一手源代码 Apache2.0。KernelWiki／NCU 子模块另循其许可，固定分发还排除了受额外条款限制的材料。适合复用方法与带归属的资源。|
|ForgeKernel|teacher 生成 PyTorch judge、每 shape 至少三组输入，与 reference 校准后冻结容差；有最终重复确认。finish correctness monitor 仅记录、不改原 verdict，仍需外部独立门禁。[forge-judge] 论文29配置／27算子汇总1.10×；7个已发布系统 kernel 子集的+39.4%是另一口径。[forge-paper]|已发布 attention、GDN、conv 等 backward kernel；不等于训练图自动注册梯度，也未核到 JVP 自动验收。|Apache2.0；可复用原生 harness、里程碑格式与硬件 KB。第三方 evaluator 有 NOTICE，CuTe DSL 自有许可。|
|AKG-AGENT|AutoResearch preflight 检查 reference／seed；修改后 quick check→KernelVerifier→KEEP 或回滚，持久化预算和恢复态。[akg-ar] 2026-06报告 PyPTO 56/100、TileLang-Ascend49/100，分别为10次搜索／pass@4的**生成成功率**，不代表训练加速。[akg-bench]|默认 Model 输出比较；未核到自动覆盖 backward／JVP，须显式补任务和独立验证。|Apache2.0；优先复用完整 workflow、Verifier／worker 适配与 trace。README 的实验定位不代表生产服务承诺。|
|KernelAgent|运行生成的测试，组合可用 `--verify`；测试本身由 agent 参与生成。官方 H100、100个 KernelBench L1 报1.56×默认 torch.compile、65/100更快；此前250任务 correctness 是另一覆盖口径。[meta-blog]|主要重建 forward；上述成绩不能证明 backward／JVP 或完整训练正确。|Apache2.0；复用 Python 生成器或 Fuser 原流程。生成测试与“PASS”不替代项目 golden reference。|
|GEAK|独立 verify agent 在干净 workspace 重测每个 patch，Director 对真原基线复核；整模还有 warm-server A/B、实际命中证明与输出 parity。README 单核3.68×仅为指定12个 MI300X HIP kernel（排除 mla_decode，FAIL计1×），不能外推到整模／其他卡。[geak]|定位推理与 kernel 性能；未核到通用 backward／JVP 门禁。|Apache2.0；复用完整 JS 流程、roles、知识与外部接口；保留 AMD 特定资源识别、测量与 overlay 机制。|
|robust-kbench|多初始化、多输入、输出幅度／变化过滤；支持 PyTorch eager／compile baseline、三种计时及 profiling。论文 H100 指定任务 forward 相对 eager 最高2.5×，不能与上述 compile／专家库基线直接比较。|明确含多种 forward／backward 测例；没有普遍 JVP 保证。|Apache2.0；优先复用评测策略与适配后的真实测例，仍需防止新型 reward hacking。|

上述数值全部为作者报告，本文未复现。特别是 ForgeKernel 论文确有 Ascend910C／CANN-Bench 实验，但公开 quickstart 与语言入口仍以 NVIDIA CUDA／CuTe 为准；不能从排行榜声明推导公开主线已有可部署 Ascend 后端。AKG 新分支枚举与 README 支持表也存在口径差异，具体 DSL 必须单独准入。

## Ergora 的最小接入与顺序

1. **先固化统一任务合同和单体专家。** 保留 `ergora-kernel-designer` 的只读提案能力；补 KDA 参考资源与固定 workload、shape／stride／dtype、硬件和编译版本、独立 reference、导数消费者、当前 compiled／library baseline、预算及晋升标准。Profiler 用于解释真实关键路径；孤立 kernel 收益不直接换算训练吞吐。
2. **先让既有 Forge campaign 成为真实消费者。** 当前 `src/ergora/kernel.py`／`data/drivers/forge.py` 已固定 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`，只支持 Linux＋local delivery；其内部 Python API 绑定不能静默升级为上表主线。方向子模板调用原 prepare／run／status，保存 native ID、冻结配置、候选源码与摘要；完整 teacher/student 循环留在 Forge。新版本另片验证，原生完成仍只产生候选。
3. **按硬件接第二种原生流程。** Ascend 优先 AKG：正确 seed 后用 AutoResearch 深挖，需铺广度时用 Evolve／AdaptiveSearch；NVIDIA Triton 初稿可先接 KernelAgent SDK。AMD 有资源时优先 GEAK 原生双层流程，保留其内部专家。整模只通过其外部 JSON 契约；kernel 使用原生 JS runtime，避免另造一套内层调度。
4. **把独立验收留在可信 runner／原所有者。** 原生 judge 后再查边界输入、随机性、数值容差、所需 backward／JVP、内存与 stream／compile／CUDA Graph 行为；预热后配对重复测完整 wrapper，再验真实训练／服务工作负载。robust-kbench 可补案例与测量组件。原生搜索不能修改这些外部门禁或替 owner 批准。
5. **先补运行能力再发布子模板。** 需要带能力声明的 native-process 子流程消费者、产物合同、权限／资源上限和 unknown 恢复映射；完整继承读取父级资料、Skill 与上下文，沿父级限制使用可信容器。GEAK exit0也可为 `no_gain`／`timeout`，AKG 示例脚本失败会打印 FAILED，不能只凭进程0判成功。适配器应核 native 结构状态及证据，超时先查原 run，禁止盲目重提。尚未实现这些消费者时，页面只能标记提案／静态引用，不能称已嵌套执行。

本次仅完成方向研究。Megatron Bridge skills 索引用于方向校准，未导入；没有变更 preset、后端、运行权限或产品代码。

[kda]: https://github.com/NVlabs/kda/tree/acdd79343c5e9d0c7cb96289f26fd3f1051ce785
[forge]: https://github.com/OpenBMB/ForgeKernel/tree/b2c8ae8510e02c28576808910a6b8827721ab7dc
[forge-judge]: https://github.com/OpenBMB/ForgeKernel/blob/b2c8ae8510e02c28576808910a6b8827721ab7dc/docs/design/v1-launch.md#4-judging-correctness
[forge-paper]: https://arxiv.org/html/2611.04998v1
[akg]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/README_CN.md
[akg-source]: https://github.com/mindspore-ai/akg/blob/d4f8b4b42c68966d7cb7c834af3344b850c21bcb/akg_agents/setup.py
[akg-ar]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/docs/v2/CN/AutoResearch.md
[akg-bench]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/docs/v2/CN/DSLBenchmarkResults202606.md
[meta]: https://github.com/meta-pytorch/KernelAgent/tree/e0647170da36ef9b059ac0bd3d60103aa4ed378b
[meta-blog]: https://pytorch.org/blog/kernelagent-hardware-guided-gpu-kernel-optimization-via-multi-agent-orchestration/
[geak]: https://github.com/AMD-AGI/GEAK/tree/ec97e49ca886f8d02f8415192fdaac45d1005d2a
[geak-interface]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/run_e2e.md
[sakana]: https://github.com/SakanaAI/robust-kbench/tree/078f5bab29934a822268d59a4e707d449abf9b4e
[sakana-paper]: https://arxiv.org/html/2509.14279v1
