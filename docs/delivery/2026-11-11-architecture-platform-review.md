# C6d：架构导航与平台说明独立评审

评审者为新的 fresh-context `/root/architecture_platform_review`；Spec、Standards 两轴另由两个 `fork_turns:none` 的独立上下文并行检查。依据根 `AGENTS.md`、[本片计划](../plans/2026-11-11-architecture-platform.md)、[PLAN](../PLAN.md)与原用户要求，应用 maintainable-project-delivery、code-review、codebase-design。固定基线与 HEAD 均为 `c1f31fcfa38ac25085e287c507377be422786026`，分支 `refactor/architecture-foundations`，基线之后提交列表为空。

本次候选使用 `git diff c1f31fcfa38ac25085e287c507377be422786026` 加 `git ls-files --others --exclude-standard`，没有用空三点差异替代工作区。首轮14文件；05:41:54 UTC核17文件，另加本报告；安装入口增量加入USAGE与入门旅程后，最终为19份内容候选加本报告，共20路径。旧C6b/c只审本次提交／CI／远端状态增量，不递归重审旧产品片；本报告也不要求递归审查。

## Spec

本地文档候选通过，开放 finding 0；C6D-SP1／P3 已关闭。职责、调用关系、已有 Interface／继承与局部选择、配置／格式／数据所有权及最轻接入均有当前入口。结构继承、控制依赖、具名数据与正式阶段投影分开；静态定义、逐实例后端、完整祖先资料和模型实际读取没有互相替代。task-definition-v2、正式信封v6与材料v2的含义及旧版本身份明确。

原六阶段、精确 owner 计划批准、candidate／证据所有者、attempt-before-send、原ID未知恢复及可信当前用户容器保持。C5c确定性原生命令夹具、C6b创建和C6a图容量没有被扩大成全部真实模型／同数量Agent已执行；双后端、GPU、WSL2等未验范围继续明示。两份完整冻结参考手册保留并可达。该结论只完成本片本地文档独立评审，不关闭P5、AC6/F6或项目整体。

安装增量由主评审及两轴同片复核：README、USAGE和Windows的clone都明确当前 `refactor/architecture-foundations` 开发分支，Windows ZIP选择相同分支，入门旅程回链源码选择。两安装器源码均从自身所在源码根安装；文档提示按验收完整提交固定身份，避免将相同包版本号当作相同功能。直接核本地main为cab3a724、没有当前preset树且CLI对象不同；没有以此推断远端main。该更正晚于实际模型调用，公开投影的 `scope_disposition / post_model_changes` 与delivery均明确只由独立follow-up覆盖。

|Finding|证据、影响与最小修正|复核结果|
|---|---|---|
|C6D-SP1／P3，非阻塞，当前六阶段首标签不准确|本片规格要求当前“调用流程”；初始 `architecture/current.md:97,126` 写 `inspect`。冻结 `dev_platform/contracts.py:18–19` 定义首stage为 `inventory`、role为 `inspector`，`workflow.py:192–195` 实际发布inventory并交给plan。用户按新图查stage/history会找不到inspect。只需更正新图可见标记，不改旧归档或生产代码。|两处标记已改为 `inventory / 盘点`、`inventory / plan`，同步一个图节点ID，恰好三行图源码变化。旧导航26,129B／SHA256 `325e6ad4ecae937f93fa0498cf26f1d6bcacbff15825c4c1b11abcc6dbc367e7`；修后26,146B／`b6a9314f20d8ba48d34a66ecd19b5c87e12b18024a12bc63032f5736f93356c3`。主评审与Spec轴均直接比源码关闭；原模型快照／判词未改，不声称模型审过修后候选。|

原用户“追加资源可以通过同时提升父级权限和子权限的方式来进行，但不能越过父模板”与“每个模板要阅读自己的所有父类/父模板的skill和上下文”按原文保留理解。当前规则要求完整资料累加、各层权限包含；需要提升访问权限时发布所需父子新精确版本并沿真实引用根最后发布。没有推导成每加一份已允许资源就必须改变所有父权限。该语义与 `_within / _readable`、逐包不可变发布及D4/D5、C3d已接受合同一致。

## Standards

通过：实证硬标准违反0，新增判断性 smell 0。导航沿现有定义库、后端ABC与本族映射、版本Input／Workflow和阶段投影，未因静态盘点新增生产抽象、插件层、调度器、账本、测试或CI。保留兼容别名、平台生命周期和冻结分发均给出真实消费者／合同及退出条件，未机械合并不同事实所有者。

归档、当前声明、历史结果、静态证据和未验范围有明确区分。自身审查公开投影如实解释完整delta与未变正文的区别，作者HTTPS成功与独立评审者超时分开；原delivery旧“下一步逐字归档”已同步，非阻塞记录建议关闭。Spec与Standards判词分别成立，没有用一轴通过遮蔽另一轴问题。

## 独立核验

- 直接比较 `BASELINE:docs/architecture/current.md` 与归档全部字节，相同59,761B，SHA256 `3231898e9ab6b60e453ad04b4c444876d7f5abdfb867eacbf93a7cc287baf920`。只定位归档必要标题／历史段落，未将其中旧“当前／待实现”当新声明，也未声称全文重审历史语义。
- 自有标准库AST读取53个根包Python文件，包括函数内导入；重算203条本地边、无环，整个依赖表等于公开清单。53个Python与18个第一方JS的路径集合、大小及SHA256逐件相符。原AST回执27,971B／`02a336d1c52bd965ccf2bf1c7db6482f2167f1b9fc1140eec402fc05e3a00ac2`直接核原件；其f957489标签保持，f957489与本片基线src树同为 `bff8c45480c31d82794cdf1dbe1775eed8abd940`。
- `src / tests / scripts / .github / pyproject.toml` 对基线无差异，未跟踪候选也全为文档／投影。另按随包 `reference-manifest.json` 逐件核283冻结文件原字节，问题0，包含两本完整参考手册。这是字节身份校验，不是重建或重新运行旧439文件／两RECORD非editable安装验收。
- 主评审首轮自有标准库静态检查17文件的JSON与348个本地文件链接，最终20路径／413链接，均问题0；`git diff --check BASELINE`通过。保留 `Agent后端接入` 标题及引用目标，并定位新导航相关标题。没有通用锚点全检或Mermaid渲染。作者首样本14文件／328链接、后续20文件／413链接及6个已加载秘密值／私有home扫描的原result已读；本评审没有读取凭据来重复秘密值扫描。

私有可复核结果保存在 `.ergora/checks/ac6-platform/independent/r1/inventory-audit.json`、`final-local-audit.json`及最终 `final-candidate-r3-audit.json`。两轴首轮17文件摘要和读取附录在 `independent/spec/snapshot-r2.json / report-r2.md`、`independent/standards/candidate-snapshot.json / standards-review.md`；最终20路径增量在 `spec/snapshot-r4.json / report-r4.md`与 `standards/candidate-snapshot-final.json / standards-review-final-increment.md`，两轴开放均0。只有本报告在登记两轴结论时又作报告记账，不递归审查。摘要证明所读候选身份，不能替代下面列明的语义读取范围。

## 实际自身模板原件

直接离线核原run `873f78512f944ad19d018980ff95b1ab`，原结果为 succeeded／exit0／approve；208.25秒按原调用记录保留。manifest、prepared input、实际run快照、prompt／stdin／protocol、准入、结构祖先及scope和原decoded结果全链一致。bundled结构审查模板只派生版本1.0.89、候选证据Skill、精确子引用和材料限额；原指令／Skill字节、原默认Claude请求、权限和其余定义保持。实际binding为Codex，准入保留Claude历史失败后的明确回退理由及 `formal_execution_authorized:false`。

17件完整附件393,375B，SHA256 `8a61e235ecc7766473884fd59d711edc61c658144e47a96338b164259863d9c0`。逐件从附件按精确边界提取并核索引，未变源与首轮候选摘要相符；完整tracked delta不等于每份tracked文档未变正文也已提供。linked其他源码、两手册、旧大型原件、后续状态、inventory修正、安装分支／ZIP／指南更正、公开投影与本报告不在原模型附件，未借模型列出的路径把它们扩大成已读。

从native stdout逐项重新解码实际list/read结果，与scope、来源完整树及其原字节比较：五文件394,893B、23个成功UTF-8页从0连续至null，7个base64页在同offset缩小重试后推进，31个completed MCP调用，无失败。原结果SHA256 `51128bdac4f419d9cfdd125cab528a772de636f13bfff5beefa6f7f0f2af2be8` 与实际result、protocol及native最后消息相符。公开投影的10份原件身份、decoded结果、附件索引和读取摘要全部匹配。

原turn自报input3,503,516，其中cached3,265,664已包含；output3,887、reasoning1,144原样单列。未相加推导账单、理解质量或独立后端错误率。四个原采样PID／starttime无live，另直接读当前相同进程身份确认；不推导所有短命／未采样进程。自有核验结果见私有 `independent/r1/self-review-audit.json`，没有执行作者driver或审计脚本。

## 实际语义读取与限制

主评审全文读新current导航、合同身份表、本片plan／delivery、两份新公开JSON及实际模型原结果／任务指令；README、TRAINING、WINDOWS、USAGE、TEMPLATE_WALKTHROUGHS、PLAN、总计划、两个父计划及旧C6b/c记录按本次全部差异与必要上下文读取。安装器只作源码阅读，未执行。未把未变长正文、归档或全部源清单的字节读取记为全文语义审查。

直接查看的当前Interface及相邻真实调用者包括：

- `agent_backends`的ABC／Invocation、四种实现与本族映射，`agents.invoke`，`agent_runs`普通／组合／workspace准入和归档；`task_mcp` Linux／SDK前置、完整scope、list/read及native回执；`pyproject`可选依赖。
- `reference_inputs`、`reference_worker`全文；`reference_workflows`全部版本及活动／调度相关实现；`review_dags`全文；`task_envelopes`版本、manifest、work/review与多样性规则；`tasks._definition / _composition`及页面 `task-composition.read`。v6确实继承WorkDelivery，队列／请求根由局部Input选择。
- `workflow_definitions`权限／材料累加、来源冲突、预算、编译、manifest／input准备和核验；`definition_bundles.revise`与D4/D5、C3d相关既有规格。`reference_executor`声明产物、producer核验、端口合并、材料v2、保存call／首次HEAD门禁后证据与恢复；冻结 `FileAdapter.verify_receipt`实际逐件核所有审计产物字节。
- 原 `dev_platform.contracts / workflow` 的六阶段与角色映射，提交／runtime／批准的原意图、attempt、memo、run及owner／plan绑定入口；`state`表与迁移／锁，`backups`离线完整目录及原平台／原home恢复，`skills.adopt`与直接兼容别名。
- 前端 `app / state / agents / task-composition`实际调用、图mount/dispose及选择；两轴另定向读 `definitions / workflow / tasks`会话、`composition-graph / composition-comparison / binding-fields`的所有权与导入。18份JS全部核字节／路径，未声称18份全文语义审查。参考手册与USAGE／WORKFLOW_DEFINITIONS只读有关标题、版本和运行边界。

没有运行作者脚本、项目入口、测试、安装／打包、模型、服务、浏览器或网络，没有读取个人凭据配置；未重验GPU／WSL2／原生Windows运行。已读前片原评审者追加的离线终核结论：自己的CI第四样本双OS七必要步骤成功、作者Ref完整SHA相符，C6b/c按该范围终结。本报告只核新增记录与事实归属，未直接核其原网络／CI原件。原独立Ref超时、smart-Git TLS失败与前三in_progress原样本保持。

本片后续应完成最终文档冻结检查、普通提交／推送、自己的必要CI与精确Git／远端身份；任何后续状态增量须按新字节复核。当前结论为本地完整文档候选的两轴独立通过，Spec开放0／Standards开放0，最高历史问题为Spec P3且已关闭。
