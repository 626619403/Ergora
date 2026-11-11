# AC5 C5b：正式任务组合选择独立审查

**C5b 本地审查与精确交付门禁通过：Spec、Standards 开放 finding 均为 0；SP1/SP2 两项 P2 和 ST1 一项 P3 已关闭。精确提交、包身份、独立 HTTPS 远端同 SHA 及本提交自己的 CI 终态均已核。** 初审发现及当时证据按下文保留，不回写原失败为通过。

主审 `task_composition_selection_review`，fresh context；另按 AIHERO 的 `code-review` 启动互不继承上下文的 `spec_axis`、`standards_axis`。先读原始 C5b/AC 要求和 `AGENTS.md`，再读作者记录；应用 `maintainable-project-delivery`、`references/independent-review.md` 和 `codebase-design`。本报告只评 C5b 创建入口，不代表 C5c 六阶段、C6 容量或项目完成。自身模板与独立审查分别记账，不称不同模型独立。

## 固定候选与范围

基线与初审 HEAD 均为 `f68d7390e0e65f8045158cb1d0270c4057c7a74d`，分支 `refactor/architecture-foundations`。`git diff f68d7390e0e65f8045158cb1d0270c4057c7a74d...HEAD` 和对应提交列表为空；按用户持续授权的 WIP 例外，以本地 `review-r1/identity.json`、`tracked.diff`、`files/` 的完整 15 文件为候选。快照时间 15:27:06 UTC；主审独立核全部快照、身份记录和当时工作区 SHA256 一致。

审查四个产品 JS 全文：`tasks.js`、`tools.js`、新 `task-composition.js`、新 `binding-fields.js`；文档范围为 `AGENT_DEFINITIONS.md`、`USAGE.md`、`WORKFLOW_DEFINITIONS.md`、`architecture/current.md`、`PLAN.md`、C5 总计划、composition-console 计划、新 C5b 计划与交付记录，以及前片 C5a 两份状态续记。新文件均读原文，既有文档读完整变更及必要上下文。前片续记不重新授予 C5b 通过。

原需求依据为 [C5 分片](../plans/2026-11-10-composition-handoff.md)、[C5b 详细计划](../plans/2026-11-10-task-composition-selection.md)及其实施前私有 `plan-preparation.md`，并回读 [AC 原目标](../plans/2026-11-08-agent-composition.md)。只读追踪 `tasks._composition`、schema-v2、`review_dags.WorkDelivery`、原 task creation、后端共有 Interface/模式策略、组件 configuration、页面 form/api/state 与刷新生命周期。

## Standards

fresh-context Standards 轴结论：**通过；新增硬文档违规 0，可行动 smell 0，最重问题无。**

- `AGENTS.md` 与 `current.md` 的所有者规则保持：`tasks.js` 继续拥有 preview/create、sequence、creationLocked 和原 ID 未知恢复；组合表单只构造原 schema-v2，未复制 WorkDelivery、后端准入或调度。
- `binding-fields.js` 确有 `tools.js` 和 `task-composition.js` 两个生产消费者；`taskComposition` 虽只有一个调用者，但凝聚完整表单和 manifest 异步生命周期，有明确所有权，不是纯转发包装。
- 字段来自已有组件 configuration，没有按厂商名重复分派；writer 不从静态请求自动继承信任，原后端仍负责模式及 Linux/current-container 拒绝。当前容器是已接受的可信当前用户执行范围，未增加 OS 隔离保证。
- 新 guard 分别保护外部输入、尚未核包的配置、writer 显式选择和迟到响应；未钉死合法配置范围。没有新增依赖、schema、数据库、测试或 CI 作业，也未发现需要另加镜像断言/测试的依据。

轴记录保存在本地 `independent/standards-axis.json`。此维护性结论不抵消下面的规格缺口。

### C5b-ST1 / P3：总 PLAN 验证状态滞后（已关闭）

修正复审时，`review-r2` 的 `docs/PLAN.md:18` 仍写 R4 受影响页面待验，而本片计划及交付记录已记 R5 补段通过。不符合 `AGENTS.md` 要求的验证完成后同步 PLAN，恢复工作者可能重复旧候选验证。最终快照已同步 R5/22 检查/30 HTTP、模型复核和公开证据，继续保留精确交付待验；原 Standards 轴已只读复核关闭。此项不曾阻塞产品正确性。

## Spec

fresh-context Spec 轴确认一项 P2；主审另对实际自身模板提出的第二项作源码核证。未发现明确范围外行为。

### C5b-SP1 / P2：成功重载工作单元清空原手选

**状态：已关闭；原独立 Spec 轴确认 R5 修正及受影响补验。** 原候选 [task-composition.js:159](../../src/ergora/data/console/task-composition.js#L159) 每次成功载入都调用 `select(choices, "")`，随后替换全部 assignment 节点。[详细计划第 3 项](../plans/2026-11-10-task-composition-selection.md)明确要求“保留原输入及手选”。

可达触发：用户已逐项分配后，再次点击“从当前输入载入工作单元”；或保留既有 unit、新增 unit 后重载。所有既有选择都被置空，用户必须逐项重选。已有 `browser-main-r3.js` 只核坏 JSON 读取失败时保留，未覆盖成功重载。

最小修正：同一 manifest/work 子流程下按 unit ID 保留仍在当前选项中的原实例；新增项留空。更换 work/manifest 时沿现有清理，不新增分配准入规则；完整关系继续由原 WorkDelivery 校验。

主审已见修正从当前 `assigned` 构造 unit ID→choice value，再用于新选择器；同包图与 work 路径不变时选项固定，更换 work/manifest 原有 `assigned = null` 清理仍在。

### C5b-SP2 / P2：模板读取失败丢失已编辑输入

**状态：已关闭；原独立 Spec 轴认可 R5 修正及受影响补验。** 原候选 [tasks.js:239](../../src/ergora/data/console/tasks.js#L239) 的 `loadTemplate()` 在 GET 前执行 `input.value = ""`、`draft.value = ""`；失败分支只显示错误。C5b 总验收要求“失败保留输入”，详细计划同时保留“草稿/输入保持”。

可达触发：已有已编辑 JSON 和草稿选择时点击“载入所选模板”，该 GET 失败。原始 JSON 与草稿选择已被清空，错误后无法恢复。该路径虽继承自原入口，仍不满足本片明确的失败保持要求。实际自身模板首审提出此项，主审读取原源码后独立确认触发和后果。

最小修正：保留预览 invalidation；只在成功且仍属于当前读取的回复内替换输入及草稿选择。受影响补验应核失败时逐字保持 edited JSON，以及成功/迟到回复仍遵守原 sequence。

主审已见上述修正：GET 前只失效旧预览；JSON 替换及草稿清空均在 `current(reading)` 后执行。

## 已读证据与边界

读取三轮 build/install 与 package-identities 原记录。R3 wheel SHA256 为 `f1a62824e0db346d661d3183bb239f1dcd2cb521725d229f8ba1dbf4c3a6d120`；记录为 439 源/wheel/安装文件、两 RECORD 与 283 冻结资产。两独立轴核四 JS 与 R3 wheel 一致；Standards 轴同时核安装副本及记录。此身份只属于 R3，后续修正不能继承其全部运行通过。

读取 `browser-main-01..06.json`、相关原驱动、`audit-browser.py`、`browser-audit.json`、cleanup 及必要原件；按主代理边界不重做已经完成的 144 HTTP、4 合同、48 原对象全量审计。六轮保留各自失败：label 定位、非数字 IID、另一 writer 先拒绝、旧 `spec.request` 展示错误、fieldset 驱动判断；第六轮仅承接已丢回复的原 ID 查询及其后行为。R2/R3 的成功 checkpoint 不倒填前轮整体通过。

既有离线审计记录 9 次成功 manifest、9 次成功 preview、4 份各 7 文件发布、48 旧对象保持；两 home 无 Agent run 或提交/请求/回执/workspace。此处只说明原记录实际范围，不推导六阶段运行。实际目视原桌面 1440×1000 和窄屏 390×844 两 PNG，所截选择区无横向溢出；窄屏长路径在原生 select 中裁切，完整身份仍须读 option/服务端 preview，不能据两图声称全页或容量通过。

实际自身模板首审原件为本地 `self-review-r1.json` 及 `self-review-r1/{review.md,original-result.json}`：run `6885032f0074414a9638acbd8452a951`、evidence `1.0.82`、167.84 秒，真实后端 Codex / `gpt-6.1-sol`，Spec request-changes、Standards approve；四 JS 身份等原候选。主审离线比对原 stdout、冻结 scope 与 native MCP trace：五份 scope 均完整，candidate 244105B 经 11 个连续 UTF-8 窗口至 `next_offset: null`；另两次 24000B 复读字节相符。共 1 次 list/17 次 read，scope 摘要和原 native 成功调用一致。私有 `independent/model-read-audit-r1.json` 保存逐 scope 核对及审计器对复读的处理说明；原 request-changes 保持，不推导模型理解或不同模型独立。

未运行测试、浏览器、模型、安装或网络，未修改产品。自然 BFCache、跨浏览器、Windows 实际页面、真实两开发域六阶段、C6 容量及外部/GPU 功能均未由本次审查证明。

## 修正与最终候选续核

修正固定快照 `review-r2` 为 2026-11-10 15:41:08 UTC 的完整 15 文件；主审核全部文件身份及相对原候选的差异。产品只改 SP1/SP2 两处：一张局部选择映射，以及成功回复后的输入替换；另两 JS 不变。原 Spec 轴关闭两项，原 Standards 轴未发现新增产品违规或可行动 smell；没有增加测试、CI、依赖或领域校验。

R5 wheel SHA256 为 `5b0e11fd31baa068a349493e4de9d996d528f3ca5e44d43522b2b894e77fae33`。主审离线独立核 439 源/wheel/安装文件及两 RECORD 各 439 个包文件记录，283 冻结源等原 manifest；四 JS 等修正快照及实际所服务字节。`independent/fix-r5-evidence-audit.json` 无错误。R4 仅有 SP2 修正的包身份，不继承页面或模型通过。

实际补段 `browser-supplement-07.json` 为 2.94 秒、22 检查通过。原完整驱动覆盖模板错误逐字保留 JSON/草稿、当前成功替换、迟到成功不覆盖新编辑；分配重复、增删、重排、失败保留、新增/重新引入留空及切换 work 后不复活旧选择。主审核新 30 对 HTTP 的原请求/响应、metadata bytes/SHA，一致且产品请求全为 GET；三份模板原服务端响应均为 200，503 是驱动在原 200 后明确注入给客户端。补段没有 preview/create、Agent 或六阶段重放；其两 home 不变与四采样进程身份不在只沿原证据范围。初次私有 manager 因非交互 stdin EOF 退出的原件继续保留。

修正后实际自身模板 run `04d2d3e522694311a50256d23596d92b`、evidence `1.0.83`，79.67 秒，Spec/Standards approve。主审直接核原 stdout、scope 和 native MCP trace：五份 scope 的 145540B 均完整；candidate 143890B 经六个连续 UTF-8 窗口至 null，无复读。共 1 次 list/10 次 read，所有页等冻结原字节；四个完整产品源确实嵌入附件并等 R5，实际 stdin、输入 prompt 与 protocol prompt 相同，原结果等 protocol result。私有 `independent/model-read-audit-r2.json` 无错误；没有重新调用模型或执行附件。原首审 request-changes 保持，第二轮通过仅证明其实际复核范围，不代替独立审查、正式 owner 或不同模型独立。

模型成本按后端原报值记录：首轮 input 747236（其中 cached 656512）、output 3586、单列 reasoning 1730；复核 input 274510（其中 cached 212608）、output 1656、单列 reasoning 406。cached 已含于 input，reasoning 不再加到 output；这些不是账单。复核附件从 244105B 减到 143890B、read 从 17 次减到 10 次，仍保持完整四源和必需祖先材料；不据两次调用推导普遍速度、质量或费用保证。没有为本片增加镜像测试或 CI，受影响补验未重复原 144 HTTP/4 合同/48 对象验收。

最终 `final-candidate-r2` 快照时间为 2026-11-11 02:18:53 UTC，共 23 文件：原 15 文件、当前审查报告、五个公开 JSON 和两 PNG。主审核全部快照与当时工作区字节一致，产品与已审 R5 保持；新增文档只补模型、证据和状态。报告自身随本次续核更新属于本片记录，不触发评审的递归评审。

五个公开 JSON 的 36 处引用对应 35 份私有原件，主审逐份核原 bytes/SHA、声明删除字段及两个派生清理字段，投影与原件经明确路径/15 个私有 origin 替换后完全一致。两公开 PNG 等已经目视的原图字节；没有重拍或扩大所截区域结论。`independent/public-evidence-audit-r1.json` 无错误。公开入口为[页面及补段](evidence/2026-11-10-task-composition-selection-browser.json)、[包与原准备失败](evidence/2026-11-10-task-composition-selection-package.json)、[两轮自身审查](evidence/2026-11-10-task-composition-selection-self-review.json)、[分页读取](evidence/2026-11-10-task-composition-selection-reads.json)、[采样清理与用量](evidence/2026-11-10-task-composition-selection-cleanup-usage.json)。

读取最终本地出口记录：234 个本地链接/锚点、五 JSON、四 JS 语法与 whitespace、受保护四源保持均通过；环境敏感值扫描为作者检查，主审没有读取密钥值。预检脚本行首分号 SyntaxError，以及无边界 `sk-` 模式将文件名子串误判为密钥的失败与逐项处置均保留；修正扫描器后零 issue，没有修改产品来迎合检查。主审没有重跑该出口或任何产品行为。

**最终本地出口通过：Standards 开放 0、最重问题无；Spec 开放 0、最重问题无；SP1/SP2/ST1 关闭，阻塞 0。** 可固定 ready 并继续原授权的普通提交/推送。本提交自己的 CI、精确 Git/包/283 冻结身份与独立 HTTPS 远端同 SHA 仍须另核，不转授前片或旧候选 CI。C5c、C6 和项目整体未完成。

## 精确提交与远端续核：首轮 CI 待定

以上保留提交前本地门禁的历史状态。现核普通提交 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`，唯一 parent 为原基线 `f68d7390e0e65f8045158cb1d0270c4057c7a74d`。`commit-closure/commit.json` 记录 2026-11-11 02:24:02 UTC 提交成功；`push.json` 与原 stderr 记录 02:24:20 UTC 普通推送成功，`HEAD -> refactor/architecture-foundations`，未 merge/force/写凭据。

主审从该精确 Git 对象读取并核 23 个变更文件，集合、bytes、SHA256 均等 `commit-closure/ready/files/`；ready 身份文件 SHA256 为 `82be41990867ad02d569f6f52b55ef4590153531a941b8fc061f7d4a1c5aaa54`，与提交记录一致。其中四产品源继续等模型 R2 已完整读取的附件。精确提交中全部 439 个包文件逐字等 R5 wheel 和安装副本，两 RECORD 各 439 包条目成立；283 冻结文件等原 manifest，Git blob、内容和模式均等原基线。R5 wheel 仍为 `5b0e11fd31baa068a349493e4de9d996d528f3ca5e44d43522b2b894e77fae33`，未重建或安装。私有 `independent/exact-git-package-audit-r1.json` 无 issue。工作区随后新增的 C5c 计划与交付文档不属于本次 23 文件候选。

按新增授权，主审只执行一次独立 HTTPS 读取：[Git smart refs](https://github.com/626619403/Ergora.git/info/refs?service=git-upload-pack)，2026-11-11 02:27:09.189859 至 02:27:10.002073 UTC，0.812213 秒，HTTP 200、curl exit 0。未重试、未跟随重定向、TLS 校验开启，未提供认证或读取环境值。原响应 786B，SHA256 `47d8af0b67ed2c57f5bc7fce6f03b7edd05a25731ad0366679a2e51567708669`；逐 pkt-line 解析得到 `refs/heads/refactor/architecture-foundations` 精确等 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`。原 headers/body/stderr、URL、时刻、字节与摘要保存为 `independent/exact-https-r1.*`。这是本次审查唯一网络读取，不扩大此前离线审查的实际范围。

CI 只离线读取主代理保存的样本，没有执行取样脚本或重取请求。`snapshot-01` 在首个 HTTPS 握手出现 URLError/SSL EOF，`sources=[]`，没有取得 CI 状态，不能记为 CI 失败。`snapshot-02` 的五份官方原响应为 02:26:52.235277 至 02:26:57.805927 UTC，逐份核 URL、HTTP 200、bytes/SHA。原 actions/run 绑定本精确 SHA、分支和 `.github/workflows/portability.yml`，run 为 [42945800414](https://github.com/626619403/Ergora/actions/runs/42945800414)；完整 groups 为 Ubuntu 3.11 job `130278182300`、Windows 3.12 job `130278178468`，没有遗漏分页。原 run 为 `In progress`，两 job 均 `in_progress`、conclusion null；两平台 build/install 和 packaged reference 共四步骤 success，两个 native regression 及 Windows PowerShell 5.1 installer/upgrade 仍待。七必需步骤未全成，job 未完成，**CI 门禁待定**。

私有 `independent/exact-ci-audit-r2.json` 保存原件逐项核对。审计器首次离线解析误要求 job 页必须有 commit anchor，实际页没有该链接；已保留 `exact-ci-audit-r2-attempt-01.json`，改按原 actions/run、完整 groups、selected job ID 与精确 commit 的 step log URL 绑定后通过身份核对。只修正审计假设，未重取 HTTP、修改原证据或将运行中状态判为通过。后续须由同一候选自己的终态样本证明两 job 和七必需步骤全部 completed/success；此前本地及前片 CI 不替代此项。

**当轮结论：Spec/Standards 开放 0；精确 Git/包/283 冻结身份及独立 HTTPS 同 SHA 通过；本提交 CI 待定，精确交付尚未完成。C5c、C6 及项目整体未完成。**

## 精确交付终核：通过

主审仅离线续核主代理保留的 `commit-closure/snapshot-04`，没有重新抓取网络、执行作者取样脚本或运行产品、模型、浏览器、测试和安装。五份官方原响应采样于 2026-11-11 02:40:55.912668 至 02:41:00.625729 UTC；逐份核 requested/final URL、HTTP 200、原 bytes/SHA256，以及摘要与原页面一致。`ci-sample.json` 为 5056B，SHA256 `abdcf08209f9ee1af50b6101bc2f48945db8e2f46bb90d2274ae06539ecf39d9`。

原 actions/run 页面再次绑定精确提交 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`、`refs/heads/refactor/architecture-foundations` 与 `.github/workflows/portability.yml`，属于同一 [Portability run 42945800414](https://github.com/626619403/Ergora/actions/runs/42945800414)。原 run 状态为 `Success`；完整 job groups 为两项、`hasMore: false`。两 job 的 ID、名称、官方 URL、页面 selected job、精确 commit 的各 step log URL 均与摘要相符。

| 平台与 job | 必需步骤 | 终态 |
| --- | --- | --- |
| Ubuntu / Python 3.11，`130278182300` | Build and install wheel；Packaged reference identity；Native application regression | job completed/success，三步骤 success 且 job_completed |
| Windows / Python 3.12，`130278178468` | 同上三项；Windows PowerShell 5.1 installer and upgrade | job completed/success，四步骤 success 且 job_completed |

七个必需步骤全部通过，原 job 页没有 failure/cancelled/timed_out 步骤。本终态授予的是本精确提交自己的 CI，通过范围沿现有 Portability 工作流，不转授前片、旧候选或 C5c。

此前样本全部保留：`snapshot-01` 于 02:25:00 UTC、`snapshot-03` 于 02:37:08 UTC 均在首个 HTTPS 握手出现 URLError/SSL EOF，`sources=[]`，未取得 CI 状态；`snapshot-02` 仍如实为 `In progress` 和四个步骤 success，不回写终态。私有 `independent/exact-ci-audit-r4.json` 保存五原件身份、逐 job/step、两次网络未知及零审计错误；`exact-ci-audit-r2.json` 与首次审计假设失败记录继续保持。

此前已完成的 23 个 ready/Git 对象、四源/模型 R2、439 个 Git/wheel/安装文件与两 RECORD、283 个冻结内容/模式以及一次独立 HTTPS 同 SHA 均引用原审计，本轮没有重复。结合本终态，**C5b 精确交付门禁通过，Spec/Standards 开放 0、阻塞 0。** 本结论只关闭 C5b 创建入口及其精确交付；C5c 六阶段真实链正在另一片处理，C6 容量和项目整体仍未完成。
