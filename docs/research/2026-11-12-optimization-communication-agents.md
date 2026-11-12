# 通信优化：Agent、自动搜索与执行工具

检索日期：2026-11-12。范围覆盖 collective 合成、MoE dispatch/combine、并行拓扑及通信计算重叠；读取官方源码、文档和作者论文，未安装依赖、运行模型、GPU 或多 rank 实验。用户给定的 Megatron Bridge Skills 索引仅用于方向校准。

**建议先接通信诊断专家和有界自动调参子流程，再按硬件接 MoE 后端与调度合成器。** 本轮找到真实的双 Agent 调优研究，但其源码尚待公开；未找到可直接导入 Ergora 的、具备可核实现与恢复合同的专用 LLM 通信优化 Agent。MSCCL++、DeepEP、NCCL EP、NVSHMEM 是库或工具；AutoCCL、TACCL 等有实际自动搜索，但不能因此改称 LLM Agent。

## 候选与接入判断

表中短 SHA 均对应本轮实际读取的固定源码；许可证为项目根许可，依赖仍须分别固定。性能数字均为作者报告，未在本项目复现。

|候选、身份与许可|真实能力、适用范围及接口|证据与主要限制|Ergora 判断|
|---|---|---|---|
|[MSCCL++ `0a6be3e`][mscclpp]，MIT|GPU 驱动通信栈及 C++/CUDA/Python API；NVLink/xGMI、同 PCIe switch 的 P2P 与 IB。官方要求 Volta+/CDNA2+，较充分测试 Ampere+/CDNA3+。`mscclpp_benchmark.bench_collective --autotune --write-config` 实际搜索配置并保存 JSON；支持读回调参结果。[源码][mscclpp-bench]|[Quick Start][mscclpp-quick]提供 MPI 单元测试、正确性与调参入口；当前 benchmark 默认检查正确性，可被显式跳过。README 收益图基于 1–2 节点 A100、NCCL 2.19.3，不能外推到最新 NCCL 或训练收益。|**优先适配**为真实搜索子模板；库接工具适配器，配置提案交原 runner 执行。|
|[AutoCCL `63acb15`][autoccl]，[根 BSD 许可][autoccl-license]|NSDI25 自动调参系统，分治搜索并考虑通信计算干扰；实际实现需要预载其 `libnccl.so`、tuner plugin、协调进程地址及 group world size，一进程管理一 GPU。|[官方论文页][autoccl-paper]：16/32 A40、NVLink/PCIe、800/100 Gbps IB 两类集群；端到端报告 1.07–1.32×。README 以 PyTorch 23.08 容器为起点，没有证明此 fork 可替换当前 NCCL 2.32 系列；不是拿一个插件就完成升级。|**适配为可选完整调参流程**，先核自带 runtime/ABI 与恢复；优先级低于无需替换当前 runtime 的测量入口。|
|[MSCCL-tools `030a750`][msccltools]、[TACCL `426bd1e`][taccl]，MIT|前者提供 MSCCLang、自动合成及计划注册；后者由拓扑 profile 和人工 sketch 经 Gurobi 生成 JSON，再 `taccl ncclize` 降为执行格式，交 MSCCL runtime 与 nccl-tests。|工具链有真实 CLI 和产物，但 README 的 Azure NDv2/NDv4、DGX2、旧 PyTorch 集成不能视为 H100/B200 已验证。Gurobi 另需许可；sketch 不是全自动拓扑发现，求解正确不证明并发执行无死锁。|**借鉴合同，按需适配**为“合成→降级→多 rank 验证”子模板；不默认替换 NCCL。|
|[TE-CCL `c128bf2`][teccl]，MIT；[OptCCL `dc54db8`][optccl]，MIT|TE-CCL 用流约束/MILP、LP 或 A* 输出 JSON schedule；`teccl solve --input_args`。较新的 OptCCL 使用 mirrored Dantzig–Wolfe，覆盖 AG/RS/AR/A2A，提供 `solve/process/run/multi`、日志文件和保存解后的后处理。两者需 Gurobi。|TE-CCL 明示大型例子需 **256 GB RAM、1 小时以上**。OptCCL 保存 solver result 不等于支持断点恢复；`--write-schedule` 默认关闭，`stop_at_feasible` 只保可行，不能标为最优。[原始论文 DOI][optccl-paper]|**适配离线合成工具**，有拓扑问题才选用；先预算 CPU/RAM/求解时限，再单独验证运行时转换。|
|[ForestColl `d7bd6a9`][forestcoll]，Apache-2.0；[TACOS v1.3.0 `1811f1f`][tacos]，MIT|ForestColl 对异构网络生成 AG/RS spanning trees，并有 MSCCL/RCCL XML 转换；TACOS 用拓扑和 collective 构造器、C++ `Synthesizer.solve` 搜索。|[ForestColl NSDI26][forestcoll-paper]及实现比仅列旧 TACCL 更值得跟踪，但不覆盖 A2A。**TACOS 当前代码只支持 AllGather、直连拓扑，返回估计时间，XML 输出仍在开发**；[论文][tacos-paper]的 40K NPU 合成规模并非 40K 真机运行。|ForestColl **按需适配**；TACOS **借鉴估计器，暂缓执行接入**。|
|[DeepEP `f6aa38f`][deepep]，MIT|主线 README 自称 V2.5：`EPBuffer`、DeepJIT、NCCL Gin，Hopper+、CUDA≥13.1、PyTorch≥2.10、NCCL≥2.32.3，NVLink/RDMA；SM/QP 用解析估计，可人工覆盖。|已删除 V1 API 与 NVSHMEM 依赖；EP 仍占 SM，不能复用旧版“零 SM、NVSHMEM 自动调参”叙述。本轮 refs 只见 v1.2.1 tag，故固定 SHA，不能把 README 版本名当已验证发布包。PP/CP/DP 新原语仍标 experimental。|**按框架固定版本适配工具**；先验接口、路由/缓冲与训练梯度，再做后端比较。|
|[NVIDIA Hybrid-EP `4e890fd`][hybridep]，DeepEP `hybrid-ep` 分支、MIT|TMA/warp pipeline 降低 SM 使用；支持 NVLink/RDMA/MNNVL。DOCA 路径或实验性 NIXL/UCX 路径；后者需要额外 etcd 元数据服务，具有 run-ID 与连接重试配置。|[官方文档][hybridep-doc]分列 H100 16/32/64 rank、B200 8 rank、GB200 的 Torch API 与 kernel-only 带宽，二者不可混比；NIXL 性能未定。与同名跨数据中心 HybridEP 论文不是已确认同一项目。|**条件适配**为 MoE 子流程后端；服务生命周期、网络与资源额度须随任务绑定。|
|[NCCL Extensions `3401dea`][ncclep-root]、[NCCL EP][ncclep]，Apache-2.0|当前官方归属 `NVIDIA/nccl-extensions`，C API/Python `nccl.ep`、`ep_bench`；HT 用 NVLink+RDMA，LL 面向小 batch；提供自动 buffer/QP/channel 配置及 staged execution，测试设备为 Hopper/Blackwell。|根文档要求 NCCL≥2.32.3 并拒绝旧 runtime；JIT 要求匹配工具链。自动配置不等于自动搜索训练拓扑；单元/微基准仍需接入框架的完整数学与梯度验证。|**纳入 MoE 后端候选**，先检查框架消费者与实际安装版本；不能把 API 自动配置包装为独立 Agent。|
|[NCCL v2.32.6-1][nccl]、[nccl-tests v2.21.1][nccltests]；[NVSHMEM `eaf955f`][nvshmem]；[UCCL `52d4184`][uccl]|NCCL 支持 PCIe/NVLink/IB/TCP，提供 tuner/profiler 插件；nccl-tests 提供正确性、全 rank 计时与 JSON。NVSHMEM 是 GPU 发起的一侧通信 API；UCCL 是面向 NVIDIA/AMD、多种 RDMA NIC/EFA 等网络的 transport/EP 库。|这些是执行、诊断或可替换 transport。NCCL 根许可 Apache-2.0 加 BSD 部分，tests 为 BSD；NVSHMEM 根许可 Apache-2.0、第三方部分另列；UCCL 为 Apache-2.0。支持矩阵不能由一个厂商 GPU 推及所有网卡/云。|**采用基线与诊断工具**；NVSHMEM/UCCL 仅在现有后端的硬件或网络约束要求时适配。|

## 更近的 Agent 与完整闭环

[2026-11-07 双 Agent 论文][rl-agent]用 LSTM+SPRT 检测持续争用，D3QN+CQL 从 96 个配置选择算法、协议、channel、thread；通过 NCCL tuner plugin 和独立 CPU 协调器执行。论文报告同版 NCCL 2.29.2/CUDA12.6 下的 P100 微基准及 A100/Slingshot-11 扩展，不能视为现代 NVLink MoE 收益。它是真实 RL Agent 研究，**不是 LLM 编码专家**；§4.4 明确源码将在发表后公开，当前没有可核仓库、发布版本、代码许可和恢复实现。结论为**借鉴检测与选参分离，暂缓导入**。

[MCCL v2，2026-10-21][mccl]已形成“被动测量→检测灰故障→warm-start 重合成→热切换”完整系统，比只做离线合成更接近方向子模板。真机原型是 **2 节点×4 H200、200 Gbps CX7**；约 12 ms 热切换来自该原型，最高 4.99× 训练收益来自 SimAI 的 128–2048 GPU 场景，且端到端模拟把故障通知与检测解耦。正文还记录小 chunk/低 channel 时测量开销约 13%，不能只引用摘要“<2%”。本轮未核到可完整复用的 MCCL runtime/许可，只有其引用的扩展 SimAI 等代码入口：**借鉴闭环，暂缓宣称可导入**。

[Lagom v1，2026-02][lagom]把通信参数与计算争用共同建模，自动搜索 channel/chunk，报告优于 NCCL/AutoCCL；读取的论文没有提供可核实现入口，列为**借鉴**。这类证据说明目标应是 step time，而非通信带宽最大化。上述检索结论限本轮公开可读来源；GitHub 搜索 API 返回限流，未绕过限制，不能声称穷尽所有专用 Agent。

## 专家与方向子模板的最小合同

**采用**一个可替换的通信分析专家，职责是从全 rank 证据定位 exposed communication、识别拓扑/流量/调度问题，提出有界候选；原有 `ergora-performance-analyst` 可承担第一版只读消费者。**适配**一个通信优化子模板管理前置检查、工具选择、候选测量和交接，而不是把每种通信库各造一个 Agent。以上官方接口为 CLI、C/C++、Python 和插件；本轮未见项目自带 MCP。若增加 MCP，仅封装已支持操作，分别报告“已安装、可启动、已验证的硬件/规模”，不可用时明确拒绝。

流程至少保留下列四个出口，运行仍归原 Temporal/runner、candidate 与审批所有者：

1. **固定工作负载和资源。** 输入 GPU/NIC/驱动/固件、拓扑与 rank↔GPU↔NIC 映射、TP/DP/PP/CP/EP group、collective 形状/字节数/dtype、路由与 batch、graph/recompute、依赖 SHA。基线先正常工作；预约匹配多节点资源，计入 CPU proxy、通信 SM、对称 buffer、求解 RAM、预热、搜索试次及集群占用，超预算拒绝。
2. **生成或调参。** 首个可执行适配从 MSCCL++ 保存/读回配置开始，AutoCCL 为隔离 runtime 的可选分支；拓扑不足再选 ForestColl/TE-CCL/OptCCL/TACCL。记录搜索空间、seed、时限、终止原因、可行性/最优性与每次失败。XML、solver JSON、MSCCL++ 配置不是互换格式，必须明确降级器和对应 runtime。
3. **多 rank 门禁。** nccl-tests 保持 correctness 检查，覆盖实际 rank/node 数、消息大小及 dtype；MoE 再核 token 无误丢/重复、权重与 backward、偏斜/空 expert、容量溢出。检查 collective 顺序、stream/event、buffer 生命周期、graph replay，以及迟到/失联 rank 的超时和全组退出；单卡、CPU、rank0 正确均不能替代。数学可行解不能替代死锁/前进性验证。
4. **成对验收与恢复。** 固定并发/网络条件，只改一个候选；未 profile 的稳态 step time/tokens、尾延迟、损失/梯度和显存为验收，匹配 trace 解释暴露区间与重叠，不能用各 stream kernel 时间之和计算收益。保存命令 argv、完整 stdout/stderr、所有 rank 状态、配置/源码 digest、JSON、trace、超时及清理回执。失败保留原 attempt；未知状态由原 owner 核查并终止全组，不能恢复半个 collective，也不能把缓存配置当成功日志。

NCCL [RAS][ras]提供跨进程健康信息和 JSON/monitoring；诊断适配器只开放查询。当前 RAS 另含会改变运行作业的 `CONTROL` 命令，不能混入只读工具。按 [NCCL 日志文档][nccl-env]为每进程设置唯一日志文件，否则输出可能丢失或损坏。**门禁通过才交原审批者采用**，研究专家不拥有自动替换 runtime 或调整网络设备的权限。

## 与 Bridge 的关系及接入顺序

[Bridge 官方 overlap 指南][bridge-overlap]与[固定源码 Skill][bridge-skill]适合吸收为知识和检查规则：TP 需要 sequence parallel/TE，EP 需要正确 dispatcher，PP/VPP、shared-expert overlap、full recompute 和 CUDA graph 有组合约束。`flex` 的存在不证明已启用某个后端，也不证明任意后端版本兼容。[MCore `a7a6d22`][mcore]仍导入 `Buffer/ElasticBuffer`，而上述 DeepEP 主线改为 `EPBuffer`，须固定匹配组合；源码还特意关闭 HybridEP 的 custom allgather 以避免迟到 rank 读到旧路由数据，说明正确性门禁必须覆盖慢 rank。

建议顺序为：**采用 nccl-tests/NCCL 查询与日志证据 → 适配只读通信专家 → 补有真实消费者的受限多节点 runner → 适配 MSCCL++ 搜索子模板 → 按已有训练框架比较 MoE 后端 → 有明确拓扑收益假设时增加合成分支。** AutoCCL 需独立 runtime 验证后进入可选分支；MCCL、双 RL Agent、Lagom 暂作设计来源。当前训练 preset 仍是只读 proposal-leaves，不能因新增说明或静态子图就宣称已执行这条流程。本轮所有收益、运行兼容、故障恢复与成本估计均未由 Ergora 实机验证。

[mscclpp]: https://github.com/microsoft/mscclpp/tree/0a6be3e10f43dbbda29bf23dbe9fd6c9964884d0
[mscclpp-bench]: https://github.com/microsoft/mscclpp/blob/0a6be3e10f43dbbda29bf23dbe9fd6c9964884d0/python/mscclpp_benchmark/bench_collective.py
[mscclpp-quick]: https://microsoft.github.io/mscclpp/quickstart.html#python-benchmark-and-tuning
[autoccl]: https://github.com/gbxu/autoccl/tree/63acb15c124400f94f1201127c1d06b35f90e757
[autoccl-license]: https://github.com/gbxu/autoccl/blob/63acb15c124400f94f1201127c1d06b35f90e757/LICENSE.txt
[autoccl-paper]: https://www.usenix.org/conference/nsdi25/presentation/xu-guanbin
[msccltools]: https://github.com/microsoft/msccl-tools/tree/030a750fc56e03fb863ffe48268672d84d4cdc7b
[taccl]: https://github.com/microsoft/taccl/tree/426bd1e30b7a170713f04f4cf20ace57e8c07251
[teccl]: https://github.com/microsoft/TE-CCL/tree/c128bf241e5b8bf6ce816b2fe5b8000baacb7c44
[optccl]: https://github.com/ml-collectives/optccl/tree/dc54db8ad0fbd03f9a2e409369c69a2235db29ea
[optccl-paper]: https://dl.acm.org/doi/10.1145/3789240.3829207
[forestcoll]: https://github.com/liangyuRain/ForestColl/tree/d7bd6a94e443e218aa26f319cbe22c70fe16921f
[forestcoll-paper]: https://www.usenix.org/conference/nsdi26/presentation/zhao-liangyu
[tacos]: https://github.com/astra-sim/tacos/tree/1811f1fb96e6bfb08965f3b94458a52307ca9efc
[tacos-paper]: https://arxiv.org/html/2304.05301v3
[deepep]: https://github.com/deepseek-ai/DeepEP/blob/f6aa38fe06cd4a0489e7730365d4e0114970a2f3/README.md
[hybridep]: https://github.com/deepseek-ai/DeepEP/tree/4e890fd19a3a52f23cc7bd38a0d9b0b1276f70d6
[hybridep-doc]: https://github.com/deepseek-ai/DeepEP/blob/4e890fd19a3a52f23cc7bd38a0d9b0b1276f70d6/docs/README_Hybrid-EP.md
[ncclep-root]: https://github.com/NVIDIA/nccl-extensions/blob/3401dea13534bc24ca827fe6e671f1edcf51d9a0/README.md
[ncclep]: https://github.com/NVIDIA/nccl-extensions/blob/3401dea13534bc24ca827fe6e671f1edcf51d9a0/nccl_ep/README.md
[nccl]: https://github.com/NVIDIA/nccl/tree/ad2d192c1f279aefcaf340f67e07880b65a1116b
[nccltests]: https://github.com/NVIDIA/nccl-tests/tree/afd59abab774a6a4b492eb344bd0c845a0b7bb4d
[nvshmem]: https://github.com/NVIDIA/nvshmem/tree/eaf955fd938eefbdb17ec607ee11b71493f95959
[uccl]: https://github.com/uccl-project/uccl/tree/52d4184c89deb5631be6dac6a9b1c40896c9e26e
[rl-agent]: https://arxiv.org/html/2611.10984v1
[mccl]: https://arxiv.org/html/2610.17091v2
[lagom]: https://arxiv.org/html/2602.20656v1
[ras]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/ras.html
[nccl-env]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html
[bridge-overlap]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/communication-overlap.html
[bridge-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-moe-comm-overlap/SKILL.md
[mcore]: https://github.com/NVIDIA/Megatron-LM/blob/a7a6d2225700a8ee701453288894501d868c6bd4/megatron/core/transformer/moe/fused_a2a.py
