# b2b0：训练循环离线读取独立审查

日期：2026-11-15。审查者：fresh-context独立Agent `training_cycle_offline_reader_product_audit`。未继承实现对话；依据原始要求、实际源码、调用者和原始验收证据审查。权限限于只读检查及本报告写入，未修改产品／测试、安装、提交、联网写入或重跑昂贵suite。

|审查轴|最终本地结论|开放问题|
|---|---|---|
|需求符合性|approve：满足本片行为保持的原读取参数整理|0|
|可维护性|approve：依赖归属、真实调用迁移与验证范围适当|0|

结论仅覆盖以下候选和本地验收；不表示普通发布、前置CI或本片自己的CI已经闭合。

基线为`d1c728087423d85ed55f06010ec81e5e1d4b2fd1`，分支`refactor/architecture-foundations`。先审查`review-scope-r1.json`、对应冻结文件和`review-tracked-r1.diff`，终核更新后的`final-scope-r1.json`、`final-scope-r1/`与`final-tracked-r1.diff`。证据根目录为项目内私有`.ergora/checks/training-cycle-offline-reader/`。

最终八文件为：`docs/PLAN.md`、`docs/architecture/current.md`、`docs/plans/2026-11-15-training-cycle-stop-supervision.md`、[本片计划](../plans/2026-11-15-training-cycle-offline-reader.md)、[本片交付](2026-11-15-training-cycle-offline-reader.md)、`src/ergora/training_cycles.py`、`src/ergora/reference_training_budget.py`及`src/ergora/reference_training_worker.py`。已逐字核对当前文件、冻结副本及清单SHA；最终tracked diff也与当前Git差异逐字一致。`final-scope-r1.json`为1,322B／SHA256 `b1061e68f5a2a7318888aa07f338f8fab61a5a66bade45cdd913d0e3351a0a75`；`final-tracked-r1.diff`为24,236B／SHA256 `a1ee9a98fe02a976713b340d6f1cee00a52c08bdd1354057c3e00394d1f47a16`。本报告是审查新增记录，不在该八文件实现清单内。

已读取根、源码及测试`AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)、maintainable-project-delivery独立审查指引，以及ergora-codebase-quality的风格／模块／测试接缝参考。适用范围还包括[停止监管设计](../plans/2026-11-15-training-cycle-stop-supervision.md)、`state`、`registrations`、`training_execution_protocol`、v3／kernel定义和所选原测试／fixture。

需求核对结果：

- `training_cycles.py:182–262`原五私有函数只把`State.root`依赖表达为`home: Path`。独立从Git基线AST施加这五个参数及对应调用的预期机械变换后，三个完整模块均与当前AST相同；共核17／4／2处调用。公共API、原`State`构造／生命周期以及其余模块算法保持。
- `reference_training_budget.py:259`的`source`仍构造原`State`、加载完整记录、核binding／来源并返回原四元组；`permission`和固定父history仍经原owner。`reference_training_worker.py:27`仍在原native adapter／registry路径执行完整核对。没有遗漏其他生产调用者，也没有在本片把这些既有应用路径改成新的只读入口。
- `state.py:156`的构造确实解析home、创建目录、取得schema锁、打开数据库并可能迁移。原记录算法的下游`registrations.published_project`只读原journal／result；`_load`的schema2 ready路径调用`CycleAdmission.validate_lock()`时保持默认`synchronize=False`，只核现存普通空锁。五函数现在可由后继H直接复用，无须构造State、伪造State或复制校验器。
- 原读取容量、严格JSON、完整canonical／raw SHA、registration来源、ready身份／时间、原clock、锁及异常路径均未改。没有新增函数／类／产品文件、wrapper、registry、schema或分派；没有异步operation、fan-out、总Workflow或公开自动执行入口。v3仍通过`kernel`节点引用原kernel assessment／kernel专家；相关资源逐字保持。

可维护性核对结果：实际依赖仍由原`training_cycles`拥有，另外两个生产文件只传原`state.root`。无需新reader层或可替换接口；没有新增guard、assert、fallback、重复校验或tracked测试／CI。保留原测试接缝并用安装实际调用和原件读取共同验证，比为五个参数各加浅层测试更能覆盖本片风险。未发现需修正的产品或结构问题。

实际核验与证据边界：

- 独立重核652个产品文件：当前source、wheel、core site-packages及SDK site-packages逐字一致；原manifest SHA／大小一致。与完整Git基线相比仅原三owner变化，没有增删产品。wheel SHA256为`e0b0364c3d88bc4ded4e38339a4d5bf24567b51aa48003dd5b00641f32505f6e`。两份原reference检查均为283／PASS，依赖检查退出0；core无Temporal SDK、SDK环境为1.34.0。这些证明安装身份与完整性，不代表运行过全部产品能力。
- 177份测试／示例的当前源码、原Git基线、冻结副本及清单独立重核相同。原新SDK安装回归`installed-r1.*`终态27通过／57.10秒，驱动58.688秒；JUnit为27／失败0／错误0／跳过0，stdout与退出0一致。包括11个展开的授权／完整binding／来源／恢复／可见stop／排空／真实registry gate场景及完整16项架构。已读所选原测试及实际子进程fixture；未重跑该suite。
- 原core离线证据`offline-originals-r1.py/json`确实持有真实schema排他锁并禁止State构造。审查者另用实际core安装重复只读加载两份原schema1／2，额外禁止`State._open`和`sqlite3.connect`；原文件SHA清单、完整字节及目录集合均保持，不存在的home仍不存在。原故意`confirmation=1`损坏授权与`offline-originals-r0-corrupted.*`身份一致，独立重读仍按完整canonical SHA拒绝，未修复或换写原件。此项证明原读取可脱离数据库初始化，不授予重新授权、执行或停止成功。
- 自身原结构模板的`self-review-r1.json`及原result SHA一致，20.475秒／approve；独立核16份完整文件共427,107B确实存在于原prompt，且prompt与真实stdin逐字相同。原运行记录还核三个祖先资源；该回复明确只覆盖供稿，回归当时在途，不将其当作本次终态审查或异后端成功。
- `owner-closure-r1.json`记录本次1个原budget owner活匹配0、验收路径进程0；审查者另核该原owner完整进程身份已不活跃。没有发送信号或全机器无进程主张。最终`git diff --check`及变更文档本地链接目标检查通过。

审查中指出初稿交付仍写“当前只有计划与原码调查”，与后文实现状态冲突；作者已改为立项调查及下文逐步记录，并以最终scope重新供审。该记录问题已关闭，没有开放最低修正项。

本地片可以按原计划收束。普通发布仍受前置43d自己的准确CI终态及原独立门禁约束，本片发布后还需自己的适用CI；本报告未联网终核它们，也不转授前片批准。后继b2b1／b2b2仍须独立完成异步operation、冷inspect固定截止、spawn取消回收、具体owner并发通知和实际停止链验收。本片没有真实GPU、业务ML训练质量或性能收益验收结论。

## 固定发布终核

原reviewer恢复本上下文，对固定发布`877e1e4f7397731915c36b82f335efeaab3854dd`完成需求／可维护性两轴终核，均为**approve，开放0／0**。本次保留前述7,132B原报告为不变前缀，其SHA256为`176bc9a8d4fbb2a5ae043ff5ed6711abf34af0dbcee32957f4eb55df4ef41214`；以下只追加发布证据与当前CI边界。

固定提交的唯一父提交为`d1c728087423d85ed55f06010ec81e5e1d4b2fd1`，tree为`5bc5305768035411b81b018a2894b76dca5dbd40`。实际Git对象与`publication-r1.json`的九文件清单逐项核对，路径、blob ID、字节数和SHA256均一致；`local-commit-r1.json`记录同一提交／tree及九份staged blob匹配。`push-before-r1.txt`、`push-after-r1.txt`及原push输出记录普通推送从d1c7280推进至877e1e4；审查者另执行只读`git ls-remote origin refs/heads/refactor/architecture-foundations`，完整远端Ref精确返回877e1e4。

独立从固定Git提交读取的652个产品文件，与原wheel、两份保留的非editable安装及其原manifest逐字相同；wheel仍为SHA256 `e0b0364c3d88bc4ded4e38339a4d5bf24567b51aa48003dd5b00641f32505f6e`。177份已提交测试／示例与原冻结输入及清单身份相同，原`installed-r1`的退出0、27通过／57.10秒及JUnit零失败／错误／跳过再次一致。已提交独立报告正是上述7,132B原件。相对本地八文件审查快照，仅PLAN、本片交付和本片计划行补入实际本地approve／状态记录，另以原审查报告组成第九文件；没有新增产品或验收语义。因此无需重复安装或suite。

前置b2a自己的官方run`43704101013`／attempt1／push／完整d1c7280及原reviewer终态两轴approve已分别读取。审查者核其`ci-b2a/20261115T112323777899Z`的HTTP200原run／jobs：准确仓库／分支／SHA，八个job及30必要步骤全部completed／success。这只关闭前置发布条件。

本候选自己的官方[run `43708885957`](https://github.com/626619403/Ergora/actions/runs/43708885957)已按原HTTP200响应核到attempt1／push、准确仓库／分支及完整877e1e4，2026-11-15 11:26:33 UTC保存的观察为`in_progress`／conclusion null。原件位于证据根的`ci-b2b0/20261115T112633364905Z-{runs,runs-http,summary}.json`；原runs SHA256为`b816cf2d8ba308fbaf5412c9ac8f676a9b676824c1c3df7592d71a35d7b90a1d`。**自己的CI终态仍待，不能以普通发布或前置成功替代。**

本轮只追加本报告，未修改产品／测试、安装、提交或推送。工作树后继HEAD`3947b1e28b2cbc27ddc53cab584cced0c8d971a6`及新的研究／文档不属于本次固定877e1e4结论；后继能力和真实训练／质量／性能边界保持各自原范围。

## 自己的准确CI终态核验

原reviewer核对官方HTTP200原件后，确认[Portability run `43708885957`](https://github.com/626619403/Ergora/actions/runs/43708885957)为**attempt1／push／`refactor/architecture-foundations`／完整提交`877e1e4f7397731915c36b82f335efeaab3854dd`**，仓库与head repository均为`626619403/Ergora`，workflow路径为`.github/workflows/portability.yml`。原run终态为`completed/success`，更新于`2026-11-15T11:51:54Z`；固定提交tree仍为`5bc5305768035411b81b018a2894b76dca5dbd40`。

独立按该固定提交的workflow和六个显式Linux组重建job／必要step清单：plan、Ubuntu／Python3.11的group0–5以及Windows／Python3.12的group all，共**8个job和30个必要步骤全部completed／success**。原jobs响应总数覆盖完整八job，每个job携带相同run ID、attempt和完整head SHA；每项必要step恰好出现一次，重建结果与summary逐项相同。必要步骤包括显式分组、七个native job各自的wheel构建／安装、reference身份、应用回归及观察上传，以及Windows PowerShell5.1安装／升级。六个Linux job对Windows专用步骤的skip符合已提交条件。

终态证据保存在原证据根的`ci-b2b0/20261115T122331991398Z-{runs,jobs,summary}.json`及两份HTTP元数据。原runs SHA256为`e4b7d91c430b7990a8b8654aa80a8a67c2f0f0bdffb8248a14c652394eb759e0`；原jobs SHA256为`be9687431ce3b4614f328b6e6dc0503352312ae7647f6783a7096b6fe898e590`。此前四份`in_progress`观察及`20261115T115835551966Z`的官方限额403均仍在原身份下，未改记成功。这里核的是官方准确run／job／step结论，未宣称读取全部日志或下载CI产物，原本地运行证据保持原范围。

**最终需求符合性：approve。最终可维护性：approve。开放finding：0／0。** 固定877e1e4的本地、普通发布及自己的准确CI门禁已闭合；后继`1b8c2ed`及之后仍分别承担其产品／发布／自己的CI验收，不转授本片结论。当前后继源码和未提交工作不在本次审查内；kernel专家保留v3，真实训练／质量／性能限制保持。

本轮仅追加状态核验，未修改产品／测试、安装、重跑suite、提交或推送，也不触发对账记的递归审查。此前9,852B报告完整保留为不变前缀，SHA256为`ba89f1b0ae01193bb8ebaaf38a65dabfa5e91a967bc5469393c5716de72a3bec`。
