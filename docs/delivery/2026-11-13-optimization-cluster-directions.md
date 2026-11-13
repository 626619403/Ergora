# 集群／恢复方向子模板交付

日期：2026-11-13。按[本片计划](../plans/2026-11-13-optimization-cluster-directions.md)推进，基线`9c84b088146e11eb45bb8c2065c9091526297789`，开始时工作树清洁。范围为一个只读方向根、catalog及原测试参数，不增加作业执行、原生归因器或恢复系统。

## 当前状态

R8十五份固定原件257,662B及原回执／NVRx归档成员身份已核，新研究请求0。一个方向根、catalog、原测试参数与使用入口已实现；r1原件保留，SP1／P3来源措辞已修正。修正r2安装、28项及三叶原件已获同片独立终核，两轴通过、开放0／0，本地出口完成。普通发布／自己的CI仍开放。

现有共享专家、父资料继承、权限、预算与证据所有者保持；模拟启动／丢失回执／空日志／checkpoint入队资料只检查方案和证据辨别，不能证明真实集群或恢复功能。

## r1实现与安装

新增`ergora-opt-cluster-resiliency-proposal@1.0.0`的workflow／instructions／context三文件与`optimization-cluster-resiliency`条目，既有参数化测试增加一个方向。复用精确analysis／measurement v2与三位专家；没有增加运行器、调度器、Agent类、依赖或重启账本。原20条catalog和542旧产品除catalog外字节保持，283冻结参考文件保持。

Python3.11非editable wheel为`4e2e63f967b67fb32be3ce40d4ba5cc6a5a105edea02e8a79e3a848f453a4a92`；545产品文件source／wheel／installed一致，两RECORD通过（wheel553文件、安装558行），283冻结文件通过。首次构建的README元数据仍为基线版本，已在测试／模型调用前用当前README重建并安装上述wheel，旧未测构建保留。安装版原`tests/test_presets.py`为28通过／110.41秒，监督总时112.764秒，固定600秒上限未变。本片未另跑本地全suite／七组collection；精确新提交自己的完整CI另验。

## r1真实只读调用与证据审查

|叶|原run|秒|结果|
|---|---|---|---|
|design|`416f616ae1c942d297c8f0420d91a75e`|61.347|成功，32个潜在worker与期望8冲突；缺实际runtime，先保留原身份|
|profile|`c164be570629428da50c872575108f60`|58.592|成功，诊断建议与原日志／原生分析／恢复证据分开|
|measurement|`7d64322c4cad4f1caf04b78b041faa32`|50.083|成功；`request-changes`，原提交先对账，不批准重提或恢复|

三次调用各自240秒内层／290秒外层限制。原manifest／input／stdin／protocol／native receipt／stream／result已核，18次固定资源、44,675B完整连续UTF8读取到`next_offset:null`；measurement手动接收design和profile完整原结果，原SHA链保持。审计证明传输及调用记录，不证明理解或正确性本身；实际输出另行阅读核对。

审查识别了synthetic `2×4×4=32`的重复生成风险，但没有把配置算式当观测rank。Lost acknowledgement仍unknown，fixture标签不是job回执；空／degraded日志的RESTART／exit0不是重启授权；checkpoint仅入队不证明持久化或下一update恢复。缺少实际job／rank日志、全rank checkpoint、优化器／RNG／数据顺序及质量／成本证据均保留。Claude不可用后的用户授权Codex回退原因逐调用记录；三次独立会话不称异后端复验。调用后一次限定`/proc`命令行观察匹配0，不声称全程后代监测或OS隔离。

自身原`ergora-structure-review@1`以text-only审五份完整产品／测试文件45,908B，原run `17a6118e2e764ee183c08067338f7d70`，28.629秒、`approve`。完整文件及继承资料存在实际stdin已核；此判词只覆盖结构材料，不代替独立评审、来源／安装／模型原件核验或CI。

公开的[r1小型证据投影](evidence/2026-11-13-optimization-cluster-directions.json)包含固定来源／SHA、wheel、调用及测试身份；完整原件保留在项目私有验收目录，未公开配置、凭据或机器路径。B2h低精度和B2i独立kernel随后推进；B3真实实验与C2完整原生嵌套保持开放。

## SP1来源精度修正

新fresh-context评审发现，固定Bridge原文仅排除NSys profiling，r1 context第8项扩大为整个Nsight profiling；原design／measurement结果也沿用了该词。已明确改为NSys／Nsight Systems，其他profiler组合需要各自版本证据，未反向宣称Nsight Compute支持。resource SHA与根digest随正文更新，r1全部产物保持原样，不改写模型结论。

r2从同一基线重新构建非editable wheel，SHA256为`78befd7c4d3eda2901ace1415cc88e76d471d8332dbb8bdd69b724716889b5d4`；545产品／两RECORD／283通过，与r1仅context及其声明摘要变化（当前README元数据保持）。原28项suite通过／109.49秒，监督110.960秒；同一240／290秒预算下三叶全部成功。

|r2叶|原run|秒|结果|
|---|---|---|---|
|design|`326c6d03d3174c4daa34eca5649902d6`|64.748|只读方案，保留原身份／32个潜在worker矛盾及恢复缺项|
|profile|`f3e329cb56e642018662f0977e1b80c1`|59.540|准确限定NSys，实际启动／恢复／profile未验|
|measurement|`1314f65611be4d3b97d775f439f15181`|52.497|`request-changes`，准确限定NSys，原提交对账优先|

新原件链核准18资源44,924B完整连续UTF8与完整原前驱手动交接；根digest为`96c851ebc8aa6395109f1162e29d7de808dadb1e2cd04d71772917391b36438e`，context SHA为`bef050adbcc217f6e2f8b324781ecb94fa5a35e55ab94b1db5bfb360cf0ff306`。[r2投影](evidence/2026-11-13-optimization-cluster-directions-r2.json)SHA为`a4cb8eebb3bb8140efe8aeea9dac9b54516602204f63ade6b8be227f75cb8040`，一次限定调用后命令行观察匹配0。r1结构审查是原五文件的历史结构证据，最终产品由同片独立评审复核；不将旧模型／测试通过授予修正版。随后独立终核见下节；普通发布和自己的CI分别验收。

## 独立终核与本地出口

原fresh-context评审者已同片核准修正后的15文件快照、r1／r2仅两产品及RECORD差异、新包545／两RECORD／283、28原测试及三叶state／input／stdin／protocol／完整MCP／native stream／result链，18资源44,924B及完整r2原前驱、三原结果和公开投影均通过；267本地目标／64锚点与diff检查通过。SP1/P3关闭，需求／可维护性两轴开放0／0，[独立报告](2026-11-13-optimization-cluster-directions-review.md)记录原问题和复核范围。本地只读方案出口完成；普通提交推送、精确远端身份与该提交自己的完整CI待验，未借旧候选CI或原r1结果关闭。
