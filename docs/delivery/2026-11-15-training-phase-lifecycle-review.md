# B3.3c1：非阻塞 phase 生命周期独立产品审查

日期：2026-11-15。审查者：`training_phase_lifecycle_product_audit`，新的 fresh-context 独立上下文，未参与 c0 设计或 c1 实施。先读原始要求，再固定候选并追实际 owner／caller。已读根、`src/ergora`、`tests` 的 `AGENTS.md`，组件执行／检查协议、`maintainable-project-delivery` 独立 brief，以及 `ergora-codebase-quality` 的三份参考。

**最终本地结论：需求符合轴 approve；结构维护轴 approve；开放 0／0。** 在下列固定范围内没有可证实的产品或维护性 finding。结论形成于原 24 项安装回归与原自身模板均返回之后；普通发布、前置片及本片自己的 CI 仍各有后续门禁。

## 固定身份与实际范围

实施基线为 `6c7e9d924f822e60a54ce8c0686a56758ae0359a`，分支 `refactor/architecture-foundations`。原始要求为 `.ergora/checks/training-phase-lifecycle/raw-requirements.md`，SHA256 `1faca23260662d39deac6e281803aec67da38ad244b60d9ebdbec8bfe9920b42`。

固定候选为 `.ergora/checks/training-phase-lifecycle/product-scope-r2/scope.json` 的 10 份完整文件，清单 SHA256 `5657f03c5a1225149863d55ee75ccd9cf43875a6cce09978e8db1354c049d4c9`。已逐份核大小／摘要，读取 tracked diff 和新文档全文；tracked diff 为 `.ergora/checks/training-phase-lifecycle/product-r2.diff`，SHA256 `5cdda0e6a7f817dd77aaab9b409077b9595fb91170dfa987bea2e4ffa6f59ee8`。

|产品／测试候选|SHA256|
|---|---|
|`src/ergora/reference_training_budget.py`|`559097bb1ad33cc2b51456e5cc4a3c1221e3cbf71236e2a3632201a09179469a`|
|`tests/fixtures/training_budget_client.py`|`b7404093cb886550f7831f13c163afbf9cdf2114d9d9b6d9bd347492f8d2ee5b`|
|`tests/test_training_submission.py`|`97a4f626f94d41c0cbc85d38dbe8fe1e83a2c6ac0d3f52ffcc82cd1385feb5bb`|

其余七份为 `docs/PLAN.md`、`docs/plans/2026-11-15-training-managed-execution.md`、`docs/delivery/2026-11-15-training-managed-execution.md`、`docs/delivery/2026-11-15-training-managed-execution-plan-review.md`、`docs/architecture/current.md`、`docs/architecture/reference-boundary.md`、`docs/delivery/2026-11-15-training-executor-protocol.md`。固定原件保存了检查当时仍在运行的历史状态；本报告单独核实随后返回的原结果。后续状态同步不改变本节候选身份。

唯一产品改动仍在原 `_BudgetPhase`；无新增产品模块、runner、执行权限、owner schema、持久 attempt／ack／stopped 或模板。原 `BudgetedStart.own()` 仍按 monitor／fence／cleanup／publish 串行调用，c1 交付可交错监管的低层生命周期。

## 需求符合判断

[原 phase owner](../../src/ergora/reference_training_budget.py) L67、L128、L160、L198、L229 的实际调用链符合本片约束：

- 父侧构造仅使用已核 `budget.folder` 和固定 mode／UUID 相对路径拼接，不再调用 `budget.path → _Submission.path → safe_file`，也不 mkdir、打开诊断文件或读 helper 输出。真实路径检查、目录及 stderr 文件初始化在 S 内。`expired()` 沿原共享 clock，父侧观察限于时钟／proc；原 intent、slot、queue、schema1 与取消／fence／result owner 未分叉。
- `start()` 在任何请求字节发出前设置三条非阻塞管道。selector 配置失败时只终止并等待尚未读到 payload 的子进程、关闭管道及 selector；worker 先 `json.load(stdin)` 才进入 phase，因而此收尾没有业务子树。启动失败的 stderr 持续排空、最多保留 65,536 字节，并能成为 unknown 的诊断原因。
- `poll()` 每次处理有限管道事件，保留实际短写 offset，接收原完整身份与顺序绑定的两帧。异常、缺损、超期和未完整输入不变为成功。只有已接收有效 stopped 帧且 total 耗尽时才允许 kill S；此前 TERM 只请求原 safe reap。
- S 仍只通过 [processes.run](../../src/ergora/processes.py) L102 的 `supervised=True` 回收直接 helper 与被收养的新 session 后代。run 返回后才发 stopped，之后仅直接读取 helper 结果及发 result，没有后续 spawn。c0 的“先 stopped 再生 publisher”问题在当前 c1 顺序中没有出现；c2 的持久停止发布仍未实施。
- 原同步 `run()` 复用 start／poll／finish；`finish()` 可为单一同步调用安全等待。原 [isolation fixture](../../tests/fixtures/training_budget_client.py) L73 则在同一父中交错 poll 两个 S，先向全部剩余 peer 请求停止，再轮询全部，最后只 finish 已观察终止者。监控完成时受控 fsync peer 仍活，父 subreaper 为 0，最终捕获进程均停止；父 observations 路径查验故障接缝也实际经过。

## 结构维护判断

新增四个生命周期方法都留在已有私有 `_BudgetPhase`，隐藏同一管道与资源寿命；原 `BudgetedStart.supervise()` 是当前生产入口，未虚构跨文件复用。它们是本 owner 的完整私有算法分解，保留 `run()` 让原消费者继续使用同一实现；没有独立 transport 框架或第二份清理算法。

新增状态分别对应短写、外部 stop 请求、一次 TERM、已退出观察和有界诊断。启动异常处理保护真实的“已 Popen、尚未发 payload、配置 fd 失败”窗口；没有为未请求的参数或无效调用顺序添加层层守卫。原 fixture 用实际生命周期替换 ThreadPoolExecutor，新增断言确认 fsync 故障确实到达；未增加重复服务／测试文件或 CI 分组。已有原接缝覆盖完整帧、持有 reader、异常 S、跨 total 的取消／回收、fence／final 存储阻塞及恢复，测试价值与变化匹配。

## 实际核验

|核验|已核结果与实际范围|
|---|---|
|最终 r2 安装身份|wheel SHA256 `e66e1e5a73fc5bea6a2c4fc08a5cf349d26a88c7c7d0221531e6af9ed7a7cbb0`；独立逐字核源码／wheel／core／SDK 各 650 文件，唯一产品变化为原 budget 模块；core 无 Temporal，SDK 1.34.0；原依赖检查 exit0。|
|原参考与测试输入|原 283 文件逐份对基线 Git blob 相同；174 份 tracked 安装测试／examples 与冻结清单及当前文件逐字相同，kernel 专家与模板保持。|
|最终原安装回归|`24 passed, 80 deselected in 495.27s`，外层 496.326947 秒；XML 24 项、失败／错误／跳过均为 0，stderr 为空。含原四 mode、slot／owner／clock、两种 final 阻塞及全部原 phase 故障接缝。|
|真实 phase 原件|受控 fsync marker、peer 存活／父 subreaper 0、完整 786,432B 输入及其 SHA 均核过；reap 完成时 total 剩余 `-0.539839` 秒；这些场景捕获的 9 个进程身份现均停止。|
|完整安装架构边界|16 passed／0.44 秒，外层 1.217 秒；固定原 suite，未另跑矩阵。|
|真实本地控制旅程|54.635 秒；九次实际 CLI 为一次预期 core 不可用和八次成功。核过全部原输出 SHA、同 run 的原取消、四个授权原件保持、request SHA、第二候选无 request／无 started、九个捕获身份已停、服务 socket 消失及原端口收尾记录。|
|自身原结构模板|原 `ergora-structure-review@1.0.0` 的实际 Codex 54.2644 秒，外层 56.7856 秒，两轴 approve／开放 0／0。独立确认 19 份全文 268,198B 与三个祖先资源进入实际 stdin，prompt 字节一致；仅供应文本审查。|
|本 reviewer 短探针|最终 installed core：240,661B 经 769 次短写、碎片两帧及 150,000B 结果、超量 stderr 排空且仅留 64KiB、可用 startup unknown 诊断、未发 payload 的 selector 失败及 Popen 失败收尾，四项全过；3 个最小替身子进程均 wait 回收。无业务 helper／服务。|
|文档链接|固定七份 Markdown 的 211 个本地链接无缺失目标。|

源码 r1 的 peer 单项 `1 passed／31.05 秒` 仅保留其原身份；最终 r2 的同一接缝已在上述 24 项内再验。第一次 r2 构建入口在 Popen 之前因不存在解释器而 FileNotFoundError，原 `build-r2-launch-failed.*` 保留；它不是产品执行失败或修后通过证据。

## 原件与后续门禁

以下为本地 ignored 证据，未随 Git 发布；以代码路径和 SHA256 识别：

- `.ergora/checks/training-phase-lifecycle/product-audit/originals-audit.json`：`2c7c1b256ef26de4e8d26e43d988178fe51eada6f101ca267b2c311c7d055021`。记录独立字节核验、原回归 case、真实 marker／PID、自身 stdin 校验及所读原件的逐份摘要。native 位置经 `native-location-r2.json` 定位，不将宿主路径写入公开记录。
- `.ergora/checks/training-phase-lifecycle/installed-regression-r2.json`：`60d28e096c4a96859c38158cbf8097c1d843e048f9d9793f6f3a911f80e721f4`；其 XML：`1a6a4cf7f8ae4344746a9051becf90f74288a02dd9c3a0dcf4a92e92f4eb5d30`。
- `.ergora/checks/training-phase-lifecycle/self-review-r2-codex/original-result.json`：`487188320a1c127267eed032429696a909d65e99e910372cdfefa13ca3a22604`。该模板结果没有认证私有原件、安装、runtime 或 CI。
- `.ergora/checks/training-phase-lifecycle/product-audit/lifecycle-probes.json`：`e098184f9207de40101c0711caff269416da39b70a7fcc030b9689d74b3590d2`；探针源码：`ddce4ea2470732e3307d51cd6d520ea039a19352437caa02534b0ca908371d79`。
- `.ergora/checks/training-phase-lifecycle/product-audit/links.json`：`c77c028ef9a7c503bd20c3d517e9fa5032bb507d6754a91282a88c51017840fa`。

本 reviewer 只读必要源码与既有原件，运行上述便宜替身探针，写本报告及 ignored `product-audit/`；未安装、运行昂贵矩阵／模型／训练、修改产品、提交或推送。

前置 B3.3b 的固定发布／自己的 CI 由其原 reviewer 续核，本报告未认证 CI43674493548。c1 仍须在前置门禁闭合后完成精确普通发布、自己的适用 CI 与本 reviewer 的固定发布续核；本地 approve 不代替这些结果。c2 的显式执行／出生能力／持久生命周期／原生训练 runner、自动循环及实际训练／GPU／质量／性能不属于本次结论。kernel 专家继续保留在 v3 优化路径，原训练、控制、实验与批准权威保持原归属。

## 作者最终状态同步补核

本地产品终核后，同一 reviewer 完整比较了作者对以下三份文档的同步。改动只登记实际返回的 24 项／自身模板结果与对应原件摘要，修正 6c7 实施基线、当前活动片及 c0 r2 已通过状态，并保留前置 b／本片发布与各自 CI 待核。产品／测试仍逐字等于 r2，原 scope 其余七份未变；新增三份文档的 147 个本地链接无缺失，三份改动 Python 的 AST 与完整 tracked diff-check 通过。无新增 finding，两轴本地 approve／开放 0／0 保持。

|补核文档|字节|SHA256|
|---|---:|---|
|`docs/PLAN.md`|57587|`17028da182e54547bac74573bbc2cb5a8e76296df465f5b5cd042333bfb798c6`|
|`docs/plans/2026-11-15-training-managed-execution.md`|20458|`1b887f562093027f09a833d7dd55c7e7d18855c962215bd01553c003b7d464f7`|
|`docs/delivery/2026-11-15-training-managed-execution.md`|8376|`03512cd08e20608df82b0a61d76729e127417a3d20503a463aff90c4d18fe0df`|

补核原件为 `.ergora/checks/training-phase-lifecycle/product-audit/final-docs.json`，SHA256 `47699f0abb08a794e2dd9f71f2d295fae07ddc7048bb512c6ec610f33901eb8f`；完整差异为同目录 `final-docs.diff`，SHA256 `91dcebdd394b0c6f675da6c03c2cbc76dd20f3dca38eece171e8b0d8524d9950`。未重跑无变化产品，也未将后续发布／CI 预记为成功。

## 最终 staged 范围与前置闭合补核

同一 reviewer 已独立核固定 tree `d43f93b67340ccf78b31ef9502df16eaaf256ecb`。HEAD 仍为原 6c7 基线，index 与给定 tree 完全一致，补写本节前工作树也与 index 一致。相对基线恰为 12 份文件：原十份候选，加前置 b 的独立终核报告及本报告；12 个 Git blob 的完整字节／SHA 与原 checker 相同。三份产品／测试继续逐字等于已审 r2，三份 Python AST、223 个固定 Git tree 本地链接和完整 staged diff-check 均通过；data、scripts、CI 与 `.gitattributes` 没有变化。

状态增量完整比较了原最终三份进度文档、前置 b 交付及其独立报告。增量只登记原 c1 本地两轴通过与前置 b 的固定发布／自己的 CI 已闭合，继续保留 c1 普通发布、它自己的 CI 与固定发布终核待办，没有加入 c2 产品、权限或训练／GPU 收益主张。**需求符合轴 approve；结构维护轴 approve；开放 0／0 保持。**

前置 b 以其原 reviewer 的固定报告与原件核闭：报告 15,572B，SHA256 `d4d114be71674972bf08e07d94169eef3b070c2dd1fb4802fc9c11b0e2e9671f`；`.ergora/checks/training-executor-protocol/product-audit/ci-publication-r1/final-ci-audit-r1.json` SHA256 `71e5941ac25803be20ed8312f00d1994de67389e5c53ff68aca4e034200c7c81`。已核其 commit 为完整 6c7、run `43674493548`／attempt 1、八个 job 与 30 个唯一必要步骤均 success、两轴 approve／开放 0／0，并核所引用 terminal summary、Actions HTML、原件 index 的字节／摘要。本次读取原 reviewer 的终核，没有重新联网认证前置 CI，也没有声称取得完整日志／产物。本报告前节的前置待办保留其当时状态；该前置现已闭合，c1 自己的发布／CI 仍待。

原 staged checker 为 `.ergora/checks/training-phase-lifecycle/publication-staged-r1.json`，SHA256 `ef3744b1c869af3fe6d395db6ba9c8f82a975d475329f31f74d86e1aa222b37c`。本次独立原件为 `.ergora/checks/training-phase-lifecycle/product-audit/staged-r1/inspection.json`，SHA256 `38743b3ad6f4244b18d993a77dbb81d6afcb3ac513f2363a872e4d7231f82ce2`；同目录 `state-delta.diff` SHA256 `653fdabfad81eca20174b2aad93937345f9e1284799bccdb029031f1a387f94a`。本节新增字节须纳入作者最终 r2 stage；其余 11 个已审 blob 保持，再记录静态身份并按原授权普通发布。未重跑无变化产品、安装或业务执行，尚未认证 c1 提交／远端／自己的 CI。
