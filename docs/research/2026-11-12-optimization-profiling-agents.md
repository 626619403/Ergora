# R7：性能诊断、Trace 与可信测量的 Agent／流程调研

检索和源码核对日期：2026-11-12。承接[专家模板重整计划](../plans/2026-11-12-specialist-template-refresh.md) R7，按 [Megatron Bridge Agent Skills Reference][index] 的 Nsight Systems Analysis、analysis pitfalls、SQLite recipes、Memory Snapshot Analysis 继续细化。技术方向与专家职责的关系见[分类说明](2026-11-12-optimization-taxonomy.md)。本报告只给诊断、采集和评价的纵向决策；跨领域搜索、实验协调与恢复所有权由后续 X3／R8 处理，不要求导入整个 NeMo。

本轮只读公开文档和源码；未安装依赖、运行模型／GPU、采集 trace、提升 profiling 权限、读取凭据或验证任何性能收益。固定文件和网页原件、HTTP／错误回执、时间及 SHA256 保存在本研究私有验收目录。网页搜索连接器不可用，直接公开 GET 可用；发现用的搜索结果不充当能力证明。以下明确区分官方文档、固定实现、作者报告和本轮实际执行。

## 结论与采用顺序

1. **采用固定 Bridge 的分析合同，适配其离线脚本。** Nsight Skill 已给出稳态窗口→rank 调查→区间并集→依赖归因→有界机会的完整分析流程；snapshot Skill 有可调用的解析／对比／重放脚本。它们是操作资料和工具组成的流程，不是带模型、调度器及恢复机制的自主 Agent。[Nsight Skill][bridge-nsys]；[snapshot Skill][bridge-memory]。
2. **官方具名候选确实存在，但形态是 BYO Skill＋原生 CLI。** 当前 Nsight Systems 文档为 v2026.6，发行说明为 **2026.6.1**；其 AI-Assisted Analysis 仍标 Preview，`nsight-systems` Skill 指导已有 Agent 使用工具。2026.6 已把 agent tools 合入 CLI／安装的 Python 环境，增加 `query`、`docs`、`survey` 和 JSONL recipe 输出。[发行说明][nsys-release]；[AI-Assisted Analysis][nsys-ai]。
3. **本轮没有核到可直接导入、成熟的官方独立 Nsight 自主诊断 Agent 或官方 MCP 服务。** 官方 Skill、`nsys analyze` 的确定性 expert-system rules，以及文档中的远程采集 agent 不能互相替代。确有第三方 `liubingjun1207/nsight-agent` v1.2.0：它是本地 STDIO MCP 包装和配套 Skill，非 NVIDIA 产品；有固定实现及作者真实使用记录，适合借鉴受限接口，尚不足以承担跨 rank 自动根因和优化采用决策。[官方 AI 说明][nsys-ai]；[第三方固定 README][mcp-readme]／[server][mcp-server]。
4. **将“采集”“离线分析”“独立性能评价”作为三个权限和证据合同。** 已有报告分析可以无 GPU；采集需要相应 workload、硬件和可用权限；吞吐晋升必须再做同条件、无 profiler 的重复测量。SQL 只读也可能写缓存／自动安装依赖，不能仅凭工具的 read-only 标记授权。[`nsys query`][nsys-query]；[官方验证流程][nsys-ai]。
5. **PyTorch／CUPTI＋HTA 是工具链候选，不改名为 Agent。** HTA 可做多 rank 分解、overlap、idle、trace diff，并有单 rank critical-path API；它不自动证明跨主机时钟准确、全部通信后端已分类或瓶颈干预有效。[HTA 固定 README][hta-readme]／[critical-path API][hta-api]／[时间对齐实现][hta-trace]。

## 按参考目录拆分的实际职责

|参考项|独立决策与消费者|本轮边界|
|---|---|---|
|Nsight Systems Analysis|窗口／rank／stage 清点、绝对时间预算、launch starvation、通信／copy 依赖、来源与收益上限|交给 R3／R4／R5／R6／R1 选择干预；不直接启用所有优化开关|
|Analysis pitfalls|检查重叠、同步、图、缺失事件、源代码归因、跨主机和 MFU 解释|作为诊断执行与测量审查共同引用的固定资源，不另造一个“陷阱 Agent”|
|SQLite recipes|探测 schema／诊断／metadata，枚举 kernel、backend、runtime、copy、event、metric|查询是起点；必须核单位、连接基数、作用域和窗口，不能把 kernel duration sum 当 step|
|Memory Snapshot Analysis|allocator 现场、时间重放、两次运行差异、来源归组、OOM 现场|交 R5 做容量和状态决策；不能覆盖所有设备显存／CPU 内存|
|关联 PyTorch／CUPTI／跨 rank trace|框架算子到 CUDA 关联、同步边、rank coverage 和时钟／capture 完整性|采集配置、离线推断和硬件计数器分别验收|

对应一手资料分别为 [Nsight Skill][bridge-nsys]、[pitfalls][bridge-pitfalls]、[SQL recipes][bridge-sql]、[snapshot Skill][bridge-memory]。同一诊断专家可处理多个技术方向；执行者与独立测量审查者也可引用同一份资料。

## 版本、许可、接口与采用判断

|候选与实现形态|本轮核定身份／许可|接口、资源和判断|
|---|---|---|
|Megatron Bridge 诊断／snapshot Skills|固定 `55694838ce73cd23b00ff95bd00512aefb963ce0`；package 为 0.8.0，根 Apache-2.0，保留各文件 notice|Nsight Skill＋SQL；snapshot Python CLI／JSON。离线脚本可无 GPU；训练侧要求匹配 Bridge／Core／PyTorch。**采用资源，适配工具流程**。[版本][bridge-package]／[许可][bridge-license]|
|NVIDIA Nsight Systems＋`nsight-systems` BYO Skill|2026-11-12 读取 v2026.6／2026.6.1；产品许可证为 NVIDIA Software License Agreement，含第三方独立许可；AI 分支 Preview|`nsys stats/analyze/recipe/export`；新 `docs/query/survey`。已有报告离线分析与 workload 采集分开。**条件适配原生 CLI**，不将安装包／Skill 默认为 Apache 可再分发。[发行][nsys-release]／[安装][nsys-install]／[许可][nsys-license]|
|第三方 Nsight Agent：MCP＋Skill|固定 `e69916fa541da7fef7695fe592c5a9149099d02b`，pyproject **1.2.0**；Python ≥3.11、`mcp>=1.27,<2`；项目 Apache-2.0，NVIDIA 样例另有许可|本地 STDIO、20 tools、18 个固定统计 report＋6 个诊断 rules；另有受限本地 capture 和既有 Compute report 导入。**借鉴接口，必要时只读适配**；不默认替代官方新 CLI。[配置][mcp-pyproject]／[许可][mcp-license]／[接口][mcp-server]|
|PyTorch profiler／memory／benchmark|2.15 文档及固定源码 `31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457`；BSD 三条款及第三方 notices|`torch.profiler.profile`、Chrome trace、execution trace、allocator snapshot、`torch.utils.benchmark.Timer`。**采用已有 workload 的原生接口**，不把新 PyTorch 能力算作旧 Bridge 已接通。[profiler][torch-profiler]／[memory][torch-memory]／[许可][torch-license]|
|Meta Holistic Trace Analysis：分析库|固定 `eb0b6d6ee288641abe06174216db920909a196b3`；version **0.6.1**，MIT；README Python ≥3.10、Linux／macOS|`TraceAnalysis(trace_dir=...)`／DataFrame／trace diff／critical-path graph；分析 PyTorch／Kineto traces。**条件适配离线分析**，不是自主 Agent 或分布式调度器。[版本][hta-version]／[README][hta-readme]／[许可][hta-license]|
|NVIDIA CUPTI：底层采集库|本轮官方当日文档；现代初始化和多 subscriber 路径要求 CUDA 13.3＋driver r610；与旧路径分开|C Activity／Callback／Profiling APIs，记录 CUDA API、kernel、memory、correlation。**借用成熟上层工具，暂缓自建 CUPTI collector**；不把新 API 支持推断为具体上层组合已兼容。[CUPTI][cupti]|

Nsight 许可对复制／分发／向他人提供功能有限制，条款 2.11 还要求直接对比非 NVIDIA 平台并向第三方披露相关 benchmark／performance data 时事先取得书面许可；不能因为可公开下载就把工具或完整 pack 随 Ergora 整包再分发。具体文件的独立许可和用户已有授权另核，优先通过用户提供的已安装工具引用。此处记录原条款的适配影响，不扩大到所有训练结果。[许可原文][nsys-license]。

## Bridge：可复用的完整分析流程与版本边界

### Nsight 诊断合同

固定 Skill 的强项是**先解释 step 的关键路径**，而非自动追逐耗时最大的 kernel。其输入要求 trace／rank／host／GPU／工具版本、Bridge／Core revision、容器、模型／精度／形状／batch、并行拓扑与 stage mapping、实际 step 定义和捕获方式。每个 supplied rank 先做调查，再选 slowest trainer-step rank 与各不同 PP stage／fingerprint 的代表；rank0 或文件名都不能代替这些身份。[固定 Skill][bridge-nsys]。

预算应裁剪到每个稳态迭代，跨 stream 做 interval union：device busy／idle、compute busy／absent、communication／dispatcher、copy 分开。compute-absent 再分 host 未发出、已发出且有已解析阻塞 producer、依赖未解三类。必须核计时守恒，保留未解份额。长 collective、copy 或暴露时间只是候选现象；只有依赖与负 slack 支持它阻塞下一次 compute 时，才算 recoverable critical-path bound。NVSHMEM／DeepEP／HybridEP 等不能被 NCCL-only regex 漏掉，dispatcher packing／routing 也不能全叫网络传输。[Skill][bridge-nsys]／[pitfalls][bridge-pitfalls]。

SQL recipes 是 schema-aware 的检查清单：先查 tables、session epoch、diagnostics，再列 workload 和连接 runtime／kernel／sync 数据；event 依赖使用 `eventSyncId`，不能用可复用的 `eventId`；有些 event timestamp 为零，需要沿 stream 操作重建 producer。graph replay 可能没有独立 kernel launch 行，runtime correlation coverage 与 Python／framework source-callstack coverage 必须分别报告。对多进程／图的连接结果先检查作用域、基数和缺失，不能复制 SQL 后直接给根因结论。[SQL recipes][bridge-sql]；[pitfalls][bridge-pitfalls]。

该 Skill 没有实现采集／重试／实验调度器，也不提供可验证的自动修改闭环。它的最小价值是“具版本的资料＋分析步骤＋输出合同”；作为方向子模板可保留它内部的诊断次序，不应切成几十个只负责重复一条检查的 Agent。

### Snapshot：离线脚本有用，内存口径须完整

固定 Skill 给出 `parse_snapshot.py`、`compare_snapshots.py`、`plot_timeline.py`、`replay_to_time.py`、`replay_step.py`；典型流程是 overview→双 trace overlay→选分歧时刻→按来源解释差异。解析／比较脚本提供文本或 JSON，绘图生成 HTML。已读 parse／common／compare／plot 源码，未执行脚本；Python 侧为 stdlib，plot HTML 会从 Plotly CDN 取 JavaScript，不能称为完全断网可用的 artifact。[Skill][bridge-memory]；[common][bridge-memory-common]；[compare][bridge-memory-compare]；[plot][bridge-memory-plot]。

当前固定训练源码在模型构建前启动 allocator history；仅选定 ranks 记录，`profile_ranks=[]` 表示所有 ranks；保留最多 100,000 个事件，在指定 end step 写带 rank 后缀的 snapshot，并附 OOM observer。这个事实以当前 `setup.py`／`train_utils.py` 为准，不能把 Skill 中旧 capture 的大 baseline、旧行号或事件量当作当前采集行为。[config][bridge-config]／[setup][bridge-setup]／[train utils][bridge-train-utils]。

解释时至少保存以下区别：

- `segments` 是 dump 时 allocator 状态；`device_traces` 是保留下来的历史。allocated、reserved、active／awaiting-free、inactive 分开；未完成释放的块不能按可复用碎片计算。来源归组表不能强制凑成全部 absolute peak。[Skill][bridge-memory]／[重建实现][bridge-memory-common]。
- ring buffer 覆盖或记录起点过晚会丢 alloc，出现大量 unmatched frees；重建 baseline／absolute peak 随之不确定。对比必须匹配 rank／stage、step／warmup 语义、allocator、图及 capture 设置；同一 elapsed second 不自动表示同一训练进度。[Skill][bridge-memory]。
- allocator snapshot 默认只见 PyTorch 管理的设备内存，NCCL／直接 CUDA 分配不可见。PyTorch 2.15 另提供 opt-in pinned-host history，但固定 Bridge 的调用没有启用它；现有 Bridge 脚本也不能因新框架有 `host_traces` 就宣称完整支持 host／CPU-offload 分析。设备总占用、进程外占用和 CPU RSS／pinned RAM 须另补。[PyTorch 文档][torch-memory]；[Bridge 调用][bridge-train-utils]。
- graph replay alloc 变少不代表显存变少，graph pool 可能增峰；OOM 现场也只证明该 rank／时刻的失败状态。不能把“更安静的 timeline”“单次不 OOM”晋升为容量或吞吐收益。[Skill][bridge-memory]。
- native pickle 会执行代码。只让受信任来源的 snapshot 进入已授权隔离 parser；不能在通用只读 Agent 上反序列化任意下载文件。stack／路径也是原件的实际数据边界，发布摘要须按已有 artifact 合同处理。[实际 load][bridge-memory-common]。

### 当前源码与旧示例不能混用

当前 `initialize_pytorch_profiler` 使用 `pytorch_profiler_collect_shapes`、`pytorch_profiler_collect_callstack` 和可选 Chakra execution-trace observer，按 rank 导出 Chrome JSON；文档／plugin 示例仍传 `record_shapes`。当前 Bridge `ProfilingConfig` 继承 Core 的配置，而不是在本文件内定义所有字段。因此这里证明的是**需要核 resolved config／真实行为的接口差异**，不在未完成 Core 字段与运行验证时断言所有示例无效或自动兼容。[profiler 实现][bridge-profiler]／[config][bridge-config]／[文档][bridge-profile-doc]／[plugins][bridge-plugins]。

同一配置明确禁止 PyTorch profiler 与 nsys profiler 同开；memory history 是独立开关，只有 PyTorch profiler 提供合适 step markers 时才能做按 step 重放。NsysPlugin 与 FaultTolerancePlugin 不兼容的边界也须交 R8，不能通过关闭恢复能力来偷偷换取 profiling 成功。[config][bridge-config]；[memory Skill][bridge-memory]；[plugins][bridge-plugins]。

## 官方 Nsight：真实工具与 Skill，保留其原生分析能力

### 2026.5 与 2026.6 分开使用

已核官方 2026.5 存档：当时 Skill 用渐进发现和 bundled scripts 引导 Agent；当前 2026.6 则将工具合入 CLI，Skill 简化为发现和启动指南。故不能把旧 pack 的脚本布局与当前 CLI 混成统一接口，也不从“agent support”推断有官方 MCP transport／服务端。[2026.5 存档][nsys-archive-ai]；[2026.6 发行][nsys-release]。

当前可复用原生能力包括：

|能力|实际接口与输出|适用范围／限制|
|---|---|---|
|清点和文档发现|`nsys survey`、`nsys docs`，文本／JSONL|已有报告 metadata／installed docs，先以安装版本 help 定义能力|
|统计与规则诊断|`nsys stats`、`nsys analyze`；六类 expert-system rules|sync／pageable async copy／sync copy／memset／GPU gaps／time utilization；是规则 findings，非自主因果证明|
|多报告分析|`nsys recipe`，CSV／Parquet／notebook／JSONL，部分 recipe 有 insights 和建议下一步|当前有 `nccl_pace`，要求 advanced NCCL tracing；不能对没有相应采集的旧报告“补出”数据|
|受限 SQL|`nsys query [options] <input-file> --sql ...`|单输入、单 SELECT／WITH、行／字符／时间限制；新路径处理 native report 或 recipe tables，不能把 SQLite shell 命令照搬|
|导出|`nsys export`：SQLite／其他格式；保留原 report|schema／导出实现依版本变化；只在派生工作目录修改查询辅助表|

依据为[CLI 手册][nsys-guide]、[query 约束][nsys-query]和[发行说明][nsys-release]。`nsys query` 不支持多报告 query；大表须显式 LIMIT／aggregate 等约束。它会在报告旁生成并复用 Parquet 缓存，需要目录写权限，输入准备可耗时数分钟，而且文档明确会自动安装所需 Python 依赖。离线／受限 runner 应先提供匹配环境、将输入复制到受控 scratch 并记录派生物；依赖不具备时显式 unavailable，不能让一次“分析”暗中获得包安装或网络权限。[query][nsys-query]。

AI pack 官方自称 Preview、仅测有限模型，重要结论要回到 docs／live help／trace 核实；周边 experiment management、正确性验证、停止条件和采用决策不是 pack 自动保证的功能。适配时保留其原生 reports／recipes，Ergora 只补实际工具清点、输入输出和候选证据合同。[AI 文档及失败模式][nsys-ai]。

### 采集权限不外推到分析权限

Linux CLI 推荐无 root；某些 CPU sampling／scheduling 受 perf 配置约束，GPU metrics 需要 elevated permissions，ftrace 需要 root。Windows 一些采集特性也需要管理员权限。缺权限时记录缺失源，继续执行仍可支持的 timing analysis；不得修改主机 sysctl、驱动权限、seccomp 或提升容器来满足研究模板。[安装要求][nsys-install]；[GPU Metrics][nsys-metrics]／[CLI][nsys-guide]。

采集命令能启动应用、写报告、在受限时终止 workload；新版还支持执行用户提供 shell callback。它与 `query`／已有报告分析应是不同 operation。可用性清点必须列出是否允许 launch、attach、stop、metrics、network clock provider、依赖安装以及已有报告 import，不能只给一个 `nsys=true`。[发行说明][nsys-release]／[CLI][nsys-guide]。

## 第三方 Nsight Agent：有真实 MCP，采用须降到可核范围

固定 server 使用官方 MCP Python SDK 的 FastMCP 和 STDIO，实际暴露 doctor／capabilities／open／stats／compare／analyze／export，以及 owner 预配置 target 的 capture 和可选 Compute report import。它调用官方 nsys，通过固定 report／rule allowlist、参数数组、超时、隔离缓存、分页返回结构化结果；没有暴露任意 shell／SQL／report script。`nsight_capture` 单独标记会产生副作用，只接预注册 target id；整套服务仍需其可访问输入和派生目录权限。[server][mcp-server]；[core][mcp-core]；[capture][mcp-capture]。

其诊断文档把 `no_findings`、`MISSING_DATA`、`CAPABILITY_UNAVAILABLE` 分开，并指出默认 500ms gap 阈值可能漏掉短 step 的重要空隙。time／NVTX filter 返回重叠事件的完整 duration，不是裁剪后的窗口占比；完整 CSV 先在本地物化，分页只控制模型输出，不限制 nsys 的计算／内存／磁盘成本。比较只是精确名称匹配的官方 aggregate 相减，不能据此证明 workload 可比、源代码根因或 wall-clock speedup。[诊断合同][mcp-diagnostics]；[README][mcp-readme]。

作者 2026-10-13 的 v1.2 validation 记录了实际 Windows／Linux-container、Systems **2025.6.3**、public T4 report、STDIO 和一次真实模型工作流，区分 mock positive、real no-findings、旧版与最终 wheel。作者还保留 Compute 2026.1 `--apply-rules` 与 `--import` 不兼容的早期失败，最终改成固定 CSV import；以及 `analyze --quiet` 隐去 SKIPPED 导致 missing-data 误判的修正。这比仅列工具名称更可审查，但它仍是**作者报告，本轮未复跑**。[v1.1 验证][mcp-validation11]；[v1.2 验证][mcp-validation12]。

采用建议是借鉴“受限接口、完整来源、缺失可见、有限 capture registry、结果快照”而非导入一个全能专家。当前没有它在 Nsight 2026.6、新 CLI 路径、Bridge 多节点／编译图／完整跨 rank critical path 上的独立验收；也没有模型长期诊断准确率或性能收益证据。若官方 CLI 已能满足消费者，优先直接适配；若确需 MCP，仅对固定版本和指定 operation 做后续独立准入，自动采集默认暂缓。[范围与测试边界][mcp-readme]／[v1.2 limits][mcp-validation12]。

## PyTorch、CUPTI 与 HTA：跨层证据不能替代性能验收

PyTorch profiler 能收 CPU／CUDA activity、shape／stack／memory 和 execution trace，用 schedule 分开 wait、warmup、active；shape／stack 增加开销，保留 tensor 引用还可能影响优化和复制。CUPTI 不可用时 CUDA 时间可能仍见于 table，但 Chrome JSON 缺 GPU activity，因此“表里有 CUDA time”不证明离线 trace 完整。execution trace 提供图结构，不自动等价于 Nsight hardware timing 或真实分布式执行收益。[固定 profiler][torch-profiler-src]／[API 文档][torch-profiler]。

不能再一概写“CUPTI 永远只支持一个 subscriber”：当前官方文档的 V2 路径在 CUDA 13.3＋r610 起支持多个，旧路径／旧驱动仍可能报 `CUPTI_ERROR_MULTIPLE_SUBSCRIBERS_NOT_SUPPORTED`。这并不覆盖 Bridge 自身禁止两个 profiler 的配置合同，也不能证明具体 PyTorch／nsys 已一起使用 V2。HES 是 Blackwell 引入的另一种 timestamp 路径，有初始化顺序、图 trace mode 和字段限制；不应把硬件／软件 capture 或不同 graph 粒度的测量直接比较。[CUPTI initialization／HES／multiple subscribers][cupti]；[Bridge guard][bridge-config]。

HTA 的真实可调用流程是：读取同一 job 的 PyTorch traces→`get_temporal_breakdown`／kernel／idle／comm overlap→定位 selected rank／annotation→critical path→overlay／diff。critical-path API **限定单 rank**，要求 CUDA synchronization events，并建议避开首个可能缺事件的 step；返回成功标记不是整个分布式训练已解释的证明。[README][hta-readme]／[API][hta-api]。

固定 HTA 的 `_align_all_ranks` 只是减去所有 trace 的共同最早 timestamp；它本身没有实现跨主机时钟偏差校准。分类也通过 pattern 匹配，适配者须审查当前 workload 的 material kernels／backend 覆盖。对不完整 sync、图、非 NCCL 后端、不同 PP stage 或异步数据路径，先报告覆盖／未解范围，再决定能否做 causal claim。HTA 有可复用测试和实现结构，但这里未验证它与 PyTorch 2.15 所有新 trace backend／格式兼容。[对齐源码][hta-trace]／[分类源码][hta-utils]。

## 可信测量与负面证据门禁

以下是建议给最小流程的验收条件，来自上述官方方法与本项目已有候选合同；不是本轮测出的结果。

1. **先固定问题和分母。** 记录 optimizer step／microstep／含 data loading 或 checkpoint 的端到端范围、有效 token 数、shape 分布、精度、batch／accumulation、并行 mesh、软件／硬件版本。对 PP 不同 stage 保留身份；吞吐以实际全局完成工作量和可信 wall time 定义，不能把 rank0、最长 stream 或 kernel sum 当全局训练时间。[Bridge contract][bridge-nsys]；[官方验证流程][nsys-ai]。
2. **分开诊断 pass 和评价 pass。** 除去 compile／warmup／graph capture／profiler start-stop-flush，保存 n、median／min／max 和 raw samples。对同一 run 比较 profiled 与 unprofiled 稳态区间评估扰动；`PROFILER_OVERHEAD` 不是全部减速，不能从它减出“校正”收益。GPU metrics／stack capture 单独短采样；最终候选用未插桩重复测量。[Skill][bridge-nsys]／[pitfalls][bridge-pitfalls]。
3. **计时确实等待所定义的工作完成。** CUDA 异步使 host launch time 不等于 device completion。局部算子可用正确同步或 CUDA events／Timer；不要在每个 kernel 间加入同步破坏原本 overlap。分布式训练另保存 rank／step 完成语义和慢 rank，框架微基准不自动提供整作业 wall time。[Timer][torch-benchmark]；[官方 timing pitfalls][nsys-pitfalls]。
4. **跨主机对齐给误差范围。** Bridge recipe 的 epoch rebase＋多次匹配 collective robust offset 是估计，必须匹配组／顺序并报告 residual，不能把真实 arrival jitter 全拟合成 clock offset。当前 Nsight vClock 可在 Linux 测相对 offset、不改系统时钟，目标为几十微秒量级但受网络影响且仍 experimental；需要 provider／consumer 和同 domain 数据。缺数据时 recipe 会退回 UTC，不能从自动对齐 UI 推出纳秒级跨主机因果。只比较 duration 仍有用，但不证明谁先到／晚完成。[Bridge SQL][bridge-sql]；[vClock][nsys-vclock]。
5. **区间、关联与计数器分开。** busy 用 union；通信 expose 不等于 blocking；kernel→runtime correlation 不等于源栈。metric 是 device-wide，报告 sample count 和 exclusivity；SMs Active 不是算力吞吐，unsampled 不是零。没有指标权限可给 timing 结论，但不能补出 roofline／occupancy 根因；kernel SOL 转 R1／Nsight Compute。[Bridge pitfalls][bridge-pitfalls]；[Nsight metrics][nsys-metrics]。
6. **收益上限与实测分开。** 对同一 profiled step T 和可恢复、互不重叠的关键路径 R，吞吐上限为 `T/(T-R)-1`；它是 ceiling，不是 forecast。受扰动的 R 不能直接移植到 unprofiled T。MFU 还需独立核算法 FLOPs、精度分母和是否改变工作量；不同机会的上限不默认相加。[Skill][bridge-nsys]。
7. **正确性／质量与性能各自通过。** trace 不能证明输出、梯度、训练质量或未捕获输入正确；单次更快可能是少做工作、缓存或错误。基线与候选保持 workload 条件，记录每 case 与重复结果，受共享资源影响的实验隔离／串行。采用由可信评价与原 owner 决定，诊断者只交证据和下一次可区分的测量。[官方 failures／validation][nsys-ai]。
8. **失败和无收益都保留。** 分成 measurement-invalid、capture-incomplete、tool／environment-unavailable、implementation／correctness-failed、valid-no-gain、verified-improvement；同时保存 effect/noise 与具体范围。无 findings 不是最优证明，一次实现失败也不推翻技术本身。失效证据的后代候选必须重新评价，不能把受污染高分留成经验。[官方重复优化失败模式][nsys-ai]；[Bridge pitfalls][bridge-pitfalls]。

本轮实际负面记录：搜索连接器 unavailable；两个猜测的 NVIDIA repo URL 返回 404；旧 docs host 的 2026.2 archive URL 返回 404，随后从官方 Archives 找到 archive.docs.nvidia.com 的 2026.5；若干猜测源码路径 404，改读已定位实际文件；HTA latest 文档超时／猜测 feature 页 404，Perfetto docs TLS EOF。它们是发现／访问范围，**不证明对应技术不存在或实现失败**。报告不以未读完的上游字段或不可用页面作兼容结论。

上游已记录的实际风险另保留：Nsight release notes 列出 crash／强制终止的 CUDA trace 丢失、seccomp 与注入不兼容、大报告／长采集的资源问题，以及导出实现回退；第三方 MCP 保留了 import 参数和 missing-data 误判的修正。遇到相应环境应记录具体失败并缩小结论，不自动关闭宿主安全策略或禁用已有恢复要求。[官方 release／known issues][nsys-release]；[MCP 作者验证][mcp-validation11]／[v1.2][mcp-validation12]。

## 最小可复用子流程合同

建议先导入 **trace 诊断** 和 **snapshot 差异分析** 两个方向子流程，共用工具准入／测量证据结构；原生多报告 recipe／HTA 内部分析仍由原工具执行。下表是 D0／D1 的候选合同，当前不宣称 Ergora 已执行这些 operation。

|合同项|最小要求|
|---|---|
|输入|原 task／run／candidate 身份；目标与 step 定义；源／容器／配置／硬件版本；immutable artifact id＋hash；rank／host／stage／group mapping；profiler settings／诊断日志；同条件未插桩样本；snapshot 来源信任与预算|
|工具清点|明确支持的 import／schema／stats／rule／SQL／recipe／memory replay／capture／metrics；精确版本与许可；缺失以 unavailable 返回。NVIDIA CLI、第三方 MCP、HTA 为可替换 backend，不因工具名称自动回退|
|权限|离线读取批准原件、写专属 scratch／派生输出；pickle 仅经已授权可信 parser；collect、GPU、metrics、clock-provider network、依赖安装、远程作业分别约束。所有祖先资料完整读取、资源权限取上限交集，不新增宿主权限|
|步骤|①准入与 identity／hash；②schema／capture／rank／clock／snapshot 历史质量；③所有 supplied ranks／阶段调查；④union／dependency 或 memory replay；⑤按证据置信度排序；⑥给一个可区分假设的下一步实验并交相应方向|
|产出|capture-quality record；每 step／rank 预算及 n／误差；taxonomy 与未分类项；来源表／query／filters／units／event references；观察／source-verified／inferred／unverified 标签；机会 ceiling、替代解释与最小验证；派生物 hashes；失败及无收益记录|
|预算|按文件大小／事件／rank 数限定 RAM、磁盘、墙钟、query／tool calls、model token 和 capture 步数；分页不等于后端预算。自动安装／额外 capture 不在预算内时明确拒绝，返回能继续的离线范围|
|恢复|保留 tool/job/session id、所属进程和部分 artifact；timeout 不当作已完成；重试前核原 operation 与输出，不重复启动 workload。session-local MCP report/result id 不是持久 artifact identity；重启后按 hash 重注册|
|独立评价|诊断者不修改可信计时／评分路径；执行者单独产生候选，独立 reviewer 核正确性／质量、未插桩匹配测量和根因证据；原 owner 决定采用，不建立第二调度／状态账本|
|结束与交接|有足够证据则输出有范围结论；缺数据则给明确 unknown 和所需最小 capture，不无限追踪或自动扩权。launch gap→R6，通信／jitter→R3／R4／R8，allocator／offload→R5，kernel 指标→R1，模型／精度语义→R2／R9|

合同主要复用 [Bridge 输出要求][bridge-nsys]、[snapshot 工具边界][bridge-memory]、[Nsight 验证方法][nsys-ai]及 [MCP 有界工具经验][mcp-readme]。R8 的作业／恢复诊断可引用这些 artifact，不在 R7 内接管 restart／stop 或集群生命周期。

D0 建议的顺序是：**采用**固定 Bridge 分析／pitfall／SQL 资源；**适配**可信 snapshot parser 和已具备环境的 Nsight 原生离线 CLI；PyTorch trace 消费者出现后**条件适配** HTA；**借鉴**第三方 MCP 的 allowlist、缺失数据和证据快照；**暂缓**默认自动采集、特权指标、自建 CUPTI collector 与自主修改／晋升闭环。先用真实受控样例核接口、缺失／timeout／schema 漂移，再在用户已有硬件和授权 runner 上独立验收；本轮不给任何 GPU 收益或模型诊断准确率结论。

[index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[bridge-nsys]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-nsys-analysis/SKILL.md
[bridge-pitfalls]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-nsys-analysis/references/pitfalls.md
[bridge-sql]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-nsys-analysis/references/sql-recipes.md
[bridge-memory]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-memory-snapshot-analysis/SKILL.md
[bridge-memory-common]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-memory-snapshot-analysis/scripts/common.py
[bridge-memory-compare]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-memory-snapshot-analysis/scripts/compare_snapshots.py
[bridge-memory-plot]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-memory-snapshot-analysis/scripts/plot_timeline.py
[bridge-package]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/package_info.py
[bridge-license]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/LICENSE
[bridge-config]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/config.py
[bridge-setup]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/setup.py
[bridge-train-utils]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/utils/train_utils.py
[bridge-profiler]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/profiling.py
[bridge-profile-doc]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/training/profiling.md
[bridge-plugins]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/recipes/run_plugins.py
[nsys-release]: https://docs.nvidia.com/nsight-systems/ReleaseNotes/index.html
[nsys-guide]: https://docs.nvidia.com/nsight-systems/UserGuide/index.html
[nsys-ai]: https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html#ai-assisted-analysis
[nsys-query]: https://docs.nvidia.com/nsight-systems/UserGuide/index.html#cli-query-command-switch-options
[nsys-install]: https://docs.nvidia.com/nsight-systems/InstallationGuide/index.html
[nsys-license]: https://docs.nvidia.com/nsight-systems/CopyrightAndLicenses/index.html#nvidia-software-license-agreement
[nsys-metrics]: https://docs.nvidia.com/nsight-systems/UserGuide/index.html#gpu-metrics
[nsys-vclock]: https://docs.nvidia.com/nsight-systems/UserGuide/index.html#vclock-plugin
[nsys-pitfalls]: https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html#common-analysis-pitfalls
[nsys-archive-ai]: https://archive.docs.nvidia.com/nsight-systems/2026.5/AnalysisGuide/index.html#ai-assisted-analysis
[mcp-readme]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/README.md
[mcp-pyproject]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/pyproject.toml
[mcp-license]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/LICENSE
[mcp-server]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/src/nsight_agent/server.py
[mcp-core]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/src/nsight_agent/core.py
[mcp-capture]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/src/nsight_agent/capture.py
[mcp-diagnostics]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/docs/DIAGNOSTICS.md
[mcp-validation11]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/docs/VALIDATION-v1.1.md
[mcp-validation12]: https://github.com/liubingjun1207/nsight-agent/blob/e69916fa541da7fef7695fe592c5a9149099d02b/docs/VALIDATION-v1.2.md
[torch-profiler]: https://docs.pytorch.org/docs/2.15/profiler.html
[torch-profiler-src]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/profiler/profiler.py
[torch-memory]: https://docs.pytorch.org/docs/2.15/torch_cuda_memory.html
[torch-benchmark]: https://docs.pytorch.org/docs/2.15/benchmark_utils.html
[torch-license]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/LICENSE
[hta-readme]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/README.md
[hta-version]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/hta/version.py
[hta-license]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/LICENSE
[hta-api]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/hta/trace_analysis.py
[hta-trace]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/hta/common/trace.py
[hta-utils]: https://github.com/facebookresearch/HolisticTraceAnalysis/blob/eb0b6d6ee288641abe06174216db920909a196b3/hta/utils/utils.py
[cupti]: https://docs.nvidia.com/cupti/main/main.html
