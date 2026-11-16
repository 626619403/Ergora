# WA5-S1：首次设计 policy 登记与拒绝执行

2026-11-16。**自身结构审查三项已独立核验：v1 回执／冻结 selection 与历史 schema 两项已最小修正，marker 路径等价无需生产改动；新作者候选冻结，定向 92 项通过，仍未合入。新同版安装／自身模板复核／fresh 独审待主控；两轮旧冻结与原失败证据保留。** 唯一源码写入树为 `.ergora/worktrees/design-policy-registration`，分支 `feat/design-policy-registration`，基线 `3d632a78b6acc4f0027b2225e7771a5da927af81`。主树源码与其他隔离树只读；本记录为本片唯一主树文档写入。

权威为[登记／源记录／运行双门 r2](../plans/2026-11-16-design-gates-registration-and-journal.md)（SHA256 `a94b4a5a95a674330e09e84b0c7596635bc985521c3f8d221ed996dbb07965ae`）及其[fresh 设计复核](2026-11-16-design-gates-registration-and-journal-design-review.md)（SHA256 `bb12afc99d8f5883f67cead512daa9eff625f87d556a72a6166f18d288ea317e`，两轴 approve／开放 0）。a1 最终修正版 `cb861ea` 已由主控完成原独审、安装与自身模板后集成于本基线；其已发布 inspection profile 不改字节、不当正式授权。

主控随后仅把权威方案 16 个 `.py:行号` 相对链接改为 `.py#L行号`，正文／字段／验收未改；当前链接格式字节 SHA256 为 `bde47bee749ff973901beeebc6f148316b3ea2d2635e191ac5804942e142f984`。原 a94 字节在 `.ergora/checks/design-training-expression-integration/approved-plan-r2-original.md`，映射见同目录 `plan-link-formatting.json`。本片已核原 a94 输入，不把链接格式整理当设计重批。

## 范围与序列化交接

输入 `project-registration-v2.json` 继承 v1 外层字段，新增完整闭合 `design_policy`：

```text
{schema_version:1, protocol:'design-knowledge-v1',
 profile:{schema_version:1, kind:'task-design-policy-profile', id, protocol,
          change_kinds, required_sections,
          minimum_questions:[{id,body,why_required}],
          minimum_knowledge_requirements:[{id,missing_information,why_needed,
            allowed_source_types,access_scope_ref,
            freshness_rule:null|{max_age_seconds:null|>=0,required_version:null|string}}],
          required_actor_assurance:'protected-owner-channel',
          limits:{artifact_bytes,inspection_bytes,source_records,questions,
                  knowledge_requirements,revisions,journal_records,journal_bytes}},
 profile_sha256,
 owner_source:{owner_id,source_requirement:'protected-owner-channel'},
 applicable_task_types, change_kinds, required_sections,
 minimum_questions, minimum_knowledge_requirements, sha256}
```

`profile_sha256` 是原 registration canonical JSON `_sha(profile)`；policy 的 `sha256` 是去自身 `sha256` 的完整 policy canonical SHA。完整 policy 连同两 SHA 进入原 definition、registration digest、marker、intent 与 result；持久判别为嵌套 `registration.schema_version:2`，project／journal 容器仍 schema1，四原生文件布局与格式不变。最低 Q/K ID 必须带 namespace；profile／项目要求取并集，同 ID 异内容或跨 Q/K 冲突拒绝。配置容量核最低并集及原传输安全界，不固定示例默认值；K freshness 为来源版本／时效要求，实际观察时点由后继任务冻结。

`owner_source.owner_id`、来源和 `required_actor_assurance` 均是待满足的要求，不是已证明的自然人身份。status 完整读回 stored policy、SHA、合并最低项与限额，显式报告 execution unsupported 与 `human_channel_unavailable`；此结论来自当前可信 human 功能尚未实现，没有声称查验真实 ACL。不发布执行 companion、不翻 a1 的 inspection/runtime 布尔。

只允许真正首次统一登记；已有 v1（包括空项目）不能转 v2，已有 v2 不允许重登记／降级；同原 operation／完整 intent 的中断恢复走原 resume。已有 control project 但没有 registration 或任何四投影仍沿原首次合同。拒绝须在 intent／reservation／native 发布前发生。后继 marker 迁移、跨登记旧 creation/prepare/submission、F/J/G、source journal、approve、definition8、Input12、UI 与模板默认均不实现。

## owner 与验证安排

`registrations` 拥有显式版本选择、policy/domain 校验、首次资格、`_prepare/_finish/status/published_project/resume`；`state` 只新增 v6 的原表 writer fences，不改表布局。`tasks._definition/_budget_project` 在预算／intent 前拒绝 v2 新生；无 IO 的纯拒绝规则留在原 `task_design`，供这两条路径与 executor 使用。`reference_executor.process` 在 job 构造前拒绝 v2／foreign marker，防止 BudgetedJob 的早 claim；直接构造 `Executor` 在原 native constructor 前同样拒绝。v1 的缺项目／repo 错配留在原 admission 回执 owner，已有 markerless legacy snapshot 不新增这两个前提。无新增 policy service、ABC、registry 或 native schema validator；不把 registrations/contracts/jsonschema 导入 native executor。

验证沿既有 registration、migration、backup、task creation、task budget、composition executor 测试和必要原 fixture，保留真实 intent、SQLite 事务、native 四文件、job／claim 边界，叶替身与真实服务／模型分列。至少一个非默认有效 policy／limits；保存原失败与修后、准确 argv、raw、JUnit、完整源码及新文件／mode。当前 private 证据目录 `.ergora/checks/design-policy-registration/`；开发解释器仅使用现有 `.venv-dev`，不改环境、不安装。

State 事务回滚仅限 DB；原 offline backup/restore 仅限 control-home inventory，外部 config/state 不在包内。v2 发布后的跨根一致回退、软件降级、旧服务在线升级及 standalone stack 停用／隔离另验；不迁移用户 control home、不停其他 owner 的训练。

## 当前检查点

已读根／src／tests AGENTS、组件协议与两项适用 skill，核隔离树基线及两权威 SHA；主控确认上述 shape／owner 交接。实现已在原 owner：新 policy 校验／合并最低项、嵌套 version2、完整 status／published journal／resume，State6 fence、两个任务出生 guard，以及 process 和直接 Executor 的前置 guard。executor 按原 native tracker 取得项目，先核原 marker 的 control home，防止把无 policy 的另一 control home 当权威；可读取的 State 项目再用纯规则拒绝全部 v2。State 缺项目与 repo 错配回到原 composition／无 snapshot 分支，其中 repo 检查仅在原无 snapshot 分支。原 v1 当前登记可切至另一执行根、已有 frozen selection 继续原 native 根的合同保持，不借本片发明跨 v2 登记豁免。native 仍未导入 registration/schema validator。

以下均为隔离源码检查，解释器是现有 `.venv-dev/bin/python`，未安装或调用模型／服务。每个实际 pytest run 的 `invocation.json`、`stdout.txt`、`stderr.txt`、`junit.xml`、`result.json` 在 `.ergora/checks/design-policy-registration/<run>/`；r2 起的通过运行另冻结 `source.tar`、`source-manifest.json`（完整 package/test/new schema 字节与 mode）、`tracked.patch` 及 git status。先前运行不转授最后候选。

|run|实际结果／身份与范围|
|---|---|
|`red-owner-seams`|私有 runner 首次算错 cwd，pytest 未启动；原 invocation／空 stdout/stderr 与 runner-error 记账保留，修 runner 后重跑。|
|`red-owner-seams-r2`|未修 3d632a78 产品源码＋新回归：10 failed／5 passed／86 deselected，16.63 秒。v2 不被原 schema 接受；已开 v5 writer 未被隔离；v5 无迁移所以中断钩子不触发。|
|`green-owner-seams-r1`|首实现 6 failed／118 passed／1 skipped，116.65 秒。5 个新 status 用例暴露局部变量赋错位置；backup 测试错误地把刻意不入 inventory 的 `.schema.lock` 当资产。两处已修，保留原 raw／JUnit；不是产品通过。|
|`green-policy-core-r2`|18 passed／144 deselected，25.82 秒。新 v2 实际四文件发布第 0–3 写入中断与全部 native 发布后 result 中断、CLI 新进程恢复／完整 journal、空 v1 和有 creation 的 v1 升级零增量、已有 control 项目首次 v2、不可重登记／降级、policy SHA／最低项冲突、两个任务出生入口，以及真正 legacy DirectJob 的 v2 拒绝与 v1 冻结 selection 对照。|
|`green-budget-preclaim`|3 passed，28.68 秒。真实 process 在 BudgetedJob 构造／claim 前拒绝；原 constructor 锁耗原预算与原 Git 锁保护保持。预算反例将原合法 v1 冻结输入／job 完整 replay 到真正首次 v2 的新 native 根；它的旧 binding **不是受支持的跨登记恢复**，拒绝不能等到后面的 owner 检查才 claim。原 v1 文件原字节保持。|
|`red-runtime-original-executor`|明确的混合版本回归复现：当前 v2 登记前置＋准确 3d632a78 的原 `reference_executor` 模块，仅在原 fixture 导入处替换；不是未改基线验收。原合法 native legacy spec/job 被放行，`claim=2, body=1, prepare=1, model=1, commands=1`、拒绝 0，原预期失败及两份源码身份保留。这里 model 是确定性 CLI fixture，真实模型调用 0；新实现同接缝全 0。|
|`source-core-r3`|164 passed／1 skipped，233.36 秒。完整 `test_registrations/test_state_migrations/test_state_backups/test_task_creation/test_task_budget`；source manifest SHA256 `4fbf928d2d6160cfca2482b63f18de6a76c4b47d308275d70a146954e7b09149`，789 个完整 package/test 输入（含新 schema）。|
|`source-runtime-r3`|73 passed／13 failed，736.88 秒，按主控要求对准确原 pytest owner 发送 SIGINT，由原 runner 正常保存 partial JUnit/result（exit2）；119 collected／86 完成／33 未跑，完整节点差集见 `selected-vs-executed.json`。24 个 composition、24 个 legacy executor、30 个普通 approve 和 8 个 cancel 已执行；其余 cancel 与三个预算节点未跑。8 项失败来自安全 `python -I -m ergora.stage_driver` 实际导入主树 editable 的 State5，不能读本片 fixture 的 State6，原 model-log／SHA 见 `mixed-version-traces.json`；不改 -I、主树或解释器环境绕过。另 5 项是作者多加的 current registration SHA 核验误伤 v1 的原 frozen selection／旧失败回执，已删除该核验，修后按原接缝定向重跑。两类失败不得混写为纯环境问题。取消时只捕获本 run 的三个 PID／start ticks，终核全 absent，无额外 signal 或他人进程操作；见 `cancel-request/cancel-cleanup.json`。|
|`red-recovery-writer-bound`|1 failed，1.87 秒。完整 policy 不投影到四文件，原 native 单文件限制不会阻止完整 intent 超出原恢复读界；把原 cap 缩小到实际完整材料之下，旧 writer 仍发布，原失败已保留。|
|`source-final-directed`|**83 passed，116.91 秒**，与最终 `71a22bd2…` 同一完整 source 输入：75 个 registration 用例（含完整 policy 与容量修正）、4 个原 v1 登记切换后 frozen selection 的 six-stage、1 个原 wrong-state 回执、2 个新 native legacy v1/v2 和 1 个原 BudgetedJob preclaim。前述 5 个作者 guard 回归在原接缝全部修后通过；混装 composition 组仍只交同版安装复核，未重复跑。|

最终容量修正沿原 owner 新增 `_intent` 构造：使用与 `_record` 相同的完整 pretty JSON／UTF-8 序列化及原 `MAX_RECOVERY_BYTES`（32 MiB），register 在 publication 锁、journal、reservation 与 native 写前检查；`_reserve` 直接消费这一份完整 intent，import 仍沿其原 source／preview 约束。实际 configured policy 限额未改，未给每字段另造默认值断言。新反例核 control 项目、journal、两边 registration 锁与 config/state 均无增量。

首轮源码冻结于 `.ergora/checks/design-policy-registration/source-final/`，仍基线 `3d632a78b6acc4f0027b2225e7771a5da927af81`、14 文件。`complete.patch` 包含 tracked 全差异和新 schema，SHA256 `83f294b0e0718e95dfa2f40e701137bbd701cc510d54050769b37471d9f5de8d`。`complete-tree.tar`／manifest 含 2,065 个 tree 原件；`package-source-manifest.json` 含 670 个包文件完整字节／mode（SHA256 `805fcb4ee55ec861bc2a7d12f21917c981bd6ad6044e3f9badd95c6a27968a00`）；package＋tests 789 输入 manifest SHA256 为 `71a22bd2ec1d288cbad5acfad8c9c4b7c4abff9c3fa981df1fda57033c9d010b`。唯一新文件 `project-registration-v2.json` mode0644。详见 `freeze.json`，应用 schema／diff-check 通过；原参考、native 锁、presets／scripts、a1 inspection profile/schema、input factory 均未改。冻结不是独审或安装通过。

首轮最终 source 定向完成后，2,065 个冻结 tree 原件逐字节／mode 重核同一，完整 patch 的反向 `git apply --check` 通过；见 `final-unchanged-and-patch-check.json`。已向主控交完整 patch／manifest／准确 argv 与 JUnit。主控随后按 fresh 实现审查 R1/P2 提出下述具体修正；首轮冻结原件保持不覆盖，其 83 项结果不转授修正版。

## fresh 实现审查 R1/P2：锁内 revision 重核

[fresh 实现审查](2026-11-16-design-policy-registration-source-review.md)指出：同 control／同 project 的两个首次登记都可能在 publication 锁前读取 `before=None` 并完成 `_prepare`；先到请求使用 config A 完成发布，迟到请求使用另一组空 config B。迟到请求锁内四投影仍为空，原 `_reserve` 会先 `_record(intent)` 再在事务中发现 `current != before`，拒绝后遗留一个孤立 intent，违反此次写前拒绝／零增量合同。这不是 native 文件冲突，不能靠原 config B 的投影重读排除。

修正只在原 `register` 的 publication 锁内、native 检查与任何 `_record` 之前，以已有 `_current` 重读同项目并比较完整 `before`；不等时沿原 revision changed 错误拒绝。保留 `_reserve` 原事务内再核验，不加新锁、owner、服务或状态。相对首轮冻结仅 `src/ergora/registrations.py` 两行及原 `tests/test_registrations.py` 的回归发生变化，仍共 14 个原候选变更文件。

回归沿原合法 registration fixture 和完整 formal policy：用真实 `_prepare` 得到迟到候选后，在同一控制目录的另一 `State` 上真实完成先到登记，再让迟到候选继续。保留原 publication 锁、`_reserve`、`_record` 和 `registration_io`；参数为先到／迟到版本 `1→2`、`2→1`、`2→2`，配置根和运行根均不同。拒绝后比较完整 registration 目录文件集合与字节、已发布 config 全部文件、当前 project 及 SQLite 逻辑全库；迟到 config 的四投影和运行根不得产生。锁文件是原锁的正常获取，不当作 native 投影。

|run|实际结果／身份与范围|
|---|---|
|`red-stale-first-registration`|**3 failed，3.79 秒**。三个合法交错均正确触发 revision 错误，但都额外生成一个 intent，文件集合断言失败。`baseline-comparison.json` 核仅新增上述测试，670 个包文件与首轮原候选字节／mode 全同；789 输入 manifest 为 `323ae5e0aeaaee3840de61c7d08715410056830116d6bc980ad935cf5444494d`。|
|`source-r1-fixed-registration`|**78 passed，59.18 秒**（runner returncode0／59.66 秒）。完整原 `tests/test_registrations.py`，含原 v1／v2 publication 中断、CLI 恢复与 import 接缝及三项新交错；未扩无关 suite。789 输入 manifest 为 `16f7647ce23b3ef8b7dd649d64db9157da34d6324cf7b3987b23c03ca698566f`，与修正版冻结完全同一。|

两个 run 的 invocation、环境覆盖、raw stdout／stderr、JUnit、result 及 source 输入仍在 `.ergora/checks/design-policy-registration/<run>/`。它们是原现有解释器的隔离源码检查，无新安装或真实模型／服务调用。

修正版另冻结于 `.ergora/checks/design-policy-registration/source-r1-fixed/`：完整 `complete.patch` SHA256 `7f6133b9c49c95d4c638d385c804c65fda8af68cdf75e0b6bd4fcb85e73a543a`；仅相对首轮两文件的 `review-r1-fix.patch` SHA256 `56c0ee1c3d1fd1f9f470b635e48176dbfdf7b9bdb1e762c9288292c0bd3dd404`。完整 tree 2,065 原件 manifest SHA256 `ba51610eee994c0b31609451918b3d6140b2f2b9dbe3557e3765fa4023a61e6d`；670 完整包 manifest SHA256 `a6f30a32319d33efda2f136e6ca61982ab7b1bd0ac639207a34242321773fc96`；package＋tests manifest 同上 `16f7647c…`。`original-freeze-delta.json` 记录准确两文件差集；`freeze.json`、原 schema／diff-check、完整与 delta 反向 patch-check 均通过。

修后运行结束再逐字节／mode 重核 2,065 个冻结 tree 原件全同，JUnit 78／0 failure／0 error／0 skipped，原首轮 `83f294…` patch 未改；见修正版 `final-unchanged-and-patch-check.json`。已把准确 delta／完整 patch／manifest 与红绿原件交主控及本片原 fresh reviewer；作者未自批，独立 finding 的关闭由 reviewer 复核记账。

## 自身结构审查后的 v1 兼容修正

主控报告：固定候选 `121ed2` 的 r2 新非 editable 安装已把原 runtime／compose／approve／cancel／budget 119 节点跑完并全过（982.955 秒），原候选及结果保留。随后原 Ergora 自身结构审查模板的 Claude 实跑返回 request-changes，原文在 `.ergora/checks/design-policy-registration/self-review-r2-claude-code/review.md`。下列是作者对三项建议的独立源码与实际接缝核验；旧安装结果不转授本轮新源码。

第一项是可达兼容回归。准确 `3d632a7` 的 `reference_executor` 只在 composition 分支和无 snapshot 分支查 State 项目，repo 比较仅在原无 snapshot 分支。原 `_execute` 把这些失败绑定为 `FAILED`／`agent-admission-error`，DirectJob 发布回执，workflow poll 可取得终态；已有 legacy snapshot 则沿原冻结 selection，无需再次满足缺项目／repo 相同。首轮 S1 把两种检查提升到 `process` 的 job 构造前，使缺项目或 repo 错配直接抛出，服务 loop 只记 rejected-envelope；还误伤原 frozen selection。

本轮把 `_admit_project` 收窄为无返回值的 preclaim 拒绝：保留原 native tracker 查找与 marker 的 control-home 核验；已有 State 项目用 `task_design.require_execution_support` 拒绝 v2；项目查询的 `ValueError` 回到原消费者处理，State 构造／schema fencing 在该回退之外。State 查询及 repo 比较回到上述原构造分支，不给 composition 添加原来没有的额外 repo 检查。job／claim owner 与失败回执结构不改。

**foreign marker 隔离是必要且明确的 v1 收紧。** native 根若已有 unified ownership marker，即使是 v1、已有 frozen selection，另一 control home 也不得用同 ID／同 repo 的无 policy 项目绕过该 marker；直接 `Executor` 和 `process` 均须在 native constructor／job／claim 前拒绝。原 fixture 现在同时核 v1 和 v2 的这两个入口，观测 starts 全零。没有 ownership marker 的原 legacy 根仍保持上述缺项目 FAILED 回执和冻结 selection 语义。这一隔离用于避免用另一 control home 掩盖真正 v2 policy，不声称认证自然人或真实 ACL。

第二项没有路径分歧。项目 owner 的实际准入是 `re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', id)`；native `core.slug` 的准入为相同字符集、最多 80 字符，成功后直接 `return value`，不改大小写或下划线。统一登记的 1–64 字符合法 ID 是其子集。实际原 core 对 7,998 个样本（全首字符／后续字符及长度 1、2、64 边界）均返回原字符串，拼出的 marker 与 `registration_paths(id)[0]` 完全相同。保留原生产规则，不加共享路径层或另一套 slug 转换。

第三项也有真实历史输入。`4ffcfdde0c728cf5904690decd165e26e1a9bb7d` 才给 v1 tracker 增加 `not: {pattern: '\\s'}`；其父 `62c4d696396942fbad86fc21f56f9e854e3ed4d1` 的合法 schema 会接受 `local/demo\n`。原 fixture 按准确旧 schema 写真实完整登记／中断 intent，随后恢复当前 schema；没有伪造 DB dict。准确旧 owner／schema 另生成真实原件，再以准确 `3d632a7` reader 调用 status／resume，均可读回／恢复且 intent 原字节保持。首轮新增的 `_validate_saved` 会在 status／`_finish` 拒绝这些合法旧记录，原 reader 没有这个输入重验前提。

修正仅让 status／`_finish` 的新增 `_validate_saved` 调用用于 nested registration2；v2 policy／SHA 校验保留。`published_project` 原本就严格重验 v1 完整来源，此合同完全保留；两个新历史回归均明确确认它仍拒绝该 tracker，而 status／resume 可继续。这不是放松新登记输入：新输入的现行 schema 和原 tracker-newline 拒绝测试均未改。

|run／probe|实际结果／身份与范围|
|---|---|
|`red-v1-compatibility-r2`|**6 failed，12.65 秒**（runner14.26 秒）。四项 markerless legacy 的 missing-control／repo-mismatch × 无 snapshot／已有 frozen snapshot，及两项真实旧 schema status／resume；670 包文件与 R1 freeze 全同，仅三处原测试／fixture变化，见 `baseline-comparison.json`。789 输入 manifest `47ac9248a4ee4d40fc8ea62284af7a24bd0a8e97af566305e9f989d036500dde`。|
|`original-v1-compatibility-probes`|私有 runner 首次误写 companion fixture 文件名，复制阶段失败，实际 case0；原 runner、错误与修正记录在该目录，未当产品失败或通过。|
|`original-v1-compatibility-probes-r2`|准确原 executor 的四项对照全部通过：无 snapshot 两项均 FAILED、poll 获终态、model／commands0；frozen 两项均 SUCCEEDED 且原 snapshot 字节不变。准确历史 owner／schema与原基线 reader 的两项 status／resume 通过，另有上述 7,998 个 slug 边界样本。每个 native case 有准确 argv／环境和 raw；完整 `result.json`／`source-identities.json` 记录各 owner SHA。它是原 owner＋当前 State6／确定性 CLI fixture 的明确组合，不冒称旧发行版安装。|
|`source-v1-compatibility-fixed-directed`|**92 passed，285.63 秒**（runner0／286.53 秒）。完整 registration80（原恢复与 R1 交错仍在），四个新 legacy 对照，两个原 v1／v2 legacy／foreign-home，原 BudgetedJob preclaim，四个原登记切换 six-stage，原 wrong-state 回执。789 输入 manifest `7a5cf605996a1ec05d548b2b3d00db22ddba351c2a00d79d32af29987e77d28f`；未重复原无变化 119 项。|

这里的 model 计数全部是原确定性 CLI fixture；作者真实模型／外部服务调用0。实际新 pytest run 的 argv、环境覆盖、raw、JUnit、result 与源码输入沿原证据目录保存；精确历史 schema SHA `225a7414cb381f0f37c60afccf7c76271b6a674b0e38b4700117c0972833400f`，测试回放的 JSON 与该旧文件全同。

本轮另冻 `.ergora/checks/design-policy-registration/source-v1-compatibility-fixed/`，准确基线仍 `3d632a7`，完整候选仍14文件。`complete.patch` SHA256 `a6ce18dc4b5fd8fec7dd7a226e776486e3671976cd8f3433a0809d56e82b84f6`；R1 冻结之上仅五文件的 `review-v1-compatibility-fix.patch` SHA256 `fd3f5ee1033ce61de046452b6c6889921a9a046d3d94758ddc131cb1cfa42e18`。五文件是两个原 owner `reference_executor/registrations`、原 `reference_acceptance` fixture、原 `test_composition_executor/test_registrations`；不改 native core、schema1、reference路径规则、State、出生 gate、Input factory 或 a1 已发布资源。

新完整 tree 2,065 原件 manifest SHA256 `a145a228af67da39fe5baa06c25cbe3f0f7dcf2f58dcac052484872de10db2ec`；670 完整包 manifest SHA256 `4e7f6bd4460d3c05420979d5fa62b23e874b9887866df8b1b99cd2aeabede809`；789 package＋tests manifest 同上 `7a5cf605…`。最终 run 后逐字节／mode 核2,065原件全同，JUnit92／0 failure／0 error／0 skip，完整与 delta 的 reverse patch-check、schema及diff-check通过；见 `freeze.json`、`previous-freeze-delta.json`、`final-unchanged-and-patch-check.json`。首轮 `83f294…` 与 R1 `7f6133…` patch 原字节保留。作者源码候选再次冻结，尚未合入、安装或独立批准。

下一步由主控把本轮 delta 接入自己的 fixed 候选，另建同版非 editable 安装、沿自身原模板复核并协调新的 fresh 实现审查。新冻结内 `installed-regression-selection.json` 给13项受影响最小安装集合：六项新回归、v1／v2及foreign-home两项、原预算preclaim一项，和使用原安全 `-I` stage driver 的四项 composition journey；作者未运行这份新安装，未更改 `-I` 或现有环境。主控集成基线已有相邻改动，其包文件计数与作者旧基线的670个包文件分列，不混写候选身份。此前混装运行的名义 pass 仍不能替代同版验收；主控报告的119项同版结果只属于 `121ed2` 原候选。

独立审查、新非 editable 安装和自身原模板由主控接作者 source 候选后执行；作者不自批。本片未提交、合并、推送或开放执行。

## 根接续：v1兼容r3固定树与新安装

作者全部14个变更文件raw／执行位已逐项同一移植到新隔离树 `design-policy-registration-fixed-r3`，基线为已接纳联合产品 `c540939d3b3f38f3851b0de965c9cd0f969eea77`，准确产品 `80cb39cbc29b7e800a2dfefb09538732eecb5a68`。完整14文件patch SHA256 `bbebaaa0435e7f5af8743ae597909723c3781387e083908dec91e0b23cd38af2`，2,072完整输入manifest SHA256 `ba2c2fbabd746690fd8ae04be26ba22f55ddbdd5e8f320a81c8b0bcbfece947c`；原件在 `fixed-r3/`。原作者完整patch的基线不同，身份映射保留，不能混写两种patch hash。

`package-v1-compatibility-r3/`的新非editable wheel SHA256 `2d1f1830d46c1acee1d3374429f901b2bc4cb8c1d8477e2a1ff6cbc057eee4db`；core／SDK各669完整包字节与执行位和source／wheel同一，三训练owner从site-packages真实导入，283参考／依赖检查通过；core无SDK、SDK1.34.0。源码manifest含根AGENTS，安装包依原规则排除，因此作者package-source的670项与实际包669项不混计。

按作者最小同版-I清单，真实旧process／失败回执／冻结selection／历史status-resume、新v2与foreign-home preclaim、原BudgetedJob及原四个composition旅程，共 **13 passed／78.701秒**（runner79.783秒）。捕获529个自有进程身份结束后均absent；准确argv、完整raw／JUnit及过程身份留存，不声称全系统无残留。r2的119／前代安装结果没有转授。

新的fresh源码审查另在真实隔离fixture确认：合法旧job已submit后删除native项目配置，c540安装仍发布FAILED且poll可见，80cb安装却在process前_admit_project的project_for抛Blocked，poll为空、无回执。两者均无prepare／命令／模型；新candidate的13过未覆盖此边界。对照原件 `reviewer-native-resolution-r1/result.json`，精确原件与两个实际site-packages来源均保留。本finding仍待最小修正／同片独立复核，不合入80cb或借原模板先行关闭。
