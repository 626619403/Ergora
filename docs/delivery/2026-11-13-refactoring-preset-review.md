# D2-A1 重构配方独立评审

日期：2026-11-13。评审者：`/root/refactoring_preset_review`（Codex，fresh context）；只收到原始需求、验收边界、固定候选和取证位置，未继承实现对话。按本项目 `AGENTS.md`、maintainable-project-delivery 的 independent-review、codebase-design 及 review-pr 进行只读检查；本轮只写本报告。

基线为 `5af9882367bbe5708f1a86ddabc16b2b665e9a49`。先检查 `.ergora/checks/refactoring-preset/review-candidate-r2/` 的全部24件及 tracked.diff，manifest SHA256 为 `a229bd2eecb43a3235c7bc5c887b601525f6b2444d8528eae5194cb6f4299117`；再补核 r3 全部27件，manifest SHA256 为 `64ffab54cee6491eb5754e11607922c18a0d186eb2fa311ee3cec17fb7ab7e48`。逐件重算均与快照及当时工作树一致。r3 只更新交付记录并增加下列三份手册，产品、测试、示例及设计相对 r2 未变。

检查范围包括3个新Agent包的全部9文件、4个新Workflow包的全部8文件、catalog、3份重构示例、`tests/test_presets.py`、[D2设计](../plans/2026-11-13-specialist-presets.md)、[交付记录](2026-11-13-refactoring-preset.md)，以及[定义手册](../WORKFLOW_DEFINITIONS.md)、[使用手册](../USAGE.md)、[入门旅程](../TEMPLATE_WALKTHROUGHS.md)的完整本片差异。相邻实现追踪到 `workflow_definitions` 的安装／编译／材料与权限检查、`review_dags` 的 WorkDelivery／StageDAG、`native_six_stage.invocation`、tasks／task_envelopes／WorkflowInput 和 console 的实际消费；同时读取了复用的三类review包。其他D旅程、根许可行政片及其余工作树差异不在本片判词内。

**Spec：已审实现、静态装配、正式准备及隔离安装范围通过，开放finding 0。Standards：通过，开放finding 0。A1总出口暂保持开放，等待本候选自身模型审查原件补核。** 本轮没有需要按优先级修复的确认缺陷或结构问题。

- `root → root/development` 只有所选原生调用；preparation、work、review覆盖全部7个Agent叶。`rewrite → compatibility → done(all)` 的传递依赖和原units相等；兼容性专家拥有自己的测试／文档工作单元，身份仍为implementer。其报告不替代原可信integrate／verify或最终独立审查。三个review分支均为required，独立实例保留只读、无shell、无network权限；all-join覆盖三者。
- 对留存manifest重新运行完整树检查、WorkDelivery与native投影：七个叶的资源来源集合恰好等于各自完整结构祖先及自身，正文均在对应提示中；权限仍由原编译器按每层祖先上限检查。留存单叶输入在原定义库移除后可独立验证，未把仅有附件名称视作完整材料。
- 留存正式prepare记录确为definition6，解出的input10通过原读取器，选中 `NativeSixStageInput` 与 `requests-composition-v10`；原task_type仍为`large-change`，input内容、unit映射和父链相等。记录中没有本任务的正式tasks目录或v10请求根。没有新增调度、账本、正式task type或runtime代码变动。
- catalog只增加`refactoring`。独立逐字比较确认旧三个条目、61份旧preset文件和283份冻结参考文件未变；validator v2保留原逻辑ID并与v1并存。`development-v5`只被现有console用于开发类别展示；实际版本路由来自定义及input，不会将本配方降为input5。新增手册明确v10须经CLI／HTTP提交，未宣称页面向导已支持该合同。
- 默认Codex writer与Claude reviewer的请求、writer显式current-container及逐实例覆盖均可由原消费者消费。示例和手册如实说明可信容器的advisory限制、不可用时的显式Codex回退及diversity原因；`require-distinct`仍拒绝同后端review。这里核的是合同与冻结事实，没有证明Claude在本环境可调用。
- 新资料分别由实际workflow节点、精确父引用和catalog消费，位置与职责一致；原CLI／HTTP继续调用现有安装Interface。两个新增测试保护数据包身份／完整祖先和正式准备这两个不同故障面；默认三reviewer与后端断言限定在bundled配方合同内，没有把任意用户配置限制为这些默认值。CLI输出对照安装进程实际加载的catalog，解除它与三个正式领域的旧耦合。未发现必须增加框架或重复算法负向suite的理由。

核验由证据原件和独立只读运算共同支持。读取 source-r1／r2 的完整命令、结果与stdout／stderr：首轮11通过（pytest 37.19秒），页面类别元数据修正后仅复跑受影响3项，3通过（13.27秒）；没有把首轮候选改记为最终候选。评审另以 `python -B` 重算文件／旧身份、验证留存manifest与input、运行原合同投影，并检查本片Markdown本地链接及空白，均无问题；未重复运行pytest或建立新执行状态。

隔离安装补核读取 `install-r1/` 的source manifest、setup／build／install记录、package identity及安装suite原件，并自行重算wheel和两份RECORD。wheel SHA256 为 `f97741f8a21e78db1813ee9abe86dce357a4fd65c14a11f5d40109be88677143`；隔离源码、wheel、实际site-packages与当前源码的475个产品文件逐字相等；wheel RECORD 483行、安装RECORD 488行的非空摘要／大小均通过，283份冻结参考与基线相同，安装为非editable。评审另外从仓库外以该环境的 `python -I -B` 读取presets，确认加载site-packages并列出四个配方及精确新根digest `ce26192b22c25031156755290c252823dbd845c199ff7f62f8e874e07076a15d`。安装suite的原命令使用 `-I`，11项全部通过（pytest 40.15秒／外层41.98秒），stderr为空。

源码准备驱动曾把path→SHA清单误当含`files`字段的包装而出现KeyError；原失败记录保留，发生在构建／安装之前。修正只影响取证驱动，未改变上述产品候选，不记作产品测试失败或隐去该样本。安装包同时包含主线已选择的许可文件；本报告只核产品与打包身份，不代替许可行政片的独立结论。

本轮没有安装、模型／GPU／网络调用、Temporal启动、产品／测试修改或提交。自身结构模板模型审查正在主线进行，尚未核其原始输入、结果、判词与清理；到达后由同一评审补记实际覆盖。A2的真实重构六阶段、旧／新行为、caller迁移和隔离回退旅程仍未由本片验收；静态装配、prepare、其他C／D任务和此次安装通过均不授予该运行结论。当前无阻塞finding，A1剩余出口为自身模型证据及最终交付状态收口。

**同片补核与最终本地判词（2026-11-13）：Spec／Standards通过，开放finding 0／0，D2-A1本地出口通过。** 上述“自身模型待核／总出口开放”保留为r3时的检查快照，由本段更新。A2实际重构、远端精确交付及本候选自己的CI仍开放，不由本地出口替代。

补核完整 r4 作者快照28件，manifest SHA256 为 `bfe5250573d145f6c38fd3f037d88f8b4d6783b44042945a57669aef854fe56b`；逐件重算与快照／当前文件均一致。相对 r3，仅交付记录更新，并新增[自身审查公开投影](evidence/2026-11-13-refactoring-preset-self-review.json)；其余26条路径逐字不变。新交付状态和投影均按原件核对，未发现范围或身份失实。

只读复核 `.ergora/checks/refactoring-preset/self-review-r1-codex/` 中的 native.stdout／stderr、admission、packet-index、input、原run冻结输入、stdin／stdout／stderr、协议命令／提示／结果、original-result及review.md，同时核对 self-review-audit-r2 和公开投影。原run `0ee55401953a42d2b405518cf9996779` 为succeeded／returncode 0，作者保存的CLI exit为0、墙钟用时32.256980秒；原stdout保留thread.started、turn.started、两条agent_message和turn.completed。最终消息JSON、协议结果、原run结果及original-result语义相等，review.md对应原response；结果文件SHA256为 `18aa2d51fdbd26d24678396e10bba51902ceb5e097027d6f158b32947788bbc8`，与原运行及公开投影相同。模型给出所供A1范围的Spec／Standards pass和approve，没有确认finding；它明示没有独立执行测试。

packet的22条路径逐件对应已审产品／数据／测试／示例，合计42,298B；每件完整原字节位于task中的对应 `COMPLETE FILE` 块，并完整进入prompt和stdin。供给input与原run冻结副本经原完整树检查得到相同digest `f264f9acc4cd8877fcdcc767ddbc2a66a36aead8b12d954b59d38f39239d83f8`。49,822B的实际prompt、stdin和协议prompt逐字相等，SHA256为 `18ba2513790cd7c6e03f4b4ad066adfbf05d11b464817b97156c186978a416f9`，与请求和公开投影相同。

实际选用的原 `ergora-structure-review@1.0.0` 根digest为 `996c55d50e307943ae5dc77b2c929baea0d996a924fa66ab8c86a41e813c40c9`，Agent为原 `ergora-structure-reviewer@1.0.0`。其根instructions 163B、Agent instructions 354B及Skill正文521B均与input assets、实际prompt／stdin和公开资源投影逐字相等；Skill的instruction SHA和完整单文件树digest分别核验，树内仅有声明的SKILL.md。这是原独立结构模板的真实调用；新refactoring父链的完整性仍由前述静态／正式准备证据支持，不把本次独立调用记作A2六阶段运行。

原请求后端为Claude Code，实际binding为Codex，保存了用户授权回退及不宣称异构成功的原因；mode为text-only。完整22件中不含D2设计、交付记录和新增三手册，这些由本fresh-context评审另行覆盖。原CLI和后端stderr均为空；原调用终态及turn.completed已核，但没有独立PID／PGID采样，不将其扩为全进程树清理证明。没有task-MCP记录或MCP读取，材料通过完整内联交付。公开后端用量逐项等于原turn.completed的自报字段，不解释为计费或理解证明，也不表示Claude实际成功。

首轮离线资源审计误把Skill树当普通sha256文件的KeyError记录已读取；本次按真实instruction SHA及树digest复核通过，保留原错误，不改记为产品或模型失败。补核只复用原run及现有安装／源码证据，没有重跑模型、测试、安装或网络操作，仅追加本报告。A1的可安装配方、版本并存、完整父链、definition6／input10准备及自身／独立两轴证据已覆盖；实际行为保持、caller迁移、回退与新配方完整运行仍须由A2提供证据。
