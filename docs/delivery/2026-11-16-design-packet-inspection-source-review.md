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
