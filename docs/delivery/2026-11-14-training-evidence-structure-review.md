# F9c C1 原训练证据只读入口：独立结构评审

日期：2026-11-14。评审者：fresh-context 独立 agent `training_evidence_structure_review`。先读 `AGENTS.md`、[当前计划](../PLAN.md)、[本片原合同](../plans/2026-11-14-training-evidence.md)、原调用者与 archive／训练／release owner，再读作者交付与实际原件；使用 maintainable-project-delivery、independent-review brief 和 codebase-design。没有继承实现对话。

## 当前结论

**最终本地结构评审通过，所查需求符合性与维护性均通过，开放阻塞 0、非阻塞 0。** 最终 r2 安装、实际 CLI／HTTP／SDK-free、原件保持与收尾、自身模板已直接补核；普通发布、完整 Ref 与本片自己的 CI 仍待。不将前片 C2 的发布或 CI 当成本片证明，也不将首轮安装的 45 通过／1 失败改写为通过。

本轮只读源代码、Git 和验收原件，进行了轻量 AST／路径／摘要／RECORD 静态核验；只写本文，没有安装、重跑 suite、启动浏览器／服务、访问远端、执行训练、批准或采用。

## 检查身份与完整范围

基线与初检 `HEAD` 为 `2181cc5c6ab92ac01664f8e769298cce350f65a5`，分支 `refactor/architecture-foundations`，对象为未提交工作树。独立检查 `git status --short`、基线完整 diff 与 `git ls-files --others --exclude-standard`；初检共 20 路径，包括下列全部新文件，没有只看 tracked diff：

|类别|已读路径|
|---|---|
|产品|`src/ergora/reference_training_evidence.py`（新）、`training.py`、`reference.py`、`cli.py`、`web.py`|
|测试与 CI|`tests/test_training_evidence.py`（新）、`tests/fixtures/training_evidence_archive.py`（新）、`tests/test_architecture_boundaries.py`、`scripts/ci/linux-groups.json`|
|本片合同与说明|`README.md`、`docs/TRAINING.md`、`docs/architecture/current.md`、`docs/PLAN.md`、`docs/plans/2026-11-14-training-evidence.md`（新）、`docs/delivery/2026-11-14-training-evidence.md`（新）|
|前片 C2 发布记账|原 preparation-console 的 plan、delivery、spec-review、structure-review 及公开 evidence JSON；完整 diff 仅补发布身份／CI 状态，不扩作本片产品验收|

首轮产品／测试／CI 的 9 路径组合 SHA-256 为 `04bedeecd11502c2dbf600b451a0326b18117b08238a4b021902f850be2a0b76`，独立重算与 r1 构建快照一致。评审中作者复用原 HTTP headers／base_url 修正新测试，当前 9 路径组合为 `bca645238f08d12e639da8b8f3732cdda651bd31e5aae735b97ee025a345aca9`；产品与 r1 wheel 仍逐字相同，不能把 r1 测试结果追认到新测试。

## 职责、复用与新增控制流

已读原 `perfctl.py` 的 `archive / gate / local_file / baseline_ok`，原 `agent_platform.training` 的 `collect_and_gate / authorize_release_and_create_task`、`training_executor`，Temporal 原模型／workflow，以及 `_TrainingProject`、`_training_records`、`reference_task_evidence` 和相邻 training 应用、CLI／HTTP 调用者。

- `training.evidence` 是 CLI、HTTP 两个生产文件共用的应用 Interface。其非负字符 offset、窗口上限、选择 artifact 时必需完整 evidence SHA、无 artifact 时拒绝无意义 SHA／offset 的检查针对实际外部输入；项目准入复用 `_project`，没有另一份注册或请求账本。
- `reference.training_evidence` 是既有 `_training_process` 的训练适配入口，明确 `sdk=False`，复用原安装身份与进程生命周期。它虽然很薄，却承担既有 reference seam 的运行时选择，不构成无职责包装。
- 新 `reference_training_evidence.inspect` 只有一个真实生产消费者：reference 训练子进程入口。新文件的理由是内聚的私有归档读取算法及其隔离运行方式，不是多个调用者或假想复用。它把归档验证／窗口／票据读取集中在一个小 Interface 后；删除后复杂度会回流进现有 reference 大文件。`main` 仅拥有该子进程的 JSON 输入、最终容量和可见错误退出。
- 内部 `document`（新文件 23–29 行）在原 `safe_file / read_raw` 之上保存每份原 JSON 的**字节**摘要；已有 `_TrainingProject.document` 只返回对象，无法提供这一事实。此局部 helper 有具体职责，没有为单用算法扩张共享 context Interface。结果最终复用 `_native_bytes` 约束总响应，未另造序列化或限流框架。
- 40–77 行分别处理无已接受归档、原 job 状态、完整内容地址、同 manifest／candidate／baseline 的 gate、原 evidence／manifest／baseline／comparator 字节。`archive_report` 按原 JSON 内容核对符合原 owner：没有为未独立绑定摘要的 gate 凭空规定字节相等，也没有执行 comparator 或重做 attestation／统计门禁。当前 baseline 的适用性来自原 reader，和归档当时快照分列。
- 79–89 行复用 `perfctl.local_file` 的原相对／保留路径及现存文件规则，再以原 adapter 拒绝 symlink；两者保护的条件不同。声明 SHA 格式和重复路径检查属于原索引输入；没有为所有索引项读取内容。选中项的完整 SHA、UTF-8、NUL、offset 检查（93–111 行）保护返回窗口的来源和字符语义，16 MiB 限额由原有界 reader 执行，未复制文件读取算法。
- 113–127 行仅按原 owner 的 ticket ID 规则读取本地票据，验证完整 project／binding／evidence／kind／receipt 引用和 `automatic_merge: false`；不存在即返回空。没有检查或更新 owner receipt 有效性、查询 Temporal 终态、创建 Task 或声称真实集成完成。`approval_currently_valid / integration_verified` 维持未知。

已有 Task evidence 的 Interface 包含开发 task 原 run/history 调度事件和 job receipt，需要 SDK／RPC；将其泛化为训练归档读取会混入另一种权威和生命周期。当前仅保留共同的 UTF-8 窗口处理习惯，不足以证明需要通用 evidence registry 或共享读取框架。原六阶段、candidate 证据和采用职责未改。

## 测试与 CI 判断

新 fixture 通过原 `perfctl archive` 生成有效归档，不在测试中复制产品读档或门禁算法；fixture 的独立脚本隔离了原 archive 的导入路径和 stdout。其父 fixture 继续复用既有项目、baseline、runner、manifest／spec／job。首轮遗留负记录后来显式移除，未放宽原 reader 的 binding 检查。

新增测试保护原字节污染、跨项目 archive／ticket、symlink、缺少 archive、显式 SHA／索引、二进制、容量及 Unicode 窗口等真实静默误读风险，调用应用 seam 并穿过真实子进程。已有 `test_training.py` 覆盖的注册／manifest／spec／runner／job 身份能力没有重复搭一套模拟。CI 只把新 suite 登记一次；完整配置没有重复 suite。architecture allowlist 仅接纳实际 reference 适配模块，未删除原依赖图断言或另造同类测试。

本轴未提出“把每个普通异常再测一遍”、为单消费者建立抽象父类、或合并两种 evidence 权威的建议。当前测试规模和新增 142 行私有算法相称。

## 已直接核验的证据与边界

私有原件根为 `.ergora/checks/training-evidence/`。亲读 source r1／r2／r3 的 `result.json` 与 stdout／stderr，并独立摘要；原 argv 均为 evidence／training／architecture 三 suite。

|原运行|实际结果与可归属范围|
|---|---|
|source-r1|26 通过／9 失败／2 跳过，pytest 24.15 秒；九个目标场景均被父 fixture 遗留旧 binding 的 negative record 先拒绝|
|source-r2|34 通过／1 失败／2 跳过，25.44 秒；仅 gate JSON 追加空白却预期冲突的测试失败|
|source-r3|35 通过／2 可选 web 跳过，24.32 秒，monitor 25.361 秒；两次失败历史仍在，不是产品 guard 被删后的成功|
|install-r1 四 suite|45 通过／1 失败，40.23 秒，monitor 41.853 秒；新 HTTP 测试先因默认 TestClient Host 未满足原 HTTP 合同获 400，既有 training HTTP 测试通过；修后运行待|

独立打开 r1 wheel，重算 SHA `85b232ca0e5ae98e41749c26b4aa8bc9482d1f0112eb81c4bcc3edc014e160b1`；573 产品文件与构建快照、实际 site-packages 和本轮工作树逐件逐字一致，wheel 581 行／安装 586 行两份 RECORD 的声明长度／SHA 全相符。283 冻结参考文件在包与当前树均逐件匹配 manifest。此为原安装的身份核验，不是本轴执行安装或重跑检查。

本轴另执行完整 tracked `git diff --check`，无诊断；全部新增路径的 no-index whitespace 无诊断，8 个改动 Python 文件 AST 解析通过。静态检查不替代实际 CLI、loopback HTTP、SDK-free、原文件集合保持或进程／服务收尾。

## 下一步与支持范围

本片本地验收证据已补核，**没有开放产品结构 finding**。下一步是普通提交／推送，按固定候选补核原完整 Ref、文档／产品身份与本片自己的 CI；本地通过不预先关闭这些发布责任。

原生 Windows、真实 Temporal 服务、训练／GPU、质量／性能、owner evidence 批准、实际集成或采用均没有本片运行主张；C2／C3、F9d／B3 保持原计划范围。

## r2 修后安装与自身模板补核

只读补核 r2 实际 wheel `d67ced0f3f65e21db69ee34a113552e9af64413f3384edcb5efe080dc785a98a`：573 产品逐件逐字匹配构建快照、实际非 editable 安装和当前树，wheel 581 行／安装 586 行两 RECORD 的每项摘要与长度相符，283 冻结文件全部相符。构建快照和当前 9 路径组合 SHA 都为 `bca645238f08d12e639da8b8f3732cdda651bd31e5aae735b97ee025a345aca9`。r2 包产品也与 r1 产品相同，修正范围只有原 HTTP 合同的测试使用方式及构建时文档快照；没有放宽产品 guard。

直接读取 r2 `regression-r1/result.json`、完整测试条目与 stderr：evidence／training／web／architecture 四 suite **46 通过、无跳过，pytest 38.99 秒，monitor 40.629 秒**；原 argv 使用该 wheel 的 Python `-I`，测试根为 r2 源快照。首轮安装失败由修后独立运行关闭，首轮原件仍保持其失败范围。

Ergora 自身原结构模板：实读 run `be2d83de99d94d7cb04c4ed72d5f7a4b` 的 admission、实际 native run／stdout、原 result 与 packet。12 份完整文件共 240,476B，逐一按原 packet 大小／SHA 从 task 提取相符；涉及产品的内容与当前树一致。原 task 的 SHA、245,299B prompt 的 SHA 与 request／native run 相符，实际 stdin 与完整 prompt 逐字相同，12 份文件及祖先／子角色两份 instructions 和 Skill 原文都完整出现在 stdin。原 result 与 run result 逐字相同、SHA `4de644590c23cbd128bb855028afc861c69e08d888341ee5c0d6205355630517` 相符，原回复为 `approve` 并明确没有独立实跑验收。本次使用用户已授权的 Codex 回退，未宣称异后端成功；本轴判断仍来自自己的源码与原件核查。packet 中 HTTP 测试是修前历史版本，此模板结果不替代上述 r2 实跑或本轴对修后测试的检查。

## 实际入口、原件保持与最终裁定

已读 `native-r1.py` 与两份 continuation 脚本，以及原 archive fixture／stdout、job stdout、commands、最终 CLI 与 SDK-free stdout／stderr、前置文件清单。确认真实原 init／runner／prepare 和原 adapter 的本地 job request 后，使用原 `perfctl archive` 及 POSIX 锁构造合成 evidence；没有运行 executor。归档 fixture 与本片测试 fixture 只存在已说明的 `unlink(missing_ok=True)` 和不创建 executor started 记录两项差异，没有替换 archive／gate 算法。

首次私有脚本因错误 SHA 的产品退出 2 与其预期 1 不同而中断；第一份 continuation 又因将整个 site-packages 放入 PYTHONPATH、仍能找到 SDK 而触发自身断言失败。亲读两份原脚本与保存的错误 stderr，不把它们追认为通过。最终 continuation 沿同一原 ID／archive 只继续读取：r2 安装 Python `-I -m ergora` 的四条原 argv、stdout／stderr 对应两次成功及两次正确退出 2。其无 SDK 进程以 `-P -S` 只提供已安装 Ergora 的副本和原参考源码，实际执行 `find_spec('temporalio') is None`，返回 JSON 与完整 CLI JSON 相等。

本轴另直接重算原 `evidence.json` 的内容地址，核返回 evidence 与原对象相等；所选 `notes.txt` 的完整 SHA、Unicode 总字符数、offset／next_offset 和返回 `窗口 🧪` 均与原全文的 `[2:6]` 相符。原索引保持 `artifact_content_status: not_read`，未把单个文本验证扩大为全部 artifact 或真实质量通过。

已读真实 loopback HTTP service／client、六条 client step、六条服务器 requests JSONL、六份原 response body、result 与 monitor cleanup。六项分别为完整证据／Unicode 窗口 200、错误 SHA／非索引路径／NUL 二进制／超上限 limit 400，逐项重算 body 长度／SHA 与 client、server 两侧完全一致；两个成功 JSON 与最终 CLI 相等。实际原请求全为 GET，零 mutation；原 cleanup 是已停止的 monitor 结果，原 final-observations 记录端口连接结果 111。本轴没有重启服务或探测当前端口。

直接对原 `protected-before.json` 的 14 件准备文件和 `read-before.json` 的全部 37 件 config／runtime 原件重新摘要，均与当前原字节相符；当前完整原文件路径集合也恰为 37 件。不存在 executor started、workflow submission、fence、owner receipt／approval、integration ticket 或命令 marker，原本地 job request 单列；以不获取可选锁的只读 Git status 核合成验收仓库为空。没有把这一合成归档认作真实训练／GPU、性能或质量证据。

最终[公开证据](evidence/2026-11-14-training-evidence.json)的 **54 份**私有原件引用，本轴逐份重新核大小／SHA，全部相符。作者 plan／delivery 已区分源码失败、安装 Host 测试修正、两次私有脚本失败、修后通过及发布在途；旧失败和自身模板的旧测试范围保持。新增公开证据与另一轴报告属于本片验收记录，不构成新产品行为或递归 review。

最终维护性与本轴所查需求结论均为本地通过，finding **0／0**。新增 guard、helper、私有算法位置、原库复用及测试／CI 的必要性判断保持；没有需要为了本片再加入的共享框架、抽象、重复测试或额外 guard。普通精确发布、自己的 CI 以及上述未验平台／真实业务范围继续各自记录。
