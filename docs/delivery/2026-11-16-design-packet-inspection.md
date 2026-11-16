# WA5a-1：设计 packet 与必要知识的只读检查

2026-11-16。实施基线 `562394c839e9353e4f889a0b03e749ca32783936`；隔离分支 `feat/design-packet-inspection`。**当前为下文 fixed-r3 六文件修正版：源码受影响组 56 passed／1 个可选 Web skip，新非 editable 安装 57 passed，原结构模板 approve；同片独立最终复核两轴approve／0，固定cb861ea并普通导入3d632a7；本片inspection-only闭合，发布／自身CI另验。** 总 PLAN 由主控维护；根工作树及 M5/native 在途差异只读。

权威输入为[原始要求](../plans/2026-11-15-workflow-evidence-and-human-gates.md)、[D1–D4 原决定](2026-11-16-workflow-design-decisions.md)、[已审 r2 设计](../plans/2026-11-16-design-knowledge-gates.md)（SHA256 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`）和[静态设计独审](2026-11-16-design-knowledge-gates-design-review.md)。设计两轴 approve／开放 0 只针对静态设计，不是实现、材料或运行批准。

## a1 原 caller 的最小接缝补充

真实入口继续为 `tasks.plan → reference.task_plan → reference_task_approval._plan`。在原 history、原 request envelope、原 pending plan receipt 身份校验之后，只对 receipt 明确列出的 `design-packet` artifact 追加检查；没有该 artifact 时保持原返回行为。新 packet 不成为旧 native profile 的隐含必需项。

当前 input1–11 的 admission 没有冻结 design policy 或可信 owner binding，亦无 v12 工厂。a1 使用随包内置、明确命名的 companion profile 检查 typed 内容、原字节与声明的 Q/K 缺项，并报告 `inspection_only:true`、`runtime_enforced:false`。packet 自报 policy／owner 不构成权威。内容完整、来源已提供与可信决定、批准和执行就绪分开；a1 永不报告可批准或执行就绪。此补充不改变 D1–D4，也不将设计讨论答复变成运行批准。

为避免 packet 与 Response 的反向 SHA 循环，且不提前实施 journal，本片不新增未明确来源的 response／resolution 快照。schema 的 Response／Resolution／binding 定义只是后继合同；packet 不能内嵌自报决定来关闭问题。所有无可信源链的问题逐 ID 保留为 unresolved，并报告 owner channel 不可用；`supplied` 知识仅在实际全文原件可读且字节身份匹配时表示资料已提供，仍不替 owner 决策。报告和 source 正文沿原 adapter 的 safe path／有界 read 读取，不联网、不扩大授权。

## 范围与交接

只实现 task-design-v1 schema、companion profile、纯领域检查及原 plan reader 的完整材料读取。input12／definition8／State6、runtime G1/G2、源 journal mutation、批准、模板默认、CLI／页面新交互均未实施或开放；283 份冻结参考不改。产品分支没有 commit／merge／push，没有安装、模型或外部服务操作。

源码检查沿 `tests/test_task_plan.py` 的真实 SDK message／history→envelope→seed→artifact fixture，已覆盖无 packet 兼容、精确 Q/K、来源字节与安全读取、身份不一致及本机 profile 的非运行边界。此接缝不是实际 Temporal 服务、可信身份或 runtime gate 验收。

原始命令、完整 raw 输出、冻结输入、完整 tracked＋untracked patch、文件 SHA／执行位已保存在 ignored `.ergora/checks/design-packet-inspection/`。本页记录准确结果与未验范围，主控接续新的非 editable 安装、自身原模板及 fresh 独立实现审查；实施者不自批。

## 实际实现与 caller

以下源码路径属于隔离候选；根源码尚未导入。

|文件／函数|实际消费者与必要性|
|---|---|
|`src/ergora/data/schemas/task-design-v1.json`|原 approval owner 的 `_inspect_design` 局部装载，使用 `contracts.validate` 校验封闭 typed packet。覆盖身份、目标、原结构、调研采用、修改／caller 依据、规范、数据／恢复、逐片顺序、验收、Q/K 和完整正文引用。Response／Resolution／binding 的 `$defs` 仅保留合同，没有运行消费者或授权效果。|
|`src/ergora/data/design-profiles/framework-development-v1.json`|同一 `_inspect_design` 从固定随包路径取得，校验其结构并计算 canonical SHA；显式是 `task-design-inspection-profile`、`inspection_only:true`、`runtime_enforced:false`。最低章节／问题、来源及读取容量由此配置给定。未来执行不能靠改一个布尔值继承本片验收。|
|`src/ergora/task_design.py:inspect_packet`|当前唯一生产 caller 是 `_inspect_design`。这是已审首片要求的纯领域检查：隐藏跨数组 ID／引用、原身份比较、最低题保留、Q 未决、K 来源／权限范围／冲突／声明时效及原 work unit 映射；只 import 标准库。没有虚构另两个已实施消费者，也没有 journal／文件／SDK／State owner。移除此模块会让原 plan reader 同时承担这整套领域关系，故保留该内聚边界。|
|`src/ergora/reference_task_approval.py:_inspect_design/_plan`|`_plan` 是私有材料读取函数的唯一 caller。沿原 adapter 读 packet 所列正文，保留全文及实际 SHA／bytes；source 正文追加到原 `materials`，由原读取视图消费。缺文件／拒绝读取形成来源状态；摘要／字节漂移保留实际已读正文并阻断内容完整性；危险路径、编码或容量错误显式失败，不截断。原历史／envelope／seed 验证仍先执行。|
|`tests/test_task_plan.py`|扩原现成 fixture，没有新测试文件或 CI 分组。测试只使用原受控 SDK message／codec／history 与本地真实文件，新增 20 个 case，原 32 个 case 保留。|

本地摘要明确分工：artifact 的 SHA 是原始文件 SHA256，`packet_content_sha256` 是原 canonical JSON 身份，`inspection_sha256` 只绑定这次 seed、packet、内置 profile 与实际来源观察。它不冒称完整源 journal 的 `materials_sha256`。API 单独报告从原件核对的字段、manifest／work unit 映射的实际可核范围、未核前版链，以及 packet 声明的时效观察基准；owner、最终 policy、可信决定及执行准入均未认证。

最低题不能只保留 ID 而改成“已同意”；profile 原题／理由及 required_by 会核对。无来源链的每个现存 Q 保持 unresolved，删除最低 Q 会得到 missing_question。K 的 missing／denied／conflicting／stale 保持原状态，实际全文 reference_only／缺失／摘要漂移／字节数不符／权限范围不符会落到具体 K、JSON 路径及受影响问题／验收；可读且身份匹配的 supplied 只表示资料供给。

旧任务没有 packet 时不增加 `design` 返回，不引入新强制要求；旧 `_Approval`、旧运行输入和原模板语义不变。设计检查的 false capabilities 只表达新设计能力未开放，不能被理解为本片向旧任务追加 runtime gate。

## 固定候选与源码证据

完整记录位于 ignored `.ergora/checks/design-packet-inspection/`；没有把私有运行数据或环境变量值复制进公开文档。

|原件|准确身份／实际结果|
|---|---|
|`source.patch`|包含全部 tracked 修改及 3 个 untracked 新文件，共 5 文件、70,359B；SHA256 `cfde3166b6f1c713f482ca6bc7585619f6e07f5a5bc3882de4eae63ccafd64dc`。分支 HEAD 仍为实施基线，无 commit。|
|`source-inputs.json`／`source-inputs.tar`|全仓 2,053 个 tracked＋新文件，36,519,438B；每文件完整 SHA、字节数、stat mode 与执行位。清单 SHA256 `d5e3c51328fd9c0d23bb7aa3b2b62d239d9561a235991a9ce86bcd775187b066`；tar SHA256 `f93bc99af6dce7a5354d40563ede0775c25cd7ebc5062fda6128d3f6844c4499`。这是源码输入身份，不是已安装包计数。|
|`inputs/`／`inputs.json`|保存实际读过的根规则、总 PLAN、src/tests 规则、组件协议、r2 设计、设计独审、D1–D4、两项 skills 及所读 references 原件与各自字节身份；root 在途 M5/native 未并入候选。|
|`source-frozen-r1.command.json`／`.stdout.raw`／`.stderr.raw`|新冻结输入下运行 `python -m pytest -q tests/test_task_plan.py tests/test_task_inputs.py tests/test_task_approval.py::test_exact_owner_approval_is_only_requested_and_repeated_commands_never_signal_again 'tests/test_task_approval.py::test_each_interruption_keeps_original_owner_receipt_and_never_resends_unknown[after-attempt-unknown]'`；**118 passed／25.11 秒**，完整进程耗时 25.775 秒。使用既有开发解释器、`PYTHONPATH=src`，实际导入隔离源码；没有安装。|
|`source-static-r1.*`／`reference-files.json`|3 个 Python 文件 AST 与 Draft2020-12 schema 语法通过；导入 reader 确属隔离树；逐原 Git blob 比较 **283 份参考完整字节和执行位同一**。|
|`source-whitespace-r1.*`|`git diff --check 562394c839e9353e4f889a0b03e749ca32783936` 通过。新增文件完整内容在 `source.patch` 与输入 tar 保留。|
|`verify-freeze-r*.command.json`／raw|最终测试前后 2,053 输入的名字、完整字节与 mode 全同一；完整 patch 的 reverse apply 检查、所有新增行空白及交付相对链接检查通过。交付正文自身 SHA 与字节数单列于 `delivery-identity.json`，不反向写入正文。|
|探索检查原件|plan r1 为 48 passed／2.78 秒；r2 为 52／2.10 秒；r3 为 52／1.97 秒。旧 inputs＋approval 全文件为 94 passed／232.66 秒，但该轮期间 a1 材料返回呈现仍有变更，故只保留为探索结果，最终精确候选以新冻结 118 项及前后身份核对为准。没有把先前结果转授变更。|

新定向覆盖：完整 packet／报告／资料实际返回与无写入；原题和 Q2 逐 ID 未决；最低题缺失／替换；K 的缺失、拒绝、冲突、配置化时效、完整／仅引用、scope 与字节漂移；危险路径／symlink／UTF-8／单件与聚合上限；M−1／M 全量返回与 M＋1 拒绝；内部自洽但换 policy／owner／job；原 work unit 映射；以及真实 `python -S` 子进程中纯检查与原 input reader 不导入 jsonschema／SDK／State／schema。旧正常批准和 attempt 后 unknown 不重发亦由最后两条原测试复核。上述“真实”仅指本地原字节、SDK message 或进程接缝，不表示服务或人类身份验收。

## 待主控的验收与明确未验

交接基于上述完整 patch／输入；主控更新 PLAN 后，以同一候选运行新的非 editable core／SDK 安装及完整包／依赖身份、自身原结构模板、新 fresh-context 实现两轴审查。实施者没有作独立结论。发现需改行为时产生新完整 freeze 并重跑受影响检查，不把当前 source pass 续给后继。

未验且未开放：input12、definition8、registration2／State6，G1/G2，源记录提交／修订／封存／撤回，可信 owner channel／ACL／身份，实际 Temporal、服务重启／signal 丢回复，work 执行、原进程竞态或训练，新的 CLI／HTTP／页面讨论流程，模板默认、发布和该候选自己的 CI。a1 不自动推断所有公司知识已发现，也不判断设计合理或人已理解；任何正文、typed 字段或来源改变仍须后继新 revision／新明确批准。

## 主控：新非 editable 安装证据

同一五文件冻结候选的新 wheel SHA256 `24a06047aa815361d0cd6e5c9f74cb2f647ff8dfc1cd128d4609a7d1c6e73886`，core／SDK 各666完整产品逐字节／执行位与源码、wheel同一，实际导入site-packages。三个新资源／模块和原approval reader为唯一产品差异；283参考／依赖检查通过，core无Temporal、SDK1.34.0、Python3.12。856构建／测试输入、179测试／示例副本冻结；六个生成egg-info文件按完整原件归档移除。原件在私有 `package-r1/`，不将源码2053输入与856安装输入混为一个集合。

新安装沿最后精确源码组的相同四个原入口，实际 **118 passed／37.87秒**（driver39.014秒、exit0）：完整plan、旧input以及旧exact-owner和attempt后unknown各一项。准确命令、JUnit、完整输出、case原件为 `package-r1/installed-affected-r1-*`。这只认证安装下本地原文件／受控SDK接缝，不是实际服务、可信人类或新runtime门；没有重跑探索94项。

新的fresh-context实现审查和原结构模板在途；未因安装通过提前关闭本片。后续如有行为修正，仍须新冻结和实际受影响验证。

### r1 实际审查结果与未覆盖的原生边界

[新 fresh 实现源审](2026-11-16-design-packet-inspection-source-review.md)需求／维护性均 request-changes，R1／P1：真实 `reference._task_operation` 使用注册安装的 `.venv/bin/python`，该原127项锁环境没有 jsonschema；`_inspect_design` 的局部 `.contracts` 导入会在有packet时失败。短 `-S` 导入红例用于定位，尚非真实任务进程验收。r1的118源码／安装绿色只来自原SDK fixture，不能覆盖或消除该真实调用者的依赖缺口。原锁／283不能为本片修改，也不在原生层复制通用schema验证器。

同一安装运行原结构模板，Codex **77.960秒、request-changes**：两项P2分别为重复source ID在领域检查前覆盖观察，及Markdown／HTML引用未核各自body media type。原始10个完整文件170,413B、完整五文件patch和3祖先资源全部进入246,404B stdin，SHA256 `5a3e3d4a7b1fcc8d2d877a25b943d9b4aec445d69d60119930e725d8fc5ad05a`；原result SHA256 `add9a0d6756bc1f0ec2afdc7909d498318d8d38469b6feebfa75f0db9d315b91`，见私有 `self-review-r1-codex/`。

实施者已收到三项问题，先核真实可达性，再把schema验证留在实际应用边界、原生owner保留safe adapter完整读取；具体最小方案和真正应用→所选解释器回归随后记录。原r1冻结／wheel／118／模型结果不覆盖、不转授后继；未提交或开放新能力。

## r2：实际应用／native 边界与两项材料修正

本节是当前实现候选；上文五文件源码、r1 wheel／118／Codex request-changes 均按原身份保留。r2 仍在基线 `562394c839e9353e4f889a0b03e749ca32783936` 的原隔离树，新增实际变更文件 `src/ergora/reference.py`，完整候选共六文件；没有改原锁、283、native/M5、根 PLAN 或模板默认。源码修正和定向检查已完成，新的安装、原模板及独立复核由主控接续；不自批、不结片。

### 最小 owner 调整与 finding 处置

1. **独审 R1／native 缺 schema 依赖。** 实际 `reference.task_plan → _task_operation` 确实使用注册的 `.venv/bin/python`，原127锁不含 jsonschema。原 `_inspect_design` 改为 `_read_design`，只有 `_plan` 这一生产 caller；它只用原 adapter 读取完整 packet／source 原字节，返回内部 `design_read` 事实：内置 profile、packet、由原 history／envelope／seed 取得的 expected 身份、实际来源 SHA／bytes／读取状态和原 work unit IDs。为保证读取可达且受限，仅核所需的 source 列表／记录形状、access／body／路径、容量及唯一 ID，不复制完整 schema validator。原 `_plan` 的原件绑定和聚合上限保留。
2. **应用结构与领域边界。** 现 `reference.task_plan` 在原 native 操作返回后，使用应用已有 `contracts.validate` 校验完整 profile／packet，再调用原纯 `task_design.inspect_packet`，核最终公共结果容量并生成检查身份。只有全部成功才返回公共结果；`design_read` 消费后删除，结构失败抛出原 ValueError，不以部分结果替代。无 packet 仍沿原返回。当前纯检查唯一生产 caller 改为该现有应用用例，没有新增服务／调度器／registry 或另一份 validator。
3. **原模板 P2／重复 source ID 覆盖。** `_read_design` 在任何 source I/O 之前预扫全部 source ID；重复时明确拒绝并给原 ID，不构造能覆盖前件的观察字典。纯领域检查仍对其他 typed ID 做其原有关系检查。实际 digest／byte count 与 packet 声明的比较归纯 owner，先复制观察再派生状态，不修改 native 原观察或让替换记录令 K 变 supplied。
4. **原模板 P2／报告媒体角色。** 纯 owner 保留 full access／report type 要求，另对 `report_ref` 精确要求 `text/markdown`、`html_ref` 要求 `text/html`。不符时在对应 JSON 路径返回 `report_media_type_mismatch` 与 expected／actual media type。JSON 原件不能同时充当 Markdown 与 HTML。

新运行边界没有获得身份／批准／执行能力。内置 profile 仍 inspection-only、runtime_enforced:false；Q 保持未决，K 的可读供给仍不替代 owner 处理。Response／Resolution 仍仅是 schema 合同，原 writer／input／journal／批准路径不变。

### 实际红／绿与测试范围

原始输出和准确 argv 全在 ignored `.ergora/checks/design-packet-inspection/r2/`，未覆盖 r1 目录中的原件。

|原件|实际观察|
|---|---|
|`original-three-red.*`|r1 产品上新增三例共 3 failed／5.72 秒。其中重复 source ID 的 mismatched-first／valid-second 未被拒绝、JSON 同时满足两种报告且 valid=true，是两项真实 P2 红例。第三例先撞到 fixture 共用 tmp/config 的 roots 漂移，不当作 R1 产品红例。|
|`original-native-red.*`|把轻量 pending fixture 放到独立子目录后，真实 registered fixture 尚缺显式 adapter 配置，1 failed／6.73 秒；保留该 fixture 配置失败，不冒充缺依赖复现。|
|`original-native-configured-red.*`|补齐原 FileAdapter 的受控 fixture 配置之后，原 `reference.task_plan → _task_operation → 注册路径的 native Python → main → _plan` 实际返回 `BLOCKED: Native jsonschema is unavailable`，**1 failed／5.02 秒**。原 creation／submission／memo／history／envelope／receipt 均走真实 owner，没有 patch 主边界或 `_Submission`。|
|`three-green.*`|同三例在 r2 产品上 **3 passed／5.73 秒**。真实 native 进程还读了一份缺 `problem` 的 typed packet，应用仍用现 schema 整体拒绝。|
|`source-frozen.*`|新冻结输入下运行完整 `tests/test_task_plan.py`、完整 `tests/test_task_inputs.py` 及原 exact-owner／attempt 后 unknown 各一项，**121 passed／30.76 秒**，driver 31.336 秒。组成是 plan55＋旧input64＋原批准2；精确命令、完整 stdout／stderr 分列保留。|
|`source-static.*`／`reference-files.json`|4 个 Python AST、Draft2020-12 schema、实际隔离源码导入通过；283 份参考完整原字节及执行位仍与基线同一。|

新增进程例沿现注册／创建／提交 fixture 和真实 SDK protobuf／converter；只替换服务端 `connection.connect` 叶子，并在所选 fixture executable 用 `-B -S` 及 import hook 明确模拟 native 无 jsonschema。主 `task_plan`、原 `_task_operation`、被选中路径的进程、`main`、`_plan` 和 `_Submission` 未被替换；原 runtime 文件树前后同一。它验证了依赖缺失的真实进程边界，不声称重建／安装了原127项环境或运行了真实 Temporal。原轻量证据 fixture 继续用于有界文件／QK 检查；没有以它替代这个新增真实边界例。

### r2 完整冻结与交接

|原件|准确身份|
|---|---|
|`r2/source.patch`|六文件完整 tracked＋untracked patch，**83,245B**，SHA256 `2cffd953981c87e165794e5e4ff2c27451234dfd95a4dd09731051bc4136aaa2`。HEAD 仍为原基线，无产品 commit。|
|`r2/source-inputs.json`|2,053 全仓 tracked＋新输入，36,530,525B，每项含完整 SHA／bytes／stat mode／执行位；清单 SHA256 `ea954a61c8098c14a4d855f76aee523afac49baa47b507e8490ebbc02f943adf`。|
|`r2/source-inputs.tar`|完整输入 tar SHA256 `4ad9baaa3ee67b75712fcec3d19723d4093d07a96624375374b1a593d8974a20`。该数量仍是源码输入，不是安装包计数。|
|`r2/inputs/`／`inputs.json`|本轮根／src／tests 规则、当前 PLAN、组件协议、已审设计、r1交付未追加本节前的原件、fresh R1 和 Codex 两 P2 报告均另存完整身份。|
|`r2/verify-freeze.*`／`source-whitespace.*`|121 项检查前后全部 2,053 输入的名字／完整字节／mode 保持；完整 patch reverse apply、所有新增行空白、交付相对链接及原 r1 patch／tar 字节保持检查通过；`git diff --check` 亦通过。|

冻结后上述核对已通过；报告自身身份仍单列，不反向放入正文。r2 不继承 r1 的 wheel／安装118／原模板结果；后继需要同一新候选的新非 editable 包、受影响安装检查、自身原结构模板和同片 fresh 复核。所有原明确未验／未开放范围保持；本轮没有安装、模型、外部服务、commit／merge／push。

## fixed-r3：两个公开读取入口统一验证

主控把作者 r2 六文件变更移植到已审主线 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`，固定父候选 `a8d1855fb62513f5faeb8b3f9b1cfe4a38c1c0a2`。五个文件原字节／执行位同作者，`task_plan` AST 同一；适配后的六文件 patch 为 `292bd72581db146417c80262ad64a4207cdae8247f6677edeb25d128ea98721d`。这一候选新 wheel `6651a8ed42de9a280d03a72601606ac51e67410823fefe5da90f5d20896e37c3`、core／SDK各668产品、858构建输入、安装 **121 passed** 已独立留存，但不转授下述修正。

r2 原结构模板 Codex 48.475秒 request-changes，发现新的 R2/P1：公开 `reference.task_approval(..., 'inspect-plan', ...)` 可绕过 `task_plan` 应用校验，返回内部 `design_read`。当前 `tasks` 生产入口实际另走 `task_plan`，但该公开 callable 和 native operation 确实可达；这是读取合同遗漏，不能描述成已发生的执行／身份绕过。同片 reviewer 已确认并撤回该阶段终批，保留前 R1／两P2已关闭事实。

最小修正只有原 `task_approval` 的两行显式 inspect-plan 路由，调用原 `task_plan`；其他批准操作保持原 `_task_operation`。原真实选定 native executable 回归扩为两个公共入口各读完整合法 packet，再各拒绝缺 `problem` 的 packet；没有新 helper／测试文件／validator。新回归在旧产品 **1 failed／8.61秒**，确实取得缺少公共 `design` 的 raw handoff；修后 **1 passed／9.05秒**。原 native main／`_Submission`、history／envelope／safe reads 和无 jsonschema import hook均保留，只替换远端 SDK connection 叶。

当前 fixed-r3 patch 共六文件、83,356B，SHA256 `4daea8ea9a08f994d9b318ee162d6b58bf2fa9ceb3008859bb7adc633642304a`；完整2064输入清单 SHA256 `a5cc6b16900c2226f061732ef24f9bc65b03aa9d9766ef7a42ddc13175a6e2b3`。源码受影响组为完整 `test_task_plan.py` 和原 exact-owner／attempt后unknown各一项：**56 passed／1 skipped／38.10秒**；skip仅为源码开发解释器没有可选 FastAPI，安装组实际补验，不能称源码57全过。无关且未变的64项 input组不重复运行；原r2的121单独保持。

新非editable wheel SHA256 `1622eba2e63f9ec4ef6d0950ffd77d2c6d3270d649dc6965a5ca2318df7e4a2e`。core／SDK各668产品，源／wheel／实际site-packages完整原字节及执行位同一、283参考及依赖检查通过，core无SDK、SDK1.34.0；857项构建／检查输入和完整2064源输入分别冻结，不混为一个集合。安装原受影响组 **57 passed／JUnit48.360秒**，无skip；完整命令／原输出／JUnit在私有 `package-r3/`，不把本地受控SDK接缝说成真实服务验收。

同一安装再次使用自身原结构模板：Codex **31.855秒、approve**；11个完整文件235,604B、完整六文件patch与全部3项祖先资源进入325,997B实际stdin，SHA256 `0b32aaf16942eea5624fd842d57ee0a153a9cea9a657050f47851fcd7a905f12`；原result SHA256 `4b2e9cf97d8915441b77a03b347c9d62e5d0248c8c6bbc7ba21fa72211d374ba`。这是supplied-text结构审查，安装／独立review仍分别记账，不反复刷旧r2 verdict。

红／绿／源码／安装四命令实际捕获201份自有进程身份记录，逐PID／BOOT／start检查均absent；只证明所捕获命令后代，非全系统扫描。最终完整源输入、patch与`git diff --check`复核同一。准确原件在私有 `fixed-r3/`、`package-r3/` 和 `self-review-r3-codex/`；原r1/r2失败与结果不覆盖。当前等待同片独立需求／维护性最终复核，尚未集成或推送。input12、State6、journal、可信actor、G1/G2及实际执行等明确后继边界保持。


## 当前片闭合与普通导入

[同片最终独立复核](2026-11-16-design-packet-inspection-source-review.md)需求／维护性两轴 **approve／开放0**，报告SHA256 `841b0efbdeec33d933f9636185db67964414b79f50fecfdb8c0d9e008d9f0108`，R1/R2及两原P2均关闭。准确源码已固定 `cb861ea7138627d6646e8de1c0867a3ed92ce474`，对0a5a0ff的完整patch仍4daea8ea；普通导入开发分支为 `3d632a78b6acc4f0027b2225e7771a5da927af81`，src与tests完整Git子树同一。inspection-only片的源码／新安装／原模板／独立门闭合，公开推送及准确候选自己的CI另验。新profile可执行、可信人类、journal、G1/G2或真实训练仍未开放；后继S1以此准确产品为依赖。
