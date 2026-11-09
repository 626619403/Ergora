# AC5 C1 定义库与静态预览：独立审查

**本地终核通过：Spec、Standards 均为 0 开放 finding，C1-S1 已关闭。** 最终 24 文件、R4 安装包/浏览器、真实自身模板及公开脱敏证据已核；本候选普通提交、自己的必要 CI 和明确 HTTPS 精确远端仍待验。下文保留初审与同片修正历史。

审查者为新的 fresh-context 独立主审及分别新建的 Spec、Standards 子审；按 AIHERO 的 `code-review`、`codebase-design` 和 `maintainable-project-delivery` 原规则执行。项目与文档均归本仓库。原始要求、C1 规格和实际源码先于作者交付叙述读取；不将待办 C2–C6、整个 AC5/AC6 或 F9 计为 C1 缺失。

固定基线为 `d7ad71d37a1a3223b0cab3c93cbad1b522320377`，初审 HEAD 与基线相同，新增提交列表为空。本次是明确授权的未提交工作树审查，实际比较 `git diff d7ad71d37a1a3223b0cab3c93cbad1b522320377 --`，并逐份读取四个未跟踪文件。初审 16 文件与 `independent/scope.json` 的全部 SHA256 一致，tracked diff 与保留原件逐字相同。主审仅写本报告及本片私有证据，没有修改产品、测试或其他文档，没有安装、启动服务、模型、提交或推送。

## 初审范围与结论

范围为 `src/ergora/web.py`，控制台的 `app.js`、`definitions.js`、`index.html`、`style.css`，`tests/test_definition_console.py`，两本定义手册、USAGE、PLAN、当前架构、C1 计划/交付记录，以及领域 P5 的三份计划/交付/审查状态增量。四个新文件是 `definitions.js`、新测试、C1 计划及交付记录。

**初审要求符合性和维护性均有一项 P2 阻塞 C1-S1。** 作者已据原浏览器反例应用最小修正；修后安装包和浏览器证据尚待同片复核，本节不提前记为通过。

## Standards

独立 Standards 子审发现 **1 项 P2 硬约束违反，C1-S1**。原 [definitions.js](../../src/ergora/data/console/definitions.js) 的导入只捕获 `detailRequest`；当前上限输入只递增 `previewRequest`，迟到导入仍自动 `openDefinition` 并清空用户文本。场景为：选工作流 A → 开始导入 B → 在回复前编辑 A 的上限 → 放行成功回复。独立调用实际输入处理器复现，违反[当前架构](../architecture/current.md)的“迟到回复不能覆盖新选择或已修改上限”及 C1 状态所有权合同。最小修正是在自动打开导入根前，同时核验开始导入时的上限/预览世代；有编辑时保留当前选择与文本。

Heuristic 无其他实证 finding。七个 HTTP handler 是必要框架接口，均复用既有用例；新视图和私有函数归同一实际生命周期所有者，`app.js` 是其唯一合理生产调用者。未发现重复 validator、单用公共抽象、新 CI 或有证据的性能阻塞。三项新增测试覆盖传输合同与历史读取/当前准入分离，没有镜像全部底层校验。实例数和静态材料预算继续由原编译器拥有；本次源码审查不冒称 C6 大图性能已验。

## Spec

独立 Spec 子审发现 **1 项 P2，C1-S1**。导入在途时输入不会增加选择世代，旧成功回复仍切换根并重置上限，违反[规格](../plans/2026-11-09-composition-console.md) C1 的“失败/迟到回复保留当前选择”及所有权合同“无效/未保存输入不因……迟到回复丢失”。主审另以未改源码模块和内存 DOM/HTTP 复现；源 SHA256 与初审范围一致。作者随后对原 R3 安装包用实际 Chromium 延迟真实 install 成功回复，同样观察到 `input_preserved=false` 和 `selection_preserved=false`。

其余源码未发现 C1 缺失或越界：七个 HTTP 入口直接调用原 Agent/Workflow 所有者；历史身份读取与当前 preview 准入分开。页面可在空项目状态进入，预览呈现完整资源、来源、权限、端口和预算；默认后端明确为请求，没有新增执行或项目授权路径。正文 JSON 下载与完整包导出用途已分别说明。

## 初审已核证据和限制

初审身份、tracked 原件核对和两份独立竞态复现保存在本片私有 `independent/`；主审复现为 `late-install-grant.mjs` / `late-install-grant.json`，Standards 独立复现为 `standards-import-grant-race.json`。作者原 R3 浏览器反例为 `r3/browser/late-install-grant-original.json` / `.log`，记录无效文本变为新根默认 JSON。R1 返回类型错误、R2 顶层 null 文字的原包及红/绿证据各自保留，未被此次 finding 覆盖。

已读取 R3 包身份与测试原日志：435 个 source/wheel/install 文件、283 冻结文件，wheel SHA256 `3211c90616c1a9dd37af558d16fb5cb3a49f30c1157d3a27f6a5bef2caa65eb0`，22 passed / 18.99 秒。这些是原 R3 身份与实际测试范围，不是修后候选验收，也不是主审重跑结果。

领域 P5 仅核既有状态事实与差异。固定对象确为 d7ad71d、唯一父 d8fc8ef、86 文件，portability workflow 未变化；既有 `closure-evidence.json` 的 SHA256 为 `c8aab0797612e45b1853b7fe93881379ddb2e7915df9b514ca45a62267cdb36a`，八份官方采样原件、对象核对及 HTTPS 原件与汇总身份一致，七个必要步骤成功。四份入口/状态文档与既有 P5 终结证据相符；未递归重审领域片，未作新的当前远端声明，也不以 P5 CI 替代 C1。

尚待修后同片复核、最终包完整真实浏览器旅程（含关闭重开、窄屏/键盘及迟到回复）、自身真实审查模板、最终快照和公开脱敏，以及本候选的普通提交/必要 CI/明确 HTTPS 精确远端门禁。源码修正不继承原 R3 运行通过结论。

初审计数：Standards **1 finding，最高 P2（C1-S1）**；Spec **1 finding，最高 P2（C1-S1）**。

## 同片源码复核

修正后的 `definitions.js` SHA256 为 `0f46722f8d7a045be8783cc83e9e6dadac2e279791939b5aca7328bec4223e9c`。相对保留 R3 仅增加安装起点的 `previewRequest` 捕获，并在自动打开根时要求选择、预览两代均未变化；没有扩展 C1 范围。

- **Standards：源码复核通过，C1-S1 源码 finding 关闭。** 新条件对应真实上限编辑和预览操作，在两次异步等待后核验，不增加抽象或重复业务校验。Standards 独立离线复验安装等待期间编辑、后续库刷新等待期间编辑、无编辑正常打开根三种场景均通过；原红与 `standards-import-grant-fixed.json` 分别保留。无新增硬标准或 heuristic finding。
- **Spec：源码复核通过，C1-S1 源码 finding 关闭。** 主审以同一真实 UI 模块场景确认文本逐字保留、选择仍为 A，且没有再请求 B 详情；`late-install-grant-source-fixed.json` 固定实际源 SHA。独立 Spec 复核确认符合迟到回复保留选择与文本合同，没有增加执行副作用。

该轮仅完成源码与离线状态行为复核，当时 R4 最终安装包、实际浏览器完整旅程、自身模板及最终快照仍待取得，不继承 R3 的运行证据；随后终核见下文。

源码复核计数：Standards **0 开放 finding**；Spec **0 开放 finding**，两轴 C1-S1 原反例及处置均保留。

## 最终 24 文件及本地验收

最终冻结清单为本片 `acceptance-scope.json` / `.diff`，基线仍为 d7ad71d；清单 SHA256 `686953f65f96882805d2803bf38565b360a431da78c0697768911db6e1b3ad7d`。完整范围恰 24 文件，含全部 tracked/untracked 实际正文、五份公开 JSON 和两张 PNG。相对初审，产品仅有上文已复核的 C1-S1 修正；其余新增为本审查报告及七份公开证据，计划/交付变化为状态记账。冻结后 delivery 更正早期 read 失败次数属于已授权说明增量；原快照没有被覆盖。源码、测试和全部公开原件逐字保持冻结身份，本报告及其后 PLAN、本片计划/交付的状态追加单独允许。

R4 wheel SHA256 `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`。主审直接读取 ZIP、实际安装目录和当前源码，**435 文件逐字相同**；另对固定基线的 Git blob 核 **283 冻结文件逐字相同**。实际回归原日志为 **22 passed / 18.28 秒**，其 SHA 与公开记录一致；本次没有重复运行测试。

实际 Chromium 的六组脚本、原 Result、日志 SHA 与公开投影全部相符，覆盖空项目进入、三域导入及幂等重试、13 Agent/11 Workflow、完整 19 实例材料、错误/迟到回复、刷新/切页、窄屏键盘与重开。C1-S1 原 R3 与修后 R4 使用同一真实延迟回复脚本，结果由双 false 变为双 true，**运行复核关闭 C1-S1**。下载的 Agent 正文及 preview JSON 与实际原库/编译器的只读结果完全相同；两份下载文件 SHA 与原记录相同。

HTTP 重启前后 argv、端口和控制目录相同，PID/starttime 已更换；原重启脚本实际比较完整两库及 bootstrap，浏览器重开后的训练预览为 9 实例、仍 0 项目。主审另只读确认最终 owned 端口关闭、保存 PID 的进程已不存在。390×844 的 document 宽 390，实际 Tab/Enter/Space 操作有原脚本和结果；两张公开截图与原图逐字相同并经主审目视查看，无个人路径或凭据。此处仅验已述 Linux/Chromium 和当前组合，不推导全平台或 C6 容量结论。

公开 [R4 包](evidence/2026-11-09-definition-console-package-r4.json)、[浏览器及原红/修后绿](evidence/2026-11-09-definition-console-browser-r4.json)、[桌面](evidence/2026-11-09-definition-console-desktop.png)与[窄屏](evidence/2026-11-09-definition-console-narrow.png)均与保留原件相符。历史包/回归、原 B1 与 S1 红日志的公开 SHA 也逐项匹配；私有 harness 的角色名和 State 调用错误如实保留，没有据此改产品。

## 自身模板与实际读取终核

主审使用原 inspectors 只读核验 prepared manifest、prepared input 和实际 run input，三个完整 composition 相同；manifest 摘要 `76c1746d…`、实际输入摘要 `8ef85855…`、prompt SHA 和 admission 的 binding/policy 均与原运行一致。原两定义库确已移除。1.0.1 证据修订与 R4 随包模板逐项比较：原指令/Skill 保持，仅为 Agent 增加完整候选附件、更新相应精确 Workflow 引用和静态材料上限；实际 run root 与该修订一致，没有换成临时自由提示调用。

真实 run `b83d16cae6e244368f397a1f9aaa66ce` 为 **178.21 秒、succeeded、approve**。候选附件 **281802 字节**，21 份源文件正文完整包含其中且仍同一 SHA。直接解析原生 stdout：一次短路径 read 失败仅返回泛化错误；随后按完整资源路径成功返回 15 页，先 40000 字节探针，再 14 页从 offset 0 连续至 null。主审逐页核 offset、size、SHA、next_offset 和实际返回正文，最终拼接逐字等于原附件；两份祖先指令与两份 SKILL.md 的实际成功返回也逐字匹配固定输入资产。初版单遍审计拒绝重复 offset 0 的失败日志保留，新审计没有编辑原流或重跑模型。

原意见 SHA256 `4383b3e2194816b6c1c30dcbd8b94614f81a4ed6c83ce294c6426cdeca10fc63` 与原 run 一致。[公开输入身份](evidence/2026-11-09-definition-console-self-review-identity.json)、[读取审计](evidence/2026-11-09-definition-console-self-review-reads.json)和[原意见投影](evidence/2026-11-09-definition-console-self-review-result.json)逐项对应原件；公开排版文件与原生结果字节的 SHA 用途已明确区分。五份公开 JSON 均可解析，无个人路径、认证状态或外部 key 值。模型没有执行仓库测试，实际完整材料交付也不证明推理质量、模型错误独立或正式 owner 批准。

## 最终两轴结论和剩余门禁

- **Standards：通过，0 开放 finding，C1-S1 关闭。** 独立子审复核最终范围与增量；七个 HTTP 入口保持原用例所有权，前端状态保持原视图生命周期。未发现重复 validator、单用公共抽象或重复测试/CI，未新增依赖或存储迁移，未发现有证据的性能问题。真实模板意见与运行事实、状态文档和交付门禁准确区分。
- **Spec：C1 本地要求符合性通过，0 开放 finding，C1-S1 关闭。** 独立子审核最终范围、实际浏览器和原流逐字读取；空项目定义库、完整静态预览、持久化、错误/迟到回复及无执行授权副作用均有相应证据。未发现 C1 缺失、错误实现或范围扩张；C2–C6 继续是后续切片。

主审私有核验结果分别保存为 `independent/r4-*-check.json`、`self-review-audit.json`、`public-evidence-audit.json` 及最终范围审计。这里只完成 C1 本地出口；**本候选普通提交、自己的必要 CI 和明确 HTTPS 远端完整 SHA 仍待验**，不能借用 P5 或其他候选。未重复调用模型、启动浏览器/服务或重跑测试，未提交/推送。

本报告追加后的静态复核为 **11 份 Markdown、208 个本地链接/锚点、94 条 CLI parser 命令通过**；结果另存本片 `independent/`，没有覆盖模型附件所用的历史静态原件。此项不替代应用或平台运行验收。

最终计数：Standards **0 开放 finding**；Spec **0 开放 finding**；两轴原最高 **P2（C1-S1）均已关闭**。
