# AC5 C5a：完整 manifest 交接独立审查

审查者 `manifest_handoff_review`，fresh context；另按 `code-review` 启动互不共享上下文的 `spec_axis`、`standards_axis`。先读原始 C5a/AC5 规格，再读实现叙述；参照 AIHERO 索引、`maintainable-project-delivery` 及 `independent-review`、`code-review`、`codebase-design`。本报告只评本片静态交接，不代表整片或项目交付完成。

固定基线与 HEAD 均为 `a2c89a5b4b5ca49bf0c3f28a4f35efaec539bd3c`。`git diff a2c89a5b4b5ca49bf0c3f28a4f35efaec539bd3c...HEAD` 与对应提交列表为空；按用户明确授权的 WIP 例外，审查本地 `review-r1/identity.json`、`tracked.diff`、`files/` 的完整13文件。快照时间14:33:58 UTC，实际已含R2修复，目录名称不代表R1失败源码。范围为四产品文件 `workflow_definitions.py`、`cli.py`、`web.py`、`data/console/definitions.js`，两合同测试 `test_composition_manifests.py`、`test_definition_console.py`，以及七份计划、手册、架构与交付文档。主审逐字核快照身份；后续仅同片三文档澄清及页面证据增量，四产品/两测试不变。增量原件与身份另存本地 `independent/clarification-files/` 和 `clarification-identity.json`。

## Standards

审查者：fresh-context Standards 子审；只读检查，无运行测试、安装、模型、浏览器或网络。基线与 HEAD 均为上述固定对象，按授权 WIP 审查完整13文件，逐份核快照哈希一致；另读必要邻居及三个 live 文档增量：C5计划、Workflow手册、C5a交付记录。

结论：**本范围 Standards 通过；文档标准违规0，可行动 baseline smell 0。** 不代替 Spec 轴或整片验收。

依据为 `AGENTS.md`、`docs/PLAN.md` 持续规则、`docs/architecture/current.md` 模块所有权及两份定义手册的完整包/历史合同；未发现 CODING_STANDARDS / CONTRIBUTING。按指定技能检查，跳过工具已有检查项。

`workflow_definitions.py:562–582` 把持久位置、摘要绑定、原锁、原包发布与历史读取留在既有 owner；CLI `:673–677` 与 HTTP `web.py:341–347` 是两个实际生产消费者。摘要校验、当前位置一致性及已存在目录分支分别保护外部输入、错误寻址、重试/损坏；复用原 `_prepare_bundle` / `inspect_manifest`，没有第二账本、权限算法或执行链。六阶段及原证据 owner 未改。

`definitions.js:627–650,990–1008` 的私有过程由保存/读取按钮实际消费，home、原 preview 与当前记录身份共同限制迟到回复；grant/根变化沿原失效路径处理。其单视图内聚合理，无须为抽取制造复用。新增配置不限制原合法 grant、home 或后端范围。

两新增测试核摘要失配、真实并发重试、损坏不覆盖、CLI/HTTP一致和源库退出后的历史读取，能捕捉静默错误；未复制编译器，未加依赖或CI。证据准确区分R1的41通过/2失败与R2两受影响项2通过（6.39秒），不倒改首轮。437文件/两RECORD/283身份记录已读；页面01驱动键序误判失败与02通过、94HTTP审计及清理原件已静态检查。

补核文档已明确空目录复制但不参与 digest，符合旧 Agent 手册:70；稳定空目录增删不属于摘要损坏保证。实际自身模板/完整读取、公开投影、最终候选身份和本片CI/精确交付仍未验；C5b/C5c/C6不在本审查范围。

## Spec

评审者：`spec_axis`，fresh context。对象为固定13文件，另复核本轮三文档澄清增量；四产品/两测试仍逐字匹配快照，四产品也匹配R2包身份。先读 AGENTS、PLAN、原C5/AC5规格，再读实现及交付叙述。

结论：**Spec 无开放 finding；未见越出C5a范围或其他有证据的错误实现。** 维护性由独立 Standards 轴判断。正式选择、writer信任界面及纵向六阶段属于C5b/c。

- **C5a-SP1，P2，已关闭（文档澄清）**。原 [C5计划](../plans/2026-11-10-composition-handoff.md)第15行承诺“执行位与目录身份”。`workflow_definitions.py:565` 的读取及 `:580` 的重试复用原核验；`:410–411` 不持久记录目录清单，`asset_trees.py:43–45` 仅摘要文件。保存后稳定增删空目录，读取/同摘要重试仍接受同 digest，原句因而过强。旧 `AGENT_DEFINITIONS.md:70` 明确空目录不参与身份，原规格第19行要求不增 schema；正常 copytree 保留空目录不等于绑定其身份。最小处置为准确声明复制保留及旧摘要范围，不默改旧 hash。已直接核 live 计划第15行、`WORKFLOW_DEFINITIONS.md:100`、交付记录末段均准确澄清，产品/测试未改，此项关闭。

实际检查：静读13文件差异、原包发布/核验、库复制、file_lock、tasks重新准入、HTTP同源/header、页面home/preview对象及编辑/比较生命周期；核快照/live/R2产品哈希，静读安装/回归证据及页面驱动和原结果。R1历史43项41通过2失败保持；R2仅补两项通过，不重标整轮。页面首失败保持，第二旅程记录三域/重开/丢回复/三种迟到回复通过，audit报告94HTTP、12preview、14manifest。

限制：本轴未运行测试、安装、浏览器、模型或网络；未逐份重算94HTTP或目视截图。实际自身模板、完整读取/公开投影、最终候选及其CI/远端身份仍待验，不由本审转授通过。

## 主审原件补核与验收边界

主审仅用文件、JSON、ZIP、RECORD静态核对，原审计存本地 `.ergora/checks/ac5-composition-handoff/independent/`；没有调用产品代码、运行测试/模型/浏览器、安装、网络或进程控制。确认：

- R2全部437源/wheel/安装文件同摘要；wheel SHA256 `d575678b1120649561efcd4e1dd8b44ed40ab3519654be51b6834db42e097e40`；两RECORD分别441/446条带摘要记录通过。283冻结资产的原验证结果已读，未重复运行验证器。
- 94组HTTP原件及元数据字节/摘要通过；12份preview的规范JSON摘要通过；14份manifest回执逐份匹配落盘完整文件/执行位树、manifest正文及对应composition。48棵旧对象树另核真实目录清单不变，18种实际静态资产等于当前源。详见 `independent/static-audit.json`；这不把静态摘要核对称为主审重新运行原owner。
- 已静读两轮页面驱动和原结果：首轮3.87秒在首次保存后因驱动按对象键序比根而失败；第二轮改字段比较，产品未变，15.33秒通过三域16/19/9实例、键盘保存/读取、重开、丢回复查询、root/grant/home实际迟到回复、比较当前根、tab及未应用字段缓冲。未由主审启动浏览器或目视截图，视口结论限原所截保存区域。HTTP采样身份清理原件已读；浏览器PID缺starttime的限制保持。

测试选择与成本符合本片风险：两新合同测试穿过真实用例及传输接口；原完整包原子/损坏回归继续复用，没有复制编译器或增加CI。原R1结果与R2受影响补验分开；本审没有发现需要重复41项邻居回归或扩大容量测量的实质证据。C6容量、自然BFCache、跨浏览器、Windows运行、本片实际自身模板/完整读取及公开投影、最终候选/CI/远端精确身份不由此静态审查授予通过，后续证据需按实际身份补核。

**实现阶段两轴统计：Standards 0项开放、最重问题无；Spec 0项开放，原P2 C5a-SP1已以文档澄清关闭。** 上述是实际自身模板及最终公开投影到达前的审查范围；下文记录同片最终补核。

## 最终候选与本地出口

最终固定对象为本地 `final-candidate-r1/identity.json`，SHA256 `66754f4d7d80c07637c32d14e2f0682162420476f5b86fbf8978d7b7c28596de`，14:46:02 UTC共22文件。主审及原两轴逐份核固定副本/记录/当前文件身份，四产品/两测试继续等于前审R2。增量为五份公开JSON、两原PNG、审查报告及计划/交付状态；报告只核身份，不递归评审。旧阶段已核的包、页面与原对象验收未重跑；前片状态续记不转授C5自己的交付门禁。

### Standards 最终补核

同片原Standards审查者独立补审。结论：**固定最终候选的 Standards 本地出口通过；新增文档标准违规0，可行动 smell 0。** 原产品审查范围与结论保持，不替代Spec或远端交付。

按 `AGENTS.md` 的真实验证/原证据所有者及公开文档规则、`docs/PLAN.md` 的分片和历史保留规则核对：五JSON列明十四份私有原件字节/SHA、替换和省略；逐份重算身份并直接比较投影，全部一致。两PNG与原截图字节一致，未重复目视；不新增截图内容验收。未发现公开JSON残留机器home路径或私有端口。

直接检查原run/result、prompt/stdin/protocol及scope/native身份；run `e7cf62b73ef34833b610e8bf5268170b` succeeded、CLI0，结果摘要 `53a56620aae84fe73ecb77896c3df7f33cdd08f53818e7b3d09dc1d5d7b36bc5`。从原工具事件独立比对五scope全部字节：候选314712B、14连续UTF-8页至null，一次base64保持offset后缩窗，失败0；13附件条目身份吻合。记录未把省略大map、字节送达、approve或同后端回退夸称为完整原件阅读、理解质量或正式批准。

四个模型采样身份gone与自报用量直接对原记录；cached已含input、reasoning另列，范围准确。R1测试41/2与页面首失败保持，R2仅两受影响项通过。前片四CI样本/官方job groups及HTTPS403后200原记录符合新增状态；无C5继承CI。空目录措辞维持原身份合同。

只运行标准库静态读取/哈希与投影比较；未运行产品、测试、安装、包验证、页面、模型或网络，未重跑父方208链接/AST/JS/secret检查。C5自己的CI、精确Git/HTTPS交付仍未验；C5b/c、C6及外部平台范围继续待办。

### Spec 最终补核

同片原Spec审查者独立补审。结论：**本地出口Spec通过，开放finding 0；未见新增缺失、越界实现或错误验收声明。** 原C5a-SP1目录措辞澄清继续关闭；C5b/c/C6仍明确后续。

原规格第9、23行要求实际自身模板及独立审查。已静读实际驱动及原件，内置structure-review只增加证据修订1.0.81及显式预算，原模板材料保持。新增freeze保存manifest后移开活动库，再从包准备输入；原manifest/prepared/actual树摘要、四份prompt字节、scope/native回执及结果身份均独立对上。实际run为Codex/gpt-6.1-sol/high，160.3717秒succeeded/approve/CLI0，原结果SHA256等于上述固定结果。

独立解析47条原native事件：list完整列出五scope，每份read字节均等于实际冻结资产；候选314712B经14个连续UTF-8页至null，216000处一次base64保持offset后缩窗重读，失败read 0。13份附件全文哈希吻合，省略大map的模型投影明确标注，未冒称模型读过省略原件。

五公开JSON所引14份原件的bytes/SHA、路径/端口替换、字段省略与清理派生值逐项一致。R1两失败及页面首失败保持，R2仅两受影响项通过。用量对上原turn.completed，cached已含input；清理仅为原记录的三HTTP/四模型采样身份，浏览器PID限制保留。

仅静读/解析/哈希，无产品、包、测试、页面、模型或网络重跑；208链接、AST/JS及敏感值门禁仍为父证据。PNG仅核身份，不代替主审目视。前片CI不转授C5a；本候选自己的CI及精确远端交付仍待验。

### 主审最终原件与图像补核

主审独立静态核22文件、模型manifest/prepared/actual完整文件/执行位摘要、prompt/stdin/protocol、scope/native回执、原模型最终消息与结果JSON的精确相等、13份冻结全文及六份受保护源码/测试。内置模板仅有明确的证据修订/附件和预算变化，原材料不变；五scope原始工具页连续覆盖通过。五JSON逐份等于14私有原件的声明替换/省略或清理派生值；没有重跑发布生成器或产品。原件见本地 `independent/final-artifact-audit.json`，两轴全文分别为 `spec-final.md`、`standards-final.md`。

已实际目视公开桌面1440×1000及窄屏390×844两PNG，均与原截图逐字节相同。所截保存区域的按钮、说明及JSON结果可读，窄屏控件换行后仍在所截内容宽度内；两图未显示结果path字段或机器绝对路径。结论只限所截区域，不授予页面全貌、跨浏览器、BFCache或容量验收。

**最终本地出口通过：Standards新增违规/可行动smell均0，最重问题无；Spec开放0，原P2 C5a-SP1关闭。** 可继续固定ready并普通提交/推送；本提交自己的CI、精确Git/发行包/283冻结身份与独立HTTPS交付仍须另核。C5b/c、C6及项目整体未完成。
