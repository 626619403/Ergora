# D2-B2g 集群／恢复方向独立评审（r1 初审／r2 复核）

日期：2026-11-13。评审者：Codex，fresh-context 独立评审会话 `cluster_directions_review`；r2 由同一评审者同片复核。先读原始要求、实际差异及新增定义，再读作者计划、交付和证据叙述。遵循项目 AGENTS、maintainable-project-delivery 及 independent-review brief；分别评估需求合规和可维护性。

## 结论

|轴|结论|开放 finding|
|---|---|---|
|需求合规|r2 通过；SP1 的措辞、资源身份和受影响新验收原件已复核|0；SP1／P3 关闭|
|可维护性|通过；已检查范围内无可执行 finding|0|

本片本地出口可关闭，需求／可维护性开放 0／0。普通提交／推送、精确远端身份及该候选自己的完整 CI 尚开放；旧候选 CI 不构成本片通过证据。真实集群启动、原生归因器、取消／恢复、GPU 训练及完整 native 内部模型流程继续属于后续验收。下文保留 r1 初审依据，并在 r2 复核节记录修正版结论。

## r1 评审身份与范围

基线为 `9c84b088146e11eb45bb8c2065c9091526297789`，分支为 `refactor/architecture-foundations`。开始核查时 HEAD 等于该基线，`baseline-identity-r1.json` 的初始 status 为空。候选为未提交的 r1：冻结清单 `.ergora/checks/optimization-cluster-directions/review-r1/manifest.json` 的 SHA-256 为 `830f82863be7dc49f7c62956769e66fd9625c1692b5173316f1497f0866ddb57`；13 个工作区文件与 `files/` 冻结副本的长度、SHA 均逐项一致。原 tracked diff 为 14,272B，SHA-256 `fb812ba69098a4511a797a811ff2ed69710509242596379411a7400cbd9d46e0`，与独立取得的基线 diff 相同；未跟踪文件纳入上述清单。

完整检查的候选文件为：

- `README.md`
- `docs/PLAN.md`
- `docs/TEMPLATE_WALKTHROUGHS.md`
- `docs/TRAINING.md`
- `docs/plans/2026-11-13-specialist-presets.md`
- `docs/plans/2026-11-13-optimization-cluster-directions.md`
- `docs/delivery/2026-11-13-optimization-cluster-directions.md`
- `docs/delivery/evidence/2026-11-13-optimization-cluster-directions.json`
- `src/ergora/data/presets/presets.json`
- `src/ergora/data/presets/workflows/ergora-opt-cluster-resiliency-proposal/workflow.json`
- 同根的 `instructions.md` 与 `context/cluster-resiliency.md`
- `tests/test_presets.py`

邻近检查覆盖 `workflow_definitions.py` 的导入、精确引用、结构继承、权限上限、预算与完整输入验证，`definition_bundles.py` 的存储读取，`task_mcp.py` 的固定资源投影和分页协议，CLI／HTTP 两个生产消费者，以及 analysis／measurement v2 和三位专家的既有定义、Skill／引用资料。原始资料限于本片的 15 份固定来源及其指定 R8 原件／回执／归档，没有泛扫其他验收目录。

## r1 finding 及处置

### SP1／P3：将 NSys 的已知限制扩成了整个 Nsight 产品族（r2 关闭）

位置：`src/ergora/data/presets/workflows/ergora-opt-cluster-resiliency-proposal/context/cluster-resiliency.md:12`，`excludes Nsight profiling`。

固定 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0` 的 [resiliency 原文第 43 行](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/training/resiliency.md#fault-tolerance)明确写的是 `Not compatible with NSys profiling`；本片保存的 `research/bridge-resiliency.md:43` 与原回执身份一致。原文没有据此声明所有 Nsight profiler 都不兼容。

可达场景：该 context 由三个叶共同继承，用户提交其他 profiler（例如 Nsight Compute）的诊断／恢复组合时，叶可能把整个产品族都当作已有明确禁用矩阵。r1 design 和 measurement 的原输出已经复述 `excludes Nsight profiling`，说明该范围扩张会传到实际提案。

最小修复：把限制准确写成 `NSys / Nsight Systems profiling`；其他 profiler 组合继续按实际版本另验，不反向推导 Nsight Compute 已支持。同步 workflow 中的资源 SHA，重核修正版包／输入身份及受影响验收；保留 r1 原输出，不将其改写为修正版证据。作者接受并修正；r1 初审时开放，r2 独立复核后关闭，见下节。

## r1 需求与可维护性判断

新增根只引用精确 analysis v2／measurement v2，形成 design、profile 并行结构与后续 measurement；catalog 按原 owner 安装，`execution_authorized` 仍为 false。单次调用只选一个叶，完整原前驱由操作方手动传入；文档没有把静态边或 join 描述为已执行实验图。20 条旧 catalog 保持一致，原 542 个产品中仅 catalog 改动，新增三个资源文件，没有修改共享 v2、执行 runtime 或依赖。

根的 write／shell／network 权限为空，既有编译器逐层核对权限并沿结构父链累加资料；真实原输入和 scope 也具有完整的所选结构祖先及专家 Skill 树，没有兄弟资源误继承。Agent 实现与模板仍通过既有定义／后端合同解耦。当前模板作为独立选择的配置接口有明确职责；CLI、HTTP 均调用原 `install_preset`，没有单用包装器、第二调度器、恢复账本、额外分派或冗余校验层。

方向合同覆盖实际初始化与唯一 rank 生成者，N×R 与 N×R×R 的条件区别，共享路径／容器映射，原 experiment／job／task／cycle 与 unknown 对账，首故障及全 rank 日志，原生诊断／建议与执行分工，持久 checkpoint／所有 rank 状态和下一 optimizer update／RNG／数据顺序／质量／总成本。NVRx 空日志的 restart-biased 结果、分析 exit0、MCP 仅返回结果、有限内存历史及 fixture 导入导出均未升级为真实恢复能力。内部模型的请求／路由／prompt 不自带完整 Ergora 父合同，完整材料、权限、出口、每次 route／retry 和总预算仍另行准入；native evidence／history／policy owner 未被替换。

既有方向测试只新增参数，继续从正式安装／manifest／输入接口检验完整继承、只读权限、固定版本及删库后恢复，没有另建测试框架或镜像实现。资料、计划、交付与公开投影区分了提案、实际测量和采用，也保留了本片未发布、CI 待验及 B3／C2 的开放范围。除 SP1 外，已检查范围内无其他需求或可维护性 finding。

## r1 独立执行的核查

以下均为只读本地核验；没有重新安装、运行模型或昂贵 suite：

1. **来源身份与语义。** 复算 15 份来源共 257,662B：8 份 HTTP 原件与原始回执逐字节一致，7 份 NVRx 成员直接从 SHA 已核归档读取比对；归档及原回执也核准。逐项对照 Slurm 主 Skill／复制模板、Bridge resiliency、NeMo Run executor／DAG／status、Submitit checkpoint，以及 Restart Agent request、空日志结果、CLI、MCP 和模型 prompt。SP1 来自该原文核对。
2. **非 editable 安装身份。** 独立复算 wheel SHA-256 `4e2e63f967b67fb32be3ce40d4ba5cc6a5a105edea02e8a79e3a848f453a4a92`；545 个产品文件在当前源码、隔离源码、wheel、安装目录间逐字节相同。wheel 553 文件及安装 RECORD 558 行逐项核 hash／长度；283 冻结文件及基线 reference manifest 相同；当前 README 与 wheel METADATA 正文一致。README 元数据调整前旧构建保留，未借其验收。实际被测参数文件与冻结候选一致。
3. **原测试记录。** 阅读安装版原 preset suite 的命令、隔离 cwd、600 秒监督上限、终态和完整 stdout：28 passed／110.41 秒，监督总时 112.764 秒。公开 stdout SHA 与原件一致。这是对已有测试原件的核查，不是本评审重跑测试。
4. **三叶原始链路。** 用安装版 `-I -B` 只读检查器重编译原 input；通过 SQLite 只读连接将 state run 与原 CLI 输出逐项对比，再核 input／task／prompt／stdin／protocol／scope／native receipt／stream／最终 result。scope 与固定资产树一致，每次 list 完整列举、read 连续 UTF-8 到 `next_offset:null`，三次各 6 份，共 18 份／44,675B；measurement 原 task 中包含 design、profile 两份完整原 JSON。三个 run 分别为 `416f616ae1c942d297c8f0420d91a75e`、`c164be570629428da50c872575108f60`、`7d64322c4cad4f1caf04b78b041faa32`，记录用时 61.347／58.592／50.083 秒；驱动内外上限为 240／290 秒。独立阅读三份原结果，measurement 的 `request-changes` 成立且未被当作恢复通过。
5. **自身模板与公开投影。** 只读核准结构审查原 state、input、stdin、protocol、原生最终输出及 packet；五全文共 45,908B，run `17a6118e2e764ee183c08067338f7d70`、28.629 秒、text-only／approve。其明确限于结构文本，不代替本次独立结论。公开投影的调用字段、来源／结果／审计／stdout／进程观察摘要 SHA 均与原件匹配；进程记录只证明一次限定命令行观察，没有全程清理或 OS 隔离升级。
6. **静态核查。** 独立 `git diff --check` 通过；13 个候选中的 Markdown 共 266 个本地目标、64 个锚点核查通过。未读取或复制 inference 配置或凭据值。

只读核验脚本的探索版本曾把 Skill 入口文本误当作完整资源树，并误用 read 参数名；根据既有 `task_mcp.freeze`／`read(path, …)` 合同纠正后，上述完整资产及分页核查通过。初次简化锚点算法未移除中文标点产生的五项也经原标题核对后消除，均非产品 finding。

## 未验范围与后续出口

没有执行 Slurm／NeMo Run／Submitit／NVRx，没有原生 job、实际全 rank 日志、归因器结果、checkpoint 持久化或恢复后的下一步、GPU／质量／性能及收益测量。synthetic 标签不是作业回执，32 是条件推导，三次 Codex 会话不是异后端复验；传输完整也不等于理解或正确性自动成立。本次没有重跑本地全 suite／七组 collection，也没有新提交、推送、远端或 CI 核查。

SP1 已由下述 r2 复核关闭；r1 成功检查仍保持 r1 范围。普通发布和该候选自己的完整 CI 分别取得原件后再关闭精确交付。后续 B2h／B2i 以及 B3 真实实验、C2 native 全部内部会话合同继续按原计划推进。

## r2 独立复核

复核候选仍基于 `9c84b088146e11eb45bb8c2065c9091526297789`，未提交／发布。`.ergora/checks/optimization-cluster-directions/review-r2/manifest.json` 的 SHA-256 为 `04e0ec1085a32a071319cd1f9a9434e0dbc9d1b5ba9ecefe3097423efc9807f9`；复核开始时 15 个文件均与冻结副本的长度／SHA 和当前工作区一致。范围为 r1 的 13 文件加本报告的初审版本及新 `docs/delivery/evidence/2026-11-13-optimization-cluster-directions-r2.json`。r2 tracked diff 为 14,239B，SHA-256 `806af1f368105be60e3696fc5aafdbe785fa3376e9aa3dc835ca5f80950874db`，与独立取得的基线 diff 相同。本次报告更新属于本片评审记账，不改变受验产品。

**SP1 关闭。** 独立比较 r1／r2 原文，产品仅将第 8 项收窄为 `excludes NSys/Nsight Systems profiling; other profiler combinations need their own version-specific evidence`，并更新声明 SHA。原有权限、预算、结构、共享专家、执行所有者与测试不变。新 context 为 8,905B，SHA-256 `bef050adbcc217f6e2f8b324781ecb94fa5a35e55ab94b1db5bfb360cf0ff306`，根 digest 为 `96c851ebc8aa6395109f1162e29d7de808dadb1e2cd04d71772917391b36438e`；与固定原文的限制范围一致，也没有宣称其他 profiler 已获支持。

本轮独立执行的只读核查如下：

- **新包与旧包差异。** 复算 r2 wheel SHA-256 `78befd7c4d3eda2901ace1415cc88e76d471d8332dbb8bdd69b724716889b5d4`；545 个产品文件再次在当前源码、隔离源码、wheel、安装目录间逐字节一致。两份 RECORD（553 个 wheel 文件／558 行安装 RECORD）、283 冻结文件及基线 reference manifest、非 editable 身份和当前 README METADATA 均核准。直接比较两个 wheel 的同名成员，仅 context、workflow 和 RECORD 改变；metadata 相同，符合 `r2-source-correction-identity.json`。六个 overlay 及实际被测参数文件也与冻结候选一致。
- **新原测试。** 完整阅读 r2 隔离安装命令、600 秒上限、终态和 stdout：原 28 项全部通过／109.49 秒，监督总时 110.960 秒；stdout SHA-256 `6d403d3dfdf8b1a755bc2790b95a150d41172478c40c774846bdd16f4ced83d3`。本评审没有重跑 suite。
- **新三叶完整链路。** 通过 SQLite 只读连接核 state run，使用 r2 安装版 `-I -B` 重编译每份原 input，逐项核准 local／state input、task／prompt／stdin／protocol、MCP scope／native receipt／原生 stream／最终 result。新 context 同时存在实际 stdin 和固定 scope；全部结构祖先和完整专家 Skill 树匹配，没有旧 context 混入。三次各 6 份资源连续 UTF-8 读到 `next_offset:null`，分别为 15,039／14,932／14,953B，共 18 份／44,924B。measurement task 逐字节包含两份 r2 完整原前驱，其 SHA 与审计一致；240／290 秒限制保持。

|r2 叶|原 run|记录秒数|独立阅读原结果后的判断|
|---|---|---|---|
|design|`326c6d03d3174c4daa34eca5649902d6`|64.748|条件 32-worker 算式、原身份 unknown、checkpoint／恢复缺项保持|
|profile|`f3e329cb56e642018662f0977e1b80c1`|59.540|准确限定 NSys；没有把建议、框架引用或路径声明当成执行证据|
|measurement|`1314f65611be4d3b97d775f439f15181`|52.497|准确限定 NSys，完整接收两前驱，保留 `request-changes` 和原提交对账优先|

- **投影与历史边界。** 新公开投影 SHA-256 `a4cb8eebb3bb8140efe8aeea9dac9b54516602204f63ade6b8be227f75cb8040`，其调用字段、15 份固定来源、原 audit、stdout 和进程观察摘要 SHA 与原件一致。r1 公开投影与 r1 冻结副本相同，旧 wheel、audit、三叶 stream／result／native receipt、结构审查摘要及测试 stdout 的原有 SHA 均保持。r2 投影明确以 `historical_r1_self_review_before_source_correction` 记录旧五全文结构审查，未声称它审过修正后字节。一次限定 `/proc` 观察匹配 0 的范围也没有扩大。
- **完整文档和静态检查。** 对照 r1／r2 文档差异、计划节点、交付和两个投影，已准确区分旧证据、新验收、独立复核待办与尚未发布／CI 的状态，没有借旧检查或历史 CI 关闭新候选。复核开始的 15 文件共 267 个本地目标／64 个锚点通过，`git diff --check` 通过。没有读取或输出 inference 配置凭据，没有运行新模型、安装、suite 或执行集群动作。

r2 需求合规和可维护性两轴通过，开放 0／0；本地出口可关闭。普通发布、精确远端身份及该候选自己的 CI 仍须后续单独核准；上节所列实际集群／恢复／native 内部模型未验范围全部保持。
