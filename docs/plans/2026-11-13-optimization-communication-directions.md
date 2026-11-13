# B2d：通信重叠与 MoE dispatcher 方向

日期：2026-11-13。承接 [D2 专家计划](2026-11-13-specialist-presets.md)、[R3 通信研究](../research/2026-11-12-optimization-communication-agents.md)及已审查的 B2c 三方向。产品基线为普通提交 `9250bf880c07e13b0aa2af9ba49f612737082a50`，实际实施起点为只增加五份CI结案Markdown的 `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`；实现开始前先核该候选自己的完整 [CI](../delivery/2026-11-13-publication-status.md)，该候选现已八job／30必要步骤成功且独立原件终核通过。三个只读配方与说明、独立安装、九次成功叶及原件审计已完成，原网络超时保留；完整fresh双轴终核通过，ST1/P3关闭／开放0／0，本地只读提案出口完成；普通发布及本候选自己的CI尚待。

## 最小范围与归属

仅新增 `optimization-tp-dp-overlap`、`optimization-moe-dispatcher`、`optimization-moe-overlap` 三个可选择的只读配方。每个新包沿 `data/presets/workflows/ergora-opt-<slug>-proposal/` 保存 workflow、instructions 和完整离线方向 context，复用精确的 `ergora-training-analysis@2` 与 `ergora-measurement-review@2`。design／profile／measurement 叶复用现有专家；两个 MoE overlap Skill 指向共享实现，综合成一个方向，不拆重复 Agent。

不改变原 catalog 条目、v1／v2 专家、manifest 协议、执行器、阶段调度或训练账本。CLI／HTTP／页面仍从现有定义库读取新配方；`run-input` 一次运行一个选定叶。前驱全文由操作者明确交接，静态边不自动执行原生通信或训练任务。

## 固定资料与实际实现核对

复用 R3 的市场／论文调查，不重复整轮检索。新增资料采用 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0` 的四份通信 Skill、`comm_overlap.py`、`flex_dispatcher_backend.py`；已保存六份 HTTP200 原件及内容 SHA。产品只写本项目的方向合同与固定来源，不把本机 Skill 目录或 URL 清单当作已读取的资源。

|方向|必须覆盖的区别及证据|
|---|---|
|TP／DP overlap|请求值与最终生效值分开；TP 的 size／sequence parallel／TE 门槛和 PP/VPP 选择；真正 Megatron DDP／distributed optimizer 的适用路径、bucket 的参数数量单位、混合精度和 launch 插件字段各自归属。新 optimizer 可能保留 Core bucket／gradient reduction 设置；DP1 仍可能跨 CP ranks 归约，不机械套普通 DP 默认值。用实际 critical path、全 rank 正确性与配对 step 测量判断争用和收益。|
|MoE dispatcher|固定实现识别 `deepep`、`hybridep`、`ncclep` 与显式 `None=alltoall`；配置与目标 GPU 校验分开，不支持的最终后端报错而非自动替换。Skill 较旧的 skip／fallback 说明及二后端表不能覆盖这一源码事实。核实际 package／ABI／框架消费者、设备和 NVLink／RDMA 拓扑；不能把当前 DeepEP master 当作与旧 Core `Buffer` 消费者兼容。强制负载均衡属于单独的 benchmark 语义，生产自然路由须独立验证。|
|MoE overlap|普通 EP overlap 与 delayed wgrad 分开；后者不能由单个 harness helper 同时开启后再归因给前者。核实际 EP／expert／dispatcher／dtype／torch、PP/VPP、重计算／shared expert／MTP 约束；延迟 wgrad 与 TE、graph scope、静态梯度累加及 attention bias 的匹配条件分别核。两个 Skill 共享同一原生实现；各版本阈值只是必要条件。|

三方向均要求固定实际 mesh、rank↔GPU↔NIC、流／事件／buffer 生命周期、全 rank 前进性与取消恢复、损失／梯度／optimizer／checkpoint／质量及未 profile 的配对端到端测量。上游案例只算来源报告；缺实际环境、初始化或报告保留 unknown，不把导入失败、配置落盘、rank0 日志或微基准当作训练收益。

## 可验收节点

|节点|出口|当前状态|
|---|---|---|
|B2d.0 前置|9250bf8 自己的 plan、六 Linux／一 Windows 必要步骤和独立终核|已完成，自己的43402253789为Success，独立终核通过|
|B2d.1 资料与数据包|固定源码逐项核对；三个只读根／完整 context，catalog 与训练／walkthrough 使用说明同步，旧包字节保持|六资料原件／SHA和关键差异已核；三根／catalog／手册／原参数表已实现，保留十三旧catalog条目|
|B2d.2 安装与合同|新非 editable wheel 的 source／wheel／installed、两 RECORD、283 冻结；现有 preset 参数检查覆盖新根的真实失效面；旧定义和 manifest 保持|Python3.11非editable530产品／两RECORD／283核准；安装preset检查23通过／96.46秒；十三旧catalog条目和521原包文件除catalog外字节保持|
|B2d.3 实际叶交接|每方向 design／profile／measurement 真实独立调用，完整祖先资料及前驱全文进入实际输入、原件／进程归属收尾；缺实际测量时 measurement 明确缺证据|两轮共九成功叶／54资源96,303B完整连续UTF8及手动前驱原文核准；三measurement缺证据request-changes。原网络超时602.224秒保留；只重试该方向，设计精确input／prompt不变，终后进程观察无匹配；未做全程PID采样|
|B2d.4 审查与发布|自身原结构模板、fresh-context Spec／Standards，修正复核、记录／计划，普通提交推送及新候选自己的 CI|自身原结构模板35.619秒approve／十一全文54,212B，实际stdin／prompt／protocol60,445B和三资源核准；新fresh双轴完整原件／公开投影及文档终核通过，ST1/P3关闭／开放0／0，本地出口完成；精确发布／本候选CI待做|

实际实验继续归原训练 manifest／runner／perfctl 与批准所有者。多 rank 原生执行及可选 MSCCL++ 搜索等需要独立的真实消费者与设备验收；这三个资料配方不会自动接入通信库、重置预算或升级上游 pin。完成本片后按 D2 接 profiling／memory-snapshot 等后续方向。
