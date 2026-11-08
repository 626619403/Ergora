# AC3b.2a 完整输入包独立审查

日期：2026-11-09。审查轮次：r1 初审及同片 r2 复核。当前状态：**r2 需求符合性与 Standards 两轴本地审查通过，四项原发现关闭。** 精确普通交付、当前候选 CI 和远端终结仍待后续。本报告保留 r1 的需修改结论与原始发现，r2 记录追加于文末。

## 审查身份、合同与冻结范围

协调者为 fresh-context `/root/composition_inputs_review`；按 `code-review` 分别以 `fork_turns: none` 启动 `/root/composition_inputs_review/standards` 与 `/root/composition_inputs_review/spec`。三者均未继承作者实现对话。先读[本片合同](2026-11-09-composition-inputs.md)、[AC3b 分片](../plans/2026-11-08-agent-composition.md)，再读作者实现叙述。读取了项目 `AGENTS.md`、AIHERO 索引、`maintainable-project-delivery` 及其 independent-review 参考、`code-review` 和 `codebase-design`。

原始需求为叶子完整继承所有结构祖先 Skill 指令和上下文，权限不超过祖先，资源不丢失，内容可长期保存并允许后续后端替换。本片只验收静态单叶输入包：操作者提供任务，保存整图及全部引用资产，精确核叶子 prompt；当前准入与历史完整性分离。模型调用、MCP、正式批准、Temporal 嵌套执行和权限强制不在本片验收范围。整包兄弟资产供操作者离线核验，不构成选中叶子的资源授权。

Baseline 与审查时 HEAD 均为 `4f102da873fc19c8a805031106d7a7c4524d5908`；`git log baseline..HEAD --oneline` 为空。本次是未提交工作树审查，使用 `git diff 4f102da873fc19c8a805031106d7a7c4524d5908 -- <以下九文件>`，而不是空的三点提交差异。

- [冻结 scope](../../.ergora/checks/ac3b2-inputs/review-r1-scope.json) SHA256：`0fb76cd9f37267dfdab79cd37d525a6181466e0c8fc28fd4c1da182a32ea7a62`。
- [冻结 tracked diff](../../.ergora/checks/ac3b2-inputs/review-r1-tracked.diff) SHA256：`900953c91f88e43ded4fedcd958d3bbf69b249814bae275079bd6ad0822abd44`；独立重算与工作树该范围 diff 逐字节相同。
- 两个新增文件已读全文，九项内容 SHA256 均与 scope 一致。

|本片文件|审查时 SHA256|
|---|---|
|`docs/PLAN.md`|`787f70b43b89fcb4baa208024911124d97cbc781c248e9b04eca3604cb778390`|
|`docs/WORKFLOW_DEFINITIONS.md`|`b56dbbe72387512b104838ab5c7a50b326b2cb84a0ac26f590d4db4bbf80f546`|
|`docs/delivery/2026-11-09-composition-inputs.md`|`61f2a78f7751ef9b4b367c107b3ed73968cd1beaf72b424f59d55a7a25518358`|
|`docs/plans/2026-11-08-agent-composition.md`|`604739d4ff3122f9ddde8f1206bc57587756470d6452f18282fd9b056ef88a4b`|
|`src/ergora/cli.py`|`6497ff1d31e08945e9c6f27b8f75663ae9c83f2a095c93e6baa31db68eaae0c9`|
|`src/ergora/contracts.py`|`e34b4a4bb63e41a66f7768a6bcc00cb1f7cc551cc0a3a13cde74b1d8c4da9d0f`|
|`src/ergora/data/schemas/composition-input-v1.json`|`61062eceb50affa6e9a5f0d0bc72f565eaf79469912db661e9110d28af623892`|
|`src/ergora/workflow_definitions.py`|`cbcfd28918bb2b77351606b760b8099f17d9355fa706bd70b81c019d1e19eb48`|
|`tests/test_workflow_definitions.py`|`9c773bf41ceecd844d6cae3e90653530d2536de37ae8eb52fb5198aaf86149bd`|

scope 仅排除前片四份报告的状态记账：`2026-11-09-definition-admission{,-review}.md`、`2026-11-09-workflow-definitions{,-review}.md`；没有排除生产或测试代码。本报告为获准的审查输出，不改生产、测试、依赖、提交或远端。

## Standards

以下保留 Standards 子轴原始结论，未与 Spec 轴合并或重排：

> Standards：通过，限 AC3b.2a r1 九文件范围；未发现硬性规范违例或有证据需要修正的 smell。
>
> 独立 fresh-context 审查以 `4f102da873fc19c8a805031106d7a7c4524d5908` 为 baseline/HEAD，提交区间为空。九文件内容均匹配 `review-r1-scope.json`；tracked diff SHA256 与指定的 `900953c9…22abd44` 一致，两个新增文件已全文读取。
>
> 已读指定 skills、AGENTS、当前计划/本片合同、相关架构规范，以及完整变更和必要调用者。所有权与复用合理：`workflow_definitions.py:323–427` 保留静态装配职责，复用 `_Compilation`、`DefinitionLibrary`、`inventory_tree`；两个公开接口均由 CLI 实际消费。`_input_fields` 集中准备与核验共有的提示构造，是同一所有者中的必要私有算法。未引入推测性框架、额外持久状态或后端分派。
>
> 新增校验分别保护外部输入、持久内容身份、完整提示预算与复制发布失败。CLI 对任务采用有上限读取；复制后的复核及聚合限制有不同保护目的，未确认不必要重复校验。
>
> 独立执行 Workflow 源码测试：**65 passed in 2.92s**；范围内 `git diff --check` 通过。未修改文件、安装依赖或执行外部写操作。未独立验收 wheel、原生 Windows、CI、远端或真实后端；本结论不覆盖这些范围，也不构成 Spec 轴结论。

## Spec

以下保留 Spec 子轴原始发现和严重度；仅将机器绝对链接改为项目相对链接：

Spec 结论：需修改，2 项 P2、1 项 P3；本范围未见额外 scope creep。

- **IN-SP1 / P2：发布可能覆盖并发出现的目录。** 合同[第15行](2026-11-09-composition-inputs.md)要求“只向新目录原子发布”；[代码424–426行](../../src/ergora/workflow_definitions.py)先检查不存在，再调用 `Path.rename`。POSIX 上另一进程若在两者之间创建空目标目录，rename 会覆盖它。临时探针在最终 rename 前插入 `mkdir`，操作成功且原目录 inode 被替换。最小修正：发布时采用原子的“不替换已有目标”语义，覆盖该并发交错。
- **IN-SP2 / P2：组合核验忽略 JSON 数值类型变化。** 合同[第10、13行](2026-11-09-composition-inputs.md)要求保存独立 v1 结构并重新核完整组合；[代码360行](../../src/ergora/workflow_definitions.py)用 Python 字典等号比较。探针把保存组合的 `schema_version: 1` 改成 `true`、`executable: false` 改成 `0`，不改声明摘要，核验仍成功。结果是非原 v1 类型的组合被报告为一致。最小修正：使用保留类型差异的规范化序列化比较，增加上述拒绝案例。
- **IN-SP3 / P3：临时锁缩小实际文件容量。** 合同[第14行](2026-11-09-composition-inputs.md)及手册承诺包上限500文件；[代码420–422行](../../src/ergora/workflow_definitions.py)在删除两份锁文件前统计。由492文件Agent包、1文件Workflow包及6份输出文件构成的499文件包，被误报超过500文件，未发布。最小修正：聚合限制仅统计最终包内容，仍核最终总量。

新鲜上下文；核对指定9文件及必要调用者，baseline/HEAD 均为 `4f102da…`，9项哈希与给定 scope 一致。独立运行新增输入相关既有测试：**19 passed、46 deselected**；另完成上述三个临时目录探针。未改文件，未验 wheel、Windows、CI、远端或真实模型调用；维护性结论留给 Standards 轴。

两轴初始汇总：Standards 0 项、无本轴最严重问题；Spec 3 项，最严重为 P2。以上是原始结果，后续处置不删除或改写它们。

## 协调者补充核验

**IN-R1 / P2：索引在初次 inventory 后变化，可返回与当前包字节不一致的输入摘要。** [代码348、356、365–378行](../../src/ergora/workflow_definitions.py)以初次 `inventory_tree` 的文件清单形成返回摘要。request、composition、任务、prompt 和对象文件有后续比对，但两个定义库 `index.json` 的读取没有与该初始文件 SHA 对照。可达场景是在用户可写输入目录上核验时，另一编辑者于初次 inventory 后、库索引读取前改写索引。本次仅给 workflow 索引追加一个换行，保持合法 JSON 和全部解析内容；核验成功，返回 `digest` 却与同一目录的随后完整 inventory 不同。合同第13–14行要求重新核树、不信自报摘要，且内容变化明确失败。最小修正是在核验期间检查完整树前后身份相同，或至少补齐索引与初始清单的内容身份检查，并明确核验需要稳定输入。

这项检查不认证作者，也不提供对恶意同用户并发写者的隔离。拥有目录写权的人可以形成另一份内容自洽的新包；这里的问题是把一次核验读到的不同字节状态当作同一个摘要返回。增加前后身份检查也不能保证返回以后文件不再变化。IN-SP1 同样是发布目录的并发语义问题，不是新模型权限或 OS 隔离问题。

协调者也独立复现了 IN-SP1 与 IN-SP2，三个探针的原始 stdout 为：

```json
{"probe": "directory appears immediately before final rename", "succeeded": true, "existing_directory_replaced": true}
{"probe": "saved composition boolean/number type substitution", "accepted": true, "schema_version": true, "executable": 0}
{"probe": "index bytes change after initial inventory", "accepted": true, "returned_digest_matches_current_tree": false}
```

复现均在 `tempfile.TemporaryDirectory` 中准备一份含单 Agent 叶子的真实输入，复用既有测试文件的 `State`、`definition`、`leaf`、`grant` 等构造器，没有修改生产或测试。IN-R1 的关键注入如下；包装器返回原始 inventory 后只改包内索引，其他操作调用真实实现：

```python
def mutate_after_inventory(source, **kwargs):
    result = inventory_tree(source, **kwargs)
    if source == target:
        index = target / "assets/workflow-definitions/index.json"
        index.write_bytes(index.read_bytes() + b"\n")
    return result

with patch.object(workflows, "inventory_tree", mutate_after_inventory):
    checked = workflows.inspect_input(target)
actual = inventory_tree(target, label="Composition input",
                        max_directories=1000, max_depth=48)[0]
assert checked["digest"] != actual
```

## 实际检查、证据与限制

三名 reviewer 均只读必要源码和调用者，隔离探针仅写临时目录。协调者重点读了完整输入新增实现、schema、CLI 路径、`_Compilation`、Agent 当前准入、`DefinitionLibrary`、树 inventory 和 `State.file_lock`；核了本片测试及手册对应合同。架构来源包括 `AGENTS.md`、`pyproject.toml`、README 与相关 ADR 0001/0002/0004/0005、当前架构及结构/身份说明。未发现必须另建 owner、引入持久状态、插件框架或复制后端逻辑的需求。

- 协调者独立执行 `PYTHONPATH=src .ergora/checks/ac3a-definitions/wheel-venv/bin/python -m pytest -q tests/test_workflow_definitions.py`：**65 passed in 3.85s**。Standards 与 Spec 的实际执行结果各自保留在上文，不合并计成更多用例覆盖。
- 范围内 `git diff --check` 通过。作者的四套相关源码日志为 **159 passed / 2 native Windows skips**；协调者已读取原日志，没有再次运行四套测试或全套无关回归。
- 审查启动时 packaging 仍待验；审查期间已产生非 editable wheel 证据。协调者独立重算 source、wheel、安装目录及 `package-identities.json`：**360 文件内容 SHA 全部相同**，安装位置与源码目录不同，wheel SHA 与记录相同；**283 冻结文件**同时匹配 manifest 与 baseline Git 对象。构建/安装不是 reviewer 执行的动作。
- 已读取最终包四套测试日志：**159 passed / 2 skipped**，Python 3.12.3；这是作者运行日志且源码/安装身份已核，不能写成 reviewer 独立重跑。已读取 package CLI 旅程脚本与摘要：6次命令、10实例、4,846字节 prompt，含容量不足、已有目录、篡改、源State移走后的核验、0 agent runs。首轮源码smoke的4,797字节来自另一份任务，两者不是同一次输入。
- 未运行或验收原生 Windows、Linux 以外平台发布行为、真实后端、MCP、模型效果、OS/网络隔离、正式批准、Temporal、当前候选 CI 或远端身份。先行合成原生 HTTP 探针仅为后续设计证据，未计本片实现验收。

r1 需求符合性结论：上述三项 Spec 发现与协调者补充项需处置并复核；其中三个 P2 阻止本轮通过，P3 容量偏差也应在本片收口前修正或给出有证据的合同处置。r1 维护性结论：Standards 初始轴范围内通过；未提出新抽象或所有权重构。修正后需记录 r2 精确范围与受影响验证；r1 的 package/源码结果不自动继承到变化后的候选。精确普通交付、必要 CI 和远端终结仍待后续。

## r2 冻结范围与复核身份

作者接受四项原始发现，修改生产实现和相应回归后，原协调者与两个原子轴在同一切片复核。没有新实现切片或替换原始报告。Baseline/HEAD 仍为 `4f102da873fc19c8a805031106d7a7c4524d5908`。

- [r2 scope](../../.ergora/checks/ac3b2-inputs/review-r2-scope.json) SHA256：`8a4133864b36bacb65452936a54dba070240b07b6005301683b4e95574f2532b`。
- [r2 tracked diff](../../.ergora/checks/ac3b2-inputs/review-r2-tracked.diff) SHA256：`fd89e177bc9604aed6a1f1851985f8947c1da630e92085cd2f14a5cf96dce734`。
- 三名 reviewer 均独立核对九项内容与该 scope 一致，工作树范围 diff 与冻结文件逐字节相同；排除仍仅为前片四份报告的记账。
- r2 生产 `workflow_definitions.py` SHA256 为 `921f254d40b3a858b282aad2b4ec231b8dae0b9c27ffaa6a8d3598092471fee2`；测试文件为 `14c1203928b0ab4499dbcafd7b12c3214bb1e255d2ac9ad23988d78dd46d7426`。CLI、contracts、新 schema 与 r1 内容相同；文档的最终身份逐项保存在 r2 scope。

## Standards r2

以下为该轴复核原始结论，保留其范围与限制：

> Standards r2：**通过，限本片九文件范围。硬规范违例 0；需要修正的启发式 smell 0。** 此结论单独追加，保留 r1 原始结论。
>
> Baseline/HEAD 仍为 `4f102da873fc19c8a805031106d7a7c4524d5908`。独立重算九项内容均匹配 `review-r2-scope.json`；scope SHA256 为 `8a413386…74f2532b`，tracked diff 为 `fd89e177…96dce734`，与冻结文件逐字一致。
>
> 维护性复核：
>
> - `workflow_definitions.py:389` 的 `_publish_input` 虽只有一个生产调用者，但集中承载必要的平台发布语义，作为所属用例中的私有算法合理；仓内未发现可直接复用的原子不覆盖实现，无需新增通用平台框架。
> - Linux 原语缺失或调用失败均明确传播；CLI 原有异常处理可以承接。Windows 分支沿原生不覆盖 rename 语义，没有不安全回退。
> - `:364` 复用现有规范化编码，避免另造 JSON 比较规则。
> - `:383` 的第二次完整 inventory 覆盖索引字节等变化，沿既有 10MB/500 文件及目录限制有界执行，成本与持久内容一致性目的相称。
> - `:444` 仅删除私有暂存库已经释放的锁；未删除共享源库锁或引入新状态。未确认相关规范回归。
>
> 独立执行七个受影响既有案例：**7 passed、65 deselected**。另以临时目录验证：缺少原语产生 `ValueError`；原生 `ENOSYS` 保留为 errno 38 的 `OSError`；两者均清理暂存且不发布目标。真实 Linux 中文目标路径准备/核验成功，源索引保持不变。范围内 `git diff --check` 通过。
>
> 未修改文件。作者的 166 passed/2 skipped 属其源码/包验证记录；本次未重复整套，也未独立验收 wheel、原生 Windows、CI、远端或真实后端。本结论仅属 Standards 轴。

## Spec r2

以下为该轴复核原始结论；仅将机器绝对链接改为项目相对链接：

Spec r2：**通过，限本次九文件范围；四项发现均关闭，无新增 finding 或 scope creep。** r1 原始结论保留。

- **IN-SP1 关闭。** [389–403行](../../src/ergora/workflow_definitions.py)在 Linux 使用 `RENAME_NOREPLACE`，Windows 使用原生不覆盖 rename。并发空目录回归通过；独立探针确认已有文件、悬空链接也被保留。缺少 libc 原语、内核返回 `ENOSYS`、其他平台均明确失败，无覆盖式回退。
- **IN-SP2 关闭。** [364行](../../src/ergora/workflow_definitions.py)改为规范化 JSON 比较；布尔替换整数、整数替换布尔、浮点替换整数三个案例均拒绝。
- **IN-SP3 关闭。** [443–445行](../../src/ergora/workflow_definitions.py)在聚合统计前删除私有暂存锁；最终500文件成功，501文件拒绝且清理暂存目录。
- **IN-R1 关闭。** [351、383行](../../src/ergora/workflow_definitions.py)比较前后完整 inventory。独立重现初次扫描后修改索引换行、增加空目录、改变文件执行位，三者均拒绝。稳定输入要求及双遍检查的能力限制已准确记录。

独立运行新增回归：**7 passed、65 deselected**；另完成上述8个临时目录/平台分支探针。九文件 SHA 与 r2 scope 一致，工作树 tracked diff 与冻结文件逐字节一致，`git diff --check` 通过；baseline/HEAD 仍为 `4f102da873fc19c8a805031106d7a7c4524d5908`。

源码/包各166项结果仅核读作者日志，未独立重跑整套、验收 wheel 身份或原生 Windows；其他平台分支仅模拟。未改文件，未验当前 CI、远端或真实模型调用。本结论不代替最终交付验收，维护性结论仍归 Standards 轴。

两轴 r2 汇总：Standards 新增 0 项、无本轴最严重问题；Spec 新增 0 项，原三项关闭。协调者的 IN-R1 同时经 Spec 复核与协调者重现后关闭；各轴结果不合并计数或互相替代。

## r2 协调者补核与当前交付限制

协调者复读修正实现、七项新增回归和更新后的文档，独立追加以下小规模验证，没有再次运行整套相关回归：

- 真正调用 Linux `renameat2`：中文目录中准备/核验成功；最终目标为已有文件、符号链接、空目录时均 `FileExistsError`，原目标 inode 与暂存内容保持。另模拟其他平台与缺少 libc 原语，均明确拒绝且目标不存在；这些模拟不算对应平台的原生验收。
- 用 r1 相同窗口在初次 inventory 后给 workflow 索引追加换行，r2 明确报 `Composition input changed during verification; retry a stable directory`。目录仍要求稳定；这不构成同用户恶意并发写入防护或作者认证。
- 一个11文件、单叶的小输入在准备中调用4次用例层 inventory，共42次文件访问，观察耗时0.0237秒。第二次核验扫描是为覆盖已证实的索引/树变化；聚合检查随复制逐次执行，所有扫描沿10MB/500文件/1000目录/48层限制有界。该计数未包括共享定义库内部扫描，也不是性能上限或大组合性能验收。
- 独立重算 r2 source、wheel、非 editable 安装及身份记录：**360文件 SHA 全同，283冻结文件同时匹配 manifest 与 baseline**。最终 wheel SHA256 为 `22ec691788490be970eab0faf97aeccc41d3f30da486c4d278e5944fdde06f16`，与记录一致。
- 使用该 r2 安装包的 Python 3.12.3，`-I -m ergora` 在临时目录独立执行3次 CLI：prepare、verify-input `--material`、重复prepare，退出依次为 **0/0/2**。中文目标路径、BOM/中文/CRLF原任务字节保持、prepare/verify摘要一致以及 `execution_authorized: false` 均通过。这是新修正版的3命令范围，不将 r1 的6次旅程冒称为 r2 重跑。
- 作者有效源码和包日志各为 **166 passed / 2 native Windows skips**，已核读。最初两次未收集测试的失败命令均保留并排除；之后测试参数等值简化的3案例复核日志也已核读。它们没有被登记为 reviewer 独立整套执行。

r2 新增 CLI 原始 stdout：

```json
{"r2_installed_cli_commands": 3, "expected_exit_codes": [0, 0, 2], "prepare_verify_digest_equal": true, "raw_bom_utf8_crlf_task_preserved": true, "non_ascii_destination": true, "execution_authorized": false, "python": "3.12.3"}
```

当前静态本地需求符合性与维护性审查通过，四项原始发现全部关闭。原生 Windows 仍待当前候选自身 CI；Linux 缺少 `renameat2`、不支持相应原语的内核/文件系统及其他平台会失败，不回退为覆盖式发布。当前候选普通提交、必要 CI、远端终结尚未核验。本片没有调用真实模型、装载 MCP、提供 OS/网络强制或接入正式批准/Temporal；后续进入 AC3b.2b 前仍须先完成最小后端能力准入。
