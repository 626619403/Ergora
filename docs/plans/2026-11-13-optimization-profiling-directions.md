# B2e：Profiling 与内存快照方向

日期：2026-11-13。承接 [D2 专家计划](2026-11-13-specialist-presets.md)与 [R7 调查](../research/2026-11-12-optimization-profiling-agents.md)。产品基线为 `2c93ef687f344138127fd1d9018c36ef003352e0`，其自己的 CI43413954876 八 job／30 必要步骤及原独立终核均通过；实际实施起点 `e85b1e6eb38ac568142b2a73b9ca3bae1d248f8a` 只增加五份同片结案 Markdown，普通推送与作者 SSH 完整 Ref 均已核准。两根／catalog／原参数表与两手册、独立安装及六真实叶已核，自身与新独立两轴通过，SP1/P3关闭／开放0／0，本地出口完成；普通发布和自己CI仍开放，不继承旧候选的CI。

## 范围与归属

新增 `optimization-profiling` 与 `optimization-memory-snapshot` 两个只读配方。每个根保存 workflow、instructions 和完整原创方向 context，精确复用 `ergora-training-analysis@2`／`ergora-measurement-review@2`及既有 designer、analyst、measurement reviewer。CLI／HTTP／页面仍使用原定义库和编译器；单次 `run-input` 只运行一个叶，measurement 手动接收完整原 design／profile 结果。

本片不新增 Agent 类、schema、parser、collector、调度器、结果账本或 GPU 依赖。不执行 pickle，也不将 Nsight 二进制或第三方 MCP 随包分发。实际原报告采集、解析、缓存／依赖安装、设备申请、停止恢复及采用继续由各原所有者负责；父权限上限和完整祖先资料继承保持。

新增六个数据文件、catalog 两条及现有方向参数测试两项；原十六 catalog 条目、共享 v1／v2、530 原包文件除 catalog 外和 283 冻结文件保持。同步训练手册及模板旅程，不增加测试函数或 CI 分组。

## 固定资料与方向合同

沿 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`，十一份 HTTP200 原件及 SHA 已保存并核准：Nsight Skill／pitfalls／SQL recipes、snapshot Skill／common／compare／plot、训练 config／setup／train_utils／profiling。复用 R7 的市场调查，不重做广泛检索。产品资料是本项目原创综合，来源 URL 只标出处，不能代替完整资源或授权。

|方向|必须保留的区别|
|---|---|
|Profiling|原报告／工具／schema／rank／step 身份；采集、离线解释、独立评价分开，查询可能写缓存或安装依赖；稳态 ROI／profiler 边界及扰动；全部 supplied ranks／PP stage 与时钟不确定性；裁剪区间并集和时间守恒；exposed 与真实 producer 阻塞分开，eventSyncId／graph join／source attribution 逐项核；缺计数器是未知；同一 profiled step 的有限机会只算上界，不当收益。|
|Memory snapshot|受信来源及 pickle／RAM／文件事件预算归 parser owner；真实模型构造前记录、selected ranks、100k 上限、end／OOM 路径；memory history 与两个 profiler 开关分开；dump segments 与 retained history 分开，allocated／active／awaiting-free／inactive 及设备总占用口径；核 first-active-device／多设备范围；历史丢失／unmatched frees 下 baseline／peak 不确定；step／warmup／graph pool 对齐；source table 不强凑 peak，CDN plot 不称完全离线。|

每个根均须输出支持的观察、假设、缺失证据和最小下一步，保留 unavailable／incomplete／failure／no_gain／noise／unknown。实际干预仍需全 rank 数值／梯度／optimizer／质量、checkpoint／RNG／数据顺序恢复及未 profile 配对端到端评价，文本审查不批准采用。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|B2e.0 前置|通信精确候选自己的 CI、独立终核、五 MD 结案与远端 Ref|完成|
|B2e.1 资料与数据|两只读根与完整 context、catalog／原参数表／两手册同步，原包保持|十一资料原件／SHA已核，两根／catalog／两手册／原参数表已实现；原十六条保持|
|B2e.2 安装与合同|新 Python3.11 非 editable 包 source／wheel／installed、两 RECORD／283、原安装 preset suite；正式七次 collection 核新全集与六组并集|Python3.11非editable536／两RECORD／283通过；安装25项／100.09秒；1713全集＝六组并集、交集0，仅collection|
|B2e.3 真实叶交接|两方向各三次独立 task-MCP 调用，完整祖先 UTF-8 读取至末页、精确 input／stdin／scope／native／结果与原前驱全文|六叶均成功，共36资源75,319B连续UTF8完整链／手动原前驱核准；profiling仅批准补证据方案，snapshot要求补实验条件；无parser／GPU测量|
|B2e.4 审查与发布|自身原结构模板接收八份完整产品／测试文件；新 fresh-context Spec／Standards、修正复核；普通提交推送及自己完整 CI／独立终核|自身26.700秒approve／八全文51,307B与三资源核准；新fresh独立两轴完整原件及文档通过，SP1/P3关闭／开放0／0，本地出口完成；普通发布及自己CI开放|

真实调用 fixture 只包含明确 synthetic 文本：10ms 窗口的 compute `[0,4]`／`[6,9]` 与 dispatcher `[2,6]`；无 dependency／clock／其他 rank timing，不可推出 recoverable critical path。两份 toy snapshot summary 区分 active／awaiting-free／可复用空间，但没有原 pickle、parser、历史／step marker／设备总占用。审查应指出这些缺项，不能把 fixture 算术当真实 GPU／parser 验收。每调用 240 秒、外层 290 秒；失败保留原件，必要重试另目录，成功叶不无故重跑。进程核验只报告实际观察范围。

本片以后继续 recipe／model verification、cluster resiliency、kernel／low-precision；B3 真实原 manifest／runner 交接和 Forge 内部原生循环各自独立验收，不由资料配方提前关闭。
