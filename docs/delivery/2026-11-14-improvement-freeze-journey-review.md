# F10d7 组合旅程独立审查

Reviewer：fresh-context 独立 agent `improvement_freeze_journey_review`；日期 2026-11-14。按 `AGENTS.md` 与 maintainable-project-delivery 的独立审查指引，先读原需求、固定基线及实际差异，再核作者记录。未继承实施对话，未修改产品、运行昂贵验收、安装、联网、提交或推送；只写本报告。

## 身份与检查范围

本地审查时固定基线／HEAD：`3a56508791a33871016acff4a7cad268aaf0be50`，分支 `refactor/architecture-foundations`。已检查 tracked diff 与 untracked 新文件，产品为后文列明的两个原 owner；文档精确范围如下：

```text
README.md
docs/PLAN.md
docs/USAGE.md
docs/IMPROVEMENT_WORKFLOW.md
docs/plans/2026-11-14-evaluated-improvement.md
docs/plans/2026-11-14-improvement-freeze-journey.md
docs/plans/2026-11-14-workflow-improvement-console.md
docs/delivery/2026-11-14-improvement-freeze-journey.md
docs/delivery/evidence/2026-11-14-improvement-freeze-journey.json
docs/delivery/2026-11-14-workflow-improvement-console.md
docs/delivery/2026-11-14-workflow-improvement-console-review.md
docs/delivery/evidence/2026-11-14-workflow-improvement-console.json
```

前片独立报告和 CI 记录仅作为该固定候选的历史边界；本审查不代其 reviewer 预批其他候选的 CI。

首轮产品无变化；随后 browser-r1 暴露下述 R1，补核当前 `src/ergora/web.py` 与 `src/ergora/data/console/tasks.js` 两个原 owner 的最小未提交修正。**源码、原 r4 证据、最终新安装件、修后页面／CLI、自身模板、收尾和固定原件索引已直接终核。**

## 两轴结论

- **需求轴：最终本地、固定发布及自身 CI 终态均 approve。** 原 r4 组合冻结合同的实际范围成立，手册与原接口一致；R1 已以最终安装件及真实页面读回闭合。最终包对同一存档的 HTTP／CLI 和来源离线解码完全相同，旧文件字节保持，收尾与原件身份核实。固定候选自己的八 job／30 必要步骤已独立核验闭合。
- **可维护性轴：最终本地、固定发布及自身 CI 终态均 approve。** 产品修正限于原 HTTP 读接口及原详情折叠区，复用既有冻结解析器，无新模块、schema、解析器、权威账本或采用／编译路径。来源验证和解析继续归原 envelope owner，HTTP 只追加完整读取结果，前端继续使用既有 disclosure。新增条件只识别旧合同缺少 context 的可达兼容场景，没有额外 guard、fallback 或异常吞没。

最终开放 finding：**需求 0，可维护性 0；R1 已关闭**。在上述已检查范围没有其他 finding。本结论绑定固定候选 `8d739c298668ab9f7d88fdaa205a21f304d9586c` 及自己的 run `43583053417`，不代审后继 F9d1。

## Finding 与最小修正

### R1／P2：已创建任务详情未展示冻结资料来源

- 位置：基线 `src/ergora/web.py:963`、`src/ergora/data/console/tasks.js:1399`。
- 可达场景：创建 v7／v11 任务，随后更正记忆并回退 Skill，再从正式任务列表打开原任务。原 GET 的 `admission_envelope.context.selection` 仍正确冻结 memory revision 2／Skill head revision 2，但页面“完整冻结合同”只显示 legacy `task.spec`，没有所选 Skill／完整记忆来源。
- 实证：直接读取私有 `browser-r1.stdout` 的 `adopted-task exposes the selected Skill in its full frozen contract` 错误；对照基线详情只传 `task.spec`，GET 未解码 `selected_context`。这轮页面在该处退出，后半程不能计为已通过。
- 影响：用户在候选采用或后续更正后，无法从该任务页面核对其原冻结资料；违反本片同一项目浏览器读回节点，不影响已存档字节本身。
- 最小修正：沿原任务 GET，从 `tasks.show` 返回的原 `admission_envelope` 调用已有 `task_envelopes.selected_context`；详情增加与 prepare preview 同名的完整来源折叠区。当前两文件 diff 符合该范围，未查询当前 canonical 记忆／head，未重编译、更新任务或更换权限。旧无 context 任务保留原读取路径。**最终 install-r1 的 HTTP／browser-r2 红绿复核通过，R1 关闭。**

## 已直接核验的证据

原件根：忽略目录 `.ergora/checks/improvement-freeze-journey/`。本次没有重跑或拼接旧运行。

1. **原 r4 身份。** 从固定 HEAD Git tree、当时工作区源文件和原非 editable 安装逐件重算 **604** 产品的 bytes／SHA256，与 `run-r4/package-identity.json` 全相同。实际重算原 wheel 为 `304a2898c1d6fb5d3c285aea3786be4aeba4eb81e582d2bfe801d9dce9e33f8c`。这证明 r4 的原固定产品；两文件修正不会继承该最终产品运行身份。
2. **完整组合驱动。** 直接读 `journey-r4.py`、stdout／空 stderr 与 `run-r4/result.json`：一次从头 **37 checks／39.804669 秒**，**6 CLI／37 HTTP**；HTTP 为 36 个 200 与预期 stale 拒绝的一个 400。37 组 request／response 摘要全部重算匹配索引；六 CLI 原 command 均使用该安装 Python 的 `-I -m ergora`，exit0、JSON stdout、空 stderr。
3. **三类来源和采用。** 同一 source.zip 的 SHA 实测 `4aa8b5208aece2d3084886f30fa10d34d5971544c47298e8c0b840eaf62db6b7`，三 input 中的选择 SHA 同一。三份完整结果均保留失败、未知成本、适用性未测及同一材料引用，原 result SHA 全匹配。Skill 两次评价使用同一预先固定 suite，三个 split 都实际完成；反馈明确为合成 scorer，0.5／0.9 只证明合同通路。明确采用／memory save／workflow import 各沿原 owner，准备和导出不前移活动状态。
4. **独立父链核对。** 未只依赖编译器返回的资源列表。从冻结 assets 中的根定义沿节点 ref 逐层重建七叶的四至五层父链，逐一枚举声明资源，与叶的 sources 比较；每叶为 7、7、7、5、7、9、7 份资源，全部正文／Skill 主文在完整 prompt。所选 Skill 的完整两文件目录逐字等于原导出目录，七叶都相同。冻结记忆逐字等于导出 `memory.txt`，含 U+FEFF、20 个真实 CRLF，source／expiry 同一。
5. **图、权限与容量。** 原 manifest、新工作流 manifest 与首次任务派生 manifest 的 **17** 个实例逐项比较：路径、parent、kind、依赖边、输入输出、levels、role、review_requirement、permissions、各层 limits／concurrency scope 均保持；只有明确允许的根版本／资源变化。逐层使用量未超过原上限，未见权限扩张。
6. **旧任务与拒绝。** 原 HTTP 第 26／37 项分别为两个 published 任务；第 31 项拒绝旧选择，第 32 项为 `not_recorded`，实际执行目录无 `stale-selection`。原恢复 CLI 返回与首次创建相同的 intent；驱动在更正／回退后对全部原任务文件作字节快照相等检查。本 reviewer 另外把两任务最初 HTTP preview 中各七份完整文件按原 writer 序列化，逐字比较当前执行目录，全部相同。原 v11 与 CLI `admission_envelope` 保持。新任务明确冻结恢复记忆 revision 4／回退 Skill head revision 3。
7. **失败边界与手册。** 直接核 r1 就绪探测失败、r2 HTTP 422 字段映射失败、r3 JSON 转义比较失败及 r3→r4 的实际差异，没有把早期片段拼成最终通过。手册九处本地链接／锚点可达，CLI 选项与原 parser、记忆保存／期限／恢复及 frozen context owner 一致；开头过时状态已改为明确的初始记录。

## R1 修后安装、页面与自身模板补核

- 最终两产品：`src/ergora/web.py` 为 52,701B／`97ad76e51f82f2d6c27509279ba3e2b2b835d21dea8a372592b853dd7a30a6f3`；`src/ergora/data/console/tasks.js` 为 85,707B／`a3cb1fbd25f557048bf81fda8d3132fa71acda2bd2eb879d451f1e875331c25a`。
- 独立重算最终当前源＝构建快照＝wheel＝非 editable 安装 **604** 产品，wheel **612** 条／安装 **617** 条 RECORD 和 **283** 参考摘要全部正确。最终 wheel SHA 为 `f3d942331a3ac340e9264ae5670b4cd9a83a674cfb475fa409269a67d96fbb1b`。原 web suite 的真实回执为 **9 passed／12.06 秒**，supervised 进程 exit0。
- 直接读被动观察器 `service-r1.py`，只记录原 ASGI 请求／回复，无故障或内容适配。检查时 **20** 组原 HTTP bytes／SHA 全部相同；`browser-r2.json` 的 **15** 检查／**6** 完整样本与原服务响应逐 JSON 完全相同、pageerror 0。两任务 API 的新 `selected_context.selection` 均等于其原 envelope，分别保留 memory2／head2 与 memory4／head3；与当前活动资料明确区分。三 input 与精确工作流读回正确。两张 1440px 截图已直接查看，来源区完整展开、既有布局可读；未把它扩大为本片全宽度矩阵。
- 原自身模板 `self-review-r1.py` 用最终安装件的原 structure-review 入口，以有理由的授权 Codex 回退执行 **33.887052 秒／approve**。从实际 task.txt 按 packet 字节长度重新取回九份 **228,623B** 完整文件，逐件 SHA 同一；当前四份产品源码相同，prompt＝实际 stdin，三祖先资源全部在场；原 result SHA 与 `a7572bdbb8fcb3ea8370416ab567c6cdd0c3580d07e8c97f3e47e93ae634f1d8` 相同。该模型因工具范围只能读 inline 材料，原回复明确保留其限制；本报告的直接文件核查独立完成。

## 剩余验收与限制

原 audit-r1 因误用不存在的 `handoff.read` 退出，失败原件保留，未计为完整通过；直接读修后 audit-r2 驱动／原 JSON／stdout／空 stderr，其 source 核验复用现有 `handoff.verify`。最终补核如下：

- 四个最终 CLI command 都绑定最终安装 Python，以 `-I -m ergora` 调用，exit0、空 stderr，stdout 摘要与 audit 相同。两个 task show 与实际 HTTP 去掉新增字段后的完整响应逐项相同；新增 `selected_context` 与本 reviewer 从原 envelope 的 base64 `selection.json` 离线解码所得完整对象相同。记忆 catalog 与 Skill list 分别等于明确恢复的 memory revision 4、明确回退的 head revision 3。没有重新选取活动资料补写旧合同。
- 两任务 **14** 个文件与原 HTTP preview 的完整 writer 字节已由本 reviewer 独立逐件比较；原 source.zip、17 实例图、七叶资料及 Skill 附件仍与前述原件相同。原 r4 全旅程与最终包读取补证明确分列，没有把原 r4 记成修后整条重跑。
- 直接重读公开 `raw_evidence.references` 的 **214** 个唯一原件，共 **7,928,410B**，bytes／SHA256 全部相同；以 sort_keys／compact JSON 规范化后的固定数组指纹为 **`1e3cdded31248b39867682ba3963aee949fec5ff7a84c1ade34a8e8929784b74`**。未修改或重生该数组。早期失败、浏览器红例、两安装身份及最终绿例分别保留。
- `cleanup-r1.json` 对应五份 service 原元数据，PID／端口逐项一致；本 reviewer 再从当前 `/proc` 核实五服务 PID 不存在、五端口无 LISTEN，观察到的浏览器 daemon `2673157`／`2676116` 也不存在。只覆盖这些自有观察进程。
- 完整当前 tracked `git diff --check` 为 exit0；手册九链接／锚点已核，新文档与最终身份分列正确。计划／交付／索引中的最终独立 `pending` 是等待本报告的状态，实施者可据本结论更新；发布门禁保留。

七个叶仅实际准备输入，未在本片执行模型调用。合成来源和 scorer 不证明真实训练、工程质量、GPU／性能或外部 ReMe／Forge 可用性。本片只做桌面读取，不继承前片全宽度／迟到矩阵。前继固定 `3a56508` 自己的 CI `43580979082` 由其原 reviewer 记录八 job／30 必要步骤及两轴终核闭合；不把它当成本片 CI。

本地审查出口时普通发布、精确远端 ref 与必要 CI 尚待；固定发布后的补核见下节，自己的 CI 仍另验。接续工作仍为 F9d 完整实验旅程和 G1 安装／升级回退／跨机重建，真实外部能力按各自原准入条件执行。

## 固定发布补核

2026-11-14，原 reviewer 沿本报告只读补核 `8d739c298668ab9f7d88fdaa205a21f304d9586c`：**需求轴 approve，可维护性轴 approve，开放 finding 0／0，R1 保持关闭。** 未联网、重跑、安装、修改产品／原件数组、提交或推送。

- 固定提交唯一父为原完整基线 `3a56508791a33871016acff4a7cad268aaf0be50`。直接读取 Git 对象的 **15** 个变更 blob，与 `static-final-r1.json` 中每项 bytes／SHA256 完全相同；文件集合也完全相同。固定原最终本地报告为 **11,985B／`17ab5c6f31122c2e4151c587884d39081a087f2fe5b8a6e153ff983250faac45`**；本节是发布后的补核，不把它当成固定报告当时已有的内容。原完整 staged diff check、Python AST 与 JS 语法的记录均为 exit0，文档链接检查通过；本次读取原静态结果，未重跑。
- 从固定 Git tree 逐件读取全部 **604** 产品文件，bytes 全等于最终 wheel、非 editable 安装、构建快照及当前源文件。因此该固定候选对应原最终安装／web／页面及 CLI 补证的产品；仍不把原基线 r4 完整组合旅程改写成修后整条运行。
- 固定提交内 `raw_evidence.references` 与发布后数组逐项相同，仍为 **214** 条，规范数组指纹仍为 **`1e3cdded31248b39867682ba3963aee949fec5ff7a84c1ade34a8e8929784b74`**；214 份原件重新读回的 bytes／SHA256 全部相同。发布后单列 `publication_evidence` 的 **五** 份调用／回执也逐件重算相同，未替换本地证据。
- 直接阅读 `publish-r1.py`、commit／push／ref 原回执：commit exit0；唯一普通 push argv 为 `git push origin 8d739c298668ab9f7d88fdaa205a21f304d9586c:refs/heads/refactor/architecture-foundations`，无 force、`+` refspec、main 或 merge 操作，exit0。保存的 `git ls-remote` 在 **2026-11-14T09:58:46.629382+00:00** 返回同一完整 SHA 与分支，本机 remote-tracking ref 亦同一。远端结论绑定保存回执的观察时刻，本次未重新联网读取。
- 固定提交已包含前继原 reviewer 的自身 CI 终态两轴 approve／开放 0／0，以及完整前继候选 `3a56508791a33871016acff4a7cad268aaf0be50` 的 run **43580979082**、八 job／30 必要步骤成功。核前继终态元数据和单列 **52** 条 CI 引用，bytes／SHA 全部同一；原 `ci-terminal-r1.json` 时刻 **09:51:20.520160 UTC** 早于新 commit **09:58:39**／push **09:58:45**，原 reviewer 终态结论已在新固定 tree 内。前继门禁先于新发布闭合，没有借其结果通过本片自己的 CI。
- 当前发布后仅有本片计划／交付／证据元数据的四份记账差异，无后继产品变化；本报告追加补核后另形成 reviewer 记账差异。

固定发布补核当时本片自己的必要 CI 仍 pending，仅闭合本地与固定发布身份门禁；其后提供的自身 CI 终态原件见下节。不合 main，不强推。

## 自身 CI 终态补核

2026-11-14，原 reviewer 仅按本片原合同，对固定完整候选 **`8d739c298668ab9f7d88fdaa205a21f304d9586c`**、自己的 **run `43583053417`** 独立补核：**需求轴 approve，可维护性轴 approve，开放 finding 0／0；R1 保持关闭。** 本轮只读固定 Git 对象、必要原件及交付范围，并更新本报告；未联网、重跑、安装、修改产品、提交或推送。

- 直接解析原 `ci-list-html-r1/page.html` 的官方 embedded JSON：唯一关联该完整 commit 链接、run、`refactor/architecture-foundations` 分支及 `.github/workflows/portability.yml`，run number 为 205。原列表的 In progress 是发现身份时的历史观察，未覆盖它来伪装终态。
- `ci-run-html-r5/page.html` 的实际 Status 卡片为 **Success**，原 commit anchor 为该完整 SHA。抓取回执为 HTTP200、原 URL 与 final URL 同为官方该 run 路径，时间 **2026-11-14T10:19:06.245947+00:00**，正文 **213,278B／`2df53b476acbf54b90291e9b99ef184045266441276916ff5d00c1362fed3b82`**；bytes／SHA256 均独立重算同一。
- 从固定 tree 读取 workflow 和 `scripts/ci/linux-groups.json`：预期为 plan、六个 Linux 分组及 Windows all，共 **八** job。原 `ci-job-batch-r1/body.json` 的 `totalCount=8`、`hasMore=false`，八个 ID 唯一、名称和各自 run/job 路径完全一致；与原 metadata 一一对应，metadata 所绑定的 run1 原页面亦含该完整 commit。早期 batch 的在途状态只用于身份发现，终态另读下表实际 job HTML。

|Job|固定 job ID|终态原件|必要步骤成功数|Complete job UTC|
|---|---:|---|---:|---|
|plan|132411702159|`ci-job-132411702159-html-r1`|1|09:58:52|
|Linux group 0|132411728936|`ci-job-132411728936-html-r2`|4|10:03:35|
|Linux group 1|132411728959|`ci-job-132411728959-html-r2`|4|10:04:23|
|Linux group 2|132411728914|`ci-job-132411728914-html-r1`|4|10:02:58|
|Linux group 3|132411728902|`ci-job-132411728902-html-r1`|4|10:01:26|
|Linux group 4|132411728916|`ci-job-132411728916-html-r1`|4|10:01:59|
|Linux group 5|132411728930|`ci-job-132411728930-html-r2`|4|10:05:00|
|Windows all|132411728947|`ci-job-132411728947-html-r4`|5|10:16:59|

- 用独立 HTML 解析器逐个读取原 `check-steps`／`check-step`：八个 job 均为 completed，且各有唯一成功的 `Complete job`。**30 个必要步骤全部 success、带完成时间及 `data-job-completed`**：plan 的 `Read explicit test groups`，七个执行 job 各自的 wheel 构建安装、参考身份、原回归、观察上传，以及 Windows 的 `Windows PowerShell 5.1 installer and upgrade`。
- 全部 **76** 个 success 步骤的日志 URL 均精确包含该完整 SHA、对应 job ID 与各自 `data-number`；开始不晚于完成，完成不晚于原抓取时刻。另有 **六** 个 skipped，恰为固定 workflow 在 Linux 排除的 Windows 安装步骤，没有其他失败或跳过。独立重建的八 job／30 必要步骤与 `ci-terminal-r1.json` 完整投影逐项相同，原 terminal SHA256 为 **`2de6c5bc39dbfe23d4d393a8d76ede2dace18f73af1388195a77d97766528642`**。
- 直接阅读发现、抓取、metadata 和 parser 脚本，未执行它们。新单列 **52** 条 CI 引用均为唯一不同路径，与原 **214** 及发布 **五** 件不交叉，所有 bytes／SHA256 重新读取相同；实际终态 run／job／batch 回执的 URL、HTTP200、长度和正文摘要也均核实。证据是官方 UI HTML／UI job batch，未扩大为已读取步骤日志正文、REST 响应或下载产物归档。
- 固定 **15** 个 Git blob 仍与原静态清单逐件同一，唯一父保持原基线；原214数组与固定 Git 逐项同一，指纹仍为 `1e3cdded31248b39867682ba3963aee949fec5ff7a84c1ade34a8e8929784b74`，214 原件及发布五件再次重算全部相同。原最终604产品与本地／固定发布结论保持，后继工作树不属于本次 CI 身份。
- 总计划／本片计划和交付明确把这次 CI 归于固定 `8d739c2`，将原 r4 合成组合、新包读取与自身 CI 分列；等待本报告的独立终核状态可据本结论更新。F9d1 有自己的合同及 reviewer，本次不对其工作、GPU／训练或质量作结论。

**该固定 F10d7 候选的最终本地、普通固定发布和自身必要 CI 三个门禁均已闭合，两轴 approve、开放 finding 0／0。** 仅覆盖本报告原合同与实际证据范围；七叶仍只是准备输入，合成 scorer 仍只证明合同，F9d1／G1 和真实外部能力继续分别验收。不合 main，不强推。
