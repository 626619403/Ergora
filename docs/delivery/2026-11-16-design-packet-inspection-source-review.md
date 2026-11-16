# WA5a-1：fresh-context 独立实现审查

2026-11-16。Reviewer：`wa5a1_packet_inspection_review`，新的独立上下文。按原始需求、D1–D4、批准的 r2 设计、实际差异及真实消费者顺序检查，之后才读实施者交付；应用 `maintainable-project-delivery` independent-review brief 与 `ergora-codebase-quality` module-design／test-seams。只读源码，唯一写入为本报告。

**需求符合性：request-changes；维护性：request-changes。开放阻塞项 1（R1）。** 本结论只针对 WA5a-1 的材料检查实现，不评判尚未实施的 G1/G2、人类讨论写入或后续产品能力。其余已检查范围未发现需要修正的实证问题。

审查候选为隔离树 `.ergora/worktrees/design-packet-inspection`、分支 `feat/design-packet-inspection`，HEAD／基线均为 `562394c839e9353e4f889a0b03e749ca32783936`。根工作树的其他在途差异不属于候选。先列目录确认实际 patch 名为 `.ergora/checks/design-packet-inspection/source.patch`，不是交接简称中的 `source-r3.patch`；完整 70,359B patch SHA256 为 `cfde3166b6f1c713f482ca6bc7585619f6e07f5a5bc3882de4eae63ccafd64dc`。

|完整检查的候选文件|SHA256|
|---|---|
|`src/ergora/data/design-profiles/framework-development-v1.json`|`e4cb6ac52415ce0fd0d970f4462759c2d7492b8395d133e29e590bbfe0051137`|
|`src/ergora/data/schemas/task-design-v1.json`|`a733a2028ec1927b979e109c122d7509553efc7585f9a5e0115a8aa382bef721`|
|`src/ergora/reference_task_approval.py`|`cd6da00413e1c9a90a204b13711f538ffd17a73809dd900ee214de6960f5e225`|
|`src/ergora/task_design.py`|`516127480fbb9602bd7a51b035be8bc46d525ddfa5ca1ec1c28a5a002fb7a87c`|
|`tests/test_task_plan.py`|`904d9e812214a15882251f15ec8d6b1f3e77b902aad33ea170d8036b53be4682`|

已独立核对上述文件的完整 SHA／bytes／执行位与冻结清单一致。`source-inputs.json` SHA 为 `d5e3c51328fd9c0d23bb7aa3b2b62d239d9561a235991a9ce86bcd775187b066`，`source-inputs.tar` SHA 为 `f93bc99af6dce7a5354d40563ede0775c25cd7ebc5062fda6128d3f6844c4499`，均与交接一致。批准设计为[WA5a／b r2](../plans/2026-11-16-design-knowledge-gates.md)，实际 SHA `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`。

**R1／P1：schema 校验进入锁定的 native 解释器，标准安装无法检查任何 design packet。**

- 位置：`src/ergora/reference_task_approval.py:23`（由 `:159` 调用），以及未改变但决定实际执行环境的 `src/ergora/reference.py:791`、`:800`。
- 可达场景：正常注册项目使用原 platform bootstrap 生成的安装，pending plan receipt 明确包含合法 `design-packet`，操作者沿 `tasks.plan → reference.task_plan → _task_operation → reference_task_approval._plan` 读取。`_task_operation` 明确启动 registration 指定的 `installation/.venv/bin/python`，仅通过 PYTHONPATH 放入应用源码；应用环境安装了什么包不会因此进入该 native venv。
- 证据：新 `_inspect_design` 的第一条导入为 `.contracts.validate`，`contracts.py:7` 又顶层导入 `jsonschema`。原 `data/reference/platform/bootstrap/install-multi-agent-platform.sh:73` 使用 `uv pip sync --require-hashes` 同步原 `requirements.lock`；该锁全部 127 个 distribution 没有 `jsonschema`。这是支持的锁定安装合同，不是偶然缺包。该参考锁属于本片禁止修改的 283 资源。
- 最小红例：本次只运行标准库短 probe，`python -B -S` 加入候选 `src` 后可成功导入 `ergora.reference_task_approval`；调用 `_inspect_design(None, None, {}, {}, 'a' * 64)` 立即得到 `ModuleNotFoundError: No module named 'jsonschema'`，尚未读取任何参数或材料。这单独证明新导入依赖；结合上述真实 launcher／锁定环境，可确定合法 packet 也在该处失败。没有 packet 时不会进入此分支，旧路径继续正常。
- 后果：公开 plan inspection 返回 `BLOCKED: No module named 'jsonschema'`，不能交付本片要求的完整材料与精确 Q/K 缺项。旧输入、旧批准及 helper 测试通过不能弥补该路径。
- 最小修正方向：将完整 `contracts.validate` 与其后的 typed 领域检查放回使用应用依赖的现 `reference.task_plan` 返回边界；native reader 保留原 history／receipt 校验、安全路径、有界全文读取及所需原身份／观察元数据。native 读取 source 列表所需的最小 I/O 形状和容量约束应留在实际读取边界，不复制通用 schema validator。不得通过改原参考锁、临时给 native 环境装应用依赖、要求用户手工补包、跳过 schema，或新建可执行 v12 入口来遮盖此问题。
- 验证：在选定 native 解释器禁止／确实没有 `jsonschema` 的条件下，经 `reference.task_plan` 的真实进程入口读取一份显式 packet，并在应用边界观察完整正文、原绑定和精确 Q/K；再用一个无效 typed packet确认仍经过原 schema 校验。同时保留无 packet 兼容和旧 approval／unknown 接缝。只测 `task_design.inspect_packet` 的 `-S` 导入不能保护该失败。

**其余需求与维护性检查。**

`reference_task_approval.py:136–162` 只在 receipt 显式列出 packet 时扩展读取，旧 profile 的必需 artifact 列表未被改写。schema、packet、报告和 source 原字节分别受原 receipt／canonical 身份及 safe read 约束；缺失、拒绝、摘要／字节数漂移保留可观察来源状态，危险路径、编码与容量错误显式失败。检查点未增加批准、signal、journal mutation、input12、definition8、State6 或模板默认变更。

`task_design.py:65–90` 保留最低题正文／理由与 required_by，每个现存 Q 均 unresolved；`:119–160` 将 K 的材料供给与 owner 决定分开。`:165–167` 永远保留 policy／owner 不可用。reader 的 `:69–78` 明确报告内置而非任务冻结的 profile、inspection-only、runtime_enforced:false、未核前版链／声明时效，以及关闭的三项能力。没有将 packet 自报 owner／答复升级为可信身份，也没有声称本片已阻断旧 runtime 的批准或执行。

纯 `task_design` 当前只有一个生产 caller，这是实施者已明确披露的事实。其 167 行内聚地隐藏跨数组引用、最低题、知识和 work unit 关系；若删除边界，这些领域义务会回到负责 I/O／history 的 approval owner。保留该纯规则模块有具体职责理由，不需要编造后继已实施消费者。单 caller 的 I/O 编排仍留原 approval 文件。R1 所指的 schema 依赖位置是实际需要修正的边界，而不是要求额外抽象层。

除 R1 外，结构 schema、安全读取、原身份及领域关系检查各有不同保护对象；未发现应删除的实证冗余 guard。新增用例扩原 `test_task_plan.py` 而非新增测试框架／CI 文件，实际使用原 SDK message／codec／history、envelope／receipt 和本地原文件；测试能够观察全文、身份漂移、只读性与 Q/K 结果。其遗漏是 R1 的真实解释器接缝：`tests/test_task_plan.py:153` 直接在测试解释器运行 `_plan`，`:432` 的 `-S` 子进程只运行纯 inspector 与旧 input reader，不调用 `_inspect_design`。

**已核证据与限制。**

读取了原始需求／D1–D4、根与适用 src/tests AGENTS、总 PLAN、组件协议、批准 r2，完整五文件及原 tasks／reference／submission／creation／input／adapter 的相关调用。完成候选文件身份、Python AST、JSON 解析、patch／输入归档摘要的短静态核对，并运行上述无安装、无服务的依赖红例。没有重跑长批、安装、网络、模型或业务执行，没有修改源码／提交，也没有读取凭据或环境快照。

已查看 `source-frozen-r1` 准确命令／stdout／stderr：**118 passed／25.11 秒**，组成是完整 plan 52、旧 input 64、旧 exact-owner／attempt 后 unknown 各一项。`source-static-r1` 报告 283 原资源完整字节与执行位同一；本次确认完整变更清单没有参考资源差异，未重复该全量原件比较。先前 94 项仍只按探索证据处理。

主控后续追加的新 wheel `24a06047aa815361d0cd6e5c9f74cb2f647ff8dfc1cd128d4609a7d1c6e73886`、core／SDK 666 完整文件、安装同四入口 **118 passed／37.87 秒**，已经在[实施交付](2026-11-16-design-packet-inspection.md)单列；本审查未代验其私有安装 raw。相同测试入口仍没有实际含 packet 的 registration-native 进程边界，不能关闭 R1。该证据与源码身份均保留，修正后的新候选需重新冻结并验证受影响路径。

本片完成仍须 R1 修复及同片复核、修后相应安装与自身模板证据。可信 owner／ACL、实际 Temporal、人类旅程、G1/G2、修订／封存／撤回、work／训练、公开发布及候选自己的 CI 均未由本源审认证；它们按已批准后继分片验收。

## r2 同片复核：源码两轴 approve，开放 finding 0

2026-11-16；同一独立 reviewer 按同片修正继续复核。**本节是当前源码判定：需求符合性 approve，维护性 approve；R1 及原模板两项 P2 均关闭，新增阻塞／非阻塞 finding 0。** 上文 r1 request-changes、原 probe、118 与原安装／模型结果保留其原范围，不由本节改写。

复核先读原范围及六文件实际差异、原应用→native 调用，再读 r2 交付和模型原报告。最终待验源码为 `.ergora/worktrees/design-packet-inspection-fixed` 的 `feat/design-packet-inspection-fixed-r2`，固定提交 `a8d1855fb62513f5faeb8b3f9b1cfe4a38c1c0a2`，唯一父 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`。本次不重新认证父提交所含 M5/native 能力。

|最终固定候选文件|SHA256|
|---|---|
|`src/ergora/data/design-profiles/framework-development-v1.json`|`e4cb6ac52415ce0fd0d970f4462759c2d7492b8395d133e29e590bbfe0051137`|
|`src/ergora/data/schemas/task-design-v1.json`|`a733a2028ec1927b979e109c122d7509553efc7585f9a5e0115a8aa382bef721`|
|`src/ergora/reference.py`|`e8d2c8c3f810600f3b981c0a3ad69e8824074f648b45c02511a5fa3a62b4a333`|
|`src/ergora/reference_task_approval.py`|`40dc8789cbd1471df25fe424dd35ab8f5f6b6f60c42eeddb9bdac98c15467656`|
|`src/ergora/task_design.py`|`f0586db715ebb90c173204b7ab5fbe3efc619761fdf491ece764b76676fdea41`|
|`tests/test_task_plan.py`|`5c53a855188c1bffe031cf38e68e691c72278b3b3dd3415320bc120976752022`|

已独立比较完整 commit diff：`fixed-r2/source.patch` 82,849B，SHA256 `292bd72581db146417c80262ad64a4207cdae8247f6677edeb25d128ea98721d`，与该父／候选的 `git diff --binary` 逐字节同一；工作树干净。六文件 SHA／bytes／执行位与 `fixed-r2/changed-files.json` 相符，AST／JSON 解析通过。适用 AGENTS／组件协议没有被本片改写。

作者 r2 树仍基于 `562394c839e9353e4f889a0b03e749ca32783936`：`r2/source.patch` 83,245B／SHA `2cffd953981c87e165794e5e4ff2c27451234dfd95a4dd09731051bc4136aaa2`；2053 输入清单 SHA `ea954a61c8098c14a4d855f76aee523afac49baa47b507e8490ebbc02f943adf`、tar SHA `4ad9baaa3ee67b75712fcec3d19723d4093d07a96624375374b1a593d8974a20`，均独立核对。上述五个非 `reference.py` 文件在作者／最终固定树完整 bytes 同一；`reference.task_plan` AST 同一。两个 `reference.py` 的其余差异仅为父基线已有的 native descriptor／source-v2 邻接内容，当前六文件 commit 中没有重新修改它们。

|原 finding|修正与复核依据|处置|
|---|---|---|
|独审 R1／P1：native 缺 `jsonschema`|最终 `reference_task_approval.py:20–68` 的 `_read_design` 只加载内置 profile、解析安全读取所需形状并用原 adapter 读完整事实，不导入 contracts／schema。`reference.py:755–791` 的现 `task_plan` 等原 `_task_operation` 返回后，才在应用解释器运行原 `contracts.validate` 和纯 inspector；仅完成校验才发布结果，内部 `design_read` 被删除。|关闭|
|原模板 P2：同 source ID 覆盖前件观察|`reference_task_approval.py:33–39` 在任何 source body I/O 之前预扫所有 source ID，重复即给原 ID 拒绝，不形成覆盖观察。`task_design.py:113–125` 复制 native observations 后比较声明 SHA／bytes，派生状态不修改原事实。mismatched-first／valid-second 回归实际观察拒绝。|关闭|
|原模板 P2：JSON 充当 Markdown／HTML 报告|`task_design.py:60–66` 在 full/report 关系之外，分别要求 `text/markdown` 与 `text/html`，不符在 `/report_ref`、`/html_ref` 给 expected／actual media type。对应回归同时观察两角色失败。|关闭|

R1 的关键边界已保留：`reference.task_plan → _task_operation → registration 指定 executable → reference_task_approval.main → _plan → 原 _Submission`。最终 `reference.py:834–851` 仍选择原安装解释器；native 没有借应用依赖、临时 v12 或另一份通用 validator。source 列表上限／记录形状／access／body／安全路径与唯一 ID 是 schema 校验前实际 I/O 所必需的局部约束，完整 typed 校验只有应用 owner 一份。领域关系与原字节读取各归其 owner，无新增单用转发层。

已检查新增 `tests/test_task_plan.py:425–544` 的真实接缝：使用既有 registration／creation／submission 记录与 SDK protobuf／converter；没有替换上述主调用边界，连接服务的 `connection.connect` 是替身。所选 fixture executable 以 `-B -S` 启动，追加测试 SDK 所需 purelib 后用 import hook 显式禁止 `jsonschema`，同时核执行命令与最终未加载 schema。绿例还读取一份缺 `problem` 的实际 packet，由应用 schema 整体拒绝，不能把 native 事实交接当作部分验证成功。它保护的是本次依赖／进程边界，不是原127项环境的完整安装或真实 Temporal。

已查看相应准确 argv／raw，按实际失败区分证据：`original-three-red` 的前两项是 duplicate source 与报告媒体的产品红例；其第三项 adapter roots 漂移及后续 `original-native-red` 缺 adapter 配置，仍只是 fixture 失败。补齐 fixture 后，`original-native-configured-red` 在原 r1 产品沿真实进程入口得到 `BLOCKED: Native jsonschema is unavailable`（1 failed／5.02 秒）。修后 `three-green` 为 **3 passed／5.73 秒**；`source-frozen` 为 **121 passed／30.76 秒**（plan55＋旧input64＋原批准2，driver31.336秒）。这批是作者 r2 树的准确源码证据；未称为最终组合的新安装验收。

本 reviewer 另运行无写入短 probe：在最终固定树 `python -B -S` 中导入并调用 `_read_design` 的空来源事实读取，确认未加载 `jsonschema`／`ergora.contracts`／Temporal；原 native lock 仍为 127 distributions 且无 `jsonschema`。该 probe 只复核依赖移出，不冒充完整 `_plan` 服务旅程。`r2/source-static` 的 283 份原参考 bytes／执行位保持结果已核 raw，最终 commit 差异亦无任何原参考变更；没有为本片修改锁定环境。

inspection-only 语义继续成立：无 packet 直接返回原结果；旧 `_Approval`、writer／input／模板默认不变。内置 profile 仍非任务冻结 policy，所有 Q 保持未决，K supplied 仅表示材料供给；owner／批准／执行能力继续关闭。完整原字节、声明和实际观察、canonical packet 身份与检查身份仍分开。没有增加 runtime gate、journal mutation 或可信身份主张。

本节只追加源审结果，没有编辑源码、运行长批、安装、模型、网络或真实服务。最终 `a8d1855…` 的新非 editable 包、安装检查及自身模板仍由主控单列新证据，原 r1 包／118／模型不转授；收到前不据本源码 approve 宣布完整切片验收完成。原有真实身份、Temporal、G1/G2、讨论写入、work／训练、发布和候选 CI 等未验范围保持。

## r2 补充：公开 approval 入口的材料旁路待修

主控随后提供 `self-review-r2-codex/review.md` 的新 P1。本 reviewer 已回到 `a8d1855…` 实际路由核对并确认；前节源码 approve 不作为当前终批。**当前需求／维护性均 request-changes，开放 1：R2／P1（公开读取校验旁路）。** R1 和两项原 P2 的已关闭处置不变。

位置为 `src/ergora/reference.py:750–752`：公开 `task_approval(project, home, 'inspect-plan', payload, timeout=...)` 仍直接返回 `_task_operation` 结果。原 native `main` 确实支持此 operation 并进入 `_plan`，因此一份缺 `problem`、但具备有界 source 读取形状的 packet 可沿该公开入口返回内部 `design_read`，跳过 `task_plan` 中的 schema／领域校验。它没有授予可信 owner 或执行权限，但违反了公开调用者不能收到未验证中间材料的本片合同。

当前仓库 `tasks.py` 的生产消费者用 `task_approval` 做 status／prepare／dispatch／resume，正式 plan 另走 `task_plan`，没有发现业务 caller 已使用这条 inspect operation；这不被写成既有业务现场故障。问题是现公开 callable 与 native operation 合成的可达接口，不能靠当前没有该业务 caller 视为隐藏内部接口。最小修正为仅将 `task_approval` 的 `inspect-plan` 转调已有 `task_plan`，其他操作仍沿原路；扩现新增的真实 native 进程回归，确认两个公开入口均拒绝无效 packet，且合法返回均无 `design_read`。主控已开始同片修正，新完整 freeze／受影响检查及新包／模板待提供后复核，本报告不提前关闭 R2。

## fixed-r3 终复核：两轴 approve，开放 finding 0

2026-11-16；同一独立 reviewer 继续同片复核。**当前最终判定：需求符合性 approve，维护性 approve；R2／P1 关闭，R1 及两项原 P2 保持关闭，开放阻塞／非阻塞 finding 均为 0。** 本节取代上节的当前 request-changes，保留全部历史证据与处置。以下新证据足以接受本次 WA5a-1 inspection-only 切片。

结论绑定 `.ergora/worktrees/design-packet-inspection-fixed`、分支 `feat/design-packet-inspection-fixed-r2` 的 HEAD `a8d1855fb62513f5faeb8b3f9b1cfe4a38c1c0a2` 加当前未提交的 `reference.py`／`test_task_plan.py` 两文件修正。唯一父基线为 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`。完整六文件 `fixed-r3/source.patch` 为 83,356B，SHA256 `4daea8ea9a08f994d9b318ee162d6b58bf2fa9ceb3008859bb7adc633642304a`；已与当前相对父基线的完整 `git diff --binary` 逐字节核对。2064 项 `fixed-r3/source-inputs.json` 的 SHA256 为 `a5cc6b16900c2226f061732ef24f9bc65b03aa9d9766ef7a42ddc13175a6e2b3`，所有输入 bytes／SHA／执行位均与当前工作副本一致。

|fixed-r3 完整候选文件|bytes|SHA256|
|---|---:|---|
|`src/ergora/data/design-profiles/framework-development-v1.json`|2390|`e4cb6ac52415ce0fd0d970f4462759c2d7492b8395d133e29e590bbfe0051137`|
|`src/ergora/data/schemas/task-design-v1.json`|28874|`a733a2028ec1927b979e109c122d7509553efc7585f9a5e0115a8aa382bef721`|
|`src/ergora/reference.py`|56453|`4fc5d60e07342bb86bbbf465395b62d2d35f78fcc780502167144026a31cecaf`|
|`src/ergora/reference_task_approval.py`|20834|`40dc8789cbd1471df25fe424dd35ab8f5f6b6f60c42eeddb9bdac98c15467656`|
|`src/ergora/task_design.py`|11281|`f0586db715ebb90c173204b7ab5fbe3efc619761fdf491ece764b76676fdea41`|
|`tests/test_task_plan.py`|41961|`0f11bfcfd4d16468130f808462fe449a53295a2679e72a906dc5c666bd5d8d29`|

**R2 的修正与覆盖。** `reference.py:752–754` 将 `task_approval(..., 'inspect-plan', ...)` 直接转入已有 `task_plan`，因此两公开 reader 共用应用解释器中的完整 schema／领域校验及内部 `design_read` 移除；其他 approval operation 继续原 `_task_operation`。这两行复用现有责任边界，没有另建 validator 或转发抽象。`tests/test_task_plan.py:425` 的现有真实 native 接缝回归现在对两个公开 reader 逐一检查合法结果的 `design`、完整性、未 ready 和无 `design_read`，再将实际 packet 删除 `problem`，确认两入口均由应用 typed 校验拒绝。原 launcher／main／`_plan`／submission／history／本地原文件均保留，服务连接 leaf 仍为 fixture；selected executable 继续以 `-B -S` 运行并明确禁止 `jsonschema` 导入。

已检查 `fixed-r3/public-route-red.*` 与 `public-route-green.*` 的准确命令及原始结果：旧产品配扩展回归为 **1 failed／8.61 秒**，在 approval reader 取得原中间交接后触发 `KeyError: 'design'`；修后为 **1 passed／9.05 秒**（JUnit 9.047 秒）。该红例是本次公开返回合同的产品失败；绿例同时覆盖合法返回与非法 packet 拒绝。R1 的 native 依赖边界、source ID 预扫和报告媒体角色规则均保持原已审实现，没有新 finding。

**本候选的新验证证据。** `fixed-r3/source-affected.*` 的完整 plan 组加原 exact-owner／attempt-after-unknown 两入口为 **56 passed，1 skipped／38.10 秒**；JUnit 精确为 57 项、1 skipped、0 errors／failures、38.092 秒。跳过项是原 `test_cli_and_api_forward_the_exact_read_request_without_confirmation`，开发解释器缺 `fastapi`。它不计作源码通过项；后述安装组实际覆盖并通过此项。本轮未重跑未变的旧 input 64 项，先前 r2 的 121 项继续仅属于其原候选证据。

新 wheel `package-r3/dist-r3/*.whl` 的 SHA256 为 `1622eba2e63f9ec4ef6d0950ffd77d2c6d3270d649dc6965a5ca2318df7e4a2e`。本 reviewer 独立核对 857 项 build／check 输入、179 项测试／example 副本、668 项产品源码及 wheel 完整成员集合，再逐字节／执行位比较源码、wheel 和 core／SDK 两套实际 site-packages；均一致。两套安装各自的 283 项原参考资源摘要均保持，core 无 Temporal、SDK 为 1.34.0 的依赖身份与记录相符，两个 `uv pip check` 均 exit 0。`package-r3/installed-selected-functions-r3.json` 所列同一完整 plan＋原批准两入口的安装组为 **57 passed／48.37 秒**，JUnit 精确 48.360 秒，0 skipped／errors／failures；driver 为 49.579 秒。此处 57 是该次安装运行的总数。

**原模板新一轮复核。** `self-review-r3-codex` 的 Codex backend 为 exit 0／succeeded／approve，31.855 秒（原始 31.85465406673029 秒），run `13ed6e1ea3ae45cebad1ddf4daa0fd3c`。独立核对其 11 份完整 scope 文件共 235,604B 与当前候选同一，完整 patch 与上述 fixed-r3 patch 同一；实际归档 stdin 同时包含完整源码／patch、完整 task 和全部 3 项祖先资源。stdin 为 325,997B，SHA256 `0b32aaf16942eea5624fd842d57ee0a153a9cea9a657050f47851fcd7a905f12`。原始结果 SHA256 `4b2e9cf97d8915441b77a03b347c9d62e5d0248c8c6bbc7ba21fa72211d374ba`，与归档 `state/runs/.../result.json` 逐字节同一；native stdout 的 `result` 是该文件绝对路径，其 `result_sha256` 也相符。模板报告明确只对供应文本作结构／接口 approve，安装行为的依据仍是上述独立安装证据。

**资源与范围。** 本轮 red／green／source／installed 四条受检命令分别捕获 23／35／71／72 条实际归属进程身份，共 201 条。已核 `package-r3/final-freeze-resource-check.json` 的全部 absent、源码未变及 diff check，并按 PID＋boot ID＋start ticks 独立复查当前 `/proc`：live 0、unknown 0。该结论限于这四次命令捕获的后代，不外推为全系统清理。

inspection-only 合同保持：无 packet 保留旧结果；Q 全部未决，K supplied 仅表示材料供给；packet 不认证 policy／owner／答案，`inspection_only:true`、`runtime_enforced:false`，批准／resolve／execute 能力继续为 false。没有 input12、definition8、State6、runtime gate、journal 写入、默认模板或原 283 参考资源变更。本次只追加本源审报告，未改源码／PLAN／其他文档、安装、跑模型／网络／长测试或提交。r1／r2 的包、运行和模板证据保留原范围；当前接受不认证原127项 native 安装全貌、真实 Temporal／可信人类身份旅程、G1/G2、work／训练、公开发布或候选自身 CI，后继分片按批准设计验收。
