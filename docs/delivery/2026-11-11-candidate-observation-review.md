# F7c-C3a 候选远端只读核对：独立审查

评审者：fresh-context Codex reviewer `f7c_candidate_observation_review`，2026-11-11。先读原始要求、[本片规格](../plans/2026-11-11-candidate-observation.md)与实际差异，再读作者交付叙述。采用 `code-review` 的 Spec／Standards 两轴、`maintainable-project-delivery` 独立 brief 及 `codebase-design` 的 Interface／所有权判据。本轮仅只读检查；唯一写入为本报告，没有运行产品、模型、套件、安装、网络、提交或推送。

## 审查身份与范围

固定基线和当时 HEAD 均为 **`93b538fd474120fa05574dcdcf376b7666502c8d`**，实际候选为未提交工作树，不能用空的 baseline→HEAD diff 表示。已核 `review-r1/manifest.json` **SHA256 `aec0fd91c00dc064e1079ac12b985255ea956d4cea080f3a40992bcf842a48b5`** 的全部 **27 个文件**：封存副本的大小／SHA 均符合清单，初次检查时当前字节逐一相等。`tracked.diff` SHA256 **`daf403a0c607e8a558f25a1f96debf34f58d523776d2d622a6791cfe7c9d1e8a`**，等于实际基线→工作树的 binary diff；新文件另按清单原字节读取。

范围包含八个产品／配置文件、三个测试文件、使用与架构文档、两份新研究及 C2a 的后续记账。原报告追加不递归审查；C2a 的 Git／CI 和后片研究均没有被用来替代本片验收。另追到 `reference._task_operation`、`_Creation.published`、`_Submission.submitted`、快照绑定、backend 局部 registry、HTTP 同源保护及原 Git 清理调用。独立重算 reference manifest 的 **283 件原字节**，零不符；manifest 与基线相同，冻结源码、依赖及 CI 定义没有本片差异。

## Spec

**首轮结论：request-changes，开放 2 项 P2。**

### SP1／P2：本地导出 ref 缺失被报告成已观察到的不相等

- 位置：`src/ergora/reference_task_export.py:196`，由 `src/ergora/issues.py:79` 原样投影；现有删除旅程在 `tests/test_task_export.py:361`。
- 规格：第 7 行列出三个独立比较，第 9 行明确“未见或不可见的ref令相应比较为null”。
- 触发：原任务、commit 与 export 收据仍完整，但人工删除原本地导出 ref。`branch_sha` 返回 `None`，随后 `None == candidate_sha` 得到 `False`；顶层 `local_export_ref_matches_candidate` 也变为 `false`。
- 后果：不可观察和实际观察到另一 OID 混为一谈，三个比较的三态合同不一致。原测试只核 `current_branch_sha is None`，因此正常通过也没有覆盖这一错误。
- 最小修正：缺失时返回 `None`，有 OID 时再比较。在现有删除旅程补核该值，源码确认顶层继续按此值投影即可，不新增重复旅程。作者已接受，修正与复核待核。

### SP2／P2：只读对象检查仍可触发 partial clone 的隐式 fetch

- 位置：`src/ergora/reference_task_export.py:190` 调 `cat-file -t`，复用第 111–118 行的 Git 进程环境。
- 规格：第 11 行要求“本片只读……无fetch／push／ref写入”，研究的本地投影合同也要求原对象缺失时明确失败。
- 触发：已注册仓库配置 promisor remote，原 candidate／base 对象后来不在本地。当前注册只要求 canonical Git root 与原基线，不排除 partial clone；Git 对缺失对象的 `cat-file` 可以自动向 promisor remote 取回。原 `git_process` 删除全部 `GIT_*` 后未重设禁止 lazy fetch，调用者原有的 `GIT_NO_LAZY_FETCH` 也会丢失。
- 后果：观察路径可能发出额外 Git 请求并写 `.git/objects`；只核显式 argv 没有 `fetch` 和普通完整仓库前后相等，不能证明这个只读保证。
- 最小修正：在原 Git owner 内，对本地观察强制禁止 lazy fetch；保留原显式 export-fetch。对象缺失应可见失败，并以本地 promisor／缺对象旅程核没有取对象和对象库写入。该项为可达源码与 Git partial-clone 语义推导；评审没有创建复现仓库或执行 Git 写入，作者复现／处置与回归仍待。

其余所审调用满足原来源、已发布 v7 creation、完整 snapshot、原 run／candidate／export 绑定；head 固定原 export，base 显式输入。开始／返回前 revision 检查、精确 native 字段与路径、全长 SHA、GH 单数 `git/ref`、GL 数字 project ID 和完整 branch 编码均可达。仓库输出按白名单生成；只有 ref 的实际 404 转为 `not_found_or_not_visible`，认证、限流、redirect、坏目标与原有完整响应预算失败不被改成相等或缺失。没有创建／恢复远端 ref、tracker 写入、自动重试、Temporal 查询／信号或 claim 释放路径；SP2 是上述显式路径之外必须补住的 Git 行为。

## Standards

**所审范围无新增 Standards finding。** 没有以这项结论抵消两项 Spec 问题。

- `tasks.exported_source_candidate` 有 `issues` 与 `issue_writebacks` 两个真实生产文件消费者，迁移前后持久 task／source 字段、`identity` 算法及旧 intent 形状不变。v7、快照、原 export 与 run／candidate guards 分别保护持久身份，没有另造候选账本。
- `remote_candidate` 由 CLI／HTTP 共用；`inspect_export` 是通往原 export owner 的既有 reference Interface 扩展。`_Export.inspect` 留在 Git／原收据 owner，分支校验从 `record` 抽出后又由显式 base 校验消费，不需要通用远程操作层。
- `IssueBackend.repository_refs` 有 GH／GL 两个真实 Adapter，配置映射仍在本族；上层无 provider 分派。各 `_branch` 虽各有一个本族调用者，拥有不同路径、URL 编码和原生字段，是必要的私有协议算法。`_document` 实际由两 Adapter 的 repo／ref 路径共用；类型化 `_HTTPStatusError` 仅为区分实际 404，保留既有 `ValueError` 外部合同，没有按错误文本猜状态或引入新 SDK。
- 新 guards 分别位于外部响应、持久来源／export 身份、当前 revision 和原 Git 对象／ref owner；未见为了假想未来消费者而新增的配置、ABC、兜底或参数校验。原候选绑定的既有重复读取仍用于核独立原件，未复制到 CLI／HTTP。
- `configure_remote` 被新观察 suite 与原生 v7→fresh CLI 旅程两个测试文件消费。通用观察 fixture 明确控制 task ports，State／HTTP 为真实；原 export 与来源衔接另保留真实 Git。三类检查分别覆盖协议／传输、真实只读 owner、端到端新 CLI 接入，未发现可直接删去的重复 case。现有 SP1 旅程补断言和 SP2 必要故障检查应针对静默错误，不扩大成镜像测试套件。

## 实际证据与验收缺口

已读 `source-r1` 的 inputs、result、stdout／stderr，独立核 stdout 摘要与记录相同：**34 passed／59.16 秒**，驱动 **61.3246 秒**。命令显式用当前源码 `PYTHONPATH` 和保留的 C2a 环境，不能称本片安装验收。它覆盖新观察 suite、真实本地 export inspect、原 v7 发布／提交／Git export→fresh CLI 及架构；Temporal SDK／result 受控，通用观察的 task ports 受控，没有真实托管平台或六阶段模型调用。其后两项可读性文本变更与冻结清单身份分开保留，不称该次结果已核最终所有字节。

观察的三个 provider 请求是顺序 GET，没有循环／重试；复用原有每响应 1 MiB 和 socket I/O 20 秒限制。手册已明确总墙钟并非 20 秒，现有 59.16 秒套件时间也不是两家平台的延迟基准；未见由现有测量支持的性能承诺或需新增通用性能框架的证据。

首轮审查时，新非 editable 包／两 RECORD、受影响安装回归、修正后实际自身模板与完整原件、同片修正复核、普通提交／推送及本提交自己的精确 Ref／双 OS 必要 CI 仍待。它们是尚未完成的验收证据，不据此另造产品缺陷。两份新研究明确区分官方静态证据、推导、后片建议与未验平台；GitLab 标签仍 unsupported，PR／MR／远端发布没有提前接入。本报告不据 pending 状态关闭本片或整个 F7。

首轮两轴计数：**Spec 开放 2（最高 P2）；Standards 开放 0。** 修正候选与实际验收原件补齐后，可由同一评审者在本报告续核。

## 同片修正复核 R2

本轮继续由原独立评审者只读复核，未运行模型、产品、测试、安装或网络。先读原需求和 r1→r2 实际差异，再核交付叙述。基线／HEAD 仍为 `93b538fd474120fa05574dcdcf376b7666502c8d`。新 **27 文件**清单 SHA256 为 **`ce3c938df5d82fe13ed36ae162a00f30ce4f002ad69cc128d6086faa973ca756`**，全部封存大小／SHA 正确，初次核对时全部等于当前字节；`tracked.diff` SHA256 **`11a2fa413eff76e72fa5530ed0cc5f6fa90eaec1c3dccdbfb2890a0dd4981ac7`**，等于实际 tracked diff。本报告按授权排除在清单外。

### Spec：SP1、SP2 关闭，开放 0

**SP1 关闭。** 原 owner 第 201 行明确以 `current is None` 返回 `None`，有 OID 时才比较；`issues` 的顶层投影仍直接消费这一值。原真实 Git 删除旅程现同时核 SHA 和比较均为 `None`，移位旅程仍核 `False`，原 export 收据与 claim 保持。修正没有改变远端 404、原 base 或候选绑定。

**SP2 关闭。** `git_process` 第 115–116 行在环境过滤之后，仅为 `operation == 'inspect'` 强制设置 `GIT_NO_LAZY_FETCH=1`；`inspect` 第 191–193 行先查询实际固定 Git 的版本，在对象读取前拒绝未知或低于 2.43 的版本。这是对旧 Git 可能静默忽略开关的明确支持范围，已写入计划和手册；没有把新限制加到旧显式 export-fetch。前置 `prepare/load/validate_branch` 只有原收据读取、根与分支格式查询，不存在先于该保护的对象读取。

已读本地 promisor 诊断脚本、结果、两个实际回归的红例及安装回归原件：

|原件范围|实际结果|可支持的结论|
|---|---|---|
|原 owner、调用者预设 flag、同 hooks／protocol flags 的 default control|缺对象后 `exit=0/commit`，对象文件 `0→4`|原问题可达；调用者变量不能越过旧过滤|
|同 flags 显式禁 lazy fetch、移除两项 promisor 配置的 control|`exit=128`，对象文件 `0→0`|禁补取与缺对象失败可区分；只去掉 promisor 而保留 filter 的早期失败 control 不冒称成功|
|修正 owner 探针与 r2 安装后的真实任务回归|缺对象可见失败，Git／任务文件、claim 与 SDK 调用保持|修正覆盖实际 owner 路径，没有以 argv 无 `fetch` 代替副作用检查|

早期 `direct-disabled-r1` 缺相同 protocol 条件，不作为可比对照。`regression-red-r1` 展开 venv 符号链接后缺 pytest，没有运行产品；实际红例是保留 r1 安装包的 `regression-red-r2`：**2 failed／23.09 秒**，分别在 `False is None` 和 Git 文件不写断言处失败。作者后补实证支持原 SP2 推导，首轮记录继续保留。所有 remote 均为本地 bare fixture，没有真实平台或外部 Git 网络。

### Standards：开放 0

本轮生产变化只有原 `reference_task_export` owner 的三态、inspect 专属环境和版本准入；没有新文件、私有 helper、ABC、上层 provider 分派、依赖或账本。一次 `--version` 的 guard 保护已实证的外部 Git 行为，并在首次对象读取前失败，不是无关参数校验。旧显式导出与原 ID 未知恢复的受影响检查继续通过。

SP1 在原删除旅程补断言；SP2 只有一个真实缺对象回归。后者将文件不写断言放在错误文案断言之前，能识别“命令成功但偷偷取对象”的静默错误，也同时保护调用者 flag 被过滤的情形。手工捕获 `ValueError` 是为了在意外成功时仍先核副作用；没有为错误文案本身新增独立 case。未发现新的结构、复用或冗余测试 finding。

### 安装身份、实际耗时与保留范围

独立从 r1／r2 两个 wheel 和两份 installed RECORD 重新读字节，逐行核大小／SHA：各 **446 个包文件、wheel RECORD 451 行、installed RECORD 456 行、283 冻结文件**均通过。r1 wheel SHA **`247bea7cf47e19c7af1ce07ab6b4666482c498bd7cfa0e30c3ddab0fde661a59`**，其八份产品／配置文件等于原 r1 审查清单；r2 wheel SHA **`a999eb34bc320e6d2ccaf68de58847574d39b5121e964d19e917bd4de38e55f8`**，全部包文件等于当前源码与安装内容。两个 wheel 的包文件变化恰为 `ergora/reference_task_export.py`，没有将 r1 检查误标为修正后全套。新环境由 wheel 普通安装；`python -I` 的驱动去掉 `PYTHONPATH`，不是 editable 或借源码覆盖安装内容。

已核实际 argv、stdout／stderr 与摘要：r1 八 suite **196 passed／1 skipped／625.86 秒**，驱动 **641.60 秒**；r2 受影响检查 **49 passed／1 failed／250.68 秒**，驱动 **252.68 秒**。唯一失败发生在对象不写断言已通过之后，内部期待 `cat-file failed` 而实际 Interface 诊断为 `fatal: git cat-file...`；仅将测试匹配改为 `git cat-file` 后，同一 r2 包的原回归 **1 passed／9.17 秒**，驱动 **9.8793 秒**。补跑 inputs 的测试大小／SHA 等于 r2 冻结字节，reference verify 退出 0。没有一份新的“50 项全通过”运行，也没有抹去原失败。真实本地 inspect 单项 r1 为 10.38 秒、r2 为 10.26 秒，这不是足以推断性能变化的基准；新三次远端 GET 仍没有真实平台延迟结论。

候选发布研究的 `requests.jsonl` 与 **12 份完整 body**现已独立重算大小／SHA，均一致：11 次 200、1 次未跟随 301；定向读回精确 GH ref、GL branch 编码及敏感 repo 字段原文。没有重复 GET。GitLab 标签研究其他本轮 body 未持久保留，不能冒称重核全部源码来源；其生成参考与本次留存同 SHA 内容相符，且产品严格能力继续 unsupported。C2a 的新 CI／终结记账按原评审自己的范围保留，没有移植到 C3a。

**修正复核结论：SP1／SP2 均关闭；Spec／Standards 开放 0／0，无新增 finding。** 本结论覆盖 r2 封存的修正与上述实际安装证据。实际自身模板的最终原回执／完整读取 audit、最终完整候选／状态与静态原件、普通提交／推送及本提交自己的精确远端／必要 CI 仍待后续终核；尚不据此标记本片完整本地出口或精确交付完成。

## 实际自身新增 SP3：独立判断

上述 R2 修正复核之后，作者补入实际自身模板原件。已读 `self-review-r1.json`、`review.md` 和 `original-result.json`：该 Codex 调用记录 **306.0272 秒**、进程成功而业务意见为 **request-changes**，提出 SP3。其附件／五 scope 完整读取及进程清理的全链 audit 此时仍待，不能仅按模型自述确认完整性。

**SP3／P2：replace refs 可使原对象缺失被报告为已验证。** 位置为冻结 r2 的 `src/ergora/reference_task_export.py:195–202`，环境在第 111–119 行。规格第 7 行要求核原 candidate／base commit，本实现还明确输出 `objects_verified_as_commits: true`。独立重新检查源码后判断此项成立：`cat-file -t <原OID>` 默认尊重 `refs/replace`，r2 只禁 lazy fetch，没有禁止对象替换。原 export 后添加 `refs/replace/<candidate>` 指向另一现存 commit，并使原对象缺失时，类型检查仍可读取 replacement 而返回 `commit`。此时结论只验证了替换对象，不能证明原 candidate／base 对象仍在；当前 ref OID 和原收据相等也不能补上该事实。

最小修正是在 inspect 专属 Git 环境过滤后同时设置 `GIT_NO_REPLACE_OBJECTS=1`，保留旧 export 行为。原无 replacement 的 promisor 回归必须继续存在；可在同一旅程扩一个 replacement 情形，分别保护隐式补取和原对象身份这两个不同静默错误。只把 replacement 加进原 case 会可能遮住 lazy-fetch 触发，不能据此丢掉 SP2 保护。

该 finding 来自实际自身模板，本轮独立源码判断支持其合同依据；作者正在用保留 r2 安装包做实际红例，评审没有自行执行复现。目前 **Spec 开放 1（SP3／P2）；Standards 开放 0；SP1／SP2 保持关闭**。前文 R2 的 0／0 是当时修正范围的记录，不覆盖本次后来新增发现，完整本地出口继续待核。

## 最终完整本地复核 R3

本轮由同一独立评审者继续，只读源码与保留原件；未运行产品、模型、测试、安装、网络或提交。先核 r2→r3 源码／测试与原合同，再核最终公开文档、实际自身读取链和验收投影；未执行会导入产品并写审计的作者 `audit-self-review.py`，以下摘要／分页结论由独立标准库只读代码重算。

基线／HEAD 仍为 **`93b538fd474120fa05574dcdcf376b7666502c8d`**。最终 `review-r3/manifest.json` SHA256 **`6d0b51e8c6f7af095afa99c5a4dcc549a63767a7ffbc964eeaafb5092cdc46e4`**，**29 件**封存副本的大小／SHA 全符，追加本节前全部等于当前文件；`tracked.diff` SHA256 **`9a0087ef6f876843e5e11604ec8df592fbc06ef26fe9b30e25f4b31790bb2cc0`**，仍等于实际基线→工作树 binary diff。新增两件为本报告与[结构化验收投影](evidence/2026-11-11-candidate-observation-acceptance.json)。本报告自身追加不递归审查；下一片 `docs/research/2026-11-11-existing-review-association.md`、`docs/plans/2026-11-11-existing-review-association.md` 均未列入这 29 件，也不属于本次交付判断。

### Spec：SP3 关闭，开放 0

**SP3 关闭。** r2→r3 唯一生产变化位于原 `_Export.git_process`：过滤继承的 `GIT_*` 后，`operation == 'inspect'` 同时强制 `GIT_NO_LAZY_FETCH=1` 和 `GIT_NO_REPLACE_OBJECTS=1`。因此候选和 base 的两次 `cat-file -t <原OID>` 都按原对象读取；Git 版本 guard 仍先于对象读取。没有将这些 inspect 选项加入旧显式 export，也没有改变三态、原收据或 claim。

独立读取并重算 SP3 实际红例 stdout SHA **`6694eabb277e205e8efe78cc5c22c4f34e34c034896ede08c2e0fb36255f623c`**，命令明确使用未改的 r2 安装解释器及 `[True]` 原任务回归：**1 failed／8.79 秒**，驱动 **9.5327 秒**。文件／claim／SDK 不写断言已过，失败在 `error is not None`，即原 inspect 错误成功；不是安装或测试驱动失败。该运行的测试大小／SHA 等于最终冻结文件。

两组最小探针及其脚本也已读：r2 原 owner 在原对象缺失、replacement 存在时返回 `commit`；同 flags 禁 replacement、或只删除 replacement ref 均退出 128。修正后的 r3 owner 与两个 control 均退出 128。每次对象集合 **2→2**，原 loose 对象始终缺失；本地 bare promisor fixture 没有外部 Git 网络。此证据与源码相符，能区分原对象身份错误和隐式补取。

回归沿原缺对象旅程参数化 **False／True**；无 replacement 的 case 继续保护 SP2，有 replacement 的 case 保护 SP3，文件不写断言继续先于错误断言。没有用 replacement case 替换原 lazy-fetch case。SP1／SP2 的修正及既有事实在最终候选中保持。

### Standards：开放 0

本轮未见新增 Standards finding。修正仍由原 Git owner 的 inspect 专属环境拥有，没有增加生产文件、helper、ABC、provider 分派、配置、依赖、账本、重试或恢复路径。两个参数值分别捕获已实证的不同静默错误，属于一个必要真实旅程的最小扩展；不存在据现有证据可直接删除的重复 suite。前文对共享 `tasks` Interface、两个生产消费者、GH／GL Adapter、本族 HTTP 与 CLI／HTTP 共用观察用例的判断继续成立。

### r3 安装身份与受影响证据

独立重新读取 r3 wheel 和 installed RECORD，逐行核原字节的大小／SHA：**446 个包文件、wheel RECORD 451 行、installed RECORD 456 行、283 件 reference 冻结文件**全部通过；446 件逐一等于当前源码及普通安装内容。wheel SHA **`7a346be467c7c5bd03035aae7331f9947be7c4ddb3a58dc3de2f534e1e4364de`**。r2→r3 包文件集合相同，差异恰为 `ergora/reference_task_export.py`。标准隔离构建 **14.5843 秒**、新非 editable 安装 **25.7478 秒**，均有退出 0 的原 argv／stdout／stderr；没有以源码覆盖安装内容。

已重算 r3 两份 stdout 摘要并核空 stderr／退出 0。受影响运行 **18 passed／82.43 秒**，驱动 **84.3279 秒**，stdout SHA **`2a3b2b19bfb07698d32b2327bc676c329d38f2ea96c448862ea5ec7ab592b019`**；覆盖有／无 replacement 的缺 promisor 对象、当前本地 ref 移位／删除三态、原显式 export、真实原生 v7 export→fresh CLI 和架构。reference verify **0.2671 秒**，stdout SHA **`0bb0be3cd8c131f05db9f9235276a2a844d70f3e7520507748f01d01c9f42a40`**。原 r1 的 196／1、r2 的 49／1 与测试文案补验继续按前文候选及范围保留，没有新的 196 项或 50 项全绿运行。

### 两轮实际自身：原件链独立重建

两轮均核实际输入树与 prepared 树完全相同，重新按文件 SHA／执行位计算 input 与 manifest digest；assets 索引、每个 definition／Skill 的树摘要、完整 composition／preview、task、prompt 与原 stdin／protocol prompt 相符。内置结构模板的原 instructions／Skill 字节保持，只允许记录中的局部 revision、候选证据 resource、材料上限及精确 agent ref 变化；在线定义索引确已移走，输入携带冻结 assets。admission 的 binding／policy 等于实际 run，`task-mcp` 模式及 `formal_execution_authorized: false` 保持。

|实际运行|完整附件与读取|原结果／范围|
|---|---|---|
|`4eec0d1776b94def80af7515f796caa5`，1.0.99|13 件／318,545 字节，附件 SHA `dc67e7a6f8006f8a2f653f72cf3aa7cbaa9d8a21a0194fd9b075c7f5fd357bbb`；candidate 连续 14 页至 null，另有一次第一页重复|**306.0272 秒／request-changes**，原 SP3；不覆盖后来最终公开文档与修正|
|`1026f3500a504828b165b05b4dc4b70e`，1.0.100|8 件／114,634 字节，附件 SHA `f9a083a02f96b0d9094727cada3ed42b88412240d7ec5f6b3c95a0a8b444795a`；candidate 连续 6 页至 null|**164.7909 秒／approve**，仅 SP3 聚焦复核；没有重跑原 13 件或独立核安装与最终文档|

两轮 native 事件各完整 list 五 scope；逐次核 read 参数、URI、offset、实际 UTF-8 字节、总大小、SHA 与 next_offset，均连续读到 null。五 scope 恰为祖先 workflow instructions、reviewer instructions、两个 Skill 和 candidate 全文，均等于实际冻结 assets；附件内各 `FILE … (complete)` 的完整 body 又分别符合 13／8 件索引。没有把编码尝试、仅列目录或模型自述计为全文读取。native receipt／scope 摘要与事件调用逐次对应，失败 MCP 调用 0。

独立重算的身份为：

|原件|首审|聚焦复核|
|---|---|---|
|input digest|`098e2f983c6855b06b1624a2f4f7d855b48566b884357470cb02e389510b3d4c`|`9a881603c087daaebbdb838ba5196f5be046e7346d0b01843c942d729a3ff392`|
|manifest digest|`01514411558e94fa677f6b49ca6fdd07d25849f14a046f82cc4ec783533ae63a`|`56b4337a5fe6147f54b9cd12e63fa25015f691a2eee9171fe17b4f899a142ac3`|
|prompt SHA|`d020ebacd527df7174bbcd9de652fceec45e17a0122cc6d9a1bda51eee782da5`|`1c3f8e3d7c20557588a44b6f590da25e2e3ddaf3e0c1d3d9033288e9429a6f28`|
|native stream SHA|`bdc0f3dcb60448b6ce679da033aae98fc1efe1196b0ba0783addf7b457fea02a`|`789ede87eb734be3da37c9aa4a98dbeb3dade8bb5e3bc9dd7849ce2b08d29bb9`|
|原 result SHA|`b765b29c1c8dc50ae867f4f06a2c34f954e3238c8fd30690ed5173b5579b85ac`|`a0a2a8f0cddf948ac22e9b80c05f5483c9aaa8c83dc2d9a94d66305ba9a872c7`|

原 result 与保留的 `original-result.json` 字节相同，response 等于各 `review.md`，业务 decision 与进程成功分别登记。两轮为 **Codex／gpt-6.1-sol／high** 的实际回退调用；保留 Claude 上游 400 与用户授权回退的范围，不称不同后端独立成功，也不把字节送达等同模型理解。每轮四个采样所属 PID／starttime 记录无存活，本次只读检查也未见这些相同进程身份仍活着；不据此推断所有未采样短进程。自报 usage 有 native 事件来源，缓存是输入子集，推理另列，不重复累加或推算费用。

### 最终公开文档、静态与本地出口

已核 r2→r3 全部实际文档差异及新验收 JSON。手册和本片计划明确禁止 replacement／lazy fetch，Git>=2.43 的支持范围与三态保持；交付和上层索引区分首审 request-changes、实际 red、r3 定向复验及聚焦 approve，没有以自身意见关闭尚未进行的独立终核。JSON 分开保留 r1／r2／r3、失败、测试文案修正和未验范围；C2a 精确交付记账及 C3b 下一片均未借给 C3a。

作者 `static-r1` 记录 29 件／393 个本地链接、六个当时加载的秘密值、issue 0；文件身份与最终冻结相比只有交付文档后来追加的静态说明不同，其余 28 件相同。本轮独立按最终 29 件重新核 JSON、private home 路径、**393 个本地链接目标全部存在**及 `git diff --check`，均通过。秘密值扫描保留为作者当时的有范围证据，本评审没有读取或转储凭据值；不把它扩大为未知秘密／历史扫描。锚点、外部 URL 与 Mermaid 渲染不在该静态检查范围。本报告追加及据此同步的纯状态记账只需最终最新字节静态检查，不递归重跑模型或原产品 suite。

**最终 Spec／Standards 开放 0／0；SP1、SP2、SP3 均关闭，无新增 finding。完整本地出口通过。** 此结论覆盖最终冻结 29 件、原调用路径、分轮安装／测试原件、实际自身完整读取及本次报告追加。普通提交／推送、精确 Git 对象／远端 Ref 和本片自己的双 OS 必要 CI 仍属 O4 后续精确交付，当前未完成；不能借 C2a CI、模型 approve 或本地出口替代。真实 SaaS／GHES、平台权限及延迟、原生 Windows 正式执行、六阶段全真实运行和成功不同后端独立性仍未由本片证明；F7 及项目整体不因此关闭。

## O4 精确 Git／作者 Ref 原件复核，CI 待终核

已独立核提交 **`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`**，唯一父提交为 **`93b538fd474120fa05574dcdcf376b7666502c8d`**。读取使用禁 lazy fetch／禁 replacement 的本地 Git 原对象；commit 与 blob 均按 Git 对象头／原内容重新计算 SHA1。实际父→子差异恰为 **29 件**，全部是普通 blob／`100644`，大小／SHA256／mode 与 `commit-closure/ready-r1/manifest.json` 及封存副本逐一相符；ready 清单 SHA256 **`f0b220682f1af5237cef3d0bebba78843038085fe1ef3aa0616f27de8a69d3a7`**。提交内报告 blob 保持本地出口快照 SHA **`a52afa14fc30fa91da6ffe65dee9eafdcd1ba337d7c87d03a9614eb505a47516`**，本节后续追加不是该提交的原字节。

完整本地出口之后，除报告外只有六份公开状态文档／验收 JSON 同步结果。已读其逐项差异，正确登记本地出口 0／0、SP1–SP3 关闭及 O4 仍待，没有改产品、测试、依赖或 CI。r3 wheel 的 **446 件包文件**又逐一等于该提交的源码，**283 件 reference 原字节**符合提交内 manifest；wheel METADATA 中 README 的原 UTF-8 body 也逐字等于提交内 README，SHA **`f4740a062d0e78009079ac5c53cd7478846732cfb38b4176b2531a6cc7becef5`**。没有重新安装或运行产品。

作者 `static-r2` 的 29 件大小／SHA 与 ready 全符，记录 **395 个本地链接／六个当时加载的秘密值／issue 0**；独立重核 ready 中 JSON 与 395 个本地目标均通过，秘密值扫描仍按前文作为作者有范围证据。C3b 两份设计不在该提交或 ready 内。此后的下一片工作树变化不属于 C3a 漂移，后续本片判断固定使用提交、ready 与原 r3 安装包。

已读普通 commit、push、Ref 的原 argv／stdout／stderr／JSON：

|作者实际操作|结果与原件|
|---|---|
|普通 commit|退出 0／1.1609 秒，29 件变更；stdout SHA `959411d82de0b59e1657f69dda3106b22ecb40eebe1cfd5f0bac92d6c2c134a1`，stderr 空|
|`git push origin HEAD:refs/heads/refactor/architecture-foundations`|退出 0／44.7522 秒；无 force，原 stderr 显示 `93b538f..ad331c8`，SHA `3899d7aacab763558f4ff20a3498d190bad7167ff5a674a98574c0d9e91389b6`，stdout 空|
|`git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`|退出 0／29.7316 秒；原 stdout 精确为上述完整 `ad331c854a6fbdbf6bacc3aac4350bb8d393713f` 与该 ref，SHA `bd004d81c61d23087950723670b45519a9a50cd2303ccdc2213fc5ce0d27b9a6`，stderr 空|

**精确 29 Git 对象／mode／ready 与作者 SSH Ref 原件的独立离线核对通过，无新增 finding。** 本评审没有直接联网查询远端；上述结论是对作者实际原件的离线核对，不能称评审者直接网络确认。本提交自己的 CI 终态与必要双 OS 步骤尚待原件终核，**O4 继续开放，C3a 精确交付尚未终结**；不借旧 C2a CI 或本地通过替代。

## O4 最终 CI 原件终核：精确交付终结

继续由原评审者只读核保留原件，没有网络请求、产品／测试／模型运行、安装或提交。对象固定为 **`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`**、原 ready 与 r3 包；没有把已经进入下一片的 C3b 工作树作为 C3a 候选。本节追加不改写提交内报告快照或前文当时的待核状态。

独立以标准库重算 **7 份实际响应**的大小／SHA，并与各 HTTP 回执或 API source 记录的请求 URL、最终 URL、状态逐一核对；没有执行作者会写结果的 parser。全部相符：

|保留原响应|HTTP／字节|body SHA256|
|---|---|---|
|`ci-api-r1/runs.json`|403／280|`cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`|
|`actions-html-r1/page.html`|200／320,264|`5270424d71499fcb7185c089633ac61be384af3ce1aa16516a21cc32030dd6b7`|
|`ci-run-html-r1/page.html`|200／150,737|`dd8308e3decf0b30fae4c45655d1db9c4bd4619d268d2126d22de0fac8be281a`|
|`ci-matrix-html-r1/page.html`|404／226,126|`cc18685632ae0e7f012545a984e3313984baee30fd1cbd7ab975e14077528ba9`|
|`ci-run-html-r2/page.html`|200／157,202|`ea0d2ae90a922fbf23d888a1ee16355b757d5af5c4c98bffd1295d9dd4477c6c`|
|`ci-job-130596697924-html-r1/page.html`|200／161,751|`b6d7cc637ce159d969ac0b3ef74beadf2408d43b6cf2b19b2e08051c1dd35928`|
|`ci-job-130596697242-html-r1/page.html`|200／159,839|`8b5075d22c6a8a3b9b47a9e67382a07f372853db7c296752552aaa4ff45658ce`|

API 原文为匿名限流 403，不能计作成功 REST 或测试失败。matrix 原文为该视图的 404，不证明 job 不存在。首份 run HTML 仍为 **In progress**；原 `ci-result-r1` 的未齐状态保持。后份 run 已为 Success、但尚无 job 原件的 `ci-result-r2` 也保留当时 `required_steps_passed: false`，没有回写成当时已经完成必要步骤终核。

Actions 发现页指向本 run。两份 run HTML 均在推送身份处链接精确完整 candidate SHA、原分支及 `portability.yml`；最终 `ci-run-html-r2` 对 **run `43042210053`** 明确显示 **Success**，并分别链接 Linux **`130596697924`**、Windows **`130596697242`**。最终 run receipt SHA 为 **`3333ce3dc790b38a04917de970d4e5f68cc0c549b0c1653f669550907eecc586`**。两份 job receipt SHA 分别为 **`6fc3a5df2117ee6168260755f0eeed0dcf8f464fe5284c139014e6b953ca1a48`**、**`ae1128210194e4d6a8856180bc5662c8a0bb1cd52d801b2f264d0d69c199bda6`**，实际请求／最终 URL 均是对应 run 下的精确 job。

从该提交的 `.github/workflows/portability.yml` 重新确认矩阵是 Ubuntu／Python 3.11 和 Windows／Python 3.12。独立解析原 HTML 元素与属性：两 job 的 `check-steps` 均为 **completed**；各必要 `check-step` 均有 `data-conclusion="success"`、`data-job-completed` 和有效起止时间，`data-log-url` 逐个固定为 `/626619403/Ergora/commit/<完整ad331c8 SHA>/checks/<原job ID>/logs/<原步骤号>`。

|job|必要步骤|原件结果|
|---|---|---|
|Linux `130596697924`|Build and install wheel；Packaged reference identity；Native application regression|3／3 success／completed；回归完成 `2026-11-11T15:01:01Z`|
|Windows `130596697242`|上述三步；Windows PowerShell 5.1 installer and upgrade|4／4 success／completed；回归完成 `2026-11-11T15:02:31Z`，installer 完成 `15:03:27Z`|

Linux 的 Windows installer 为 skipped，与原 workflow 的 Windows 条件一致，不计入 Linux 必要三步。两 job 的 Complete job 也均 success。重建的七步名称、结论、时间、完成标记与各 receipt／body 摘要逐项等于 `ci-result-r3.json`，该投影 SHA **`8c29853d1b64b6849147fe641b9fe15e57094d4bf8821f036d1fbbba45aca739`**。此处只确认官方 HTML 报告的终态与必要步骤，没有下载完整 job 日志，也不据链接推断未读取的测试明细或计数。

**O4 最终结论：通过。** 同片的精确 29 Git 对象／mode／ready、原 r3 包／283 冻结、普通提交／推送、作者 SSH 同完整 Ref 原件及本提交自己的 **run `43042210053` 双 OS 七必要步骤**均已由原评审者独立离线终核。Spec／Standards 仍开放 **0／0**，无新增 finding；**C3a 对 `ad331c854a6fbdbf6bacc3aac4350bb8d393713f` 的精确交付终结**。原 REST 403、matrix 404、非终态及中间未齐样本保留；不称成功 REST、完整日志或评审者独立直接网络成功。C3b、F7 其余及项目整体仍按各自范围继续，前文真实平台／执行环境限制保持。
